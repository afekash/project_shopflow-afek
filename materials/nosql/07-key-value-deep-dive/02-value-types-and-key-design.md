---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Value Types and Key Design

A key-value store's entire query interface is: look up by key. That means **your key design is your data model**. Before writing any data, you need to answer: what are the access patterns, and how do I design keys that support them?

Redis adds a second dimension to this: the **value type**. Unlike stores that hold opaque bytes, Redis understands the structure of common data types and provides operations that work natively on them. The choice of value type is as important as the choice of key name.

---

## Key Naming: Your Only Schema

Keys are arbitrary strings, but a naming convention is essential. The standard Redis convention is colon-separated namespacing:

```
entity:identifier:field

user:42:name
user:42:email
session:abc123
rate:ip:192.168.1.1:2024010110
cache:product:1001
leaderboard:global
```

This is not enforced by Redis -- it's a discipline you impose. Benefits:
- **Readable** -- keys are self-documenting
- **Scannable** -- `SCAN 0 MATCH user:42:*` finds all keys for user 42
- **Collision-safe** -- `user:42` and `product:42` are different namespaces

```{code-cell} python
import redis
import json

r = redis.Redis(host="redis", port=6379, decode_responses=True)
r.flushdb()  # start clean

# Good key naming: entity:id:field
r.set("user:42:name", "Alice")
r.set("user:42:email", "alice@example.com")
r.set("product:1001:name", "Laptop")
r.set("product:1001:price", "1299.99")

# Scan all keys for user 42
keys = list(r.scan_iter("user:42:*"))
print("user:42 keys:", sorted(keys))
```

---

## Value Types: Beyond Simple Strings

Most key-value stores store opaque bytes. Redis goes further -- it knows about the structure of common data types and provides operations that work natively on them.

> **Core Concept:** The hash table at the key level is the foundation. See [Hash Tables](../../core-concepts/02-data-structures/01-hash-tables.md). The sorted set is implemented as a skip list (similar to a balanced BST) for O(log n) ordered operations. See [Trees for Storage](../../core-concepts/02-data-structures/02-trees-for-storage.md).

| Type | Best For | Key Operations |
|------|----------|---------------|
| **String** | Simple values, counters, serialized JSON | GET/SET, INCR, APPEND |
| **Hash** | Structured objects (avoid N separate keys) | HSET/HGET, HINCRBY |
| **List** | Ordered sequences, queues | LPUSH/RPUSH, BRPOP |
| **Set** | Unique membership, tagging | SADD, SISMEMBER, SINTER |
| **Sorted Set** | Ranked data, leaderboards | ZADD, ZRANGE, ZRANK |
| **HyperLogLog** | Approximate unique counts | PFADD, PFCOUNT |
| **Stream** | Append-only log, event sourcing | XADD, XREAD, XREADGROUP |

---

## Choosing the Right Type

The choice matters for both performance and memory efficiency. Storing a user object as a JSON string means deserializing the whole blob to read one field. Storing it as a hash means you can fetch just the fields you need.

```{code-cell} python
user = {"id": 42, "name": "Alice", "email": "alice@example.com", "plan": "pro", "login_count": 47}

# Approach 1: JSON string -- simple but coarse-grained reads
r.set("user:json:42", json.dumps(user))

# Approach 2: Hash -- field-level access and updates
r.hset("user:hash:42", mapping={k: str(v) for k, v in user.items()})

# Approach 3: Separate string keys -- maximum granularity, many keys
for k, v in user.items():
    r.set(f"user:fields:42:{k}", str(v))

# Hash allows atomic field update without fetching the whole object
r.hincrby("user:hash:42", "login_count", 1)
print(f"login_count after increment: {r.hget('user:hash:42', 'login_count')}")

print(f"\nKey count after three approaches: {r.dbsize()} keys")
```

The rule of thumb: use a **hash** when you have a structured object and need field-level access. Use a **string** with JSON when you always read the whole object and never update individual fields. Use **separate string keys** only when fields are truly independent and accessed at different rates.

> **Core Concept:** [Probabilistic Structures](../../core-concepts/02-data-structures/04-probabilistic-structures.md) explains HyperLogLog: how ~12KB of memory can approximate unique cardinality across billions of values. Redis's `PFADD`/`PFCOUNT` is the production implementation.

```{code-cell} python
# HyperLogLog: count unique visitors with fixed memory
r.pfadd("visitors:home:2024-01-15", "user_1", "user_2", "user_3", "user_1")  # user_1 deduped
r.pfadd("visitors:home:2024-01-16", "user_2", "user_4", "user_5")

approx_day1 = r.pfcount("visitors:home:2024-01-15")
approx_day2 = r.pfcount("visitors:home:2024-01-16")
approx_total = r.pfcount("visitors:home:2024-01-15", "visitors:home:2024-01-16")

print(f"Day 1 unique visitors: ~{approx_day1}")
print(f"Day 2 unique visitors: ~{approx_day2}")
print(f"Total unique (merged): ~{approx_total}")
print("Memory per HLL key: always 12KB regardless of cardinality")
```

---

**Next:** [Common Patterns →](03-common-patterns.md)

---

[← Back: KV Concepts and Tradeoffs](01-kv-concepts-and-tradeoffs.md) | [Course Home](../README.md)
