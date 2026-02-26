# Key-Value Stores

## What Is a Key-Value Store?

A key-value store is the simplest form of NoSQL database. The data model is exactly what it sounds like: a giant dictionary (hash map) where you look up **values** by their **keys**.

```
Key                   →   Value
──────────────────────────────────────────────────────────
"session:user_42"     →   "{\"user_id\": 42, \"role\": \"admin\", \"expires\": 1709999999}"
"cache:product:1001"  →   "{\"name\": \"Laptop\", \"price\": 1299.99}"
"rate:ip:192.168.1.1" →   "47"
"feature:dark_mode"   →   "true"
"leaderboard:global"  →   [sorted set of user_id → score pairs]
```

The value is **opaque to the database** -- the database doesn't know or care what's inside. It just stores and retrieves bytes. The application is responsible for interpreting the value.

This simplicity is the key-value store's superpower: it can be extraordinarily fast because there's almost nothing to do.

## How Key-Value Stores Work Internally

### In-Memory Hash Table

The most common implementation stores all data in memory as a hash table. A hash table lookup is O(1) -- constant time regardless of how many keys exist. This is why Redis can serve hundreds of thousands of requests per second from a single machine.

> **Core Concept:** See [Hash Tables](../../core-concepts/02-data-structures/01-hash-tables.md) for how hash functions, collision handling, and O(1) amortized lookup work.

**Why a key-value store chose a hash table:** Key-value access patterns are pure lookups -- the entire value proposition is "give me the value for this key." O(1) is the best possible complexity for that operation. Unlike SQL indexes which need B-trees for range scans and sorting, a key-value store only needs to answer one question. A hash table answers that question faster than any other structure.

```
Key → Hash Function → Bucket Index → Value

"session:user_42"
         │
    hash("session:user_42") = 3,842,917,201
         │
    3,842,917,201 % num_buckets = 47
         │
    bucket[47] → stored value
```

### Persistence Options (Redis)

Pure in-memory storage is fast but data is lost on restart. Redis offers two persistence strategies:

**RDB (Snapshot)**
Periodically write the entire in-memory dataset to disk as a binary snapshot. Fast restarts but may lose data written since the last snapshot.

**AOF (Append-Only File)**
Every write command is appended to a log file. On restart, replay the log to reconstruct the dataset. Slower but more durable (configurable to fsync every second, or every write).

**Combined (recommended for production)**: Use both. RDB for fast restarts, AOF for minimal data loss.

### Consistent Hashing for Horizontal Scaling

When you have multiple key-value nodes, how do you decide which node stores which key? Naive approach: `node_index = hash(key) % num_nodes`. Problem: when you add or remove a node, the modulo changes and almost every key needs to move.

> **Core Concept:** See [Consistent Hashing](../../core-concepts/03-scaling/03-consistent-hashing.md) for the full virtual ring mechanism, virtual nodes, and the math behind why only 1/N of keys move when a node joins or leaves.

**Why Redis Cluster chose consistent hashing:** Redis keys are completely independent -- no relationships, no joins, no foreign keys. This makes consistent hashing ideal: each key belongs to exactly one node, and cross-node operations are never needed. Compare this to a relational database where rows from different tables must be co-located for JOINs to work efficiently. Because Redis has no join requirement, adding nodes is as simple as moving some keys -- no query routing complexity.

Redis Cluster uses a variant called **hash slots** -- 16,384 slots distributed across nodes. Each key maps to a slot (`HASH_SLOT = CRC16(key) % 16384`), and the cluster configuration tracks which node owns which slots.

## Redis Data Structures

Redis goes beyond simple string values. It provides rich data structures that blur the line between key-value store and mini-database:

### Strings
```bash
SET user:42:name "Alice"
GET user:42:name       # "Alice"
INCR user:42:login_count   # atomic increment, great for counters
```

### Lists (doubly-linked list)
```bash
LPUSH tasks "task_3"   # push to left
RPUSH tasks "task_4"   # push to right
BRPOP tasks 0          # blocking pop from right (job queue pattern)
```

### Sets (unique values)
```bash
SADD online_users "user_1" "user_2" "user_3"
SISMEMBER online_users "user_2"   # O(1) membership check
SCARD online_users                # count
SINTER online_users premium_users # intersection (who's online AND premium?)
```

### Sorted Sets (score-ordered set)
```bash
ZADD leaderboard 9850 "alice"
ZADD leaderboard 9200 "bob"
ZADD leaderboard 9500 "carol"
ZRANGE leaderboard 0 2 WITHSCORES REV   # top 3: alice, carol, bob
ZRANK leaderboard "bob"                  # rank of bob
```

Sorted sets are the magic behind real-time leaderboards -- O(log n) inserts, O(log n + k) range queries.

### Hashes (nested key-value)
```bash
HSET user:42 name "Alice" email "alice@example.com" plan "enterprise"
HGET user:42 name        # "Alice"
HMGET user:42 name email # ["Alice", "alice@example.com"]
HINCRBY user:42 login_count 1
```

### HyperLogLog (cardinality estimation)
```bash
PFADD page_visitors:home "user_1" "user_2" "user_3"
PFCOUNT page_visitors:home   # approximate unique visitor count, 0.81% error, uses 12KB regardless of cardinality
```

