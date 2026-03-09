---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Replication in Neo4j

```{note}
This lesson requires the Neo4j Cluster lab. Run `make lab-neo4j-cluster` before starting.
This lab takes ~30 seconds to initialize. Wait for the "Neo4j Cluster is ready" message.
```

A single Neo4j instance is a single point of failure. If it goes down, your fraud detection stops, your recommendation engine stops, your network topology queries stop. Replication solves this: run multiple copies of the database so that a single node failure does not interrupt service.

But replication is not just about redundancy. It introduces a fundamental tension that every distributed system must navigate: **how do you ensure that all copies stay consistent with each other?**

> **Core Concept:** See [Replication Patterns](../../core-concepts/05-replication-and-availability/01-replication-patterns.md) for the general taxonomy: primary-secondary, multi-primary, and peer-to-peer. Neo4j uses primary-secondary within a Raft consensus group.

---

## Neo4j Causal Clustering

Neo4j's replication model is called **causal clustering**. The cluster has two types of members:

**Primary members** (formerly "core servers") form the consensus group. They run the Raft protocol to elect a leader and agree on every write. All writes go through the leader. Primaries can also serve reads.

**Secondary members** (formerly "read replicas") receive a stream of committed transactions from the primaries and apply them asynchronously. They can serve reads but cannot accept writes. They are not part of the consensus group — their failure does not affect the cluster's ability to commit.

```
         ┌─────────────┐
Writes → │   Primary   │ ← Raft leader (elected)
         │   (Leader)  │
         └──────┬──────┘
                │ Raft replication (synchronous before commit)
         ┌──────┴──────┐
         │   Primary   │  ←─ Raft followers (vote on commits)
         │  (Follower) │
         └─────────────┘
         │   Primary   │  ←─ Raft followers
         │  (Follower) │
         └──────┬──────┘
                │ Transaction stream (async)
         ┌──────┴──────┐
         │  Secondary  │  ←─ Read replicas (scale reads, no vote)
         └─────────────┘
```

> **Core Concept:** See [Consensus and Failover](../../core-concepts/05-replication-and-availability/02-consensus-and-failover.md) for how Raft works: leader election, log replication, and why a majority quorum is required for commits.

---

## The Commit Process

When an application writes to the cluster:

1. The write is sent to the **leader** (or routed to it by the driver)
2. The leader appends it to its Raft log and replicates it to followers
3. A **majority of primaries** (including the leader) must acknowledge the write before it is committed
4. The leader responds to the client with success
5. Committed transactions are streamed to secondaries asynchronously

The "majority acknowledgment" step is what makes the cluster safe: even if one primary fails immediately after a commit, the write survives — it has been persisted on the majority. This is the Raft safety guarantee.

The cost: write latency includes a network round trip to get acknowledgment from at least one follower. In a 3-primary cluster, the write must reach 2 of 3 (the leader + 1 follower).

---

## Read Routing and Causal Consistency

The Neo4j driver can route reads to any cluster member — leader or follower — depending on the configured routing policy:

- `READ` session: driver sends reads to any available member (secondaries preferred for load distribution)
- `WRITE` session: driver sends all operations to the leader

**Causal consistency** is a key feature of Neo4j's clustering model. When your application performs a write followed immediately by a read, you want the read to see the write — even if it is routed to a secondary that has not yet received the transaction.

Neo4j solves this with **bookmarks**: after a write transaction, the client receives a bookmark (a transaction ID). When the client opens a subsequent read session with that bookmark, the driver ensures the read is served by a cluster member that has caught up to at least that transaction. This is "read your own writes" — a consistency guarantee weaker than full linearizability but sufficient for almost all application patterns.

> **Core Concept:** See [Consistency Models](../../core-concepts/04-distributed-systems/03-consistency-models.md) for how causal consistency compares to eventual consistency, linearizability, and session consistency.

---

## Hands-On: Observing the Cluster

