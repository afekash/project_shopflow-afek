# UPDATE and DELETE

## Overview

UPDATE modifies existing rows. DELETE removes rows. Both support WHERE clauses (without WHERE = affects ALL rows!).

## UPDATE Syntax

```sql
UPDATE table_name
SET column1 = value1, column2 = value2
WHERE condition;
```

### Simple UPDATE

```sql
-- Increase all product prices by 10%
UPDATE Products
SET UnitPrice = UnitPrice * 1.1
WHERE CategoryID = 1;  -- Only beverages

-- Update multiple columns
UPDATE Employees
SET Title = 'Sales Manager', HireDate = GETDATE()
WHERE EmployeeID = 5;
```

⚠️ **Without WHERE, updates ALL rows:**

```sql
-- DANGER: Updates every product!
UPDATE Products
SET Discontinued = 1;
```

## UPDATE with JOIN (T-SQL)

```sql
-- Update products based on category data
UPDATE p
SET p.UnitPrice = p.UnitPrice * 1.15
FROM Products p
    INNER JOIN Categories c ON p.CategoryID = c.CategoryID
WHERE c.CategoryName = 'Beverages';
```

**Standard SQL version:**

```sql
UPDATE Products
SET UnitPrice = UnitPrice * 1.15
WHERE CategoryID IN (
    SELECT CategoryID FROM Categories WHERE CategoryName = 'Beverages'
);
```

### Update from Another Table

```sql
-- Update product prices from price list
UPDATE Products
SET UnitPrice = pl.NewPrice
FROM Products p
    INNER JOIN PriceList pl ON p.ProductID = pl.ProductID
WHERE pl.EffectiveDate = '2024-01-01';
```

## DELETE Syntax

```sql
DELETE FROM table_name
WHERE condition;
```

### Simple DELETE

```sql
-- Delete discontinued products
DELETE FROM Products
WHERE Discontinued = 1;

-- Delete old orders
DELETE FROM Orders
WHERE OrderDate < '1996-01-01';
```

⚠️ **Without WHERE, deletes ALL rows:**

```sql
-- DANGER: Deletes every customer!
DELETE FROM Customers;
```

## DELETE with JOIN

```sql
-- Delete orders from specific customer
DELETE o
FROM Orders o
    INNER JOIN Customers c ON o.CustomerID = c.CustomerID
WHERE c.Country = 'France' AND o.OrderDate < '1997-01-01';
```

## TRUNCATE vs DELETE

**DELETE:**
- Removes rows one by one
- Can have WHERE clause
- Logged (can rollback)
- Triggers fire
- Slower

**TRUNCATE:**
- Removes all rows instantly
- No WHERE clause
- Minimally logged
- Triggers don't fire
- Much faster
- Resets IDENTITY

```sql
-- Delete all (slow, logged)
DELETE FROM TempTable;

-- Truncate (fast, minimal logging)
TRUNCATE TABLE TempTable;
```

**When to use TRUNCATE:**
- Clearing staging tables
- Deleting ALL rows
- No foreign key references

## UPDATE with Subquery

```sql
-- Set product price to category average
UPDATE Products
SET UnitPrice = (
    SELECT AVG(UnitPrice)
    FROM Products p2
    WHERE p2.CategoryID = Products.CategoryID
)
WHERE UnitPrice IS NULL;
```

## OUTPUT Clause

```sql
-- See what was updated/deleted
UPDATE Products
SET UnitPrice = UnitPrice * 1.1
OUTPUT 
    deleted.ProductID,
    deleted.ProductName,
    deleted.UnitPrice AS OldPrice,
    inserted.UnitPrice AS NewPrice
WHERE CategoryID = 1;
```

**deleted** = old values, **inserted** = new values

```sql
-- Track deletions
DELETE FROM Orders
OUTPUT 
    deleted.OrderID,
    deleted.CustomerID,
    deleted.OrderDate
INTO OrdersArchive
WHERE OrderDate < '1996-01-01';
```

## Conditional UPDATE

```sql
-- Update based on conditions
UPDATE Products
SET UnitPrice = CASE 
    WHEN UnitPrice < 20 THEN UnitPrice * 1.15
    WHEN UnitPrice < 50 THEN UnitPrice * 1.10
    ELSE UnitPrice * 1.05
END
WHERE CategoryID = 1;
```

## Foreign Key Constraints

**Cascading deletes:**

```sql
-- If Orders has CASCADE DELETE on CustomerID:
DELETE FROM Customers WHERE CustomerID = 'ALFKI';
-- Also deletes all orders for that customer

-- Without CASCADE:
-- Error: Cannot delete due to foreign key constraint
```

**Safe pattern:**

```sql
-- Delete child records first
DELETE FROM [Order Details] WHERE OrderID = 10248;
DELETE FROM Orders WHERE OrderID = 10248;
```

## Big Data Context

**UPDATE/DELETE are expensive in data lakes:**

```sql
-- Traditional database (fast):
UPDATE orders SET status = 'shipped' WHERE order_id = 123;

-- Data lake (expensive):
-- - Parquet files are immutable
-- - Must rewrite entire partition
-- - Can take minutes for large partitions
```

**Delta Lake/Iceberg** provide efficient UPDATE/DELETE:
- Copy-on-write or merge-on-read
- Row-level updates without full rewrite
- ACID transactions

**Best practice:** Append new records instead of UPDATE:

```sql
-- Instead of UPDATE:
UPDATE customer SET address = 'new' WHERE id = 1;

-- Append new version:
INSERT INTO customer VALUES (1, 'new', '2024-01-15', current_version + 1);
-- Query with: WHERE id = 1 ORDER BY version DESC LIMIT 1
```

## Practice Exercises

```sql
-- 1. Increase prices of out-of-stock products by 5%
UPDATE Products
SET UnitPrice = UnitPrice * 1.05
WHERE UnitsInStock = 0;

-- 2. Delete categories with no products
DELETE FROM Categories
WHERE CategoryID NOT IN (SELECT DISTINCT CategoryID FROM Products);

-- 3. Update employee titles
UPDATE Employees
SET Title = 'Senior ' + Title
WHERE HireDate < '1993-01-01';

-- 4. Clear staging table
TRUNCATE TABLE StagingOrders;
```

## Key Takeaways

- UPDATE modifies existing rows, DELETE removes them
- Always use WHERE (or affect all rows!)
- T-SQL supports UPDATE/DELETE with JOINs
- TRUNCATE faster than DELETE for removing all rows
- OUTPUT clause captures old/new values
- Foreign keys can CASCADE deletes
- In data lakes: UPDATE/DELETE expensive, prefer appends

## What's Next?

[Next: MERGE (UPSERT) →](03-merge-upsert.md)

---

[← Back: INSERT](01-insert.md) | [Course Home](../README.md) | [Next: MERGE →](03-merge-upsert.md)
