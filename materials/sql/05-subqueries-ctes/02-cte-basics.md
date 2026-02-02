# Common Table Expressions (CTEs)

## Overview

CTEs (WITH clause) create temporary named result sets that exist for a single query. Cleaner and more readable than subqueries.

## Basic Syntax

```sql
WITH cte_name AS (
    SELECT ...
)
SELECT * FROM cte_name;
```

## Simple Example

```sql
-- Calculate average product price, then find expensive products
WITH AvgPrice AS (
    SELECT AVG(UnitPrice) AS Average
    FROM Products
)
SELECT 
    p.ProductName,
    p.UnitPrice,
    ap.Average
FROM Products p
    CROSS JOIN AvgPrice ap
WHERE p.UnitPrice > ap.Average;
```

## Multiple CTEs

Separate with commas (not multiple WITH keywords).

```sql
WITH 
CategoryStats AS (
    SELECT 
        CategoryID,
        AVG(UnitPrice) AS AvgPrice,
        COUNT(*) AS ProductCount
    FROM Products
    GROUP BY CategoryID
),
ExpensiveCategories AS (
    SELECT CategoryID
    FROM CategoryStats
    WHERE AvgPrice > 30
)
SELECT 
    c.CategoryName,
    cs.AvgPrice,
    cs.ProductCount
FROM Categories c
    INNER JOIN CategoryStats cs ON c.CategoryID = cs.CategoryID
    INNER JOIN ExpensiveCategories ec ON c.CategoryID = ec.CategoryID;
```

## CTEs vs Subqueries

**CTE version (readable):**

```sql
WITH CustomerOrders AS (
    SELECT CustomerID, COUNT(*) AS OrderCount
    FROM Orders
    GROUP BY CustomerID
)
SELECT c.CompanyName, co.OrderCount
FROM Customers c
    LEFT JOIN CustomerOrders co ON c.CustomerID = co.CustomerID
ORDER BY co.OrderCount DESC;
```

**Subquery version (harder to read):**

```sql
SELECT 
    c.CompanyName,
    (SELECT COUNT(*) FROM Orders WHERE CustomerID = c.CustomerID) AS OrderCount
FROM Customers c
ORDER BY OrderCount DESC;
```

## Practical Examples

### Multi-Step Calculation

```sql
-- Calculate revenue, then rank by revenue
WITH OrderRevenue AS (
    SELECT 
        OrderID,
        SUM(Quantity * UnitPrice * (1 - Discount)) AS Revenue
    FROM [Order Details]
    GROUP BY OrderID
)
SELECT 
    o.OrderID,
    o.CustomerID,
    o.OrderDate,
    or.Revenue
FROM Orders o
    INNER JOIN OrderRevenue or ON o.OrderID = or.OrderID
WHERE or.Revenue > 1000
ORDER BY or.Revenue DESC;
```

### Reusing CTE Multiple Times

```sql
WITH ProductStats AS (
    SELECT 
        CategoryID,
        AVG(UnitPrice) AS AvgPrice,
        COUNT(*) AS ProductCount
    FROM Products
    GROUP BY CategoryID
)
SELECT 
    'High' AS Level,
    CategoryID,
    AvgPrice
FROM ProductStats
WHERE AvgPrice > 50
UNION ALL
SELECT 
    'Low' AS Level,
    CategoryID,
    AvgPrice
FROM ProductStats
WHERE AvgPrice < 20;
```

**Benefit:** `ProductStats` computed once, used twice.

### Data Quality Checks

```sql
-- Find orders with invalid references
WITH MissingCustomers AS (
    SELECT OrderID, CustomerID
    FROM Orders
    WHERE CustomerID NOT IN (SELECT CustomerID FROM Customers)
),
MissingEmployees AS (
    SELECT OrderID, EmployeeID
    FROM Orders
    WHERE EmployeeID NOT IN (SELECT EmployeeID FROM Employees)
)
SELECT 
    'Missing Customer' AS Issue,
    OrderID,
    CustomerID AS ProblemID
FROM MissingCustomers
UNION ALL
SELECT 
    'Missing Employee',
    OrderID,
    CAST(EmployeeID AS NVARCHAR)
FROM MissingEmployees;
```

## Advanced Insights

### CTE Materialization

CTEs are **not materialized** by default - they're executed each time referenced (like inline views).

```sql
WITH ExpensiveCalc AS (
    SELECT ...complex calculation...
)
SELECT * FROM ExpensiveCalc  -- Executes CTE
UNION ALL
SELECT * FROM ExpensiveCalc; -- Executes CTE again!
```

**Solution:** Use temp table if CTE is expensive and reused:

```sql
SELECT ...complex calculation...
INTO #ExpensiveCalc
FROM ...;

SELECT * FROM #ExpensiveCalc
UNION ALL
SELECT * FROM #ExpensiveCalc;
```

### CTE Scope

CTEs only exist for the immediately following statement:

```sql
WITH Temp AS (SELECT ...)
SELECT * FROM Temp;  -- ✅ Works

SELECT * FROM Temp;  -- ❌ Error: Temp doesn't exist
```

## Practice Exercises

```sql
-- 1. Products above category average
WITH CategoryAvg AS (
    SELECT CategoryID, AVG(UnitPrice) AS AvgPrice
    FROM Products
    GROUP BY CategoryID
)
SELECT p.ProductName, p.UnitPrice, ca.AvgPrice
FROM Products p
    INNER JOIN CategoryAvg ca ON p.CategoryID = ca.CategoryID
WHERE p.UnitPrice > ca.AvgPrice;

-- 2. Top 5 customers by order count
WITH CustomerOrderCount AS (
    SELECT CustomerID, COUNT(*) AS OrderCount
    FROM Orders
    GROUP BY CustomerID
)
SELECT TOP 5 c.CompanyName, coc.OrderCount
FROM Customers c
    INNER JOIN CustomerOrderCount coc ON c.CustomerID = coc.CustomerID
ORDER BY coc.OrderCount DESC;

-- 3. Monthly sales summary
WITH MonthlySales AS (
    SELECT 
        YEAR(OrderDate) AS Year,
        MONTH(OrderDate) AS Month,
        SUM(Freight) AS TotalFreight
    FROM Orders
    GROUP BY YEAR(OrderDate), MONTH(OrderDate)
)
SELECT Year, Month, TotalFreight
FROM MonthlySales
WHERE TotalFreight > 1000
ORDER BY Year, Month;
```

## Key Takeaways

- CTEs use `WITH name AS (SELECT ...)` syntax
- More readable than nested subqueries
- Multiple CTEs separated by commas
- CTEs can reference earlier CTEs
- Not materialized by default (executed each time referenced)
- Scope limited to next statement
- Great for breaking complex queries into steps

## What's Next?

[Next: Recursive CTEs →](03-recursive-ctes.md)

---

[← Back: Subqueries](01-subqueries.md) | [Course Home](../README.md) | [Next: Recursive CTEs →](03-recursive-ctes.md)
