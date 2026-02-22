# ACID vs BASE

## The Problem

Multiple clients are writing to your database simultaneously. Client A is transferring $100 from Account 1 to Account 2 -- a two-step operation. Client B reads Account 1 between Client A's two steps. What does Client B see?

Without careful coordination, Client B might see $100 debited from Account 1 but not yet credited to Account 2 -- money that appears to have vanished. Or worse, two concurrent transfers might both succeed, overdrawing the account.

How you answer this question -- how aggressively you prevent these anomalies -- defines whether your system is ACID or BASE.

## The Solution

Two opposing philosophies:

- **ACID** (pessimistic): assume conflicts will happen. Lock or coordinate to guarantee correctness at all times.
- **BASE** (optimistic): assume conflicts are rare. Proceed without coordination, reconcile when conflicts are detected.

Neither is universally better. The right choice depends entirely on whether your use case requires guaranteed correctness at the cost of throughput, or can tolerate temporary inconsistency for the benefit of availability and scale.

## How It Works

### ACID

**Atomicity**: A transaction is all-or-nothing. If any step fails, the entire transaction is rolled back. No partial writes are ever visible to other transactions.

```
Transfer $100: Account A → Account B

Step 1: Debit Account A: balance -= 100
Step 2: Credit Account B: balance += 100

If Step 2 fails: Step 1 is automatically undone.
No transaction ever sees money debited but not credited.
```

**Consistency**: The database enforces its rules (constraints, foreign keys, data types) at all times. A transaction that would violate a constraint is rejected entirely.

**Isolation**: Concurrent transactions don't interfere with each other. Each transaction executes as if it were the only one running. The *level* of isolation is configurable (see [Consistency Models](03-consistency-models.md) for the isolation spectrum).

**Durability**: Once a transaction is committed, it survives crashes. The database uses a write-ahead log (see [Write-Ahead Logs](../05-replication-and-availability/03-write-ahead-logs.md)) to ensure committed data can always be recovered.

```python
# ACID transaction: bank transfer
# Either both operations commit, or neither does
BEGIN TRANSACTION;
  UPDATE accounts SET balance = balance - 100 WHERE id = 'alice';
  UPDATE accounts SET balance = balance + 100 WHERE id = 'bob';
COMMIT;
-- atomically visible to all readers immediately after COMMIT
```

**What ACID requires:**
- Locks or optimistic concurrency control to isolate concurrent transactions
- Write-ahead logging for durability
- Constraint validation before commit
- On a single node: straightforward. Across multiple nodes: requires distributed protocols (2-phase commit) which are expensive and reduce availability.

### BASE

Coined as a deliberate contrast to ACID:

**Basically Available**: The system guarantees availability, even at the cost of consistency. Requests are served even when some nodes are unavailable or partitioned.

**Soft state**: The database state may change without new input -- background synchronization, conflict resolution, and replication happen asynchronously. The system is always in transition.

**Eventually consistent**: Given no new updates, all nodes will eventually converge to the same state. There is no guarantee of when -- it could be milliseconds or seconds -- but eventually all nodes agree.

```python
# BASE: social media post like (Cassandra-style)
# Write to the local node; other nodes sync asynchronously
INSERT INTO post_likes (post_id, user_id, liked_at)
VALUES ('post_123', 'user_42', NOW());
-- Succeeds immediately on the local node
-- Replicates to other nodes in the background
-- For a brief period, Node B might show 1,041 likes while Node A shows 1,042
-- Eventually all nodes converge to 1,042
```

**What BASE enables:**
- No locking across nodes: every write succeeds locally, no waiting for other nodes
- High throughput: no coordination overhead between write and acknowledgment
- High availability: the system serves requests regardless of partition state
- Cost: application must handle the possibility of reading stale data

### The Core Trade-off

```
                 ACID                         BASE
──────────────────────────────────────────────────────────
Correctness    Always enforced               Eventually enforced
Throughput     Limited by coordination       High (no coordination)
Availability   May refuse during partition   Always available
Latency        Higher (wait for consensus)   Low (local write)
Complexity     Database handles it           Application must handle it
Scale          Hard to distribute            Designed for distribution
```

### When to Use Each

**Use ACID when:**
- Money changes hands (transfers, payments, billing)
- Inventory management (can't oversell)
- Seat reservations (can't double-book)
- Any operation where partial state is unacceptable and correctness is non-negotiable

**Use BASE when:**
- Social features (likes, follows, activity feeds)
- Analytics and metrics (approximate counts are fine)
- Caches (stale data is tolerable)
- High-throughput append-only workloads (event logs, IoT sensors)
- Any operation where a brief window of inconsistency causes no real harm

**The nuanced reality**: Many modern systems implement both. A system might use ACID transactions for the core financial operations but BASE eventually-consistent replication for read replicas that serve analytics queries. The transaction boundary defines where the ACID guarantee applies; outside that boundary, consistency can be relaxed.

## Where You'll See This

- **Relational databases**: ACID by default -- the entire engine is built around atomicity and isolation
- **Distributed databases**: BASE by default for replication, but many offer ACID for single-shard transactions and distributed transactions via 2-phase commit
- **Isolation levels**: The spectrum from READ UNCOMMITTED to SERIALIZABLE is the ACID isolation trade-off in detail -- see [Consistency Models](03-consistency-models.md)
- **Conflict resolution**: BASE systems must handle write conflicts -- last-writer-wins, application merge, CRDTs (conflict-free replicated data types)
- **Eventual consistency in practice**: DNS propagation, social media feeds, shopping cart contents -- all BASE, and we accept this without thinking about it

---

**Next:** [Consistency Models →](03-consistency-models.md)
