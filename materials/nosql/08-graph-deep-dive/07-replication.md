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
import os
from neo4j import GraphDatabase, RoutingControl

CLUSTER_URI = os.environ.get("NEO4J_CLUSTER_URI", "neo4j://neo4j-core1:7687")
AUTH = ("neo4j", "password")

driver = GraphDatabase.driver(CLUSTER_URI, auth=AUTH)
driver.verify_connectivity()
print(f"Connected to cluster at {CLUSTER_URI}")
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
# Check cluster topology via the system database
with driver.session(database="system") as session:
    result = session.run("SHOW SERVERS")
    print("\nCluster members:")
    for r in result:
        print(f"  {r['name']} | state={r['state']} | health={r['health']}")

driver.close()
```

---

## Failover: What Happens When a Primary Dies

If the Raft leader fails, the remaining primaries detect the absence (via heartbeat timeout) and elect a new leader. The election requires a majority — in a 3-primary cluster, 2 of 3 must be reachable to elect a leader.

During the election window (typically 5–15 seconds), writes to the cluster will fail. The driver will retry with backoff until the new leader is elected. Reads from secondaries continue uninterrupted.

If a majority of primaries are lost (e.g., 2 of 3 fail), the cluster enters a **read-only state** — it refuses writes to prevent data divergence. This is the CP behavior discussed in the tradeoffs lesson: Neo4j chooses to stop accepting writes rather than allow a split-brain state.

> **Compare with Redis Sentinel:** Redis Sentinel uses a similar majority election mechanism. The key difference is that Redis can be configured for weaker consistency (`min-replicas-to-write 0`) to stay writable under partition. Neo4j's Raft model provides stronger guarantees by default.

---

**← Back: [Tradeoffs and Limitations](06-tradeoffs-and-limitations.md)** | **Next: [Sharding →](08-sharding.md)** | [Course Home](../README.md)
