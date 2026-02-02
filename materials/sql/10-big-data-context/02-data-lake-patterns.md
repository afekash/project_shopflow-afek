# Data Lake Patterns

## Overview

Data lakes store massive amounts of raw data (structured, semi-structured, unstructured) in cloud object storage (S3, ADLS, GCS). Understanding data lake patterns is essential for modern data engineering.

## Data Lake vs Data Warehouse

| Aspect | Data Warehouse | Data Lake |
|--------|----------------|-----------|
| **Schema** | Schema-on-write (upfront) | Schema-on-read (flexible) |
| **Data types** | Structured only | All types (JSON, Parquet, images, logs) |
| **Storage** | Expensive (databases) | Cheap (object storage) |
| **Processing** | SQL engines | Spark, Presto, Athena |
| **Use case** | BI, reports | ML, exploration, archives |

## Data Lake Architecture

```
Raw Zone (Bronze)          Refined Zone (Silver)       Curated Zone (Gold)
├── logs/                  ├── cleaned_logs/           ├── user_metrics/
├── events/                ├── processed_events/       ├── sales_dashboard/
└── database_dumps/        └── enriched_data/          └── ml_features/
```

**Bronze:** Raw ingestion (untouched)
**Silver:** Cleaned, validated, deduplicated
**Gold:** Business-level aggregates, ready for BI/ML

## File Formats

### Parquet (Columnar)

**Best for:** Analytics, large datasets

```sql
-- Create Parquet table (Spark/Hive)
CREATE TABLE sales
USING parquet
LOCATION 's3://bucket/sales/';
```

**Benefits:**
- Columnar storage (read only needed columns)
- Excellent compression (5-10× smaller)
- Predicate pushdown (skip row groups)
- Schema embedded in files

**When to use:** OLAP, analytics, data warehouses

### ORC (Columnar)

Similar to Parquet, optimized for Hive.

### JSON (Row-oriented)

**Best for:** Semi-structured, nested data

```sql
CREATE EXTERNAL TABLE events (
    user_id STRING,
    event_type STRING,
    properties MAP<STRING, STRING>
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
LOCATION 's3://bucket/events/';
```

**When to use:** APIs, logs, flexible schemas

### CSV (Row-oriented)

Simple but inefficient for large data.

## Partitioning

Critical for performance - skip irrelevant data.

```sql
-- Partitioned by date
s3://bucket/sales/
    year=2023/
        month=01/
            day=01/
                part-00000.parquet
                part-00001.parquet
            day=02/
                ...
        month=02/
            ...
    year=2024/
        ...
```

**Query with partition pruning:**

```sql
SELECT * FROM sales
WHERE year = 2024 AND month = 1;
-- Only scans year=2024/month=01/ folder
-- Skips 99% of data!
```

## Immutability Pattern

**Data lakes are append-only** - don't UPDATE/DELETE.

**Wrong:**

```sql
UPDATE orders SET status = 'shipped' WHERE order_id = 123;
-- Parquet files are immutable!
```

**Right:**

```sql
-- Insert new version
INSERT INTO orders VALUES (123, 'shipped', '2024-01-15', version=2);

-- Query latest version
SELECT * FROM orders
WHERE (order_id, version) IN (
    SELECT order_id, MAX(version)
    FROM orders
    GROUP BY order_id
);
```

## Delta Lake / Apache Iceberg

Add ACID transactions to data lakes.

### Delta Lake Example

```sql
-- Enable Delta
CREATE TABLE orders
USING delta
LOCATION 's3://bucket/orders/';

-- Now UPDATE works!
UPDATE orders SET status = 'shipped' WHERE order_id = 123;

-- Time travel
SELECT * FROM orders VERSION AS OF 5;  -- Previous version

-- Optimize (compact small files)
OPTIMIZE orders;

-- Vacuum (delete old versions)
VACUUM orders RETAIN 7 DAYS;
```

**Benefits:**
- ACID transactions
- Time travel
- Schema evolution
- MERGE/UPDATE/DELETE support

## Slowly Changing Dimensions (SCD)

Track dimension changes over time.

### SCD Type 1 (Overwrite)

```sql
-- New address overwrites old
MERGE INTO dim_customer
USING staging_customer
ON dim_customer.customer_id = staging_customer.customer_id
WHEN MATCHED THEN UPDATE SET address = staging_customer.address;
```

**Loses history** - simple but no audit trail.

### SCD Type 2 (Add Row)

```sql
-- Add new row, keep old
INSERT INTO dim_customer
SELECT 
    customer_id,
    address,
    CURRENT_DATE AS effective_date,
    '9999-12-31' AS end_date,
    TRUE AS is_current
FROM staging_customer;

-- Expire old row
UPDATE dim_customer
SET end_date = CURRENT_DATE - 1, is_current = FALSE
WHERE customer_id = 123 AND is_current = TRUE;
```

