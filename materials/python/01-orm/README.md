# Python ORMs for Data Engineers

Welcome to the Python ORM module. This course teaches how Python applications communicate with databases, when to use Object-Relational Mapping (ORM) frameworks, and — just as importantly — when to bypass them.

## Overview

ORMs are powerful tools for backend developers, but in data engineering knowing **when not to use them** is just as important as knowing how. This module covers both perspectives.

**Total Duration:** 5–6 hours

## Prerequisites

- Completion of the SQL fundamentals module (or equivalent SQL knowledge)
- Basic Python knowledge — classes, functions, context managers
- Understanding of SELECT, INSERT, UPDATE, DELETE, JOINs, and transactions

## Quick Start

```bash
# Start the lab (PostgreSQL sidecar + workspace)
make lab-orm
```

Then open the lessons in order. The lab injects `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` into the workspace automatically — no manual connection string setup needed.

## The Learning Journey

| Lesson | Duration | Topics | Database |
|--------|----------|--------|----------|
| **01 – Database Fundamentals** | ~45 min | [Python Database Fundamentals](01-python-database-fundamentals.md) | PostgreSQL (lab) |
| **02 – ORM Concepts** | ~45 min | [ORM Concepts](02-orm-concepts.md) | PostgreSQL (lab) |
| **03 – Defining Models** | ~60 min | [Defining Models](03-defining-models.md) | SQLite (in-process) |
| **04 – CRUD Operations** | ~60 min | [CRUD Operations](04-crud-operations.md) | SQLite (in-process) |
| **05 – Testing** | ~45 min | [Testing and Database Lifecycle](05-testing.md) | SQLite in-memory |
| **06 – Schema Migrations** | ~45 min | [Schema Migrations](06-schema-migrations.md) | SQLite (in-process) |

**Lessons 01–02** need the lab running (`make lab-orm`) — they connect to PostgreSQL.  
**Lessons 03–06** use SQLite, which is built into Python — no lab required.

## The Bookstore Domain

Lessons 03–05 build a complete **Bookstore database**:

- **Authors** — writers of books
- **Publishers** — companies that publish books
- **Books** — products in the bookstore
- **Sales** — purchase records

This domain lets you practice defining models with relationships, CRUD operations, querying, transactions, testing, and schema migrations.

## Where ORMs Fit in Data Engineering

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA ENGINEERING LANDSCAPE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  OPERATIONAL / TRANSACTIONAL              ANALYTICAL / OLAP         │
│  ─────────────────────────────            ──────────────────────    │
│  PostgreSQL, MySQL, SQLite                Snowflake, BigQuery,      │
│  Small–medium datasets                    Redshift, Databricks      │
│  CRUD operations                          Large-scale analytics     │
│  Web backends, APIs                       Data warehouses           │
│                                                                     │
│  ✓ ORM is appropriate here                ✗ Use raw SQL + driver    │
│  - Faster development                     - Exact query control     │
│  - Type safety                            - Cost optimization       │
│  - Easy testing                           - Complex analytics       │
│  - Schema as code                         - No abstraction risk     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### SQLAlchemy 2.0
The most mature and widely-used Python ORM. Supports both the ORM (declarative models) and Core (SQL expression language) layers. Database-agnostic design.

### PostgreSQL (Lessons 01–02)
The lab provides a PostgreSQL container. We use it to practice raw DB-API connections and to demonstrate ORM-vs-raw-SQL comparisons on a real server.

### SQLite (Lessons 03–06)
Built into Python — zero installation, same ORM code works for PostgreSQL or MySQL in production. In-memory mode (`sqlite:///:memory:`) is ideal for tests.

### Alembic
SQLAlchemy's migration tool. Tracks schema changes as versioned code files, generates `ALTER TABLE` SQL automatically, and supports upgrade/downgrade.

## Key Takeaways

By the end of this module you will understand:

1. **How Python talks to databases** — drivers, DB-API 2.0, connection protocols
2. **What ORMs are and how they work** — wrapper around SQL, not a replacement
3. **When to use ORMs** — backend apps, operational databases, CRUD workloads
4. **When NOT to use ORMs** — analytical databases, large-scale data processing, ETL
5. **Testing** — in-memory databases, pytest fixtures, factory patterns
6. **Schema migrations** — version-controlled database changes with Alembic

## Philosophy: ORM is a Tool, Not a Requirement

This course takes a **balanced approach**:

- ORMs are powerful for certain use cases (web backends, operational databases)
- Raw SQL with drivers is better for others (analytical queries, data warehouses, bulk ETL)
- Understanding both makes you a better data engineer

**Critical message:** In data engineering you'll spend most of your time with analytical databases (Snowflake, BigQuery, Redshift) where **raw SQL is the standard**. ORMs are primarily for application development and operational databases.

## Additional Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Python DB-API Specification (PEP 249)](https://peps.python.org/pep-0249/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)

---

**Ready to begin?** Start with [01 – Python Database Fundamentals](01-python-database-fundamentals.md).
