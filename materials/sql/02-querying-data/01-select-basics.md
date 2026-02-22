# SELECT Basics

## Overview

The `SELECT` statement is the foundation of SQL querying. It retrieves data from tables and allows you to choose which columns to display, compute new values, and eliminate duplicates.

## Core Concepts

### Basic SELECT Syntax

```sql
SELECT column1, column2, ...
FROM table_name;
```

### Example 1: Select Specific Columns

```sql
-- Get product names and prices
SELECT ProductName, UnitPrice
FROM Products;
```

**Result:** 77 rows with 2 columns

### Example 2: Select All Columns

```sql
-- Get all product information
SELECT *
FROM Products;
```

**Result:** 77 rows with all columns (ProductID, ProductName, SupplierID, CategoryID, etc.)

⚠️ **Warning:** `SELECT *` is convenient but has drawbacks (see Advanced Insights below).

### Example 3: Column Aliases

Use `AS` to give columns more readable names:

```sql
-- Rename columns in output
SELECT 
    ProductName AS Name,
    UnitPrice AS Price,
    UnitsInStock AS Stock
FROM Products;
```

The `AS` keyword is optional in SQL Server:

```sql
-- Also valid (AS is implicit)
SELECT 
    ProductName Name,
    UnitPrice Price,
    UnitsInStock Stock
FROM Products;
```

**Best Practice:** Always use `AS` for clarity.

### Example 4: Computed Columns

Create new columns from expressions:

```sql
-- Calculate inventory value
SELECT 
    ProductName,
    UnitPrice,
    UnitsInStock,
    UnitPrice * UnitsInStock AS InventoryValue
FROM Products;
```

### Example 5: String Concatenation

Combine columns into one:

```sql
-- Full product description
SELECT 
    ProductName + ' (' + QuantityPerUnit + ')' AS ProductDescription,
    UnitPrice
FROM Products;
```

**T-SQL tip:** Use `CONCAT()` to handle NULLs automatically:

```sql
SELECT 
    CONCAT(ProductName, ' (', QuantityPerUnit, ')') AS ProductDescription,
    UnitPrice
FROM Products;
```

### Example 6: DISTINCT - Eliminating Duplicates

Get unique values:

```sql
-- How many different cities do customers live in?
SELECT DISTINCT City
FROM Customers;
```

**Result:** 69 unique cities (instead of 91 rows)

```sql
-- Multiple columns: unique combinations
SELECT DISTINCT City, Country
FROM Customers
ORDER BY Country, City;
```

**Result:** 69 rows (some cities appear in multiple countries)

## Advanced Insights

### SELECT * - Why You Should Avoid It

`SELECT *` is tempting but problematic:

1. **Unclear intent** - What columns do you actually need?
2. **Breaks code** - If table schema changes, queries break
3. **Performance overhead** - Reads unnecessary columns
4. **Network waste** - Transfers extra data

**Impact in large tables:**

```sql
-- BAD: Fetches ALL columns including BLOBs
SELECT * FROM Products;  -- Includes Photo column (image data)

-- GOOD: Only fetch what you need
SELECT ProductID, ProductName, UnitPrice FROM Products;
```

### Column-Oriented Storage and SELECT *

> **Core Concept:** See [I/O and Storage Fundamentals](../../core-concepts/01-complexity-and-performance/02-io-and-storage-fundamentals.md) for how row-oriented vs column-oriented storage works at the I/O level and why column selection matters for read performance.

In **columnar databases** (Parquet, ORC, columnar indexes), the cost of `SELECT *` is extreme:

```sql
-- Row-oriented (traditional OLTP):
-- Reads entire rows sequentially, SELECT * only slightly slower

-- Column-oriented (OLAP):
-- Each column is stored separately
-- SELECT * requires reading ALL columns from different locations
-- Massive I/O overhead vs selecting 2-3 columns
```

**Example:** In a table with 100 columns:
- `SELECT col1, col2` - Reads 2 column files
- `SELECT *` - Reads 100 column files (50x more I/O!)

Columnar storage is why `SELECT *` is expensive in data lakes -- it reads every column file. This is the I/O trade-off from core-concepts applied to query design: SQL's declarative model means you *can* ask for all columns, but the physical cost of doing so in column-oriented storage is 50x higher than being explicit.

This is why data warehouse best practices emphasize explicit column selection.

### Expression Evaluation Order

Computed columns are evaluated in the SELECT phase:

```sql
SELECT 
    ProductName,
    UnitPrice,
    UnitPrice * 1.2 AS PriceWithTax,
    PriceWithTax * 0.1 AS Tax  -- ❌ Error! Alias not available yet
FROM Products;
```

Each expression is independent - you can't reference aliases within SELECT.

**Workaround:**

```sql
-- Option 1: Repeat the expression
SELECT 
    ProductName,
    UnitPrice,
    UnitPrice * 1.2 AS PriceWithTax,
    (UnitPrice * 1.2) * 0.1 AS Tax
FROM Products;

-- Option 2: Use a subquery or CTE (covered later)
```