**Tracks full history** - common in data warehouses.

### SCD Type 3 (Add Column)

```sql
ALTER TABLE dim_customer ADD previous_address STRING;

UPDATE dim_customer
SET previous_address = address, address = 'new_address'
WHERE customer_id = 123;
```

**Limited history** (only previous value).

## Data Lake Best Practices

### 1. Partition Strategy

```sql
-- Good: Date partitioning (evenly distributed)
PARTITION BY (year, month, day)

-- Bad: User ID partitioning (skewed - some users have millions of records)
PARTITION BY (user_id)
```

**Rule:** Partition key should have ~1GB - 1TB per partition.

### 2. File Sizing

**Too small:** Millions of tiny files (slow to list)
**Too large:** Can't parallelize, slow reads

**Sweet spot:** 128MB - 1GB per file

```sql
-- Spark: Control file size
spark.sql.files.maxPartitionBytes = 134217728  -- 128MB
```

### 3. Compaction

Merge small files into larger ones.

```sql
-- Delta Lake
OPTIMIZE table_name;

-- Spark (rewrite)
spark.read.parquet("s3://bucket/data/")
     .repartition(100)
     .write.parquet("s3://bucket/data_optimized/");
```

### 4. Schema Evolution

```sql
-- Add column (Delta Lake)
ALTER TABLE events ADD COLUMN user_agent STRING;

-- Parquet: Old files have NULL for new column
-- New files have values
-- Schema merging handles differences
```

## Data Lake SQL Engines

### Apache Spark

```python
# Read Parquet
df = spark.read.parquet("s3://bucket/sales/")

# SQL on data lake
spark.sql("""
    SELECT year, SUM(revenue)
    FROM sales
    WHERE year >= 2020
    GROUP BY year
""")
```

### Presto / Trino

```sql
-- Query S3 directly
SELECT country, COUNT(*)
FROM s3.default.customers
WHERE signup_date >= DATE '2024-01-01'
GROUP BY country;
```

### AWS Athena

```sql
-- Serverless queries on S3
CREATE EXTERNAL TABLE logs (
    timestamp STRING,
    level STRING,
    message STRING
)
PARTITIONED BY (date STRING)
LOCATION 's3://bucket/logs/';

SELECT level, COUNT(*) FROM logs WHERE date = '2024-01-15' GROUP BY level;
```

## Medallion Architecture

Bronze → Silver → Gold pattern.

```sql
-- Bronze: Raw ingestion
CREATE TABLE bronze_events
LOCATION 's3://lake/bronze/events/'
AS SELECT * FROM kafka_stream;

-- Silver: Cleaned
CREATE TABLE silver_events
LOCATION 's3://lake/silver/events/'
AS SELECT 
    user_id,
    event_type,
    CAST(timestamp AS TIMESTAMP) AS event_time
FROM bronze_events
WHERE user_id IS NOT NULL;

-- Gold: Business metrics
CREATE TABLE gold_daily_users
LOCATION 's3://lake/gold/daily_users/'
AS SELECT 
    DATE(event_time) AS date,
    COUNT(DISTINCT user_id) AS daily_active_users
FROM silver_events
GROUP BY DATE(event_time);
```

## Practice Exercises

```sql
-- 1. Create partitioned Parquet table
CREATE TABLE sales (
    sale_id BIGINT,
    amount DECIMAL,
    customer_id BIGINT
)
USING parquet
PARTITIONED BY (year INT, month INT)
LOCATION 's3://bucket/sales/';

-- 2. SCD Type 2 implementation
-- Add new customer record
INSERT INTO dim_customer VALUES (
    123, 'John Doe', 'New Address', 
    CURRENT_DATE, '9999-12-31', TRUE
);

-- Expire old record
UPDATE dim_customer
SET end_date = CURRENT_DATE - 1, is_current = FALSE
WHERE customer_id = 123 AND end_date = '9999-12-31' AND NOT is_current;

-- 3. Query with partition pruning
SELECT SUM(amount)
FROM sales
WHERE year = 2024 AND month = 1;
```

## Key Takeaways

- Data lakes use cheap object storage (S3, ADLS)
- **Parquet** = columnar, compressed, best for analytics
- **Partitioning** critical for performance (skip irrelevant data)
- **Immutability** - append new versions, don't update
- **Delta Lake/Iceberg** add ACID transactions
- **SCD Type 2** tracks dimension history
- Medallion: Bronze (raw) → Silver (clean) → Gold (business)
- File size matters: 128MB - 1GB sweet spot

## What's Next?

[Next: Distributed SQL →](03-distributed-sql.md)

---

[← Back: OLTP vs OLAP](01-oltp-vs-olap.md) | [Course Home](../README.md) | [Next: Distributed SQL →](03-distributed-sql.md)
