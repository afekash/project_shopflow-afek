---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Cache Write Patterns

Cache-aside populates the cache on reads. But writes require their own strategy: when data changes in your database, what happens to the cached copy?

The previous lesson covered the read side of caching (cache-aside, TTL, expiration). This lesson covers the write side: **write-through** and **write-behind** -- two patterns that determine how writes flow between Redis and your source of truth.

> **Core Concept:** See [Caching Patterns](../../core-concepts/07-application-patterns/01-caching-patterns.md) for the general descriptions of write-through and write-behind, including their consistency and durability tradeoffs.

---

## Write-Through

Every write goes to both Redis and the database synchronously. The cache is always consistent with the source -- there is no window where the cached value is stale.

```
Write:
  1. Write to database (source of truth)
  2. Update the cache synchronously
  3. Return success when both succeed
```

```{code-cell} python
import redis
import json

r = redis.Redis(host="redis", port=6379, decode_responses=True)
r.flushdb()

def update_product_price(r, product_id: int, new_price: float):
    # Simulate writing to the source of truth first
    print(f"  DB: UPDATE products SET price={new_price} WHERE id={product_id}")

    # Update the cache synchronously -- use keepttl to preserve the existing expiry
    key = f"cache:product:{product_id}"
    if r.exists(key):
        cached = json.loads(r.get(key))
        cached["price"] = new_price
        r.set(key, json.dumps(cached), keepttl=True)
        print(f"  Cache: updated product:{product_id} price to {new_price}")
    else:
        print(f"  Cache: key not present, skipping")

# Populate cache first
r.set("cache:product:42", json.dumps({"id": 42, "name": "Laptop", "price": 1299.99}), ex=300)
print(f"Before: {json.loads(r.get('cache:product:42'))['price']}")

update_product_price(r, 42, 1199.99)
print(f"After:  {json.loads(r.get('cache:product:42'))['price']}")
```

**When to use write-through:**
- Reads vastly outnumber writes, so the extra write latency is acceptable
- Stale reads would cause business problems (pricing, inventory counts)
- The cached data is always predictably needed after a write

**Tradeoff:** Every write is slower (two synchronous writes). The cache fills with data that may never be read (you cache on write, even for unpopular keys).

---

## Write-Behind (Write-Back)

Writes go to Redis immediately and are asynchronously flushed to the database later. The cache absorbs write bursts that the database couldn't handle directly.

```
Write:
  1. Write to Redis (fast)
  2. Mark entry as "dirty"
  3. Return success immediately
  4. (Background) Flush dirty entries to database
```

```{code-cell} python
import time

def record_page_view(r, page: str):
    # Fast in-memory increment -- database not touched
    r.incr(f"analytics:views:{page}")

# Simulate high-frequency writes (counters, analytics)
pages = ["home", "products", "checkout", "home", "home", "products"]
for page in pages:
    record_page_view(r, page)

# Show what accumulated in Redis
keys = list(r.scan_iter("analytics:views:*"))
print("Accumulated in Redis (not yet flushed to DB):")
for key in sorted(keys):
    print(f"  {key}: {r.get(key)}")

# Background flush: atomically read and clear each counter
def flush_analytics_to_db(r):
    keys = list(r.scan_iter("analytics:views:*"))
    flushed = {}
    for key in keys:
        count = r.getdel(key)  # atomic get + delete
        page = key.split(":")[-1]
        flushed[page] = int(count)
        print(f"  DB: UPDATE page_stats SET views = views + {count} WHERE page = '{page}'")
    return flushed

print("\nFlushing to DB...")
flush_analytics_to_db(r)
print(f"Redis keys remaining: {r.dbsize()}")
```

**When to use write-behind:**
- Write-heavy workloads where every increment would overwhelm the database (counters, real-time analytics, shopping cart saves)
- Small data loss is acceptable (if Redis crashes before the flush, recent increments are lost)
- Writes can be batched (UPDATE ... SET views = views + 47 is cheaper than 47 individual updates)

**Tradeoff:** Data loss window between write and flush. Requires Redis to be persistent enough to survive the flush interval. Logic to track and flush dirty entries adds operational complexity.

---

## Choosing Between the Three Patterns

| Pattern | Write latency | Consistency | Data loss risk | Best for |
|---------|--------------|-------------|---------------|----------|
| **Cache-aside** | Fast (no cache write) | Eventual (TTL-based) | None (DB is source of truth) | Read-heavy, any data |
| **Write-through** | Slower (DB + cache) | Strong (always consistent) | None | Read-heavy, consistency critical |
| **Write-behind** | Fastest (cache only) | Eventual (async flush) | Yes (flush window) | Write-heavy, counters, analytics |

In practice: start with cache-aside. Move to write-through if you find yourself invalidating aggressively. Use write-behind only for high-frequency counters where the database can't keep up.

---

**Next:** [Replication →](06-replication.md)

---

[← Back: Caching and Expiration](04-caching-and-expiration.md) | [Course Home](../README.md)