Used for analytics where exact counts aren't needed: unique visitors, unique searches.

### Streams (append-only log)
```bash
XADD events "*" type "click" user "user_42" element "buy_button"
XREAD COUNT 100 STREAMS events 0   # read from offset 0
XREADGROUP GROUP processors consumer1 COUNT 10 STREAMS events ">"   # consumer groups
```

Redis Streams are similar to Kafka topics but lighter-weight. Good for event sourcing within a single application.

### TTL (Time-to-Live)
```bash
SET session:token_xyz "{...}" EX 3600   # expires in 3600 seconds
TTL session:token_xyz                    # seconds remaining
```

TTL is fundamental to caching -- expired keys are automatically deleted by Redis's lazy expiration + background cleanup.

## Strengths

**Sub-millisecond latency**
In-memory storage with simple lookups. Redis routinely achieves < 1ms p99 latency.

**Massive throughput**
A single Redis instance handles 100,000+ operations per second. Redis Cluster scales linearly across nodes.

**Simple, predictable API**
GET, SET, DEL. The surface area is tiny and operations are well-understood.

**Atomic operations**
Redis is single-threaded for command execution, so all operations are naturally atomic. `INCR`, `LPUSH`, and other operations cannot be partially applied.

**Rich built-in data structures**
Sorted sets, streams, and hyperloglogs give you capabilities that would otherwise require custom application logic.

## Weaknesses

**No querying by value**
You can only look up by key. If you need to find all sessions for a specific user ID, you need to design your key structure to support that (e.g., maintain an index set `user:42:sessions`).

**Limited data modeling**
No relationships, no nesting beyond one level of hash fields. Complex entities require multiple keys and manual consistency management.

**Memory bound**
Storing everything in RAM limits total dataset size. Large datasets are expensive. Redis 7+ supports tiered storage, but this is still relatively new.

**No complex queries**
No aggregations, no filtering across keys, no joins. Redis Modules (RediSearch, RedisJSON) add some of this, but they change the cost/complexity profile.

## Main Players

| Database | Notable For |
|----------|------------|
| **Redis** | Most popular, richest data structures, pub/sub, streams, modules |
| **Memcached** | Simpler than Redis, multi-threaded, pure caching |
| **Amazon DynamoDB** | Managed service, scales to any size, also supports GSIs for rich queries |
| **etcd** | Distributed configuration store, used by Kubernetes |
| **Amazon ElastiCache** | Managed Redis/Memcached on AWS |

**DynamoDB** deserves special mention: it is technically a key-value store (each item is looked up by primary key) but adds **Global Secondary Indexes (GSIs)** and **Local Secondary Indexes (LSIs)**, making it a "key-value plus" that can handle some query patterns that pure key-value stores cannot.

## Primary Use Cases

**Caching**
Store the results of expensive database queries or API calls. Serve subsequent requests from cache. When the cache expires (TTL), fetch fresh data and re-cache.

```python
# Cache-aside pattern
result = redis.get(f"product:{product_id}")
if result is None:
    result = postgres.query("SELECT * FROM products WHERE id = %s", product_id)
    redis.set(f"product:{product_id}", json.dumps(result), ex=300)  # cache 5 min
return json.loads(result)
```

**Session Storage**
Web sessions are naturally key-value (session token → user data). Redis is perfect: fast lookup, TTL handles expiration, in-memory means low latency.

**Rate Limiting**
```bash
# Allow 100 requests per minute per IP
INCR rate:192.168.1.1:2024010110   # current minute bucket
EXPIRE rate:192.168.1.1:2024010110 60
# if count > 100: reject request
```

**Real-Time Leaderboards**
Sorted sets give you O(log n) rank updates and rank queries -- ideal for gaming leaderboards, developer API usage rankings, or recommendation rankings.

**Feature Flags**
```bash
SET feature:dark_mode "true"
SET feature:new_checkout "false"
```

**Pub/Sub Messaging**
```bash
PUBLISH channel:notifications '{"user": 42, "msg": "Your order shipped"}'
SUBSCRIBE channel:notifications   # other services listen
```

## At Scale

- **Redis Cluster**: Data partitioned across multiple nodes using hash slots. Supports up to 1000 nodes.
- **Redis Sentinel**: Automatic failover for a single Redis instance (no sharding, just HA)
- **Read replicas**: Redis supports replica nodes that serve reads, offloading the primary

In production at companies like GitHub, Twitter, and Airbnb, Redis handles billions of operations per day. The typical pattern is Redis as the caching/session layer in front of a persistent database (PostgreSQL, MongoDB).

## Summary

| Aspect | Key-Value Store |
|--------|----------------|
| Data model | Flat key → value pairs |
| Schema | None -- values are opaque bytes |
| Scaling | Horizontal via consistent hashing |
| Consistency | Tunable (Redis: eventual with persistence) |
| Query | By key only (no value querying) |
| Latency | Sub-millisecond |
| Best for | Caching, sessions, rate limiting, leaderboards, pub/sub |
| Avoid when | Complex queries, relationships, large persistent datasets |

---

**Next:** [Column-Family Stores →](03-column-family-stores.md)

---

[← Back: Document Stores](01-document-stores.md) | [Course Home](../README.md)
