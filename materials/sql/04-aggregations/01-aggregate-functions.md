# Aggregate Functions

## Overview

Aggregate functions perform calculations across multiple rows and return a single value. Essential for reporting and analytics.

## Core Functions

### COUNT

Counts rows or non-NULL values.

```sql
-- Count all rows (including NULLs)
SELECT COUNT(*) AS TotalProducts FROM Products;
-- Result: 77

-- Count non-NULL values
SELECT COUNT(Region) AS CustomersWithRegion FROM Customers;
-- Result: 31 (60 customers have NULL region)

-- Count distinct values
SELECT COUNT(DISTINCT Country) AS UniqueCountries FROM Customers;
-- Result: 21
```

**Important:** `COUNT(*)` counts rows, `COUNT(column)` ignores NULLs.

### SUM

Adds numeric values.

```sql
-- Total freight cost
SELECT SUM(Freight) AS TotalFreight FROM Orders;
-- Result: ~64,942

-- Total inventory value
SELECT SUM(UnitPrice * UnitsInStock) AS InventoryValue FROM Products;

-- SUM ignores NULLs
SELECT SUM(UnitsOnOrder) FROM Products;
-- NULLs treated as 0
```

### AVG

Average of numeric values (ignores NULLs).

```sql
-- Average product price
SELECT AVG(UnitPrice) AS AvgPrice FROM Products;
-- Result: ~28.87

-- Average with NULLS handled
SELECT 
    AVG(Region) AS AvgWithNulls,  -- Wrong! Can't average strings
    AVG(CAST(Region AS INT)) -- If Region were numeric
FROM Customers;
```

**Note:** `AVG` skips NULLs. `AVG(col)` ≠ `SUM(col) / COUNT(*)` if NULLs exist.

### MIN and MAX

```sql
-- Price range
SELECT 
    MIN(UnitPrice) AS CheapestProduct,
    MAX(UnitPrice) AS MostExpensive
FROM Products;
-- Result: 2.50, 263.50

-- Date range
SELECT 
    MIN(OrderDate) AS FirstOrder,
    MAX(OrderDate) AS LastOrder
FROM Orders;
-- Result: 1996-07-04, 1998-05-06
```

Works on any comparable type (numbers, dates, strings).

## Combining Aggregates

```sql
-- Multiple aggregates in one query
SELECT 
    COUNT(*) AS ProductCount,
    AVG(UnitPrice) AS AvgPrice,
    MIN(UnitPrice) AS MinPrice,
    MAX(UnitPrice) AS MaxPrice,
    SUM(UnitsInStock) AS TotalStock
FROM Products;
```

## NULL Handling

```sql
-- Total vs Average with NULLs
SELECT 
    COUNT(*) AS TotalProducts,           -- 77
    COUNT(UnitsOnOrder) AS NonNullCount, -- 75 (2 NULLs)
    SUM(UnitsOnOrder) AS TotalOnOrder,   -- 780
    AVG(UnitsOnOrder) AS AvgOnOrder      -- 10.4 (780/75, not 780/77!)
FROM Products;
```

**Key:** Aggregates ignore NULLs except `COUNT(*)`.

## Advanced Insights

### String Aggregation

```sql
-- Combine multiple rows into one string (SQL Server 2017+)
SELECT STRING_AGG(ProductName, ', ') AS AllProducts
FROM Products
WHERE CategoryID = 1;
-- Result: "Chai, Chang, Guaraná Fantástica, ..."

-- With ordering
SELECT STRING_AGG(ProductName, ', ') WITHIN GROUP (ORDER BY ProductName)
FROM Products;
```

### Statistical Functions

```sql
-- Standard deviation and variance
SELECT 
    STDEV(UnitPrice) AS PriceStdDev,
    VAR(UnitPrice) AS PriceVariance
FROM Products;
```

## Big Data Context

**Pre-aggregation** is critical in data warehouses:

```sql
-- Instead of aggregating billions of rows every query:
SELECT SUM(Revenue) FROM FactSales WHERE Year = 2024;

-- Pre-aggregate into summary tables:
CREATE TABLE AggSalesByYear (
    Year INT,
    TotalRevenue DECIMAL,
    OrderCount BIGINT
);

-- Refresh daily
-- Query: instant!
SELECT TotalRevenue FROM AggSalesByYear WHERE Year = 2024;
```

**Approximate aggregations** for massive scale (HyperLogLog for COUNT DISTINCT, t-Digest for percentiles).

## Practice Exercises

```sql
-- 1. How many orders were placed?
SELECT COUNT(*) FROM Orders;

-- 2. Average freight cost
SELECT AVG(Freight) FROM Orders;

-- 3. Total quantity sold across all orders
SELECT SUM(Quantity) FROM [Order Details];

-- 4. Price range of products
SELECT MIN(UnitPrice), MAX(UnitPrice) FROM Products;

-- 5. How many unique customers placed orders?
SELECT COUNT(DISTINCT CustomerID) FROM Orders;
```

## Key Takeaways

- `COUNT(*)` counts rows, `COUNT(col)` counts non-NULLs
- `SUM`, `AVG`, `MIN`, `MAX` ignore NULLs
- `COUNT(DISTINCT col)` for unique values
- Combine multiple aggregates in one query
- Pre-aggregation critical for performance at scale

## What's Next?

[Next: GROUP BY and HAVING →](02-group-by-having.md)

---

[← Back: Normalization](../03-joining-tables/04-normalization-vs-denormalization.md) | [Course Home](../README.md) | [Next: GROUP BY →](02-group-by-having.md)
