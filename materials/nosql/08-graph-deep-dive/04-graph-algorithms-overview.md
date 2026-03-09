---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Graph Algorithms Overview

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

driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))

with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")

    # Legitimate cluster: normal retail customers transacting with each other
    session.run("""
        CREATE (l1:Account {id: 'L1', name: 'Lena',   type: 'retail',    risk_score: 1, country: 'IL'})
        CREATE (l2:Account {id: 'L2', name: 'Lior',   type: 'retail',    risk_score: 2, country: 'IL'})
        CREATE (l3:Account {id: 'L3', name: 'Liat',   type: 'retail',    risk_score: 1, country: 'IL'})
        CREATE (l4:Account {id: 'L4', name: 'Liron',  type: 'retail',    risk_score: 2, country: 'IL'})
        CREATE (l5:Account {id: 'L5', name: 'Lavi',   type: 'retail',    risk_score: 3, country: 'IL'})

        // Mule accounts: appear legitimate, bridge the clean cluster to the collector
        CREATE (m1:Account {id: 'M1', name: 'Moran',  type: 'retail',    risk_score: 6, country: 'IL'})
        CREATE (m2:Account {id: 'M2', name: 'Fares',  type: 'business',  risk_score: 7, country: 'CY'})
        CREATE (m3:Account {id: 'M3', name: 'Moshe',  type: 'business',  risk_score: 8, country: 'CY'})

        // Fraud ring A: three accounts cycling money between themselves, each also draining to collector
        CREATE (f1:Account {id: 'F1', name: 'Fadi',   type: 'business',  risk_score: 9, country: 'CY'})
        CREATE (f2:Account {id: 'F2', name: 'Farid',  type: 'business',  risk_score: 9, country: 'AE'})
        CREATE (f3:Account {id: 'F3', name: 'Farida', type: 'business',  risk_score: 8, country: 'AE'})

        // Collector: single account that aggregates funds from both the mule chain and the fraud ring
        CREATE (c1:Account {id: 'C1', name: 'Cash-Out', type: 'offshore', risk_score: 10, country: 'SC'})

        // Dormant ring B: completely isolated chain — no connection to any other cluster
        CREATE (d1:Account {id: 'D1', name: 'Dana',   type: 'retail',    risk_score: 8, country: 'IL'})
        CREATE (d2:Account {id: 'D2', name: 'Dov',    type: 'retail',    risk_score: 8, country: 'IL'})
        CREATE (d3:Account {id: 'D3', name: 'Dikla',  type: 'business',  risk_score: 9, country: 'CY'})
    """)

    # Legitimate cluster transfers (normal, small amounts)
    session.run("""
        MATCH (l1:Account {id:'L1'}), (l2:Account {id:'L2'}),
              (l3:Account {id:'L3'}), (l4:Account {id:'L4'}), (l5:Account {id:'L5'})
        CREATE (l1)-[:TRANSFER {amount: 200,  days_ago: 45}]->(l2)
        CREATE (l1)-[:TRANSFER {amount: 150,  days_ago: 30}]->(l3)
        CREATE (l2)-[:TRANSFER {amount: 300,  days_ago: 20}]->(l3)
        CREATE (l3)-[:TRANSFER {amount: 250,  days_ago: 15}]->(l4)
        CREATE (l4)-[:TRANSFER {amount: 180,  days_ago: 10}]->(l5)
        CREATE (l2)-[:TRANSFER {amount: 400,  days_ago:  5}]->(l5)
    """)

    # Mule chain: funds leave the legitimate cluster and pass through two mule accounts
    session.run("""
        MATCH (l5:Account {id:'L5'}), (m1:Account {id:'M1'}),
              (m2:Account {id:'M2'}), (m3:Account {id:'M3'}), (c1:Account {id:'C1'})
        CREATE (l5)-[:TRANSFER {amount: 9800, days_ago: 8}]->(m1)
        CREATE (m1)-[:TRANSFER {amount: 9500, days_ago: 7}]->(m2)
        CREATE (m2)-[:TRANSFER {amount: 9200, days_ago: 6}]->(m3)
        CREATE (m3)-[:TRANSFER {amount: 8900, days_ago: 5}]->(c1)
    """)

    # Fraud ring A: internal cycle (F1→F2→F3→F1) plus each member drains directly to collector
    # Each node has exactly 2 outgoing edges: one ring hop, one to Cash-Out
    session.run("""
        MATCH (f1:Account {id:'F1'}), (f2:Account {id:'F2'}),
              (f3:Account {id:'F3'}), (c1:Account {id:'C1'})
        CREATE (f1)-[:TRANSFER {amount: 50000, days_ago: 14}]->(f2)
        CREATE (f2)-[:TRANSFER {amount: 48000, days_ago: 13}]->(f3)
        CREATE (f3)-[:TRANSFER {amount: 46000, days_ago: 12}]->(f1)
        CREATE (f1)-[:TRANSFER {amount: 15000, days_ago:  4}]->(c1)
        CREATE (f2)-[:TRANSFER {amount: 12000, days_ago:  3}]->(c1)
        CREATE (f3)-[:TRANSFER {amount: 10000, days_ago:  2}]->(c1)
    """)

    # Dormant ring B: isolated chain — no edge to any other cluster
    session.run("""
        MATCH (d1:Account {id:'D1'}), (d2:Account {id:'D2'}), (d3:Account {id:'D3'})
        CREATE (d1)-[:TRANSFER {amount: 5000, days_ago: 90}]->(d2)
        CREATE (d2)-[:TRANSFER {amount: 4800, days_ago: 89}]->(d3)
    """)

