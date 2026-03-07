---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Graph Algorithms Overview

```{note}
This lesson requires the Neo4j lab. Run `make lab-neo4j` before starting.
```

Graph databases do not just answer "who is connected to whom?" They enable a whole category of analytical questions that are impossible or impractical in relational or key-value stores: "who is the most influential node?", "which groups cluster together?", "what is the fastest route?" These questions are answered by **graph algorithms**.

This lesson surveys the major categories of graph algorithms, explains the problems they solve, and demonstrates each class with a hands-on example.

> **Core Concept:** See [Graphs and Traversal](../../core-concepts/02-data-structures/05-graphs-and-traversal.md) for BFS, DFS, and Dijkstra — the building blocks that graph algorithms are composed from.

---

## Three Categories of Graph Algorithms

### 1. Centrality Algorithms — Who Matters Most?

Centrality algorithms measure the importance or influence of a node within the graph. "Importance" can mean different things depending on the variant:

**Degree centrality** — how many direct connections does a node have? The most connected person in a social network. Simple but often misleading — having many connections doesn't mean you're influential.

**PageRank** — Google's original algorithm. A node is important if it is pointed to by other important nodes. Influence flows through the graph: being connected to influential nodes makes you more influential. Used in: ranking web pages, identifying key opinion leaders, fraud detection (accounts that many flagged accounts point to).

**Betweenness centrality** — how often does a node appear on the shortest path between two other nodes? A node with high betweenness is a "bridge" — remove it and many connections break. Used in: network resilience analysis, identifying chokepoints in supply chains.

**Closeness centrality** — how quickly can a node reach all other nodes? Used in: logistics (where to put a distribution center), influence propagation.

### 2. Community Detection — What Groups Exist?

Community detection algorithms partition the graph into clusters of nodes that are more densely connected to each other than to the rest of the graph. The goal is not to find a predetermined structure — it's to discover emergent groupings in the data.

**Louvain algorithm** — hierarchically optimizes a metric called modularity (the difference between actual edge density within a community and the expected density in a random graph). Fast, scalable, widely used.

**Label propagation** — each node starts with a unique label. In each iteration, each node adopts the most common label among its neighbors. The process converges when labels stabilize. Very fast, non-deterministic.

**Weakly/strongly connected components** — find all groups of nodes that can reach each other. A weakly connected component ignores edge direction; strongly connected requires paths in both directions. Used in: fraud ring detection (identifying isolated clusters of suspicious accounts).

### 3. Pathfinding Algorithms — What Is the Best Route?

**Shortest path (Dijkstra)** — minimum hops or minimum weight between two nodes. Already covered in the traversal lesson.

**All-pairs shortest path** — compute shortest paths between every pair of nodes. Expensive (O(V × (V + E) log V)) but enables network-wide analysis.

**Minimum spanning tree** — find the subset of edges that keeps all nodes connected with minimum total weight. Used in: network design (lay cable with minimum cost), clustering.

---

## Hands-On: Computing Centrality and Finding Communities

The following examples compute centrality scores and detect communities using standard Cypher queries. In production, Neo4j's [Graph Data Science (GDS)](https://neo4j.com/docs/graph-data-science/) library provides highly optimized, parallel implementations of all these algorithms — but the logic demonstrated here is equivalent.

```{code-cell} python
from neo4j import GraphDatabase
from collections import defaultdict

driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))

with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")

    session.run("""
        CREATE (a:Account {id: 'A1', name: 'Alice'})
        CREATE (b:Account {id: 'A2', name: 'Bob'})
        CREATE (c:Account {id: 'A3', name: 'Carol'})
        CREATE (d:Account {id: 'A4', name: 'Dave'})
        CREATE (e:Account {id: 'A5', name: 'Eve'})
        CREATE (f:Account {id: 'A6', name: 'Frank'})
        CREATE (g:Account {id: 'A7', name: 'Grace'})

        CREATE (a)-[:TRANSFER]->(b)
        CREATE (a)-[:TRANSFER]->(c)
        CREATE (b)-[:TRANSFER]->(d)
        CREATE (c)-[:TRANSFER]->(d)
        CREATE (d)-[:TRANSFER]->(e)
        CREATE (d)-[:TRANSFER]->(f)
        CREATE (e)-[:TRANSFER]->(g)
        CREATE (f)-[:TRANSFER]->(g)
        CREATE (b)-[:TRANSFER]->(c)
    """)

print("Transaction graph created (financial network with 7 accounts)")
```

