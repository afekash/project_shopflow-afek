# DDL Basics

## Overview

DDL (Data Definition Language) creates and modifies database objects: tables, views, indexes, constraints.

## CREATE TABLE

```sql
CREATE TABLE Products (
    ProductID INT PRIMARY KEY IDENTITY(1,1),
    ProductName NVARCHAR(40) NOT NULL,
    CategoryID INT,
    UnitPrice MONEY DEFAULT 0,
    UnitsInStock SMALLINT,
    Discontinued BIT DEFAULT 0
);
```

### Data Types

**Numeric:**
- `INT`, `BIGINT`, `SMALLINT`, `TINYINT`
- `DECIMAL(p,s)`, `NUMERIC(p,s)`
- `MONEY`, `SMALLMONEY`
- `FLOAT`, `REAL`

**String:**
- `VARCHAR(n)` - Variable ASCII
- `NVARCHAR(n)` - Variable Unicode
- `CHAR(n)` - Fixed ASCII
- `TEXT`, `NTEXT` (deprecated, use VARCHAR(MAX))

**Date/Time:**
- `DATE`, `TIME`, `DATETIME`, `DATETIME2`
- `SMALLDATETIME`, `DATETIMEOFFSET`

**Binary:**
- `BINARY(n)`, `VARBINARY(n)`, `IMAGE`

**Other:**
- `BIT` - Boolean
- `UNIQUEIDENTIFIER` - GUID
- `XML`, `JSON` (NVARCHAR with validation)

## Constraints

### PRIMARY KEY

```sql
-- Single column
CREATE TABLE Categories (
    CategoryID INT PRIMARY KEY,
    CategoryName NVARCHAR(15)
);

-- Composite key
CREATE TABLE OrderDetails (
    OrderID INT,
    ProductID INT,
    Quantity INT,
    PRIMARY KEY (OrderID, ProductID)
);
```

### FOREIGN KEY

```sql
CREATE TABLE Products (
    ProductID INT PRIMARY KEY,
    CategoryID INT,
    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID)
);

-- With cascade
CREATE TABLE Orders (
    OrderID INT PRIMARY KEY,
    CustomerID NCHAR(5),
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
        ON DELETE CASCADE  -- Delete orders when customer deleted
        ON UPDATE CASCADE  -- Update OrderID if customer ID changes
);
```

### UNIQUE

```sql
CREATE TABLE Employees (
    EmployeeID INT PRIMARY KEY,
    Email NVARCHAR(100) UNIQUE,  -- No duplicates
    SSN CHAR(11) UNIQUE
);
```

### CHECK

```sql
CREATE TABLE Products (
    ProductID INT PRIMARY KEY,
    UnitPrice MONEY CHECK (UnitPrice >= 0),  -- Price must be positive
    UnitsInStock INT CHECK (UnitsInStock >= 0),
    ReorderLevel INT,
    CHECK (ReorderLevel <= UnitsInStock)  -- Table-level constraint
);
```

### DEFAULT

```sql
CREATE TABLE Orders (
    OrderID INT PRIMARY KEY,
    OrderDate DATETIME DEFAULT GETDATE(),  -- Defaults to current date
    Freight MONEY DEFAULT 0,
    Status NVARCHAR(20) DEFAULT 'Pending'
);
```

### NOT NULL

```sql
CREATE TABLE Customers (
    CustomerID NCHAR(5) PRIMARY KEY,
    CompanyName NVARCHAR(40) NOT NULL,  -- Required
    ContactName NVARCHAR(30),  -- Optional (allows NULL)
    Country NVARCHAR(15) NOT NULL
);
```

## CREATE TABLE AS SELECT (CTAS)

```sql
-- Create table from query
SELECT ProductID, ProductName, UnitPrice
INTO ExpensiveProducts
FROM Products
WHERE UnitPrice > 50;
```

**Note:** Doesn't copy constraints or indexes.

