# GROUP BY and HAVING

## Overview

`GROUP BY` aggregates rows into groups. `HAVING` filters groups after aggregation (WHERE filters rows before).

## GROUP BY Basics

```sql
-- Count orders per customer
SELECT 
    CustomerID,
    COUNT(*) AS OrderCount
FROM Orders
GROUP BY CustomerID
ORDER BY OrderCount DESC;
```

**How it works:**
1. Partition rows by CustomerID
2. Apply COUNT(*) to each group
3. Return one row per group

### Multiple Columns

```sql
-- Orders per customer per year
SELECT 
    CustomerID,
    YEAR(OrderDate) AS OrderYear,
    COUNT(*) AS OrderCount
FROM Orders
GROUP BY CustomerID, YEAR(OrderDate)
ORDER BY CustomerID, OrderYear;
```

Each unique combination of (CustomerID, Year) becomes a group.

## HAVING vs WHERE

**WHERE** - Filter **rows** before grouping  
**HAVING** - Filter **groups** after aggregation

```sql
-- Wrong: Can't use aggregate in WHERE
SELECT CustomerID, COUNT(*) AS OrderCount
FROM Orders
WHERE COUNT(*) > 10  -- ❌ Error!
GROUP BY CustomerID;

-- Correct: Use HAVING for aggregate conditions
SELECT CustomerID, COUNT(*) AS OrderCount
FROM Orders
GROUP BY CustomerID
HAVING COUNT(*) > 10;  -- ✅ Filters groups
```

### Combining WHERE and HAVING

```sql
-- Filter rows (WHERE), then groups (HAVING)
SELECT 
    CustomerID,
    COUNT(*) AS OrderCount,
    SUM(Freight) AS TotalFreight
FROM Orders
WHERE YEAR(OrderDate) = 1997        -- Filter: only 1997 orders
GROUP BY CustomerID
HAVING COUNT(*) > 5                  -- Filter: only customers with >5 orders
ORDER BY TotalFreight DESC;
```

**Execution order:** WHERE → GROUP BY → HAVING → SELECT → ORDER BY

## Practical Examples

### Category Sales

```sql
SELECT 
    c.CategoryName,
    COUNT(DISTINCT p.ProductID) AS ProductCount,
    AVG(p.UnitPrice) AS AvgPrice,
    SUM(p.UnitsInStock) AS TotalStock
FROM Categories c
    INNER JOIN Products p ON c.CategoryID = p.CategoryID
GROUP BY c.CategoryName
ORDER BY TotalStock DESC;
```

### Customer Analysis

```sql
-- High-value customers (>$1000 total freight)
SELECT 
    c.CompanyName,
    COUNT(o.OrderID) AS OrderCount,
    SUM(o.Freight) AS TotalFreight
FROM Customers c
    LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
GROUP BY c.CustomerID, c.CompanyName
HAVING SUM(o.Freight) > 1000
ORDER BY TotalFreight DESC;
```

### Product Performance

```sql
-- Products sold more than 50 times
SELECT 
    p.ProductName,
    COUNT(od.OrderID) AS TimesSold,
    SUM(od.Quantity) AS TotalQuantity
FROM Products p
    INNER JOIN [Order Details] od ON p.ProductID = od.ProductID
GROUP BY p.ProductID, p.ProductName
HAVING COUNT(od.OrderID) > 50
ORDER BY TimesSold DESC;
```

## Big Data Context

**Group by cardinality** matters:

```sql
-- Low cardinality (8 categories) - fast
SELECT CategoryID, COUNT(*) FROM Products GROUP BY CategoryID;

-- High cardinality (millions of users) - expensive shuffle in distributed systems
SELECT UserID, COUNT(*) FROM Events GROUP BY UserID;
```

High cardinality GROUP BY requires shuffling all data by key - expensive in Spark/Presto.

**Solution:** Pre-aggregate or use approximate algorithms.

## Practice Exercises

```sql
-- 1. Orders per employee
SELECT EmployeeID, COUNT(*) AS OrderCount
FROM Orders
GROUP BY EmployeeID;

-- 2. Customers who placed >10 orders
SELECT CustomerID, COUNT(*) AS OrderCount
FROM Orders
GROUP BY CustomerID
HAVING COUNT(*) > 10;

-- 3. Average order value by country
SELECT ShipCountry, AVG(Freight) AS AvgFreight
FROM Orders
GROUP BY ShipCountry
ORDER BY AvgFreight DESC;

-- 4. Products by category (names concatenated)
SELECT 
    CategoryID,
    STRING_AGG(ProductName, ', ') AS Products
FROM Products
GROUP BY CategoryID;
```

## Key Takeaways

- `GROUP BY` aggregates rows into groups
- Each SELECT column must be in GROUP BY or be an aggregate
- `WHERE` filters before grouping, `HAVING` filters after
- Multiple GROUP BY columns create groups from combinations
- High cardinality grouping is expensive in distributed systems

## What's Next?

[Next: Advanced Grouping →](03-advanced-grouping.md)

---

[← Back: Aggregate Functions](01-aggregate-functions.md) | [Course Home](../README.md) | [Next: Subqueries and CTEs →](../05-subqueries-ctes/01-subqueries.md)
