# SQL Fundamentals for Data Engineering

Welcome to the SQL course for data engineers! This comprehensive guide covers everything from basic SELECT queries to advanced window functions and big data concepts.

## Course Overview

This course uses the **Northwind** database (a classic OLTP system) to teach SQL fundamentals while constantly relating concepts to modern data engineering practices including data warehouses, data lakes, and distributed computing.

## Prerequisites

- Basic understanding of relational databases
- Docker installed (for running MS SQL Server)
- A SQL client (Azure Data Studio, DBeaver, or VS Code with SQL extension)

## Core Concepts Reference

This course links to the **[Core Concepts library](../core-concepts/README.md)** -- a tool-agnostic reference for the foundational building blocks that appear across all data technologies. Think of it as a companion dictionary: when this course references B-trees, bloom filters, or ACID, follow the link to understand the general concept, then return here to see how SQL databases specifically implement it.

Key concepts you'll encounter in this course:

| When you see... | The core concept is... |
|-----------------|----------------------|
| Big O notation, O(log n) index seeks | [Big O Notation](../core-concepts/01-complexity-and-performance/01-big-o-notation.md) |
| Columnar storage, SELECT * cost | [I/O and Storage Fundamentals](../core-concepts/01-complexity-and-performance/02-io-and-storage-fundamentals.md) |
| Clustered/nonclustered indexes, B-trees | [Trees for Storage](../core-concepts/02-data-structures/02-trees-for-storage.md) |
| Bloom filters (WHERE, joins) | [Probabilistic Structures](../core-concepts/02-data-structures/04-probabilistic-structures.md) |
| Table partitioning, zone maps | [Partitioning Strategies](../core-concepts/03-scaling/02-partitioning-strategies.md) |
| ACID properties, transactions | [ACID vs BASE](../core-concepts/04-distributed-systems/02-acid-vs-base.md) |
| Isolation levels | [Consistency Models](../core-concepts/04-distributed-systems/03-consistency-models.md) |
| WAL, Delta Lake / Iceberg transactions | [Write-Ahead Logs](../core-concepts/05-replication-and-availability/03-write-ahead-logs.md) |
| Normalization vs denormalization | [Schema Strategies](../core-concepts/06-architecture-patterns/01-schema-strategies.md) |
| Distributed joins, shuffles | [Query Routing Patterns](../core-concepts/06-architecture-patterns/02-query-routing-patterns.md) |

**Note:** SQL is taught before NoSQL in this course. The core-concepts library contains no NoSQL-specific content, only general theory. NoSQL materials will later build on these same concepts and show you how different databases made different choices from the same toolkit.

## Learning Path

| Module | Topics | Key Concepts |
|--------|--------|--------------|
| **01 - Fundamentals** | [Introduction](01-fundamentals/01-introduction.md), [Database Setup](01-fundamentals/02-database-setup.md), [Execution Order](01-fundamentals/03-sql-execution-order.md) | SQL basics, OLTP vs OLAP, query processing |
| **02 - Querying Data** | [SELECT](02-querying-data/01-select-basics.md), [WHERE](02-querying-data/02-filtering-where.md), [ORDER BY](02-querying-data/03-sorting-order-by.md) | Column selection, filtering, sorting, SARGability |
| **03 - Joining Tables** | [Join Theory](03-joining-tables/01-join-theory.md), [Join Types](03-joining-tables/02-join-types.md), [Advanced Joins](03-joining-tables/03-advanced-joins.md), [Normalization](03-joining-tables/04-normalization-vs-denormalization.md) | Set theory, join algorithms, OLTP vs OLAP design |
| **04 - Aggregations** | [Aggregate Functions](04-aggregations/01-aggregate-functions.md), [GROUP BY](04-aggregations/02-group-by-having.md), [Advanced Grouping](04-aggregations/03-advanced-grouping.md) | COUNT, SUM, AVG, ROLLUP, CUBE |
| **05 - Subqueries & CTEs** | [Subqueries](05-subqueries-ctes/01-subqueries.md), [CTEs](05-subqueries-ctes/02-cte-basics.md), [Recursive CTEs](05-subqueries-ctes/03-recursive-ctes.md) | Correlated subqueries, WITH clause, hierarchies |
| **06 - Window Functions** | [Basics](06-window-functions/01-window-basics.md), [Ranking](06-window-functions/02-ranking-functions.md), [Analytics](06-window-functions/03-analytic-functions.md), [Frames](06-window-functions/04-frames-running-totals.md) | OVER, PARTITION BY, ROW_NUMBER, LAG/LEAD |
| **07 - Set Operations** | [Set Operations](07-set-operations/01-set-operations.md) | UNION, INTERSECT, EXCEPT |
| **08 - Data Manipulation** | [INSERT](08-data-manipulation/01-insert.md), [UPDATE/DELETE](08-data-manipulation/02-update-delete.md), [MERGE](08-data-manipulation/03-merge-upsert.md), [Transactions](08-data-manipulation/04-transactions.md) | DML, UPSERT, ACID properties, SCD patterns |
| **09 - Schema Design** | [DDL](09-schema-design/01-ddl-basics.md), [ALTER TABLE](09-schema-design/02-alter-table.md), [Indexes](09-schema-design/03-indexes.md) | CREATE TABLE, constraints, indexing strategies |
| **10 - Big Data Context** | [OLTP vs OLAP](10-big-data-context/01-oltp-vs-olap.md), [Data Lakes](10-big-data-context/02-data-lake-patterns.md), [Distributed SQL](10-big-data-context/03-distributed-sql.md) | Star schema, immutability, partitioning |

## Quick Start

### 1. Set Up the Database

Follow the instructions in [Database Setup](01-fundamentals/02-database-setup.md) to:
- Run MS SQL Server 2022 in Docker
- Restore the Northwind database
- Connect using your preferred SQL client

### 2. Start Learning

Begin with [Module 01 - Introduction](01-fundamentals/01-introduction.md) and work through the modules sequentially.

### 3. Practice as You Go

Each module includes:
- **Practical examples** you can run directly
- **Practice exercises** to test your understanding
- **Advanced insights** for deeper learning
- **Big data context** connecting concepts to data engineering

## Database Schema Quick Reference

The Northwind database models a fictional import-export company with:

- **Customers** - Companies that place orders
- **Orders** - Customer orders with dates and shipping info
- **Order Details** - Line items (which products, quantities)
- **Products** - Items for sale with pricing
- **Categories** - Product categorization
- **Suppliers** - Companies that supply products
- **Employees** - Staff who handle orders
- **Shippers** - Shipping companies

See [Introduction](01-fundamentals/01-introduction.md) for the full ERD diagram.

## Learning Tips

1. **Run every query** - Don't just read, execute the examples
2. **Modify and experiment** - Change queries to see different results
3. **For weaker students** - Focus on the "Core Concepts" sections first
4. **For stronger students** - Pay special attention to "Advanced Insights" and "Big Data Context" sections
5. **Think about scale** - Always consider how concepts apply to billions of rows

## Additional Resources

- [SQL Server Documentation](https://docs.microsoft.com/en-us/sql/)
- [Northwind Database](https://github.com/microsoft/sql-server-samples/tree/master/samples/databases/northwind-pubs)
- [Query Execution Plans](https://docs.microsoft.com/en-us/sql/relational-databases/performance/execution-plans)

## Course Instructor

This material is designed for varying skill levels - from SQL beginners to those with some experience who need data engineering context. Work at your own pace and don't hesitate to ask questions!

---

**Ready to begin?** Start with [01 - Introduction to SQL](01-fundamentals/01-introduction.md)
