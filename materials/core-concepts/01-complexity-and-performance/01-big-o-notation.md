---
kernelspec:
  name: python3
  language: python
  display_name: Python 3
---

# Big O Notation

## The Problem

You have a database query that runs in 10 milliseconds on your laptop with 1,000 rows. Will it still be acceptable when your production system has 1 billion rows? Without a way to reason about how performance scales with data size, you're guessing.

The same question applies everywhere: will this search algorithm still be fast when the dataset doubles? Will this sort hold up under 10x load? Big O notation gives you the vocabulary to answer these questions before your system melts down in production.

## The Solution

**Asymptotic complexity analysis** -- classify operations by how their cost grows relative to input size `n`. The O() notation describes the dominant term as `n` grows large, ignoring constants and lower-order terms.

The key insight: what matters is the *shape* of the growth curve, not the exact runtime on any specific input.

## How It Works

### The Complexity Classes

**O(1) -- Constant Time**
The operation takes the same time regardless of data size. Looking up a value in a hash map, accessing an array element by index, reading a config value.

```
n = 1,000       → 1 step
n = 1,000,000   → 1 step
n = 1,000,000,000 → 1 step
```

**O(log n) -- Logarithmic**
Each step eliminates half the remaining search space. Binary search on a sorted list, lookup in a balanced tree. Doubling the data adds just one more step.

```
n = 1,000       → ~10 steps   (log₂ 1,000 ≈ 10)
n = 1,000,000   → ~20 steps   (log₂ 1,000,000 ≈ 20)
n = 1,000,000,000 → ~30 steps (log₂ 10⁹ ≈ 30)
```

**O(n) -- Linear**
You must visit every element. Scanning an unsorted list, counting items, reading every row in a table.

```
n = 1,000       → 1,000 steps
n = 1,000,000   → 1,000,000 steps
n = 1,000,000,000 → 1,000,000,000 steps
```

**O(n log n) -- Log-Linear**
Efficient sorting algorithms (merge sort, heapsort, Timsort). You need to touch every element, but each element's placement uses a logarithmic comparison process.

```
n = 1,000       → ~10,000 steps
n = 1,000,000   → ~20,000,000 steps
n = 1,000,000,000 → ~30,000,000,000 steps
```

**O(n²) -- Quadratic**
For each element, you process every other element. Naive nested loops, bubble sort. Doubling the data quadruples the work.

```
n = 1,000       → 1,000,000 steps
n = 1,000,000   → 1,000,000,000,000 steps  ← unusable at scale
```

### Concrete Examples

```{code-cell} python
# O(1) -- dictionary/hash lookup
user_cache = {"user_42": {...}, "user_43": {...}}
user = user_cache["user_42"]  # constant time regardless of cache size

# O(log n) -- binary search on sorted list
import bisect
prices = [5.00, 10.00, 15.00, 18.00, 20.00, 25.00]  # sorted
idx = bisect.bisect_left(prices, 18.00)  # log₂(6) ≈ 3 comparisons

# O(n) -- linear scan
def find_user_by_email(users: list, email: str):
    for user in users:  # must check every user
        if user["email"] == email:
            return user

# O(n log n) -- efficient sort
sorted_events = sorted(events, key=lambda e: e["timestamp"])  # Timsort

# O(n²) -- naive nested loop join
matches = []
for order in orders:        # 830 iterations
    for customer in customers:  # × 91 iterations = 75,530 total
        if order["customer_id"] == customer["id"]:
            matches.append((order, customer))
```

### Why Constants Are Dropped

O(2n) is still O(n) because constants don't affect the *shape* of growth. Both double when data doubles. O(n + log n) is O(n) because n dominates as n grows large. Big O describes behavior at scale, not on small inputs.

## Trade-offs


| Complexity | At n=1,000 | At n=1,000,000 | At n=1,000,000,000 |
| ---------- | ---------- | -------------- | ------------------ |
| O(1)       | 1μs        | 1μs            | 1μs                |
| O(log n)   | 10μs       | 20μs           | 30μs               |
| O(n)       | 1ms        | 1 second       | 16 minutes         |
| O(n log n) | 10ms       | 20 seconds     | 8 hours            |
| O(n²)      | 1 second   | 11 days        | 31,710 years       |


*Assuming 1 nanosecond per step.*

The practical rule: an O(n) operation that feels fast on your laptop (1ms for 1,000 rows) will take **16 minutes** for 1 billion rows. An O(n²) algorithm is simply not viable at scale.

**What you gain vs lose when moving up the complexity ladder:**

- Better complexity often requires more structure (sorted arrays, indexes, hash maps)
- Structure has upfront cost: building an index takes time and space
- The payoff: every subsequent lookup is faster by orders of magnitude

## Where You'll See This

- **Index design** (any database): Adding an index converts an O(n) table scan to an O(log n) index seek
- **Query optimization**: Join algorithms are chosen by the query planner based on complexity -- hash join is O(n + m) but requires memory; nested loop is O(n × m) but uses less memory
- **Data pipeline design**: Spark and Hadoop optimize execution plans specifically to avoid O(n²) cross-node operations (shuffles)
- **Cache design**: A cache with O(1) lookup in front of an O(n) scan transforms read-heavy workloads
- **Algorithm selection**: Choosing between sorting strategies, search algorithms, and data structures all comes down to Big O trade-offs

---

**Next:** [I/O and Storage Fundamentals →](02-io-and-storage-fundamentals.md)