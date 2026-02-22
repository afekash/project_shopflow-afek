# Why NoSQL?

## The Relational Model: A Brief History

Relational databases have been the foundation of software since the 1970s. Edgar Codd's relational model and SQL gave us structured, consistent, and durable data storage that powered almost every application for three decades. For most use cases -- banking systems, ERPs, e-commerce -- relational databases are still the right choice.

But around 2005–2010, something changed.

## The Web 2.0 Problem

The explosion of social media, mobile applications, and the internet of things created data challenges that relational databases were never designed to handle:

| Challenge | Example | Problem |
|-----------|---------|---------|
| **Scale** | Facebook: 3 billion users | A single PostgreSQL server can't store all of it |
| **Velocity** | Twitter: 500K tweets/minute | Write throughput saturates single-node disk I/O |
| **Variety** | User profiles with different fields | Rigid schemas require migrations for every change |
| **Volume** | IoT sensors: millions of events/second | Relational row storage is not efficient for time-series |

Companies like Google, Amazon, Facebook, and LinkedIn hit these walls first. Their solutions became the open-source databases we now call "NoSQL."

> **"Not Only SQL"** -- NoSQL doesn't mean abandoning SQL. It means choosing the right tool for each problem. Most modern systems use relational databases alongside NoSQL databases.

## Where Relational Databases Hit Walls

### 1. Vertical Scaling Has a Ceiling

Relational databases are designed to run on a **single server**. When you need more capacity, you scale *up*: more CPU, more RAM, bigger disks. This is called **vertical scaling**. At some point there is no bigger machine, or the cost becomes prohibitive. NoSQL databases are architected for **horizontal scaling**: spread data across many commodity nodes.

> **Core Concept:** For the full analysis of why vertical scaling hits a ceiling and how horizontal scaling distributes load, see [Vertical vs Horizontal Scaling](../../core-concepts/03-scaling/01-vertical-vs-horizontal.md).

In the SQL course, we mostly worked with single-node databases where vertical scaling sufficed. NoSQL databases were designed ground-up for horizontal scaling -- this is the fundamental architectural difference. Every NoSQL type covered in the next module makes different trade-offs around *how* to distribute data horizontally: key-value stores use consistent hashing, column-family stores use a peer-to-peer token ring, and document stores use range-based sharding. Same concept, different choices.

### 2. Rigid Schemas Slow Down Development

In a relational database, every row in a table must have the same columns (schema). Adding a new field requires an `ALTER TABLE` migration -- which on a table with 100 million rows can take hours and lock the table.

**The impedance mismatch**: Application code uses objects and arrays. Relational tables use rows and foreign keys. Converting between the two adds complexity.

Consider storing a user profile:

```sql
-- Relational: must know all fields upfront
CREATE TABLE users (
    id          BIGINT PRIMARY KEY,
    name        VARCHAR(255),
    email       VARCHAR(255),
    twitter_url VARCHAR(255),   -- added in sprint 4
    bio         TEXT,            -- added in sprint 7
    avatar_url  VARCHAR(500)     -- added in sprint 12, migration required each time
);
```

```json
// NoSQL document: schema evolves naturally
{
  "_id": "user_123",
  "name": "Alice",
  "email": "alice@example.com",
  "twitter_url": "https://twitter.com/alice",
  "bio": "Data engineer at Acme Corp",
  "avatar_url": "https://cdn.example.com/avatars/alice.jpg",
  "badges": ["early_adopter", "power_user"]   // array of strings, no join table needed
}
```

### 3. Joins Don't Scale Across Machines

The SQL `JOIN` operation works brilliantly on a single server because all the data is local. But if you horizontally shard your relational database across 10 machines, a single query might need to gather data from all 10 nodes and merge it -- this is called a **distributed join** and it is expensive.

NoSQL databases sidestep this by designing data models that avoid joins: data that is accessed together is stored together.

## What Makes NoSQL Different

NoSQL databases don't share a single design. They are a family of databases that make different trade-offs:

