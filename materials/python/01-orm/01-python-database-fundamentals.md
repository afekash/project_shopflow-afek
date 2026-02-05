# Python Database Fundamentals

## Overview

Before diving into ORMs, you need to understand how Python applications communicate with databases at a fundamental level. This foundation will help you appreciate what ORMs do and when to bypass them.

In this lesson, we'll connect to the **Northwind database** that we set up in the SQL course, giving you hands-on experience with real database operations.

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

**Key Insight:** ORMs don't replace SQL - they generate it for you. Understanding the driver layer helps you debug issues and know when to drop to raw SQL.

## What is a Database Driver?

A **database driver** is software that enables Python to communicate with a specific database system.

**Core Functions:**

- Translates Python method calls into database-specific network protocols
- Sends SQL statements as text strings over the network (or to local file)
- Parses results and returns them as Python data structures
- Manages connections, authentication, and error handling

**Each database has its own driver:**

| Database | Python Driver | Install Command |
|----------|---------------|-----------------|
| SQLite | `sqlite3` | Built into Python |
| PostgreSQL | `psycopg2` | `pip install psycopg2-binary` |
| MySQL | `mysql-connector-python` | `pip install mysql-connector-python` |
| SQL Server | `pyodbc` | `pip install pyodbc` |
| Snowflake | `snowflake-connector-python` | `pip install snowflake-connector-python` |
| BigQuery | `google-cloud-bigquery` | `pip install google-cloud-bigquery` |

## Python DB-API 2.0 (PEP 249)

Python defines a **standard interface** that all database drivers should implement, called **DB-API 2.0** (defined in PEP 249).

This means the basic workflow is the same across all databases:

1. **Connect** - Establish connection to database
2. **Cursor** - Create a cursor object to execute queries
3. **Execute** - Send SQL statement
4. **Fetch** - Retrieve results
5. **Commit** - Save changes (for writes)
6. **Close** - Clean up connection

**Why this matters:** Understanding DB-API helps you work with any database, even if there's no ORM support.

## Connecting to Northwind Database

Let's connect to the Northwind database we set up in the SQL course. This gives us a real database with actual data to work with.

**Connection Details:**
- **Server**: `localhost,1433`
- **Database**: `Northwind`
- **User**: `SA`
- **Password**: `61eF92j4VTtl`

### Installing the SQL Server Driver

```bash
pip install pyodbc
```

### Import the Driver

```python
import pyodbc
```

### Establish Connection

```python
# Connection string for SQL Server
connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=Northwind;"
    "UID=SA;"
    "PWD=61eF92j4VTtl;"
    "TrustServerCertificate=yes;"
)

# Connect to Northwind
conn = pyodbc.connect(connection_string)
print(f"Connected to Northwind database")
print(f"Connection: {conn}")
```

### Create a Cursor

```python
# Create cursor for executing queries
cursor = conn.cursor()
print(f"Cursor created: {cursor}")
```

### Query Customers

Let's query the Customers table from Northwind:

```python
# Query first 5 customers
cursor.execute("SELECT TOP 5 CustomerID, CompanyName, City, Country FROM Customers")

# Fetch results
customers = cursor.fetchall()

print(f"Found {len(customers)} customers:")
for customer in customers:
    print(f"  {customer.CustomerID}: {customer.CompanyName} ({customer.City}, {customer.Country})")
```

### Query Products with Price Information

```python
# Query products with their categories and prices
cursor.execute("""
    SELECT TOP 5 
        ProductName, 
        UnitPrice, 
        UnitsInStock,
        (UnitPrice * UnitsInStock) AS InventoryValue
    FROM Products
    WHERE Discontinued = 0
    ORDER BY UnitPrice DESC
""")

products = cursor.fetchall()

print("Most expensive products in stock:")
for product in products:
    print(f"  {product.ProductName}: ${product.UnitPrice:.2f} "
          f"({product.UnitsInStock} units, value: ${product.InventoryValue:.2f})")
```

### Parameterized Queries (SQL Injection Prevention)

