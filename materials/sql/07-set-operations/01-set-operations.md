# Set Operations

## Overview

Set operations combine results from multiple SELECT statements. Based on set theory: union, intersection, difference.

## UNION

Combines results, **removes duplicates**.

```sql
-- All cities from customers and suppliers
SELECT City FROM Customers
UNION
SELECT City FROM Suppliers;
```

**Requirements:**
- Same number of columns
- Compatible data types
- Column names from first query used

## UNION ALL

Combines results, **keeps duplicates** (faster).

```sql
-- All cities including duplicates
SELECT City, 'Customer' AS Source FROM Customers
UNION ALL
SELECT City, 'Supplier' FROM Suppliers;
```

**Performance:** Use UNION ALL when duplicates don't matter - avoids expensive duplicate removal.

### When to Use Each

```sql
-- UNION: Remove duplicates (slower)
SELECT Country FROM Customers
UNION
SELECT Country FROM Suppliers;
-- Result: 29 unique countries

-- UNION ALL: Keep duplicates (faster)
SELECT Country FROM Customers
UNION ALL
SELECT Country FROM Suppliers;
-- Result: 120 rows (91 + 29)
```

## INTERSECT

Returns rows that appear in **both** queries.

```sql
-- Cities with both customers and suppliers
SELECT City FROM Customers
INTERSECT
SELECT City FROM Suppliers;
-- Result: London, São Paulo, etc.
```

**Equivalent JOIN version:**

```sql
SELECT DISTINCT c.City
FROM Customers c
    INNER JOIN Suppliers s ON c.City = s.City;
```

## EXCEPT (MINUS in Oracle)

Returns rows in first query but **not** in second.

```sql
-- Cities with customers but no suppliers
SELECT City FROM Customers
EXCEPT
SELECT City FROM Suppliers;
```

**Equivalent:**

```sql
SELECT DISTINCT City
FROM Customers
WHERE City NOT IN (SELECT City FROM Suppliers WHERE City IS NOT NULL);
```

## Practical Examples

### Combined Contact List

```sql
-- All contacts from customers, suppliers, and employees
SELECT 
    CompanyName AS Name, 
    ContactName AS Contact,
    Phone,
    'Customer' AS Type
FROM Customers
UNION ALL
SELECT 
    CompanyName,
    ContactName,
    Phone,
    'Supplier'
FROM Suppliers
UNION ALL
SELECT 
    'Northwind Traders',
    FirstName + ' ' + LastName,
    HomePhone,
    'Employee'
FROM Employees
ORDER BY Type, Name;
```

### Missing Data Analysis

```sql
-- Products ordered vs not ordered
SELECT ProductID FROM Products
EXCEPT
SELECT DISTINCT ProductID FROM [Order Details];
-- Result: Products never ordered
```

### Data Comparison

```sql
-- Find customers in both USA and with orders in 1997
SELECT CustomerID FROM Customers WHERE Country = 'USA'
INTERSECT
SELECT DISTINCT CustomerID FROM Orders WHERE YEAR(OrderDate) = 1997;
```

## Ordering and Limiting

ORDER BY goes at the end (applies to final result):

```sql
(SELECT City FROM Customers)
UNION
(SELECT City FROM Suppliers)
ORDER BY City;  -- Sorts final combined result
```

**TOP/LIMIT before UNION:**

```sql
-- Top 5 from each, then combine
(SELECT TOP 5 ProductName, UnitPrice FROM Products ORDER BY UnitPrice DESC)
UNION ALL
(SELECT TOP 5 CategoryName, 0 FROM Categories);
```

## Advanced: Multiple Set Operations

```sql
-- Complex combinations (use parentheses for clarity)
SELECT City FROM Customers
UNION
SELECT City FROM Suppliers
EXCEPT
SELECT City FROM Employees;
-- Cities with customers or suppliers, but no employees
```

## Column Compatibility

Columns must be compatible:

```sql
-- ✅ Works: both numeric
SELECT ProductID FROM Products
UNION
SELECT CategoryID FROM Categories;

-- ❌ Error: incompatible types
SELECT ProductName FROM Products
UNION
SELECT UnitPrice FROM Products;
```

**Fix:** Cast to compatible type:

```sql
SELECT ProductName FROM Products
UNION
SELECT CAST(UnitPrice AS NVARCHAR) FROM Products;
```

## Big Data Context

**UNION ALL is preferred** in ETL pipelines:

```sql
-- Combine data from multiple sources
SELECT * FROM sales_2022
UNION ALL
SELECT * FROM sales_2023
UNION ALL
SELECT * FROM sales_2024;
```

**No deduplication needed** - saves expensive shuffle/sort operation.

**INTERSECT/EXCEPT are expensive** in distributed systems:
- Require shuffle to colocate matching rows
- Consider joins or EXISTS/NOT EXISTS instead

```sql
-- INTERSECT (expensive shuffle)
SELECT id FROM table_a
INTERSECT
SELECT id FROM table_b;

-- Better: SEMI JOIN (can use broadcast)
SELECT DISTINCT id FROM table_a
WHERE EXISTS (SELECT 1 FROM table_b WHERE table_b.id = table_a.id);
```

## Practice Exercises

```sql
-- 1. All countries from customers and suppliers (no duplicates)
SELECT Country FROM Customers
UNION
SELECT Country FROM Suppliers;

-- 2. Customers who ordered in both 1996 and 1997
SELECT DISTINCT CustomerID FROM Orders WHERE YEAR(OrderDate) = 1996
INTERSECT
SELECT DISTINCT CustomerID FROM Orders WHERE YEAR(OrderDate) = 1997;

-- 3. Products in stock but never ordered
SELECT ProductID FROM Products WHERE UnitsInStock > 0
EXCEPT
SELECT DISTINCT ProductID FROM [Order Details];

-- 4. Combined list with source tag
SELECT City, 'Customer' AS Source FROM Customers
UNION ALL
SELECT City, 'Supplier' FROM Suppliers
ORDER BY City;
```

## Key Takeaways

- `UNION` removes duplicates, `UNION ALL` keeps them
- `INTERSECT` returns rows in both queries
- `EXCEPT` returns rows in first but not second
- Column count and types must match
- ORDER BY applies to final result
- UNION ALL is faster (no dedup) - use when possible
- In big data, UNION ALL preferred over UNION
- INTERSECT/EXCEPT expensive - consider JOINs/EXISTS

## What's Next?

[Next: Module 08 - Data Manipulation →](../08-data-manipulation/01-insert.md)

---

[← Back: Window Frames](../06-window-functions/04-frames-running-totals.md) | [Course Home](../README.md) | [Next: INSERT →](../08-data-manipulation/01-insert.md)
