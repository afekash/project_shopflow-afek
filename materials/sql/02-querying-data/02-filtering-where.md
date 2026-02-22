# Filtering with WHERE

## Overview

The `WHERE` clause filters rows based on conditions. It's executed early in the query pipeline (before GROUP BY and SELECT), making it crucial for performance optimization.

## Core Concepts

### Basic WHERE Syntax

```sql
SELECT columns
FROM table
WHERE condition;
```

### Comparison Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `=` | Equal | `WHERE Country = 'USA'` |
| `<>` or `!=` | Not equal | `WHERE Country <> 'USA'` |
| `>` | Greater than | `WHERE UnitPrice > 50` |
| `>=` | Greater or equal | `WHERE UnitPrice >= 50` |
| `<` | Less than | `WHERE UnitPrice < 20` |
| `<=` | Less or equal | `WHERE UnitPrice <= 20` |

### Example 1: Simple Filtering

```sql
-- Find expensive products
SELECT ProductName, UnitPrice
FROM Products
WHERE UnitPrice > 50;
```

**Result:** 12 products with price > $50

### Example 2: Text Matching

```sql
-- Find German customers
SELECT CompanyName, City
FROM Customers
WHERE Country = 'Germany';
```

**Note:** String comparisons are case-insensitive by default in SQL Server (depends on collation).

### Example 3: BETWEEN Operator

Inclusive range checking:

```sql
-- Products priced between $20 and $50
SELECT ProductName, UnitPrice
FROM Products
WHERE UnitPrice BETWEEN 20 AND 50;

-- Equivalent to:
WHERE UnitPrice >= 20 AND UnitPrice <= 50;
```

**Pro tip:** `BETWEEN` is inclusive on both ends.

### Example 4: IN Operator

Match against a list of values:

```sql
-- Orders shipped to USA, Canada, or Mexico
SELECT OrderID, CustomerID, ShipCountry
FROM Orders
WHERE ShipCountry IN ('USA', 'Canada', 'Mexico');

-- Equivalent to:
WHERE ShipCountry = 'USA' 
   OR ShipCountry = 'Canada' 
   OR ShipCountry = 'Mexico';
```

### Example 5: LIKE Operator (Pattern Matching)

Use wildcards for partial matches:

- `%` - Any sequence of characters (0 or more)
- `_` - Exactly one character
- `[]` - Any single character in the set
- `[^]` - Any single character NOT in the set

```sql
-- Products starting with 'Ch'
SELECT ProductName
FROM Products
WHERE ProductName LIKE 'Ch%';
-- Results: Chai, Chang, Chef Anton's Gumbo Mix, etc.

-- Products with 'chocolate' anywhere in the name
SELECT ProductName
FROM Products
WHERE ProductName LIKE '%chocolate%';
-- Results: Chocolade, Gumbär Gummibärchen, etc.

-- Products with exactly 5 characters
SELECT ProductName
FROM Products
WHERE ProductName LIKE '_____';  -- Five underscores

-- Products starting with C, H, or T
SELECT ProductName
FROM Products
WHERE ProductName LIKE '[CHT]%';
```

### Example 6: NULL Handling

`NULL` represents missing or unknown data. It requires special operators:

```sql
-- Products without a region supplier
SELECT ProductName, SupplierID
FROM Products
WHERE SupplierID IS NULL;  -- IS NULL, not = NULL

-- Products with a region supplier
SELECT ProductName, SupplierID
FROM Products
WHERE SupplierID IS NOT NULL;
```

**⚠️ Common mistake:**

```sql
-- ❌ WRONG: This returns no rows (NULL = NULL is always UNKNOWN)
WHERE SupplierID = NULL;

-- ✅ CORRECT: Use IS NULL
WHERE SupplierID IS NULL;
```

### Example 7: Boolean Logic (AND, OR, NOT)

Combine multiple conditions:

```sql
-- Expensive beverage products
SELECT ProductName, UnitPrice, CategoryID
FROM Products
WHERE CategoryID = 1 AND UnitPrice > 15;

-- Products that are either discontinued OR out of stock
SELECT ProductName, UnitsInStock, Discontinued
FROM Products
WHERE Discontinued = 1 OR UnitsInStock = 0;

-- Active products that are NOT beverages
SELECT ProductName, CategoryID
FROM Products
WHERE Discontinued = 0 AND CategoryID <> 1;
```

**Operator precedence:** `NOT > AND > OR`

```sql
-- This might not do what you expect!
WHERE Country = 'USA' OR Country = 'Canada' AND City = 'Vancouver'
-- Interpreted as: USA OR (Canada AND Vancouver)

-- Use parentheses for clarity:
WHERE (Country = 'USA' OR Country = 'Canada') AND City = 'Vancouver'
```

