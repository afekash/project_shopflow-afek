# CAP Theorem

## The Problem

You've distributed your data across multiple nodes for scalability and fault tolerance. Then the network fails. Two of your nodes can no longer communicate with each other.

What does the system do now? It has a choice: refuse to serve requests until the nodes reconnect and agree on the current state, or keep serving requests from whichever node is reachable -- accepting that responses may be stale.

There is no option that gives you both. This is the fundamental trade-off of distributed systems.

## The Solution

The **CAP theorem**, proposed by Eric Brewer in 2000 and formally proven in 2002, states:

> A distributed system can guarantee at most two of the following three properties simultaneously.

```
         Consistency (C)
              /\
             /  \
            /    \
           /      \
          /        \
  Availability  ──── Partition
      (A)         Tolerance (P)
```

Since network partitions are unavoidable in any real distributed system, the practical choice is always between C and A *during a partition*.

## How It Works

### The Three Properties

**Consistency (C)**
Every read receives the most recent write, or an error. All nodes see the same data at the same time. If you write a value to Node 1, any subsequent read from Node 2 must return the updated value -- or return an error, never stale data.

**Availability (A)**
Every request receives a response (not an error). The system keeps serving requests even when some nodes are unreachable. The response may contain stale data.

**Partition Tolerance (P)**
The system continues operating when network messages between nodes are lost or delayed. A network partition is a split: some nodes can talk to each other, others cannot.

### Why Partition Tolerance Is Not Optional

Networks fail. Switches crash. Cables are cut. Data center links go down. A distributed system that assumes a perfectly reliable network will eventually be unavailable whenever reality contradicts that assumption.

Therefore: **every distributed system must be partition tolerant**. The real question is what happens *during* a partition:

```
                    Network Partition Occurs
                           │
              ┌────────────┴────────────┐
              │                         │
         Prioritize C              Prioritize A
              │                         │
    ┌─────────▼─────────┐    ┌─────────▼─────────┐
    │ Return error or   │    │ Return potentially │
    │ wait until nodes  │    │ stale data from    │
    │ are in sync       │    │ the available node │
    └───────────────────┘    └───────────────────┘
```

### A Concrete Example

A distributed account balance database, replicated across two data centers. A user deposits $100. The write lands on Data Center 1. Then the network link between the data centers fails.

A user in Data Center 2's region now checks their balance:

**CP system (prioritize consistency)**: Data Center 2 refuses to serve the read because it cannot confirm it has the latest data. Returns an error or times out. The system sacrifices availability for correctness.

**AP system (prioritize availability)**: Data Center 2 serves the read from its local data, returning the balance before the $100 deposit. The user sees stale data. The system sacrifices consistency for availability.

For a bank account, **CP** is the only acceptable choice. For a social media "likes" counter, **AP** is usually fine -- a user seeing 1,042 likes instead of 1,043 for a few seconds is not a problem.

### CP vs AP: Not Binary

CAP is often taught as a strict binary choice, but in practice most systems offer tunable behavior:

**CP-leaning systems** refuse to serve stale data but may queue or reject requests during partitions:
- Strong consistency for critical operations (payments, inventory)
- May allow eventual consistency for non-critical reads

**AP-leaning systems** always serve requests but data may be stale:
- Writes succeed locally and propagate asynchronously
- Reads may reflect data from before the partition
- Conflict resolution needed when partition heals (e.g., last-writer-wins, application-level merge)

**Tunable systems** let you choose per-operation:
```
Operation-level consistency choices:
  Financial transfer:  → require majority acknowledgment (CP)
  User profile read:   → read from any available node (AP)
  Analytics counter:   → eventual consistency fine (AP)
  Inventory decrement: → require coordination (CP)
```

## Trade-offs

**Choosing CP (sacrifice availability during partitions):**
- Users get errors or timeouts during network incidents
- Data is always correct when served
- Appropriate for financial systems, inventory, any operation where stale data causes real harm
- System complexity: must handle "not available" gracefully in the application

**Choosing AP (sacrifice consistency during partitions):**
- Users always get a response, even during network incidents
- Data may be stale for the duration of the partition + replication catch-up time
- Appropriate for social features, content feeds, analytics, caches
- System complexity: must handle eventual consistency and conflict resolution in the application

**No free lunch**: there is no way to have all three simultaneously in a truly distributed system. Picking C or A during partitions is a fundamental constraint, not a product limitation.

## Advanced Note: PACELC Extension

CAP only describes behavior during network partitions. In 2012, Daniel Abadi proposed **PACELC** to also describe behavior during *normal operation*:

> **If Partition (P): trade off Availability (A) vs Consistency (C). Else (E): trade off Latency (L) vs Consistency (C).**

Even without partitions, making a write durable across multiple nodes requires waiting for those nodes to acknowledge. That wait introduces latency. Systems that skip cross-node coordination have lower latency but weaker consistency guarantees.

```
              │ During Partition │ Normal Operation
──────────────┼──────────────────┼──────────────────
CP + EL       │ Choose C         │ Trade C for latency
CP + EC       │ Choose C         │ Maintain C (pay latency)
AP + EL       │ Choose A         │ Trade C for latency
```

PACELC explains why many "CP" systems still offer eventual consistency modes: even without partitions, strong consistency has a latency cost that most applications don't want to pay for every operation.

## Where You'll See This

- **Distributed databases**: Every distributed database sits somewhere on the CP/AP spectrum -- the documentation will tell you where, and you can often tune it per operation
- **Replication configurations**: Write concern settings, quorum levels, and consistency modes are all implementations of the CP/AP trade-off -- see [Quorum and Tunable Consistency](04-quorum-and-tunable-consistency.md)
- **Microservices**: Service-to-service calls across network boundaries face the same CAP trade-offs -- a service call may fail, and the calling service must decide: fail the request (C) or serve a cached/default response (A)
- **Caches**: A cache that may serve stale data is an AP design. A cache that refuses to serve if it can't validate freshness is a CP design.

---

**Next:** [ACID vs BASE →](02-acid-vs-base.md)
