# Window Functions Basics

## Overview

Window functions perform calculations across rows **related to the current row** without collapsing results like GROUP BY. Critical for analytics and data engineering.

## OVER() Clause

The `OVER()` clause defines the "window" of rows.

```sql
-- Add row numbers to products
SELECT 
    ProductID,
    ProductName,
    UnitPrice,
    ROW_NUMBER() OVER (ORDER BY UnitPrice DESC) AS PriceRank
FROM Products;
```

**Key difference from GROUP BY:**
- GROUP BY: Collapses rows into groups
- Window functions: Keep all rows, add computed columns

## PARTITION BY

Divides rows into partitions (like GROUP BY but doesn't collapse).

```sql
-- Row number within each category
SELECT 
    CategoryID,
    ProductName,
    UnitPrice,
    ROW_NUMBER() OVER (PARTITION BY CategoryID ORDER BY UnitPrice DESC) AS RankInCategory
FROM Products
ORDER BY CategoryID, RankInCategory;
```

**Result:** Each category gets its own ranking (1, 2, 3...).

## ORDER BY in OVER

Defines the sort order within each window/partition.

```sql
-- Rank all products by price (no partitions)
SELECT 
    ProductName,
    UnitPrice,
    ROW_NUMBER() OVER (ORDER BY UnitPrice DESC) AS OverallRank,
    RANK() OVER (ORDER BY UnitPrice DESC) AS OverallRankWithTies
FROM Products;
```

## Practical Examples

### Running Total

```sql
-- Running total of freight by date
SELECT 
    OrderID,
    OrderDate,
    Freight,
    SUM(Freight) OVER (ORDER BY OrderDate, OrderID) AS RunningTotal
FROM Orders
ORDER BY OrderDate;
```

### Comparison to Aggregate

```sql
-- Each product with category total stock
SELECT 
    p.ProductName,
    p.CategoryID,
    p.UnitsInStock,
    SUM(p.UnitsInStock) OVER (PARTITION BY p.CategoryID) AS CategoryTotalStock,
    p.UnitsInStock * 100.0 / SUM(p.UnitsInStock) OVER (PARTITION BY p.CategoryID) AS PercentOfCategory
FROM Products p;
```

**No GROUP BY needed!** All product rows retained.

### Multiple Windows

```sql
-- Different windows in one query
SELECT 
    ProductName,
    CategoryID,
    UnitPrice,
    AVG(UnitPrice) OVER () AS OverallAvg,
    AVG(UnitPrice) OVER (PARTITION BY CategoryID) AS CategoryAvg,
    UnitPrice - AVG(UnitPrice) OVER (PARTITION BY CategoryID) AS DiffFromCategoryAvg
FROM Products;
```

## Window Function Categories

1. **Ranking:** ROW_NUMBER, RANK, DENSE_RANK, NTILE
2. **Analytic:** LAG, LEAD, FIRST_VALUE, LAST_VALUE
3. **Aggregate:** SUM, AVG, COUNT, MIN, MAX with OVER

## When to Use Window Functions

- **Rankings** within groups
- **Running totals** and moving averages
- **Comparisons** to previous/next rows
- **Percentages** of group totals
- **Deduplication** (ROW_NUMBER + WHERE = 1)

## Practice Exercises

```sql
-- 1. Rank products by price
SELECT 
    ProductName,
    UnitPrice,
    ROW_NUMBER() OVER (ORDER BY UnitPrice DESC) AS Rank
FROM Products;

-- 2. Running count of orders by date
SELECT 
    OrderDate,
    COUNT(*) OVER (ORDER BY OrderDate) AS CumulativeOrders
FROM Orders;

-- 3. Product price vs category average
SELECT 
    ProductName,
    CategoryID,
    UnitPrice,
    AVG(UnitPrice) OVER (PARTITION BY CategoryID) AS CategoryAvg
FROM Products;
```

## Key Takeaways

- Window functions use `OVER()` clause
- `PARTITION BY` creates groups (like GROUP BY but keeps all rows)
- `ORDER BY` in OVER defines window sort order
- Combine rankings, analytics, and aggregates
- All rows retained (unlike GROUP BY)
- Essential for analytics and data engineering

## What's Next?

[Next: Ranking Functions →](02-ranking-functions.md)

---

[← Back: Recursive CTEs](../05-subqueries-ctes/03-recursive-ctes.md) | [Course Home](../README.md) | [Next: Ranking Functions →](02-ranking-functions.md)
