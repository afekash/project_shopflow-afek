# Graph Databases

## What Is a Graph Database?

A graph database stores data as a network of **nodes** (entities) and **edges** (relationships). Both nodes and edges can have **properties** (key-value attributes).

```
           [Person]                [Person]
         name: "Alice"           name: "Bob"
         age: 32                 age: 28
              │                       │
              │  FRIENDS_WITH         │
              └───────────────────────┘
                    since: 2019
              │
              │  WORKS_AT
              ▼
           [Company]
         name: "Acme Corp"
         industry: "SaaS"
              │
              │  LOCATED_IN
              ▼
           [City]
         name: "Tel Aviv"
```

This is not a data modeling convenience -- it reflects a fundamentally different way of thinking about data. In graph databases, **relationships are first-class citizens** stored as explicit connections, not derived at query time through joins.

## Where Relational Databases Struggle with Graphs

Consider a social network: find all users within 3 degrees of separation from Alice.

**In SQL (relational):**
```sql
-- Friends of Alice (degree 1)
SELECT f1.user_id
FROM friendships f1
WHERE f1.user1_id = 'alice'

UNION

-- Friends of friends (degree 2) - recursive CTE
WITH RECURSIVE friends_of_friends AS (
    SELECT user1_id, user2_id, 1 as depth FROM friendships WHERE user1_id = 'alice'
    UNION ALL
    SELECT f.user1_id, f.user2_id, fof.depth + 1
    FROM friendships f
    JOIN friends_of_friends fof ON f.user1_id = fof.user2_id
    WHERE fof.depth < 3
)
SELECT DISTINCT user2_id FROM friends_of_friends;
```

This requires a recursive CTE -- a complex query that the database optimizes poorly at scale. With 1 million users and 50 million friendship records, this query can take minutes.

**In Neo4j (Cypher):**
```cypher
MATCH (alice:Person {name: "Alice"})-[:FRIENDS_WITH*1..3]-(friend:Person)
RETURN DISTINCT friend.name
```

One line. And it runs in milliseconds regardless of total dataset size because of how graph databases store connections.

## How Graph Databases Work Internally: Index-Free Adjacency

This is the key architectural innovation.

In a relational database, a JOIN works by:
1. Taking a value (foreign key)
2. Looking it up in an index
3. Finding matching rows

This is O(log n) per hop, where n is the table size. Three hops = O(log³ n) operations. At scale with billions of rows, this degrades significantly.

A graph database stores each node with **direct physical pointers to its neighboring nodes**. Following a relationship means following a pointer in memory -- O(1) per hop regardless of the total number of nodes in the graph.

```
Relational (JOIN):
  Alice → look up "alice" in friendships index → scan matching rows → look up each friend ID in users index
  Each hop: O(log n) index lookup

Graph (index-free adjacency):
  Alice node → pointer → Bob node → pointer → Carol node → ...
  Each hop: O(1) pointer follow
```

This is why graph traversals stay fast even as the graph grows to billions of nodes -- the traversal cost depends on the local neighborhood size, not the total graph size.

## The Property Graph Model

The most widely-used graph model (used by Neo4j, Amazon Neptune with Gremlin) is the **property graph**:

- **Nodes**: Entities with labels (type) and properties (attributes)
  ```
  (:Person {name: "Alice", age: 32, email: "alice@example.com"})
  (:Company {name: "Acme Corp", founded: 2015})
  ```

- **Edges**: Directed, typed relationships with properties
  ```
  [:WORKS_AT {since: "2022-03-01", role: "Senior Engineer"}]
  [:FRIENDS_WITH {since: "2019-07-15", strength: 0.87}]
  ```

- **Labels**: Multiple labels per node (like tags)
  ```
  (:Person:Employee:VIPCustomer {name: "Alice"})
  ```

## Cypher Query Language

Neo4j uses **Cypher**, a declarative pattern-matching language. Patterns in Cypher visually resemble the graph structure they describe.

```
ASCII art in Cypher:
(node)-[:RELATIONSHIP]->(otherNode)
```

### Basic Patterns

```cypher
-- Find Alice
MATCH (p:Person {name: "Alice"})
RETURN p

-- Find everyone Alice works with
MATCH (alice:Person {name: "Alice"})-[:WORKS_AT]->(company:Company)<-[:WORKS_AT]-(colleague:Person)
RETURN colleague.name, company.name

-- Find mutual friends of Alice and Bob
MATCH (alice:Person {name: "Alice"})-[:FRIENDS_WITH]-(mutual)-[:FRIENDS_WITH]-(bob:Person {name: "Bob"})
RETURN mutual.name

-- Shortest path between Alice and Carol
MATCH path = shortestPath(
    (alice:Person {name: "Alice"})-[:FRIENDS_WITH*]-(carol:Person {name: "Carol"})
)
RETURN length(path), [n IN nodes(path) | n.name]

-- Find influencers: people with most connections in tech companies
MATCH (p:Person)-[:WORKS_AT]->(:Company {industry: "Tech"}),
      (p)-[:FRIENDS_WITH]-(friend)
RETURN p.name, count(friend) AS connections
ORDER BY connections DESC
LIMIT 10
```

### Writing Data

