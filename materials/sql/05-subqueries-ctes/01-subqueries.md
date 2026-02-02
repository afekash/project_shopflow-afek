# Subqueries

## Overview

A subquery is a query nested inside another query. Useful for multi-step logic and filtering based on aggregated or related data.

## Scalar Subqueries

Returns a single value (one row, one column).

```sql
-- Products more expensive than average
SELECT ProductName, UnitPrice
FROM Products
WHERE UnitPrice > (SELECT AVG(UnitPrice) FROM Products);
```

```sql
-- Order with highest freight cost
SELECT OrderID, Freight
FROM Orders
WHERE Freight = (SELECT MAX(Freight) FROM Orders);
```

## Subqueries with IN

Returns multiple values (one column, multiple rows).

```sql
-- Customers who placed orders in 1997
SELECT CustomerID, CompanyName
FROM Customers
WHERE CustomerID IN (
    SELECT CustomerID 
    FROM Orders 
    WHERE YEAR(OrderDate) = 1997
);
```

### NOT IN

```sql
-- Customers who never ordered
SELECT CustomerID, CompanyName
FROM Customers
WHERE CustomerID NOT IN (
    SELECT CustomerID FROM Orders WHERE CustomerID IS NOT NULL
);
```

**Warning:** `NOT IN` with NULLs can return empty results! Use `NOT EXISTS` instead (covered next).

## EXISTS and NOT EXISTS

Tests if subquery returns any rows (boolean result).

```sql
-- Customers with at least one order
SELECT CustomerID, CompanyName
FROM Customers c
WHERE EXISTS (
    SELECT 1 FROM Orders o WHERE o.CustomerID = c.CustomerID
);

-- Customers with NO orders
SELECT CustomerID, CompanyName
FROM Customers c
WHERE NOT EXISTS (
    SELECT 1 FROM Orders o WHERE o.CustomerID = c.CustomerID
);
```

**Advantage:** More efficient than `NOT IN`, handles NULLs correctly.

## Correlated Subqueries

Subquery references outer query's columns (executed once per outer row).

```sql
-- Products more expensive than their category average
SELECT 
    ProductName, 
    UnitPrice,
    CategoryID
FROM Products p
WHERE UnitPrice > (
    SELECT AVG(UnitPrice) 
    FROM Products 
    WHERE CategoryID = p.CategoryID  -- Correlated!
);
```

```sql
-- Employees who earn more than their department average
SELECT 
    e.EmployeeID,
    e.FirstName,
    e.Title
FROM Employees e
WHERE e.Salary > (
    SELECT AVG(Salary)
    FROM Employees
    WHERE Title = e.Title
);
```

**Performance:** Can be slow - runs once for each outer row.

## Subqueries in FROM (Derived Tables)

Subquery acts as a table.

```sql
-- Average order value by customer
SELECT 
    c.CustomerID,
    c.CompanyName,
    summary.AvgFreight
FROM Customers c
    INNER JOIN (
        SELECT CustomerID, AVG(Freight) AS AvgFreight
        FROM Orders
        GROUP BY CustomerID
    ) summary ON c.CustomerID = summary.CustomerID
ORDER BY summary.AvgFreight DESC;
```

Must use an alias for derived tables.

## Subqueries in SELECT

```sql
-- Show each product with its category's product count
SELECT 
    p.ProductName,
    p.CategoryID,
    (SELECT COUNT(*) 
     FROM Products 
     WHERE CategoryID = p.CategoryID) AS ProductsInCategory
FROM Products p;
```

**Note:** Correlated - runs once per product.

## ANY and ALL

Compare with results of subquery.

```sql
-- Products more expensive than ANY product in category 1
SELECT ProductName, UnitPrice
FROM Products
WHERE UnitPrice > ANY (
    SELECT UnitPrice FROM Products WHERE CategoryID = 1
);
-- Equivalent to: UnitPrice > MIN(beverages)

-- Products more expensive than ALL products in category 1
SELECT ProductName, UnitPrice
FROM Products
WHERE UnitPrice > ALL (
    SELECT UnitPrice FROM Products WHERE CategoryID = 1
);
-- Equivalent to: UnitPrice > MAX(beverages)
```

## Practical Examples

### Find Top N per Group

```sql
-- Top 3 most expensive products per category
SELECT *
FROM Products p
WHERE (
    SELECT COUNT(*)
    FROM Products
    WHERE CategoryID = p.CategoryID 
    AND UnitPrice >= p.UnitPrice
) <= 3
ORDER BY CategoryID, UnitPrice DESC;
```

### Filtering with Aggregates

```sql
-- Categories with above-average product count
SELECT CategoryName
FROM Categories c
WHERE (
    SELECT COUNT(*) 
    FROM Products 
    WHERE CategoryID = c.CategoryID
) > (
    SELECT COUNT(*) / (SELECT COUNT(DISTINCT CategoryID) FROM Products)
    FROM Products
);
```

## Advanced Insights

### When to Use Subqueries vs JOINs

**Use subqueries for:**
- One-off filters (`IN`, `EXISTS`)
- Scalar values (average, max)
- Clearer logic in some cases

**Use JOINs for:**
- Need columns from both tables
- Better performance (usually)
- More explicit execution plan

## Practice Exercises

```sql
-- 1. Products above average price
SELECT ProductName, UnitPrice FROM Products
WHERE UnitPrice > (SELECT AVG(UnitPrice) FROM Products);

-- 2. Customers who ordered product "Chai"
SELECT DISTINCT CustomerID FROM Orders
WHERE OrderID IN (
    SELECT OrderID FROM [Order Details]
    WHERE ProductID = 1
);

-- 3. Employees with above-average orders handled
SELECT EmployeeID, 
       (SELECT COUNT(*) FROM Orders WHERE EmployeeID = e.EmployeeID) AS OrderCount
FROM Employees e
WHERE (SELECT COUNT(*) FROM Orders WHERE EmployeeID = e.EmployeeID) > 
      (SELECT COUNT(*) / (SELECT COUNT(*) FROM Employees) FROM Orders);
```

## Key Takeaways

- Scalar subqueries return single value
- `IN` tests membership in a set
- `EXISTS` checks if subquery returns rows (better than `NOT IN`)
- Correlated subqueries reference outer query (can be slow)
- Derived tables (FROM subqueries) act as temporary tables
- Optimizers often convert subqueries to JOINs

## What's Next?

[Next: CTE Basics →](02-cte-basics.md)

---

[← Back: Advanced Grouping](../04-aggregations/03-advanced-grouping.md) | [Course Home](../README.md) | [Next: CTE Basics →](02-cte-basics.md)
