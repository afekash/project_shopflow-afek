# Ranking Functions

## Overview

Ranking functions assign ranks to rows within partitions. Four main functions with different tie-handling behavior.

## ROW_NUMBER()

Unique sequential number, even for ties.

```sql
-- Rank products by price (unique ranks)
SELECT 
    ProductName,
    UnitPrice,
    ROW_NUMBER() OVER (ORDER BY UnitPrice DESC) AS RowNum
FROM Products;
```

**Ties:** Arbitrary ordering (use additional ORDER BY columns for deterministic results).

```sql
-- Deterministic tie-breaking
SELECT 
    ProductName,
    UnitPrice,
    ROW_NUMBER() OVER (ORDER BY UnitPrice DESC, ProductID) AS RowNum
FROM Products;
```

## RANK()

Same rank for ties, skips next ranks.

```sql
SELECT 
    ProductName,
    UnitPrice,
    RANK() OVER (ORDER BY UnitPrice DESC) AS Rank
FROM Products;
```

**Example:** If two products tie for rank 1, next product gets rank 3 (skips 2).

## DENSE_RANK()

Same rank for ties, no gaps.

```sql
SELECT 
    ProductName,
    UnitPrice,
    DENSE_RANK() OVER (ORDER BY UnitPrice DESC) AS DenseRank
FROM Products;
```

**Example:** Two products at rank 1, next product gets rank 2 (no skip).

## NTILE(n)

Divides rows into n buckets (quartiles, deciles, etc.).

```sql
-- Divide products into 4 price quartiles
SELECT 
    ProductName,
    UnitPrice,
    NTILE(4) OVER (ORDER BY UnitPrice) AS PriceQuartile
FROM Products;
```

**Result:** 
- Quartile 1: Cheapest 25%
- Quartile 4: Most expensive 25%

## Comparison

```sql
SELECT 
    ProductName,
    UnitPrice,
    ROW_NUMBER() OVER (ORDER BY UnitPrice DESC) AS RowNum,
    RANK() OVER (ORDER BY UnitPrice DESC) AS Rank,
    DENSE_RANK() OVER (ORDER BY UnitPrice DESC) AS DenseRank,
    NTILE(10) OVER (ORDER BY UnitPrice DESC) AS Decile
FROM Products
ORDER BY UnitPrice DESC;
```

| Price | ROW_NUMBER | RANK | DENSE_RANK |
|-------|------------|------|------------|
| 263.50 | 1 | 1 | 1 |
| 123.79 | 2 | 2 | 2 |
| 97.00 | 3 | 3 | 3 |
| 97.00 | 4 | 3 | 3 |
| 81.00 | 5 | 5 | 4 |

## Practical Uses

### Top N per Group

```sql
-- Top 3 most expensive products per category
WITH Ranked AS (
    SELECT 
        CategoryID,
        ProductName,
        UnitPrice,
        ROW_NUMBER() OVER (PARTITION BY CategoryID ORDER BY UnitPrice DESC) AS Rank
    FROM Products
)
SELECT CategoryID, ProductName, UnitPrice
FROM Ranked
WHERE Rank <= 3;
```

### Deduplication

```sql
-- Remove duplicate customer entries (keep most recent)
WITH Dupes AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY CustomerID ORDER BY LastModified DESC) AS RowNum
    FROM CustomerImport
)
DELETE FROM Dupes WHERE RowNum > 1;
```

### Price Segments

```sql
-- Segment products into price tiers
SELECT 
    ProductName,
    UnitPrice,
    CASE NTILE(3) OVER (ORDER BY UnitPrice)
        WHEN 1 THEN 'Budget'
        WHEN 2 THEN 'Standard'
        WHEN 3 THEN 'Premium'
    END AS PriceTier
FROM Products;
```

### Percentile Calculation

```sql
-- Find median priced product per category
WITH Ranked AS (
    SELECT 
        CategoryID,
        ProductName,
        UnitPrice,
        ROW_NUMBER() OVER (PARTITION BY CategoryID ORDER BY UnitPrice) AS RowNum,
        COUNT(*) OVER (PARTITION BY CategoryID) AS TotalCount
    FROM Products
)
SELECT CategoryID, ProductName, UnitPrice
FROM Ranked
WHERE RowNum = (TotalCount + 1) / 2;  -- Median
```

## Advanced Example: Running Rank

```sql
-- Customer ranking by total orders, showing rank changes over time
SELECT 
    o.CustomerID,
    o.OrderDate,
    COUNT(*) OVER (
        PARTITION BY o.CustomerID 
        ORDER BY o.OrderDate
    ) AS OrdersToDate,
    RANK() OVER (
        PARTITION BY o.OrderDate 
        ORDER BY COUNT(*) OVER (PARTITION BY o.CustomerID ORDER BY o.OrderDate) DESC
    ) AS RankOnThisDate
FROM Orders o;
```

## Practice Exercises

```sql
-- 1. Top 5 products by price
SELECT TOP 5 ProductName, UnitPrice,
    ROW_NUMBER() OVER (ORDER BY UnitPrice DESC) AS Rank
FROM Products;

-- 2. Employee order rankings
SELECT 
    EmployeeID,
    COUNT(*) AS OrderCount,
    RANK() OVER (ORDER BY COUNT(*) DESC) AS Rank
FROM Orders
GROUP BY EmployeeID;

-- 3. Product quartiles by price
SELECT 
    ProductName,
    UnitPrice,
    NTILE(4) OVER (ORDER BY UnitPrice) AS Quartile
FROM Products;
```

## Key Takeaways

- `ROW_NUMBER()` - Unique ranks (arbitrary for ties)
- `RANK()` - Ties get same rank, gaps after
- `DENSE_RANK()` - Ties get same rank, no gaps
- `NTILE(n)` - Divide into n buckets
- Great for top N, deduplication, segmentation
- Requires sorting - expensive at scale

## What's Next?

[Next: Analytic Functions →](03-analytic-functions.md)

---

[← Back: Window Basics](01-window-basics.md) | [Course Home](../README.md) | [Next: Analytic Functions →](03-analytic-functions.md)
