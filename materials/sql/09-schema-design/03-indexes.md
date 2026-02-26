# Indexes

## Overview

Indexes speed up data retrieval but slow down writes. Understanding when and how to use them is critical for performance.

## Index Types

> **Core Concept:** See [Trees for Storage](../../core-concepts/02-data-structures/02-trees-for-storage.md) for how B-trees and B+ trees work -- node structure, why they're optimized for disk I/O, and the clustered vs non-clustered distinction. SQL databases use B-trees for indexes because they need sorted access for range scans and ORDER BY.

### Clustered Index

Physical order of data. **One per table**. In B-tree terms: this is a B+ tree where the leaf nodes *are* the data rows, stored in key order. A lookup by the clustered key is a single tree traversal that lands directly on the row data.

```sql
-- Usually on primary key
CREATE CLUSTERED INDEX IX_Products_ProductID
ON Products(ProductID);
```

**How it works:**
- Data sorted by index key (B+ tree leaf order = physical storage order)
- Fast range scans (leaf nodes linked for sequential traversal)
- Slow inserts (must maintain sort order; may split B-tree pages)

### Nonclustered Index

Separate B-tree structure pointing to data. **Multiple per table**. The leaf nodes contain the index key plus a pointer (row ID or the clustered key) to the actual data row.

```sql
CREATE NONCLUSTERED INDEX IX_Products_CategoryID
ON Products(CategoryID);
```

**How it works:**
- Index B-tree stores key + pointer (RID or clustered key)
- Lookup: traverse the non-clustered B-tree (O(log n)) → then follow pointer to fetch the full row (an additional random I/O)
- Can be avoided with a **covering index** (INCLUDE columns) -- the index leaf contains all needed columns, eliminating the row lookup

## CREATE INDEX

```sql
-- Simple index
CREATE INDEX IX_Customers_Country
ON Customers(Country);

-- Composite index (multiple columns)
CREATE INDEX IX_Orders_CustomerDate
ON Orders(CustomerID, OrderDate);

-- Unique index
CREATE UNIQUE INDEX IX_Employees_Email
ON Employees(Email);
```

## Covering Indexes (INCLUDE)

Index contains all needed columns - no table lookup needed.

```sql
CREATE INDEX IX_Products_CategoryID
ON Products(CategoryID)
INCLUDE (ProductName, UnitPrice);

-- This query uses only the index:
SELECT ProductName, UnitPrice
FROM Products
WHERE CategoryID = 1;
```

**Benefit:** Much faster (no table lookup).

## Filtered Indexes

Index subset of rows.

```sql
-- Index only active products
CREATE INDEX IX_Products_Active
ON Products(CategoryID)
WHERE Discontinued = 0;
```

**Benefit:** Smaller index, faster queries on subset.

## DROP INDEX

```sql
DROP INDEX IX_Products_CategoryID ON Products;
```

## Index Usage Example

**Without index:**

```sql
-- Table scan: reads all 830 rows
SELECT * FROM Orders WHERE CustomerID = 'ALFKI';
```

**With index:**

```sql
CREATE INDEX IX_Orders_CustomerID ON Orders(CustomerID);

-- Index seek: reads ~6 rows directly
SELECT * FROM Orders WHERE CustomerID = 'ALFKI';
```

**Performance:** 100x faster on large tables.

## When to Create Indexes

**Good candidates:**
- Columns in WHERE clauses
- Columns in JOIN conditions
- Columns in ORDER BY
- Foreign keys
- Columns used in GROUP BY

**Bad candidates:**
- Small tables (< 1000 rows)
- Columns with low cardinality (few distinct values like BIT)
- Frequently updated columns
- Very wide columns

## Index Maintenance

Indexes fragment over time.

```sql
-- Rebuild index (offline, fast)
ALTER INDEX IX_Products_CategoryID ON Products REBUILD;

-- Reorganize (online, slower)
ALTER INDEX IX_Products_CategoryID ON Products REORGANIZE;

-- Rebuild all indexes on table
ALTER INDEX ALL ON Products REBUILD;
```

## Viewing Indexes

```sql
-- Show indexes on table
EXEC sp_helpindex 'Products';

-- Query system views
SELECT 
    i.name AS IndexName,
    i.type_desc AS IndexType,
    COL_NAME(ic.object_id, ic.column_id) AS ColumnName
FROM sys.indexes i
    INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
WHERE i.object_id = OBJECT_ID('Products');
```

## Execution Plans

View how SQL Server uses indexes:

```sql
-- Show actual execution plan
SET STATISTICS IO ON;
SET STATISTICS TIME ON;

SELECT * FROM Products WHERE CategoryID = 1;

-- Check plan:
-- - Index Seek = Good (uses index)
-- - Index Scan = OK (reads whole index)
-- - Table Scan = Bad (reads whole table, no index)
```

