# Query Routing Patterns

## The Problem

Data is spread across multiple nodes or partitions (see [Partitioning Strategies](../03-scaling/02-partitioning-strategies.md)). A query arrives. How does the system find the relevant data without asking every node?

Asking all nodes for every query -- **scatter-gather** -- works but costs grow linearly with cluster size. A 100-node cluster queried by scatter-gather requires 100x the network and compute resources vs. a query that goes to one node. At petabyte scale, the difference between routing a query to 1 node vs. 1,000 nodes is the difference between a 50ms query and a 50-second query.

The choice of query routing pattern is as consequential as the choice of partition key -- they must be designed together.

## The Solution

Two fundamental routing strategies: **targeted** (send to exactly the right node(s)) and **scatter-gather** (send to all nodes, merge results). The goal is to maximize targeted queries by designing schemas and partition keys around the most frequent access patterns.

## How It Works

### Targeted Queries

The query includes enough information to determine exactly which partition(s) hold the relevant data. The routing layer (a coordinator, a proxy, or the client library) consults the partition map and forwards the query to the one or few partitions that own the data.

```
Query: "Give me the order with order_id=10042"
  Partition key: order_id
  Routing: hash(10042) → partition 3 → Node C
  
  Request flow:
  Client → Coordinator → [Node C only] → return result

Cost: O(1) network round-trips (or O(k) for range queries spanning k partitions)
```

**For range queries with range-partitioned data**:

```
Query: "Give me all orders created in January 2025"
  Partition key: created_date (range partitioned by month)
  Routing: January 2025 → Partition "2025-01" → Node B
  
  Request flow:
  Client → Coordinator → [Node B only] → return results
  
  All January 2025 orders are co-located on Node B. ✓
```

**What makes targeted queries possible:**
- The partition key appears in the WHERE clause
- The partition key is designed around the most frequent query pattern
- The routing layer has an up-to-date partition map

### Scatter-Gather Queries

The query cannot be routed to a specific partition -- it either doesn't include the partition key, or it spans all partitions by design. The routing layer sends the query to all partitions and merges the results.

```
Query: "Give me all orders with status='pending'"
  Partition key: order_id (not status)
  Routing: cannot determine which partition(s) -- must ask all

  Request flow:
  Client → Coordinator → [All nodes in parallel] → merge partial results → return

Cost: O(N) network round-trips (N = number of partitions)
      O(N × data_per_partition) processing
```

```
Scatter-gather merge:
  Node A returns: 47 pending orders
  Node B returns: 83 pending orders
  Node C returns: 12 pending orders
  Coordinator merges all 142 results, applies final sort/limit, returns to client
```

**When scatter-gather is unavoidable:**
- The query filters on a non-partition-key column
- Aggregations across the entire dataset (total count, global max, distributed GROUP BY)
- Full-text search across all records
- Administrative queries (index rebuilds, statistics collection)

**Managing scatter-gather cost:**
- Parallel fan-out: send to all partitions simultaneously, not sequentially. The total latency is the slowest partition's response, not the sum.
- Result pruning: each partition applies filters locally before returning. Only matching rows cross the network.
- Early termination: for LIMIT queries, stop collecting results once you have enough.

### Broadcast Joins

A special case of query routing relevant for distributed query engines: when joining a large table to a small table, instead of moving the large table to meet the small one (expensive shuffle), broadcast the small table to every partition of the large one.

```
Joining orders (1 billion rows, partitioned) with promotion_codes (500 rows, small):

Naive distributed join (shuffle):
  → Move all 1 billion order rows across the network based on join key
  → Join with promotion_codes at each node
  Cost: network transfer of 1 billion rows 🐢

Broadcast join:
  → Send the 500 promotion_codes to every node
  → Each node joins its local orders with the local copy of promotion_codes
  → No order rows cross the network
  Cost: network transfer of 500 rows × N nodes ✓
```

The decision threshold: if the smaller table fits in memory on each node (typically < a few hundred MB), broadcast is almost always the right choice.

### The Router/Coordinator Role

In distributed databases, a routing component (often called a coordinator, router, or proxy) sits between the client and the data nodes:

```
Client
  │
  ▼
Coordinator (knows the partition map)
  │    │    │
  ▼    ▼    ▼
Node  Node  Node  (partitions)
```

**Responsibilities:**
- Maintain the partition map (which key ranges → which nodes)
- Route queries to the correct partition(s)
- Collect and merge results from scatter-gather queries
- Handle node failures (re-route to replicas)
- Optionally: cache partial results, handle retries

**Coordinator placement:**
- **Dedicated coordinator nodes**: Separate machines that handle only routing. Avoids routing overhead on data nodes. Can be a bottleneck if not scaled independently.
- **Client-side routing**: Each client has a copy of the partition map and routes directly to data nodes. Eliminates the coordinator hop but requires clients to track partition state.
- **Any-node routing**: Any data node can act as coordinator for a query. The receiving node routes to the correct nodes as needed. Simplest for clients but adds coordination work to data nodes.

### Impact of Partition Key Design

Routing strategy and partition key are inseparable. The partition key must match your most frequent query patterns:

```
Use case: multi-tenant SaaS application
  Most queries: "get all records for tenant X"
  Bad partition key:  record_id (scatter-gather for every tenant query)
  Good partition key: tenant_id (all tenant data co-located, targeted queries)

Use case: IoT sensor readings
  Most queries: "get readings for sensor Y in the last 24 hours"
  Bad partition key:  random UUID (scatter-gather for every sensor query)
  Good partition key: (sensor_id, day_bucket) -- co-locates each sensor's daily data
```

## Trade-offs

| Pattern | Network Cost | Latency | When to Use |
|---------|-------------|---------|-------------|
| Targeted (1 partition) | O(1) | Lowest | Most frequent queries, include partition key |
| Targeted (k partitions) | O(k) | Low-moderate | Range queries, finite partition span |
| Scatter-gather | O(N) | Scales with N | Non-partition-key filters, aggregations |
| Broadcast join | O(small_table × N) | Moderate | Joining large table to small lookup table |

**The design principle**: Design your partition key around the query pattern that most needs to be fast. Scatter-gather queries are not wrong -- they're necessary for some operations. The goal is to ensure your highest-throughput, latency-sensitive queries are targeted.

## Where You'll See This

- **Distributed databases** (MongoDB sharding, Cassandra, DynamoDB): mongos (MongoDB's coordinator) routes queries targeted vs. scatter-gather based on whether the shard key is present in the filter
- **Distributed query engines** (Spark, Trino/Presto, BigQuery): Query planners decide whether to broadcast small tables or shuffle large ones; partition pruning is the targeted-query equivalent
- **Distributed search** (Elasticsearch): Search queries fan out to all shards (scatter-gather) by default; routing keys can force queries to specific shards
- **API gateways and service meshes**: Request routing to microservices follows the same targeted vs. broadcast logic -- a request to `/users/42` routes to the User Service shard for user 42

---

**Next:** [Polyglot Persistence →](03-polyglot-persistence.md)
