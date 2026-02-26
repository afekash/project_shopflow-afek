# Vertical vs Horizontal Scaling

## The Problem

Your system is running out of capacity. Queries slow down, writes back up, CPU pegs at 100%. You need more capacity. How do you add it?

This is the fundamental scaling decision, and the choice you make here determines your entire system architecture.

## The Solution

Two fundamentally different strategies:

- **Vertical scaling (scale up)**: Make the existing machine bigger -- more CPU cores, more RAM, faster disks.
- **Horizontal scaling (scale out)**: Add more machines and distribute the work across them.

Neither is universally better. Each solves different problems and introduces different constraints.

## How It Works

### Vertical Scaling

Take the existing server and give it more resources.

```
Vertical Scaling (Scale Up):

Before:              After:
┌──────────────┐     ┌──────────────────────────┐
│  8-core CPU  │ →   │  128-core CPU             │
│  32 GB RAM   │     │  4 TB RAM                 │
│  2 TB SSD    │     │  100 TB NVMe RAID         │
└──────────────┘     └──────────────────────────┘
   1 machine              1 (bigger) machine
```

**Advantages:**
- Zero change to application code -- no distributed systems complexity to manage
- Consistent latency -- data is local, no network round-trips between nodes
- Strong consistency is trivial -- one machine, one truth
- Simple operations -- one thing to monitor, backup, and upgrade

**Limitations:**
- **Cost curve is exponential**: A server with 4x the RAM costs roughly 8-16x more, not 4x. High-end hardware has a premium that compounds at the top of the range.
- **Hard ceiling**: There is a largest available machine. Once you reach it, the strategy is exhausted.
- **Single point of failure**: The bigger the machine, the worse the failure event. When the giant server goes down, everything goes down.
- **Maintenance windows**: Upgrading or restarting a single large server takes everything offline.

### Horizontal Scaling

Add commodity servers and distribute data and load across them.

```
Horizontal Scaling (Scale Out):

Before:              After:
┌──────────────┐     ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│  32-core CPU │     │Node 1│  │Node 2│  │Node 3│  │Node 4│
│  128 GB RAM  │ →   │ 32GB │  │ 32GB │  │ 32GB │  │ 32GB │
│  10 TB SSD   │     └──────┘  └──────┘  └──────┘  └──────┘
└──────────────┘     4 commodity nodes (same total RAM, much cheaper)
```

**Advantages:**
- **Theoretically unlimited**: Need more capacity? Add another node. There's no ceiling.
- **Commodity hardware**: Cheap, standardized servers available in large quantities. No premium pricing.
- **Fault tolerance**: Lose one node; the others keep running. No single point of failure.
- **Rolling upgrades**: Take one node offline at a time; the cluster keeps serving requests.
- **Geographic distribution**: Nodes can be placed in different data centers or regions.

**Limitations:**
- **Distributed systems complexity**: Data must be partitioned across nodes. Queries that touch data on multiple nodes are expensive (see [Partitioning Strategies](02-partitioning-strategies.md)).
- **Consistency trade-offs**: When data is on multiple nodes, ensuring all nodes agree on the current state requires coordination -- see [CAP Theorem](../04-distributed-systems/01-cap-theorem.md).
- **Network becomes critical**: Nodes communicate over the network. Network latency and failures become a primary concern.
- **Operational complexity**: Many nodes = many things to monitor, configure, and upgrade.

### The Cost Curve Comparison

```
Performance vs Cost:

Vertical Scaling:
Cost │                              *
     │
     │                        *
     │
     │                   *
     │              *
     │  *  *  *  *
     └──────────────────────────── Performance
  (exponential - cheap at low end, costs explode as you hit hardware limits)

Horizontal Scaling:
Cost │                     *
     │                  *
     │               *
     │            *
     │         *
     │      *
     │   *
     │ *
     └──────────────── Performance
  (roughly linear -- each node adds proportional capacity)
```

The crossover point depends on what you're measuring. In raw hardware cost, commodity nodes become competitive with high-end servers somewhere in the hundreds-of-GB-of-RAM range. But hardware is only part of the cost — horizontal scaling adds real engineering overhead: distributed coordination, partial failures, consistency trade-offs, and operational complexity. When you factor that in, many teams are better served staying vertical longer than they expect.

### When Each Makes Sense

**Choose vertical scaling when:**
- Your dataset fits in a single node (most simple applications do -- don't over-engineer)
- You need strong ACID guarantees and joins (distributed versions are complex)
- Your team is small and operational complexity must stay low
- You're in early stages and simplicity matters more than theoretical scale limits

**Choose horizontal scaling when:**
- Your data doesn't fit or too expensive to fit on a single machine
- Write throughput saturates a single machine's I/O capacity
- You need geographic distribution (nodes in multiple regions)
- Cost at scale is a concern (commodity hardware is cheaper at the high end)
- You need fault tolerance (no single point of failure, this can be also approached by [replication](../05-replication-and-availability/01-replication-patterns.md))

**Advanced Note:** Vertical scaling first, horizontal when necessary. Many organizations horizontal-scale prematurely, adding complexity they don't need. A single well-tuned server can handle far more load than most teams expect -- PostgreSQL on a 128-core machine can serve millions of queries per day. That said, don't take "scale vertically first" to an extreme: a 1TB RAM server costs tens of thousands of dollars per month and is not a practical threshold to aim for. The real signal to switch is when vertical scaling requires hardware that is disproportionately expensive relative to what horizontal scaling would cost -- not an arbitrary RAM number.

## Where You'll See This

- **Relational databases**: Primarily vertical; horizontal sharding is possible but complex and usually avoided until necessary
- **NoSQL databases**: Designed ground-up for horizontal scaling -- adding nodes is a first-class operation, not an afterthought
- **Caching layers**: Horizontal via [Consistent Hashing](03-consistent-hashing.md) across cache nodes
- **Cloud auto-scaling**: Cloud providers automate both strategies -- vertical (instance resize) and horizontal (add instances) based on load
- **Replication vs Sharding**: Replication (multiple copies of the same data) scales reads; sharding (different data on different nodes) scales writes and storage -- see [Replication Patterns](../05-replication-and-availability/01-replication-patterns.md) and [Partitioning Strategies](02-partitioning-strategies.md)

---

**Next:** [Partitioning Strategies →](02-partitioning-strategies.md)