```{code-cell} python
import os, time, socket
from neo4j import GraphDatabase, RoutingControl
from neo4j.exceptions import AuthError, ServiceUnavailable

ALL_NODES = [("neo4j-core1", 7687), ("neo4j-core2", 7687), ("neo4j-core3", 7687)]
AUTH = ("neo4j", "password")

def live_nodes():
    """Return only the cluster nodes that currently resolve in DNS (i.e. are running)."""
    result = []
    for host, port in ALL_NODES:
        try:
            socket.getaddrinfo(host, port)
            result.append((host, port))
        except socket.gaierror:
            pass
    return result

def cluster_resolver(address):
    return live_nodes()

# On a fresh cluster start the system database needs a few extra seconds to
# initialise before it accepts password auth. Retry with backoff.
for attempt in range(10):
    try:
        nodes = live_nodes()
        bootstrap_host, bootstrap_port = nodes[0]
        driver = GraphDatabase.driver(
            f"neo4j://{bootstrap_host}:{bootstrap_port}",
            auth=AUTH,
            resolver=cluster_resolver,
        )
        driver.verify_connectivity()
        print(f"Connected to cluster via {bootstrap_host}")
        break
    except (AuthError, ServiceUnavailable) as e:
        print(f"  Not ready yet ({e.__class__.__name__}), retrying in 5 s…")
        driver.close()
        time.sleep(5)
else:
    raise RuntimeError("Cluster did not become ready in time")
```

```{code-cell} python
# Write to the cluster — goes to the leader via routing
with driver.session(database="neo4j") as session:
    session.run("""
        MERGE (alice:Person {name: 'Alice'})
        MERGE (bob:Person   {name: 'Bob'})
        MERGE (alice)-[:KNOWS]->(bob)
    """)
    print("Write committed via cluster routing")

# Read from the cluster — may be served by any primary
with driver.session(database="neo4j") as session:
    result = session.run("MATCH (p:Person) RETURN p.name AS name ORDER BY name")
    names = [r["name"] for r in result]
    print(f"Read result: {names}")
```

```{code-cell} python
# Bookmark-based causal consistency: read your own write
with driver.session(database="neo4j") as write_session:
    write_session.run("""
        MERGE (carol:Person {name: 'Carol'})
        MERGE (carol)-[:KNOWS]->(alice:Person {name: 'Alice'})
    """)
    bookmark = write_session.last_bookmarks()
    print(f"Write completed. Bookmark: {bookmark}")

# Pass the bookmark to the read session -- guaranteed to see the above write
with driver.session(database="neo4j", bookmarks=bookmark) as read_session:
    result = read_session.run("""
        MATCH (p:Person)-[:KNOWS]->(q:Person)
        RETURN p.name AS from_node, q.name AS to_node
        ORDER BY from_node
    """)
    print("Relationships (read with causal bookmark):")
    for r in result:
        print(f"  {r['from_node']} → {r['to_node']}")
```

```{code-cell} python
# Check cluster topology via the system database.
# SHOW SERVERS returns an internal UUID in `name`; `address` holds the bolt
# advertised address (e.g. "neo4j-core1:7687"), so we strip the port to get
# the human-readable service name.
def resolve(server_record):
    """Return the service hostname from a SHOW SERVERS record."""
    address = server_record["address"]   # e.g. "neo4j-core1:7687"
    if address:
        return address.split(":")[0]         # e.g. "neo4j-core1"
    return None

with driver.session(database="system") as session:
    result = session.run("SHOW SERVERS")
    print("\nCluster members:")
    for r in result:
        host = resolve(r)
        if host:
            print(f"  {host} | state={r['state']} | health={r['health']}")

driver.close()
```

---

## Failover: What Happens When a Primary Dies

If the Raft leader fails, the remaining primaries detect the absence (via heartbeat timeout) and elect a new leader. The election requires a majority — in a 3-primary cluster, 2 of 3 must be reachable to elect a leader.

During the election window (typically 5–15 seconds), writes to the cluster will fail. The driver will retry with backoff until the new leader is elected. Reads from secondaries continue uninterrupted.

If a majority of primaries are lost (e.g., 2 of 3 fail), the cluster enters a **read-only state** — it refuses writes to prevent data divergence. This is the CP behavior discussed in the tradeoffs lesson: Neo4j chooses to stop accepting writes rather than allow a split-brain state.