```python
# NEVER do this (vulnerable to SQL injection):
# country = input("Enter country: ")
# cursor.execute(f"SELECT * FROM Customers WHERE Country = '{country}'")

# ALWAYS use parameterized queries:
country = "Germany"
cursor.execute("""
    SELECT CustomerID, CompanyName, City 
    FROM Customers 
    WHERE Country = ?
""", country)

german_customers = cursor.fetchall()

print(f"Customers in {country}:")
for customer in german_customers:
    print(f"  {customer.CustomerID}: {customer.CompanyName} ({customer.City})")
```

### Close Connection

```python
# Always close connections when done
cursor.close()
conn.close()
print("Connection closed")
```

## Comparison: SQLite vs SQL Server

Let's see how the same operations work with SQLite (file-based database):

### SQLite: Creating a Database

```python
import sqlite3
import os

# Drop the database if it exists
if os.path.exists("example.db"):
    os.remove("example.db")

# SQLite - creates file
conn = sqlite3.connect("example.db")
print(f"SQLite connection: {conn}")
```

### SQLite: Create Table and Insert Data

```python
cursor = conn.cursor()

# Create table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
print("Table created")
```

### SQLite: Insert Data

```python
# Insert single user
cursor.execute(
    "INSERT INTO users (name, email) VALUES (?, ?)",
    ("Alice", "alice@example.com")
)
print(f"Inserted user, last ID: {cursor.lastrowid}")
```

### SQLite: Insert Multiple Rows

```python
# Insert multiple rows
users_data = [
    ("Bob", "bob@example.com"),
    ("Charlie", "charlie@example.com"),
    ("Diana", "diana@example.com"),
]
cursor.executemany(
    "INSERT INTO users (name, email) VALUES (?, ?)",
    users_data
)

# Commit changes
conn.commit()
print(f"Inserted {cursor.rowcount} users")
```

### SQLite: Query Data

```python
# Query all users
cursor.execute("SELECT id, name, email FROM users ORDER BY name")

rows = cursor.fetchall()
print(f"Found {len(rows)} users:")
for row in rows:
    print(f"  ID {row[0]}: {row[1]} ({row[2]})")
```

### SQLite: Dictionary-Style Access

```python
# Enable dictionary-style access
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT id, name, email FROM users WHERE id = 1")
row = cursor.fetchone()

# Access by column name
print(f"User: {row['name']}")
print(f"Email: {row['email']}")
print(f"ID: {row['id']}")
```

### SQLite: Close Connection

```python
cursor.close()
conn.close()
print("SQLite connection closed")
```

## Using Context Managers (Best Practice)

Always use context managers to ensure connections are properly closed, even if errors occur:

### SQL Server with Context Manager

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

# Connection automatically closes when exiting 'with' block
with pyodbc.connect(connection_string) as conn:
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM Customers")
    count = cursor.fetchone()[0]
    
    print(f"Northwind has {count} customers")

# Connection automatically closed here
```

### SQLite with Context Manager

```python
import sqlite3

with sqlite3.connect("example.db") as conn:
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    
    print(f"Database has {count} users")
    
# Connection automatically closed
```

## Transactions

Transactions ensure that multiple operations either all succeed or all fail together.

### Transaction Example

```python
import sqlite3

conn = sqlite3.connect("bank.db")
cursor = conn.cursor()

# Create accounts table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        account_id INTEGER PRIMARY KEY,
        balance REAL
    )
