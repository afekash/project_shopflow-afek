# Consensus and Failover

## The Problem

In a primary-secondary system (see [Replication Patterns](01-replication-patterns.md)), the primary node handles all writes. When the primary fails, you need a new primary -- but how do you choose one?

Two scenarios make this harder than it sounds:

**Split brain**: A network partition makes Node A unable to communicate with Nodes B and C. Node A thinks it's still the primary. Nodes B and C decide to elect a new primary. Now you have *two* primaries, both accepting writes. When the partition heals, the data has diverged -- which writes are correct?

**Stale promotion**: A secondary that's significantly behind (replication lag) is promoted to primary. Writes that were committed on the old primary but not yet replicated are lost.

Both scenarios result in data corruption or data loss. You need a principled way to elect a new primary that prevents these problems.

## The Solution

**Consensus protocols** -- a group of nodes votes to elect a new leader. The key requirement: a candidate needs votes from a **strict majority** of all nodes (not just online nodes). This majority requirement guarantees that two nodes can never simultaneously hold valid leadership.

## How It Works

### Why Majority (Quorum)?

If Node A has 2 out of 3 votes, Node B cannot also have 2 out of 3 votes -- there aren't enough votes to go around. Two groups that each hold a majority *must* overlap. The overlap node will only vote once, so only one candidate can win.

```
3 nodes:  majority = 2
  Node A wins 2 votes → Node A is leader
  Node B cannot also win 2 votes (only 3 total, A already has 2) ✓

2 nodes:  majority = 2 (both must agree)
  If one node is down → no majority possible → no election → no availability ✗

  This is why 2-node clusters without an arbiter can't automatically elect a leader.
  You need an odd number of nodes, or an extra tiebreaker (arbiter).

5 nodes:  majority = 3
  Can tolerate loss of 2 nodes while still electing a leader.
```

### The Election Process

```
1. Primary stops responding (crash, network partition, overload)
         │
         ▼
2. Secondaries detect via periodic heartbeats
   (each secondary sends heartbeat to all others every N seconds)
         │
         ▼
3. After election timeout (typically 10 seconds), a secondary
   starts a new election term and nominates itself as candidate
         │
         ▼
4. Candidate requests votes from all other nodes
         │
         ▼
5. Each node votes YES if:
   - It hasn't voted in this term yet (prevents split votes)
   - The candidate's log is at least as up-to-date as its own
     (prevents electing a lagging secondary that would lose data)
         │
         ▼
6. If candidate receives majority votes → becomes new primary
   If no candidate wins → start another election round
   (random backoff prevents repeated ties)
         │
         ▼
7. New primary announces itself to the cluster
   Old primary (if it recovers) steps down when it discovers a newer term
```

The "up-to-date log" check in step 5 prevents stale promotions: a secondary that's missing recent writes cannot become primary because nodes with those writes will refuse to vote for it.

### Leader Lease and Fencing

A recovered old primary is a danger: it might still think it's the leader and accept writes that conflict with the new leader's writes. **Fencing** prevents this:

**Epoch/Term numbers**: Every election increments a term number. The new primary includes the term number in every operation. Nodes reject operations from a leader with an older term number -- the old primary's writes are ignored automatically.

```
Node A was primary in term 5.
Network partition: Nodes B and C elect Node B as primary in term 6.
Node A's partition heals: A tries to write with term 5.
Nodes B and C reject: "I'm already in term 6, term 5 is stale."
Node A sees the higher term and steps down.
```

**Leader lease**: A primary is granted leadership for a bounded time window. If it can't renew the lease (via heartbeats to a majority), it voluntarily steps down before the window expires, ensuring a new election can proceed safely.

### Failure Detection

How do nodes know the primary has failed? **Heartbeats** -- each node periodically sends a small message to all other nodes. Silence for longer than the expected heartbeat interval triggers suspicion. After a configurable timeout, the primary is declared failed and an election begins.

```
Heartbeat timeline:
  T0: Primary sends heartbeat → Secondary receives ✓
  T2: Primary sends heartbeat → Secondary receives ✓
  T4: Primary crashes (no heartbeat sent)
  T6: Secondary expected heartbeat, none received
  T8: Secondary still no heartbeat → increment miss count
  T10: Miss threshold exceeded → declare primary failed → start election
```

**The timeout trade-off**: A shorter timeout = faster failover detection but more false positives (network hiccups trigger unnecessary elections). A longer timeout = slower failover but fewer spurious elections. Typical production values: 5-30 seconds.

### Protocol Families

The mathematics of majority voting is the same across protocols; they differ in their details:

**Raft** (2013): Designed to be understandable. Strong leader, simple log replication. Used in etcd, CockroachDB, and many modern distributed systems. A good starting point for understanding consensus.

**Paxos** (1989): The foundational consensus protocol. Notoriously difficult to understand correctly, but every modern consensus protocol is either Paxos or derived from it. Multi-Paxos is the practical variant.

**ZAB** (Zookeeper Atomic Broadcast): The protocol underlying Apache ZooKeeper. Similar to Raft, designed for a coordinator/configuration service role.

### Built-in vs External Consensus

Two architectural approaches:

**Built-in consensus**: The database engine embeds the election protocol. Failover is automatic; no external coordinator needed. Configuration is simpler; the database handles its own leadership.

**External consensus**: The database uses an external coordination service (ZooKeeper, etcd, Consul) to manage leader election. The database itself is simpler but the operational footprint includes an additional distributed system to manage.

```
Built-in:
  Database cluster ←─ manages its own elections
  Operators configure one system

External coordinator:
  Database cluster ←─ asks ZooKeeper/etcd "who is primary?"
  ZooKeeper/etcd ←─ runs its own consensus protocol
  Operators manage two distributed systems
```

## Trade-offs

**Automatic failover (via consensus):**
- Higher availability: primary failure is handled without human intervention
- Faster recovery: seconds to elect a new primary vs. minutes for manual intervention
- Risk of false positives: a slow-but-alive primary might be incorrectly declared failed

**Manual failover:**
- Operator can inspect the situation before promoting a new primary
- No risk of split-brain from automated decisions
- Slower recovery (minutes to hours vs. seconds)

**The majority requirement:**
- Guarantees no split-brain
- Requires ≥ 3 nodes for automatic failover (2-node clusters need an arbiter or external tiebreaker)
- An even number of nodes is wasteful: 4 nodes has the same fault tolerance as 3 (majority of 4 = 3, majority of 3 = 2, so both tolerate 1 failure)

## Where You'll See This

- **Document databases** (MongoDB): Built-in election protocol based on Raft principles -- replica sets elect a new primary automatically when the current primary fails
- **Distributed configuration stores** (etcd, ZooKeeper, Consul): Pure consensus services used as external coordinators; other systems delegate leadership tracking to them
- **Distributed SQL** (CockroachDB, YugabyteDB): Use Raft per partition; every shard independently elects a leader
- **Distributed caches** (Redis Sentinel): A separate Sentinel process monitors Redis instances and orchestrates failover using its own quorum
- **Kubernetes**: etcd is the consensus backbone for all cluster state; every Kubernetes API write goes through Raft in etcd

---

**Next:** [Write-Ahead Logs →](03-write-ahead-logs.md)
