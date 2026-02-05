# ORM Concepts: When to Use, When to Avoid

## Overview

Object-Relational Mapping (ORM) frameworks sit between your application code and the database driver. They provide a higher-level abstraction, but understanding what they do - and crucially, **when not to use them** - is essential for data engineers.

## What is an ORM?

**ORM (Object-Relational Mapping)** is a programming technique that maps database tables to Python classes, and rows to Python objects.

**The key insight:** An ORM is a **wrapper around the driver**. It still sends SQL to the database - it just generates that SQL for you.

## The ORM Layer in the Stack

```
┌─────────────────────────────────────────────────────┐
│                   YOUR CODE                         │
│                                                     │
│   user = User(name="Alice")     # Python object     │
│   session.add(user)             # Tell ORM to save  │
│   session.commit()              # Execute           │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                     ORM                             │
│                                                     │
│   Generates: INSERT INTO users (name) VALUES (?)    │
│   Manages: connections, transactions, caching       │
│   Tracks: which objects changed (Unit of Work)      │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                    DRIVER                           │
│   Sends SQL to database, returns results            │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                  DATABASE                           │
│   Executes SQL, returns rows                        │
└─────────────────────────────────────────────────────┘
```

**Critical understanding:** The ORM doesn't talk directly to the database. It uses the driver underneath, just like your raw SQL code does.

## What ORMs Provide

ORMs add several conveniences on top of raw DB-API:

### 1. Object Mapping

```python
# Raw DB-API - tuples
import pyodbc

connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=Northwind;"
    "UID=SA;"
    "PWD=61eF92j4VTtl;"
    "TrustServerCertificate=yes;"
)

conn = pyodbc.connect(connection_string)
cursor = conn.cursor()
cursor.execute("SELECT CustomerID, CompanyName, ContactName FROM Customers WHERE CustomerID = 'ALFKI'")
row = cursor.fetchone()
print(f"(Customer ID: {row[0]}) - (Company Name: {row[1]}) - (Contact Name: {row[2]})")  # Tuple access by index
conn.close()
```

