# Recursive CTEs

## Overview

Recursive CTEs call themselves, useful for hierarchical or graph data (org charts, bill of materials, path finding).

## Syntax

```sql
WITH RECURSIVE cte_name AS (
    -- Anchor: Base case
    SELECT ...
    
    UNION ALL
    
    -- Recursive: Calls itself
    SELECT ...
    FROM cte_name
    JOIN ...
)
SELECT * FROM cte_name;
```

**T-SQL note:** Omit `RECURSIVE` keyword (implied).

## Employee Hierarchy Example

```sql
-- Find all employees under a manager
WITH EmployeeHierarchy AS (
    -- Anchor: Top-level manager
    SELECT 
        EmployeeID,
        FirstName + ' ' + LastName AS Name,
        ReportsTo,
        0 AS Level
    FROM Employees
    WHERE ReportsTo IS NULL  -- CEO
    
    UNION ALL
    
    -- Recursive: Employees reporting to previous level
    SELECT 
        e.EmployeeID,
        e.FirstName + ' ' + e.LastName,
        e.ReportsTo,
        eh.Level + 1
    FROM Employees e
        INNER JOIN EmployeeHierarchy eh ON e.ReportsTo = eh.EmployeeID
)
SELECT 
    REPLICATE('  ', Level) + Name AS OrgChart,
    Level
FROM EmployeeHierarchy
ORDER BY Level, Name;
```

**Result:**
```
Andrew Fuller (Level 0)
  Nancy Davolio (Level 1)
  Janet Leverling (Level 1)
  Steven Buchanan (Level 1)
    ...
```

## Number Sequence Generator

```sql
-- Generate numbers 1 to 100
WITH Numbers AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1
    FROM Numbers
    WHERE n < 100
)
SELECT n FROM Numbers
OPTION (MAXRECURSION 100);
```

**MAXRECURSION:** Prevents infinite loops (default 100, 0 = unlimited).

## Date Range Generator

```sql
-- All dates in January 2024
WITH DateRange AS (
    SELECT CAST('2024-01-01' AS DATE) AS Date
    UNION ALL
    SELECT DATEADD(DAY, 1, Date)
    FROM DateRange
    WHERE Date < '2024-01-31'
)
SELECT Date
FROM DateRange
OPTION (MAXRECURSION 31);
```

## Path Finding

```sql
-- Find all paths from employee to CEO
WITH EmployeePath AS (
    -- Anchor: Start with each employee
    SELECT 
        EmployeeID,
        FirstName + ' ' + LastName AS Path,
        ReportsTo,
        0 AS Depth
    FROM Employees
    
    UNION ALL
    
    -- Recursive: Add manager to path
    SELECT 
        ep.EmployeeID,
        ep.Path + ' -> ' + e.FirstName + ' ' + e.LastName,
        e.ReportsTo,
        ep.Depth + 1
    FROM EmployeePath ep
        INNER JOIN Employees e ON ep.ReportsTo = e.EmployeeID
)
SELECT 
    EmployeeID,
    Path,
    Depth
FROM EmployeePath
WHERE ReportsTo IS NULL  -- Reached the top
ORDER BY EmployeeID;
```

## Practical Example: Product Categories (if hierarchical)

```sql
-- If categories had parent-child relationships
WITH CategoryTree AS (
    -- Root categories
    SELECT 
        CategoryID,
        CategoryName,
        ParentCategoryID,
        CategoryName AS FullPath,
        0 AS Level
    FROM Categories
    WHERE ParentCategoryID IS NULL
    
    UNION ALL
    
    -- Subcategories
    SELECT 
        c.CategoryID,
        c.CategoryName,
        c.ParentCategoryID,
        ct.FullPath + ' > ' + c.CategoryName,
        ct.Level + 1
    FROM Categories c
        INNER JOIN CategoryTree ct ON c.ParentCategoryID = ct.CategoryID
)
SELECT * FROM CategoryTree
ORDER BY FullPath;
```

## Advanced: Cycle Detection

Prevent infinite loops with cycle tracking:

```sql
WITH EmployeeCycles AS (
    SELECT 
        EmployeeID,
        FirstName,
        ReportsTo,
        CAST(EmployeeID AS VARCHAR(MAX)) AS Path
    FROM Employees
    WHERE ReportsTo IS NULL
    
    UNION ALL
    
    SELECT 
        e.EmployeeID,
        e.FirstName,
        e.ReportsTo,
        ec.Path + ',' + CAST(e.EmployeeID AS VARCHAR)
    FROM Employees e
        INNER JOIN EmployeeCycles ec ON e.ReportsTo = ec.EmployeeID
    WHERE ec.Path NOT LIKE '%' + CAST(e.EmployeeID AS VARCHAR) + '%'  -- Cycle detection
)
SELECT * FROM EmployeeCycles;
```

## Performance Considerations

Recursive CTEs can be slow on large hierarchies:

**Tips:**
- Add WHERE clauses to limit depth
- Index parent/child columns
- Use MAXRECURSION to prevent runaway queries
- For deep hierarchies (>100 levels), consider materialized paths or nested sets

## Practice Exercises

```sql
-- 1. Generate numbers 1-50
WITH Nums AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM Nums WHERE n < 50
)
SELECT * FROM Nums
OPTION (MAXRECURSION 50);

-- 2. All dates in December 2023
WITH Dates AS (
    SELECT CAST('2023-12-01' AS DATE) AS d
    UNION ALL
    SELECT DATEADD(DAY, 1, d) FROM Dates WHERE d < '2023-12-31'
)
SELECT * FROM Dates
OPTION (MAXRECURSION 31);

-- 3. Employee depth from CEO
WITH Depth AS (
    SELECT EmployeeID, 0 AS Level
    FROM Employees WHERE ReportsTo IS NULL
    UNION ALL
    SELECT e.EmployeeID, d.Level + 1
    FROM Employees e
    JOIN Depth d ON e.ReportsTo = d.EmployeeID
)
SELECT e.FirstName, e.LastName, d.Level
FROM Employees e
JOIN Depth d ON e.EmployeeID = d.EmployeeID;
```

## Key Takeaways

- Recursive CTEs have anchor (base case) and recursive part
- Use UNION ALL to combine parts
- Great for hierarchies, graphs, sequences
- MAXRECURSION prevents infinite loops
- T-SQL doesn't use RECURSIVE keyword
- Not ideal for big data (sequential nature)
- Performance degrades with depth - consider alternatives for large hierarchies

## What's Next?

[Next: Module 06 - Window Functions →](../06-window-functions/01-window-basics.md)

---

[← Back: CTE Basics](02-cte-basics.md) | [Course Home](../README.md) | [Next: Window Functions →](../06-window-functions/01-window-basics.md)