```{code-cell} python
# Degree centrality: how many connections does each node have (in + out)?
with driver.session() as session:
    result = session.run("""
        MATCH (a:Account)
        OPTIONAL MATCH (a)-[out:TRANSFER]->()
        OPTIONAL MATCH ()-[in:TRANSFER]->(a)
        RETURN a.name AS name, 
               count(DISTINCT out) AS outgoing, 
               count(DISTINCT in)  AS incoming,
               count(DISTINCT out) + count(DISTINCT in) AS total_degree
        ORDER BY total_degree DESC
    """)
    print("Degree centrality (transfer graph):")
    print(f"  {'Name':<8} {'Out':>5} {'In':>5} {'Total':>7}")
    print(f"  {'-'*8} {'-'*5} {'-'*5} {'-'*7}")
    for r in result:
        print(f"  {r['name']:<8} {r['outgoing']:>5} {r['incoming']:>5} {r['total_degree']:>7}")
```

```{code-cell} python
# PageRank approximation: 10 iterations of the PageRank recurrence
# In production, use GDS: CALL gds.pageRank.stream('myGraph')
with driver.session() as session:
    session.run("""
        MATCH (a:Account)
        SET a.pagerank = 1.0 / 7.0
    """)

    for _ in range(10):
        session.run("""
            MATCH (a:Account)
            WITH a, 
                 [(src)-[:TRANSFER]->(a) | src] AS sources
            WITH a, sources,
                 reduce(total = 0.0, src IN sources |
                     total + src.pagerank / size([(src)-[:TRANSFER]->() | 1])
                 ) AS incoming_rank
            SET a.pagerank = 0.15 / 7.0 + 0.85 * incoming_rank
        """)

    result = session.run("""
        MATCH (a:Account)
        RETURN a.name AS name, round(a.pagerank * 100, 2) AS score
        ORDER BY score DESC
    """)
    print("\nPageRank scores (higher = more influential in the transfer network):")
    for r in result:
        print(f"  {r['name']}: {r['score']}")
```

```{code-cell} python
# Weakly connected components (reachability regardless of direction)
# Find isolated clusters — in fraud detection, isolated clusters of suspicious accounts
with driver.session() as session:
    result = session.run("""
        MATCH (a:Account)
        WITH collect(a) AS nodes
        UNWIND nodes AS node
        MATCH (node)-[:TRANSFER*0..]-(connected)
        WITH node, collect(DISTINCT connected.name) AS component
        RETURN node.name AS account, size(component) AS component_size,
               component AS members
        ORDER BY component_size DESC, account
    """)
    print("\nConnected components (accounts reachable from each node):")
    seen = set()
    for r in result:
        key = tuple(sorted(r['members']))
        if key not in seen:
            seen.add(key)
            print(f"  Component of size {r['component_size']}: {sorted(r['members'])}")

driver.close()
```

---

## When to Use Graph Algorithms

Graph algorithms are not "nice to have" analytical features — for certain problems, they are the only practical approach:

| Problem | Algorithm | Why graph? |
|---------|-----------|-----------|
| Fraud ring detection | Connected components, PageRank | Reveals hidden account clusters invisible in flat data |
| Recommendation ("you may also like") | Similarity via shared neighbors | Collaborative filtering is a graph problem at scale |
| Critical infrastructure | Betweenness centrality | Finds single points of failure in networks |
| Route optimization | Dijkstra, A* | Minimum-cost path in a weighted graph |
| Community discovery | Louvain, Label propagation | No predefined groups — emergence from structure |
| Permission auditing | Reachability, path enumeration | Find all privilege-escalation paths |

In production Neo4j deployments, these algorithms run via the **Graph Data Science library**, which projects the graph into an optimized in-memory format for batch computation. The Cypher examples above illustrate the logic — GDS is the production-grade tool.

---

**← Back: [Traversal and Pattern Matching](03-traversal-and-pattern-matching.md)** | **Next: [Real-World Use Cases →](05-real-world-use-cases.md)** | [Course Home](../README.md)
