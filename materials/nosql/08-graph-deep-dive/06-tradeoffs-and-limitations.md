---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Tradeoffs and Limitations

```{note}
This lesson requires the Neo4j lab. Run `make lab-neo4j` before starting.
```

Graph databases are a genuine solution to a real class of problems. But they are also misapplied frequently — chosen because the data "could be a graph," not because the queries demand it. This lesson is about understanding what graph databases are bad at, where they sit on the CAP triangle, how they handle transactions, and what operational surprises you should expect.

---

## What Graph Databases Are Bad At

### Global Aggregations

Graph traversal is local and relational. "How many nodes of type `:Transaction` have `amount > 10000`?" is not a traversal — it's a full scan. Graph databases handle this with indexes, but they are not optimized for it the way a columnar analytics database is.

If your primary workload is "aggregate over many records by attribute" (sales reports, time-series analysis, metrics dashboards), a relational or columnar database will outperform a graph database by a large margin. Graph databases optimize for local, pointer-following operations, not global attribute scans.

### Tabular / Uniform Data

If all your entities have the same structure and your queries are primarily "filter by column, return rows," there is no benefit to a graph model. Worse, you pay the overhead of a graph database (memory, complexity, licensing) for workloads that MongoDB, PostgreSQL, or even SQLite would handle faster.

The question to ask before choosing a graph database: "Are relationships the primary thing my queries traverse?" If the answer is "mostly, we just filter and aggregate," use a different tool.

### High-Throughput Write Ingestion

Graph databases are generally write-constrained compared to key-value stores or time-series databases. Adding a new node with relationships requires updating the node, creating relationship records, and maintaining indexes. Cassandra can ingest millions of writes per second; Neo4j is typically measured in thousands to tens of thousands for mixed graph workloads.

If your graph is also an event stream ingestion target, you likely need a staging layer (Kafka → batch graph load) rather than direct writes.

---

## CAP Positioning

> **Core Concept:** See [CAP Theorem](../../core-concepts/04-distributed-systems/01-cap-theorem.md) for the fundamental tradeoff between consistency, availability, and partition tolerance.

Neo4j is a **CP system** — it prioritizes consistency over availability when a network partition occurs. In a causal cluster, if the primary fails and a new leader cannot be elected (e.g., due to a partition), write operations will fail rather than proceed with potentially inconsistent state.

This is the appropriate choice for most graph workloads. Fraud detection, access control, and knowledge graphs require that the data be correct — a recommendation engine serving stale data for a few seconds is acceptable; a fraud detection system that has diverged replicas and allows a transaction that should be blocked is not.

> **Core Concept:** See [ACID vs BASE](../../core-concepts/04-distributed-systems/02-acid-vs-base.md) for why CP systems tend toward ACID behavior while AP systems tend toward BASE.

---

## ACID in Neo4j

Neo4j supports full ACID transactions. Each write operation (whether a single `CREATE` or a complex multi-step mutation) runs within a transaction. If any step fails, the entire transaction rolls back. Reads can be wrapped in a read transaction for a consistent snapshot.

This is significant: graph databases do not sacrifice transactional integrity for performance. A fraud detection write that creates 5 nodes and 12 relationships either fully commits or fully rolls back. There is no partial-write ambiguity.

The cost: ACID transactions require locking and coordination, which limits write throughput. This is the same tradeoff as any ACID database — PostgreSQL has the same constraint.

```{code-cell} python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))

with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")

with driver.session() as session:
    # Transactional write: all-or-nothing
    tx = session.begin_transaction()
    try:
        tx.run("CREATE (a:Account {id: 'ACC-001', balance: 1000.0})")
        tx.run("CREATE (b:Account {id: 'ACC-002', balance: 500.0})")
        tx.run("""
            MATCH (a:Account {id: 'ACC-001'}), (b:Account {id: 'ACC-002'})
            CREATE (a)-[:TRANSFERRED {amount: 200.0, ts: timestamp()}]->(b)
            SET a.balance = a.balance - 200.0,
                b.balance = b.balance + 200.0
        """)
        tx.commit()
        print("Transaction committed: transfer of 200 recorded")
    except Exception as e:
        tx.rollback()
        print(f"Transaction rolled back: {e}")

with driver.session() as session:
    result = session.run("""
        MATCH (a:Account)
        RETURN a.id AS id, a.balance AS balance
        ORDER BY a.id
    """)
    print("Account balances after transfer:")
    for r in result:
        print(f"  {r['id']}: {r['balance']}")

driver.close()
```

---

## The Supernode Problem

A **supernode** is a node with an extraordinarily high number of relationships — a celebrity in a social network (millions of followers), a global hub in a transport network, a root certificate authority. Supernodes are a structural performance problem in graph databases.

When you traverse to or from a supernode, Neo4j must iterate over millions of relationships. A query that seems simple — "find all accounts that transacted with this central exchange" — can become extremely slow if the exchange node has 50 million outgoing edges.

Strategies:
- **Relationship type filtering**: only traverse specific relationship types at supernodes
- **Property filtering**: add a `LIMIT` or property condition before expanding a supernode
- **Modeling the supernode away**: instead of a single hub node, use intermediate category nodes to split the fan-out
- **Accept the limitation**: for some queries, supernodes are unavoidable and you design around them

---

## Summary: When to Use vs. When to Avoid

| Use a graph database when... | Avoid a graph database when... |
|------------------------------|-------------------------------|
| Relationships are the primary query target | Primary queries are attribute-based scans |
| Query depth is variable or deep | Data is naturally tabular and uniform |
| You need path finding or community detection | High-throughput bulk ingestion is required |
| Schema flexibility is important | Simple key-value or document model suffices |
| Relationship properties matter | Analytics / aggregation is the main workload |

---

**← Back: [Real-World Use Cases](05-real-world-use-cases.md)** | **Next: [Replication →](07-replication.md)** | [Course Home](../README.md)
