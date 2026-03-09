---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Traversal and Pattern Matching

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

### Cell 1 — Setup: microservices dependency graph

Three independent applications — checkout, analytics, notifications — each with their own
services and infra. A shared `auth-service` and `users-db` sit at the centre and are depended
on by all three. Every dependency edge carries a `criticality` property (`'critical'` or
`'optional'`) so we can later ask not just *what* breaks, but *how badly*.

```{code-cell} python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))

with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")

    session.run("""
        // ── Shared infrastructure ──────────────────────────────────────────
        CREATE (auth:Service  {name: 'auth-service',   app: 'shared'})
        CREATE (usersdb:Database {name: 'users-db',    app: 'shared'})
        CREATE (cache:Cache   {name: 'session-cache',  app: 'shared'})

        // ── Checkout app ────────────────────────────────────────────────────
        CREATE (co_gw:Service  {name: 'checkout-gateway',  app: 'checkout'})
        CREATE (co_svc:Service {name: 'checkout-service',  app: 'checkout'})
        CREATE (co_pay:Service {name: 'payment-service',   app: 'checkout'})
        CREATE (co_db:Database {name: 'orders-db',         app: 'checkout'})
        CREATE (co_q:Queue     {name: 'payment-queue',     app: 'checkout'})

        // ── Analytics app ───────────────────────────────────────────────────
        CREATE (an_gw:Service  {name: 'analytics-gateway', app: 'analytics'})
        CREATE (an_svc:Service {name: 'analytics-service', app: 'analytics'})
        CREATE (an_db:Database {name: 'events-db',         app: 'analytics'})
        CREATE (an_q:Queue     {name: 'events-queue',      app: 'analytics'})

        // ── Notifications app ───────────────────────────────────────────────
        CREATE (no_gw:Service  {name: 'notify-gateway',    app: 'notifications'})
        CREATE (no_svc:Service {name: 'notify-service',    app: 'notifications'})
        CREATE (no_db:Database {name: 'templates-db',      app: 'notifications'})

        // ── Checkout dependency edges ───────────────────────────────────────
        CREATE (co_gw)-[:CALLS        {criticality: 'critical'}]->(auth)
        CREATE (co_gw)-[:CALLS        {criticality: 'critical'}]->(co_svc)
        CREATE (co_svc)-[:CALLS       {criticality: 'critical'}]->(co_pay)
        CREATE (co_svc)-[:READS_FROM  {criticality: 'critical'}]->(co_db)
        CREATE (co_pay)-[:PUBLISHES_TO {criticality: 'critical'}]->(co_q)
        CREATE (auth)-[:READS_FROM    {criticality: 'critical'}]->(usersdb)
        CREATE (auth)-[:READS_FROM    {criticality: 'optional'}]->(cache)

        // ── Analytics dependency edges ──────────────────────────────────────
        CREATE (an_gw)-[:CALLS        {criticality: 'critical'}]->(auth)
        CREATE (an_gw)-[:CALLS        {criticality: 'critical'}]->(an_svc)
        CREATE (an_svc)-[:READS_FROM  {criticality: 'critical'}]->(an_db)
        CREATE (an_svc)-[:READS_FROM  {criticality: 'optional'}]->(usersdb)
        CREATE (an_svc)-[:PUBLISHES_TO {criticality: 'optional'}]->(an_q)

        // ── Notifications dependency edges ──────────────────────────────────
        CREATE (no_gw)-[:CALLS        {criticality: 'critical'}]->(auth)
        CREATE (no_gw)-[:CALLS        {criticality: 'critical'}]->(no_svc)
        CREATE (no_svc)-[:READS_FROM  {criticality: 'critical'}]->(no_db)
        CREATE (no_svc)-[:READS_FROM  {criticality: 'optional'}]->(usersdb)
    """)

print("Platform dependency graph created")
print("  Apps:      checkout, analytics, notifications")
print("  Shared:    auth-service, users-db, session-cache")
print("  Edge prop: criticality = 'critical' | 'optional'")
```

### Cell 2 — Traversal parameters: direction, type filter, depth

```{code-cell} python
with driver.session() as session:
    # Direction: outgoing CALLS from checkout-gateway
    r = session.run("""
        MATCH (gw:Service {name: 'checkout-gateway'})-[:CALLS]->(dep)
        RETURN dep.name AS name
    """).values()
    print("Direction — outgoing CALLS from checkout-gateway:")
    for row in r:
        print(f"  → {row[0]}")

    # Direction: incoming CALLS (what calls checkout-gateway?)
    r = session.run("""
        MATCH (gw:Service {name: 'checkout-gateway'})<-[:CALLS]-(caller)
        RETURN caller.name AS name
    """).values()
    callers = [row[0] for row in r]
    print("\nDirection — incoming CALLS to checkout-gateway:")
    print(f"  {callers if callers else '(none — it is the entry point)'}")

    # Type filter: any single-hop relationship (CALLS, READS_FROM, PUBLISHES_TO)
    r = session.run("""
        MATCH (gw:Service {name: 'checkout-gateway'})-[rel]->(dep)
        RETURN type(rel) AS rel_type, rel.criticality AS crit, dep.name AS name
    """).values()
    print("\nType filter — any outgoing relationship from checkout-gateway:")
    for row in r:
        print(f"  -[{row[0]} criticality={row[1]}]→ {row[2]}")

    # Depth: exactly 1 hop vs up to 3 hops via CALLS
    r1 = session.run("""
        MATCH (gw:Service {name: 'checkout-gateway'})-[:CALLS*1]->(dep)
        RETURN DISTINCT dep.name AS name
    """).values()
    r3 = session.run("""
        MATCH (gw:Service {name: 'checkout-gateway'})-[:CALLS*1..3]->(dep)
        RETURN DISTINCT dep.name AS name
    """).values()
    print("\nDepth — CALLS*1  (direct only):", [r[0] for r in r1])
    print("Depth — CALLS*1..3 (up to 3 hops):", [r[0] for r in r3])
```

