# Consistency Models

## The Problem

"Consistent" is used everywhere in databases, but it means different things in different contexts. When you write data to one node and read from another, what exactly can you expect?

- Does your read always return the value you just wrote?
- Does another client's concurrent read see the same thing as yours?
- If you made 5 writes in order, will another client always see them in that order?

These guarantees -- what you can assume about the relationship between writes and reads -- are formalized as **consistency models**. Understanding the spectrum is essential for reasoning about distributed system behavior.

## The Solution

Consistency is not a binary property. It's a spectrum from very strong (highest guarantees, highest cost) to very weak (lowest guarantees, lowest cost). Choosing a point on the spectrum is a deliberate engineering decision based on what your application actually needs.

## How It Works

### The Consistency Spectrum

```
Strongest                                                    Weakest
    │                                                           │
    ▼                                                           ▼
Linearizable → Sequential → Causal → Read-Your-Writes → Eventual
    │               │           │            │               │
High latency     Medium      Lower        Low           Lowest latency
High coordination  ←────── coordination overhead ──────→  no coordination
```

### Linearizable (Strong) Consistency

Every operation appears to happen instantaneously at a single point in time, and that order is consistent with real-world time. If a write completes before a read begins, the read always sees the written value.

The mental model: the entire distributed system behaves as if it were a single machine.

```
Timeline:
  T1: Client A writes X=1
  T2: Client B reads X       → must return 1 (write completed before read began)
  T3: Client C reads X       → must return 1

Even if Client B and C are reading from different nodes.
```

**Cost**: Before returning, the system must coordinate with enough nodes to guarantee the write is globally visible. This adds latency proportional to the number of nodes consulted.

**When to use**: Financial balances, leader election, distributed locks, inventory counts where overselling is unacceptable.

### Sequential Consistency

All operations appear in some global order, but that order doesn't have to match real-world clock time. All nodes agree on the same order of operations -- they just might not reflect the exact real-time sequence.

```
Client A writes: X=1, then X=2
Client B reads:  must see X=1 before X=2 (sequential order preserved)
                 but might not see X=2 immediately after A's write
```

Less strict than linearizable (no real-time ordering guarantee) but still ensures all nodes see operations in the same sequence.

### Causal Consistency

Operations that are causally related must appear in order everywhere. Operations that are not causally related may appear in different orders on different nodes.

**Causally related**: Event B was caused by Event A (e.g., you can only reply to a post after it was created; the reply is causally dependent on the post).

```
Alice posts a message: "Meeting at 3pm"
Bob reads Alice's message, then replies: "Can we push to 4pm?"

Causal consistency guarantees:
  Any node that shows Bob's reply MUST also show Alice's message first.
  (You can't see a reply without seeing what it's replying to.)

But: if Carol posts "Great weather today" at the same time as Alice's message,
     different nodes may show those in different orders (not causally related).
```

Commonly implemented as **read-your-writes**: you always see the effects of your own writes, even when reading from a replica.

### Eventual Consistency

Given no new updates, all nodes will eventually converge to the same value. No guarantee about how quickly, and no guarantee about ordering. A read may return any version that was valid at some point.

```
Client A writes X=1 to Node 1.
                    Node 1 replicates asynchronously to Node 2.

Immediately after:
  Read from Node 1 → returns 1
  Read from Node 2 → might return old value (0) or new value (1)

After replication completes:
  Read from Node 1 → returns 1
  Read from Node 2 → returns 1   (eventually consistent ✓)
```

**When to use**: Social media feeds, shopping cart contents, product ratings, DNS propagation, CDN caches -- any use case where a brief window of stale data is tolerable.

### Isolation Levels: ACID's Consistency Spectrum

Within a single database (not distributed across nodes), **isolation levels** define the consistency spectrum for concurrent transactions. From weakest to strongest:

**Read Uncommitted**: A transaction can read data that another transaction has written but not yet committed. Risk: dirty reads -- you read data that might be rolled back.

**Read Committed**: A transaction only reads data that has been committed. Eliminates dirty reads. Risk: non-repeatable reads -- two reads of the same row within one transaction may return different values if another transaction committed between them.

**Repeatable Read**: If a transaction reads a row, subsequent reads of that row within the same transaction return the same value, even if another transaction modifies and commits that row. Eliminates non-repeatable reads. Risk: phantom reads -- a range query may return different rows if another transaction inserts or deletes rows matching the range.

**Snapshot Isolation**: The transaction reads from a consistent snapshot of the database taken at the start of the transaction. All reads are internally consistent (no phantoms), but the snapshot may be stale compared to concurrent writes.

**Serializable**: The strongest isolation level. Transactions execute as if they were sequential, never concurrent. No dirty reads, no non-repeatable reads, no phantom reads. Highest performance cost.

```
Isolation Level    │ Dirty Read │ Non-repeatable Read │ Phantom Read
───────────────────┼────────────┼────────────────────┼─────────────
Read Uncommitted   │ Possible   │ Possible            │ Possible
Read Committed     │ No         │ Possible            │ Possible
Repeatable Read    │ No         │ No                  │ Possible (MySQL: No)
Snapshot           │ No         │ No                  │ No
Serializable       │ No         │ No                  │ No
```

## Trade-offs

**Stronger consistency means:**
- Higher latency (must wait for cross-node coordination or lock acquisition)
- Lower throughput (fewer concurrent operations can proceed)
- Higher availability cost (may refuse requests rather than serve stale data)
- Application simplicity (database handles correctness)

**Weaker consistency means:**
- Lower latency (writes/reads proceed without coordination)
- Higher throughput (no lock contention)
- Higher availability (always serves requests)
- Application complexity (application must handle stale reads, conflicts, eventual convergence)

## Advanced Note: PACELC and Normal Operation

Even without network partitions, consistency costs latency. Making a write visible to all nodes *before* returning to the client requires waiting for those nodes to acknowledge. Systems that skip this have lower latency but weaker consistency.

See [CAP Theorem](01-cap-theorem.md) for the partition behavior and [Quorum and Tunable Consistency](04-quorum-and-tunable-consistency.md) for the practical mechanism to tune this trade-off.

## Where You'll See This

- **Database transaction settings**: Isolation level is set per-session or per-transaction in relational databases; the default varies by database and version
- **Distributed database tuning**: Quorum reads, consistency levels, and read/write concerns are all mechanisms for choosing a point on the consistency spectrum
- **Application design**: Read-your-writes consistency often requires routing reads to the same node as the preceding write (sticky sessions, primary reads)
- **Conflict resolution**: Eventually consistent systems need conflict resolution strategies when concurrent writes diverge -- see [ACID vs BASE](02-acid-vs-base.md)

---

**Next:** [Quorum and Tunable Consistency →](04-quorum-and-tunable-consistency.md)
