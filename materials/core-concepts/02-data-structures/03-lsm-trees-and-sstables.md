# LSM-Trees and SSTables

## The Problem

B-trees are excellent for read-heavy workloads: each lookup is O(log n) and range scans are fast. But for write-heavy workloads -- millions of sensor readings per second, high-frequency trading events, IoT telemetry -- B-trees hit a fundamental physical limit.

Every B-tree write requires:
1. Locating the correct page on disk (a seek)
2. Reading that page into memory
3. Modifying the page
4. Writing it back to disk

This involves **random I/O** -- the disk must jump to different locations for each write. On SSDs, random I/O throughput is ~10x lower than sequential I/O throughput. On HDDs, the difference is 100x. When you're writing millions of records per second, the disk becomes the bottleneck.

The question: can you build a storage structure that achieves high write throughput by converting random writes to sequential writes?

## The Solution

**Log-Structured Merge-trees (LSM-trees)** -- a storage architecture that never updates data in place. Instead, every write is an append. Reads are more complex but writes are blazingly fast: sequential appends are the fastest possible disk operation.

The tradeoff is intentional: sacrifice some read performance to unlock write throughput that is orders of magnitude higher than B-trees can achieve.

## How It Works

### The Write Path

```
Client Write
     │
     ▼
1. Write-Ahead Log (WAL)          ← sequential append to disk for durability
     │
     ▼
2. Memtable (in-memory)           ← sorted tree in RAM (red-black tree or skip list)
     │
     │  (when memtable reaches size threshold, e.g. 64MB)
     ▼
3. SSTable flush to disk          ← sorted, immutable file written sequentially
     │
     │  (background, periodically)
     ▼
4. Compaction                     ← merge multiple SSTables, remove deleted entries
```

**Step 1 -- Write-Ahead Log (WAL)**: Before touching anything else, append the write to a sequential log on disk. If the process crashes, the WAL can be replayed on restart to recover all confirmed writes. See [Write-Ahead Logs](../05-replication-and-availability/03-write-ahead-logs.md) for the general principle.

**Step 2 -- Memtable**: The write also lands in an in-memory sorted tree (the memtable). This is the "working set" -- all reads check here first. The memtable is fast because it's pure RAM.

**Step 3 -- SSTable flush**: When the memtable fills up (typically 32-256MB), it is flushed to disk as an **SSTable (Sorted String Table)** -- a sorted, immutable file. Immutable means: once written, never modified. The memtable is cleared and a new one starts. The flush is a sequential write -- the fastest possible disk operation.

**Step 4 -- Compaction**: Over time, many SSTables accumulate. A background process merges them: it performs a sorted merge (like merge sort), discards deleted records (marked by tombstones), and produces fewer, larger SSTables. Compaction is also sequential I/O.

### SSTables: Sorted String Tables

An SSTable is a sorted, immutable file of key-value pairs:

```
SSTable file layout:
┌────────────────────────────────────────┐
│ Data Block: sorted key-value pairs     │
│   key="order:001" → value={...}        │
│   key="order:002" → value={...}        │
│   key="order:003" → value={...}        │
│   ...                                  │
├────────────────────────────────────────┤
│ Index Block: sparse index for fast     │
│   seek within the file                 │
│   "order:001" → offset 0              │
│   "order:100" → offset 4096           │
├────────────────────────────────────────┤
│ Bloom Filter: probabilistic check      │
│   "is this key in this file at all?"   │
└────────────────────────────────────────┘
```

Because each SSTable is sorted, binary search within a file is O(log n). Because they're immutable, reads never block writes.

### The Read Path

Reads are more complex than writes:

1. Check the **memtable** (most recent writes are here)
2. Check **SSTables from newest to oldest** (stop at the first match)
3. Use **bloom filters** to skip SSTables that definitely don't contain the key (avoids unnecessary reads)

```
Read for key "order:042":
  ┌─────────────────────────────────────────────────────────┐
  │ Memtable: not found                                     │
  │ SSTable 5 (newest): bloom filter says NO → skip         │
  │ SSTable 4: bloom filter says MAYBE → binary search → NO │
  │ SSTable 3: bloom filter says MAYBE → binary search → YES│
  │   return value ✓                                        │
  └─────────────────────────────────────────────────────────┘
```

See [Probabilistic Structures](04-probabilistic-structures.md) for how bloom filters work.

### Compaction Strategies

Without compaction, you accumulate many SSTables and reads must check all of them. Compaction is the maintenance process that merges and prunes:

**Size-tiered compaction**: Merge SSTables of similar sizes. Produces large, infrequently rewritten files. Good for write throughput; can make reads slower temporarily.

**Leveled compaction**: Organize SSTables into levels (L0, L1, L2...). Each level is 10x larger than the previous. Merging is more frequent but reads only need to check one SSTable per level. Better read performance at the cost of higher write amplification.

```
Without compaction:
  SST1: {a→1, b→2}
  SST2: {b→3, c→4}    (b updated -- old value in SST1 is "stale")
  SST3: {a→deleted}   (tombstone)
  
After compaction:
  SST_merged: {b→3, c→4}    (a deleted, b has newest value)
```

## Trade-offs

**What you gain:**
- Write throughput orders of magnitude higher than B-trees on the same hardware
- Sequential I/O pattern is optimal for SSDs and HDDs alike
- Natural fit for append-heavy workloads (log data, time-series, event streams)

**What you give up:**
- **Read amplification**: A point lookup may need to check multiple SSTables. Bloom filters mitigate but don't eliminate this.
- **Write amplification**: Compaction re-writes data multiple times. A single user write may cause 10-30x more bytes written to disk over time (tunable by compaction strategy).
- **Space amplification**: Multiple versions of the same key exist until compaction runs. Disk usage is temporarily higher than the logical data size.

| Dimension | B-Tree | LSM-Tree |
|-----------|--------|----------|
| Write throughput | Moderate (random I/O) | High (sequential I/O) |
| Read throughput | High (direct lookup) | Moderate (check multiple SSTables) |
| Write amplification | Low | High (compaction) |
| Read amplification | Low | Moderate (mitigated by bloom filters) |
| Best for | Read-heavy (OLTP) | Write-heavy (time-series, logs) |

## Where You'll See This

- **Column-family stores** (Cassandra, HBase): LSM-trees are the core storage engine -- chosen specifically for write-heavy IoT, event, and time-series workloads
- **Embedded key-value engines** (RocksDB, LevelDB): Used inside many databases as the storage layer (CockroachDB, TiKV, MyRocks)
- **Search engines** (Elasticsearch/Lucene): Inverted indexes use an SSTable-like structure with periodic segment merges
- **Time-series databases** (InfluxDB, Prometheus): Append-only time-series data is a natural fit for LSM-tree write patterns

---

**Next:** [Probabilistic Structures →](04-probabilistic-structures.md)