## Advanced Insights

### SARGability (Search ARGument ABLE)

**SARGable** queries can use indexes efficiently. Non-SARGable queries force table scans.

#### ❌ Non-SARGable (BAD)

```sql
-- Functions on indexed columns prevent index usage
WHERE YEAR(OrderDate) = 1997;  -- Can't use index on OrderDate
WHERE UPPER(Country) = 'USA';  -- Can't use index on Country
WHERE UnitPrice * 1.2 > 50;    -- Can't use index on UnitPrice
```

These force the database to:
1. Read EVERY row
2. Apply the function to the column
3. Check the condition

#### ✅ SARGable (GOOD)

```sql
-- Rewrite to isolate the column
WHERE OrderDate >= '1997-01-01' 
  AND OrderDate < '1998-01-01';  -- Index can be used!

-- Use case-insensitive collation or computed column
WHERE Country = 'USA' COLLATE SQL_Latin1_General_CP1_CI_AS;

-- Isolate the column
WHERE UnitPrice > 50 / 1.2;  -- UnitPrice > 41.67
```

**Performance impact:**
- Non-SARGable: 830 row table scan (slower)
- SARGable: Index seek to ~100 rows (faster)

In data warehouses with billions of rows, non-SARGable queries can be **100-1000x slower**.

### NULL Logic (Three-Valued Logic)

SQL uses three-valued logic: `TRUE`, `FALSE`, `UNKNOWN`

```sql
-- Consider UnitsOnOrder can be NULL
WHERE UnitsInStock > UnitsOnOrder;

-- If UnitsOnOrder is NULL:
-- 50 > NULL → UNKNOWN (not TRUE, row is excluded!)
```

**Comparison results:**

| Expression | Result |
|------------|--------|
| `NULL = NULL` | UNKNOWN |
| `NULL <> NULL` | UNKNOWN |
| `NULL > 5` | UNKNOWN |
| `5 > NULL` | UNKNOWN |

**WHERE clause behavior:** Only rows where condition is `TRUE` are returned (UNKNOWN rows are excluded)

**Handling NULLs:**

```sql
-- Include rows where UnitsOnOrder is NULL or zero
WHERE UnitsOnOrder IS NULL OR UnitsOnOrder = 0;

-- Treat NULL as zero
WHERE COALESCE(UnitsOnOrder, 0) = 0;
```

### Short-Circuit Evaluation

