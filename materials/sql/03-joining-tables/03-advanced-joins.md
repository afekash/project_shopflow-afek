# Advanced Joins

## Overview

Beyond basic INNER and LEFT JOINs, there are advanced techniques including self-joins, multi-column joins, and join algorithms. Understanding these patterns is essential for complex queries and performance optimization.

## Self-Joins

A **self-join** joins a table to itself. Used for hierarchical data, comparisons within the same table, and finding relationships between rows.

### Example 1: Employee Management Hierarchy

```sql
-- Find each employee and their manager
SELECT 
    e.EmployeeID,
    e.FirstName + ' ' + e.LastName AS Employee,
    m.FirstName + ' ' + m.LastName AS Manager
FROM Employees e
    LEFT JOIN Employees m ON e.ReportsTo = m.EmployeeID
ORDER BY m.EmployeeID, e.EmployeeID;
```

**Result:** 9 rows
- Employees with managers: Both columns populated
- Top-level manager (Andrew Fuller): Manager column is NULL

### Example 2: Find Products in the Same Category

```sql
-- For each product, find other products in its category
SELECT 
    p1.ProductName AS Product,
    p2.ProductName AS SimilarProduct,
    p1.CategoryID
FROM Products p1
    INNER JOIN Products p2 ON p1.CategoryID = p2.CategoryID
                           AND p1.ProductID <> p2.ProductID  -- Exclude self
WHERE p1.ProductName = 'Chai'
ORDER BY p2.ProductName;
```

**Result:** Other beverages besides Chai

### Example 3: Find Products with Similar Prices

```sql
-- Products within $5 of each other (excluding self)
SELECT 
    p1.ProductName AS Product1,
    p1.UnitPrice AS Price1,
    p2.ProductName AS Product2,
    p2.UnitPrice AS Price2,
    ABS(p1.UnitPrice - p2.UnitPrice) AS PriceDifference
FROM Products p1
    INNER JOIN Products p2 ON p1.ProductID < p2.ProductID  -- Avoid duplicates
WHERE ABS(p1.UnitPrice - p2.UnitPrice) <= 5
ORDER BY PriceDifference;
```

**Note:** `p1.ProductID < p2.ProductID` ensures each pair appears once (not both A-B and B-A).

## Inequality Joins (Theta Joins)

Join using operators other than `=`.

### Example 1: Find Substitute Products

```sql
-- Products in the same category that are cheaper
SELECT 
    p1.ProductName AS OriginalProduct,
    p1.UnitPrice AS OriginalPrice,
    p2.ProductName AS CheaperAlternative,
    p2.UnitPrice AS AlternativePrice,
    p1.UnitPrice - p2.UnitPrice AS Savings
FROM Products p1
    INNER JOIN Products p2 
        ON p1.CategoryID = p2.CategoryID
        AND p2.UnitPrice < p1.UnitPrice
WHERE p1.ProductName = 'Chai'
ORDER BY p2.UnitPrice;
```

### Example 2: Running Totals with Self-Join

```sql
-- Running total of order freight costs
SELECT 
    o1.OrderID,
    o1.OrderDate,
    o1.Freight,
    SUM(o2.Freight) AS RunningTotal
FROM Orders o1
    INNER JOIN Orders o2 
        ON o2.OrderDate <= o1.OrderDate  -- All orders up to this date
GROUP BY o1.OrderID, o1.OrderDate, o1.Freight
ORDER BY o1.OrderDate;
```

## Practice Exercises

1. **Self-join:** Find pairs of products with the same price
2. **Hierarchy:** Show each employee with their manager's manager (grandmanager)
3. **Multi-column:** Join on both CategoryID and SupplierID

### Solutions

```sql
-- Exercise 1
SELECT 
    p1.ProductName AS Product1,
    p2.ProductName AS Product2,
    p1.UnitPrice
FROM Products p1
    INNER JOIN Products p2 
        ON p1.UnitPrice = p2.UnitPrice
        AND p1.ProductID < p2.ProductID;

-- Exercise 2
SELECT 
    e.FirstName + ' ' + e.LastName AS Employee,
    m.FirstName + ' ' + m.LastName AS Manager,
    gm.FirstName + ' ' + gm.LastName AS Grandmanager
FROM Employees e
    LEFT JOIN Employees m ON e.ReportsTo = m.EmployeeID
    LEFT JOIN Employees gm ON m.ReportsTo = gm.EmployeeID;

-- Exercise 3
SELECT p1.ProductName, p2.ProductName
FROM Products p1
    INNER JOIN Products p2 
        ON p1.CategoryID = p2.CategoryID
        AND p1.SupplierID = p2.SupplierID
        AND p1.ProductID < p2.ProductID;


## Key Takeaways

- **Self-joins** join a table to itself (hierarchies, comparisons)
- **Multi-column joins** match on multiple conditions simultaneously
- **Inequality joins** use `<`, `>`, `BETWEEN` (less common, more expensive)

## What's Next?

Learn why Northwind is normalized and how that differs from data warehouses:

[Next: Normalization vs Denormalization →](04-normalization-vs-denormalization.md)

---

[← Back: Join Types](02-join-types.md) | [Course Home](../README.md) | [Next: Normalization vs Denormalization →](04-normalization-vs-denormalization.md)