```cypher
-- Create nodes and relationship
CREATE (alice:Person {name: "Alice", age: 32})
CREATE (acme:Company {name: "Acme Corp"})
CREATE (alice)-[:WORKS_AT {role: "Engineer", since: "2022-01-01"}]->(acme)

-- Merge (create if not exists)
MERGE (p:Person {email: "alice@example.com"})
ON CREATE SET p.name = "Alice", p.created_at = datetime()
ON MATCH SET p.last_seen = datetime()
```

## Scaling Graph Databases

Graph databases are the hardest category to scale horizontally. The reason is fundamental: **graph partitioning is an NP-hard problem**.

When you cut a graph across machine boundaries, some relationships will cross the partition boundary. A traversal that follows such a relationship must make a network call to another machine. In practice, many real-world graph traversals (social network queries, fraud detection paths) are "small world" -- they follow densely connected clusters where many nodes have relationships to many others. Cutting these clusters apart destroys the performance advantage.

**Common approaches:**

- **Vertical scaling**: Most Neo4j deployments scale up (more RAM) rather than out. Neo4j is designed to hold the entire working set in memory.
- **Causal clustering (Neo4j Enterprise)**: Multiple read replicas with a single primary for writes. Good for read-heavy workloads.
- **Domain partitioning**: Manually shard by subgraph (e.g., European users on one cluster, American users on another) where cross-shard traversals are rare.

This is a genuine limitation. If you need graph traversals at massive scale (billions of nodes, trillion edges), graph databases become harder to operate. Companies like Facebook and LinkedIn built custom distributed graph systems for this reason.

## Strengths

**Relationship-heavy queries are natural and fast**
Multi-hop traversals that would require recursive CTEs in SQL are a single pattern match in Cypher.

**Intuitive data modeling**
The data model matches how humans think about connected data. No need to translate mental models into tables and foreign keys.

**Flexible schema**
Nodes and relationships can have varying properties without migrations.

**Pattern matching**
Find complex structural patterns in data (fraud rings, supply chain cycles) efficiently.

## Weaknesses

**Hard to scale horizontally**
Graph partitioning degrades traversal performance. Most graph databases scale vertically.

**Not great for aggregations**
Aggregating across millions of nodes (like SUM of all salaries) is not what graph databases are optimized for.

**Smaller ecosystem**
Fewer tools, cloud services, and engineers familiar with graph databases compared to MongoDB or Cassandra.

**Write performance**
Updating many relationships at once can be slow due to the need to maintain adjacency pointers.

## Main Players

| Database | Notable For |
|----------|------------|
| **Neo4j** | Most mature, Cypher language, rich tooling |
| **Amazon Neptune** | Managed, supports both Gremlin and SPARQL |
| **ArangoDB** | Multi-model (graph + document + key-value) |
| **TigerGraph** | Distributed graph at enterprise scale |
| **Memgraph** | In-memory, Cypher-compatible, real-time analytics |

## Primary Use Cases

**Social Networks**
Friends-of-friends, mutual connections, content recommendation based on social graph.

**Fraud Detection**
Identify fraud rings: accounts that share the same phone, address, or device, connected through transaction patterns. A ring that looks innocent in isolation becomes obvious as a graph pattern.

```cypher
-- Find accounts sharing the same phone number, with transactions between them
MATCH (a:Account)-[:HAS_PHONE]->(p:Phone)<-[:HAS_PHONE]-(b:Account),
      (a)-[:TRANSFERRED_TO]->(b)
WHERE a <> b
RETURN a.account_id, b.account_id, p.number
```

**Recommendation Engines**
"People who bought X also bought Y" -- collaborative filtering as graph traversal.

**Knowledge Graphs**
Google's Knowledge Graph, Wikipedia's Wikidata -- entities and their semantic relationships.

**Network and IT Operations**
Map physical network topology, find impact of a device failure, trace packet routes.

**Supply Chain and Logistics**
Model supplier relationships, dependency graphs, route optimization.

## Relational vs Graph: The Friends-of-Friends Benchmark

To illustrate performance differences, consider finding friends-of-friends (depth 2) in a social network with 1 million users and 50 million friendships:

| Depth | Relational (PostgreSQL) | Graph (Neo4j) |
|-------|------------------------|---------------|
| 2 hops | ~2 seconds | <10ms |
| 3 hops | Minutes | <100ms |
| 4 hops | Hours / timeout | <1 second |

The relational database performance degrades exponentially with depth. The graph database performance depends on the local neighborhood size, which stays roughly constant.

## Summary

| Aspect | Graph Database |
|--------|---------------|
| Data model | Nodes, edges, properties |
| Schema | Flexible, schema-on-write optional |
| Scaling | Primarily vertical (horizontal is hard) |
| Consistency | Strong (Neo4j default) |
| Traversal performance | O(1) per hop (index-free adjacency) |
| Best for | Social graphs, fraud detection, recommendations, knowledge graphs |
| Avoid when | Aggregations, large-scale horizontal scaling, tabular data |

---

**Next:** [Choosing the Right Database →](05-choosing-the-right-database.md)

---

[← Back: Column-Family Stores](03-column-family-stores.md) | [Course Home](../README.md)
