# Graphs and Traversal

## The Problem

Some data is fundamentally about **relationships**. A social network is not a list of people — it's a web of connections between people. A computer network is not a list of servers — it's a topology of links. A dependency graph is not a list of packages — it's a lattice of "depends on" edges.

Relational databases model relationships as foreign keys between tables. This works well when relationships are shallow and uniform. When relationships are the *primary thing you're querying* — and especially when you need to follow them to arbitrary depth — the relational model starts fighting against you.

Graphs are the data structure designed for this class of problem.

## The Data Structure

A **graph** is a set of **nodes** (also called vertices) and **edges** (also called relationships or links) connecting them.

```
Nodes:  A, B, C, D
Edges:  A→B, A→C, B→D, C→D

    A
   / \
  B   C
   \ /
    D
```

Every graph has two fundamental properties that drive all design decisions:

| Property | Options | What it means |
|----------|---------|---------------|
| **Direction** | Directed / Undirected | Does the edge A→B imply B→A? |
| **Weight** | Weighted / Unweighted | Does each edge carry a numeric cost? |

In directed graphs, edges have a start and end node. "Alice FOLLOWS Bob" does not mean "Bob FOLLOWS Alice." In undirected graphs, edges are symmetric — if A is connected to B, B is connected to A.

In weighted graphs, edges carry a cost: distance, latency, trust score, transfer amount. Pathfinding algorithms use these weights to find *optimal* paths, not just *any* path.

## Representing Graphs in Memory

Two classical representations, each with different tradeoffs:

### Adjacency Matrix

A 2D array where `matrix[i][j] = 1` if there is an edge from node `i` to node `j`.

```
    A  B  C  D
A [ 0, 1, 1, 0 ]
B [ 0, 0, 0, 1 ]
C [ 0, 0, 0, 1 ]
D [ 0, 0, 0, 0 ]
```

- Edge existence check: O(1) — just look up the cell
- Space: O(V²) — impractical when graphs are large and sparse
- Iteration over neighbors: O(V) — must scan an entire row

### Adjacency List

A map where each node stores a list of its neighbors.

```
A → [B, C]
B → [D]
C → [D]
D → []
```

- Edge existence check: O(degree) — scan the neighbor list
- Space: O(V + E) — proportional to actual edges, not the maximum
- Iteration over neighbors: O(degree) — fast

**Real graph databases use adjacency lists (or equivalent pointer structures) because real graphs are sparse.** A social network with 1 billion users does not have 1 billion² connections — each user has thousands of friends, not billions.

> **Index-free adjacency:** Graph databases take the adjacency list idea further. Each node stores *direct pointers* to its neighbor nodes — not indirect lookups through an index. Following a relationship is a pointer dereference: O(1) per hop, regardless of graph size. This is the key performance advantage over a relational database, which must do an index lookup (O(log n)) at every join.

## Traversal Algorithms

A **traversal** visits all reachable nodes from a starting point. Two canonical strategies:

### Breadth-First Search (BFS)

Explore neighbors at the current depth before going deeper. Uses a queue.

```
Start at A. Visit order: A → B, C → D

Level 0:  A
Level 1:  B, C       (neighbors of A)
Level 2:  D          (neighbors of B and C not yet seen)
```

BFS finds **shortest paths** (by hop count) and is the basis for "degrees of separation" queries. Time complexity: **O(V + E)**.

### Depth-First Search (DFS)

Follow one path as deep as possible before backtracking. Uses a stack (or recursion).

```
Start at A. Visit order: A → B → D → C → (D already visited)
```

DFS is useful for cycle detection, topological sorting, and reachability analysis. Time complexity: **O(V + E)**.

### Path-Finding in Weighted Graphs

When edges have weights, shortest path is not the fewest hops — it's the minimum total weight.

- **Dijkstra's algorithm:** Greedy. Correct for non-negative weights. O((V + E) log V) with a priority queue.
- **Bellman-Ford:** Handles negative weights. O(VE) — slower but more general.
- **A\*:** Dijkstra with a heuristic to guide search toward the goal. Used in routing and navigation.

## Complexity Summary

| Operation | Adjacency Matrix | Adjacency List |
|-----------|-----------------|----------------|
| Add node | O(V²) — resize matrix | O(1) |
| Add edge | O(1) | O(1) |
| Find neighbors | O(V) | O(degree) |
| BFS / DFS traversal | O(V²) | O(V + E) |
| Space | O(V²) | O(V + E) |

For sparse graphs (E << V²) — which describes most real-world graphs — adjacency lists are strictly better.

## When Graphs Are the Right Model

The graph model shines when:

1. **Relationships are the query target** — you need to traverse connections, not just filter attributes
2. **Depth is variable or unbounded** — "find all friends of friends" or "find the shortest path between any two nodes"
3. **Schema is flexible** — different nodes have different properties; relationships change over time
4. **Local neighborhood matters** — fraud rings, recommendations, influence propagation

The graph model struggles when:

1. **You need global aggregations** — "count all nodes with property X" requires scanning the whole graph
2. **Data is naturally tabular** — customer orders, log entries, time-series events
3. **Writes are extremely high-throughput** — graph databases optimize for traversal, not bulk ingestion
4. **You need to distribute across many machines** — graph partitioning is fundamentally hard (see [Graph Partitioning](../03-scaling/04-graph-partitioning.md))

## Where This Shows Up

| Technology | How it uses graphs |
|------------|-------------------|
| **Neo4j** | Native graph database; property graph model; index-free adjacency |
| **Amazon Neptune** | Managed graph DB; supports both property graphs and RDF |
| **NetworkX (Python)** | In-memory graph analysis; BFS/DFS/Dijkstra built-in |
| **Apache Spark GraphX** | Distributed graph computation on large datasets |
| **Relational DBs** | Can represent graphs with adjacency tables; recursive CTEs for traversal; O(log n) per hop |
