# I/O and Storage Fundamentals

## The Problem

Two operations each take 1 millisecond on your development machine. In production, one takes 1 millisecond and the other takes 1 second. They look identical in code. Why the 1000x difference?

The answer is almost always the same: one operation reads data from memory, the other reads data from disk -- or worse, from the network. Understanding the storage hierarchy is the single most important physical constraint that explains why data systems are designed the way they are.

## The Solution

Every computer has a hierarchy of storage with radically different latency and cost characteristics. The further down the hierarchy you go, the slower the access but the cheaper the cost per byte. The entire field of data systems engineering is essentially a series of clever tricks to keep hot data near the top of this hierarchy.

## How It Works

### The Storage Hierarchy

```
Storage Layer          Latency        Size (typical)    Cost/GB
──────────────────────────────────────────────────────────────
L1 CPU Cache           ~0.3 ns        ~100 KB           very high
L2 CPU Cache           ~3 ns          ~1 MB             high
L3 CPU Cache           ~10 ns         ~10-50 MB         high
RAM (DRAM)             ~80-100 ns     8 GB – 1 TB       moderate
SSD (NVMe, sequential) ~200 μs        512 GB – 8 TB     low
SSD (NVMe, random)     ~500 μs        same              low
HDD (sequential)       ~2-3 ms        1 TB – 20 TB      very low
HDD (random seek)      ~10 ms         same              very low
Network (LAN)          ~500 μs – 1 ms infinite          varies
Network (cross-region) ~30-150 ms     infinite          varies
```

**Key numbers to internalize:**
- RAM is ~1,000x faster than SSD
- Sequential SSD is ~10x faster than random SSD
- A disk seek (random I/O) can take 10ms -- the same time RAM could do 100,000 operations

### Random vs Sequential I/O

This single distinction drives the design of most storage data structures.

**Random I/O**: Accessing data at arbitrary locations on disk. Each access requires the disk head to move (HDD) or the controller to locate the correct block (SSD). This is slow because seek time dominates.

**Sequential I/O**: Reading or writing data in order, one block after the next. The disk head doesn't need to move (HDD) or the controller can prefetch (SSD). Sequential I/O can be 10-100x faster than random I/O on the same hardware.

```
Random reads of 1,000 scattered 4KB records:
  HDD:  1,000 × 10ms seek  = 10 seconds
  SSD:  1,000 × 0.5ms seek = 0.5 seconds

Sequential read of the same 4MB data:
  HDD:  4MB at 100MB/s     = 40 milliseconds
  SSD:  4MB at 3,000MB/s   = 1.3 milliseconds
```

This is why **append-only** designs are so common in data systems -- appending is always sequential. Updating records in-place is always random.

### Row-Oriented vs Column-Oriented Storage

The same principle applies within a database storage format.

**Row-oriented storage**: All columns of a row are stored contiguously on disk.

```
Row 1: [id=1, name="Alice", age=30, city="London", salary=80000]
Row 2: [id=2, name="Bob",   age=25, city="Paris",  salary=72000]
Row 3: [id=3, name="Carol", age=35, city="London", salary=95000]
```

- Good for: reading or writing complete rows (OLTP workloads -- INSERT, UPDATE, SELECT *)
- Bad for: reading a single column across many rows (must load all columns to get one)

**Column-oriented storage**: All values for one column are stored contiguously.

```
id column:     [1, 2, 3, ...]
name column:   ["Alice", "Bob", "Carol", ...]
age column:    [30, 25, 35, ...]
city column:   ["London", "Paris", "London", ...]
salary column: [80000, 72000, 95000, ...]
```

- Good for: `SELECT AVG(salary) FROM employees` -- reads only the salary column, skipping everything else
- Good for: compression (similar values in sequence compress well)
- Bad for: reading or writing complete rows (must read from every column file)

### The I/O Implication for Query Design

When you run a query that touches 1% of columns:
- Row-oriented: reads 100% of the data (all columns travel from disk)
- Column-oriented: reads ~1% of the data (only the needed column files)

At scale, this difference is not a performance optimization -- it's the difference between a query finishing in 10 seconds or 16 minutes.

`SELECT *` is an anti-pattern specifically because it defeats column-oriented storage: it forces the system to read every column even when the application only needs two of them.

## Trade-offs

| Design Choice | Faster For | Slower For |
|---------------|-----------|-----------|
| In-memory storage | Everything | Limited by RAM size and cost |
| Row-oriented | Write single records, read full records | Aggregate queries over one column |
| Column-oriented | Aggregate queries, analytics | Write or read individual records |
| Sequential writes | Throughput (append-only logs) | Point lookups (must scan or index) |
| Random access structures (B-trees) | Point lookups and range scans | Write throughput (random I/O per write) |

## Where You'll See This

- **LSM-trees** (Cassandra, RocksDB): Convert random writes to sequential appends -- see [LSM-Trees and SSTables](../02-data-structures/03-lsm-trees-and-sstables.md)
- **B-trees** (most SQL databases, MongoDB): Sorted structure for point and range lookups; accepts the random I/O cost for writes -- see [Trees for Storage](../02-data-structures/02-trees-for-storage.md)
- **Column-oriented databases** (Redshift, BigQuery, Parquet files): Pure column storage for analytics workloads
- **Write-ahead logs** (PostgreSQL, MySQL, Cassandra): Sequential append for crash safety, then random I/O for the actual data structure -- see [Write-Ahead Logs](../05-replication-and-availability/03-write-ahead-logs.md)
- **Data lake file formats** (Parquet, ORC): Column-oriented file format that makes analytics queries read a fraction of the data
- **Bloom filters**: Skip disk reads entirely when data is provably absent -- see [Probabilistic Structures](../02-data-structures/04-probabilistic-structures.md)

---

**Next:** [Hash Tables →](../02-data-structures/01-hash-tables.md)
