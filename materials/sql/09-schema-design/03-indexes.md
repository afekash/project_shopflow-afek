# Indexes

## Overview

Indexes speed up data retrieval but slow down writes. Understanding when and how to use them is critical for performance.

## Index Types

### Clustered Index

Physical order of data. **One per table**.

```sql
-- Usually on primary key
CREATE CLUSTERED INDEX IX_Products_ProductID
ON Products(ProductID);
```

**How it works:**
- Data sorted by index key
- Fast range scans
- Slow inserts (must maintain order)

### Nonclustered Index

Separate structure pointing to data. **Multiple per table**.

```sql
CREATE NONCLUSTERED INDEX IX_Products_CategoryID
ON Products(CategoryID);
```

**How it works:**
- Index stores key + pointer (RID or clustered key)
- Requires lookup to get full row (unless covering)

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

**Traditional databases:** B-tree indexes

**Data lakes/warehouses:**
- **No indexes** in Parquet/ORC files
- Instead: **Partitioning, clustering, sorting**
- **Zone maps** (min/max statistics per file)
- **Bloom filters** for existence checks

**Example:**

```sql
-- Partitioning = coarse-grained "index"
CREATE TABLE sales (
    sale_id BIGINT,
    amount DECIMAL,
    sale_date DATE
)
PARTITIONED BY (year INT, month INT)
CLUSTERED BY (customer_id) INTO 100 BUCKETS;

-- Query prunes partitions (like index)
SELECT * FROM sales WHERE year = 2024 AND month = 1;
-- Only reads files in year=2024/month=1 partition
```

**Columnar benefits:**
- Reads only needed columns
- Compression reduces I/O
- Predicate pushdown skips row groups

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
