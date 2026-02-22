# Quorum and Tunable Consistency

## The Problem

You're replicating data across N nodes for durability and fault tolerance. Two extreme options:

- **Require ALL N nodes to acknowledge every write**: Maximum durability -- every node has the latest data before you return success. But if even one node is slow or unavailable, every write stalls.
- **Require only ONE node to acknowledge**: Maximum availability -- writes complete as fast as the fastest node. But reads from any other node might return stale data.

Neither extreme is right for most applications. Payments need strong guarantees; analytics can tolerate staleness. Is there a principled way to choose a middle ground?

## The Solution

**Quorum-based consistency** -- configure independently how many nodes must acknowledge writes (W) and how many nodes must respond to reads (R). The key mathematical insight:

> If R + W > N, you are guaranteed to read the latest write.

The overlap between the write-acknowledged nodes and the read-consulted nodes guarantees at least one node in the read set has the latest write.

## How It Works

### The R + W > N Guarantee

```
N = 3 nodes (replication factor 3)

                Node 1  Node 2  Node 3
Write (W=2):    ✓       ✓               ← write confirmed on 2 nodes
Read  (R=2):            ✓       ✓       ← read from 2 nodes

Overlap: Node 2 is in both sets.
Node 2 confirmed the write, so Node 2's response to the read is up-to-date.
The read returns the latest value. ✓

W + R = 2 + 2 = 4 > N = 3  ← the guarantee holds
```

If R + W ≤ N, there's no guaranteed overlap. You might read from nodes that didn't receive the write:

```
N = 3, W=1, R=1  (W + R = 2, not > N=3)

Write to Node 1 only.
Read from Node 3 only.

Node 3 might not have received the write yet → stale read ✗
```

### Common Quorum Configurations

```
N = 3 (3 replicas)

  W=3, R=1 (ALL writes, ONE read):
    Write: must confirm on all 3 nodes → slowest writes, strongest durability
    Read: can read from any 1 node → fastest reads, always up-to-date (W+R=4 > 3)
    Risk: if any node is unavailable, writes fail

  W=2, R=2 (QUORUM):
    Write: 2 nodes confirm → balanced latency and durability
    Read: return newest value from 2 nodes → balanced (W+R=4 > 3)
    Tolerates 1 node failure for both reads and writes

  W=1, R=3 (ONE write, ALL reads):
    Write: fastest (just 1 confirmation) → writes always fast
    Read: must read all 3 and take newest → slowest reads, but always up-to-date
    Risk: if any node is unavailable, reads fail

  W=1, R=1 (fastest, weakest):
    W+R=2, not > N=3 → NO GUARANTEE
    Used for maximum throughput when stale reads are acceptable
    Common for analytics, metrics, non-critical reads

  W=2, R=1 (write quorum, single read):
    W+R=3, not > N=3 → NO GUARANTEE
    Writes are durable but reads may be stale
    Common pattern when writes need confirmation but reads can be approximate
```

### Tuning Per Operation

The real power of quorum-based systems: you don't have to pick one configuration globally. You can tune consistency per operation based on what each operation actually requires.

```
// Financial transfer: require strongest consistency
db.accounts.update(
    { _id: "account_42" },
    { $inc: { balance: -100 } },
    write_concern = "majority",  # W = majority of nodes
    read_concern = "majority"    # R = majority of nodes
)

// Product view count: eventual consistency acceptable
db.products.update(
    { _id: "product_123" },
    { $inc: { views: 1 } },
    write_concern = "one",       # W = 1 node (fast)
    read_concern = "local"       # R = 1 node (might be stale)
)
```

### Read Repair

When a read queries multiple nodes (R > 1) and finds they have different values, the system can repair the discrepancy:

1. Return the newest value to the client (based on timestamp or version vector)
2. Asynchronously write the newest value to the nodes that had stale data

```
Read from Node 1, Node 2, Node 3:
  Node 1: X = 5 (older)
  Node 2: X = 7 (newer)  ← return this
  Node 3: X = 5 (older)

Read repair: write X=7 to Nodes 1 and 3 asynchronously
After repair: all nodes have X=7
```

Read repair converges stale nodes toward the current value without background replication overhead.

### Hinted Handoff

When a node is temporarily unavailable during a write, some systems (particularly AP-leaning ones) use **hinted handoff**: write to a healthy node on behalf of the unavailable node, with a "hint" that this data must be forwarded when the target node recovers.

```
Normal write (W=2): → Node 1 ✓, Node 2 ✓
Node 2 is down:     → Node 1 ✓, Node 3 (hint: "this belongs to Node 2")
Node 2 recovers:    → Node 3 forwards the hinted data to Node 2
```

This allows writes to succeed even when the target replica is temporarily down, at the cost of the hint delivery window where Node 2's data is stale.

## Trade-offs

| Configuration | Write Availability | Read Availability | Consistency |
|---------------|-------------------|-------------------|-------------|
| W=N, R=1      | Low (all must be up) | High | Strong |
| W=majority, R=majority | Medium | Medium | Strong (R+W > N) |
| W=1, R=N      | High | Low (all must respond) | Strong |
| W=1, R=1      | High | High | Weak (eventual) |

**The fundamental insight**: Consistency, availability, and latency form a three-way trade-off. Quorum lets you tune the exact operating point per operation, rather than making a single global choice.

**Latency implications**:
- Higher W → write latency = slowest of the W nodes
- Higher R → read latency = slowest of the R nodes
- QUORUM (majority) is usually the practical sweet spot: tolerates one node failure, doesn't pay the latency of waiting for all nodes

## Where You'll See This

- **Column-family stores** (Cassandra): Consistency levels ONE, QUORUM, ALL are configurable per read/write operation -- the canonical quorum-based system
- **Distributed databases** (Riak, CockroachDB): Quorum reads and writes are the default mechanism for balancing availability and consistency
- **Document databases** (MongoDB): Write concern (`w: majority`) and read concern (`majority`) are the quorum knobs; the math is the same
- **Consensus protocols** (Raft, Paxos): Leader election requires a majority quorum of nodes to agree before a candidate can become leader -- see [Consensus and Failover](../05-replication-and-availability/02-consensus-and-failover.md)
- **Distributed lock managers**: Acquiring a distributed lock requires writing to a quorum to prevent two nodes from both thinking they hold the lock

---

**Next:** [Replication Patterns →](../05-replication-and-availability/01-replication-patterns.md)