| Property | Relational | NoSQL |
|----------|------------|-------|
| **Schema** | Fixed, enforced upfront | Flexible, enforced by application |
| **Scaling** | Primarily vertical | Primarily horizontal |
| **Joins** | First-class, efficient | Avoided or approximated |
| **Consistency** | ACID by default | Trade-offs exposed to developer |
| **Data model** | Tables and rows | Documents, key-value, columns, graphs |

### Four Major Paradigms

NoSQL databases cluster into four major types (covered in depth in the next module):

```
┌─────────────────────────────────────────────────────────────────┐
│                        NoSQL Database Types                     │
├───────────────┬───────────────┬──────────────┬──────────────────┤
│  Document     │  Key-Value    │   Column-    │   Graph          │
│  Store        │  Store        │   Family     │                  │
│               │               │              │                  │
│  MongoDB      │  Redis        │  Cassandra   │  Neo4j           │
│  CouchDB      │  DynamoDB     │  HBase       │  ArangoDB        │
├───────────────┴───────────────┴──────────────┴──────────────────┤
│  Each makes different trade-offs in: data model, scale,         │
│  consistency, and query flexibility                             │
└─────────────────────────────────────────────────────────────────┘
```

## When to Use NoSQL (and When Not To)

NoSQL is not automatically better. Choose based on your actual needs:

**Choose NoSQL when:**
- Your data doesn't fit neatly into tables (semi-structured, hierarchical, or polymorphic)
- You need to write or read millions of records per second
- Your schema evolves rapidly and migrations are slowing you down
- You need to distribute data across geographic regions
- Your data is inherently graph-like (relationships are the data)

**Stick with relational when:**
- You need complex multi-table transactions (banking, inventory, billing)
- Your data is well-structured and relationships are stable
- You need ad-hoc querying flexibility across many dimensions
- Your scale is manageable with a single server (most applications!)
- Your team knows SQL well and the ecosystem matters

**Advanced Note:** The line is blurring. PostgreSQL now supports JSONB (flexible document storage), full-text search, and even graph extensions. MongoDB now supports multi-document ACID transactions. Choosing a database is increasingly about ecosystem, operational familiarity, and specific performance characteristics -- not a binary relational vs. NoSQL decision.

## Connecting to What You Know

You already know SQL from the [SQL module](../../sql/README.md). Here is how concepts map:

| SQL Concept | NoSQL Analog |
|-------------|-------------|
| Database | Database |
| Table | Collection (documents) / Keyspace (Cassandra) |
| Row | Document / Item / Node |
| Column | Field / Attribute / Property |
| Primary key | `_id` / partition key |
| Foreign key | Embedded document or reference |
| JOIN | Avoided -- embed related data |
| INDEX | Index (similar concept, different implementations) |
| ACID transaction | Write concern / consistency level (tunable) |

## At Scale

Real-world large-scale systems rarely run a single database type. Companies like Netflix, Uber, and Airbnb use **polyglot persistence** -- different databases for different needs within the same system:

- **PostgreSQL** for financial transactions and billing (ACID required)
- **Redis** for session caching and real-time leaderboards (speed required)
- **MongoDB** for user-generated content and product catalogs (schema flexibility required)
- **Cassandra** for activity feeds and time-series metrics (write throughput required)
- **Neo4j** for recommendation engines and fraud detection (relationships are the data)

The skill is not picking "the best database" -- it's knowing which tool fits which problem.

## Summary

- Relational databases are excellent for structured, transactional data -- don't abandon them without reason
- Web-scale data (billions of users, millions of events/second) exposed limits in vertical scaling, rigid schemas, and distributed joins
- NoSQL databases trade some relational guarantees (like strict ACID and flexible joins) for horizontal scalability, schema flexibility, and high throughput
- NoSQL is a family, not a single thing -- there are four major paradigms, each suited to different problems

---

**Next:** [CAP Theorem and Trade-offs →](02-cap-theorem-and-tradeoffs.md)

---

[Course Home](../README.md)
