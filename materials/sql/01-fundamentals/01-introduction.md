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

### What is Complexity?

Complexity analysis answers: "How does performance scale when data grows?"

- **O(1)** - Constant time: Same speed regardless of data size
- **O(log n)** - Logarithmic: Doubles data = adds one step (e.g., binary search)
- **O(n)** - Linear: Doubles data = doubles time (e.g., full table scan)
- **O(n log n)** - Log-linear: Efficient sorting algorithms
- **O(n²)** - Quadratic: Doubles data = 4x time (e.g., nested loops)
- **O(n³)** - Cubic: Doubles data = 8x time (e.g., triple nested loops)

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

### Python Code Examples

The same complexity concepts apply in programming languages:

```python
# O(1) - Dictionary/hash lookup
products = {42: "Chai", 43: "Coffee", 44: "Tea"}
product = products[42]  # Constant time, regardless of dict size

# O(log n) - Binary search on sorted list
import bisect
prices = [5.00, 10.00, 15.00, 18.00, 20.00, 25.00]  # sorted
index = bisect.bisect_left(prices, 18.00)  # log₂(6) ≈ 3 comparisons

# O(n) - Linear search through list
products = ["Chai", "Coffee", "Tea", "Sugar", "Salt"]
for product in products:
    if "soup" in product.lower():  # Must check every item
        print(product)

# O(n log n) - Efficient sorting
prices = [25.00, 10.00, 18.00, 5.00, 20.00]
sorted_prices = sorted(prices)  # Python's Timsort algorithm

# O(n²) - Nested loops (Cartesian product)
orders = list(range(830))      # 830 orders
customers = list(range(91))    # 91 customers
matches = []
for order_id in orders:
    for customer_id in customers:
        if order_id % 91 == customer_id:  # 830 × 91 = 75,530 checks
            matches.append((order_id, customer_id))

# O(n³) - Triple nested loop
categories = list(range(8))
suppliers = list(range(29))
products = list(range(77))
for cat in categories:
    for sup in suppliers:
        for prod in products:
            # 8 × 29 × 77 = 17,864 iterations
            pass
```

### Why It Matters in SQL

Understanding complexity helps you:

1. **Predict performance** - Will this query scale to millions of rows?
2. **Choose indexes** - Turn O(n) scans into O(log n) seeks
3. **Optimize joins** - O(n log n) hash join vs O(n²) nested loop
4. **Design schemas** - Denormalization trades space for O(1) lookups

**Rule of thumb**: If you see O(n²) or worse in production queries, investigate immediately. It's often fixable with indexes or query rewrites.

### Shuffling and Batching in Big Data

When working with distributed systems (like Spark, Hadoop, or distributed databases), two key concepts affect performance:

**Shuffling** - Moving data between nodes in a cluster. This happens when you need to reorganize data (e.g., during JOINs or GROUP BY operations). Shuffling is expensive because it involves network I/O and disk writes. Minimizing shuffles is crucial for performance.

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
