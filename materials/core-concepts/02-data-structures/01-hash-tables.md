# Hash Tables

## The Problem

You have a collection of records and need to retrieve a specific one by its identifier as fast as possible. A sorted array lets you binary search in O(log n), but you can do better. A linked list requires O(n) to scan. Is there a way to jump *directly* to the storage location of any record, without searching at all?

This is the lookup problem, and it's one of the most fundamental challenges in computing.

## The Solution

**Hash tables** solve this by computing a deterministic function (a *hash function*) on the key to derive a storage location directly. Instead of searching for the key, you calculate where it should be and jump straight there.

The result: O(1) average-case lookup, insert, and delete -- constant time regardless of how many records are stored.

## How It Works

### The Core Mechanism

```
Key                       Hash Function                   Storage
──────────────────────────────────────────────────────────────────
"session:user_42"  ──→   hash("session:user_42")        ──→  bucket[47]
                         = 3,842,917,201
                         % 100 (bucket count)
                         = 47
```

1. Apply the hash function to the key → produces an integer
2. Take the integer modulo the number of buckets → produces a bucket index
3. Store the value at that bucket

To retrieve the value: apply the same function, find the same bucket, return the value. No searching required.

### Hash Functions

A good hash function must be:
- **Deterministic**: same input always produces same output
- **Uniform**: outputs spread evenly across the bucket range (avoid clustering)
- **Fast**: computing the hash should be O(1)

Common algorithms: MurmurHash, xxHash (fast, good distribution), SHA-256 (cryptographic -- slower, but collision-resistant).

### Collision Handling

Two different keys can hash to the same bucket -- this is a **collision**. Two standard strategies:

**Chaining**: Each bucket holds a linked list. When two keys hash to the same bucket, both entries are appended to the list. Lookup walks the chain comparing keys until it finds a match.

Say `hash("session:user_42") % 100 = 47` and `hash("session:user_99") % 100 = 47`. Both land in bucket 47 and form a chain:

```
Bucket array
 [44] → null
 [45] → null
 [46] → null
 [47] → ["session:user_42" → "tok_abc"] → ["session:user_99" → "tok_xyz"] → null
 [48] → null
```

Lookup for `"session:user_99"`: go to bucket 47, scan the chain, skip `user_42`, return `tok_xyz`. Average O(1); worst case O(n) if many keys collide. Used by Java's `HashMap` and Python's `dict`.

---

**Open addressing**: All entries live inside the bucket array itself — no external lists. On collision, probe forward until an empty slot is found (linear probing), or apply a second hash function to jump to a different slot (double hashing).

Say `hash("user:42") % 8 = 3` and `hash("user:99") % 8 = 3`. Insert `user:42` first, then `user:99` probes slot 4 (next free):

```
Index: [ 0 ][ 1 ][ 2 ][ 3        ][ 4        ][ 5 ][ 6 ][ 7 ]
Value: [   ][   ][   ][ user:42  ][ user:99  ][   ][   ][   ]
                       ^primary    ^probe +1
```

Lookup for `"user:99"`: hash → slot 3, key mismatch, probe to slot 4, match found. More cache-friendly than chaining (data stays contiguous in memory), but performance degrades rapidly above a ~70% load factor as probe sequences grow long.

### Load Factor and Rehashing

The **load factor** = (number of stored keys) / (number of buckets). When the load factor exceeds a threshold (commonly 0.7), performance degrades because most buckets have collisions.

**Rehashing**: Allocate a larger bucket array (typically 2x) and re-insert every key into the new array. This is an O(n) operation but happens rarely enough that the amortized cost per operation remains O(1).

```python
# Simplified hash table implementation
class HashTable:
    def __init__(self, capacity=100):
        self.capacity = capacity
        self.buckets = [[] for _ in range(capacity)]
        self.size = 0

    def _hash(self, key):
        return hash(key) % self.capacity

    def put(self, key, value):
        bucket = self.buckets[self._hash(key)]
        for i, (k, v) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)  # update existing
                return
        bucket.append((key, value))        # new entry
        self.size += 1
        if self.size / self.capacity > 0.7:
            self._rehash()

    def get(self, key):
        for k, v in self.buckets[self._hash(key)]:
            if k == key:
                return v
        raise KeyError(key)
```

### Complexity Summary

| Operation | Average Case | Worst Case (all keys collide) |
|-----------|-------------|-------------------------------|
| Lookup    | O(1)        | O(n)                          |
| Insert    | O(1)        | O(n)                          |
| Delete    | O(1)        | O(n)                          |

Worst case is theoretical -- a good hash function makes it negligible. The amortized cost across operations including rehashing remains O(1).

## Trade-offs

**What you gain:**
- O(1) point lookups -- the fastest possible for key-based retrieval
- O(1) inserts -- no sorting or balancing required
- Simple implementation

**What you give up:**
- **No ordering**: keys are scattered across buckets. You cannot scan keys in sorted order, do range queries (`key > X`), or find the minimum/maximum efficiently. For this you need a tree structure.
- **Memory overhead**: bucket array must be larger than the data to maintain low load factor
- **Rehashing cost**: occasional O(n) pause to resize (amortized away, but not zero)
- **Hash function quality matters**: a bad hash function collapses performance to O(n)

**When to use a hash table vs a tree:**
- Need only `get(key)` and `set(key, value)` → hash table (faster constant)
- Need `range(key_min, key_max)` or sorted iteration → tree structure
- Need both → use a tree (accept the O(log n) point lookup cost)

## Where You'll See This

- **In-memory databases** (Redis): The entire keyspace is a hash table -- pure key lookups at O(1), no range queries needed
- **Database buffer pools**: Pages are cached in memory using a hash table keyed on page ID
- **JOIN algorithms**: Hash join builds a hash table of the smaller relation, then probes it for each row of the larger relation -- O(n + m) vs O(n × m) for nested loops
- **Aggregate operations**: `GROUP BY` implementations build hash tables where the key is the grouping column(s) and the value is the accumulator
- **Distributed hash tables (DHT)**: Consistent hashing extends this concept across nodes -- see [Consistent Hashing](../03-scaling/03-consistent-hashing.md)
- **Sets and membership testing**: Set operations (`contains`, `union`, `intersect`) are all O(1) per element using hash tables

---

**Next:** [Trees for Storage →](02-trees-for-storage.md)
