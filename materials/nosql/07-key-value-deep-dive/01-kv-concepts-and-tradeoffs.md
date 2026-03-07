---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Key-Value Stores: Concepts and Tradeoffs

```{note}
This lesson requires the Redis lab. Run `make lab-redis` before starting.
```

A key-value store is a database built around one operation: given a key, return the value. No joins, no aggregations, no filtering by field. Just a lookup. That constraint, which sounds like a limitation, is what makes key-value stores so fast and so scalable.

The right way to think about a key-value store is as a **dictionary at infrastructure scale** -- the same O(1) lookup you get from a Python `dict`, but distributed across machines, surviving restarts, and serving hundreds of thousands of requests per second.

This lesson is about the concepts: what problems key-value stores are designed for, what you give up, and what the key implementation decisions look like. Redis is our vehicle throughout -- but every concept here applies to any key-value store.

---

## The Simplicity Contract

When you use a key-value store, you agree to a contract: **you will always look up data by key**. In exchange, the store promises sub-millisecond latency and linear horizontal scalability.

This means the database never needs to scan, filter, sort, or join. The only question is: "what is the value for key X?" That's a single hash table lookup.

> **Core Concept:** See [Hash Tables](../../core-concepts/02-data-structures/01-hash-tables.md) for how a hash function maps keys to bucket indices for O(1) amortized lookup. The entire Redis keyspace is one giant hash table in memory.

The contract breaks down the moment you need to ask "give me all sessions for user 42" -- because there's no way to filter by the *contents* of a value. The key-value store doesn't know what's inside the value. You can only ask for things you already know the key for.

This forces a discipline: **you design your keys to support your access patterns**. The key is your only query mechanism.

```{code-cell} python
import redis
import time

r = redis.Redis(host="redis", port=6379, decode_responses=True)

# O(1) lookup -- same speed for 10 keys or 10 million keys
r.set("user:42:name", "Alice")
r.set("user:42:email", "alice@example.com")
r.set("user:43:name", "Bob")

start = time.monotonic()
name = r.get("user:42:name")
elapsed = (time.monotonic() - start) * 1000

print(f"GET user:42:name = {name!r}  ({elapsed:.3f}ms)")
print(f"Total keys: {r.dbsize()}")
```

---

## Why In-Memory?

Most key-value stores keep their entire dataset in RAM. This is an explicit design choice, not a limitation of implementation.

> **Core Concept:** See [I/O and Storage Fundamentals](../../core-concepts/01-complexity-and-performance/02-io-and-storage-fundamentals.md) for the latency gap between RAM and disk. RAM access is ~100ns; SSD is ~100µs; disk is ~10ms. A key-value store optimized for sub-millisecond latency has to live in RAM.

The consequence: dataset size is bounded by available RAM. Redis is typically deployed with 8-64GB of RAM per node. For data that fits in memory -- sessions, caches, counters, leaderboards -- this is not a problem. For terabytes of persistent data, you need a different tool.

Redis gives you a window into memory usage:

```{code-cell} python
info = r.info("memory")
print(f"Used memory:        {info['used_memory_human']}")
print(f"Peak memory:        {info['used_memory_peak_human']}")
print(f"Memory fragmentation: {info['mem_fragmentation_ratio']:.2f}")
```

---

## Persistence: Surviving Restarts

Pure in-memory storage means data is lost on restart. Redis offers two persistence mechanisms -- and this is a direct application of the write-ahead log concept.

> **Core Concept:** See [Write-Ahead Logs](../../core-concepts/05-replication-and-availability/03-write-ahead-logs.md) for the general pattern of logging writes before applying them, enabling crash recovery.

### RDB (Snapshot)

At configurable intervals, Redis forks and writes the entire in-memory dataset to a binary `.rdb` file. Fast to load on restart, but you lose all writes since the last snapshot.

```
Every 60s (if ≥1000 keys changed):
  fork() → child writes dataset to dump.rdb → parent continues serving
```

**Tradeoff:** Fast restarts (load snapshot once), but up to 60 seconds of data loss.

### AOF (Append-Only File)

Every write command is appended to a log file (`appendonly.aof`). On restart, Redis replays the log to reconstruct the dataset.

```
SET user:42:name "Alice"  → appended to aof file
INCR counter              → appended
DEL session:xyz           → appended
...
On restart: replay all commands from beginning
```

**Tradeoff:** Near-zero data loss (configurable to `fsync` every second or every write), but slower restarts as dataset grows.

### Which to use

| Scenario | Recommendation |
|----------|---------------|
| Pure cache (data re-populatable) | No persistence -- fastest |
| Sessions, rate limiters | AOF with `fsync everysec` |
| Production primary store | Both: AOF for durability + RDB for fast restart |

```{code-cell} python
# Check current persistence configuration
config = r.config_get("save")
aof = r.config_get("appendonly")
print(f"RDB save schedule: {config}")
print(f"AOF enabled:       {aof}")
```

---

## The Single-Threaded Event Loop

Redis processes commands in a single thread. This sounds like a performance problem but is actually the opposite.

A single thread means:
- **No locks needed** -- only one command executes at a time, so operations are naturally atomic
- **No context switching** -- the CPU spends all its time on useful work, not thread management
- **Predictable latency** -- no contention delays from lock contention

The bottleneck is not CPU (Redis is I/O bound, not compute bound). The single thread is almost never the limiting factor until you have extremely high key counts or use CPU-intensive commands like `SORT` on large lists.

```{code-cell} python
# Because Redis is single-threaded, INCR is atomic -- no race conditions
# even with many concurrent clients. This makes it ideal for counters.
r.set("page_views", 0)

# Simulate 10 increments
for _ in range(10):
    r.incr("page_views")

print(f"page_views: {r.get('page_views')}")  # always exactly 10
```

---

## Where Key-Value Stores Sit in CAP

> **Core Concept:** See [CAP Theorem](../../core-concepts/04-distributed-systems/01-cap-theorem.md) for the tradeoff between consistency, availability, and partition tolerance.

A single Redis instance is **CA**: consistent (only one copy of data) and available (no partition to worry about).

Redis Cluster is **CP** by default: when a network partition isolates a primary node, the affected slots become unavailable rather than serving potentially stale data. This is the right choice for a cache or session store -- serving wrong data silently is worse than returning an error.

> **ACID vs BASE:** Redis operations are atomic at the command level -- a `INCR` is always atomic. But Redis has no multi-key transactions in the traditional sense. It's BASE: individual operations are consistent, but there are no cross-key guarantees. See [ACID vs BASE](../../core-concepts/04-distributed-systems/02-acid-vs-base.md).

---

## The KV Store Spectrum

Key-value stores span a wide range of tradeoffs:

| Store | Storage | Durability | Speed | Best For |
|-------|---------|------------|-------|----------|
| **Memcached** | RAM only | None | Fastest | Pure caching |
| **Redis** | RAM + optional disk | RDB/AOF | Very fast | Caching, sessions, data structures |
| **RocksDB** | SSD (LSM-tree) | Full | Fast for writes | Embedded, large datasets |
| **DynamoDB** | SSD (managed) | Full | Fast | Managed, any scale |
| **etcd** | SSD (Raft) | Full | Moderate | Config, coordination |

Redis sits in the sweet spot: fast enough to be a cache, durable enough to be a primary store for the right use cases, and rich enough in data structures to solve problems that pure key-value stores can't.

---

**Next:** [Data Modeling Patterns →](02-data-modeling-patterns.md)

---

[← Back: Key-Value Stores Overview](../02-nosql-types/02-key-value-stores.md) | [Course Home](../README.md)
