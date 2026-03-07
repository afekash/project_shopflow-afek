---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# ORM Concepts: When to Use, When to Avoid

```{note}
This lesson requires the ORM lab. Run `make lab-orm` before starting.
```

## Overview

Object-Relational Mapping (ORM) frameworks sit between your application code and the database driver. They provide a higher-level abstraction — but understanding what they do, and crucially **when not to use them**, is essential for data engineers.

## What is an ORM?

**ORM (Object-Relational Mapping)** maps database tables to Python classes, and rows to Python objects.

**The key insight:** An ORM is a **wrapper around the driver**. It still sends SQL to the database — it just generates that SQL for you.

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

**Critical understanding:** The ORM doesn't talk directly to the database. It uses the driver underneath — just like your raw SQL code does.

## What ORMs Provide

### 1. Object Mapping vs. Tuples

Without an ORM you get back tuples and must access columns by index:

```{code-cell} python
import os
import psycopg2

conn = psycopg2.connect(
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
)
cur = conn.cursor()

# Create a tiny demo table
cur.execute("DROP TABLE IF EXISTS demo_customers")
cur.execute("""
    CREATE TABLE demo_customers (
        id           SERIAL PRIMARY KEY,
        company_name TEXT NOT NULL,
        contact_name TEXT NOT NULL
    )
""")
cur.executemany(
    "INSERT INTO demo_customers (company_name, contact_name) VALUES (%s, %s)",
    [("Acme Corp", "Alice"), ("Beta Ltd", "Bob"), ("Gamma GmbH", "Charlie")],
)
conn.commit()

cur.execute("SELECT id, company_name, contact_name FROM demo_customers LIMIT 1")
row = cur.fetchone()
print(f"(ID: {row[0]}) - (Company: {row[1]}) - (Contact: {row[2]})")  # index access
conn.close()
```

With an ORM you access rows as object attributes — we'll see this in detail in Lesson 03.

### 2. SQL Generation

ORMs build SQL from Python expressions. SQLAlchemy lets you inspect the generated SQL:

```{code-cell} python
from sqlalchemy import create_engine, select, MetaData, Table
import os

db_url = (
    f"postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
)

engine = create_engine(db_url, echo=True)  # echo=True shows every SQL statement

metadata = MetaData()
customers = Table("demo_customers", metadata, autoload_with=engine)
print(f"Columns: {[c.name for c in customers.columns]}")
```

```{code-cell} python
# Build a query as a Python expression — no string concatenation needed
stmt = select(customers).where(customers.c.company_name.like("%Ltd%"))

print("Generated SQL:")
print(stmt)
```

```{code-cell} python
with engine.connect() as conn:
    result = conn.execute(stmt)
    for row in result:
        print(f"  {row.id}: {row.company_name}")
```

### 3. Database Portability

The same ORM model works across databases — just change the connection string:

```python
# SQLite (development / tests)
engine = create_engine("sqlite:///dev.db")

# PostgreSQL (production)
engine = create_engine("postgresql+psycopg2://user:pass@localhost/prod")

# MySQL
engine = create_engine("mysql+mysqlconnector://user:pass@localhost/prod")

# Models and queries stay the same!
```

### 4. Transaction Management

Raw DB-API requires manual `commit` / `rollback`. ORMs handle this via the Session:

```python
# ORM session — details in Lesson 04
with Session(engine) as session:
    session.add(User(name="Alice"))
    session.add(Order(user_id=1, total=99.99))
    session.commit()  # commits both, or rolls back both on error
```

## When to Use an ORM

### ✓ Backend Applications and APIs

```python
# REST API endpoint — ORM keeps the code clean
@app.post("/products")
def create_product(data: ProductCreate):
    product = Product(name=data.name, price=data.price)
    session.add(product)
    session.commit()
    return {"id": product.id}
```

**Why ORM works here:**
- CRUD operations map naturally to Python objects
- Schema changes stay in code (schema as code)
- Developer productivity matters more than query micro-optimization

### ✓ Operational Databases

- Small-to-medium datasets (thousands to millions of rows)
- Transactional workloads (CRUD)
- Relationships between entities (users, orders, products)

### ✓ Testing and Development

```python
# In-memory SQLite — instant, zero setup (details in Lesson 05)
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
```

## When NOT to Use an ORM

### ✗ Analytical Databases (Snowflake, BigQuery, Redshift)

Complex analytical queries are far clearer as raw SQL:

