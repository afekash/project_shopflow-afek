# MERGE (UPSERT)

## Overview

MERGE performs INSERT, UPDATE, or DELETE in a single statement based on matching conditions. Essential for data synchronization and ETL.

Also called **UPSERT** (UPDATE or INSERT).

## Basic Syntax

```sql
MERGE target_table AS target
USING source_table AS source
ON target.key = source.key
WHEN MATCHED THEN
    UPDATE SET target.col = source.col
WHEN NOT MATCHED BY TARGET THEN
    INSERT (col1, col2) VALUES (source.col1, source.col2)
WHEN NOT MATCHED BY SOURCE THEN
    DELETE;
```

## Simple MERGE Example

```sql
-- Synchronize product prices from import table
MERGE Products AS target
USING ProductPriceUpdates AS source
ON target.ProductID = source.ProductID
WHEN MATCHED THEN
    UPDATE SET target.UnitPrice = source.NewPrice
WHEN NOT MATCHED BY TARGET THEN
    INSERT (ProductID, ProductName, UnitPrice)
    VALUES (source.ProductID, source.ProductName, source.NewPrice);
```

**What happens:**
- If ProductID exists: UPDATE price
- If ProductID doesn't exist: INSERT new product
- Returns count of affected rows

## MERGE with DELETE

```sql
-- Sync categories: update existing, insert new, delete removed
MERGE Categories AS target
USING StagingCategories AS source
ON target.CategoryID = source.CategoryID
WHEN MATCHED THEN
    UPDATE SET 
        target.CategoryName = source.CategoryName,
        target.Description = source.Description
WHEN NOT MATCHED BY TARGET THEN
    INSERT (CategoryName, Description)
    VALUES (source.CategoryName, source.Description)
WHEN NOT MATCHED BY SOURCE THEN
    DELETE;  -- Remove categories not in source
```

## Conditional MERGE

```sql
-- Only update if price changed
MERGE Products AS target
USING ProductUpdates AS source
ON target.ProductID = source.ProductID
WHEN MATCHED AND target.UnitPrice <> source.UnitPrice THEN
    UPDATE SET target.UnitPrice = source.UnitPrice
WHEN NOT MATCHED THEN
    INSERT (ProductID, ProductName, UnitPrice)
    VALUES (source.ProductID, source.ProductName, source.UnitPrice);
```

## MERGE with OUTPUT

Track what happened:

```sql
MERGE Products AS target
USING ProductUpdates AS source
ON target.ProductID = source.ProductID
WHEN MATCHED THEN
    UPDATE SET target.UnitPrice = source.UnitPrice
WHEN NOT MATCHED THEN
    INSERT (ProductID, ProductName, UnitPrice)
    VALUES (source.ProductID, source.ProductName, source.UnitPrice)
OUTPUT 
    $action AS Action,  -- 'INSERT', 'UPDATE', or 'DELETE'
    inserted.ProductID,
    inserted.UnitPrice AS NewPrice,
    deleted.UnitPrice AS OldPrice;
```

## MERGE from Query

```sql
-- Source can be a query, not just a table
MERGE CustomerSummary AS target
USING (
    SELECT 
        CustomerID,
        COUNT(*) AS OrderCount,
        SUM(Freight) AS TotalFreight
    FROM Orders
    GROUP BY CustomerID
) AS source
ON target.CustomerID = source.CustomerID
WHEN MATCHED THEN
    UPDATE SET 
        target.OrderCount = source.OrderCount,
        target.TotalFreight = source.TotalFreight
WHEN NOT MATCHED THEN
    INSERT (CustomerID, OrderCount, TotalFreight)
    VALUES (source.CustomerID, source.OrderCount, source.TotalFreight);
```

## UPSERT Pattern (Before MERGE)

**Pre-SQL Server 2008:**

```sql
-- Check if exists, then INSERT or UPDATE
IF EXISTS (SELECT 1 FROM Products WHERE ProductID = @id)
    UPDATE Products SET UnitPrice = @price WHERE ProductID = @id;
ELSE
    INSERT INTO Products (ProductID, UnitPrice) VALUES (@id, @price);
```

**Better:** Use MERGE (atomic, no race conditions).

