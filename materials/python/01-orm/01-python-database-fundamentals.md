---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Python Database Fundamentals

```{note}
This lesson requires the ORM lab. Run `make lab-orm` before starting.
```

## Overview

Before diving into ORMs, you need to understand how Python applications communicate with databases at the fundamental level. This foundation will help you appreciate what ORMs do and when to bypass them.

In this lesson we'll connect to **PostgreSQL** (the database running in our lab), explore the DB-API interface, and compare it against SQLite for contrast.

## The Big Picture: How Python Talks to Databases

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Your Python │────▶│    Driver    │────▶│   Database   │
│     Code     │     │  (DB-API)    │     │   Server     │
└──────────────┘     └──────────────┘     └──────────────┘
      │                    │                     │
      │              Sends SQL as          Executes SQL
      │              text strings          Returns rows
      │                    │                     │
      ▼                    ▼                     ▼
  ┌──────────────────────────────────────────────────┐
  │  ORM sits HERE - generates SQL for you,          │
  │  but underneath it's still sending SQL           │
  │  through the driver                              │
  └──────────────────────────────────────────────────┘
```

**Key insight:** ORMs don't replace SQL — they generate it for you. Understanding the driver layer helps you debug issues and know when to drop down to raw SQL.

## What is a Database Driver?

A **database driver** is software that enables Python to communicate with a specific database system.

**Core functions:**

- Translates Python method calls into database-specific network protocols
- Sends SQL statements as text strings over the network (or to a local file)
- Parses results and returns them as Python data structures
- Manages connections, authentication, and error handling

**Each database has its own driver:**

| Database | Python Driver | Install |
|----------|---------------|---------|
| SQLite | `sqlite3` | Built into Python |
| PostgreSQL | `psycopg2` | `psycopg2-binary` |
| MySQL | `mysql-connector-python` | `mysql-connector-python` |
| Snowflake | `snowflake-connector-python` | `snowflake-connector-python` |
| BigQuery | `google-cloud-bigquery` | `google-cloud-bigquery` |

## Python DB-API 2.0 (PEP 249)

Python defines a **standard interface** that all database drivers must implement, called **DB-API 2.0** (PEP 249).

This means the basic workflow is the same across all databases:

1. **Connect** — establish a connection
2. **Cursor** — create a cursor object to execute queries
3. **Execute** — send a SQL statement
4. **Fetch** — retrieve results
5. **Commit** — save changes (for writes)
6. **Close** — clean up the connection

**Why this matters:** You can work with any database using the same pattern, even when there's no ORM support.

## Connecting to PostgreSQL

The lab starts a PostgreSQL container and injects connection details as environment variables. Let's use them.

```{code-cell} python
import os
import psycopg2

host     = os.environ["DB_HOST"]
port     = os.environ["DB_PORT"]
dbname   = os.environ["DB_NAME"]
user     = os.environ["DB_USER"]
password = os.environ["DB_PASSWORD"]

print(f"Connecting to {user}@{host}:{port}/{dbname}")
```

### Establish a Connection

```{code-cell} python
conn = psycopg2.connect(
    host=host,
    port=port,
    dbname=dbname,
    user=user,
    password=password,
)
print(f"Connected: {conn.status}")
```

### Create a Cursor

```{code-cell} python
cursor = conn.cursor()
print(f"Cursor created: {cursor}")
```

### Run a Query

```{code-cell} python
cursor.execute("SELECT version()")
row = cursor.fetchone()
print(f"PostgreSQL version: {row[0]}")
```

### Parameterized Queries (SQL Injection Prevention)

```{code-cell} python
# NEVER do this:
# cursor.execute(f"SELECT * FROM users WHERE name = '{user_input}'")

# ALWAYS use placeholders:
name = "Alice"
cursor.execute("SELECT %s AS greeting", (f"Hello, {name}!",))
row = cursor.fetchone()
print(row[0])
```

### Close the Connection

```{code-cell} python
cursor.close()
conn.close()
print("Connection closed")
```

## Context Managers (Best Practice)

Always use context managers to ensure connections are properly closed even when errors occur.

```{code-cell} python
import os
import psycopg2

with psycopg2.connect(
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), current_user")
        db, usr = cur.fetchone()
        print(f"Database: {db}, User: {usr}")
