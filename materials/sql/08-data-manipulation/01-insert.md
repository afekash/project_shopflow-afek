# INSERT

## Overview

INSERT adds new rows to tables. Three main patterns: single row, multiple rows, and INSERT...SELECT.

## Single Row INSERT

```sql
-- Insert one customer
INSERT INTO Customers (CustomerID, CompanyName, ContactName, Country)
VALUES ('NEWCO', 'New Company', 'John Doe', 'USA');
```

**Column list optional** if providing all columns in order:

```sql
-- Not recommended (fragile if schema changes)
INSERT INTO Shippers
VALUES ('Fast Delivery', '555-1234');
```

## Multiple Row INSERT

```sql
-- Insert multiple rows at once (SQL Server 2008+)
INSERT INTO Categories (CategoryName, Description)
VALUES 
    ('Frozen Foods', 'Frozen items'),
    ('Organic', 'Organic products'),
    ('Gluten-Free', 'Gluten-free items');
```

**Performance:** Much faster than individual INSERTs (single transaction, less overhead).

## INSERT...SELECT

Copy data from another table:

```sql
-- Create backup of discontinued products
INSERT INTO ProductsArchive (ProductID, ProductName, UnitPrice, Discontinued)
SELECT ProductID, ProductName, UnitPrice, Discontinued
FROM Products
WHERE Discontinued = 1;
```

### Cross-Table Population

```sql
-- Create summary table
CREATE TABLE CategorySummary (
    CategoryID INT,
    ProductCount INT,
    AvgPrice MONEY
);

-- Populate from aggregation
INSERT INTO CategorySummary
SELECT 
    CategoryID,
    COUNT(*),
    AVG(UnitPrice)
FROM Products
GROUP BY CategoryID;
```

## INSERT with DEFAULT and NULL

```sql
-- Use DEFAULT keyword for default values
INSERT INTO Products (ProductName, UnitPrice, UnitsInStock)
VALUES ('New Product', DEFAULT, 0);

-- Explicitly insert NULL
INSERT INTO Customers (CustomerID, CompanyName, Region)
VALUES ('TEST1', 'Test Company', NULL);
```

## INSERT INTO...SELECT INTO

**SELECT INTO** creates a new table:

```sql
-- Create new table with data
SELECT ProductID, ProductName, UnitPrice
INTO ExpensiveProducts
FROM Products
WHERE UnitPrice > 50;
```

**vs INSERT INTO** (table must exist):

```sql
-- Table must already exist
INSERT INTO ExpensiveProducts
SELECT ProductID, ProductName, UnitPrice
FROM Products
WHERE UnitPrice > 50;
```

## IDENTITY Columns

SQL Server auto-generates values:

```sql
-- Don't specify EmployeeID (it's IDENTITY)
INSERT INTO Employees (FirstName, LastName, Title)
VALUES ('Jane', 'Smith', 'Sales Rep');

-- Get the generated ID
SELECT SCOPE_IDENTITY() AS NewEmployeeID;
```

**Force explicit IDENTITY value:**

```sql
SET IDENTITY_INSERT Employees ON;

INSERT INTO Employees (EmployeeID, FirstName, LastName)
VALUES (100, 'John', 'Doe');

SET IDENTITY_INSERT Employees OFF;
```

## OUTPUT Clause

Return inserted values:

```sql
-- See what was inserted
INSERT INTO Categories (CategoryName, Description)
OUTPUT inserted.CategoryID, inserted.CategoryName
VALUES ('New Category', 'Description');

-- Capture into variable/table
DECLARE @NewIDs TABLE (ID INT, Name NVARCHAR(50));

INSERT INTO Categories (CategoryName, Description)
OUTPUT inserted.CategoryID, inserted.CategoryName INTO @NewIDs
VALUES ('Category A', 'Desc A'), ('Category B', 'Desc B');

SELECT * FROM @NewIDs;
```

## Big Data Context

**Batch INSERTs** in data lakes:

```sql
-- Traditional OLTP: many small INSERTs (row-by-row)
INSERT INTO orders VALUES (...);  -- 1 row
INSERT INTO orders VALUES (...);  -- 1 row

-- Data lake ETL: batch INSERT (millions of rows)
INSERT INTO orders_table
SELECT * FROM staging_orders;  -- Millions of rows in one operation
```

**Partitioning:** Insert into specific partitions:

```sql
-- Hive/Spark: INSERT with partition
INSERT INTO sales PARTITION (year=2024, month=1)
SELECT customer_id, amount, date FROM staging_sales
WHERE year = 2024 AND month = 1;
```

**Append-only pattern:** Data lakes rarely UPDATE - just INSERT new versions.

## Practice Exercises

```sql
-- 1. Insert a new shipper
INSERT INTO Shippers (CompanyName, Phone)
VALUES ('Express Ship', '555-9999');

-- 2. Insert multiple suppliers
INSERT INTO Suppliers (CompanyName, ContactName, Country)
VALUES 
    ('Supplier A', 'Contact A', 'USA'),
    ('Supplier B', 'Contact B', 'Canada');

-- 3. Copy cheap products to new table
SELECT *
INTO BudgetProducts
FROM Products
WHERE UnitPrice < 10;

-- 4. Insert aggregated data
CREATE TABLE EmployeeStats (
    EmployeeID INT,
    TotalOrders INT,
    TotalFreight MONEY
);

INSERT INTO EmployeeStats
SELECT EmployeeID, COUNT(*), SUM(Freight)
FROM Orders
GROUP BY EmployeeID;
```

## Key Takeaways

- INSERT adds new rows to tables
- Multiple row INSERT faster than individual inserts
- INSERT...SELECT copies data from queries
- SELECT INTO creates new table
- IDENTITY columns auto-generate values
- OUTPUT clause returns inserted data
- In data lakes: batch inserts, append-only pattern

## What's Next?

[Next: UPDATE and DELETE →](02-update-delete.md)

---

[← Back: Set Operations](../07-set-operations/01-set-operations.md) | [Course Home](../README.md) | [Next: UPDATE and DELETE →](02-update-delete.md)
