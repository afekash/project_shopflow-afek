---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# The Property Graph Model

```{note}
This lesson requires the Neo4j lab. Run `make lab-neo4j` before starting.
```

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

## Hands-On: Building a Property Graph

```{code-cell} python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))

with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")

    session.run("""
        CREATE (neo4j_inc:Company {name: 'Neo4j Inc', founded: 2007})
        CREATE (graphdb:Product   {name: 'Neo4j', type: 'Database', category: 'Graph'})
        CREATE (bloom:Product     {name: 'Bloom',  type: 'Tool',     category: 'Visualization'})
        CREATE (alice:Person      {name: 'Alice',  role: 'Engineer'})
        CREATE (bob:Person        {name: 'Bob',    role: 'Architect'})

        CREATE (alice)-[:WORKS_AT  {since: 2021}]->(neo4j_inc)
        CREATE (bob)-[:WORKS_AT    {since: 2019}]->(neo4j_inc)
        CREATE (alice)-[:USES      {frequency: 'daily'}]->(graphdb)
        CREATE (bob)-[:USES        {frequency: 'weekly'}]->(bloom)
        CREATE (neo4j_inc)-[:MAKES]->(graphdb)
        CREATE (neo4j_inc)-[:MAKES]->(bloom)
        CREATE (alice)-[:KNOWS     {context: 'work'}]->(bob)
    """)

print("Property graph created")
```

```{code-cell} python
with driver.session() as session:
    result = session.run("""
        MATCH (p:Person)-[r:WORKS_AT]->(c:Company)-[:MAKES]->(prod:Product)
        RETURN p.name AS person, p.role AS role, 
               r.since AS joined, prod.name AS product
        ORDER BY r.since
    """)
    print("People, their company, and the products their company makes:")
    for record in result:
        print(f"  {record['person']} ({record['role']}, joined {record['joined']}) → {record['product']}")
```

```{code-cell} python
with driver.session() as session:
    result = session.run("""
        MATCH (p:Person)-[:USES]->(prod:Product)
        RETURN p.name AS person, prod.name AS product, prod.category AS category
    """)
    print("Who uses what:")
    for record in result:
        print(f"  {record['person']} uses {record['product']} ({record['category']})")

driver.close()
```

Notice that nodes of the same label (`Product`) have different meaningful properties (`type`, `category`), and relationships carry their own properties (`since`, `frequency`). This richness is native to the property graph model — not bolted on.

---

**← Back: [Why Graph Databases?](01-why-graphs.md)** | **Next: [Traversal and Pattern Matching →](03-traversal-and-pattern-matching.md)** | [Course Home](../README.md)
