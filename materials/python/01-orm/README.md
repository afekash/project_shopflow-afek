# Python ORMs for Data Engineers

Welcome to the Python ORM module! This course teaches you how Python applications communicate with databases, when to use Object-Relational Mapping (ORM) frameworks, and when to stick with raw SQL.

## Overview

ORMs are powerful tools for backend developers, but in data engineering, knowing when **not** to use them is just as important as knowing how to use them. This module covers both perspectives.

**Total Duration:** 5-6 hours

## Prerequisites

- Completion of SQL fundamentals course (or equivalent SQL knowledge)
- **Northwind database setup** - You should have the Northwind database running from the SQL course
- Python 3.10+ installed
- Basic Python knowledge (classes, functions, context managers)
- Understanding of:
  - SELECT, INSERT, UPDATE, DELETE operations
  - JOINs and relationships
  - Transactions

## The Learning Journey

This module takes you on a progressive journey:

1. **Connect to Northwind** (Lesson 01) - Learn raw database drivers by connecting to the existing Northwind database
2. **Understand ORMs** (Lesson 02) - Learn what ORMs do and when to use them
3. **Create Bookstore Database** (Lessons 03-06) - Build a new database using ORM and practice CRUD operations

### Two Databases, Two Purposes

| Database | Purpose | Lessons |
|----------|---------|---------|
| **Northwind** | Learn raw SQL drivers | 01-02 |
| **Bookstore** | Practice ORM operations | 03-06 |

## Key Takeaways

By the end of this module, you will understand:

1. **How Python talks to databases** - drivers, DB-API, connection protocols
2. **What ORMs are and how they work** - wrapper around SQL, not a replacement
3. **When to use ORMs** - backend apps, operational databases, CRUD workloads
4. **When NOT to use ORMs** - analytical databases, large-scale data processing
5. **Database lifecycle** - Creating and dropping databases (SQLite and SQL Server)
6. **Testing and reproducibility** - in-memory databases, pytest, factory patterns
7. **Schema migrations** - Version-controlled database changes with Alembic

## Where ORMs Fit in Data Engineering

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA ENGINEERING LANDSCAPE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  OPERATIONAL / TRANSACTIONAL                ANALYTICAL / OLAP       │
│  ─────────────────────────────              ──────────────────      │
│  PostgreSQL, MySQL, SQLite                  Snowflake, BigQuery,    │
│  Small-medium datasets                      Redshift, Databricks    │
│  CRUD operations                            Large-scale analytics   │
│  Web backends, APIs                         Data warehouses         │
│                                                                     │
│  ✓ ORM is appropriate here                  ✗ Use raw SQL + driver  │
│  - Faster development                       - Need exact query      │
│  - Type safety                                control               │
│  - Easy testing                             - Complex analytical    │
│  - Schema management                          queries               │
│                                             - Cost optimization     │
│                                             - No abstraction risk   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Learning Path

| Lesson | Duration | Topics | Key Concepts | Databases Used |
|--------|----------|--------|--------------|----------------|
| **01 - Database Fundamentals** | ~45 min | [Python Database Fundamentals](01-python-database-fundamentals.md) | Drivers, DB-API, how Python talks to databases, raw SQL connections | **Northwind** (SQL Server) |
| **02 - ORM Concepts** | ~45 min | [ORM Concepts](02-orm-concepts.md) | What is ORM, when to use it, when NOT to use it, ORM vs raw SQL | **Northwind** (SQL Server) |
| **03 - Defining Models** | ~60 min | [Defining Models](03-defining-models.md) | Tables as classes, columns, data types, relationships, database portability | **Bookstore** (SQLite + SQL Server) |
| **04 - CRUD Operations** | ~60 min | [CRUD Operations](04-crud-operations.md) | Insert, query, update, delete, sessions, transactions | **Bookstore** (SQLite) |
| **05 - Testing & Lifecycle** | ~45 min | [Testing and Database Lifecycle](05-testing-and-migrations.md) | In-memory databases, pytest, factory patterns, database lifecycle | **Bookstore** (SQLite + SQL Server) |
| **06 - Schema Migrations** | ~45 min | [Schema Migrations](06-schema-migrations.md) | Alembic, version-controlled schema changes, migration workflow | **Bookstore** (SQLite) |

## Quick Start

### 1. Verify Northwind Database

Make sure your Northwind database is running from the SQL course:

```bash
# Check SQL Server container is running
docker ps
```

**Connection Details:**
- Server: `localhost,1433`
- Database: `Northwind`
- User: `SA`
- Password: `61eF92j4VTtl`

### 2. Install Dependencies

```bash
pip install sqlalchemy alembic pytest pyodbc
```

Or using `uv`:

```bash
uv pip install sqlalchemy alembic pytest pyodbc
```

### 3. Verify Installation

```bash
python -c "import sqlalchemy; print(f'SQLAlchemy {sqlalchemy.__version__}')"
python -c "import pyodbc; print(f'pyodbc {pyodbc.version}')"
```

