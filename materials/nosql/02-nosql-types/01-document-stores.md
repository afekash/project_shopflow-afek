# Document Stores

## What Is a Document Store?

A document store organizes data as **semi-structured documents** — typically JSON or a JSON-like format. Each document is a self-contained unit that can hold nested objects, arrays, and mixed data types.

Unlike a relational table row (which must match a fixed schema), documents in the same collection can have completely different shapes.

```json
// Two documents in the same "users" collection
// No schema enforcement -- they look completely different

{
  "id": "user_001",
  "name": "Alice",
  "email": "alice@example.com",
  "plan": "enterprise",
  "team": { "name": "Acme Engineering", "size": 50 }
}

{
  "id": "user_002",
  "name": "Bob",
  "email": "bob@example.com",
  "twitter": "@bob_codes",
  "preferences": {
    "theme": "dark",
    "notifications": ["email", "sms"]
  }
}
```

## The Data Model

### Documents

A document is a key-value map where values can be:

- Primitive types: strings, numbers, booleans, dates, null
- Arrays of any of the above
- Nested documents (sub-documents)

This directly mirrors how most programming languages model objects — which is why document stores became popular with modern application development. The document is always the unit of storage, retrieval, and atomicity.

### Collections

Documents are grouped into **collections** (analogous to tables). Collections typically don't enforce a schema — you can insert any document into any collection. Different document stores handle this differently; some offer optional schema validation, others are fully schemaless.

### Document Identity

Every document has a unique identifier field. Most document stores auto-generate IDs if you don't provide one, often encoding metadata like timestamp and node identity into the ID to guarantee uniqueness across a distributed cluster without requiring coordination.

## How Document Stores Work Internally

### Storage Format

Documents are stored in a binary-encoded format on disk (e.g., BSON, MessagePack, or similar). Binary formats add type information and are more efficient to parse than raw text JSON. The document is stored as a single contiguous unit — meaning reads that touch a single document are very efficient.

### Indexing

Document stores support **B-tree indexes** on any field within a document, including nested fields and array elements. Secondary indexes allow queries beyond just the primary key. Without an index, queries scan every document in the collection — a full collection scan — which is expensive at scale.

### Schema-on-Read vs Schema-on-Write

> **Core Concept:** See [Schema Strategies](../../core-concepts/06-architecture-patterns/01-schema-strategies.md) for the full schema-on-write vs schema-on-read trade-off and how it connects to normalization vs denormalization.


| Approach                                    | When schema is enforced | Flexibility | Who validates |
| ------------------------------------------- | ----------------------- | ----------- | ------------- |
| **Schema-on-write** (relational)            | Before insert           | Low         | Database      |
| **Schema-on-read** (document store default) | When you read/process   | High        | Application   |


In SQL, you had schema-on-write — the database enforced structure via `CREATE TABLE`, and any row that violated the schema was rejected before storage. Document stores default to schema-on-read: because documents are self-describing (each document carries its own field names), you can evolve your data model without `ALTER TABLE` migrations. The trade-off: data quality is now the application's responsibility at read time, not the database's at write time.

With schema-on-read, you can add new fields to documents freely. But application code must handle variation — old documents might not have a field that new ones do.

**Best practice**: Use optional JSON Schema validation (supported by most document stores) to enforce constraints on critical fields while preserving flexibility during iteration.

## Scaling Document Stores

### Replication (High Availability)

> **Core Concept:** See [Replication Patterns](../../core-concepts/05-replication-and-availability/01-replication-patterns.md) for primary-secondary replication and how it compares to peer-to-peer approaches.

Most document stores support replication: multiple nodes hold copies of the same data. Typically, one node is the **primary** (handles all writes) and others are **secondaries** that replicate from it. If the primary fails, a secondary is automatically promoted. This provides durability and read scalability.

### Sharding (Horizontal Write Scaling)

> **Core Concept:** See [Partitioning Strategies](../../core-concepts/03-scaling/03-partitioning-strategies.md) for range vs hash partitioning and how to choose a partition key.

When a single node can no longer handle write throughput or data volume, the collection is **sharded** — partitioned across multiple machines using a **shard key**. Each shard holds a subset of the documents. The shard key choice is critical: a poor choice leads to hotspots (all writes going to one shard).

```
                    Shard Key: user_id

┌────────────────────────────────────────────────┐
│  user_id: 0001–3333   →  Shard 1               │
│  user_id: 3334–6666   →  Shard 2               │
│  user_id: 6667–9999   →  Shard 3               │
└────────────────────────────────────────────────┘
```