## DROP TABLE

```sql
DROP TABLE IF EXISTS TempTable;
```

⚠️ **Permanent** - no undo!

## Temporary Tables

**Local temp table** (session-specific):

```sql
CREATE TABLE #TempProducts (
    ProductID INT,
    ProductName NVARCHAR(40)
);

INSERT INTO #TempProducts SELECT ProductID, ProductName FROM Products WHERE UnitPrice > 50;

SELECT * FROM #TempProducts;

-- Automatically dropped when session ends
```

**Global temp table** (all sessions):

```sql
CREATE TABLE ##GlobalTemp (
    ID INT,
    Value NVARCHAR(50)
);

-- Dropped when last session using it disconnects
```

## Table Variables

```sql
DECLARE @Products TABLE (
    ProductID INT,
    ProductName NVARCHAR(40),
    UnitPrice MONEY
);

INSERT INTO @Products
SELECT ProductID, ProductName, UnitPrice
FROM Products
WHERE CategoryID = 1;

SELECT * FROM @Products;
```

**vs Temp Tables:**
- Table variables: Faster for small datasets, no statistics
- Temp tables: Better for large datasets, has statistics, can be indexed

## Computed Columns

```sql
CREATE TABLE OrderDetails (
    OrderID INT,
    ProductID INT,
    UnitPrice MONEY,
    Quantity INT,
    Discount REAL,
    LineTotal AS (UnitPrice * Quantity * (1 - Discount))  -- Computed
);

-- Persisted (stored on disk)
LineTotal AS (UnitPrice * Quantity * (1 - Discount)) PERSISTED
```

## Big Data Context

**Data lake table creation:**

```sql
-- Hive/Spark: CREATE TABLE with format
CREATE EXTERNAL TABLE products (
    product_id INT,
    product_name STRING,
    price DECIMAL(10,2)
)
PARTITIONED BY (category STRING)
STORED AS PARQUET
LOCATION 's3://bucket/products/';
```

**Key differences:**
- Schema-on-read vs schema-on-write
- External tables (data in S3/ADLS, schema in metastore)
- File format matters (Parquet, ORC, Avro)
- Partitioning critical for performance

## Practice Exercises

```sql
-- 1. Create customers table
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY IDENTITY(1,1),
    CompanyName NVARCHAR(40) NOT NULL,
    Email NVARCHAR(100) UNIQUE,
    Country NVARCHAR(15) DEFAULT 'USA',
    CreditLimit MONEY CHECK (CreditLimit > 0)
);

-- 2. Temp table for analysis
CREATE TABLE #HighValueOrders (
    OrderID INT,
    CustomerID NCHAR(5),
    TotalValue MONEY
);

INSERT INTO #HighValueOrders
SELECT o.OrderID, o.CustomerID, SUM(od.Quantity * od.UnitPrice)
FROM Orders o
JOIN [Order Details] od ON o.OrderID = od.OrderID
GROUP BY o.OrderID, o.CustomerID
HAVING SUM(od.Quantity * od.UnitPrice) > 1000;

-- 3. Create table from query
SELECT CategoryID, COUNT(*) AS ProductCount
INTO CategoryStats
FROM Products
GROUP BY CategoryID;
```

## Key Takeaways

- CREATE TABLE defines structure and constraints
- PRIMARY KEY uniquely identifies rows
- FOREIGN KEY enforces referential integrity
- UNIQUE, CHECK, DEFAULT, NOT NULL constrain data
- Temp tables (#) for session-specific data
- CTAS (SELECT INTO) creates table from query
- Computed columns derive values from other columns
- Data lakes use external tables with file formats

## What's Next?

[Next: ALTER TABLE →](02-alter-table.md)

---

[← Back: Transactions](../08-data-manipulation/04-transactions.md) | [Course Home](../README.md) | [Next: ALTER TABLE →](02-alter-table.md)