> **Compare with Redis Sentinel:** Redis Sentinel uses a similar majority election mechanism. The key difference is that Redis can be configured for weaker consistency (`min-replicas-to-write 0`) to stay writable under partition. Neo4j's Raft model provides stronger guarantees by default.

### Hands-On: Simulating a Leader Failover

```{code-cell} python
import subprocess, time
from neo4j import GraphDatabase

AUTH = ("neo4j", "password")

CORE_CONTAINERS = ["neo4j-core1", "neo4j-core2", "neo4j-core3"]

def docker_status():
    """Return a dict of {container_name: 'running'|'exited'|...} via docker inspect."""
    result = {}
    for name in CORE_CONTAINERS:
        out = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}}", name],
            capture_output=True, text=True
        )
        result[name] = out.stdout.strip() if out.returncode == 0 else "unknown"
    return result

def show_topology(driver):
    """Print cluster topology from Neo4j alongside ground-truth Docker container status."""
    # Ground-truth liveness from Docker — not subject to cluster cache lag
    container_state = docker_status()
    print("  Docker container states (ground truth):")
    for name, state in container_state.items():
        marker = "✓" if state == "running" else "✗"
        print(f"    {marker} {name}: {state}")

    # Neo4j cluster view — may lag behind by a few seconds after a failure
    with driver.session(database="system") as s:
        rows = list(s.run(
            "SHOW DATABASES YIELD name, address, role, writer "
            "WHERE name = 'neo4j'"
        ))
    writer = next((r["address"].split(":")[0] for r in rows if r["writer"]), "unknown")
    print(f"\n  Neo4j cluster view (may be stale):")
    print(f"    Leader (writer): {writer}")
    with driver.session(database="system") as s:
        for r in s.run("SHOW SERVERS"):
            host = resolve(r)
            docker_state = container_state.get(host, "unknown")
            mismatch = " ← STALE" if r["health"] == "AVAILABLE" and docker_state != "running" else ""
            print(f"    {host} | state={r['state']} | health={r['health']} | docker={docker_state}{mismatch}")

    return writer

driver = GraphDatabase.driver(
    "neo4j://neo4j-core1:7687",
    auth=AUTH,
    resolver=cluster_resolver,  # defined in the first cell — tries all three nodes
)
print("=== Topology before failover ===")
leader = show_topology(driver)
print(f"\nLeader to stop: {leader}")
with open("/tmp/neo4j_leader", "w") as f:
    f.write(leader)
```

```{code-cell} python
%%bash
LEADER=$(cat /tmp/neo4j_leader)
echo "Stopping leader: $LEADER"
docker stop "$LEADER"
```

```{code-cell} python
# Give Raft ~15 seconds to detect the failure and elect a new leader
# (leader_failure_detection_window=5s-8s + election rounds).
print("Waiting 15 s for re-election...")
time.sleep(15)

# Reconnect via a surviving node — the stopped leader may no longer resolve.
nodes = live_nodes()  # only returns nodes currently up
bootstrap_host = nodes[0][0]

driver.close()
driver = GraphDatabase.driver(f"neo4j://{bootstrap_host}:7687", auth=AUTH, resolver=cluster_resolver)
print("\n=== Topology after leader failure ===")
show_topology(driver)
# Any "← STALE" marker above means Neo4j's cluster metadata hasn't propagated
# yet — the Docker state is the ground truth for actual liveness.
```

```{code-cell} python
%%bash
# Bring the stopped node back up.
LEADER=$(docker ps -a --filter "status=exited" --filter "name=neo4j-core" \
  --format "{{.Names}}" | head -1)
echo "Restarting: $LEADER"
docker start "$LEADER"
```

```{code-cell} python
# Allow the rejoined node to catch up with the Raft log before querying.
print("Waiting 20 s for the node to rejoin...")
time.sleep(20)

driver.close()
driver = GraphDatabase.driver("neo4j://neo4j-core1:7687", auth=AUTH, resolver=cluster_resolver)
print("\n=== Topology after node rejoin ===")
show_topology(driver)

driver.close()
```

---

**← Back: [Tradeoffs and Limitations](06-tradeoffs-and-limitations.md)** | **Next: [Sharding →](08-sharding.md)** | [Course Home](../README.md)
