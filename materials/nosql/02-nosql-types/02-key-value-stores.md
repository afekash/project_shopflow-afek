# Key-Value Stores

A key-value store is the simplest NoSQL model: a giant dictionary (hash map) where you retrieve **values** by their **keys**.

```
Key                   →   Value
──────────────────────────────────────────────────────────
"session:user_42"     →   "{\"user_id\": 42, \"role\": \"admin\", \"expires\": 1709999999}"
"cache:product:1001"  →   "{\"name\": \"Laptop\", \"price\": 1299.99}"
"rate:ip:192.168.1.1" →   "47"
"feature:dark_mode"   →   "true"
```

The value is **opaque to the database** -- it just stores and retrieves bytes. The application decides what the value means. This simplicity makes key-value stores extraordinarily fast: there's almost nothing to do except a hash table lookup.

## Strengths and Weaknesses

| Aspect | Key-Value Store |
|--------|----------------|
| **Latency** | Sub-millisecond (in-memory implementations) |
| **Throughput** | 100k+ operations/sec per node |
| **Data model** | Flat key → opaque value |
| **Querying** | By key only -- no filtering by value |
| **Scaling** | Horizontal via consistent hashing / hash slots |
| **Best for** | Caching, sessions, rate limiting, leaderboards, pub/sub |
| **Avoid when** | Complex queries, relationships, large persistent datasets |

## Main Players

| Database | Notable For |
|----------|------------|
| **Redis** | Most popular; rich data structures, pub/sub, streams |
| **Memcached** | Simpler, multi-threaded, pure caching |
| **Amazon DynamoDB** | Managed; key-value + Global Secondary Indexes |
| **etcd** | Distributed config store, used by Kubernetes |

## Primary Use Cases

- **Caching** -- store expensive query results; serve from memory on repeat access
- **Session storage** -- fast TTL-based token → user data lookup
- **Rate limiting** -- atomic increment counters per time window
- **Real-time leaderboards** -- sorted sets with O(log n) rank updates
- **Pub/Sub messaging** -- decouple producers and consumers
- **Feature flags** -- instant reads for boolean feature toggles

## Deep Dive with Redis

The module below uses Redis to explore key-value stores in depth -- concepts, tradeoffs, data modeling patterns, caching, replication, and sharding.

**[→ Key-Value Deep Dive](../07-key-value-deep-dive/01-kv-concepts-and-tradeoffs.md)**

---

**Next:** [Column-Family Stores →](03-column-family-stores.md)

---

[← Back: Document Stores](01-document-stores.md) | [Course Home](../README.md)
