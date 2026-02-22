# Schema Strategies

## The Problem

Every data system must answer: when do you enforce structure on your data?

You can enforce structure when writing data -- reject anything that doesn't conform to the expected format. Or you can accept anything when writing and interpret the structure when reading.

You can also normalize data -- store each fact in exactly one place, eliminating redundancy. Or denormalize -- duplicate data across multiple places to make reads faster.

These two dimensions -- schema enforcement timing and normalization level -- define the fundamental shape of your data model.

## The Solution

Two orthogonal spectrums, each a deliberate trade-off:

1. **Schema-on-write vs schema-on-read**: *When* is structure validated?
2. **Normalized vs denormalized**: *How redundant* is the data?

Every data system makes choices on both dimensions, often implicitly. Making them explicit lets you understand why a technology was designed the way it was and whether it fits your use case.

## How It Works

### Schema-on-Write

Structure is validated before the data is stored. The system rejects writes that don't conform to the predefined schema. All stored data is guaranteed to be structurally valid.

```
Table definition (defined once, enforced forever):
  CREATE TABLE orders (
    order_id   BIGINT PRIMARY KEY,
    customer   VARCHAR(255) NOT NULL,
    total      DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
  );

Valid write:
  INSERT INTO orders (order_id, customer, total) VALUES (1, 'Alice', 99.99); ✓

Invalid write:
  INSERT INTO orders (order_id, customer) VALUES (2, 'Bob');
  -- ERROR: NOT NULL constraint on total violated ✗
```

**What you gain:**
- Data quality guaranteed at the storage layer: you never have to handle structurally invalid data at read time
- Queries are simpler: you know exactly what fields exist and what type they are
- The database can optimize based on known structure (indexes, statistics)
- Errors surface immediately at write time (close to the source)

**What you give up:**
- Schema changes are expensive: adding a column to a table with 100 million rows requires a migration (ALTER TABLE), which can take hours and may lock the table
- Rigid schema slows iteration: every change to the data model requires a migration before new data can be stored
- Impedance mismatch: application objects often have polymorphic structure that doesn't fit neatly into fixed columns

### Schema-on-Read

Data is stored in any format. Structure is imposed at read time by the consumer. The storage layer is flexible; the interpretation layer is where structure is defined.

```
Stored as-is (no validation at write time):
  { "order_id": 1, "customer": "Alice", "total": 99.99, "region": "EU" }
  { "order_id": 2, "customer": "Bob" }   ← missing "total" -- allowed!
  { "order_id": 3, "items": [...], "customer": "Carol", "total": 149.99 }

At read time, the application interprets what it finds:
  order = db.find(order_id=2)
  total = order.get("total", 0.0)   # handle missing field in application
```

**What you gain:**
- No migrations: add a new field by just including it in new writes; old reads return missing-field defaults
- Schema evolution is cheap: the first write of a new format is valid immediately
- Handles heterogeneous data: different records can have different shapes (polymorphic entities)
- Data from external sources can be stored immediately without transformation

**What you give up:**
- Data quality is the application's responsibility: invalid data silently stored
- Reading is more complex: every reader must handle missing fields, wrong types, structural variations
- Bugs surface at read time, not write time -- often far from the source
- Query optimization is harder: the storage layer can't assume field existence or type

### Schema Evolution

In practice, schemas always change. The strategies differ in how much they fight that reality:

```
Adding a "discount" field to orders:

Schema-on-write:
  ALTER TABLE orders ADD COLUMN discount DECIMAL(10,2) DEFAULT NULL;
  -- Migration required. On large tables: plan a maintenance window.
  -- After migration: all queries know "discount" exists.

Schema-on-read:
  Just start writing { "discount": 10.00 } in new orders.
  Old orders don't have "discount". New code must handle both cases.
  -- No migration. But code complexity increases slightly.
```

### Normalization vs Denormalization

A perpendicular dimension: how redundant is the data?