## Alternative: INSERT...ON DUPLICATE KEY UPDATE

MySQL syntax (SQL Server doesn't support):

```sql
-- MySQL only
INSERT INTO Products (ProductID, ProductName, UnitPrice)
VALUES (1, 'Chai', 19.00)
ON DUPLICATE KEY UPDATE UnitPrice = 19.00;
```

**SQL Server equivalent:** MERGE

## Real-World Example: SCD Type 1

```sql
-- Slowly Changing Dimension Type 1 (overwrite)
MERGE DimCustomer AS target
USING StagingCustomer AS source
ON target.CustomerID = source.CustomerID
WHEN MATCHED AND (
    target.CompanyName <> source.CompanyName OR
    target.City <> source.City OR
    target.Country <> source.Country
) THEN
    UPDATE SET 
        target.CompanyName = source.CompanyName,
        target.City = source.City,
        target.Country = source.Country,
        target.LastModified = GETDATE()
WHEN NOT MATCHED BY TARGET THEN
    INSERT (CustomerID, CompanyName, City, Country, LastModified)
    VALUES (source.CustomerID, source.CompanyName, source.City, source.Country, GETDATE());
```

## Performance Considerations

**MERGE can be slow:**
- Requires matching logic (join)
- Multiple operations in one statement
- Can cause locking issues

**Alternatives for bulk operations:**
- Separate INSERT (for new rows) and UPDATE (for existing)
- Bulk INSERT + UPDATE with EXISTS check
- Consider staging table approach

## Big Data Context

**MERGE in data lakes** (Delta Lake, Iceberg):

```sql
-- Delta Lake MERGE (Spark SQL)
MERGE INTO target_table
USING source_table
ON target_table.id = source_table.id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

**Use cases:**
- **CDC** (Change Data Capture) replication
- **Deduplication** in streaming pipelines
- **SCD Type 1/2** in data warehouses

**Performance:** Can be expensive - requires scanning target table and source.

**Optimization:**
- Partition target table
- Use Z-ordering/clustering on merge keys
- Batch updates (don't merge every record individually)

## Practice Exercises

```sql
-- 1. Simple upsert for shippers
MERGE Shippers AS target
USING (VALUES (1, 'Speedy Express', '503-555-9831')) AS source (ShipperID, CompanyName, Phone)
ON target.ShipperID = source.ShipperID
WHEN MATCHED THEN
    UPDATE SET Phone = source.Phone
WHEN NOT MATCHED THEN
    INSERT (CompanyName, Phone) VALUES (source.CompanyName, source.Phone);

-- 2. Sync categories from staging
CREATE TABLE StagingCategories (CategoryID INT, CategoryName NVARCHAR(15));
INSERT INTO StagingCategories VALUES (1, 'Beverages'), (9, 'New Category');

MERGE Categories AS target
USING StagingCategories AS source
ON target.CategoryID = source.CategoryID
WHEN MATCHED THEN
    UPDATE SET target.CategoryName = source.CategoryName
WHEN NOT MATCHED THEN
    INSERT (CategoryName) VALUES (source.CategoryName);

-- 3. Conditional merge with output
MERGE Products AS target
USING (SELECT 1 AS ProductID, 20.00 AS UnitPrice) AS source
ON target.ProductID = source.ProductID
WHEN MATCHED AND target.UnitPrice <> source.UnitPrice THEN
    UPDATE SET target.UnitPrice = source.UnitPrice
OUTPUT $action, inserted.ProductID, deleted.UnitPrice, inserted.UnitPrice;
```

## Key Takeaways

- MERGE = INSERT, UPDATE, DELETE in one statement
- Used for synchronization and ETL
- `WHEN MATCHED` - row exists in target
- `WHEN NOT MATCHED BY TARGET` - insert new
- `WHEN NOT MATCHED BY SOURCE` - delete removed
- OUTPUT with `$action` shows what happened
- Essential for SCD patterns in warehouses
- Delta Lake/Iceberg support MERGE for data lakes

## What's Next?

[Next: Transactions →](04-transactions.md)

---

[← Back: UPDATE/DELETE](02-update-delete.md) | [Course Home](../README.md) | [Next: Transactions →](04-transactions.md)