## Strengths

**Natural mapping to application code**
Application objects map directly to documents. No ORM layer needed to translate between objects and rows.

**Flexible schema evolution**
Add new fields to documents without migrations. Old documents simply won't have the new field.

**Rich querying within a document**
Query by nested fields, filter by array contents, use aggregation pipelines. Far richer than key-value lookups.

**Locality of reference**
Data that is accessed together is stored together via embedded sub-documents. No joins across tables required for common access patterns.

**Designed for horizontal scaling**
Sharding and replication are first-class features in most document store engines.

## Weaknesses

**Expensive cross-document aggregations**
Aggregating across many documents (like a SQL `GROUP BY` across millions of rows) must process each document individually. There are no pre-computed statistics the way relational query planners maintain them.

**Data duplication**
Embedding data instead of referencing it means the same information can exist in multiple documents. Updates must touch every copy.

**No efficient multi-document joins**
Document stores are not optimized for joins. Queries that need to combine data from multiple collections are expensive. Schema design should avoid them by embedding related data.

**Weak multi-document transactionality (historically)**
The original document store model guaranteed atomicity only within a single document. Multi-document transactions have been added to several systems, but they carry coordination overhead and are not the primary design pattern.

## Main Players


| Database              | Notable For                                                                 |
| --------------------- | --------------------------------------------------------------------------- |
| **MongoDB**           | Most popular, richest feature set, best horizontal scaling story            |
| **CouchDB**           | Built-in replication, HTTP API, offline-first mobile sync                   |
| **Amazon DocumentDB** | MongoDB-compatible managed service on AWS                                   |
| **Couchbase**         | High performance, memory-first architecture, SQL-like query language (N1QL) |
| **Firestore**         | Google's cloud-native document store, real-time sync                        |


## Primary Use Cases

**Content Management Systems**
Articles, blog posts, and pages all have different fields. A document store lets each content type evolve independently without complex table hierarchies.

**User Profiles and Preferences**
Users accumulate different settings, social connections, and preferences over time. Documents handle this variation naturally.

**Product Catalogs**
A smartphone has different attributes (RAM, screen size, carrier) than a t-shirt (size, color, material). Document stores handle polymorphic product types without awkward inheritance modeling in a relational schema.

**Event Logging and Activity Feeds**
Events are naturally self-contained records. Write once, query by time range or event type.

**Mobile and Web Application Backends**
The document shape matches JSON API responses, so the database layer becomes thin and the impedance mismatch between application and storage disappears.

## When NOT to Use Document Stores

- **Complex multi-entity transactions**: Transferring money between accounts requires atomic updates across multiple documents — awkward in document stores and not their design intent
- **Highly relational data**: If your data naturally has many-to-many relationships with complex join patterns, a relational database or graph database is a better fit
- **Analytical workloads**: Aggregating across millions of documents to compute statistics is better served by columnar databases (Redshift, BigQuery) or column-family stores

## Advanced Note: Document Stores and ACID

The classic document store guarantee is **single-document atomicity**: within one document, all updates are applied or none are. This is sufficient for many workloads because embedding related data into a single document keeps logically related state co-located.

Several modern document stores have added **multi-document ACID transactions** to close the gap with relational databases. The trade-off remains: transactions require coordination across nodes or documents, adding latency. A well-designed document schema that embeds related data minimizes the need for transactions in the first place.

> **At Scale**: At large scale, transaction support becomes a liability — coordination is expensive when data is distributed across many shards. Systems operating at extreme scale (Facebook-scale user graphs, Google-scale analytics) typically abandon multi-document transactions entirely and handle consistency at the application layer.

## Summary


| Aspect      | Document Store                                          |
| ----------- | ------------------------------------------------------- |
| Data model  | JSON documents with nested structure                    |
| Schema      | Flexible, schema-on-read (optional validation)          |
| Scaling     | Horizontal via sharding, HA via replication             |
| Consistency | Tunable (strong to eventual)                            |
| Joins       | Avoid — embed related data                              |
| Best for    | Content, profiles, catalogs, event logs, app backends   |
| Avoid when  | Complex transactions, highly relational data, analytics |


---

**Next:** [Key-Value Stores →](02-key-value-stores.md)

---

[← Back: CAP Theorem](../01-introduction/02-cap-theorem-and-tradeoffs.md) | [Course Home](../README.md)