SQL optimizers may (but aren't required to) short-circuit boolean expressions:

```sql
-- If Country check is FALSE, the expensive function might not run
WHERE Country = 'USA' AND some_expensive_function(ProductID) = 1;
```

**However:** Don't rely on order! The optimizer may rearrange conditions.

**Safer approach:**

```sql
-- Use CASE to guarantee order
WHERE CASE 
    WHEN Country = 'USA' THEN some_expensive_function(ProductID)
    ELSE 0
END = 1;
```

## Big Data Context

### Predicate Pushdown

Modern query engines push WHERE conditions as close to the data as possible:

```sql
SELECT ProductName, UnitPrice
FROM Products
WHERE CategoryID = 1 AND UnitPrice > 20;
```

**In distributed systems:**
1. **File-level pruning** - Skip entire files/partitions where predicate is false
2. **Row group pruning** - In Parquet, skip row groups using min/max statistics
3. **Late materialization** - Check predicates before reading all columns

**Example:** Query 1 billion row Parquet table partitioned by date:

```sql
WHERE OrderDate >= '2024-01-01' AND OrderDate < '2024-02-01';
```

- Without predicate pushdown: Read 1 billion rows
- With partition pruning: Read only January partition (~80 million rows)
- With row group pruning: Read only relevant row groups (~50 million rows)

**92% I/O savings!**

### Partition Pruning

Data lakes partition tables by columns (usually date):

```
/orders/year=2023/month=01/
/orders/year=2023/month=02/
/orders/year=2024/month=01/
```

```sql
-- Only reads year=2024 partitions
SELECT * FROM orders WHERE year = 2024;

-- ❌ Can't prune: function on partition column
WHERE YEAR(order_date) = 2024;  -- Scans all partitions!

-- ✅ Can prune: isolated column
WHERE year = 2024;
```

### Approximate Filters (Bloom Filters)

> **Core Concept:** See [Probabilistic Structures](../../core-concepts/02-data-structures/04-probabilistic-structures.md) for how bloom filters work -- the bit array, hash functions, no false negatives, bounded false positive rate.

In big data, checking if a value exists can be expensive. **Bloom filters** provide fast, probabilistic membership tests. The key property: a bloom filter can tell you with certainty that a value is *not* in the set (no false negatives), but only probabilistically that it *is* (small false positive rate). This makes them ideal as a pre-filter -- use the bloom filter to skip rows that definitely won't match, then apply the exact filter only to the survivors.

```sql
-- Traditional (slow on huge tables):
WHERE customer_id IN (SELECT id FROM customers WHERE country = 'USA');

-- With bloom filter (fast):
-- 1. Build bloom filter from USA customers (small)
-- 2. Broadcast to all nodes
-- 3. Filter rows locally before shuffle (bloom filter eliminates definite non-matches)
-- 4. Exact filter applied to remaining candidates
-- Result: 95%+ reduction in shuffle data
```

## Practical Examples

### Example 1: Complex Product Search

```sql
-- Find active, expensive products from specific categories
SELECT 
    ProductName,
    UnitPrice,
    CategoryID,
    UnitsInStock
FROM Products
WHERE Discontinued = 0
    AND UnitPrice BETWEEN 20 AND 100
    AND CategoryID IN (1, 2, 4)  -- Beverages, Condiments, Dairy
    AND UnitsInStock > 10
ORDER BY UnitPrice DESC;
```

### Example 2: Date Filtering (SARGable)

```sql
-- Orders from 1997 (proper way)
SELECT OrderID, CustomerID, OrderDate
FROM Orders
WHERE OrderDate >= '1997-01-01' 
    AND OrderDate < '1998-01-01';

-- Orders from Q4 1997
SELECT OrderID, CustomerID, OrderDate
FROM Orders
WHERE OrderDate >= '1997-10-01' 
    AND OrderDate < '1998-01-01';
```

### Example 3: Text Search with Multiple Patterns

```sql
-- Products with 'sauce', 'syrup', or 'spread' in the name
SELECT ProductName, CategoryID
FROM Products
WHERE ProductName LIKE '%sauce%'
   OR ProductName LIKE '%syrup%'
   OR ProductName LIKE '%spread%';
```

### Example 4: NULL-Safe Comparisons

```sql
-- Find customers without a region specified
SELECT CustomerID, CompanyName, Region
FROM Customers
WHERE Region IS NULL;

-- Find customers WITH a region
SELECT CustomerID, CompanyName, Region
FROM Customers
WHERE Region IS NOT NULL;

-- Find customers in specific regions OR no region
SELECT CustomerID, CompanyName, Region
FROM Customers
WHERE Region IN ('WA', 'CA', 'OR') OR Region IS NULL;
```

## Practice Exercises

1. Find all products with "chef" or "chef's" in the name (case-insensitive)
2. Get orders from the first half of 1997 (Jan-Jun) - use SARGable predicates
3. Find customers from USA with no region specified
4. Get products that are either discontinued OR have zero units in stock
5. Find orders with freight cost between $50 and $100, shipped to France or Germany

### Solutions

```sql
-- Exercise 1
SELECT ProductName FROM Products
WHERE ProductName LIKE '%chef%';

-- Exercise 2
SELECT OrderID, OrderDate FROM Orders
WHERE OrderDate >= '1997-01-01' AND OrderDate < '1997-07-01';

-- Exercise 3
SELECT CustomerID, CompanyName FROM Customers
WHERE Country = 'USA' AND Region IS NULL;

-- Exercise 4
SELECT ProductName, Discontinued, UnitsInStock FROM Products
WHERE Discontinued = 1 OR UnitsInStock = 0;

-- Exercise 5
SELECT OrderID, Freight, ShipCountry FROM Orders
WHERE Freight BETWEEN 50 AND 100
    AND ShipCountry IN ('France', 'Germany');
```

## Key Takeaways

- `WHERE` filters rows early in query execution (before GROUP BY)
- Use `=`, `<>`, `<`, `>`, `BETWEEN`, `IN`, `LIKE` for comparisons
- `NULL` requires `IS NULL` / `IS NOT NULL` (not `=` or `<>`)
- **SARGability** is critical: avoid functions on indexed columns
- Boolean logic: `NOT > AND > OR` (use parentheses for clarity)
- Predicate pushdown enables massive I/O savings in data lakes
- Partition pruning is essential for big data query performance
- Three-valued logic: `TRUE`, `FALSE`, `UNKNOWN` (WHERE returns only TRUE rows)

## What's Next?

Learn how to sort your filtered results:

[Next: Sorting with ORDER BY →](03-sorting-order-by.md)

---

[← Back: SELECT Basics](01-select-basics.md) | [Course Home](../README.md) | [Next: Sorting with ORDER BY →](03-sorting-order-by.md)
