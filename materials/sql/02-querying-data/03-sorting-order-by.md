# Sorting with ORDER BY

## Overview

The `ORDER BY` clause sorts query results. It's executed near the end of query processing (after SELECT), so it can reference column aliases. While powerful, sorting can be expensive on large datasets.

## Core Concepts

### Basic ORDER BY Syntax

```sql
SELECT columns
FROM table
WHERE condition
ORDER BY column1 [ASC|DESC], column2 [ASC|DESC];
```

- **ASC** - Ascending (default, lowest to highest)
- **DESC** - Descending (highest to lowest)

### Example 1: Single Column Sort

```sql
-- Products sorted by price (low to high)
SELECT ProductName, UnitPrice
FROM Products
ORDER BY UnitPrice ASC;

-- ASC is default, so this is equivalent:
SELECT ProductName, UnitPrice
FROM Products
ORDER BY UnitPrice;
```

```sql
-- Products sorted by price (high to low)
SELECT ProductName, UnitPrice
FROM Products
ORDER BY UnitPrice DESC;
```

### Example 2: Multiple Column Sort

Sort by multiple columns with different directions:

```sql
-- Sort by category, then by price within each category
SELECT CategoryID, ProductName, UnitPrice
FROM Products
ORDER BY CategoryID ASC, UnitPrice DESC;
```

**Sorting logic:**
1. Primary sort: CategoryID ascending (1, 1, 1, 2, 2, 2, ...)
2. Within each category: UnitPrice descending (most expensive first)

### Example 3: Sorting by Column Aliases

Since ORDER BY executes after SELECT, aliases are available:

```sql
-- Calculate total value and sort by it
SELECT 
    ProductName,
    UnitPrice,
    UnitsInStock,
    UnitPrice * UnitsInStock AS InventoryValue
FROM Products
ORDER BY InventoryValue DESC;  -- Alias works here!
```

### Example 4: Sorting by Column Position

You can reference columns by their position (1-indexed):

```sql
SELECT ProductName, UnitPrice, UnitsInStock
FROM Products
ORDER BY 2 DESC, 3 ASC;  -- Position 2 = UnitPrice, Position 3 = UnitsInStock
```

**⚠️ Warning:** Avoid this in production code - it's fragile (breaks if you reorder SELECT columns).

### Example 5: Sorting by Computed Expressions

```sql
-- Sort by total line value
SELECT 
    OrderID,
    ProductID,
    UnitPrice,
    Quantity,
    Discount
FROM [Order Details]
ORDER BY UnitPrice * Quantity * (1 - Discount) DESC;
```

### Example 6: NULL Handling in Sorting

By default in SQL Server, `NULL` sorts **first** in ascending order:

```sql
-- Region with NULLs will appear first
SELECT CustomerID, CompanyName, Region
FROM Customers
ORDER BY Region;
```

**SQL Standard** (not SQL Server) supports `NULLS FIRST`/`NULLS LAST`:

```sql
-- Standard SQL (works in PostgreSQL, Oracle):
ORDER BY Region NULLS LAST;
```

**T-SQL workaround** to put NULLs last:

```sql
-- Use CASE to push NULLs to the end
SELECT CustomerID, CompanyName, Region
FROM Customers
ORDER BY 
    CASE WHEN Region IS NULL THEN 1 ELSE 0 END,  -- NULLs sort last
    Region;
```

## Advanced Insights

### Sorting Performance Costs

Sorting is **expensive** for large datasets:

**Complexity:**
- **O(n log n)** for most sort algorithms
- Requires memory for sorting buffers
- May spill to tempdb if data doesn't fit in memory

**Execution plan operators:**
- **Sort** - Explicit sort operation (expensive!)
- **Top N Sort** - Optimized for TOP/LIMIT (only maintains N rows)

```sql
-- Full sort: Must process all 830 rows, then sort
SELECT OrderID, OrderDate, Freight
FROM Orders
ORDER BY Freight DESC;

-- Top N sort: Only maintains top 10 during scan
SELECT TOP 10 OrderID, OrderDate, Freight
FROM Orders
ORDER BY Freight DESC;
```

