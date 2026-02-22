# Probabilistic Data Structures

## The Problem

Some questions require exact answers. Others don't.

- "How many *distinct* users visited this page today?" -- you want a number within 1%, not exact
- "Is this email address in our blocklist?" -- you want near-certain membership; the occasional false positive is acceptable
- "What is the 99th percentile API response time?" -- you want an accurate approximation, not an exact sort of all requests

The exact answers to these questions require O(n) memory: store every distinct user, store every blocked email, store every response time. At scale, n is billions. That's tens or hundreds of gigabytes for a single counter.

Probabilistic data structures trade a small, mathematically bounded amount of accuracy for massive memory savings -- often from gigabytes to kilobytes.

## The Solution

A family of structures that maintain compact summaries of data streams, answering approximate queries in constant time and space. The error rates are not random -- they are mathematically provable upper bounds.

## How It Works

### Bloom Filters: Membership Testing

**Question answered:** "Is this element *possibly* in the set, or is it *definitely not* in the set?"

A bloom filter is a bit array of size `m` with `k` hash functions. To add an element:
1. Apply each of k hash functions to the element → k positions in the array
2. Set those k bits to 1

To check membership:
1. Apply the same k hash functions
2. If ANY bit is 0 → element is **definitely not** in the set (no false negatives)
3. If ALL bits are 1 → element is **probably** in the set (small false positive rate)

```
Bit array (m=10 bits):  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

Insert "alice" (k=2 hash functions):
  hash1("alice") % 10 = 3  → set bit 3
  hash2("alice") % 10 = 7  → set bit 7
  Array: [0, 0, 0, 1, 0, 0, 0, 1, 0, 0]

Insert "bob":
  hash1("bob") % 10 = 1  → set bit 1
  hash2("bob") % 10 = 5  → set bit 5
  Array: [0, 1, 0, 1, 0, 1, 0, 1, 0, 0]

Check "alice":   bits 3 and 7 are set → PROBABLY in set ✓
Check "carol":   hash1("carol")=3 (set!), hash2("carol")=9 (not set) → DEFINITELY NOT ✓
Check "dave":    hash1("dave")=1 (set!), hash2("dave")=5 (set!) → PROBABLY in set ✗ 
                 (false positive -- "dave" was never inserted but both bits happen to be set)
```

**Key properties:**
- No false negatives: if an element was inserted, the filter always says "possibly in set"
- Small false positive rate: controllable by adjusting m (array size) and k (hash count)
- Memory: fixed at m bits regardless of how many elements are inserted
- No deletions (standard bloom filter -- variants like counting bloom filters support this)

**Typical usage pattern:** Bloom filter says NO → skip the expensive operation entirely. Bloom filter says YES → do the expensive operation (accept occasional false positives).

```python
# Conceptual: skip SSTable reads using bloom filter
def get(key):
    for sstable in sstables_newest_first:
        if sstable.bloom_filter.might_contain(key):  # ~1% false positive rate
            result = sstable.binary_search(key)       # expensive disk read
            if result is not None:
                return result
    return None
# Without bloom filters: check every SSTable with a disk read
# With bloom filters: skip ~99% of SSTable reads when key is absent
```

### HyperLogLog: Cardinality Estimation

**Question answered:** "Approximately how many *distinct* elements have been seen?"

HyperLogLog uses the statistical property that the maximum leading zeros in a hash value correlates with cardinality. If the maximum leading-zero count in all observed hashes is k, the estimated cardinality is approximately 2^k.

Multiple registers (sub-streams) are averaged to reduce variance.

```
Count distinct users who visited the homepage:

Naive approach: maintain a set of user IDs
  Memory: O(n) -- 1 billion users × 8 bytes = 8 GB

HyperLogLog:
  Memory: 12 KB regardless of cardinality
  Error:  0.81% (mathematically bounded)

PFADD visitors "user_1001"
PFADD visitors "user_1002"
...
PFADD visitors "user_999999999"
PFCOUNT visitors → 999,811,423  (within 0.81% of actual 1 billion)
```

The 12KB is constant -- it doesn't grow with the number of distinct elements.

**Merging**: HyperLogLog registers can be merged without the original data. You can count distinct users across multiple time periods by merging their HyperLogLogs, without storing all user IDs.

### Count-Min Sketch: Frequency Estimation

**Question answered:** "Approximately how many times has this element appeared?"

A 2D array of counters with multiple hash functions. To increment a key: hash it with each function, increment the corresponding counter in each row. To query frequency: return the minimum counter value across all rows (the minimum because only that row's specific cell was incremented for this key -- collisions only cause over-counts, so min is the best estimate).

```
Count-Min Sketch (4 rows × 8 columns):

Insert "alice" 3 times:
  Row 0: hash0("alice")=2 → counter[0][2] += 3
  Row 1: hash1("alice")=5 → counter[1][5] += 3
  Row 2: hash2("alice")=7 → counter[2][7] += 3
  Row 3: hash3("alice")=1 → counter[3][1] += 3

Query "alice":
  min(counter[0][2], counter[1][5], counter[2][7], counter[3][1]) = 3 ✓
```

Used for: finding heavy hitters (top-k frequent elements), network traffic analysis, database query cardinality estimation.

### t-Digest: Approximate Percentiles

**Question answered:** "What is the p99 latency?" (or any other percentile)

t-Digest maintains a sorted set of centroids -- clusters of data points with their count and mean. Near the tails (very low and very high percentiles), centroids are small (more precise). Near the median, centroids can be large (less precise -- less important for most use cases).

```
Computing exact p99:
  Store all 1,000,000 response times → sort → take 99th percentile
  Memory: O(n) = ~8 MB for 1M floats

t-Digest:
  Memory: O(compression parameter) -- typically a few KB
  Error:  < 0.1% relative error at the tails (p1, p99)
           higher relative error at the median (p50) -- usually acceptable
```

## Trade-offs

| Structure | Query | Memory | Error Guarantee |
|-----------|-------|--------|----------------|
| Bloom Filter | Membership | O(m) fixed | No false negatives; bounded false positive rate |
| HyperLogLog | Count distinct | ~12 KB fixed | ±0.81% relative error |
| Count-Min Sketch | Frequency | O(width × depth) | Over-estimate only; bounded by ε × total |
| t-Digest | Percentiles | O(compression) | ±0.1% at tails; higher at median |

**Common theme:** All of these structures trade exact answers for:
- Memory savings of 3-6 orders of magnitude
- O(1) time for both inserts and queries
- Mathematically provable error bounds (not random error)

The key question when adopting a probabilistic structure: is this use case tolerant of bounded approximation? Analytics, monitoring, and cardinality estimation usually are. Inventory counts and financial transactions usually are not.

## Where You'll See This

- **LSM-tree reads** (Cassandra, RocksDB): Bloom filters skip SSTable reads for absent keys -- see [LSM-Trees and SSTables](03-lsm-trees-and-sstables.md)
- **Query execution** (Spark, Hive): Bloom filters as join pre-filters to avoid sending rows across the network that won't match
- **Analytics platforms** (Redis, Druid): HyperLogLog for `COUNT DISTINCT` queries over billions of events without storing all distinct values
- **Monitoring and observability** (Prometheus, Datadog): HyperLogLog for unique user counts; t-Digest for latency percentiles
- **Stream processing** (Kafka Streams, Flink): Count-Min Sketch for heavy hitter detection in unbounded streams
- **Database planners**: Cardinality estimation in query planners uses probabilistic sketches to estimate result sizes without scanning data

---

**Next:** [Vertical vs Horizontal Scaling →](../03-scaling/01-vertical-vs-horizontal.md)