Press `Ctrl+L` in SSMS/Azure Data Studio to see graphical plan.

## Practical Examples

### Optimize JOIN

```sql
-- Create indexes on join columns
CREATE INDEX IX_OrderDetails_OrderID ON [Order Details](OrderID);
CREATE INDEX IX_OrderDetails_ProductID ON [Order Details](ProductID);

-- Now this is fast:
SELECT o.OrderID, p.ProductName
FROM Orders o
    INNER JOIN [Order Details] od ON o.OrderID = od.OrderID
    INNER JOIN Products p ON od.ProductID = p.ProductID;
```

### Optimize WHERE + ORDER BY

```sql
-- Index matches query pattern
CREATE INDEX IX_Orders_Customer_Date
ON Orders(CustomerID, OrderDate DESC);

-- Uses index efficiently:
SELECT OrderID, OrderDate
FROM Orders
WHERE CustomerID = 'ALFKI'
ORDER BY OrderDate DESC;
```

### Covering Index for Report

```sql
-- Report query
SELECT ProductName, UnitPrice, UnitsInStock
FROM Products
WHERE CategoryID = 1
ORDER BY ProductName;

-- Covering index (no table lookup needed)
CREATE INDEX IX_Products_Category_Report
ON Products(CategoryID, ProductName)
INCLUDE (UnitPrice, UnitsInStock);
```

## Big Data Context

> **Core Concept:** See [Partitioning Strategies](../../core-concepts/03-scaling/02-partitioning-strategies.md) for range vs hash partitioning, hot spots, and rebalancing at the distributed level. See [Probabilistic Structures](../../core-concepts/02-data-structures/04-probabilistic-structures.md) for how bloom filters provide fast existence checks without scanning data.

**Traditional databases:** B-tree indexes (random I/O per write, O(log n) per read)

**Data lakes/warehouses:**
- **No B-tree indexes** in Parquet/ORC files -- B-trees require mutable in-place updates, which is incompatible with immutable file formats
- Instead: **Partitioning** (coarse-grained routing to file subsets), **clustering/sorting** (data order within files), **zone maps** (min/max statistics stored in file metadata -- enables skipping entire files when the predicate is outside the min/max range)
- **Bloom filters** per column per row group -- existence checks without reading data

**Example:**

```sql
-- Partitioning = coarse-grained "index" -- prunes which files to read
CREATE TABLE sales (
    sale_id BIGINT,
    amount DECIMAL,
    sale_date DATE
)
PARTITIONED BY (year INT, month INT)
CLUSTERED BY (customer_id) INTO 100 BUCKETS;

-- Query prunes partitions (like index seek, but at file granularity)
SELECT * FROM sales WHERE year = 2024 AND month = 1;
-- Only reads files in year=2024/month=1 partition -- all other files skipped
```

**Columnar benefits:**
- Reads only needed columns (see [I/O and Storage Fundamentals](../../core-concepts/01-complexity-and-performance/02-io-and-storage-fundamentals.md))
- Compression reduces I/O (similar values in sequence compress well)
- Predicate pushdown skips row groups (zone map says min > predicate → skip the whole row group)

## Index Trade-offs

| Aspect | Benefit | Cost |
|--------|---------|------|
| **Reads** | Much faster | |
| **Writes** | | Slower (maintain index) |
| **Storage** | | Extra disk space |
| **Maintenance** | | Fragmentation, rebuild needed |

**Rule of thumb:** Index if table > 1000 rows and query scans > 10% of table.

## Practice Exercises

```sql
-- 1. Create index on frequently queried column
CREATE INDEX IX_Orders_OrderDate ON Orders(OrderDate);

-- 2. Covering index for specific query
CREATE INDEX IX_Products_Category_Covering
ON Products(CategoryID)
INCLUDE (ProductName, UnitPrice);

-- 3. Filtered index for active products
CREATE INDEX IX_Products_Active
ON Products(UnitPrice)
WHERE Discontinued = 0;

-- 4. View indexes
EXEC sp_helpindex 'Products';
```

## Key Takeaways

- Indexes speed up reads, slow down writes
- **Clustered** = physical order (one per table)
- **Nonclustered** = separate structure (many per table)
- **Covering** indexes include all needed columns
- **Filtered** indexes for subsets
- Index JOIN, WHERE, ORDER BY columns
- In data lakes: use partitioning/clustering instead
- Monitor execution plans to verify index usage

## What's Next?

[Next: Module 10 - Big Data Context →](../10-big-data-context/01-oltp-vs-olap.md)

---

[← Back: ALTER TABLE](02-alter-table.md) | [Course Home](../README.md) | [Next: OLTP vs OLAP →](../10-big-data-context/01-oltp-vs-olap.md)
