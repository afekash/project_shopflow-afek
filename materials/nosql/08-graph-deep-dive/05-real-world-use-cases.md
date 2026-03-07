---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Real-World Use Cases

```{note}
This lesson requires the Neo4j lab. Run `make lab-neo4j` before starting.
```

Graph databases have moved well beyond their origins as social network infrastructure. Today they are core infrastructure in cybersecurity, machine learning pipelines, AI knowledge systems, and supply chain operations. This lesson walks through concrete patterns in each domain — not toy examples, but the shapes of real production deployments.

---

## Cybersecurity: Fraud Detection and Attack Graphs

Cybersecurity is one of the highest-impact domains for graph technology. The reason is structural: attacks, fraud, and insider threats are not isolated events — they are sequences of connected actions across interconnected entities.

### Fraud Ring Detection

In financial fraud, individual accounts appear legitimate in isolation. The fraud is only visible when you map the connections: multiple accounts share a device fingerprint, phone number, or bank account. Those shared accounts connect to flagged accounts with a few more hops. The "fraud ring" is a subgraph — a cluster of accounts that appear innocent when examined individually but are clearly coordinated when their connections are visible.

A graph query can find all accounts reachable from a flagged account through shared-identity relationships within N hops — a query that is either impossible or catastrophically slow in a relational database at depth 4+.

### Attack Graph Analysis

In network security, an **attack graph** maps possible paths an attacker could take from an entry point (e.g., a compromised laptop) to a target (e.g., a database server). Nodes are hosts, services, and vulnerabilities. Edges are "can exploit to reach."

Graph algorithms on this structure answer:
- What is the shortest path from the internet to the payment database?
- Which single vulnerability, if patched, would cut off the most attack paths? (betweenness centrality on the vulnerability node)
- What is the blast radius if this service is compromised?

Tools like BloodHound (Active Directory attack path analysis) are essentially graph databases running attack graph analysis. The underlying technology is a Neo4j instance.

```{code-cell} python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))

with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")

    # Simplified attack graph: hosts, services, vulnerabilities
    session.run("""
        CREATE (internet:Zone    {name: 'Internet'})
        CREATE (dmz:Host         {name: 'DMZ Web Server',    ip: '10.0.1.10'})
        CREATE (appserver:Host   {name: 'App Server',        ip: '10.0.2.20'})
        CREATE (dbserver:Host    {name: 'Payment DB',        ip: '10.0.3.30', sensitive: true})
        CREATE (vuln_rce:Vuln    {name: 'CVE-2024-1234',     type: 'RCE',     severity: 'critical'})
        CREATE (vuln_sqli:Vuln   {name: 'CVE-2024-5678',     type: 'SQLi',    severity: 'high'})

        CREATE (internet)-[:CAN_REACH]->(dmz)
        CREATE (dmz)-[:HAS_VULN]->(vuln_rce)
        CREATE (vuln_rce)-[:GRANTS_ACCESS]->(appserver)
        CREATE (appserver)-[:HAS_VULN]->(vuln_sqli)
        CREATE (vuln_sqli)-[:GRANTS_ACCESS]->(dbserver)
    """)

with driver.session() as session:
    result = session.run("""
        MATCH path = (internet:Zone {name: 'Internet'})-[*]->(target:Host {sensitive: true})
        RETURN [n IN nodes(path) | coalesce(n.name, n.type)] AS attack_path,
               length(path) AS steps
        ORDER BY steps
    """)
    print("Attack paths from Internet to sensitive hosts:")
    for r in result:
        print(f"  {' → '.join(r['attack_path'])} ({r['steps']} steps)")

driver.close()
```

---

## Machine Learning: Recommendation Engines

Recommendation systems are fundamentally graph problems. Users, items, and the interactions between them form a bipartite graph. The classic "collaborative filtering" insight — recommend items that similar users liked — is a graph traversal:

> "Find users who share purchases with Alice. Return items those users bought that Alice has not."

This is a 3-hop pattern: `Alice → [BOUGHT] → Item ← [BOUGHT] ← OtherUser → [BOUGHT] → NewItem`

At Netflix and Spotify scale, this is computed in batch using GDS and the results are cached. But the *structure* of the query is a graph pattern match.

### Knowledge Graph-Augmented AI (RAG)

A newer application: **GraphRAG**. Large language models hallucinate because they lack grounded, structured knowledge. Knowledge graphs provide exactly that: a structured representation of facts and relationships that can be queried precisely.

The pattern:
1. A knowledge graph contains entities and relationships: `(Drug)-[:TREATS]->(Disease)`, `(Drug)-[:INTERACTS_WITH]->(Drug)`, `(Patient)-[:HAS_CONDITION]->(Disease)`
2. A user asks a question: "What drugs treat diabetes but interact with blood pressure medications?"
3. The question is parsed into a graph query
4. The graph returns precise, structured results
5. An LLM formats the results into a natural language answer

This is used in pharma (drug-drug interaction checking), finance (regulatory compliance), and enterprise search. Neo4j's AuraDB has built-in GraphRAG capabilities, and the pattern is emerging as a standard architecture for enterprise AI.

---

## Network and Infrastructure Operations

IT infrastructure is a graph: servers connect to switches, switches connect to routers, services depend on other services, certificates are issued by CAs, firewall rules govern traffic. Querying this as a relational database (or worse, a flat CMDB) means constant multi-table joins.

Key graph queries in infrastructure management:

- **Blast radius analysis**: if this pod crashes, which upstream services break? (upstream dependency traversal)
- **Certificate chain validation**: trace the issuer chain from a leaf certificate to a root CA
- **Resource ownership**: which teams own resources accessible to this compromised credential?
- **Compliance**: does any data classified as PII flow through an unencrypted channel? (trace data lineage edges, check encryption labels)

ServiceNow, Dynatrace, and Datadog all use graph models for topology mapping.

---

## Supply Chain and Logistics

Supply chains are networks: suppliers supply components, components go into products, products ship through warehouses to retailers. Disruption propagates through this network in ways that are only visible when you model the whole graph.

Graph queries in supply chain:
- **Tier-N supplier risk**: "Which products are at risk if this third-tier supplier is disrupted?"
- **Alternative sourcing**: "If supplier X fails, what is the closest alternative path to fulfill order Y?"
- **Bottleneck identification**: betweenness centrality on supplier nodes reveals single-source dependencies

The 2021 global chip shortage was a supply chain graph problem at planetary scale — cascading failures through tiers of suppliers that no company had mapped in a single system.

---

**← Back: [Graph Algorithms Overview](04-graph-algorithms-overview.md)** | **Next: [Tradeoffs and Limitations →](06-tradeoffs-and-limitations.md)** | [Course Home](../README.md)
