# NoSQL Databases

Welcome to the NoSQL module! This course covers the motivations behind NoSQL, the major database paradigms (document, key-value, column-family, graph), and hands-on deep dives into two representative examples: **document stores** (using MongoDB) and **key-value stores** (using Redis). Each deep dive includes replication and sharding with real multi-node Docker clusters.

## Prerequisites

- Basic understanding of relational databases and SQL (see [SQL course](../sql/README.md))
- Docker and Docker Compose installed
- Python 3.10+ and `pip`
- `mongosh` installed locally (or accessible via Docker exec)

## Core Concepts Reference

This course references concepts from the **[Core Concepts library](../core-concepts/README.md)** throughout. These are the tool-agnostic building blocks that underpin document stores, key-value stores, and every other database technology.

When a lesson links to a core concept, the recommended flow is:
1. Follow the link, read the generic theory
2. Return to the NoSQL lesson to see *why this specific tool chose this concept*
3. Where applicable, compare to how you saw it in the SQL course

Key concepts that appear frequently in this module:

| When you see... | The core concept is... |
|-----------------|----------------------|
| LSM-trees, SSTables, commit log | [LSM-Trees and SSTables](../core-concepts/02-data-structures/03-lsm-trees-and-sstables.md) |
| Consistent hashing, token ring | [Consistent Hashing](../core-concepts/03-scaling/03-consistent-hashing.md) |
| CAP theorem, CP vs AP | [CAP Theorem](../core-concepts/04-distributed-systems/01-cap-theorem.md) |
| ACID vs BASE | [ACID vs BASE](../core-concepts/04-distributed-systems/02-acid-vs-base.md) |
| Quorum, consistency levels | [Quorum and Tunable Consistency](../core-concepts/04-distributed-systems/04-quorum-and-tunable-consistency.md) |
| Replica sets, replication | [Replication Patterns](../core-concepts/05-replication-and-availability/01-replication-patterns.md) |
| Elections, failover | [Consensus and Failover](../core-concepts/05-replication-and-availability/02-consensus-and-failover.md) |
| Sharding, shard keys | [Partitioning Strategies](../core-concepts/03-scaling/02-partitioning-strategies.md) |
| Targeted vs scatter-gather queries | [Query Routing Patterns](../core-concepts/06-architecture-patterns/02-query-routing-patterns.md) |
| Cache-aside, write-through, eviction | [Caching Patterns](../core-concepts/07-application-patterns/01-caching-patterns.md) |
| Pub/sub, fan-out, consumer groups | [Pub/Sub and Messaging Patterns](../core-concepts/07-application-patterns/02-pubsub-and-messaging.md) |

## Learning Path

| Module | Topics | Duration |
|--------|---------|----------|
| **01 - Introduction** | [Why NoSQL](01-introduction/01-why-nosql.md), [CAP Theorem & Trade-offs](01-introduction/02-cap-theorem-and-tradeoffs.md) | ~35 min |
| **02 - NoSQL Types** | [Document Stores](02-nosql-types/01-document-stores.md), [Key-Value Stores](02-nosql-types/02-key-value-stores.md), [Column-Family Stores](02-nosql-types/03-column-family-stores.md), [Graph Databases](02-nosql-types/04-graph-databases.md), [Choosing the Right DB](02-nosql-types/05-choosing-the-right-database.md) | ~60 min |
| **03 - Document Store (MongoDB)** | Basics: [Overview & Setup](03-mongodb-basics/01-mongodb-overview.md), [Data Modeling](03-mongodb-basics/02-documents-and-data-modeling.md), [Indexes & Performance](03-mongodb-basics/03-indexes-and-performance.md). Replication: [Replica Set Architecture](04-mongodb-replication/01-replica-set-architecture.md), [Hands-On Replica Set](04-mongodb-replication/02-hands-on-replica-set.md). Sharding: [Sharding Architecture](05-mongodb-sharding/01-sharding-architecture.md), [Hands-On Sharded Cluster](05-mongodb-sharding/02-hands-on-sharded-cluster.md) | ~180 min |
| **06 - Exercises** | [Theory Exercises](06-exercises/01-nosql-theory-exercises.md), [Document-store challenges](06-exercises/02-mongodb-exercises.md) | ~30 min |
| **07 - Key-Value Deep Dive** | [KV Concepts & Tradeoffs](07-key-value-deep-dive/01-kv-concepts-and-tradeoffs.md), [Value Types & Key Design](07-key-value-deep-dive/02-value-types-and-key-design.md), [Common Patterns](07-key-value-deep-dive/03-common-patterns.md), [Caching & Expiration](07-key-value-deep-dive/04-caching-and-expiration.md), [Cache Write Patterns](07-key-value-deep-dive/05-cache-write-patterns.md), [Replication](07-key-value-deep-dive/06-replication.md), [Sharding](07-key-value-deep-dive/07-sharding.md) | ~120 min |

**Total: ~7 hours** (split across three sessions)

## Session Split

- **Session 1 (~1.5 hours):** Modules 01 and 02 — NoSQL concepts and database types
- **Session 2 (~3 hours):** Document store deep dive (MongoDB) — basics, replication, sharding with hands-on clusters
- **Session 3 (~2 hours):** Key-value deep dive (Redis) — Sentinel and Cluster labs

## Lab Environments

Labs are under `labs/` and started via the root Makefile:

- **Document store:** `make lab-nosql` (single node), `make lab-replica-set` (3-node replica set), `make lab-sharded` (sharded cluster)
- **Key-value:** `make lab-redis`, `make lab-redis-sentinel`, `make lab-redis-cluster`

## Tools Used

| Tool | Purpose |
|------|---------|
| **mongosh** | Cluster administration, index management, explain plans, interactive exploration |
| **pymongo** | Application-level patterns: connection strings, read preferences, write concerns |
| **MongoDB Compass** | Optional GUI for visual exploration (mentioned, not used in exercises) |
| **redis-py** | Redis client for Python: single instance, Sentinel, and Cluster modes |
| **redis-cli** | Redis command-line interface for cluster management and inspection |

## Quick Start

Use the project Makefile to start the workspace plus the lab you need:

```bash
# Document store (Module 03 — single node)
make lab-nosql

# Document store — replica set (replication lessons)
make lab-replica-set

# Document store — sharded cluster (sharding lessons)
make lab-sharded

# Key-value (Module 07) — single Redis
make lab-redis

# Key-value — Redis with Sentinel
make lab-redis-sentinel

# Key-value — Redis Cluster
make lab-redis-cluster
```

Stop the current lab with `make down`.

---

**Ready to begin?** Start with [01 - Why NoSQL?](01-introduction/01-why-nosql.md)
