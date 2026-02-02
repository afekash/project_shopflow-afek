# Analytic Functions

## Overview

Analytic functions access data from other rows relative to the current row - without self-joins. Essential for time series, comparisons, and change detection.

## LAG()

Access previous row's value.

```sql
-- Compare each product price to previous product
SELECT 
    ProductName,
    UnitPrice,
    LAG(UnitPrice) OVER (ORDER BY UnitPrice) AS PreviousPrice,
    UnitPrice - LAG(UnitPrice) OVER (ORDER BY UnitPrice) AS PriceDiff
FROM Products
ORDER BY UnitPrice;
```

**Syntax:** `LAG(column, offset, default) OVER (...)`
- `offset` - How many rows back (default 1)
- `default` - Value if no previous row (default NULL)

### Month-over-Month Change

```sql
-- Monthly order count with change from previous month
WITH MonthlyOrders AS (
    SELECT 
        YEAR(OrderDate) AS Year,
        MONTH(OrderDate) AS Month,
        COUNT(*) AS OrderCount
    FROM Orders
    GROUP BY YEAR(OrderDate), MONTH(OrderDate)
)
SELECT 
    Year,
    Month,
    OrderCount,
    LAG(OrderCount) OVER (ORDER BY Year, Month) AS PrevMonthCount,
    OrderCount - LAG(OrderCount) OVER (ORDER BY Year, Month) AS MonthOverMonthChange
FROM MonthlyOrders
ORDER BY Year, Month;
```

## LEAD()

Access next row's value.

```sql
-- Compare each order date to next order
SELECT 
    OrderID,
    OrderDate,
    LEAD(OrderDate) OVER (ORDER BY OrderDate) AS NextOrderDate,
    DATEDIFF(day, OrderDate, LEAD(OrderDate) OVER (ORDER BY OrderDate)) AS DaysUntilNext
FROM Orders;
```

## FIRST_VALUE()

First value in the window.

```sql
-- Each product with its category's cheapest product
SELECT 
    ProductName,
    CategoryID,
    UnitPrice,
    FIRST_VALUE(ProductName) OVER (
        PARTITION BY CategoryID 
        ORDER BY UnitPrice
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS CheapestInCategory,
    FIRST_VALUE(UnitPrice) OVER (
        PARTITION BY CategoryID 
        ORDER BY UnitPrice
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS LowestPrice
FROM Products;
```

**Note:** Frame clause ensures we see the entire partition.

## LAST_VALUE()

Last value in the window.

```sql
-- Each product with category's most expensive product
SELECT 
    ProductName,
    CategoryID,
    UnitPrice,
    LAST_VALUE(ProductName) OVER (
        PARTITION BY CategoryID 
        ORDER BY UnitPrice
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS MostExpensiveInCategory
FROM Products;
```

**Common mistake:** Without frame clause, LAST_VALUE only sees up to current row!

## Practical Examples

### Customer Retention Analysis

```sql
-- Days between customer orders
WITH CustomerOrders AS (
    SELECT 
        CustomerID,
        OrderID,
        OrderDate,
        LAG(OrderDate) OVER (PARTITION BY CustomerID ORDER BY OrderDate) AS PrevOrderDate
    FROM Orders
)
SELECT 
    CustomerID,
    OrderDate,
    PrevOrderDate,
    DATEDIFF(day, PrevOrderDate, OrderDate) AS DaysSinceLastOrder,
    CASE 
        WHEN DATEDIFF(day, PrevOrderDate, OrderDate) > 90 THEN 'At Risk'
        WHEN DATEDIFF(day, PrevOrderDate, OrderDate) > 30 THEN 'Moderate'
        ELSE 'Active'
    END AS CustomerStatus
FROM CustomerOrders
WHERE PrevOrderDate IS NOT NULL;
```

### Price Change Detection

