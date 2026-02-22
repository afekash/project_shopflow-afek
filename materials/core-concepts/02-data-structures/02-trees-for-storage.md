# Trees for Storage

## The Problem

Hash tables give you O(1) point lookups -- the fastest possible for "give me the value for exactly this key." But hash tables scatter keys randomly across buckets, destroying any ordering. You cannot answer:

- "Give me all records where `price` is between 10 and 50"
- "Give me the first 100 records alphabetically"
- "Give me the record immediately after this one"

For these operations you need a structure that maintains **sorted order** while keeping lookups fast. Scanning a sorted array works but inserts are O(n) (must shift elements). You need something better.

## The Solution

**Tree-based structures** maintain keys in sorted order while keeping lookup, insert, and delete at O(log n). The key idea: organize keys hierarchically so that at each node, you can eliminate half the remaining search space -- the same principle as binary search, but now the structure maintains itself as data changes.

## How It Works

### Binary Search Trees (BST): The Foundation

The simplest tree: each node has at most two children. Left subtree contains only smaller keys; right subtree contains only larger keys.

```
         [50]
        /    \
     [25]    [75]
     /  \    /  \
  [10] [30] [60] [90]
```

Lookup: compare key to current node, go left if smaller, right if larger. Each comparison eliminates one subtree. O(log n) if the tree is balanced.

The problem: naive insert can produce a linear tree (a linked list) if keys arrive in sorted order:

```
Insert 10, 20, 30, 40 in order:
10 → 20 → 30 → 40  (each on the right, depth = n, lookup = O(n))
```

Balanced trees solve this by automatically restructuring on insert/delete.

### B-Trees: Optimized for Disk

B-trees generalize BSTs to have many children per node (not just two). A B-tree node can hold hundreds of keys and hundreds of child pointers.

```
B-Tree node (order 4, up to 3 keys per node):

┌─────────────────────────────────┐
│  key1=10  │  key2=50  │ key3=90 │
└──┬────────┴──┬────────┴──┬──────┘
   │           │           │
  [1-9]     [11-49]     [51-89]   [91+]
```

**Why many children?** Disk reads happen in fixed-size blocks (typically 4KB or 16KB). A B-tree node is sized to fill exactly one disk block. A single disk read retrieves hundreds of keys, and the tree depth (number of disk reads per lookup) stays very small.

```
1 million records, 100 keys per node:
  Depth = log₁₀₀(1,000,000) = 3 levels
  Lookup = 3 disk reads regardless of where the key is
```

### B+ Trees: The Standard for Databases

Most database systems use **B+ trees**, a variant with two key properties:

1. **Data only in leaf nodes**: Internal nodes store only keys for navigation; all actual data (or pointers to data) lives in the leaf level.
2. **Leaves are linked**: Each leaf node has a pointer to the next leaf, forming a sorted linked list at the bottom.

```
B+ Tree structure:

Internal nodes (navigation only):
         [30 | 60]
        /    |    \
     [10|20] [30|50] [60|80|90]
       ↓       ↓       ↓
  Leaf nodes (data here):
  [10→d, 20→d] ←→ [30→d, 50→d] ←→ [60→d, 80→d, 90→d]
                                               ↑
                                       linked for range scans
```

**Range queries become efficient**: To find all records with key between 30 and 80:
1. Descend the tree to find key 30: O(log n)
2. Follow leaf pointers right until key > 80: O(k) where k is the result size

This is how every relational database serves range queries, ORDER BY, and index scans efficiently.

### Write Operations: The Hidden Cost

Every write that changes a key must update the tree in-place:
1. Find the correct leaf node (O(log n) disk reads)
2. Insert the key (may split the node, propagating up)
3. Write the modified nodes back to disk (random I/O)

This random I/O is the fundamental limitation of B-trees for write-heavy workloads. Each write touches multiple disk pages at arbitrary locations. For systems with massive write throughput, this becomes the bottleneck -- which is why LSM-trees exist (see [LSM-Trees and SSTables](03-lsm-trees-and-sstables.md)).

### Clustered vs Non-Clustered (Covering) Index

Two modes of B+ tree deployment:

**Clustered index**: The leaf nodes *are* the actual data rows, stored in key order. One clustered index per table. Looking up by the clustered key is a single tree traversal that lands directly on the data.

**Non-clustered index**: The leaf nodes contain the key plus a pointer (row ID) to the actual data elsewhere. Looking up by a non-clustered key requires the tree traversal *plus* a separate lookup to fetch the full row.

```
Clustered lookup (2-3 disk reads total):
  Root → Internal node → Leaf with data ✓

Non-clustered lookup (4-5 disk reads total):
  Root → Internal node → Leaf with pointer → Data page at pointer location
```

## Trade-offs

| Operation | B+ Tree | Hash Table |
|-----------|---------|------------|
| Point lookup | O(log n) | O(1) |
| Range scan | O(log n + k) | Not supported |
| Sorted iteration | O(n) via leaf links | Not supported |
| Insert/Update | O(log n) + random I/O | O(1) amortized |
| Memory usage | Low (disk-resident) | Higher (in-memory) |

**What you gain:** Both point lookups and range queries in one structure. The entire sorted keyspace is navigable.

**What you give up:** Write throughput is limited by random I/O. For massive write rates (millions per second), the disk becomes the bottleneck.

## Where You'll See This

- **Relational databases** (PostgreSQL, MySQL, SQL Server): The primary index structure for all tables and indexes
- **Document databases** (MongoDB): Uses B-trees for all collection indexes -- same reason, same trade-off
- **Embedded databases** (SQLite, LevelDB): B-tree as the underlying storage engine
- **File system metadata**: Most modern file systems (ext4, NTFS, APFS) use B-trees to store directory structures
- **In-memory variants**: Red-black trees are self-balancing BSTs used for in-memory sorted structures (Java TreeMap, C++ std::map); also used inside LSM-tree memtables

---

**Next:** [LSM-Trees and SSTables →](03-lsm-trees-and-sstables.md)
