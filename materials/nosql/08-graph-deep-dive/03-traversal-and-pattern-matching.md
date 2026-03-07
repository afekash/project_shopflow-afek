---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Traversal and Pattern Matching

```{note}
This lesson requires the Neo4j lab. Run `make lab-neo4j` before starting.
```

A graph database is only as useful as your ability to ask it questions. The two fundamental operations are **traversal** — following relationships from one node to another — and **pattern matching** — finding subgraphs that match a structural description. This lesson is about the concepts behind both, using Cypher as the vehicle to make them concrete.

---

## Traversal: Following the Graph

Traversal starts at one or more nodes and walks relationships to find connected nodes. The critical parameters are:

**Direction** — do you follow relationships in their declared direction (outgoing), against it (incoming), or either way (undirected)?

**Relationship type filter** — do you only follow relationships of a specific type, or any relationship?

**Depth** — how many hops do you go? A fixed depth (exactly 2 hops) or a variable range (1 to 5 hops)?

These three parameters determine what part of the graph you see. The same node with the same data gives completely different results depending on how you traverse from it.

> **Core Concept:** See [Graphs and Traversal](../../core-concepts/02-data-structures/05-graphs-and-traversal.md) for BFS vs DFS strategies and their time complexity. Graph databases use BFS variants for shortest-path queries and DFS for reachability.

The depth parameter is particularly important because it's where graph databases separate from relational ones. A relational JOIN is always fixed-depth: you join table A to table B. In a graph, `[:KNOWS*1..5]` means "follow KNOWS relationships between 1 and 5 times." The engine figures out the paths; you describe the structure.

---

## Pattern Matching: Describing Subgraphs

Pattern matching is the more general operation. Instead of saying "start here and walk there," you describe a structural template and ask the database to find all parts of the graph that match it.

A pattern describes:
- Node types (labels) and their properties
- Relationship types and their properties
- How they connect

The database scans the graph and returns all subgraphs that fit the description. This is conceptually similar to a SQL `WHERE` clause — but operating on graph structure rather than column values.

The power of pattern matching is that it finds structure you didn't know existed. You don't need to know *which* nodes are involved — you describe the *shape* and the database finds all instances of that shape.

---

## Path Queries: Shortest Path and All Paths

Two specific traversal patterns appear constantly in graph applications:

**Shortest path** — find the path between two nodes that traverses the fewest relationships (or the minimum total weight, for weighted graphs). Used in: fraud rings (shortest connection between a flagged account and a clean account), routing, degrees of separation.

**All paths** — find every path between two nodes, up to a depth limit. Used in: impact analysis ("all ways service A depends on service B"), access control ("all permission chains that grant user X access to resource Y").

Both are expensive on large, dense graphs — the number of paths can grow exponentially with depth. Graph databases handle this with depth limits and early termination strategies.

---

## Hands-On: Traversal and Pattern Queries

```{code-cell} python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))

with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")

    session.run("""
        CREATE (alice:Person  {name: 'Alice',  city: 'NYC'})
        CREATE (bob:Person    {name: 'Bob',    city: 'NYC'})
        CREATE (carol:Person  {name: 'Carol',  city: 'London'})
        CREATE (dave:Person   {name: 'Dave',   city: 'London'})
        CREATE (eve:Person    {name: 'Eve',    city: 'NYC'})
        CREATE (frank:Person  {name: 'Frank',  city: 'Berlin'})
        CREATE (grace:Person  {name: 'Grace',  city: 'Berlin'})

        CREATE (alice)-[:KNOWS]->(bob)
        CREATE (alice)-[:KNOWS]->(carol)
        CREATE (bob)-[:KNOWS]->(dave)
        CREATE (carol)-[:KNOWS]->(dave)
        CREATE (dave)-[:KNOWS]->(eve)
        CREATE (dave)-[:KNOWS]->(frank)
        CREATE (frank)-[:KNOWS]->(grace)

        CREATE (alice)-[:WORKS_WITH]->(eve)
        CREATE (bob)-[:WORKS_WITH]->(carol)
    """)

print("Graph created")
```

```{code-cell} python
# Fixed-depth traversal: direct friends only
with driver.session() as session:
    result = session.run("""
        MATCH (alice:Person {name: 'Alice'})-[:KNOWS]->(friend)
        RETURN friend.name AS name, friend.city AS city
    """)
    print("Alice's direct connections (depth 1):")
    for r in result:
        print(f"  {r['name']} ({r['city']})")
```

```{code-cell} python
# Variable-depth traversal: up to 3 hops, return distinct reachable nodes
with driver.session() as session:
    result = session.run("""
        MATCH (alice:Person {name: 'Alice'})-[:KNOWS*1..3]->(person)
        RETURN DISTINCT person.name AS name, person.city AS city
        ORDER BY name
    """)
    print("Everyone Alice can reach within 3 KNOWS hops:")
    for r in result:
        print(f"  {r['name']} ({r['city']})")
```

```{code-cell} python
# Pattern matching: find pairs of people in the same city who have a common friend
with driver.session() as session:
    result = session.run("""
        MATCH (a:Person)-[:KNOWS]->(common:Person)<-[:KNOWS]-(b:Person)
        WHERE a.city = b.city AND a.name < b.name
        RETURN a.name AS person_a, b.name AS person_b, 
               collect(common.name) AS via, a.city AS city
    """)
    print("Same-city pairs with a common KNOWS connection:")
    for r in result:
        print(f"  {r['person_a']} & {r['person_b']} ({r['city']}) — via {r['via']}")
```

```{code-cell} python
# Shortest path between two specific nodes
with driver.session() as session:
    result = session.run("""
        MATCH path = shortestPath(
            (alice:Person {name: 'Alice'})-[:KNOWS*]-(grace:Person {name: 'Grace'})
        )
        RETURN [node IN nodes(path) | node.name] AS path_names,
               length(path) AS hops
    """)
    for r in result:
        print(f"Shortest path: {' → '.join(r['path_names'])} ({r['hops']} hops)")

driver.close()
```

The structural template in the pattern-matching query — `(a)-[:KNOWS]->(common)<-[:KNOWS]-(b)` — describes a "diamond" shape: two people who share a connection. The database finds all instances of that diamond, regardless of which specific nodes are involved. You described the shape; Neo4j found the data.

---

## Traversal vs Full Scan

One important nuance: not all graph queries are traversals. Some queries ask about the whole graph:

- "How many nodes have label `:Person`?" — this is a scan, not a traversal
- "Find all `:Person` nodes where `city = 'NYC'`" — this is also a scan, filtered by an index on `city`
- "Find all paths between Alice and Grace" — this is a traversal

Scans and indexes in graph databases work similarly to relational databases — a range index on a property lets you find starting nodes quickly. The graph performance advantage only kicks in once you start traversing relationships from those nodes.

---

**← Back: [The Property Graph Model](02-property-graph-model.md)** | **Next: [Graph Algorithms →](04-graph-algorithms-overview.md)** | [Course Home](../README.md)