```{code-cell} python
import os
import psycopg2
import random
from datetime import date, timedelta

conn = psycopg2.connect(
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
)
cur = conn.cursor()

# Seed demo data
cur.execute("DROP TABLE IF EXISTS demo_orders CASCADE")
cur.execute("""
    CREATE TABLE demo_orders (
        id          SERIAL PRIMARY KEY,
        customer_id INT REFERENCES demo_customers(id),
        revenue     NUMERIC(10,2),
        order_date  DATE
    )
""")
for cid in range(1, 4):
    for _ in range(random.randint(3, 8)):
        cur.execute(
            "INSERT INTO demo_orders (customer_id, revenue, order_date) VALUES (%s, %s, %s)",
            (cid, round(random.uniform(50, 500), 2), date.today() - timedelta(days=random.randint(0, 365))),
        )
conn.commit()
print("Demo data seeded")
```

```{code-cell} python
# Complex analytical query — exact control is essential
cur.execute("""
    SELECT
        c.company_name,
        COUNT(o.id)      AS orders,
        SUM(o.revenue)   AS total_revenue,
        AVG(o.revenue)   AS avg_order
    FROM demo_customers c
    LEFT JOIN demo_orders o ON c.id = o.customer_id
    GROUP BY c.company_name
    ORDER BY total_revenue DESC
""")

print(f"{'Company':<15} {'Orders':<8} {'Revenue':>12} {'Avg Order':>12}")
print("-" * 52)
for company, orders, revenue, avg in cur.fetchall():
    print(f"{company:<15} {orders:<8} ${float(revenue or 0):>10,.2f} ${float(avg or 0):>10,.2f}")

conn.close()
```

**Why NOT ORM:**
- You need exact query plans for cost optimization
- Window functions, CTEs, complex aggregations — ORM builders become unreadable
- Analytical databases charge per bytes scanned; you must control every query

### ✗ ETL Pipelines and Bulk Inserts

```python
# ❌ DON'T: ORM object-per-row is extremely slow at scale
for row in million_rows:
    session.add(Product(name=row["name"], price=row["price"]))
session.commit()

# ✓ DO: bulk insert via driver
cursor.executemany("INSERT INTO products (name, price) VALUES (%s, %s)", rows)
conn.commit()
```

## Real-World Decision Framework

| Question | ORM ✓ | Raw SQL ✓ |
|----------|-------|-----------|
| Is this a CRUD application? | Yes | No |
| Are queries simple? | Yes | No |
| Is data volume small (<1M rows per query)? | Yes | No |
| Is developer productivity the priority? | Yes | Maybe |
| Is query cost a concern? | No | Yes |
| Complex aggregations, window functions, CTEs? | No | Yes |
| Is this an analytical database? | No | Yes |
| Bulk inserts or ETL (>10K rows at a time)? | No | Yes |

## Direct Comparison: Raw SQL vs ORM

```{code-cell} python
import os
import psycopg2

conn = psycopg2.connect(
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
)
cur = conn.cursor()

cur.execute("""
    SELECT c.company_name, COUNT(o.id) AS order_count
    FROM demo_customers c
    LEFT JOIN demo_orders o ON c.id = o.customer_id
    GROUP BY c.company_name
    ORDER BY order_count DESC
""")
print("Top customers (raw SQL):")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} orders")

conn.close()
```

```{code-cell} python
from sqlalchemy import create_engine, select, func, MetaData, Table
import os

db_url = (
    f"postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
)
engine = create_engine(db_url, echo=True)

metadata  = MetaData()
customers = Table("demo_customers", metadata, autoload_with=engine)
orders    = Table("demo_orders",    metadata, autoload_with=engine)

stmt = (
    select(customers.c.company_name, func.count(orders.c.id).label("order_count"))
    .join(orders, customers.c.id == orders.c.customer_id, isouter=True)
    .group_by(customers.c.company_name)
    .order_by(func.count(orders.c.id).desc())
)

with engine.connect() as conn:
    print("\nTop customers (SQLAlchemy Core):")
    for row in conn.execute(stmt):
        print(f"  {row.company_name}: {row.order_count} orders")
```

Both produce the same result. For this simple query either approach is fine. As complexity grows, raw SQL scales more gracefully.

## Cleanup

```{code-cell} python
import os
import psycopg2

conn = psycopg2.connect(
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
)
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS demo_orders CASCADE")
cur.execute("DROP TABLE IF EXISTS demo_customers CASCADE")
conn.commit()
conn.close()
print("Demo tables cleaned up")
```

## Key Takeaways

- **ORMs are wrappers** — they generate SQL, they don't replace it
- **Use ORMs for backend apps** — CRUD operations, operational databases
- **Use raw SQL for analytics** — data warehouses, complex queries, bulk operations
- **Always see the SQL** — enable `echo=True`, understand what's generated
- **Know both approaches** — the best engineers use the right tool for the job

## What's Next?

Now that you understand when to use ORMs and when to use raw SQL, let's learn how to define models and map tables to Python classes.

**Next lesson:** [Defining Models - Tables as Python Classes](03-defining-models.md)

---

[← Back: Database Fundamentals](01-python-database-fundamentals.md) | [Course Home](README.md) | [Next: Defining Models →](03-defining-models.md)
