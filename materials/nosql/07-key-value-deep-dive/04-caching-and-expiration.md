---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Caching and Expiration

Caching is the most common reason to reach for Redis. An application has a slow operation -- a database query, an external API call, a computation -- and repeats it many times. Redis sits in front of the slow operation, serving results from memory so the expensive call only happens occasionally.

This lesson is about how caching works on the read side: the cache-aside pattern, how TTL and expiration actually work internally, eviction policies when memory is full, and the cache stampede problem.

> **Core Concept:** See [Caching Patterns](../../core-concepts/07-application-patterns/01-caching-patterns.md) for the full taxonomy: cache-aside, write-through, write-behind, eviction policies, thundering herd, and cold start. This lesson focuses on how the read-side concepts look in Redis.

---

## The Fundamental Pattern: Cache-Aside

Cache-aside (also called lazy population) is the pattern most Redis users start with. The application checks the cache on every read; on a miss, it fetches from the source and populates the cache.

```{code-cell} python
import redis
import json
import time

r = redis.Redis(host="redis", port=6379, decode_responses=True)
r.flushdb()

# Simulate a slow database
def fetch_from_db(product_id: int) -> dict:
    time.sleep(0.05)  # 50ms "database" query
    return {"id": product_id, "name": f"Product {product_id}", "price": 99.99}

def get_product(r, product_id: int, ttl: int = 300) -> dict:
    key = f"cache:product:{product_id}"
    cached = r.get(key)
    if cached:
        return json.loads(cached)

    result = fetch_from_db(product_id)
    r.set(key, json.dumps(result), ex=ttl)
    return result

# First call: cache miss (slow)
start = time.monotonic()
product = get_product(r, 42)
print(f"First call (miss):  {(time.monotonic()-start)*1000:.1f}ms -> {product['name']}")

# Second call: cache hit (fast)
start = time.monotonic()
product = get_product(r, 42)
print(f"Second call (hit):  {(time.monotonic()-start)*1000:.1f}ms -> {product['name']}")

print(f"TTL remaining: {r.ttl('cache:product:42')}s")
```

The TTL is the key mechanism: after 300 seconds, the cached entry disappears and the next request triggers a fresh database fetch.

---

## TTL: How Expiration Actually Works

Setting a TTL is not just a hint -- Redis actively manages expiration, but not in the way you might expect.

Redis uses a two-stage expiration strategy:

**1. Lazy expiration:** When a key is accessed, Redis checks if it has expired. If yes, delete it and return nil. This means an expired key occupies memory until it's next accessed.

**2. Active cleanup:** Redis runs a background job that randomly samples a small percentage of keys with TTLs every 100ms. If a sampled key has expired, it's deleted. This ensures stale keys are eventually removed even if never accessed.

The consequence: an expired key may sit in memory for a few hundred milliseconds after its TTL. For strict memory management, be aware that `maxmemory` includes keys that are technically expired but not yet cleaned up.

```{code-cell} python
r.set("temp:key", "value", ex=5)

print(f"After set:    TTL={r.ttl('temp:key')}s, exists={r.exists('temp:key')}")
time.sleep(2)
print(f"After 2s:     TTL={r.ttl('temp:key')}s, exists={r.exists('temp:key')}")

# TTL of -1 means no expiry set
r.set("permanent:key", "value")
print(f"No TTL:       TTL={r.ttl('permanent:key')} (-1 = no expiry)")

# TTL of -2 means key doesn't exist
print(f"Missing key:  TTL={r.ttl('nonexistent:key')} (-2 = not found)")
```

---

## Eviction: When Memory Is Full

If Redis reaches its `maxmemory` limit and a new write arrives, it must either reject the write or evict an existing key. The configured `maxmemory-policy` decides which.

> **Core Concept:** See [Caching Patterns -- Eviction Policies](../../core-concepts/07-application-patterns/01-caching-patterns.md) for the conceptual tradeoffs between LRU, LFU, and other strategies.

| Policy | What Gets Evicted | Use When |
|--------|-------------------|----------|
| `noeviction` | Nothing (writes fail) | You need to know when memory is full |
| `allkeys-lru` | Least recently used (any key) | General caching with mixed TTLs |
| `volatile-lru` | Least recently used (TTL keys only) | Mix of cache keys (TTL) and persistent keys (no TTL) |
| `allkeys-lfu` | Least frequently used (any key) | Skewed workloads with hot keys |
| `volatile-ttl` | Key closest to expiry | Prioritize freshness |
| `allkeys-random` | Random | Uniform access patterns |

The most common production choice is `allkeys-lru`: any key can be evicted, so Redis works as a pure LRU cache. Use `volatile-lru` when your Redis instance holds both cache keys (with TTL) and persistent data (without TTL) -- this protects persistent keys from eviction.

```{code-cell} python
policy = r.config_get("maxmemory-policy")
maxmem = r.config_get("maxmemory")
print(f"Eviction policy: {policy['maxmemory-policy']}")
print(f"Max memory:      {maxmem['maxmemory']} bytes (0 = unlimited)")
```

---

## Cache Stampede: The Thundering Herd in Practice

When a popular cached key expires and many concurrent requests all miss simultaneously, they all hit the database at once.

> **Core Concept:** See [Caching Patterns -- Thundering Herd](../../core-concepts/07-application-patterns/01-caching-patterns.md) for the full problem description and solutions.

The fix: use a distributed lock. Only one request regenerates the cache; others wait.

```{code-cell} python
import threading

def get_with_lock(r, key: str, ttl: int = 60):
    cached = r.get(key)
    if cached:
        return json.loads(cached), "hit"

    lock_key = f"lock:{key}"
    # SET NX EX: set only if not exists (atomic compare-and-set)
    acquired = r.set(lock_key, "1", nx=True, ex=5)

    if acquired:
        time.sleep(0.05)  # simulate DB query
        data = {"result": "fresh_data", "generated_at": time.time()}
        r.set(key, json.dumps(data), ex=ttl)
        r.delete(lock_key)
        return data, "miss+regenerated"
    else:
        for _ in range(10):
            time.sleep(0.01)
            cached = r.get(key)
            if cached:
                return json.loads(cached), "waited"
        return None, "timeout"

results = []
def worker():
    data, status = get_with_lock(r, "hot:key")
    results.append(status)

# 10 concurrent requests for same expired key
threads = [threading.Thread(target=worker) for _ in range(10)]
[t.start() for t in threads]
[t.join() for t in threads]

from collections import Counter
print("Results:", dict(Counter(results)))
# Expected: 1 regenerated, rest waited (only 1 DB query)
```

---

## Measuring Cache Effectiveness

A cache that's 20% effective (80% miss rate) adds latency without helping. Redis tracks hit/miss stats that you should monitor in production.

```{code-cell} python
r.config_resetstat()

for i in range(20):
    r.set(f"tracked:{i}", f"value_{i}", ex=60)

for i in range(30):  # 20 hits + 10 misses
    r.get(f"tracked:{i}")

stats = r.info("stats")
hits = stats["keyspace_hits"]
misses = stats["keyspace_misses"]
total = hits + misses
hit_rate = hits / total * 100 if total > 0 else 0

print(f"Keyspace hits:   {hits}")
print(f"Keyspace misses: {misses}")
print(f"Hit rate:        {hit_rate:.1f}%")
print()
print("Rule of thumb: production caches should be > 90% hit rate.")
print("< 80% means your TTLs are too short or your key design needs review.")
```

---

**Next:** [Cache Write Patterns →](05-cache-write-patterns.md)

---

[← Back: Common Patterns](03-common-patterns.md) | [Course Home](../README.md)
