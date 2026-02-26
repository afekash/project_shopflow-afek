# Partitioning Strategies

## The Problem

A single node cannot hold all your data. You need to split it across multiple nodes. But how you split it determines everything:

- Which queries can be answered quickly (single-node lookup) vs. slowly (ask all nodes)
- Whether write load is even or concentrated on one overloaded node
- Whether you can grow the cluster without migrating most data

The choice of partitioning strategy is one of the most consequential and hardest-to-change decisions in a distributed system. Get it wrong and you're either rebalancing constantly or rebuilding from scratch.

## The Solution

**Partitioning** (also called **sharding**) -- divide data into subsets (partitions/shards), each owned by one node. Every record belongs to exactly one partition based on a **partition key** (also called shard key).

Three fundamental strategies, each with different trade-offs:

## How It Works

### Strategy 1: Range Partitioning

Split the key space into contiguous ranges. All records with keys in a given range go to the same partition.

```
Partition key: user_id (integer)

Partition 1: user_id [1,         2,500,000)  → Node A
Partition 2: user_id [2,500,000, 5,000,000)  → Node B
Partition 3: user_id [5,000,000, 7,500,000)  → Node C
Partition 4: user_id [7,500,000, ∞)          → Node D
```

**What makes it good:**
- Range queries are efficient: `WHERE user_id BETWEEN 1000 AND 5000` hits only the relevant partition(s)
- Sorted scans within a range are local to one node
- Intuitive and easy to reason about

**What makes it dangerous:**
- **Hot spots from monotonic keys**: If user IDs are assigned sequentially, all new writes land on the last partition (the "hot" partition). The other partitions are idle.
- **Skew**: If user activity is concentrated in a range (e.g., active users have high IDs), one partition is overloaded.

```
Sequential key hot spot:
Time →  User 1  User 2  User 3  ... User 5M  User 5M+1  User 5M+2
          ↓       ↓       ↓             ↓        ↓          ↓
        Node A   Node A  Node A      Node B   Node C     Node C
                                                ↑ ALL new writes here
```

**Mitigation**: Use a composite key where the first component is not monotonic, or use hashed sharding for write-heavy data with sequential keys.

### Strategy 2: Hash Partitioning

Apply a hash function to the partition key, then use modulo (or consistent hashing) to assign to a partition.

```
Partition key: user_id
Hash function: hash(user_id) % 4

user_id=1001: hash(1001) = 7842 % 4 = 2 → Partition 2 → Node B
user_id=1002: hash(1002) = 1923 % 4 = 3 → Partition 3 → Node C
user_id=1003: hash(1003) = 5514 % 4 = 0 → Partition 0 → Node A
user_id=1004: hash(1004) = 8731 % 4 = 1 → Partition 1 → Node D
```

**What makes it good:**
- Even distribution: hash functions spread keys uniformly, eliminating hot spots from sequential keys
- Write load is balanced across all nodes
- Adding a node with consistent hashing moves only ~1/N of keys (see [Consistent Hashing](03-consistent-hashing.md))

**What makes it dangerous:**
- **Range queries are scatter-gather**: Records with consecutive user IDs land on different nodes. `WHERE user_id BETWEEN 1000 AND 5000` must query all partitions and merge results.
- **No locality**: Related records that happen to be looked up together may be on different nodes.

```
Range query with hash partitioning:
  "Give me all events for user_ids 1000-2000"
    → hash(1000) → Node B
    → hash(1001) → Node A
    → hash(1002) → Node D
    ... must ask all nodes and merge
```

### Strategy 3: Zone/Directory-Based Partitioning

Explicit placement rules: a coordinator (directory) maps each partition to a node, and partitions are assigned based on semantic grouping rather than key arithmetic.

```
Coordinator metadata table:
  partition "US_WEST"  → Node Group 1 (AWS us-west-2)
  partition "EU"       → Node Group 2 (AWS eu-west-1)
  partition "APAC"     → Node Group 3 (AWS ap-southeast-1)
  partition "ARCHIVE"  → Node Group 4 (cold storage)
```

**What makes it good:**
- Precise control over data placement (geographic affinity, hardware tiers, compliance requirements)
- Can move partitions without changing the key → partition mapping (just update the directory)
- Natural for multi-tenant systems where each tenant is a partition

**What makes it dangerous:**
- Directory is a central component -- must be highly available (see [Replication Patterns](../05-replication-and-availability/01-replication-patterns.md))
- Manual management of partition assignments doesn't scale to millions of partitions
- Requires application awareness of partition semantics

### Rebalancing

When nodes are added or removed, partitions must be rebalanced. The strategies differ:

**Fixed partitions**: Pre-create more partitions than nodes (e.g., 1000 partitions across 10 nodes). When a node is added, move some partitions to it. No per-key remapping.

```
10 nodes, 1000 partitions (100 per node):
Add Node 11: move ~91 partitions to the new node
             (each existing node gives up ~9 partitions)
             No individual keys move -- entire partitions move atomically
```

**Dynamic partitioning**: Partitions split when they grow too large, merge when they shrink. Partition count adapts to data volume. B-trees use this internally.

### Hot Spots and Skew

Even with hash partitioning, some keys are intrinsically "hot" -- a celebrity user's posts, a viral product, a frequently-read config key. The same partition key will be hammered while others are idle.

Mitigations:
- **Key salting**: Append a random prefix to hot keys, spreading reads across multiple partitions. Reads must then query all salted variants and merge.
- **Read replicas for hot partitions**: Route reads for specific hot partitions to dedicated replicas.
- **Application-level caching**: Cache hot keys in memory before they reach the database.

```
Hot key: "celebrity:user_001" (10,000 reads/sec)
Salted:  "celebrity:user_001:0", "celebrity:user_001:1", ..., "celebrity:user_001:9"
  → spread across 10 partitions
  → each partition handles 1,000 reads/sec ✓

Write: update all 10 salted keys
Read: query all 10, merge (take latest timestamp)
```

## Trade-offs

| Strategy | Write Distribution | Range Queries | Implementation |
|----------|--------------------|---------------|---------------|
| Range | Potentially skewed (hot spots) | Efficient | Simple |
| Hash | Even | Scatter-gather | Moderate |
| Zone/Directory | Explicit control | Depends on zone structure | Complex |

**The fundamental tension**: Even distribution (hash) vs. query efficiency (range). This is why the partition key choice is so critical -- it determines which queries are fast and which are expensive.

**What you always give up with partitioning:**
- Queries that don't include the partition key must scatter-gather across all partitions
- Multi-partition transactions are expensive or impossible depending on the system
- The partition key is hard (sometimes impossible) to change after the fact

## Where You'll See This

- **Distributed databases**: Every distributed database partitions data -- it's the only option at scale
- **Data warehouses**: Table partitioning (by date, region, etc.) prunes partitions from queries so only relevant partitions are scanned
- **Message queues**: Topics are partitioned across brokers; consumers are assigned to partitions
- **Search indexes**: Index shards are partitions of the document collection
- **File systems at scale**: Distributed file systems partition the namespace (directory tree) across metadata servers

---

**Next:** [Consistent Hashing →](03-consistent-hashing.md)
