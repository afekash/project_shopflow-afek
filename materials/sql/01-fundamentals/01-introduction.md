# Introduction to SQL

## Overview

SQL (Structured Query Language) is the standard language for interacting with relational databases. Whether you're working with traditional OLTP systems, data warehouses, or modern data lakes, SQL remains the lingua franca of data engineering.

## What is SQL?

SQL is a **declarative language** - you describe *what* you want, not *how* to get it. The database engine's query optimizer figures out the execution plan.

```sql
-- You write (declarative):
SELECT ProductName, UnitPrice 
FROM Products 
WHERE UnitPrice > 50;

-- The optimizer decides:
-- Should I scan the whole table?
-- Is there an index on UnitPrice?
-- What join algorithm should I use if this gets more complex?
```

## SQL's Role in Data Engineering

As a data engineer, you'll use SQL for:

1. **ETL/ELT Pipelines** - Transforming data in motion
2. **Data Quality** - Validating, deduplicating, profiling data
3. **Analytics** - Aggregating metrics, building reports
4. **Schema Design** - Creating tables, constraints, indexes
5. **Data Modeling** - Star schemas, snowflake schemas, data vault

## The Northwind Database

This course uses **Northwind**, a classic database representing an import-export company.

### Entity Relationship Diagram
View in the schema designer which should show something like this: [ERD](northwind-schema.png)

### Key Tables

- **Customers** (91 rows) - Companies that buy products
- **Orders** (830 rows) - Customer orders from 1996-1998
- **Order Details** (2,155 rows) - Line items (junction/fact table)
- **Products** (77 rows) - Items for sale
- **Categories** (8 rows) - Beverages, Condiments, Confections, etc.
- **Suppliers** (29 rows) - Companies that supply products
- **Employees** (9 rows) - Sales representatives
- **Shippers** (3 rows) - Shipping companies

## OLTP vs OLAP: Why It Matters

### OLTP (Online Transaction Processing)

Northwind is an **OLTP system** - optimized for transactional workloads:

- **Many small transactions** - Insert an order, update inventory
- **High concurrency** - Many users making changes simultaneously
- **ACID guarantees** - Atomicity, Consistency, Isolation, Durability
- **Normalized schema (3NF)** - Minimal redundancy, referential integrity
- **Row-oriented storage** - Fast reads/writes of individual records

### OLAP (Online Analytical Processing)

Data warehouses are **OLAP systems** - optimized for analytics:

- **Few large queries** - "Show me all sales by region for Q4"
- **Read-heavy workload** - Rarely updated, mostly queried
- **Eventual consistency acceptable** - Batch updates, ETL jobs
- **Denormalized schema (star/snowflake)** - Fast aggregations, pre-joined data
- **Column-oriented storage** - Fast scans of specific columns across millions of rows

### Example: Same Business Question, Different Designs

**OLTP (Northwind):**

```sql
-- Must JOIN 4 tables to get order totals by category
SELECT 
    c.CategoryName,
    SUM(od.Quantity * od.UnitPrice * (1 - od.Discount)) AS Revenue
FROM Orders o
    INNER JOIN [Order Details] od ON o.OrderID = od.OrderID
    INNER JOIN Products p ON od.ProductID = p.ProductID
    INNER JOIN Categories c ON p.CategoryID = c.CategoryID
WHERE YEAR(o.OrderDate) = 1997
GROUP BY c.CategoryName;
```

**OLAP (Star Schema):**

```sql
-- Fact table already has CategoryName denormalized
SELECT 
    CategoryName,
    SUM(Revenue) AS Revenue
FROM FactOrders
WHERE OrderYear = 1997
GROUP BY CategoryName;
```

The OLAP version is faster because:
1. **Pre-joined data** - No JOINs needed at query time
2. **Columnar storage** - Only reads CategoryName and Revenue columns
3. **Pre-aggregated** - Revenue already calculated
4. **Partitioned** - Can skip entire year partitions

## Advanced Insight: Query Optimization Philosophy

Understanding the **optimizer** is crucial for data engineers:

