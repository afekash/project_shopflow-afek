# Graph Partitioning

## The Problem

You have a graph too large to fit on one machine. You need to split it across multiple nodes. This sounds like ordinary partitioning — but with graphs, splitting the data is fundamentally harder than it is for key-value, document, or columnar stores.

In other databases, a record belongs to one partition and is retrieved in one operation. A graph edge connects *two* nodes. If those nodes end up on different partitions, every traversal that crosses the edge requires a **network hop** — and traversals in a graph database are sequences of edge-crossings. A single query might need hundreds.

This is the core problem: **partitioning cuts edges, and cut edges cost network round trips**.

## Why Graph Partitioning Is Computationally Hard

The ideal partition minimizes the number of edges that cross partition boundaries — the **edge cut**. Fewer cross-partition edges means fewer network hops and faster queries.

Finding the *optimal* minimum edge cut is an **NP-hard problem**. As the graph grows, there is no algorithm that can compute the perfect partition in polynomial time. You can find good approximations, but not guarantees.

This contrasts sharply with other partitioning strategies:

| Strategy | Complexity | Works well when |
|----------|-----------|-----------------|
| Hash partitioning (key-value) | O(1) per record | Records are independent |
| Range partitioning (time-series) | O(log n) per record | Access patterns are range-based |
| Graph partitioning (min edge cut) | NP-hard | Must be approximated |

## The Two Partitioning Axes

### Edge Cut vs. Vertex Cut

There are two ways to think about partitioning a graph:

**Edge-cut partitioning:** Nodes are assigned to partitions, and edges that connect nodes in different partitions are "cut." The node is only on one partition; the edge crosses a boundary.

```
Partition 1:   A — B           A → B is local (same partition)
                                A → C crosses the partition boundary ✗
Partition 2:   C — D           C → D is local
```

Cost: each cut edge requires a network hop during traversal. High-connectivity graphs (social networks, fraud rings) have many cut edges — the query latency explodes.

**Vertex-cut partitioning:** Edges are assigned to partitions, and *nodes* that appear in edges on multiple partitions are replicated. A node can exist (as a ghost/mirror) on more than one partition.

```
Edge (A→B) → Partition 1    Node A replicated on Partition 1
Edge (A→C) → Partition 2    Node A replicated on Partition 2
```

Cost: storage increases due to replicas; writes to a node must update all replicas. But traversal locality improves — each edge lookup is local to its partition.

Neither strategy eliminates the fundamental problem. They trade traversal latency for storage and write overhead.

## Approximation Strategies

Because optimal graph partitioning is NP-hard, real systems use heuristics:

### METIS / Spectral Partitioning

Multilevel graph partitioning algorithms (METIS being the canonical implementation). The graph is coarsened into smaller representative graphs, partitioned, then the partition is projected back. Produces near-optimal cuts for medium-sized graphs but requires the full graph topology upfront — not practical for streaming or dynamic graphs.

### Label Propagation

Each node starts with a label (its partition). Iteratively, each node adopts the most common label among its neighbors. Cheap and parallelizable, but produces lower-quality cuts than METIS. Used in systems that prioritize speed over optimality.

### Streaming Partitioning

Assigns nodes to partitions as they arrive (no global view). Heuristic: send a node to the partition containing the most of its already-assigned neighbors. Works at scale but quality degrades for highly irregular graphs.

### Locality-Aware Manual Partitioning

In practice, domain knowledge often beats algorithms. If a fraud detection graph clusters by geography or transaction network, partitioning by that attribute keeps most traversals local. This is the approach Neo4j recommends — design your data model so that common queries stay within a shard.

## The Practical Consequence

Graph databases do not horizontally scale as naturally as key-value or document stores. In most real deployments:

- **Graphs fit on one machine** (vertical scaling + replication for availability)
- **Sharding is reserved for graphs that cannot fit** and accepted with a performance cost for cross-shard traversals
- **Denormalization and data duplication** are used to keep hot subgraphs co-located

This is a fundamental architectural tradeoff. Neo4j's recommendation for very large graphs is to use its **Fabric / Composite Databases** feature, which allows you to manually route queries to specific shards — but the burden of partitioning logic falls on the application.

## Contrast with Other Databases

| Database | Partitioning strategy | Why it works |
|----------|-----------------------|-------------|
| Redis | Hash slots (key % 16384) | Records are independent; no cross-record relationships |
| MongoDB | Hashed or range shard key | Documents are mostly self-contained |
| Cassandra | Consistent hashing on partition key | Rows within a partition are co-located by design |
| **Graph DB** | Approximated edge-cut / vertex-cut | No natural key; edges create cross-partition dependencies |

> **See also:** [Partitioning Strategies](./02-partitioning-strategies.md) for how hash, range, and consistent hashing work in databases where partitioning is tractable. [Graphs and Traversal](../02-data-structures/05-graphs-and-traversal.md) for why graph traversal makes cross-partition hops so expensive.
