# Sharding Graph Databases

Replication gives you high availability — multiple copies of the same data for redundancy and read scaling. Sharding is different: it gives you capacity — splitting the data across machines so that no single machine needs to hold all of it.

For most databases, sharding is hard but tractable. For graph databases, sharding is genuinely difficult in a way that has no clean solution. Understanding why this is the case is essential context for any engineer designing systems at scale.

---

## Why Sharding Other Databases Is "Easy"

In a key-value store like Redis, each record is independent. Given a key, a hash function maps it to a shard. No record references another record in a way that requires both to be on the same shard. A read request for key `user:42:session` can go to shard 3, and a read request for `user:43:session` can go to shard 1 — neither operation knows the other exists.

In a document store like MongoDB, documents are largely self-contained. A sharded collection routes each document to a shard based on a shard key. Cross-document references exist (DBRefs), but most queries target a single document or a set of documents on the same shard.

The reason sharding works for these databases: **their records are mostly independent**. You can physically separate them without breaking most queries.

> **Core Concept:** See [Partitioning Strategies](../../core-concepts/03-scaling/02-partitioning-strategies.md) for how hash, range, and consistent hashing partitioning work in systems where records are independent.

---

## Why Graph Sharding Is Hard

A graph is, by definition, a structure of **dependencies between records**. Every edge connects two nodes. If those two nodes end up on different shards, any query that traverses that edge requires a **network hop** between shards.

In a traversal that follows 5 hops, if each hop crosses a shard boundary, that's 5 network round trips — turning a sub-millisecond pointer dereference into a multi-hundred-millisecond distributed query.

Finding a partition that minimizes cross-shard edges (the **minimum edge cut** problem) is NP-hard. As the graph grows, no algorithm can compute the optimal partition efficiently.

> **Core Concept:** See [Graph Partitioning](../../core-concepts/03-scaling/04-graph-partitioning.md) for the full explanation of edge-cut vs vertex-cut, approximation algorithms, and why the NP-hardness matters in practice.

---

## The Two Partitioning Strategies

When a graph must be sharded, two fundamentally different strategies exist:

### Edge-Cut Partitioning

Nodes are assigned to shards. Edges that connect nodes on different shards are "cut edges" — they cross a shard boundary.

```
Shard 1: (Alice) — (Bob) — (Carol)
                               ↕  ← cut edge
Shard 2: (Dave) — (Eve)
```

Traversing Alice → Bob → Carol is local to Shard 1. But traversing Carol → Dave requires a cross-shard call to Shard 2. In a graph with millions of highly-connected nodes (a social network, a fraud graph), the fraction of cut edges is high, and traversal performance degrades.

### Vertex-Cut Partitioning

Edges are assigned to shards. Nodes that appear in edges on multiple shards are **replicated** — a ghost copy exists on each shard that hosts one of its edges.

```
Shard 1: (Alice) — (Carol edge) — copy of (Carol)
Shard 2: copy of (Carol) — (Dave edge) — (Dave)
```

Traversal within each shard is local, but writes to Carol must update all replicas. Storage increases proportionally to how many shards a high-degree node touches.

Neither strategy is universally better. The choice depends on graph topology:
- Vertex-cut is better for **dense, hub-and-spoke graphs** (many supernodes). When a small number of nodes connect to millions of others, edge-cut would place the majority of edges across shard boundaries, making almost every traversal a cross-shard call. Vertex-cut instead replicates those high-degree nodes onto every shard that needs them, keeping traversals local at the cost of write amplification to all replicas.
- Edge-cut is better for **balanced, cluster-structured graphs** (natural communities). When the graph breaks naturally into dense clusters with only a few inter-cluster edges, most traversals stay within a single shard and only a small fraction of edges are ever "cut." Vertex-cut would add replication overhead without any benefit, since there are no supernodes to justify it.

---

## Neo4j's Approach: Fabric and Composite Databases

Neo4j does not attempt automatic graph partitioning — the problem is too hard to solve generically. Instead, it provides **Composite Databases** (formerly Fabric): a federation layer that allows a single Cypher query to be routed across multiple independent Neo4j databases.

The architecture:

```
Client → Composite Database (routing layer)
            ├─ routes sub-query A → Shard DB 1
            ├─ routes sub-query B → Shard DB 2
            └─ merges results before returning to client
```

The key difference from automatic sharding: **the application is responsible for knowing which data is on which shard**. The query must be written with explicit `USE` clauses to target specific shards. The Composite layer does not transparently route a traversal that crosses shard boundaries — that is the application developer's problem to solve.

This means graph sharding in Neo4j is a **modeling decision**, not an infrastructure decision. You design your data model so that the queries you care about stay within a shard. For example:
- A fraud detection system might shard by country — most fraud rings are geographically local
- A supply chain graph might shard by product category
- A social network might shard by user registration cohort

Queries that genuinely cross shards are accepted as expensive, and you design to minimize them.

---

## Practical Implications

| Scenario | Recommendation |
|----------|---------------|
| Graph fits on one machine (< ~500 GB) | Single instance + replication for availability. Don't shard. |
| Graph is large but queries are local | Shard by domain (geography, category). Use Composite DBs with explicit routing. |
| Graph is large and queries are global | Consider whether a graph DB is the right tool. Large-scale graph analytics may need Spark GraphX or specialized tools. |
| Reads are the bottleneck, not storage | Add secondaries (read replicas). No sharding needed. |

> **Compare with Redis Cluster:** Redis shards trivially because keys are independent. A Redis Cluster with 6 nodes can hold 6x the data with no performance penalty for writes. A Neo4j Composite with 6 shards may perform *worse* than a single instance if traversals frequently cross shard boundaries. The structural difference in how the data relates is the reason.

The honest answer to "can graph databases scale horizontally?" is: **yes, but not as transparently as key-value or document stores, and with real performance costs for cross-shard traversals**. Graph databases scale vertically first, replicate second, and shard only when forced to by data volume — not by request load.

---

**← Back: [Replication](07-replication.md)** | [Course Home](../README.md)
