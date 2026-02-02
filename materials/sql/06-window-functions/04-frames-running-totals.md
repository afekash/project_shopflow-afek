# Window Frames and Running Totals

## Overview

Window **frames** define which rows within a partition to include in aggregate calculations. Essential for running totals, moving averages, and rolling calculations.

## Frame Syntax

```sql
function() OVER (
    [PARTITION BY ...]
    [ORDER BY ...]
    [ROWS | RANGE | GROUPS] BETWEEN frame_start AND frame_end
)
```

**Frame types:**
- `ROWS` - Physical row count
- `RANGE` - Logical range (value-based)
- `GROUPS` - Groups of tied values

## ROWS Frames

Physical offset from current row.

```sql
-- Running total of freight
SELECT 
    OrderID,
    OrderDate,
    Freight,
    SUM(Freight) OVER (
        ORDER BY OrderDate, OrderID
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS RunningTotal
FROM Orders;
```

**Frame boundaries:**
- `UNBOUNDED PRECEDING` - Start of partition
- `N PRECEDING` - N rows before current
- `CURRENT ROW` - Current row
- `N FOLLOWING` - N rows after current
- `UNBOUNDED FOLLOWING` - End of partition

## Moving Averages

```sql
-- 7-day moving average of order count
WITH DailyOrders AS (
    SELECT 
        CAST(OrderDate AS DATE) AS Date,
        COUNT(*) AS OrderCount
    FROM Orders
    GROUP BY CAST(OrderDate AS DATE)
)
SELECT 
    Date,
    OrderCount,
    AVG(OrderCount) OVER (
        ORDER BY Date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS MovingAvg7Day
FROM DailyOrders;
```

## Common Frame Patterns

### Cumulative Sum (Running Total)

```sql
SELECT 
    ProductID,
    ProductName,
    UnitPrice,
    SUM(UnitPrice) OVER (
        ORDER BY UnitPrice
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS CumulativePrice
FROM Products;
```

### Centered Moving Average

```sql
-- 3-value centered average (prev, current, next)
SELECT 
    OrderID,
    Freight,
    AVG(Freight) OVER (
        ORDER BY OrderID
        ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
    ) AS CenteredAvg
FROM Orders;
```

### Rolling Count

```sql
-- Count orders in last 30 days per customer
SELECT 
    CustomerID,
    OrderDate,
    COUNT(*) OVER (
        PARTITION BY CustomerID
        ORDER BY OrderDate
        RANGE BETWEEN INTERVAL '30' DAY PRECEDING AND CURRENT ROW
    ) AS OrdersLast30Days
FROM Orders;
```

## RANGE vs ROWS

**ROWS:** Physical row offset

```sql
-- Exactly 3 rows
ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
```

**RANGE:** Value-based (includes all rows with same ORDER BY value)

```sql
-- All rows with OrderDate within 7 days before current row
RANGE BETWEEN INTERVAL '7' DAY PRECEDING AND CURRENT ROW
```

### Example: RANGE with Ties

```sql
-- If multiple products have same price, RANGE includes all of them
SELECT 
    ProductName,
    UnitPrice,
    COUNT(*) OVER (
        ORDER BY UnitPrice
        RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS CountUpToThisPrice
FROM Products;
```

## Practical Examples

### Year-to-Date Sales

```sql
WITH MonthlySales AS (
    SELECT 
        YEAR(OrderDate) AS Year,
        MONTH(OrderDate) AS Month,
        SUM(Freight) AS MonthlyTotal
    FROM Orders
    GROUP BY YEAR(OrderDate), MONTH(OrderDate)
)
SELECT 
    Year,
    Month,
    MonthlyTotal,
    SUM(MonthlyTotal) OVER (
        PARTITION BY Year
        ORDER BY Month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS YTDTotal
FROM MonthlySales;
```

### Percentage of Running Total

```sql
-- Each order's contribution to running total
WITH OrderValues AS (
    SELECT 
        OrderID,
        OrderDate,
        Freight,
        SUM(Freight) OVER (ORDER BY OrderDate, OrderID) AS RunningTotal,
        SUM(Freight) OVER () AS GrandTotal
    FROM Orders
)
SELECT 
    OrderID,
    Freight,
    RunningTotal,
    100.0 * RunningTotal / GrandTotal AS PercentOfTotal
FROM OrderValues;
```

### Moving Min/Max

```sql
-- 5-order moving window of max freight
SELECT 
    OrderID,
    Freight,
    MAX(Freight) OVER (
        ORDER BY OrderID
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) AS Max5Orders,
    MIN(Freight) OVER (
        ORDER BY OrderID
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) AS Min5Orders
FROM Orders;
```

### Gap and Island Detection

```sql
-- Find consecutive order sequences per customer
WITH OrderGaps AS (
    SELECT 
        CustomerID,
        OrderID,
        OrderDate,
        ROW_NUMBER() OVER (PARTITION BY CustomerID ORDER BY OrderDate) AS SeqNum,
        DATEADD(day, 
            -ROW_NUMBER() OVER (PARTITION BY CustomerID ORDER BY OrderDate),
            OrderDate
        ) AS GroupDate
    FROM Orders
)
SELECT 
    CustomerID,
    GroupDate AS SequenceStart,
    MIN(OrderDate) AS FirstOrder,
    MAX(OrderDate) AS LastOrder,
    COUNT(*) AS ConsecutiveOrders
FROM OrderGaps
GROUP BY CustomerID, GroupDate
HAVING COUNT(*) > 3  -- Sequences of 4+ orders
ORDER BY CustomerID, FirstOrder;
```

## Default Frame Behavior

**Without explicit frame:**

```sql
-- Default frame depends on ORDER BY
SUM(x) OVER (ORDER BY y)
-- Equivalent to:
SUM(x) OVER (ORDER BY y ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)

-- Without ORDER BY: entire partition
SUM(x) OVER (PARTITION BY z)
-- Equivalent to:
SUM(x) OVER (PARTITION BY z ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
```

## Practice Exercises

```sql
-- 1. Running count of products
SELECT 
    ProductID,
    ProductName,
    COUNT(*) OVER (ORDER BY ProductID) AS RunningCount
FROM Products;

-- 2. 3-product moving average price
SELECT 
    ProductName,
    UnitPrice,
    AVG(UnitPrice) OVER (
        ORDER BY ProductID
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS MovingAvg3
FROM Products;

-- 3. YTD order count by month
WITH MonthlyCount AS (
    SELECT 
        YEAR(OrderDate) AS Yr,
        MONTH(OrderDate) AS Mo,
        COUNT(*) AS Cnt
    FROM Orders
    GROUP BY YEAR(OrderDate), MONTH(OrderDate)
)
SELECT 
    Yr, Mo, Cnt,
    SUM(Cnt) OVER (PARTITION BY Yr ORDER BY Mo) AS YTD
FROM MonthlyCount;
```

## Key Takeaways

- Frames define which rows to include in aggregates
- `ROWS` - physical offset, `RANGE` - value-based
- Default frame: UNBOUNDED PRECEDING to CURRENT ROW (if ORDER BY present)
- Running totals use UNBOUNDED PRECEDING AND CURRENT ROW
- Moving averages use N PRECEDING AND CURRENT ROW
- Essential for time series and trend analysis

## What's Next?

[Next: Module 07 - Set Operations →](../07-set-operations/01-set-operations.md)

---

[← Back: Analytic Functions](03-analytic-functions.md) | [Course Home](../README.md) | [Next: Set Operations →](../07-set-operations/01-set-operations.md)