```

## Working with Real Data

Let's create a small table and explore the full DB-API cycle.

### Create Table and Insert Rows

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

cur.execute("DROP TABLE IF EXISTS demo_users")
cur.execute("""
    CREATE TABLE demo_users (
        id   SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        city TEXT NOT NULL
    )
""")

users = [
    ("Alice",   "Tel Aviv"),
    ("Bob",     "Haifa"),
    ("Charlie", "Jerusalem"),
    ("Diana",   "Tel Aviv"),
]
cur.executemany("INSERT INTO demo_users (name, city) VALUES (%s, %s)", users)
conn.commit()
print(f"Inserted {len(users)} users")
```

### Query All Rows

```{code-cell} python
cur.execute("SELECT id, name, city FROM demo_users ORDER BY name")
rows = cur.fetchall()

print(f"Found {len(rows)} users:")
for row in rows:
    print(f"  {row[0]}: {row[1]} ({row[2]})")
```

### Dictionary-Style Access with `RealDictCursor`

```{code-cell} python
from psycopg2.extras import RealDictCursor

with conn.cursor(cursor_factory=RealDictCursor) as dict_cur:
    dict_cur.execute("SELECT * FROM demo_users WHERE city = %s", ("Tel Aviv",))
    for row in dict_cur.fetchall():
        print(f"  name={row['name']}, city={row['city']}")
```

### Transactions

```{code-cell} python
try:
    cur.execute("INSERT INTO demo_users (name, city) VALUES (%s, %s)", ("Eve", "Eilat"))
    cur.execute("INSERT INTO demo_users (name, city) VALUES (%s, %s)", ("Frank", "Beersheba"))
    conn.commit()
    print("Both rows inserted")
except Exception as e:
    conn.rollback()
    print(f"Rolled back: {e}")
```

### Cleanup

```{code-cell} python
cur.execute("DROP TABLE demo_users")
conn.commit()
cur.close()
conn.close()
print("Cleaned up")
```

## SQLite for Local Comparison

SQLite is built into Python — no server required. It's useful for lightweight local work and tests, and uses the same DB-API interface.

```{code-cell} python
import sqlite3

# In-memory SQLite database
conn = sqlite3.connect(":memory:")
cur  = conn.cursor()

cur.execute("""
    CREATE TABLE products (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        name  TEXT NOT NULL,
        price REAL NOT NULL
    )
""")
cur.executemany(
    "INSERT INTO products (name, price) VALUES (?, ?)",
    [("Laptop", 2500.0), ("Mouse", 89.90), ("Keyboard", 149.0)],
)
conn.commit()

cur.execute("SELECT name, price FROM products ORDER BY price DESC")
for name, price in cur.fetchall():
    print(f"  {name}: ${price:.2f}")

conn.close()
```

**Key difference from PostgreSQL:** placeholders are `?` in SQLite vs `%s` in psycopg2. Otherwise the pattern is identical — this is DB-API in action.

## Why This Matters for Data Engineering

In data engineering, especially for **analytical databases** (Snowflake, BigQuery, Redshift), you'll use drivers directly with raw SQL:

| Reason | Explanation |
|--------|-------------|
| Exact query control | You write exactly what executes |
| Cost optimization | Charge per query/bytes scanned — optimize everything |
| Complex analytics | Window functions, CTEs, advanced aggregations |
| No abstraction overhead | Direct communication, no object mapping |
| Database-specific features | COPY, clustering, partitioning |

## Key Takeaways

- **Drivers are the foundation** — all Python database access uses drivers
- **DB-API 2.0 is standard** — same pattern across all databases
- **Raw SQL gives control** — you see exactly what executes
- **Results are tuples by default** — no automatic object mapping
- **Parameterized queries** — always use placeholders, never f-strings with user input
- **Context managers** — always use `with` for automatic cleanup
- **Analytical workloads** — use drivers directly, not ORMs

## What's Next?

Now that you understand how Python communicates with databases at the driver level, you're ready to learn what ORMs add on top of this foundation.

**Next lesson:** [ORM Concepts - When to Use, When to Avoid](02-orm-concepts.md)

---

[← Back: Module README](README.md) | [Next: ORM Concepts →](02-orm-concepts.md)