### Cell 3 — Structural pattern matching

```{code-cell} python
with driver.session() as session:
    # Blast-radius pattern: for every node in the graph, find all gateway services
    # that can reach it through at least one critical-only path (2+ hops).
    # Rank each dependency by how many distinct apps would go down if it failed.
    #
    # Shape: (gateway:Service)-[:CALLS|READS_FROM|PUBLISHES_TO {criticality:'critical'}*2..]->
    #        (dep)
    #
    # No starting node is named — the query finds ALL instances of this shape.
    result = session.run("""
        MATCH path = (gw:Service)-[rels:CALLS|READS_FROM|PUBLISHES_TO*2..]->(dep)
        WHERE gw.name ENDS WITH '-gateway'
          AND all(r IN rels WHERE r.criticality = 'critical')
        WITH dep,
             collect(DISTINCT gw.name)  AS dependent_gateways,
             collect(DISTINCT gw.app)   AS affected_apps
        WHERE size(affected_apps) >= 1
        RETURN dep.name                   AS dependency,
               labels(dep)[0]            AS kind,
               size(affected_apps)       AS apps_at_risk,
               affected_apps             AS apps,
               dependent_gateways        AS via_gateways
        ORDER BY apps_at_risk DESC, dependency
    """)

    print("Blast-radius — dependencies reachable via all-critical paths from 2+ hops away")
    print("Ranked by number of apps that would be affected if the dependency went down:\n")
    print(f"  {'Dependency':<22} {'Kind':<10} {'Apps at risk':>12}   Apps")
    print(f"  {'-'*22} {'-'*10} {'-'*12}   {'-'*40}")
    for r in result:
        print(f"  {r['dependency']:<22} {r['kind']:<10} {r['apps_at_risk']:>12}   {sorted(r['apps'])}")
        print(f"  {'':22} {'':10} {'':12}   via: {sorted(r['via_gateways'])}")
```

```{code-cell} python
with driver.session() as session:
    # Diamond pattern: which pairs of apps share a downstream dependency
    # through a critical path? These pairs are operationally coupled —
    # a failure propagates across the app boundary.
    result = session.run("""
        MATCH (a:Service)-[ra:CALLS|READS_FROM*1..3]->(shared)<-[rb:CALLS|READS_FROM*1..3]-(b:Service)
        WHERE a.app < b.app
          AND a.app <> 'shared' AND b.app <> 'shared'
          AND all(r IN ra WHERE r.criticality = 'critical')
          AND all(r IN rb WHERE r.criticality = 'critical')
        RETURN DISTINCT a.app AS app_a, b.app AS app_b,
               shared.name AS shared_dep, labels(shared)[0] AS dep_type
        ORDER BY app_a, app_b
    """)
    print("Diamond pattern — app pairs sharing a critical downstream dependency:")
    print("  (shape: (AppA)-[critical*]->(shared)<-[critical*]-(AppB))\n")
    for r in result:
        print(f"  {r['app_a']} ↔ {r['app_b']}  —  shared critical dep: {r['shared_dep']} ({r['dep_type']})")
```

### Cell 4 — Traversal vs scan

```{code-cell} python
with driver.session() as session:
    # SCAN: filter nodes by a property — never follows a relationship.
    # Neo4j resolves this with a label+property index on Service.app.
    result = session.run("""
        MATCH (s:Service)
        WHERE s.app = 'shared'
        RETURN s.name AS name
    """)
    shared = [r['name'] for r in result]
    print("Scan — all shared Services (label+property index lookup, no traversal):")
    print(f"  {shared}")
    print("  Performance: O(matches) — proportional to result size, not graph size\n")

    # TRAVERSAL: walk critical relationships pointer-by-pointer from a gateway.
    # The graph performance advantage kicks in here — each hop is O(1).
    result = session.run("""
        MATCH (gw:Service {name: 'checkout-gateway'})-[r:CALLS|READS_FROM|PUBLISHES_TO*1..4]->(dep)
        WHERE all(rel IN r WHERE rel.criticality = 'critical')
        RETURN DISTINCT dep.name AS name, labels(dep)[0] AS kind
        ORDER BY kind, name
    """)
    print("Traversal — everything reachable from checkout-gateway via critical edges (pointer walk):")
    for r in result:
        print(f"  {r['name']} ({r['kind']})")
    print("  Performance: O(reachable nodes × degree) — independent of total graph size")

driver.close()
```

The four cells above each isolate one concept. Cell 2 changes exactly one traversal parameter at a time so the effect is visible in the output. Cell 3 never names a starting node — it describes a shape and Neo4j finds every subgraph that matches it; the `criticality` property on edges means the result tells you not just what is connected but how dangerously. Cell 4 makes the scan/traversal boundary explicit: the index-free adjacency performance guarantee from lesson 01 only applies once you cross from lookup into traversal.

---

## Traversal vs Full Scan

One important nuance: not all graph queries are traversals. Some queries ask about the whole graph:

- "How many nodes have label `:Person`?" — this is a scan, not a traversal
- "Find all `:Person` nodes where `city = 'NYC'`" — this is also a scan, filtered by an index on `city`
- "Find all paths between Alice and Grace" — this is a traversal

Scans and indexes in graph databases work similarly to relational databases — a range index on a property lets you find starting nodes quickly. The graph performance advantage only kicks in once you start traversing relationships from those nodes.

---

**← Back: [The Property Graph Model](02-property-graph-model.md)** | **Next: [Graph Algorithms →](04-graph-algorithms-overview.md)** | [Course Home](../README.md)