print("Fraud network created:")
print("  Cluster 1 (main): L1–L5 (legitimate) → M1/M2/M3 (mule chain) → C1 (collector)")
print("                    F1/F2/F3 (fraud ring, internal cycle) → C1 (collector)")
print("  Cluster 2 (dormant): D1–D3 (isolated suspicious chain, no connection to cluster 1)")
print("  Total: 14 accounts, 19 transfers")
```

```{code-cell} python
# Degree centrality: how many connections does each node have (in + out)?
# In a fraud network, high in-degree on a single account signals a collector.
with driver.session() as session:
    result = session.run("""
        MATCH (a:Account)
        OPTIONAL MATCH (a)-[out:TRANSFER]->()
        OPTIONAL MATCH ()-[in:TRANSFER]->(a)
        RETURN a.name AS name,
               a.type AS type,
               a.country AS country,
               count(DISTINCT out) AS outgoing,
               count(DISTINCT in)  AS incoming,
               count(DISTINCT out) + count(DISTINCT in) AS total_degree
        ORDER BY total_degree DESC
    """)
    print("Degree centrality — who has the most transfer connections?\n")
    print(f"  {'Name':<10} {'Type':<10} {'Country':<8} {'Out':>5} {'In':>5} {'Total':>7}")
    print(f"  {'-'*10} {'-'*10} {'-'*8} {'-'*5} {'-'*5} {'-'*7}")
    for r in result:
        flag = " ← collector!" if r['incoming'] >= 3 else ""
        print(f"  {r['name']:<10} {r['type']:<10} {r['country']:<8} {r['outgoing']:>5} {r['incoming']:>5} {r['total_degree']:>7}{flag}")
    print("\nObservation: Cash-Out has the highest in-degree — multiple ring members funneling to one account.")
```

```{code-cell} python
# PageRank approximation: 10 iterations of the PageRank recurrence.
# Key dynamics:
#   - The fraud ring cycle (F1→F2→F3→F1) keeps rank circulating, making all three members equal
#   - Each ring member also points to Cash-Out, so Cash-Out receives rank from three already-inflated sources
#   - The mule chain (Lavi→Moran→Fares→Moshe→Cash-Out) acts as a pipeline, progressively concentrating rank
# In production, use GDS: CALL gds.pageRank.stream('myGraph')
node_count = 14

with driver.session() as session:
    session.run(f"""
        MATCH (a:Account)
        SET a.pagerank = 1.0 / {node_count}
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
            SET a.pagerank = 0.15 / 14.0 + 0.85 * incoming_rank
        """)

    result = session.run("""
        MATCH (a:Account)
        RETURN a.name AS name, a.type AS type, round(a.pagerank * 100, 2) AS score
        ORDER BY score DESC
    """)
    print("PageRank scores — higher means more 'influential' in the transfer network:\n")
    for r in result:
        bar = "█" * int(r['score'] * 2)
        print(f"  {r['name']:<10} ({r['type']:<9})  {r['score']:>5.2f}  {bar}")
    print()
    print("Observation: Cash-Out scores highest — it absorbs rank from both the mule pipeline and the fraud ring.")
    print("Fadi/Farid/Farida score equally: the internal cycle redistributes rank symmetrically among them.")
    print("Dana/Dov/Dikla score near baseline — isolated, receiving no rank from outside their component.")
```

```{code-cell} python
# Weakly connected components (reachability regardless of direction).
# A cluster of accounts with no connection to the rest of the graph is a red flag:
# it suggests a self-contained operation deliberately kept isolated from known activity.
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
    print("Weakly connected components — which accounts can reach each other?\n")
    seen = set()
    for r in result:
        key = tuple(sorted(r['members']))
        if key not in seen:
            seen.add(key)
            label = ""
            if r['component_size'] <= 4:
                label = "  ← ISOLATED RING — no connection to main network"
            print(f"  Component ({r['component_size']} accounts): {sorted(r['members'])}{label}")

    print()
    print("Observation: Dana/Dov/Dikla form a fully isolated cluster.")
    print("They transfer only among themselves — a dormant fraud ring with no visible link to the main network.")
    print("In a flat database, these accounts look normal. The graph reveals the hidden structure.")

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
