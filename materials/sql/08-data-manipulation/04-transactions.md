# Transactions

## Overview

Transactions group multiple SQL statements into a single unit of work. Either all succeed (COMMIT) or all fail (ROLLBACK). Foundation of **ACID** properties.

## ACID Properties

> **Core Concept:** See [ACID vs BASE](../../core-concepts/04-distributed-systems/02-acid-vs-base.md) for the full theory -- ACID vs BASE as opposing philosophies, pessimistic vs optimistic concurrency, and when each model fits.

SQL databases enforce ACID through a combination of:
- **Locking** (for isolation): reads and writes acquire locks to prevent concurrent interference
- **Write-ahead logging** (for durability and atomicity): every change is appended to the WAL before being applied, enabling crash recovery and rollback -- see [Write-Ahead Logs](../../core-concepts/05-replication-and-availability/03-write-ahead-logs.md)

The four properties:
- **Atomicity** - All or nothing
- **Consistency** - Database remains valid
- **Isolation** - Concurrent transactions don't interfere
- **Durability** - Committed changes persist

## Basic Transaction Syntax

```sql
BEGIN TRANSACTION;  -- or BEGIN TRAN

    -- SQL statements here
    UPDATE Accounts SET Balance = Balance - 100 WHERE AccountID = 1;
    UPDATE Accounts SET Balance = Balance + 100 WHERE AccountID = 2;

COMMIT;  -- Save changes
-- or ROLLBACK;  -- Undo changes
```

## Explicit Transaction Example

```sql
-- Transfer money between accounts
BEGIN TRANSACTION;

    UPDATE Accounts SET Balance = Balance - 500 WHERE AccountID = 1;
    
    -- Check if first account has sufficient funds
    IF (SELECT Balance FROM Accounts WHERE AccountID = 1) < 0
    BEGIN
        ROLLBACK;
        PRINT 'Insufficient funds';
        RETURN;
    END
    
    UPDATE Accounts SET Balance = Balance + 500 WHERE AccountID = 2;

COMMIT;
PRINT 'Transfer successful';
```

## TRY...CATCH with Transactions

```sql
BEGIN TRY
    BEGIN TRANSACTION;
    
        -- Delete order details first (foreign key)
        DELETE FROM [Order Details] WHERE OrderID = 10248;
        
        -- Then delete order
        DELETE FROM Orders WHERE OrderID = 10248;
        
    COMMIT;
    PRINT 'Order deleted successfully';
END TRY
BEGIN CATCH
    -- Error occurred, rollback
    IF @@TRANCOUNT > 0
        ROLLBACK;
    
    PRINT 'Error: ' + ERROR_MESSAGE();
END CATCH;
```

## SAVEPOINT (Nested Rollback)

```sql
BEGIN TRANSACTION;

    INSERT INTO Categories (CategoryName) VALUES ('Category 1');
    SAVE TRANSACTION SavePoint1;
    
    INSERT INTO Categories (CategoryName) VALUES ('Category 2');
    SAVE TRANSACTION SavePoint2;
    
    INSERT INTO Categories (CategoryName) VALUES ('Category 3');
    
    -- Rollback to SavePoint2 (undoes Category 3 only)
    ROLLBACK TRANSACTION SavePoint2;
    
COMMIT;  -- Commits Category 1 and 2
```

## Isolation Levels

> **Core Concept:** See [Consistency Models](../../core-concepts/04-distributed-systems/03-consistency-models.md) for the general consistency spectrum -- from linearizable (strongest) to eventual (weakest). Isolation levels are SQL's implementation of this spectrum for concurrent transactions within a single database.

Isolation levels are the SQL implementation of the general consistency spectrum. READ UNCOMMITTED offers the weakest guarantees (highest performance), SERIALIZABLE offers the strongest (lowest concurrency). The default (READ COMMITTED in most databases) is a pragmatic middle ground that eliminates the most harmful anomalies while maintaining reasonable concurrency.

Controls how transactions see changes from other transactions.

```sql
-- Set isolation level
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
-- Options:
-- - READ UNCOMMITTED (dirty reads allowed)
-- - READ COMMITTED (default)
-- - REPEATABLE READ
-- - SERIALIZABLE
-- - SNAPSHOT
```

### READ UNCOMMITTED

Lowest isolation, highest concurrency. Allows **dirty reads**.

```sql
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
SELECT * FROM Products;  -- May see uncommitted changes from other transactions
```

**Use case:** Reports where approximate data is acceptable.

### READ COMMITTED (Default)

Reads only committed data. Prevents dirty reads.

```sql
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
SELECT * FROM Orders;  -- Only sees committed data
```

**Issue:** Non-repeatable reads (same query returns different results within transaction).

### REPEATABLE READ

Prevents non-repeatable reads by locking rows.

```sql
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

BEGIN TRANSACTION;
    SELECT * FROM Products WHERE CategoryID = 1;
    -- Rows are locked; same SELECT will return same results
    SELECT * FROM Products WHERE CategoryID = 1;
COMMIT;
```

**Issue:** Phantom reads (new rows can appear).

### SERIALIZABLE

Highest isolation. Prevents phantom reads. Locks ranges.

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

BEGIN TRANSACTION;
    SELECT * FROM Products WHERE UnitPrice > 50;
    -- Range is locked; no new products >50 can be inserted by others