### 4. Start Learning

Begin with [Lesson 01 - Python Database Fundamentals](01-python-database-fundamentals.md) and work through the lessons sequentially.

## The Bookstore Domain

In lessons 03-05, you'll build a complete **Bookstore database** with:

- **Authors** - Writers of books
- **Publishers** - Companies that publish books
- **Books** - Products in the bookstore
- **Sales** - Purchase records

This realistic domain lets you practice:
- Defining models with relationships
- CRUD operations
- Querying with filters and joins
- Transactions
- Testing
- Schema migrations

## Philosophy: ORM is a Tool, Not a Requirement

This course takes a **balanced approach**:

- ORMs are powerful for certain use cases (web backends, operational databases)
- Raw SQL with drivers is better for others (analytical queries, data warehouses)
- Understanding both makes you a better data engineer

**Critical Message:** In data engineering, you'll spend most of your time working with analytical databases (Snowflake, BigQuery, Redshift) where **raw SQL is the standard**. ORMs are primarily for application development and operational databases.

## Technology Stack

### SQLAlchemy 2.0

We use SQLAlchemy as our ORM example because:

- Most mature and powerful Python ORM
- Widely used in industry
- Supports both ORM and Core (SQL expression language)
- Database-agnostic design

### SQLite

All examples use SQLite because:

- Built into Python - zero installation
- Perfect for learning and testing
- Same ORM code works with PostgreSQL, MySQL, etc. in production
- In-memory mode for instant test databases

### SQL Server (Northwind)

We connect to SQL Server for:

- Real-world database experience
- Learning database drivers (pyodbc)
- Understanding database portability
- Comparing SQLite vs SQL Server

## Code Format for Notebooks

All materials are designed to work as Jupyter notebooks:

- **Small, focused code cells** - Each cell has a single responsibility
- **Observable outputs** - Every cell produces visible results
- **Progressive building** - Later cells build on earlier ones
- **Runnable top-to-bottom** - Execute all cells in order

To generate notebooks from the markdown files:

```bash
uv run python generate_notebooks.py
```

## Learning Tips

1. **Run every example** - Don't just read, execute the code in notebooks
2. **Use `echo=True`** - See the SQL generated by the ORM
3. **Compare with raw SQL** - Understand what the ORM does under the hood
4. **Practice testing** - In-memory databases are a game-changer
5. **Know your use case** - Ask yourself: "Should this be ORM or raw SQL?"
6. **Start with Northwind** - Get familiar with raw SQL first
7. **Build the Bookstore** - Practice ORM with a complete domain

## Progressive Complexity

The course builds complexity gradually:

**Lesson 01:**
- Connect to existing database (Northwind)
- Learn raw DB-API with pyodbc
- Compare SQLite and SQL Server syntax

**Lesson 02:**
- Understand ORM concepts
- See SQL generation in action
- Learn decision framework

**Lesson 03:**
- Create new database (Bookstore)
- Define models progressively
- Support both SQLite and SQL Server

**Lesson 04:**
- Populate Bookstore with data
- Practice CRUD operations
- Work with relationships

**Lesson 05:**
- Test Bookstore models
- Manage database lifecycle
- Create test factories

**Lesson 06:**
- Learn schema migrations
- Version control database changes
- Apply and rollback migrations

## Additional Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Python DB-API Specification (PEP 249)](https://peps.python.org/pep-0249/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [pyodbc Documentation](https://github.com/mkleehammer/pyodbc/wiki)

## Course Philosophy

Throughout this module, we emphasize:

- **Transparency** - Always show the SQL being generated
- **Trade-offs** - Every tool has pros and cons
- **Practical guidance** - Real-world decision frameworks
- **Data engineering perspective** - ORMs in the broader data landscape
- **Progressive learning** - Start simple, build complexity
- **Hands-on practice** - Learn by building real databases

## Database Management

You'll learn to:

### SQLite
- Create databases: `create_engine("sqlite:///bookstore.db")`
- Drop databases: `os.remove("bookstore.db")`
- In-memory testing: `create_engine("sqlite:///:memory:")`

### SQL Server
- Create databases: `CREATE DATABASE` via pyodbc
- Drop databases: `DROP DATABASE` via pyodbc
- Connect with SQLAlchemy: `mssql+pyodbc://...`

## Support Both Databases

All Bookstore examples support both SQLite and SQL Server:

```python
# Configuration
SQLITE_URL = "sqlite:///bookstore.db"
SQLSERVER_URL = "mssql+pyodbc://SA:pass@localhost:1433/Bookstore?driver=..."

# Choose database
USE_SQLSERVER = False
database_url = SQLSERVER_URL if USE_SQLSERVER else SQLITE_URL
engine = create_engine(database_url)
```

---

**Ready to begin?** Start with [01 - Python Database Fundamentals](01-python-database-fundamentals.md)

**Have Northwind running?** Great! You'll use it in lessons 01-02.

**Ready to build?** You'll create the Bookstore database in lessons 03-05.
