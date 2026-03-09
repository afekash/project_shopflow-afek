---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# The Property Graph Model

Graph databases are not all the same. There are two dominant data models for representing graphs: the **property graph** and **RDF triples**. Neo4j, Amazon Neptune (graph mode), and most modern graph databases use the property graph model. Understanding what it is — and what it enables — is the foundation for everything else in this module.

---

## The Four Building Blocks

A property graph is built from four concepts:

**Nodes** are the entities in your domain. A node represents one thing: a person, a product, a transaction, a device. Nodes are the "nouns" of your graph.

**Relationships** (also called edges) connect two nodes. They are always directed — they have a start node and an end node. A relationship represents an action, a connection, or an association between two entities. Relationships are the "verbs."

**Labels** classify nodes and relationships by type. A node can have multiple labels: `(:Person:Employee)`. A relationship has exactly one type: `[:WORKS_AT]`. Labels are used to filter and index — when you query for all `Person` nodes, Neo4j only looks at nodes tagged with that label.

**Properties** are key-value pairs attached to nodes or relationships. A `Person` node might have `{name: "Alice", age: 34}`. A `KNOWS` relationship might have `{since: 2019, strength: "close"}`. Properties can hold any scalar value or list of scalars.

```
(alice:Person {name:"Alice", age:34})
  -[:KNOWS {since:2019}]->
(bob:Person {name:"Bob", age:28})
```

This is a complete, self-contained fact: Alice knows Bob, they've known each other since 2019, and both have names and ages.

---

## Index-Free Adjacency: The Key Performance Property

In a relational database, a "relationship" between two rows is represented as a foreign key. To find all friends of Alice, the database must:
1. Look up Alice's row to find her ID
2. Scan the `friendships` table for rows where `user_id = alice_id` (or use an index — O(log n))
3. For each result, look up the friend's row by ID (another O(log n) per friend)

In a native graph database, each node stores **direct pointers** to its neighboring nodes. Finding Alice's friends means:
1. Look up Alice's node
2. Follow the pointers stored on that node — each one is a direct memory address

No index lookup. No scan. Each hop is O(1), not O(log n).

> **Core Concept:** See [Graphs and Traversal](../../core-concepts/02-data-structures/05-graphs-and-traversal.md) for the adjacency-list representation that makes this possible.

This is the mechanism behind the performance advantage shown in the previous lesson. The property graph model was specifically designed to support this storage layout — relationships are first-class objects with their own identity, stored adjacent to the nodes they connect.

---

## Contrast: RDF / Triple Stores

The other major graph model is **RDF** (Resource Description Framework). RDF represents everything as triples:

```
<subject>  <predicate>  <object>
Alice      knows        Bob
Bob        livesIn      London
```

RDF is used in semantic web, knowledge bases, and linked data (Wikidata, DBpedia). It uses SPARQL as its query language. The key differences from property graphs:

| | Property Graph | RDF / Triple Store |
|--|----------------|--------------------|
| **Data unit** | Node + relationship + properties | Triple (subject-predicate-object) |
| **Relationship properties** | Native | Requires reification (awkward) |
| **Query language** | Cypher (or Gremlin) | SPARQL |
| **Ontology / inference** | Not built-in | Core feature (OWL, RDFS) |
| **Use case** | Application graphs, analytics | Knowledge bases, semantic web |

For most application development — fraud detection, recommendations, network analysis — the property graph model is more intuitive and more performant. RDF shines when you need standardized ontologies and inference across globally linked data.

---

## Schema Flexibility

Unlike relational databases, property graphs do not enforce a schema by default. Two nodes with the same label can have completely different properties. A `Person` node can have `{name, email, phone}` while another `Person` node has `{name, company, title}`.

This is not just a convenience — it reflects how graph data tends to evolve. Real-world entities don't all have the same attributes. A product in an e-commerce graph might be a book (with author, ISBN) or a physical item (with dimensions, weight) or a subscription (with billing cycle). The property graph handles all three as `(:Product)` nodes with different properties, without requiring a `NULL`-heavy table or a complex polymorphism pattern.

You can add constraints and indexes when needed — Neo4j supports uniqueness constraints and existence constraints on specific labels — but the default is flexible.

---

## Hands-On: Warm Introduction Routing

The previous lesson showed variable-depth traversal. This example shows what **relationship properties** unlock: queries where the *quality* of a path matters, not just its length.

The scenario: you want an introduction to someone. The naive answer is "shortest path" — fewest hops. But a 4-hop path through people you genuinely know beats a 2-hop path through a coworker you barely know. The graph stores a `familiarity` score (1–10) on every edge, and we want the path whose weakest link is strongest — the classic **maximum bottleneck path** problem.

