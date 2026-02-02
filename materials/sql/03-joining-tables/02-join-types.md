# Join Types

## Overview

SQL provides several JOIN types to handle different data combination scenarios. Each type determines which rows from the left and right tables appear in the result set.

## The Five Main JOIN Types

1. **INNER JOIN** - Only matching rows from both tables
2. **LEFT OUTER JOIN** - All left table rows + matching right rows
3. **RIGHT OUTER JOIN** - All right table rows + matching left rows
4. **FULL OUTER JOIN** - All rows from both tables
5. **CROSS JOIN** - Cartesian product (all combinations)

## INNER JOIN

Returns only rows where the join condition matches in **both** tables.

### Syntax

```sql
SELECT columns
FROM table1
    INNER JOIN table2 ON table1.key = table2.key;
```

The `INNER` keyword is optional (it's the default):

```sql
FROM table1 JOIN table2 ON table1.key = table2.key;  -- Same as INNER JOIN
```

### Example 1: Products with Their Categories

```sql
-- Get product names with category names
SELECT 
    p.ProductName,
    p.UnitPrice,
    c.CategoryName
FROM Products p
    INNER JOIN Categories c ON p.CategoryID = c.CategoryID;
```

**Result:** 77 rows (all products have a category)

### Example 2: Orders with Customer Information

```sql
-- Orders with customer company names
SELECT 
    o.OrderID,
    o.OrderDate,
    c.CompanyName,
    o.Freight
FROM Orders o
    INNER JOIN Customers c ON o.CustomerID = c.CustomerID;
```

**Result:** 830 rows (all orders have a customer)

### When to Use INNER JOIN

- You only want rows where **both sides match**
- Most common JOIN type
- Excludes orphaned records

## LEFT OUTER JOIN (LEFT JOIN)

Returns **all rows from the left table** plus matching rows from the right table. Right-side columns are `NULL` when there's no match.

### Syntax

```sql
SELECT columns
FROM table1
    LEFT OUTER JOIN table2 ON table1.key = table2.key;
```

`OUTER` is optional:

```sql
FROM table1 LEFT JOIN table2 ON table1.key = table2.key;  -- Same thing
```

### Example 1: All Customers and Their Orders

```sql
-- Show ALL customers, even those without orders
SELECT 
    c.CustomerID,
    c.CompanyName,
    COUNT(o.OrderID) AS OrderCount
FROM Customers c
    LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
GROUP BY c.CustomerID, c.CompanyName
ORDER BY OrderCount DESC;
```

**Result:** 91 rows (all customers)
- Customers with orders: OrderCount > 0
- Customers without orders: OrderCount = 0

### Example 2: Find Customers With No Orders

```sql
-- Customers who have never placed an order
SELECT 
    c.CustomerID,
    c.CompanyName
FROM Customers c
    LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
WHERE o.OrderID IS NULL;  -- No matching order
```

**Result:** ~2 customers (those with NULL OrderID)

### When to Use LEFT JOIN

- You want **all rows from the left table**
- Find records that **don't have** matches (use `WHERE right.key IS NULL`)
- Common in reporting (show all entities even with zero activity)

## RIGHT OUTER JOIN (RIGHT JOIN)

Returns **all rows from the right table** plus matching rows from the left table. Mirror image of LEFT JOIN.

### Syntax

```sql
SELECT columns
FROM table1
    RIGHT OUTER JOIN table2 ON table1.key = table2.key;
```

### Example: All Categories and Product Counts

```sql
-- Show ALL categories, even those without products
SELECT 
    c.CategoryID,
    c.CategoryName,
    COUNT(p.ProductID) AS ProductCount
FROM Products p
    RIGHT JOIN Categories c ON p.CategoryID = c.CategoryID
GROUP BY c.CategoryID, c.CategoryName;
```

**Result:** 8 rows (all categories, even if no products)

### When to Use RIGHT JOIN

**Honestly?** Almost never. You can always rewrite as LEFT JOIN:

```sql
-- RIGHT JOIN version:
FROM Products p RIGHT JOIN Categories c ON ...

-- Equivalent LEFT JOIN (preferred):
FROM Categories c LEFT JOIN Products p ON ...
```

**Best practice:** Stick with LEFT JOIN for consistency and readability.

## FULL OUTER JOIN (FULL JOIN)

Returns **all rows from both tables**. Non-matching rows have NULLs for the other table's columns.

### Syntax

```sql
SELECT columns
FROM table1
    FULL OUTER JOIN table2 ON table1.key = table2.key;
```

### Example: All Customers and Orders (Hypothetical)

```sql
-- Show all customers AND all orders
-- (In Northwind, all orders have customers, so this = LEFT JOIN)
SELECT 
    c.CustomerID,
    c.CompanyName,
    o.OrderID,
    o.OrderDate
FROM Customers c
    FULL OUTER JOIN Orders o ON c.CustomerID = o.CustomerID;
```

**Result:** 
- Customers with orders: Both sides populated
- Customers without orders: Order columns NULL
- Orders without customers: Customer columns NULL (rare due to FK constraints)

### When to Use FULL OUTER JOIN

- Reconciling data from two sources
- Finding orphans in **both** tables
- Relatively rare in practice

### Example: Finding Data Quality Issues

```sql
-- Find mismatches between two versions of customer data
SELECT 
    COALESCE(old.CustomerID, new.CustomerID) AS CustomerID,
    old.CompanyName AS OldName,
    new.CompanyName AS NewName
FROM OldCustomers old
    FULL OUTER JOIN NewCustomers new ON old.CustomerID = new.CustomerID
WHERE old.CustomerID IS NULL OR new.CustomerID IS NULL;
```

## CROSS JOIN

Returns the **Cartesian product** - every combination of rows.

### Syntax

```sql
SELECT columns
FROM table1
    CROSS JOIN table2;

-- Old syntax (implicit):
SELECT columns
FROM table1, table2;  -- No WHERE clause = Cartesian product
```

### Example 1: All Category-Supplier Combinations

```sql
-- What if every supplier could supply every category?
SELECT 
    s.CompanyName AS Supplier,
    c.CategoryName AS Category
FROM Suppliers s
    CROSS JOIN Categories c;
```

**Result:** 29 suppliers × 8 categories = 232 rows

### Example 2: Generate Date Ranges for All Employees

```sql
-- Create a calendar grid: each employee × each day in January
WITH January AS (
    SELECT CAST('2024-01-01' AS DATE) AS Date
    UNION ALL
    SELECT DATEADD(DAY, 1, Date)
    FROM January
    WHERE Date < '2024-01-31'
)
SELECT 
    e.EmployeeID,
    e.FirstName + ' ' + e.LastName AS EmployeeName,
    j.Date
FROM Employees e
    CROSS JOIN January j
ORDER BY e.EmployeeID, j.Date
OPTION (MAXRECURSION 31);
```

**Result:** 9 employees × 31 days = 279 rows

### When to Use CROSS JOIN

- Generate all combinations (test data, grids, schedules)
- Pair every item from one list with every item from another
- Usually combined with WHERE to filter the Cartesian product

## Advanced Insights

### NULL Behavior in JOINs

When a LEFT/RIGHT/FULL JOIN doesn't find a match, right-side columns are `NULL`:

```sql
SELECT c.CustomerID, o.OrderID
FROM Customers c
    LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
WHERE o.OrderID IS NULL;  -- Find non-matches
```

**Important:** Use `IS NULL` to test, not `= NULL`.

### JOIN vs WHERE for Filtering

```sql
-- These are equivalent for INNER JOIN:

-- JOIN condition
FROM Orders o
    INNER JOIN Customers c ON o.CustomerID = c.CustomerID
                          AND c.Country = 'USA';

-- WHERE clause
FROM Orders o
    INNER JOIN Customers c ON o.CustomerID = c.CustomerID
WHERE c.Country = 'USA';
```

**For OUTER JOINs, they're different!**

```sql
-- Filter in JOIN: Include all Orders, but only USA customer info
FROM Orders o
    LEFT JOIN Customers c ON o.CustomerID = c.CustomerID
                         AND c.Country = 'USA';
-- Result: All 830 orders, Customer columns NULL for non-USA

-- Filter in WHERE: Exclude orders to non-USA customers
FROM Orders o
    LEFT JOIN Customers c ON o.CustomerID = c.CustomerID
WHERE c.Country = 'USA';
-- Result: Only orders to USA customers
```

## Practice Exercises

1. List all products with their category names
2. Find all customers who have **never** placed an order
3. Count how many products are in each category, including empty categories
4. Create a grid of all employees × all shippers
5. Full order summary: Order, Customer, Employee, all line items

### Solutions

```sql
-- Exercise 1
SELECT p.ProductName, c.CategoryName
FROM Products p
    INNER JOIN Categories c ON p.CategoryID = c.CategoryID;

-- Exercise 2
SELECT c.CustomerID, c.CompanyName
FROM Customers c
    LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
WHERE o.OrderID IS NULL;

-- Exercise 3
SELECT 
    c.CategoryID,
    c.CategoryName,
    COUNT(p.ProductID) AS ProductCount
FROM Categories c
    LEFT JOIN Products p ON c.CategoryID = p.CategoryID
GROUP BY c.CategoryID, c.CategoryName;

-- Exercise 4
SELECT 
    e.FirstName + ' ' + e.LastName AS Employee,
    s.CompanyName AS Shipper
FROM Employees e
    CROSS JOIN Shippers s;

-- Exercise 5
SELECT 
    o.OrderID,
    o.OrderDate,
    c.CompanyName AS Customer,
    e.FirstName + ' ' + e.LastName AS Employee,
    p.ProductName,
    od.Quantity,
    od.UnitPrice,
    od.Quantity * od.UnitPrice AS LineTotal
FROM Orders o
    INNER JOIN Customers c ON o.CustomerID = c.CustomerID
    INNER JOIN Employees e ON o.EmployeeID = e.EmployeeID
    INNER JOIN [Order Details] od ON o.OrderID = od.OrderID
    INNER JOIN Products p ON od.ProductID = p.ProductID
ORDER BY o.OrderID, p.ProductName;
```

## Key Takeaways

- **INNER JOIN** - Only matching rows (most common)
- **LEFT JOIN** - All left rows + matching right rows
- **RIGHT JOIN** - All right rows + matching left rows (rarely used, prefer LEFT)
- **FULL OUTER JOIN** - All rows from both tables (uncommon)
- **CROSS JOIN** - Cartesian product, all combinations
- Use `IS NULL` on right table to find non-matches in LEFT JOIN
- OUTER JOIN filtering: JOIN condition ≠ WHERE clause
- Always verify expected cardinality after joining

## What's Next?

Learn advanced JOIN techniques and performance optimization:

[Next: Advanced Joins →](03-advanced-joins.md)

---

[← Back: Join Theory](01-join-theory.md) | [Course Home](../README.md) | [Next: Advanced Joins →](03-advanced-joins.md)