**Normalized** (3NF and beyond): Each fact is stored in exactly one place. Data is split into many tables connected by foreign keys. Updates affect one place; no risk of inconsistency.

```
Normalized orders (each fact once):
  customers: { id: 1, name: "Alice", email: "alice@example.com" }
  orders:    { id: 101, customer_id: 1, total: 99.99 }
  items:     { order_id: 101, product_id: 42, qty: 2 }
  products:  { id: 42, name: "Widget", price: 49.99 }

To get order details: JOIN 4 tables.
```

**Denormalized**: Data is duplicated across records to avoid joins. Reads are fast (everything in one place); writes are complex (must update all copies).

```
Denormalized order (everything in one document/record):
  {
    order_id: 101,
    customer_name: "Alice",        ← duplicated
    customer_email: "alice@...",   ← duplicated
    total: 99.99,
    items: [
      { product_name: "Widget", price: 49.99, qty: 2 }  ← duplicated
    ]
  }

To get order details: one document read. No join.
If Alice changes her email → must update every order ← update anomaly risk
```

**The normalization/denormalization spectrum:**

| Level | Storage | Read cost | Write cost | Risk |
|-------|---------|-----------|------------|------|
| Highly normalized | Compact | Many joins | Simple update | Complex queries |
| Partially normalized | Moderate | Some joins | Moderate | Some duplication |
| Fully denormalized | Large | No joins | Update all copies | Update anomalies |

**OLTP vs OLAP**:
- **OLTP** (transactional systems): Normalize. You update individual records frequently. Normalization prevents update anomalies. JOINs are the cost.
- **OLAP** (analytical systems): Denormalize. You read huge aggregations across many records. Denormalization avoids JOINs across billions of rows. Redundancy is the cost.

```
Star schema (analytical denormalization):
  Fact table: sales (order_id, date_key, product_key, customer_key, amount)
  Dimension tables: dim_date, dim_product, dim_customer
  
  One JOIN to each dimension -- much simpler than fully normalized OLTP schema.
  Reads are optimized for aggregations over the fact table.
```

### The Combined View

```
                    Schema-on-Write         Schema-on-Read
                    ──────────────          ──────────────
Normalized          Relational OLTP         Rare (hybrid approaches)
                    (PostgreSQL, MySQL)      
                    
Denormalized        Relational OLAP         Document stores, key-value
                    (star schema DW)        (MongoDB, DynamoDB, Cassandra)
```

## Trade-offs

**Schema-on-write + normalized** (classic RDBMS):
- Highest data quality and consistency guarantees
- Slowest schema evolution
- Best for: financial systems, inventory, any system where correctness matters more than agility

**Schema-on-read + denormalized** (document/key-value):
- Fastest development iteration
- Highest risk of data quality issues at scale
- Best for: rapidly evolving products, heterogeneous data, read-heavy workloads with known access patterns

**Schema-on-write + denormalized** (analytical warehouses):
- Predetermined structure for known analytical queries
- Great read performance, higher storage cost
- Best for: BI, reporting, aggregations over large datasets

## Where You'll See This

- **Relational databases**: Schema-on-write by definition; normalization level is the designer's choice
- **Document databases** (MongoDB, CouchDB): Schema-on-read by default; application enforces structure; denormalization is common (embed related data)
- **Column-family stores** (Cassandra): Schema-on-write for column families but flexible within rows; heavily denormalized around query patterns
- **Data lakes** (S3 + Parquet): Schema-on-read -- raw files stored in any format; schemas defined at query time by Spark, Athena, etc.
- **Data warehouses** (Redshift, BigQuery, Snowflake): Schema-on-write with denormalized star/snowflake schemas optimized for analytical queries
- **Event sourcing**: Append-only schema-on-read -- events are stored raw; projections interpret and reshape data for different consumers

---

**Next:** [Query Routing Patterns →](02-query-routing-patterns.md)
