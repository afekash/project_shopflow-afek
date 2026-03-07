---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Why Graph Databases?

```{note}
This lesson requires the Neo4j lab. Run `make lab-neo4j` before starting.
```

Every database is optimized for a particular shape of question. Relational databases are optimized for structured records and set operations. Key-value stores are optimized for point lookups. Graph databases are optimized for a different class of question entirely: **how are things connected, and what can I reach from here?**

This lesson is about recognizing when that question is what your problem is really asking.

---

## The Relationship Problem

Consider a fraud detection system. You want to find all accounts that share a device with an account that has been flagged for fraud. In a relational database, that's a join: `accounts → device_links → accounts`. But fraud rings don't stop there. The flagged account shares a phone number with another account, which shares a bank card with three more, which share addresses with others still. You're not asking one join — you're asking a join that recurses to an unknown depth.

Relational databases can do this with recursive CTEs, but the cost grows with depth. Each hop is an index lookup: O(log n) per join, per hop, per row. At depth 4 or 5, across millions of accounts, the query plan explodes.

The same pattern appears in:
- Social networks ("friends of friends who live in Berlin")
- Recommendation engines ("users who bought this also bought...")
- Network topology ("what is the blast radius if this router fails?")
- Supply chain ("which suppliers are affected by this factory disruption?")
- Access control ("can this service account reach this data?")

The shape of all these problems is the same: **traverse a web of relationships to arbitrary depth, efficiently**.

> **Core Concept:** See [Graphs and Traversal](../../core-concepts/02-data-structures/05-graphs-and-traversal.md) for why adjacency-list traversal is O(degree) per hop, and why that matters for deep queries.

---

## The Cost of Joins at Depth

Here's the concrete performance difference. A social network query: "find all friends within 3 degrees of separation for user Alice."

In a relational database with 1 million users and an average of 200 friends each:

| Depth | Rows touched (approx.) | Index lookups |
|-------|------------------------|---------------|
| 1 hop | 200 | 200 × O(log n) |
| 2 hops | 200² = 40,000 | 40,000 × O(log n) |
| 3 hops | 200³ = 8,000,000 | 8M × O(log n) |

In a graph database with index-free adjacency, following a relationship is a **pointer dereference** — O(1) per hop, not O(log n). The 3-hop query touches 8 million relationships, but each one is a direct memory access, not an index scan.

This is not a constant-factor improvement. At 5 or 6 hops, the relational query has timed out. The graph query is still running in milliseconds.

---

## When to Use a Graph Database

A graph database is the right choice when:

1. **Relationships are central to your query**, not just a foreign key lookup
2. **Depth is variable or unknown** — you don't know in advance how many hops you'll need
3. **The data forms a network** — nodes with many-to-many connections that reference each other
4. **Local structure matters** — you care about neighborhoods, clusters, or paths, not global aggregates

A graph database is **not** the right choice when:
- Your primary access pattern is filtering or aggregating over large attribute sets ("all orders placed in Q3 by customers in Europe")
- Data is naturally tabular with few cross-record relationships
- You need to ingest millions of records per second (graph databases optimize for traversal, not bulk write)
- Your graph is small enough that a relational recursive CTE is fast enough

> **Core Concept:** See [Polyglot Persistence](../../core-concepts/06-architecture-patterns/03-polyglot-persistence.md) for how graph databases fit alongside relational and other stores in a multi-database architecture.

---

## Hands-On: Comparing Approaches

The code below builds a small social network in Neo4j and demonstrates the depth-traversal query. The point is not the syntax — it's that the query expresses the depth naturally, and Neo4j executes it by walking pointers.

```{code-cell} python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))

with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")

    session.run("""
        CREATE (alice:Person {name: 'Alice'})
        CREATE (bob:Person   {name: 'Bob'})
        CREATE (carol:Person {name: 'Carol'})
        CREATE (dave:Person  {name: 'Dave'})
        CREATE (eve:Person   {name: 'Eve'})
        CREATE (frank:Person {name: 'Frank'})
        CREATE (alice)-[:KNOWS]->(bob)
        CREATE (alice)-[:KNOWS]->(carol)
        CREATE (bob)-[:KNOWS]->(dave)
        CREATE (carol)-[:KNOWS]->(dave)
        CREATE (dave)-[:KNOWS]->(eve)
        CREATE (eve)-[:KNOWS]->(frank)
    """)

print("Graph created: 6 people, 6 KNOWS relationships")
```

```{code-cell} python
with driver.session() as session:
    result = session.run("""
        MATCH (alice:Person {name: 'Alice'})-[:KNOWS*1..3]->(person)
        RETURN DISTINCT person.name AS name, 
               min(length(shortestPath((alice)-[:KNOWS*]->(person)))) AS hops
        ORDER BY hops
    """)
    print("People reachable from Alice within 3 hops:")
    for record in result:
        print(f"  {record['name']} ({record['hops']} hop(s))")
```

```{code-cell} python
driver.close()
```

The `[:KNOWS*1..3]` syntax expresses variable-length traversal. Neo4j evaluates this by following pointers — it never touches nodes that are not reachable. A relational database would need to union multiple self-joins or use a recursive CTE, re-scanning the index at each depth level.

---

**Next:** [The Property Graph Model →](02-property-graph-model.md) | [Course Home](../README.md)