**TOP N sort is much more efficient** - O(n log k) where k = 10.

### Avoiding Sorts with Indexes

If an index exists on the sort columns, the database can read data **in sorted order** without an explicit sort operation:

```sql
-- Assuming index on OrderDate:
SELECT OrderID, OrderDate
FROM Orders
ORDER BY OrderDate;  -- No sort operator needed! Just scan index.
```

**Index scan vs Sort:**
- **Index scan:** O(n) - Sequential read
- **Explicit sort:** O(n log n) - Much slower

**Clustered index:** Physical row order matches index order - even better!

### Multi-Column Sort Optimization

Multi-column sorts need multi-column indexes:

```sql
-- To avoid sort, need index on (CategoryID, UnitPrice)
SELECT ProductName, CategoryID, UnitPrice
FROM Products
ORDER BY CategoryID, UnitPrice DESC;
```

Index must match:
- Same column order
- Same sort direction (or index can be read backward)

### Collations and String Sorting

String sorting depends on **collation** (locale, case sensitivity):

```sql
-- Default collation (case-insensitive in most SQL Server installations)
ORDER BY ProductName;  -- 'Apple' = 'apple'

-- Case-sensitive sort
ORDER BY ProductName COLLATE SQL_Latin1_General_CP1_CS_AS;  -- 'Apple' < 'apple'
```

**International sorting:**

```sql
-- English sort order
ORDER BY ProductName COLLATE Latin1_General_CI_AS;

-- Swedish sort order (ö, ä, å at end of alphabet)
ORDER BY ProductName COLLATE Finnish_Swedish_CI_AS;
```

## Big Data Context

### Distributed Sorting - The Shuffle Problem

In distributed systems (Spark, Presto), sorting requires a **shuffle**:

```sql
-- Data is partitioned across 100 nodes
SELECT * FROM huge_table ORDER BY timestamp;
```

**What happens:**
1. **Local sort** on each node (100 sorts in parallel)
2. **Shuffle** - Redistribute data so each node gets a range
   - Node 1: timestamps 0-999
   - Node 2: timestamps 1000-1999
   - etc.
3. **Final sort** on each node
4. **Concatenate** results

**Shuffle is expensive:**
- Network I/O (terabytes transferred)
- Disk spill if data doesn't fit in memory
- Serialization/deserialization overhead

**Cost:** Sorting 1TB across 100 nodes might transfer **1TB across network** and take **10-30 minutes**.

### Avoiding Unnecessary Sorts

**Question:** Do you really need sorted data?

```sql
-- If you're aggregating, sorting is wasted:
SELECT Category, COUNT(*)
FROM products
ORDER BY Category  -- Unnecessary! GROUP BY already groups
GROUP BY Category;

-- Just remove ORDER BY
SELECT Category, COUNT(*)
FROM products
GROUP BY Category;
```

**Rule of thumb:** Only sort if:
1. User will see the data (reports, UI)
2. Downstream process requires sorted data
3. You need TOP N rows

### Partial Sorting and Sampling

For exploratory analysis, consider sampling instead of sorting:

```sql
-- Instead of sorting billions of rows for top 100:
SELECT TOP 100 * FROM huge_table ORDER BY value DESC;  -- Expensive!

-- Consider approximate top N or sampling:
SELECT TOP 100 * FROM huge_table TABLESAMPLE (1 PERCENT) ORDER BY value DESC;
```

In data lakes, use **approximate algorithms**:
- Top-K heavy hitters (Count-Min Sketch)
- Percentiles (t-Digest)
- Sampling-based approaches

### Presorted Data and Partitioning

If data is already sorted (e.g., time-series data ingested in order), preserve that order:

```sql
-- Data lake partitioned and sorted by date
/events/year=2024/month=01/day=01/part-00000.parquet (sorted by timestamp)
/events/year=2024/month=01/day=02/part-00000.parquet (sorted by timestamp)
```

```sql
-- This query can avoid shuffle if engine is smart!
SELECT * FROM events 
WHERE date = '2024-01-01'
ORDER BY timestamp;  -- Data is already sorted!
```