```{code-cell} python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))

with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")

    session.run("""
        CREATE (dan:Person      {name: 'Dan'})
        CREATE (maya:Person     {name: 'Maya'})
        CREATE (roy:Person      {name: 'Roy'})
        CREATE (noa:Person      {name: 'Noa'})
        CREATE (uri:Person      {name: 'Uri'})
        CREATE (tal:Person      {name: 'Tal'})

        // Warm family path: strong bonds all the way through
        CREATE (dan)-[:KNOWS  {familiarity: 10, type: 'sibling'}]->(maya)
        CREATE (maya)-[:KNOWS {familiarity:  9, type: 'friend'}]->(noa)
        CREATE (noa)-[:KNOWS  {familiarity:  8, type: 'friend'}]->(uri)
        CREATE (uri)-[:KNOWS  {familiarity:  9, type: 'sibling'}]->(tal)

        // Cold shortcut: fewer hops but weak links
        CREATE (dan)-[:KNOWS {familiarity:  3, type: 'coworker'}]->(roy)
        CREATE (roy)-[:KNOWS {familiarity:  2, type: 'neighbor'}]->(tal)
    """)

print("Social graph created")
```

```{code-cell} python
# Find all paths from Dan to Tal up to 5 hops.
#
# Cost model: each hop contributes 1/familiarity to the total accumulated cost.
#   - familiarity=10  →  hop cost = 0.10  (very warm, cheap)
#   - familiarity=2   →  hop cost = 0.50  (cold, expensive)
#
# Costs accumulate across hops — a longer cold path is genuinely worse than a
# shorter warm one. Max possible cost per hop is 1.0 (familiarity=1).
with driver.session() as session:
    result = session.run("""
        MATCH path = (dan:Person {name: 'Dan'})-[:KNOWS*1..5]->(tal:Person {name: 'Tal'})
        WITH path,
             [r IN relationships(path) | r.familiarity] AS scores,
             [n IN nodes(path) | n.name]                AS names,
             [r IN relationships(path) | r.type]        AS rel_types
        WITH names, rel_types, length(path) AS hops, scores,
             reduce(cost = 0.0, s IN scores | cost + (1.0 / s)) AS total_cost
        RETURN names, rel_types, hops, scores,
               round(total_cost, 3) AS coldness
        ORDER BY coldness ASC
    """)

    print("Introduction paths from Dan to Tal, ranked by warmth (coldness ↑ = worse):\n")
    print(f"  {'Coldness':>8}   {'Hops':>4}   Route")
    print(f"  {'-'*8}   {'-'*4}   {'-'*60}")
    for r in result:
        steps = list(zip(r["names"], r["rel_types"] + [""]))
        route = " → ".join(
            f"{name} [{rel}]" if rel else name for name, rel in steps
        )
        hop_details = " + ".join(f"1/{f}={1/f:.2f}" for f in r["scores"])
        print(f"  {r['coldness']:>8.3f}   {r['hops']:>4}   {route}")
        print(f"  {'':>8}   {'':>4}   {hop_details}  =  {r['coldness']:.3f}")
```

```{code-cell} python
# Shortest path by hop count — the naive answer
with driver.session() as session:
    result = session.run("""
        MATCH p = shortestPath(
            (dan:Person {name: 'Dan'})-[:KNOWS*]-(tal:Person {name: 'Tal'})
        )
        WITH p,
             [r IN relationships(p) | r.familiarity] AS scores,
             [n IN nodes(p) | n.name]                AS names,
             [r IN relationships(p) | r.type]        AS rel_types
        WITH names, rel_types, length(p) AS hops, scores,
             reduce(cost = 0.0, s IN scores | cost + (1.0 / s)) AS total_cost
        RETURN names, rel_types, hops, scores,
               round(total_cost, 3) AS coldness
    """)
    print("Shortest path (fewest hops):\n")
    for r in result:
        steps = list(zip(r["names"], r["rel_types"] + [""]))
        route = " → ".join(
            f"{name} [{rel}]" if rel else name for name, rel in steps
        )
        hop_details = " + ".join(f"1/{f}={1/f:.2f}" for f in r["scores"])
        print(f"  {r['hops']} hop(s)  |  coldness = {r['coldness']:.3f}")
        print(f"  Path:  {route}")
        print(f"  Cost:  {hop_details}  =  {r['coldness']:.3f}")

driver.close()
```

The key insight: **shortest path is the wrong metric for warm introductions**. The coldness score accumulates `1 / familiarity` across every hop — so a single weak link (familiarity=2, cost=0.50) meaningfully drags up the total, and a longer path of strong ties can still beat a short cold one. This cost lives entirely on the relationships — it could not be expressed without edge properties.

---

**← Back: [Why Graph Databases?](01-why-graphs.md)** | **Next: [Traversal and Pattern Matching →](03-traversal-and-pattern-matching.md)** | [Course Home](../README.md)
