# Replication Patterns

## The Problem

A single machine storing your data is a single point of failure. The disk fails. The server reboots for a kernel update. The network card dies. In every case, your application loses access to its data -- and if the disk fails catastrophically, the data itself is gone.

The same problem appears at larger scale: a data center loses power. A network link between regions is cut. Any single location holding unique data represents existential risk.

## The Solution

**Replication** -- maintain copies of data on multiple nodes. If one node fails, others have a copy and can continue serving requests. The fundamental design question is:

> Who accepts writes, and how do changes propagate to the other copies?

The answer determines your system's consistency guarantees, availability characteristics, and complexity.

## How It Works

### Pattern 1: Primary-Secondary (Leader-Follower)

One node is designated the **primary** (also called leader or master). All writes go to the primary. Other nodes are **secondaries** (followers, replicas) that receive copies of the data.

```
           Application
           │         │
     All writes    Optional reads
           │         │
     ┌─────▼─────────▼─────┐
     │     PRIMARY NODE     │
     │   (accepts writes)   │
     └──────────┬───────────┘
                │ replicate changes
         ┌──────┴──────┐
         │             │
    ┌────▼────┐   ┌────▼────┐
    │Secondary│   │Secondary│
    │  (read) │   │  (read) │
    └─────────┘   └─────────┘
```

**Replication mechanism**: The primary records every write in an operations log (oplog, binlog, WAL). Secondaries tail this log and apply each operation to their own copy of the data.

**Write path**:
1. Client writes to primary
2. Primary writes to its local storage (and WAL)
3. Primary acknowledges to client (with w:1) or waits for secondaries to confirm (with w:majority)
4. Secondaries asynchronously pull the oplog and apply operations

**Read path**:
- Read from primary: always current data
- Read from secondary: potentially stale by the replication lag amount (milliseconds to seconds typically)

**What makes it good:**
- Simple consistency model: one authoritative source of truth for writes
- Easy to reason about: primary's data is always the current state
- Works well for read-heavy workloads: add secondaries to scale reads

**What makes it constrained:**
- Write throughput is limited to what the primary can handle (single write endpoint)
- Primary failure requires a failover process -- see [Consensus and Failover](02-consensus-and-failover.md)
- Secondaries can lag during high write load

### Pattern 2: Peer-to-Peer (Multi-Master / Leaderless)

Any node can accept writes. There is no designated primary. Writes succeed locally and propagate to peer nodes asynchronously.

```
           Application
        │      │      │
   write    write    write
        │      │      │
   ┌────▼──┐ ┌─▼────┐ ┌▼─────┐
   │ Node 1│↔│Node 2│↔│Node 3│
   └───────┘ └──────┘ └──────┘
     Any node accepts reads and writes
     Changes propagate between peers
```

**Write path**:
1. Client writes to any node (often the closest)
2. Node writes locally, acknowledges when quorum of peers confirm (or immediately for eventual consistency)
3. Node propagates to peers asynchronously

**Conflict resolution**: When two clients write the same key to different nodes simultaneously, both writes succeed initially. When the writes propagate and meet, a conflict resolution strategy kicks in:
- **Last-Writer-Wins (LWW)**: Timestamp determines the winner. Simple but can lose data if clocks aren't synchronized.
- **Version vectors**: Track which replica created which version; application merges conflicting versions.
- **CRDTs** (Conflict-free Replicated Data Types): Data structures designed so that all possible orderings of operations produce the same result (counters, sets with specific semantics).

**What makes it good:**
- No single point of failure: any node going down doesn't affect writes
- Write throughput scales with node count: each node accepts writes independently
- Geographic distribution: route writes to the local data center

**What makes it complex:**
- Conflicts are possible and require resolution logic
- Harder to reason about consistency: "did my write win?"
- Read-your-writes requires either reading from the same node or waiting for propagation

### Pattern 3: Multi-Primary (Multi-Active)

Multiple designated primary nodes, each accepting writes for their assigned data range, with replication between them. Not "any node" (that's peer-to-peer) but "multiple specifically designated write nodes."

```
           Application
        │                │
   writes to Region A   writes to Region B
        │                │
   ┌────▼──────────┐  ┌──▼────────────┐
   │  Primary A    │←→│  Primary B    │
   │ (US writes)   │  │ (EU writes)   │
   └───────────────┘  └───────────────┘
   Each primary replicates to the other
```

Commonly used for **multi-region active-active** deployments: users write to their local region, and changes propagate to other regions. The application must be designed to tolerate the brief window where regions are inconsistent.

### Synchronous vs Asynchronous Replication

The acknowledgment timing is a separate axis from the pattern:

**Synchronous (strong durability)**: The primary waits for secondary acknowledgment before telling the client the write succeeded. The data is guaranteed to be on multiple nodes before the client proceeds.
- Cost: write latency = primary latency + network round-trip to secondaries
- Benefit: zero data loss if primary fails immediately after acknowledgment

**Asynchronous (high throughput)**: The primary acknowledges to the client immediately, replicates to secondaries in the background.
- Cost: if primary fails before replication, recent writes are lost
- Benefit: write latency = primary latency only (no waiting for secondaries)

**Semi-synchronous**: Wait for at least one secondary to acknowledge, then replicate to the rest asynchronously. A practical middle ground.

## Trade-offs

| Pattern | Write Scalability | Consistency | Failure Handling | Complexity |
|---------|------------------|-------------|-----------------|------------|
| Primary-Secondary | Limited by primary | Simple (strong from primary, eventual from secondary) | Failover required | Low |
| Peer-to-Peer | Scales with nodes | Complex (quorum or eventual) | No single point | High |
| Multi-Primary | Scales with primaries | Complex (conflict resolution) | Per-region resilience | Highest |

## Where You'll See This

- **Relational databases**: Primary-secondary is the dominant model; added over time as the ecosystem matured, often requiring external tools for automatic failover
- **Document databases** (MongoDB): Primary-secondary (replica sets) with automatic election built into the engine -- see [Consensus and Failover](02-consensus-and-failover.md)
- **Column-family stores** (Cassandra): Peer-to-peer with tunable quorum -- any node accepts writes, consistency configured at query time
- **In-memory databases** (Redis): Primary-secondary with Redis Sentinel for automatic failover; Redis Cluster uses multi-primary across hash slot ranges
- **Distributed file systems**: Primary-secondary for metadata; peer-to-peer for data chunks
- **Geo-distributed systems**: Multi-primary is required for active-active multi-region deployments

---

**Next:** [Consensus and Failover →](02-consensus-and-failover.md)