## Practical Examples

### Example 1: Customer Ranking by Orders

```sql
-- Top 10 customers by order count
SELECT TOP 10
    c.CustomerID,
    c.CompanyName,
    COUNT(o.OrderID) AS OrderCount
FROM Customers c
    LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
GROUP BY c.CustomerID, c.CompanyName
ORDER BY OrderCount DESC;
```

### Example 2: Product Price Analysis

```sql
-- Most and least expensive products by category
SELECT 
    CategoryID,
    ProductName,
    UnitPrice
FROM Products
WHERE Discontinued = 0
ORDER BY CategoryID, UnitPrice DESC;
```

### Example 3: Recent Orders

```sql
-- Last 20 orders with customer info
SELECT TOP 20
    o.OrderID,
    o.OrderDate,
    c.CompanyName,
    o.Freight
FROM Orders o
    INNER JOIN Customers c ON o.CustomerID = c.CustomerID
ORDER BY o.OrderDate DESC, o.OrderID DESC;
```

### Example 4: Alphabetical Product List with NULL Handling

```sql
-- Products alphabetically, NULLs in QuantityPerUnit last
SELECT 
    ProductName,
    QuantityPerUnit
FROM Products
ORDER BY 
    CASE WHEN QuantityPerUnit IS NULL THEN 1 ELSE 0 END,
    QuantityPerUnit,
    ProductName;
```

### Example 5: Complex Multi-Column Sort

```sql
-- Orders by country, then by freight (expensive first), then by date
SELECT 
    OrderID,
    ShipCountry,
    Freight,
    OrderDate
FROM Orders
ORDER BY 
    ShipCountry ASC,
    Freight DESC,
    OrderDate DESC;
```

## Practice Exercises

1. List all employees by hire date (most recent first)
2. Find the 5 most expensive products
3. Show customers sorted by country, then city, then company name
4. List orders sorted by order date, but with NULL ship dates appearing last
5. Get top 10 order details by line item value (quantity × price × (1 - discount))

### Solutions

```sql
-- Exercise 1
SELECT EmployeeID, FirstName, LastName, HireDate
FROM Employees
ORDER BY HireDate DESC;

-- Exercise 2
SELECT TOP 5 ProductName, UnitPrice
FROM Products
ORDER BY UnitPrice DESC;

-- Exercise 3
SELECT CustomerID, CompanyName, City, Country
FROM Customers
ORDER BY Country, City, CompanyName;

-- Exercise 4
SELECT OrderID, OrderDate, ShippedDate
FROM Orders
ORDER BY 
    OrderDate,
    CASE WHEN ShippedDate IS NULL THEN 1 ELSE 0 END,
    ShippedDate;

-- Exercise 5
SELECT TOP 10
    OrderID,
    ProductID,
    UnitPrice,
    Quantity,
    Discount,
    UnitPrice * Quantity * (1 - Discount) AS LineTotal
FROM [Order Details]
ORDER BY LineTotal DESC;
```

## Key Takeaways

- `ORDER BY` sorts results (executed after SELECT, so aliases work)
- **ASC** (default) = ascending, **DESC** = descending
- Multi-column sorts: primary sort first, then secondary within groups
- **NULL** sorts first by default in SQL Server (use CASE for NULLS LAST)
- Sorting is **expensive** - O(n log n), may spill to disk
- **Indexes** can eliminate sort operations entirely
- Use **TOP N** when possible - much more efficient than full sort
- In distributed systems, sorting requires expensive **shuffles**
- Consider if sorting is necessary - avoid for intermediate results
- Presorted data in data lakes can avoid shuffle costs

## What's Next?

Now that you can select, filter, and sort single tables, let's learn how to combine multiple tables:

[Next: Module 03 - Joining Tables →](../03-joining-tables/01-join-theory.md)

---

[← Back: Filtering with WHERE](02-filtering-where.md) | [Course Home](../README.md) | [Next: Join Theory →](../03-joining-tables/01-join-theory.md)