COMMIT;
```

**Issue:** Lowest concurrency, highest blocking.

### SNAPSHOT

Reads a consistent snapshot (row versioning).

```sql
ALTER DATABASE Northwind SET ALLOW_SNAPSHOT_ISOLATION ON;

SET TRANSACTION ISOLATION LEVEL SNAPSHOT;

BEGIN TRANSACTION;
    -- Sees database as it was at transaction start
    SELECT * FROM Products;
COMMIT;
```

**Benefit:** No blocking, consistent reads.  
**Cost:** TempDB overhead for row versions.

## Deadlocks

Two transactions wait for each other's locks.

**Example:**

```sql
-- Transaction 1
BEGIN TRANSACTION;
    UPDATE Products SET UnitPrice = 10 WHERE ProductID = 1;
    -- Waits for Transaction 2's lock on ProductID = 2
    UPDATE Products SET UnitPrice = 20 WHERE ProductID = 2;
COMMIT;

-- Transaction 2 (concurrent)
BEGIN TRANSACTION;
    UPDATE Products SET UnitPrice = 30 WHERE ProductID = 2;
    -- Waits for Transaction 1's lock on ProductID = 1
    UPDATE Products SET UnitPrice = 40 WHERE ProductID = 1;
COMMIT;
-- DEADLOCK! SQL Server picks a victim and rolls back one transaction
```

**Prevention:**
- Access tables in same order
- Keep transactions short
- Use appropriate isolation level

## Autocommit Mode

SQL Server default: each statement is its own transaction.

```sql
-- This is automatically committed
UPDATE Products SET UnitPrice = 10 WHERE ProductID = 1;
```

To use explicit transactions, use BEGIN TRANSACTION.

## Implicit Transactions

```sql
SET IMPLICIT_TRANSACTIONS ON;

-- No BEGIN TRANSACTION needed
UPDATE Products SET UnitPrice = 10 WHERE ProductID = 1;
-- Transaction is still open, must explicitly COMMIT or ROLLBACK
COMMIT;
```

**Not recommended** - prefer explicit BEGIN TRANSACTION.

## Checking Transaction State

```sql
-- Check if transaction is active
SELECT @@TRANCOUNT;  -- Returns number of open transactions

-- Get transaction ID
SELECT @@TRANID;
```

## Big Data Context

**Transactions in data warehouses:**

Traditional databases: ACID transactions on all operations

Data lakes (S3, ADLS): **No transactions** by default
- Parquet files are immutable
- No rollback capability
- Concurrent writes can overwrite

**Delta Lake / Apache Iceberg** add ACID transactions by implementing their own transaction logs -- the same write-ahead log concept applied to file-based storage. Before any write, a log entry is appended to the transaction log. On crash, the log is replayed. See [Write-Ahead Logs](../../core-concepts/05-replication-and-availability/03-write-ahead-logs.md) for the general principle.

```sql
-- Delta Lake example (same SQL, ACID guaranteed by the transaction log)
BEGIN TRANSACTION;
    DELETE FROM events WHERE date < '2020-01-01';
    INSERT INTO events SELECT * FROM new_events;
COMMIT;
```

**Trade-offs:**
- OLTP: Strong consistency, ACID, short transactions
- OLAP: Eventual consistency, batch loads, long-running queries

**Best practice for data lakes:**
- Atomic file operations
- Partition-level commits
- Idempotent operations (can rerun safely)

## Practice Exercises

```sql
-- 1. Safe order deletion
BEGIN TRY
    BEGIN TRANSACTION;
        DELETE FROM [Order Details] WHERE OrderID = 10250;
        DELETE FROM Orders WHERE OrderID = 10250;
    COMMIT;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    PRINT ERROR_MESSAGE();
END CATCH;

-- 2. Batch insert with savepoints
BEGIN TRANSACTION;
    INSERT INTO Categories (CategoryName) VALUES ('Cat1');
    SAVE TRANSACTION SP1;
    INSERT INTO Categories (CategoryName) VALUES ('Cat2');
    -- Rollback Cat2 if needed
    ROLLBACK TRANSACTION SP1;
COMMIT;

-- 3. Check for deadlocks
-- Run in separate windows simultaneously to create deadlock
-- Window 1:
BEGIN TRANSACTION;
UPDATE Products SET UnitPrice = 10 WHERE ProductID = 1;
WAITFOR DELAY '00:00:05';
UPDATE Products SET UnitPrice = 20 WHERE ProductID = 2;
COMMIT;

-- Window 2:
BEGIN TRANSACTION;
UPDATE Products SET UnitPrice = 30 WHERE ProductID = 2;
WAITFOR DELAY '00:00:05';
UPDATE Products SET UnitPrice = 40 WHERE ProductID = 1;
COMMIT;
```

## Key Takeaways

- Transactions ensure **ACID** properties
- `BEGIN TRANSACTION`, `COMMIT`, `ROLLBACK`
- Use TRY...CATCH for error handling
- **Isolation levels** balance consistency vs concurrency
- **Deadlocks** occur when transactions wait for each other
- Data lakes traditionally lack transactions (Delta/Iceberg add them)
- Keep transactions short for better concurrency

## What's Next?

[Next: Module 09 - Schema Design →](../09-schema-design/01-ddl-basics.md)

---

[← Back: MERGE](03-merge-upsert.md) | [Course Home](../README.md) | [Next: DDL Basics →](../09-schema-design/01-ddl-basics.md)