""")

# Insert test accounts
cursor.execute("INSERT OR REPLACE INTO accounts VALUES (1, 1000.0)")
cursor.execute("INSERT OR REPLACE INTO accounts VALUES (2, 500.0)")
conn.commit()
print("Initial accounts created")
```

### Transfer Money Between Accounts

```python
# Transfer $100 from account 1 to account 2
try:
    # Start transaction (implicit in Python DB-API)
    cursor.execute(
        "UPDATE accounts SET balance = balance - 100 WHERE account_id = 1"
    )
    cursor.execute(
        "UPDATE accounts SET balance = balance + 100 WHERE account_id = 2"
    )
    
    # Commit if both succeed
    conn.commit()
    print("Transfer successful")
    
except Exception as e:
    # Rollback if anything fails
    conn.rollback()
    print(f"Transfer failed: {e}")
```

### Verify Transfer

```python
cursor.execute("SELECT account_id, balance FROM accounts")
accounts = cursor.fetchall()

print("Account balances:")
for account in accounts:
    print(f"  Account {account[0]}: ${account[1]:.2f}")

conn.close()
```

## Advanced Note: Connection Strings

Different databases use different connection formats:

### SQLite

```python
# File-based
sqlite3.connect("path/to/database.db")

# In-memory (database exists only in RAM)
sqlite3.connect(":memory:")
```

### SQL Server (pyodbc)

```python
# Connection string format
pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=Northwind;"
    "UID=SA;"
    "PWD=61eF92j4VTtl;"
    "TrustServerCertificate=yes;"
)
```

### PostgreSQL (psycopg2)

```python
import psycopg2

# Connection parameters
psycopg2.connect(
    host="localhost",
    port=5432,
    database="mydb",
    user="user",
    password="pass"
)

# Or as connection string
psycopg2.connect("postgresql://user:pass@localhost:5432/mydb")
```

## Why This Matters for Data Engineering

In data engineering, especially when working with **analytical databases** (Snowflake, BigQuery, Redshift), you'll often use drivers directly with raw SQL:

**Reasons to use drivers + raw SQL:**

1. **Exact query control** - You write exactly what executes
2. **Cost optimization** - Analytical databases charge per query; you need to optimize
3. **Complex analytics** - Window functions, CTEs, advanced aggregations
4. **No abstraction overhead** - Direct communication with database
5. **Database-specific features** - COPY commands, clustering, partitioning

### Example: Analytical Query with Northwind

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
    
    # Complex analytical query - you want EXACT control
    cursor.execute("""
        SELECT 
            c.Country,
            COUNT(DISTINCT c.CustomerID) as CustomerCount,
            COUNT(o.OrderID) as TotalOrders,
            SUM(od.UnitPrice * od.Quantity) as TotalRevenue,
            AVG(od.UnitPrice * od.Quantity) as AvgOrderValue
        FROM Customers c
        LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
        LEFT JOIN [Order Details] od ON o.OrderID = od.OrderID
        GROUP BY c.Country
        HAVING COUNT(o.OrderID) > 5
        ORDER BY TotalRevenue DESC
    """)
    
    print("Top countries by revenue:")
    print(f"{'Country':<15} {'Customers':<12} {'Orders':<10} {'Revenue':<15} {'Avg Order'}")
    print("-" * 70)
    
    for row in cursor.fetchall():
        print(f"{row.Country:<15} {row.CustomerCount:<12} {row.TotalOrders:<10} "
              f"${row.TotalRevenue:>12,.2f} ${row.AvgOrderValue:>10,.2f}")
```

**Why not use ORM here?**

- This query is too complex for typical ORM patterns
- You need exact control for cost optimization
- The ORM might generate suboptimal SQL
- No need for object mapping - you just want the data

## Practice Exercises

### Exercise 1: Query Northwind Orders

Connect to Northwind and find:
1. Total number of orders
2. Orders from the last month (use `DATEADD`)
3. Top 5 customers by order count

```python
# TODO: Write queries to answer the questions above
```

### Exercise 2: Create a Sales Report

Using the Northwind database, create a report showing:
- Product name
- Total quantity sold
- Total revenue
- Only products with revenue > $10,000

```python
# TODO: Write a query with JOIN and aggregation
```

### Exercise 3: Compare SQLite and SQL Server

Create the same simple table in both SQLite and SQL Server:
1. Create a `categories` table (id, name, description)
2. Insert 3 categories
3. Query all categories

```python
# TODO: Implement for both databases
```

## Key Takeaways

- **Drivers are the foundation** - All Python database access uses drivers
- **DB-API 2.0 is standard** - Same pattern across all databases
- **Raw SQL gives control** - You see exactly what executes
- **Results are tuples** - No automatic object mapping
- **Parameterized queries** - Always use placeholders to prevent SQL injection
- **Context managers** - Always use `with` for automatic cleanup
- **Analytical workloads** - Use drivers directly, not ORMs
- **Operational workloads** - ORMs can help (covered in next lesson)

## What's Next?

Now that you understand how Python communicates with databases at the driver level, you're ready to learn what ORMs add on top of this foundation.

**Next lesson:** [ORM Concepts - When to Use, When to Avoid](02-orm-concepts.md)

---

[← Back: Module README](README.md) | [Course Home](../../README.md) | [Next: ORM Concepts →](02-orm-concepts.md)
