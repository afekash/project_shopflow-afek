# Write-Ahead Logs

## The Problem

Your system crashes mid-operation. The process was updating a B-tree page -- it had read the page into memory, modified it, and was about to write it back to disk when the power failed. The in-memory state is gone. The on-disk state is partially overwritten. The data structure is corrupt.

Even with modern SSDs, a write to disk is not atomic at the page level. A 16KB B-tree page write can be interrupted after 4KB, leaving a partially-written, invalid page. Without a recovery mechanism, any crash during a write risks data corruption.

More broadly: how do you build a system that can always recover to a consistent state after a crash, without paying the performance cost of waiting for every write to be fully flushed to disk?

## The Solution

**Write-Ahead Logging (WAL)** -- before applying any change to the main data structure, first append a record of the intended change to a sequential log. Only after the log entry is safely on disk do you apply the change to the main structure.

On crash: replay the log to reconstruct any changes that were recorded but not yet fully applied.

The key insight: a sequential append to the log is fast (sequential I/O) and atomic at the page level (a log entry fits in one write). Applying the change to the main structure can then happen in the background, at any time, because the log always lets you redo it.

## How It Works

### The WAL Principle

```
Without WAL:
  Client write → modify B-tree page in memory → write to disk
  Crash between steps: ??? unknown state, possibly corrupt

With WAL:
  Client write → append to log → fsync log → modify data structure
  Crash at any point: replay the log, recover to correct state
```

**The guarantee**: If the log entry made it to disk before the crash, the change can be fully replayed on restart. If the log entry didn't make it to disk, the change never happened as far as the log is concerned -- the write was never confirmed to the client.

### Log Entry Format

A WAL entry is a compact, ordered record:

```
Log Sequence Number (LSN)  │ Transaction ID │ Operation │ Data
───────────────────────────┼────────────────┼───────────┼─────────────────────
000001                     │ txn_42         │ BEGIN     │
000002                     │ txn_42         │ INSERT    │ table=orders, row={...}
000003                     │ txn_42         │ UPDATE    │ table=accounts, id=1, balance=900→800
000004                     │ txn_42         │ COMMIT    │
000005                     │ txn_43         │ BEGIN     │
000006                     │ txn_43         │ UPDATE    │ table=accounts, id=2, balance=200→300
000007                     │ txn_43         │ COMMIT    │
```

The **COMMIT** entry is the point of truth: once COMMIT is durably in the log, the transaction is committed, regardless of whether the data pages have been updated yet. Replaying from the log after a crash will reconstruct the committed state.

### Crash Recovery via Log Replay

On startup after a crash, the system scans the WAL:

```
1. Find the last checkpoint (a point where all in-memory data was flushed to disk)
2. Replay all log entries after the checkpoint
3. REDO: apply all operations from committed transactions
4. UNDO: roll back any transactions that have BEGIN but no COMMIT
         (the transaction was in-flight when the crash occurred)
5. Database is now in a consistent state
```

```
Log after a crash:
  LSN 100: txn_10 COMMIT        → redo (was committed)
  LSN 101: txn_11 BEGIN         → undo (no commit found → was in-flight)
  LSN 102: txn_11 UPDATE ...    → undo
  LSN 103: txn_12 BEGIN         → undo
  LSN 104: txn_12 INSERT ...    → undo
  LSN 105: [crash here]

Recovery:
  Redo LSN 100 (txn_10's committed changes) ✓
  Undo LSNs 101-102 (txn_11, uncommitted) ✓
  Undo LSNs 103-104 (txn_12, uncommitted) ✓
  Database consistent.
```

### Log-Based Replication

The WAL is not just for crash recovery -- it's also a natural replication mechanism. Secondary nodes can tail the primary's WAL and apply the same operations:

```
Primary:                           Secondary:
  Client → write → WAL → data       ← tail WAL → apply operations → own data copy
                    │                                ↑
                    └─────── stream log entries ─────┘
```

This is exactly how primary-secondary replication works in most database systems. The replication log and the crash recovery log are the same log -- read for two different purposes.

This gives you a useful property: a replica that falls behind can simply replay the log from where it left off, catching up without a full data copy (as long as the log hasn't been truncated past the point of divergence).

### Log Compaction and Truncation

Logs grow without bound. Two strategies for managing size:

**Checkpointing**: Periodically, the system writes all in-memory data pages to disk (a checkpoint). Log entries before the checkpoint are no longer needed for crash recovery and can be deleted. The log only needs to retain entries after the last checkpoint.

```
           Checkpoint N     Checkpoint N+1
                │                │
────────────────▼────────────────▼──────────────────►
  [old entries] [entries since N] [entries since N+1] [current]
                ↑                 ↑
          deletable             deletable after next checkpoint
```

**Log compaction (for key-value logs)**: In systems where the log is the primary data store (like LSM-tree memtables or event sourcing systems), compaction merges multiple updates to the same key, keeping only the latest value. This reduces replay time and disk usage.

### Append-Only as a Design Philosophy

WAL is a specific application of a more general principle: **append-only logs are safe, durable, and fast**.

Because sequential writes are the fastest disk operation (see [I/O and Storage Fundamentals](../01-complexity-and-performance/02-io-and-storage-fundamentals.md)), an append-only log can absorb writes at very high throughput. The log is the source of truth; the main data structure is a derived view that can always be reconstructed from the log.

This philosophy appears at multiple scales:
- **WAL in databases**: Crash recovery for the storage engine
- **Oplog/binlog in replication**: Log as the replication stream
- **Immutable data lake storage**: Files are never updated, only new versions appended
- **Event sourcing**: Application state is derived from an append-only event log

## Trade-offs

**What you gain:**
- Crash safety: committed data survives any failure
- Fast writes: sequential log append is much faster than random B-tree page update
- Replication: the log is a natural replication stream
- Point-in-time recovery: replay the log to any past LSN

**What you give up:**
- Every write incurs a log append overhead (typically small compared to data write)
- Log takes disk space and must be managed (checkpointing, truncation)
- Log replay time after a crash (proportional to log volume since last checkpoint)

## Where You'll See This

- **Relational databases** (PostgreSQL WAL, MySQL binlog, SQL Server transaction log): WAL is the standard mechanism for durability and replication in every production relational database
- **Column-family stores** (Cassandra commit log, HBase WAL): The WAL absorbs writes before the memtable, providing durability for the in-memory LSM-tree write path
- **In-memory databases** (Redis AOF -- Append-Only File): Replays command log on restart to reconstruct the dataset; RDB snapshots serve as checkpoints
- **Distributed consensus** (Raft log, Paxos log): The consensus log IS the WAL -- replicated across nodes and replayed on leader failover
- **Data lake transactions** (Delta Lake, Apache Iceberg): Transaction logs bring ACID semantics to object storage by implementing WAL principles on top of files

---

**Next:** [Schema Strategies →](../06-architecture-patterns/01-schema-strategies.md)