With ORM, you would access data as object attributes instead (we'll see this in detail in Lesson 03):

```python
# ORM - objects (preview - we'll learn this in Lesson 03)
# user = session.get(User, 1)
# print(user.id, user.name, user.email)  # Object attributes
```

### 2. SQL Generation

ORMs generate SQL from Python code. Let's see what SQL they create:

```python
# Install SQLAlchemy
# pip install sqlalchemy
```

```python
from sqlalchemy import create_engine, select, MetaData, Table

# Connect to Northwind
engine = create_engine(
    "mssql+pyodbc://SA:61eF92j4VTtl@localhost:1433/Northwind"
    "?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes",
    echo=True  # Shows generated SQL
)

# Reflect the Customers table
metadata = MetaData()
customers = Table('Customers', metadata, autoload_with=engine)

print(f"Customers table columns: {[c.name for c in customers.columns]}")
```

```python
# Build a query using SQLAlchemy
stmt = select(customers).where(customers.c.Country == "Germany").limit(3)

print("SQLAlchemy query object:")
print(stmt)
```

```python
# Execute and see the generated SQL
with engine.connect() as conn:
    result = conn.execute(stmt)
    rows = result.fetchall()
    
    print(f"\nFound {len(rows)} German customers:")
    for row in rows:
        print(f"  {row.CustomerID}: {row.CompanyName} ({row.City})")
```

### 3. Seeing Generated SQL

Enable SQL logging to understand what the ORM does:

```python
from sqlalchemy import create_engine

# Enable SQL echo - shows every query
engine = create_engine("sqlite:///test.db", echo=True)

# Now every query is printed to console
# This is ESSENTIAL for learning and debugging
```

### 4. Transaction Management

```python
# Raw DB-API - manual commit/rollback
import sqlite3

conn = sqlite3.connect("db.sqlite")
try:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users ...")
    cursor.execute("INSERT INTO orders ...")
    conn.commit()
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    conn.close()
```

With ORM (preview - details in Lesson 04):

```python
# ORM - automatic tracking (we'll learn this in Lesson 04)
# with Session(engine) as session:
#     session.add(User(...))
#     session.add(Order(...))
#     session.commit()  # Commits both, or rolls back both
```

### 5. Database Portability

```python
# Same ORM code works with different databases
# Just change the connection string:

# SQLite
engine = create_engine("sqlite:///dev.db")

# PostgreSQL
engine = create_engine("postgresql://user:pass@localhost/prod")

# SQL Server
engine = create_engine("mssql+pyodbc://SA:pass@localhost/prod?driver=...")

# MySQL
engine = create_engine("mysql://user:pass@localhost/prod")

# Models and queries stay the same!
```

## When to Use an ORM

ORMs shine in certain scenarios:

### ✓ Backend Applications (Web APIs, Microservices)

**Example Use Case:**
```python
# REST API endpoint with ORM (conceptual)
# @app.post("/users")
# def create_user(user_data: UserCreate):
#     user = User(
#         name=user_data.name,
#         email=user_data.email
#     )
#     session.add(user)
#     session.commit()
#     return {"id": user.id, "name": user.name}
```

**Why ORM works here:**
- CRUD operations (Create, Read, Update, Delete)
- Simple queries
- Objects map naturally to API resources
- Developer productivity matters more than query optimization

### ✓ Operational Databases (PostgreSQL, MySQL, SQL Server)

**Characteristics:**
- Small to medium datasets (thousands to millions of rows)
- Transactional workloads
- Relationships between entities
- Schema managed by application

**Example:**
```python
# Application database - CRUD-focused
# user = session.get(User, user_id)
# user.last_login = datetime.now()
# session.commit()
```

### ✓ Testing and Development

```python
# In-memory database for tests (we'll learn this in Lesson 05)
# @pytest.fixture
# def db_session():
#     engine = create_engine("sqlite:///:memory:")
#     Base.metadata.create_all(engine)
#     with Session(engine) as session:
#         yield session
```

**Why ORM works here:**
- Instant test databases
- No external dependencies
- Schema as code
- Reproducible across environments

### ✓ Rapid Prototyping

**Example:**
```python
# Quick prototype - schema evolves rapidly
# class BlogPost(Base):
#     __tablename__ = "posts"
#     id: Mapped[int] = mapped_column(primary_key=True)
#     title: Mapped[str]
#     content: Mapped[str]
#
# Base.metadata.create_all(engine)  # Tables created instantly
```

**Why ORM works here:**
- Fast iteration
- Schema changes are code changes
- Focus on logic, not SQL

## When NOT to Use an ORM

This is equally important for data engineers:

### ✗ Analytical Databases (Snowflake, BigQuery, Redshift)

Let's compare with a real Northwind example:

```python
# ❌ ORM doesn't know about these optimizations
# This is conceptual - ORMs struggle with complex analytics
```

```python
# ✓ Use raw SQL with driver for analytics
import pyodbc

connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=Northwind;"
    "UID=SA;"
    "PWD=61eF92j4VTtl;"
    "TrustServerCertificate=yes;"
)

with pyodbc.connect(connection_string) as conn:
    cursor = conn.cursor()
    
    # Complex analytical query with aggregations
    cursor.execute("""
        SELECT 
            YEAR(o.OrderDate) as Year,
            MONTH(o.OrderDate) as Month,
            COUNT(DISTINCT o.CustomerID) as UniqueCustomers,
            COUNT(o.OrderID) as TotalOrders,
            SUM(od.UnitPrice * od.Quantity) as Revenue,
            AVG(od.UnitPrice * od.Quantity) as AvgOrderValue
        FROM Orders o
        JOIN [Order Details] od ON o.OrderID = od.OrderID
        WHERE o.OrderDate >= '1997-01-01'
        GROUP BY YEAR(o.OrderDate), MONTH(o.OrderDate)
        ORDER BY Year DESC, Month DESC
    """)
    
    print(f"{'Year':<6} {'Month':<6} {'Customers':<12} {'Orders':<10} {'Revenue':<15} {'Avg Order'}")
    print("-" * 70)
    
    for row in cursor.fetchmany(5):
        print(f"{row.Year:<6} {row.Month:<6} {row.UniqueCustomers:<12} {row.TotalOrders:<10} "
              f"${row.Revenue:>12,.2f} ${row.AvgOrderValue:>10,.2f}")
```

**Why NOT ORM:**
- **Optimization**: You need exact control over query plans
- **Complexity**: Window functions, CTEs, complex aggregations
- **Scale**: Billions of rows - can't load into objects
- **Database features**: Clustering, partitioning, materialized views
- **Cost**: Analytical databases charge per query/data scanned

### ✗ ETL Pipelines and Bulk Operations

```python
# ❌ DON'T use ORM for bulk inserts
# for row in million_rows:
#     session.add(Product(name=row['name'], price=row['price']))
# session.commit()  # Extremely slow!
```

```python
# ✓ Use bulk operations or raw SQL
import sqlite3

conn = sqlite3.connect("products.db")
cursor = conn.cursor()

# Create sample data
products_data = [
    (f"Product {i}", 10.0 + i) 
    for i in range(1000)
]

# Bulk insert - much faster
cursor.executemany(
    "INSERT INTO products (name, price) VALUES (?, ?)",
    products_data
)
conn.commit()

print(f"Inserted {len(products_data)} products efficiently")
conn.close()
```

**Why NOT ORM:**
- **Performance**: ORM adds overhead for each object
- **Memory**: Can't load millions of objects into RAM
- **Simplicity**: Bulk operations don't need object mapping

### ✗ Complex Analytical Queries

```python
# ❌ This is painful with ORM - complex query builders become unreadable
# ORM query builders struggle with complex CTEs and window functions
```

```python
# ✓ Much clearer with raw SQL
import pyodbc

connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=Northwind;"
    "UID=SA;"
    "PWD=61eF92j4VTtl;"
    "TrustServerCertificate=yes;"
)

with pyodbc.connect(connection_string) as conn:
    cursor = conn.cursor()
    
    # Complex query with CTE and window function
    cursor.execute("""
        WITH CustomerStats AS (
            SELECT 
                c.CustomerID,
                c.CompanyName,
                COUNT(o.OrderID) as OrderCount,
                SUM(od.UnitPrice * od.Quantity) as TotalSpent,
                RANK() OVER (ORDER BY SUM(od.UnitPrice * od.Quantity) DESC) as SpendingRank
            FROM Customers c
            LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
            LEFT JOIN [Order Details] od ON o.OrderID = od.OrderID
            GROUP BY c.CustomerID, c.CompanyName
        )
        SELECT TOP 5
            CustomerID,
            CompanyName,
            OrderCount,
            TotalSpent,
            SpendingRank
        FROM CustomerStats
        WHERE OrderCount > 5
        ORDER BY TotalSpent DESC
    """)
    
    print("Top 5 customers by spending:")
    for row in cursor.fetchall():
        print(f"  #{row.SpendingRank} {row.CompanyName}: ${row.TotalSpent:,.2f} ({row.OrderCount} orders)")
```

**Why NOT ORM:**
- Complex queries are clearer in SQL
- ORM query builders become unreadable
- Harder to debug and optimize

## Real-World Decision Framework

Ask yourself these questions:

| Question | ORM ✓ | Raw SQL ✓ |
|----------|-------|-----------|
| Is this a CRUD application? | Yes | No |
| Are queries simple? | Yes | No |
| Is data volume small (<1M rows)? | Yes | No |
| Do I need relationships? | Yes | Maybe |
| Is developer productivity critical? | Yes | Maybe |
| Is query cost a concern? | No | Yes |
| Are queries complex (window functions, CTEs)? | No | Yes |
| Is this an analytical database? | No | Yes |
| Do I need bulk operations (>10K rows)? | No | Yes |
| Am I doing ETL? | No | Yes |

## Comparing Raw SQL vs ORM

Let's see a direct comparison with Northwind data:

### Raw SQL Approach

```python
import pyodbc

connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=Northwind;"
    "UID=SA;"
    "PWD=61eF92j4VTtl;"
    "TrustServerCertificate=yes;"
)

with pyodbc.connect(connection_string) as conn:
    cursor = conn.cursor()
    
    # Get products with category
    cursor.execute("""
        SELECT TOP 5
            p.ProductName,
            p.UnitPrice,
            c.CategoryName
        FROM Products p
        JOIN Categories c ON p.CategoryID = c.CategoryID
        WHERE p.UnitPrice > 20
        ORDER BY p.UnitPrice DESC
    """)
    
    print("Expensive products (Raw SQL):")
    for row in cursor.fetchall():
        print(f"  {row.ProductName}: ${row.UnitPrice:.2f} ({row.CategoryName})")
```

### ORM Approach (Preview)

With SQLAlchemy (we'll learn details in Lesson 03-04):

```python
from sqlalchemy import create_engine, select, MetaData, Table

engine = create_engine(
    "mssql+pyodbc://SA:61eF92j4VTtl@localhost:1433/Northwind"
    "?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes",
    echo=True
)

metadata = MetaData()
products = Table('Products', metadata, autoload_with=engine)
categories = Table('Categories', metadata, autoload_with=engine)

# Build query
stmt = (
    select(products.c.ProductName, products.c.UnitPrice, categories.c.CategoryName)
    .join(categories, products.c.CategoryID == categories.c.CategoryID)
    .where(products.c.UnitPrice > 20)
    .order_by(products.c.UnitPrice.desc())
    .limit(5)
)

with engine.connect() as conn:
    result = conn.execute(stmt)
    
    print("\nExpensive products (ORM):")
    for row in result:
        print(f"  {row.ProductName}: ${row.UnitPrice:.2f} ({row.CategoryName})")

# Both produce the same results!
# ORM version shows the generated SQL with echo=True
```

**Observation:** For this simple query, both approaches work. Raw SQL is more concise and direct. ORM provides type safety and can help catch errors at development time.

## Key Takeaways

- **ORMs are wrappers** - They generate SQL, they don't replace it
- **Use ORMs for backend apps** - CRUD operations, operational databases
- **Use raw SQL for analytics** - Data warehouses, complex queries, bulk operations
- **Always see the SQL** - Enable logging (`echo=True`), understand what's generated
- **Know both approaches** - The best engineers use the right tool for the job
- **In data engineering** - You'll mostly use raw SQL with drivers for analytical workloads
- **For application development** - ORMs can boost productivity

## What's Next?

Now that you understand when to use ORMs and when to use raw SQL, let's learn how to define models and map tables to Python classes.

**Next lesson:** [Defining Models - Tables as Python Classes](03-defining-models.md)

---

[← Back: Database Fundamentals](01-python-database-fundamentals.md) | [Course Home](README.md) | [Next: Defining Models →](03-defining-models.md)