1. **Cost-Based Optimization** - Estimates I/O, CPU, memory costs for each plan
2. **Statistics** - Tracks cardinality (row counts), data distribution
3. **Heuristics** - Rules like "push predicates down", "eliminate unnecessary columns"
4. **Execution Plans** - The actual steps the engine takes (you can view these!)

```sql
-- In SQL Server, see the execution plan:
SET SHOWPLAN_TEXT ON;
GO
SELECT * FROM Products WHERE UnitPrice > 50;
GO
SET SHOWPLAN_TEXT OFF;
```

## Understanding Complexity: Big O Notation

When discussing query performance, we use **Big O notation** to describe how an algorithm's resource usage (time or space) grows as the input size increases.

> **Core Concept:** For the full Big O theory -- all complexity classes, the at-scale table (O(n) that takes 1ms on 1,000 rows takes 16 minutes on 1 billion), and language-agnostic examples -- see [Big O Notation](../../core-concepts/01-complexity-and-performance/01-big-o-notation.md).

Understanding complexity is essential for SQL because the **query optimizer uses cost models based on these same principles**:

- An index seek is O(log n) -- the optimizer prefers it when selectivity is high
- A table scan is O(n) -- the optimizer uses it when it's cheaper than the index (e.g., returning most of the table)
- A hash join is O(n + m) but requires memory; a nested loop is O(n × m) but uses less memory
- The optimizer chooses between these based on estimated cardinality and available memory

### SQL Operation Examples

```sql
-- O(1) - Index lookup by primary key
SELECT * FROM Products WHERE ProductID = 42;
-- Uses clustered index, direct access

-- O(log n) - Binary search on indexed column
SELECT * FROM Products WHERE UnitPrice = 18.00;
-- Uses B-tree index, log(77) ≈ 6 comparisons

-- O(n) - Full table scan
SELECT * FROM Products WHERE ProductName LIKE '%soup%';
-- Must check all 77 rows (no index on substring search)

-- O(n log n) - Sorting without index
SELECT * FROM Products ORDER BY UnitPrice DESC;
-- If no index exists, must sort in memory

-- O(n²) - Nested loop join (worst case)
SELECT *
FROM Orders o
    CROSS JOIN Customers c
WHERE o.CustomerID = c.CustomerID;
-- For each of 830 orders, scans 91 customers = 75,530 comparisons
-- In practice, the optimizer will use an index on the join condition to optimize the query or use a hash join if the tables are small enough.
```

**Rule of thumb**: If you see O(n²) or worse in production queries, investigate immediately. It's often fixable with indexes or query rewrites.

### Shuffling and Batching in Big Data

When working with distributed systems (like Spark, Hadoop, or distributed databases), two key concepts affect performance:

**Shuffling** - Moving data between nodes in a cluster. This happens when you need to reorganize data (e.g., during JOINs or GROUP BY operations). Shuffling is expensive because it involves network I/O and disk writes. Minimizing shuffles is crucial for performance. See [Query Routing Patterns](../../core-concepts/06-architecture-patterns/02-query-routing-patterns.md) for how distributed query engines minimize this cost.

**Batching** - Processing data in groups instead of one record at a time. Instead of performing 1 million individual operations, you send 1 query that processes 1 million rows. This reduces overhead and improves throughput dramatically.

Both concepts become critical when your data doesn't fit on a single machine and you need distributed processing.


## Key Takeaways

- SQL is **declarative** - you specify what, not how
- Northwind is an **OLTP system** with normalized tables
- **OLTP** = many small writes, normalized, row-oriented
- **OLAP** = few large reads, denormalized, column-oriented
- Understanding the **query optimizer** helps you write efficient SQL
- As a data engineer, you'll work with both paradigms

## Practice Exercises

1. **Explore the schema**: Run `SELECT * FROM INFORMATION_SCHEMA.TABLES` to see all tables
2. **Count rows**: Find out how many rows are in each table
3. **Identify relationships**: Which tables have foreign keys to Orders?

## What's Next?

- [Database Setup](02-database-setup.md) - Get Northwind running
- [SQL Execution Order](03-sql-execution-order.md) - How queries are processed

---

[← Back to Course Home](../README.md) | [Next: Database Setup →](02-database-setup.md)