```sql
-- Find products with price changes (if historical data exists)
SELECT 
    ProductID,
    ProductName,
    EffectiveDate,
    UnitPrice,
    LAG(UnitPrice) OVER (PARTITION BY ProductID ORDER BY EffectiveDate) AS OldPrice,
    UnitPrice - LAG(UnitPrice) OVER (PARTITION BY ProductID ORDER BY EffectiveDate) AS PriceChange,
    100.0 * (UnitPrice - LAG(UnitPrice) OVER (PARTITION BY ProductID ORDER BY EffectiveDate)) 
        / LAG(UnitPrice) OVER (PARTITION BY ProductID ORDER BY EffectiveDate) AS PercentChange
FROM ProductPriceHistory
ORDER BY ProductID, EffectiveDate;
```

### Session Analysis

```sql
-- Identify new sessions (>30 min gap between events)
WITH Events AS (
    SELECT 
        UserID,
        EventTime,
        LAG(EventTime) OVER (PARTITION BY UserID ORDER BY EventTime) AS PrevEventTime,
        DATEDIFF(minute, 
            LAG(EventTime) OVER (PARTITION BY UserID ORDER BY EventTime), 
            EventTime
        ) AS MinutesSinceLast
    FROM UserEvents
)
SELECT 
    *,
    CASE WHEN MinutesSinceLast > 30 OR MinutesSinceLast IS NULL 
         THEN 1 ELSE 0 END AS IsNewSession
FROM Events;
```

### Comparison to Best/Worst

```sql
-- Compare each product to category's best and worst
SELECT 
    ProductName,
    CategoryID,
    UnitPrice,
    FIRST_VALUE(UnitPrice) OVER (
        PARTITION BY CategoryID ORDER BY UnitPrice
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS CategoryMin,
    LAST_VALUE(UnitPrice) OVER (
        PARTITION BY CategoryID ORDER BY UnitPrice
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS CategoryMax,
    UnitPrice - FIRST_VALUE(UnitPrice) OVER (
        PARTITION BY CategoryID ORDER BY UnitPrice
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS DiffFromCheapest
FROM Products;
```

## Advanced: Multi-Step LAG

```sql
-- Compare to 2 months ago
SELECT 
    YEAR(OrderDate) AS Year,
    MONTH(OrderDate) AS Month,
    COUNT(*) AS OrderCount,
    LAG(COUNT(*), 1) OVER (ORDER BY YEAR(OrderDate), MONTH(OrderDate)) AS Prev1Month,
    LAG(COUNT(*), 2) OVER (ORDER BY YEAR(OrderDate), MONTH(OrderDate)) AS Prev2Months
FROM Orders
GROUP BY YEAR(OrderDate), MONTH(OrderDate);
```

## Practice Exercises

```sql
-- 1. Order frequency per customer
SELECT 
    CustomerID,
    OrderDate,
    LAG(OrderDate) OVER (PARTITION BY CustomerID ORDER BY OrderDate) AS PrevOrder,
    DATEDIFF(day, 
        LAG(OrderDate) OVER (PARTITION BY CustomerID ORDER BY OrderDate), 
        OrderDate
    ) AS DaysBetweenOrders
FROM Orders;

-- 2. Product price vs category extremes
SELECT 
    ProductName,
    CategoryID,
    UnitPrice,
    FIRST_VALUE(UnitPrice) OVER (PARTITION BY CategoryID ORDER BY UnitPrice) AS MinInCategory,
    LAST_VALUE(UnitPrice) OVER (PARTITION BY CategoryID ORDER BY UnitPrice 
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS MaxInCategory
FROM Products;

-- 3. Next order forecast
SELECT 
    OrderID,
    OrderDate,
    Freight,
    LEAD(Freight) OVER (ORDER BY OrderDate) AS NextOrderFreight
FROM Orders;
```

## Key Takeaways

- `LAG()` accesses previous rows
- `LEAD()` accesses next rows
- `FIRST_VALUE()` gets first value in window
- `LAST_VALUE()` gets last value (mind the frame!)
- Essential for time series and change analysis
- Eliminates self-joins
- Requires sorting - expensive at scale

## What's Next?

[Next: Frames and Running Totals →](04-frames-running-totals.md)

---

[← Back: Ranking Functions](02-ranking-functions.md) | [Course Home](../README.md) | [Next: Frames and Running Totals →](04-frames-running-totals.md)
