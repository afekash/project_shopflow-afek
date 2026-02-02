# ALTER TABLE

## Overview

ALTER TABLE modifies existing table structure: add/drop columns, modify data types, add/drop constraints.

## ADD COLUMN

```sql
-- Add single column
ALTER TABLE Products
ADD Barcode NVARCHAR(50);

-- Add with default
ALTER TABLE Products
ADD CreatedDate DATETIME DEFAULT GETDATE();

-- Add with NOT NULL (table must be empty OR provide default)
ALTER TABLE Products
ADD SKU NVARCHAR(20) NOT NULL DEFAULT 'TBD';
```

### Add Multiple Columns

```sql
ALTER TABLE Products
ADD 
    Weight DECIMAL(10,2),
    Dimensions NVARCHAR(50),
    LastModified DATETIME DEFAULT GETDATE();
```

## DROP COLUMN

```sql
ALTER TABLE Products
DROP COLUMN Barcode;

-- Drop multiple
ALTER TABLE Products
DROP COLUMN Weight, Dimensions;
```

⚠️ **Cannot drop** columns with constraints, indexes, or dependencies.

## MODIFY COLUMN (ALTER COLUMN)

```sql
-- Change data type
ALTER TABLE Products
ALTER COLUMN ProductName NVARCHAR(100);  -- Was NVARCHAR(40)

-- Change NULL/NOT NULL
ALTER TABLE Products
ALTER COLUMN Region NVARCHAR(15) NULL;  -- Allow NULLs

ALTER TABLE Products
ALTER COLUMN ProductName NVARCHAR(40) NOT NULL;  -- Require value
```

**Restrictions:**
- Cannot change if data incompatible
- Cannot change column with constraints
- Cannot change IDENTITY columns

## ADD Constraints

### PRIMARY KEY

```sql
-- Add primary key
ALTER TABLE Products
ADD CONSTRAINT PK_Products PRIMARY KEY (ProductID);
```

### FOREIGN KEY

```sql
-- Add foreign key
ALTER TABLE Products
ADD CONSTRAINT FK_Products_Categories
    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID);

-- With cascade
ALTER TABLE Orders
ADD CONSTRAINT FK_Orders_Customers
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
    ON DELETE CASCADE;
```

### CHECK

```sql
ALTER TABLE Products
ADD CONSTRAINT CK_Products_Price
    CHECK (UnitPrice >= 0);
```

### UNIQUE

```sql
ALTER TABLE Employees
ADD CONSTRAINT UQ_Employees_Email
    UNIQUE (Email);
```

### DEFAULT

```sql
ALTER TABLE Orders
ADD CONSTRAINT DF_Orders_Status
    DEFAULT 'Pending' FOR Status;
```

## DROP Constraints

```sql
-- Drop by name
ALTER TABLE Products
DROP CONSTRAINT FK_Products_Categories;

ALTER TABLE Products
DROP CONSTRAINT CK_Products_Price;

-- Drop PRIMARY KEY
ALTER TABLE Products
DROP CONSTRAINT PK_Products;
```

## Rename Objects

**sp_rename** (SQL Server):

```sql
-- Rename table
EXEC sp_rename 'OldTableName', 'NewTableName';

-- Rename column
EXEC sp_rename 'Products.ProductName', 'Name', 'COLUMN';

-- Rename constraint
EXEC sp_rename 'FK_Products_Categories', 'FK_Products_Cat';
```

## Practical Examples

### Evolve Schema Over Time

```sql
-- Add tracking columns
ALTER TABLE Products
ADD 
    CreatedBy NVARCHAR(50),
    CreatedDate DATETIME DEFAULT GETDATE(),
    ModifiedBy NVARCHAR(50),
    ModifiedDate DATETIME;

-- Add soft delete
ALTER TABLE Products
ADD IsDeleted BIT DEFAULT 0;
```

### Fix Data Type

```sql
-- Phone numbers stored as INT, need VARCHAR
-- 1. Add new column
ALTER TABLE Customers
ADD PhoneNew NVARCHAR(20);

-- 2. Copy data
UPDATE Customers
SET PhoneNew = CAST(Phone AS NVARCHAR);

-- 3. Drop old column
ALTER TABLE Customers
DROP COLUMN Phone;

-- 4. Rename new column
EXEC sp_rename 'Customers.PhoneNew', 'Phone', 'COLUMN';
```

### Add Computed Column

```sql
ALTER TABLE Products
ADD InventoryValue AS (UnitPrice * UnitsInStock) PERSISTED;
```

## Schema Versioning

```sql
-- Track schema version
CREATE TABLE SchemaVersion (
    Version INT PRIMARY KEY,
    AppliedDate DATETIME DEFAULT GETDATE(),
    Description NVARCHAR(200)
);

-- Migration script example
IF NOT EXISTS (SELECT 1 FROM SchemaVersion WHERE Version = 2)
BEGIN
    ALTER TABLE Products ADD Barcode NVARCHAR(50);
    INSERT INTO SchemaVersion (Version, Description)
    VALUES (2, 'Added Barcode column to Products');
END
```

## Caution: Production Changes

**Best practices:**
- Test in dev/staging first
- Backup database before ALTER
- Consider downtime/locking
- Use transactions when possible

```sql
BEGIN TRANSACTION;

ALTER TABLE Products
ADD NewColumn NVARCHAR(50);

-- Verify
IF COL_LENGTH('Products', 'NewColumn') IS NOT NULL
    COMMIT;
ELSE
    ROLLBACK;
```

## Big Data Context

**Schema evolution in data lakes:**

Traditional database:
```sql
ALTER TABLE products ADD color STRING;  -- Expensive: rewrites table
```

**Parquet (append-only):**
- New files have new schema
- Old files lack new column (read as NULL)
- Schema merging on read

**Delta Lake:**
```sql
-- Schema evolution automatic
INSERT INTO products (id, name, color)  -- 'color' is new
SELECT id, name, 'blue' FROM source;
-- Delta Lake updates schema automatically
```

**Hive/Spark:**
```sql
-- Add partition
ALTER TABLE sales ADD PARTITION (year=2024, month=1)
LOCATION 's3://bucket/sales/2024/01/';
```

**Best practice:** Design schema carefully upfront - changes expensive in data lakes.

## Practice Exercises

```sql
-- 1. Add audit columns
ALTER TABLE Products
ADD CreatedDate DATETIME DEFAULT GETDATE(),
    CreatedBy NVARCHAR(50);

-- 2. Add constraint
ALTER TABLE Products
ADD CONSTRAINT CK_Price_Positive CHECK (UnitPrice > 0);

-- 3. Modify column type
ALTER TABLE Customers
ALTER COLUMN Phone NVARCHAR(30);

-- 4. Add foreign key
ALTER TABLE Orders
ADD CONSTRAINT FK_Orders_Shippers
    FOREIGN KEY (ShipVia) REFERENCES Shippers(ShipperID);
```

## Key Takeaways

- ALTER TABLE modifies existing table structure
- ADD/DROP COLUMN changes columns
- ALTER COLUMN changes data type or NULL constraint
- ADD/DROP CONSTRAINT manages constraints
- sp_rename renames objects (SQL Server)
- Always test in non-production first
- Schema evolution easier in Delta Lake than raw Parquet
- In data lakes, partition management via ALTER TABLE

## What's Next?

[Next: Indexes →](03-indexes.md)

---

[← Back: DDL Basics](01-ddl-basics.md) | [Course Home](../README.md) | [Next: Indexes →](03-indexes.md)
