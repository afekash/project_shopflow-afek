# Graph Databases

## What Is a Graph Database?

A graph database stores data as a network of **nodes** (entities) and **edges** (relationships). Both nodes and edges can have **properties** (key-value attributes). Unlike relational databases, relationships are first-class citizens — stored as explicit connections rather than derived at query time through joins.

```
        (alice:Person)
         name: "Alice"
              │
              │ [:WORKS_AT {since: 2022}]
              ▼
        (acme:Company)
         name: "Acme Corp"
              │
              │ [:LOCATED_IN]
              ▼
        (city:City)
         name: "Tel Aviv"
```

## The Key Insight: Index-Free Adjacency

In a relational database, a JOIN performs an index lookup — O(log n) per hop. At 3 hops across millions of rows, that becomes expensive fast.

A graph database stores each node with **direct pointers to its neighbors**. Following a relationship is a memory pointer dereference — O(1) per hop, regardless of graph size. This is why a 3-hop social network query that takes minutes in PostgreSQL takes milliseconds in Neo4j.

## When to Use a Graph Database

Use a graph database when **relationships are the primary thing your queries traverse**:

- Social networks: friends-of-friends, mutual connections
- Fraud detection: accounts sharing a device, phone, or bank card across transaction chains
- Recommendation engines: collaborative filtering as graph traversal
- Knowledge graphs: entities and semantic relationships for AI/RAG systems
- IT and network topology: blast radius analysis, dependency chains
- Supply chain: tier-N supplier risk, alternative sourcing paths

Avoid graph databases when your primary queries are attribute-based aggregations, bulk ingestion, or simple key-value lookups. See [Tradeoffs and Limitations](../08-graph-deep-dive/06-tradeoffs-and-limitations.md).

## Main Players

| Database | Notable For |
|----------|------------|
| **Neo4j** | Most mature, Cypher language, rich tooling, causal clustering |
| **Amazon Neptune** | Managed, supports property graphs (Gremlin) and RDF (SPARQL) |
| **ArangoDB** | Multi-model: graph + document + key-value |
| **TigerGraph** | Distributed graph at enterprise scale |
| **Memgraph** | In-memory, Cypher-compatible, real-time analytics |

## Go Deeper

The overview above covers what graph databases are. The **[Graph Deep Dive module](../08-graph-deep-dive/01-why-graphs.md)** covers how they work, when to use them, and what they're bad at:

| Lesson | Topic |
|--------|-------|
| [Why Graphs?](../08-graph-deep-dive/01-why-graphs.md) | The problem graphs solve vs. relational JOINs at depth |
| [Property Graph Model](../08-graph-deep-dive/02-property-graph-model.md) | Nodes, edges, labels, properties, index-free adjacency |
| [Traversal & Pattern Matching](../08-graph-deep-dive/03-traversal-and-pattern-matching.md) | Variable-depth traversal, pattern queries, shortest path |
| [Graph Algorithms](../08-graph-deep-dive/04-graph-algorithms-overview.md) | PageRank, community detection, pathfinding |
| [Real-World Use Cases](../08-graph-deep-dive/05-real-world-use-cases.md) | Fraud/cyber, ML/AI, knowledge graphs, infrastructure |
| [Tradeoffs & Limitations](../08-graph-deep-dive/06-tradeoffs-and-limitations.md) | What graph DBs are bad at, CAP, ACID, supernodes |
| [Replication](../08-graph-deep-dive/07-replication.md) | Causal clustering, Raft consensus, read routing |
| [Sharding](../08-graph-deep-dive/08-sharding.md) | Why graph sharding is hard, Fabric, comparison with KV/doc sharding |

---

**Next:** [Choosing the Right Database →](05-choosing-the-right-database.md)

---

[← Back: Column-Family Stores](03-column-family-stores.md) | [Course Home](../README.md)
