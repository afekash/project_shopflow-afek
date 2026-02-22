# NoSQL Databases

Welcome to the NoSQL module! This course covers the motivations behind NoSQL, the major database paradigms, and a deep hands-on dive into MongoDB -- including replication and sharding using real multi-node Docker clusters.

## Prerequisites

- Basic understanding of relational databases and SQL (see [SQL course](../sql/README.md))
- Docker and Docker Compose installed
- Python 3.10+ and `pip`
- `mongosh` installed locally (or accessible via Docker exec)

## Core Concepts Reference

This course references concepts from the **[Core Concepts library](../core-concepts/README.md)** throughout. These are the tool-agnostic building blocks that underpin MongoDB, Cassandra, Redis, and every other database technology.

When a lesson links to a core concept, the recommended flow is:
1. Follow the link, read the generic theory
2. Return to the NoSQL lesson to see *why this specific tool chose this concept*
3. Where applicable, compare to how you saw it in the SQL course

Key concepts that appear frequently in this module:

| When you see... | The core concept is... |
|-----------------|----------------------|
| LSM-trees, SSTables, commit log | [LSM-Trees and SSTables](../core-concepts/02-data-structures/03-lsm-trees-and-sstables.md) |
| Consistent hashing, token ring | [Consistent Hashing](../core-concepts/03-scaling/02-consistent-hashing.md) |
| CAP theorem, CP vs AP | [CAP Theorem](../core-concepts/04-distributed-systems/01-cap-theorem.md) |
| ACID vs BASE | [ACID vs BASE](../core-concepts/04-distributed-systems/02-acid-vs-base.md) |
| Quorum, consistency levels | [Quorum and Tunable Consistency](../core-concepts/04-distributed-systems/04-quorum-and-tunable-consistency.md) |
| Replica sets, replication | [Replication Patterns](../core-concepts/05-replication-and-availability/01-replication-patterns.md) |
| Elections, failover | [Consensus and Failover](../core-concepts/05-replication-and-availability/02-consensus-and-failover.md) |
| Sharding, shard keys | [Partitioning Strategies](../core-concepts/03-scaling/03-partitioning-strategies.md) |
| Targeted vs scatter-gather queries | [Query Routing Patterns](../core-concepts/06-architecture-patterns/02-query-routing-patterns.md) |

## Learning Path

| Module | Topics | Duration |
|--------|---------|----------|
| **01 - Introduction** | [Why NoSQL](01-introduction/01-why-nosql.md), [CAP Theorem & Trade-offs](01-introduction/02-cap-theorem-and-tradeoffs.md) | ~35 min |
| **02 - NoSQL Types** | [Document Stores](02-nosql-types/01-document-stores.md), [Key-Value Stores](02-nosql-types/02-key-value-stores.md), [Column-Family Stores](02-nosql-types/03-column-family-stores.md), [Graph Databases](02-nosql-types/04-graph-databases.md), [Choosing the Right DB](02-nosql-types/05-choosing-the-right-database.md) | ~60 min |
| **03 - MongoDB Basics** | [Overview & Setup](03-mongodb-basics/01-mongodb-overview.md), [Data Modeling](03-mongodb-basics/02-documents-and-data-modeling.md), [Indexes & Performance](03-mongodb-basics/03-indexes-and-performance.md) | ~70 min |
| **04 - Replication** | [Replica Set Architecture](04-mongodb-replication/01-replica-set-architecture.md), [Hands-On Replica Set](04-mongodb-replication/02-hands-on-replica-set.md) | ~50 min |
| **05 - Sharding** | [Sharding Architecture](05-mongodb-sharding/01-sharding-architecture.md), [Hands-On Sharded Cluster](05-mongodb-sharding/02-hands-on-sharded-cluster.md) | ~60 min |
| **06 - Exercises** | [Theory Exercises](06-exercises/01-nosql-theory-exercises.md), [MongoDB Challenges](06-exercises/02-mongodb-exercises.md) | ~30 min |

**Total: ~5 hours** (split across two sessions)

## Session Split

- **Session 1 (~1.5 hours):** Modules 01 and 02 -- NoSQL concepts and database types
- **Session 2 (~3 hours):** Modules 03-05 -- MongoDB deep dive with hands-on cluster exercises

## Demo Apps

All hands-on infrastructure lives under `demo-app/`:

- [`demo-app/replica-set/`](demo-app/replica-set/README.md) -- 3-node MongoDB replica set
- [`demo-app/sharded-cluster/`](demo-app/sharded-cluster/README.md) -- Full sharded cluster (mongos + config servers + 2 shards)
- [`demo-app/app/`](demo-app/app/) -- Python scripts for application-level patterns

## Tools Used

| Tool | Purpose |
|------|---------|
| **mongosh** | Cluster administration, index management, explain plans, interactive exploration |
| **pymongo** | Application-level patterns: connection strings, read preferences, write concerns |
| **MongoDB Compass** | Optional GUI for visual exploration (mentioned, not used in exercises) |

## Quick Start

```bash
# Start a single MongoDB node (Module 03)
docker run -d --name mongodb -p 27017:27017 mongo:7

# Connect with mongosh
mongosh "mongodb://localhost:27017"

# Start the replica set (Module 04)
cd demo-app/replica-set
docker compose up -d
bash init-replica.sh

# Start the sharded cluster (Module 05)
cd demo-app/sharded-cluster
docker compose up -d
bash init-sharding.sh
```

---

**Ready to begin?** Start with [01 - Why NoSQL?](01-introduction/01-why-nosql.md)