### NULL Handling in Expressions

`NULL` propagates through expressions:

```sql
-- If UnitsOnOrder is NULL, result is NULL
SELECT 
    ProductName,
    UnitsInStock,
    UnitsOnOrder,
    UnitsInStock + UnitsOnOrder AS TotalUnits  -- NULL if either is NULL
FROM Products;
```

Use `COALESCE()` to substitute defaults:

```sql
SELECT 
    ProductName,
    UnitsInStock,
    UnitsOnOrder,
    UnitsInStock + COALESCE(UnitsOnOrder, 0) AS TotalUnits
FROM Products;
```

### DISTINCT Performance Implications

`DISTINCT` requires sorting or hashing to identify duplicates:

```sql
-- Requires a SORT or HASH operation
SELECT DISTINCT Country FROM Customers;
```

**Performance characteristics:**
- **Sort-based:** O(n log n), uses tempdb if large
- **Hash-based:** O(n), uses memory (can spill to disk)

**In big data:**
- Distributed `DISTINCT` requires a **shuffle** (expensive!)
- All data with the same value must go to the same node
- Consider approximate alternatives for very large datasets (HyperLogLog)

## Big Data Context

### Projection Pushdown

When querying data lakes (Parquet, ORC), the query engine only reads selected columns:

```sql
-- Only reads ProductName and UnitPrice columns from Parquet
SELECT ProductName, UnitPrice
FROM products_parquet_table;
```

This is called **projection pushdown** - the storage layer skips irrelevant columns entirely.

**Impact:**
- 100-column table, SELECT 2 columns = 98% I/O savings
- Critical for cost in cloud data warehouses (BigQuery, Snowflake charge by bytes scanned)

### Schema Evolution

In data lakes with schema evolution, `SELECT *` can be dangerous:

```sql
-- Schema v1: (id, name, price)
-- Schema v2: (id, name, price, discount, tax)

-- SELECT * returns different columns depending on file version
-- Explicit column selection prevents breakage
SELECT id, name, price FROM products;  -- Always returns 3 columns
```

## Practical Examples

### Example 1: Product Catalog

```sql
-- Create a simple product listing
SELECT 
    ProductID AS ID,
    ProductName AS [Product Name],  -- Spaces require brackets
    UnitPrice AS Price,
    UnitsInStock AS [In Stock]
FROM Products
WHERE Discontinued = 0;
```

### Example 2: Price Analysis

```sql
-- Show price statistics
SELECT 
    ProductName,
    UnitPrice AS CurrentPrice,
    UnitPrice * 0.9 AS [10% Discount],
    UnitPrice * 1.2 AS [With 20% Markup],
    CASE 
        WHEN UnitPrice < 20 THEN 'Budget'
        WHEN UnitPrice < 50 THEN 'Standard'
        ELSE 'Premium'
    END AS PriceCategory
FROM Products;
```

### Example 3: Contact Directory

```sql
-- Create customer contact list
SELECT DISTINCT
    ContactName + ' - ' + CompanyName AS Contact,
    Phone,
    City + ', ' + Country AS Location
FROM Customers
WHERE Phone IS NOT NULL
ORDER BY Country, City;
```

## Practice Exercises

1. **Basic Selection:** Select just the CategoryName and Description from Categories
2. **Computed Column:** Show each order's CustomerID and total value (sum of Freight)
3. **String Manipulation:** Create a full name column for Employees (FirstName + LastName)
4. **Distinct Values:** How many different countries have suppliers?
5. **NULL Handling:** Calculate total units (InStock + OnOrder), treating NULL as 0

### Solutions

```sql
-- Exercise 1
SELECT CategoryName, Description
FROM Categories;

-- Exercise 2
SELECT 
    CustomerID,
    SUM(Freight) AS TotalFreight
FROM Orders
GROUP BY CustomerID;

-- Exercise 3
SELECT 
    FirstName + ' ' + LastName AS FullName,
    Title
FROM Employees;

-- Exercise 4
SELECT COUNT(DISTINCT Country) AS UniqueCountries
FROM Suppliers;

-- Exercise 5
SELECT 
    ProductName,
    UnitsInStock,
    UnitsOnOrder,
    UnitsInStock + COALESCE(UnitsOnOrder, 0) AS TotalUnits
FROM Products;
```

## Key Takeaways

- `SELECT` specifies which columns to retrieve
- Use explicit column names instead of `SELECT *` for performance
- `AS` creates column aliases (improves readability)
- Expressions create computed columns
- `DISTINCT` eliminates duplicate rows (has performance cost)
- `NULL` propagates through expressions - use `COALESCE()` to handle
- In columnar storage, selecting fewer columns = massive performance gains
- Projection pushdown is critical for data lake query performance

## What's Next?

Now that you can select columns, let's learn how to filter rows:

[Next: Filtering with WHERE →](02-filtering-where.md)

---

[← Back: SQL Execution Order](../01-fundamentals/03-sql-execution-order.md) | [Course Home](../README.md) | [Next: Filtering with WHERE →](02-filtering-where.md)
