# Defining Models: Tables as Python Classes

## Overview

In ORMs, database tables are represented as Python classes, and rows become instances of those classes. This lesson covers how to define models using SQLAlchemy 2.0's declarative syntax.

We'll create a **Bookstore database** that we'll use throughout this module for practicing ORM operations.

## Core Concept: Models = Tables

A **model** is a Python class that represents a database table:

```python
# This Python class...
class Author(Base):
    __tablename__ = "authors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

# ...creates this SQL table:
# CREATE TABLE authors (
#     id INTEGER PRIMARY KEY,
#     name VARCHAR(100) NOT NULL
# )
```

**Key insight:** The ORM translates your Python class into SQL DDL (Data Definition Language) and generates SQL queries based on your model structure.

## The Bookstore Domain

Throughout this module, we'll build a **Bookstore database** with these entities:

- **Authors** - Writers of books
- **Publishers** - Companies that publish books
- **Books** - Products in our bookstore
- **Sales** - Records of book purchases

This gives us a realistic domain to practice CRUD operations, relationships, and queries.

## Setting Up SQLAlchemy 2.0

### Install SQLAlchemy

```bash
pip install sqlalchemy
```

### Import Required Components

```python
from sqlalchemy import create_engine, String, ForeignKey, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from datetime import date
from decimal import Decimal
from typing import Optional
```

### Define Base Class

```python
# Base class for all models (define once per project)
class Base(DeclarativeBase):
    pass

print("Base class defined")
```

### Create SQLite Engine

```python
# Create SQLite database file
engine = create_engine("sqlite:///bookstore.db", echo=True)
print(f"Engine created: {engine}")
print(f"Database URL: {engine.url}")
```

**Note:** `echo=True` shows all SQL statements - essential for learning!

## Progressive Model Building

Let's build our models step by step, starting simple and adding complexity.

### Step 1: First Model - Author

```python
class Author(Base):
    __tablename__ = "authors"
    __table_args__ = {'extend_existing': True} 
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Basic columns
    name: Mapped[str] = mapped_column(String(100))
    birth_year: Mapped[Optional[int]]  # Optional - can be NULL
    
    # String representation
    def __repr__(self):
        return f"Author(id={self.id}, name={self.name!r}, birth_year={self.birth_year})"

print("Author model defined")
```

### Create the Authors Table

```python
# Create only the authors table
Base.metadata.create_all(engine, tables=[Author.__table__])
print("Authors table created in database")

# The echo=True shows the generated SQL:
# CREATE TABLE authors (
#     id INTEGER NOT NULL PRIMARY KEY,
#     name VARCHAR(100) NOT NULL,
#     birth_year INTEGER
# )
```

### Verify Table Creation

```python
# Check that the table exists
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Tables in database: {tables}")

# Get column info
columns = inspector.get_columns('authors')
print(f"\nAuthors table columns:")
for col in columns:
    print(f"  - {col['name']}: {col['type']} (nullable={col['nullable']})")
```

### Step 2: Add Publisher Model

```python
class Publisher(Base):
    __tablename__ = "publishers"
    __table_args__ = {'extend_existing': True} 
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(50))
    
    def __repr__(self):
        return f"Publisher(id={self.id}, name={self.name!r}, country={self.country!r})"

print("Publisher model defined")
```

### Create Publishers Table

```python
# Create the publishers table
Base.metadata.create_all(engine, tables=[Publisher.__table__])
print("Publishers table created")
```

### Step 3: Add Book Model with Relationships

```python
class Book(Base):
    __tablename__ = "books"
    __table_args__ = {'extend_existing': True} 
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Basic info
    title: Mapped[str] = mapped_column(String(200))
    isbn: Mapped[str] = mapped_column(String(13), unique=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))  # 10 digits, 2 decimal places
    
    # Foreign keys
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    publisher_id: Mapped[int] = mapped_column(ForeignKey("publishers.id"))
    
    # Relationships (ORM navigation - not in database schema)
    author: Mapped["Author"] = relationship(back_populates="books")
    publisher: Mapped["Publisher"] = relationship(back_populates="books")
    
    def __repr__(self):
        return f"Book(id={self.id}, title={self.title!r}, isbn={self.isbn!r}, price={self.price})"

print("Book model defined")
```

### Update Author and Publisher with Reverse Relationships

```python
# Redefine Author with books relationship
class Author(Base):
    __tablename__ = "authors"
    __table_args__ = {'extend_existing': True} 
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    birth_year: Mapped[Optional[int]]
    
    # Relationship - access author.books to get all their books
    books: Mapped[list["Book"]] = relationship(back_populates="author")
    
    def __repr__(self):
        return f"Author(id={self.id}, name={self.name!r})"

# Redefine Publisher with books relationship
class Publisher(Base):
    __tablename__ = "publishers"
    __table_args__ = {'extend_existing': True} 
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(50))
    
    # Relationship
    books: Mapped[list["Book"]] = relationship(back_populates="publisher")
    
    def __repr__(self):
        return f"Publisher(id={self.id}, name={self.name!r})"

print("Models updated with relationships")
```

### Create Books Table

```python
# Create the books table (with foreign keys)
Base.metadata.create_all(engine, tables=[Book.__table__])
print("Books table created with foreign keys")

# SQL generated includes:
# CREATE TABLE books (
#     id INTEGER NOT NULL PRIMARY KEY,
#     title VARCHAR(200) NOT NULL,
#     isbn VARCHAR(13) NOT NULL UNIQUE,
#     price NUMERIC(10, 2) NOT NULL,
#     author_id INTEGER NOT NULL,
#     publisher_id INTEGER NOT NULL,
#     FOREIGN KEY(author_id) REFERENCES authors (id),
#     FOREIGN KEY(publisher_id) REFERENCES publishers (id)
# )
```

### Step 4: Add Sales Model

```python
class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = {'extend_existing': True} 
    
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    quantity: Mapped[int]
    sale_date: Mapped[date]
    
    # Relationship
    book: Mapped["Book"] = relationship(back_populates="sales")
    
    def __repr__(self):
        return f"Sale(id={self.id}, book_id={self.book_id}, quantity={self.quantity}, date={self.sale_date})"

print("Sale model defined")
```

### Update Book with Sales Relationship

```python
# Redefine Book with sales relationship
class Book(Base):
    __tablename__ = "books"
    __table_args__ = {'extend_existing': True} 
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    isbn: Mapped[str] = mapped_column(String(13), unique=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    publisher_id: Mapped[int] = mapped_column(ForeignKey("publishers.id"))
    
    # Relationships
    author: Mapped["Author"] = relationship(back_populates="books")
    publisher: Mapped["Publisher"] = relationship(back_populates="books")
    sales: Mapped[list["Sale"]] = relationship(back_populates="book")
    
    def __repr__(self):
        return f"Book(id={self.id}, title={self.title!r}, price={self.price})"

print("Book model updated with sales relationship")
```

### Create Sales Table

```python
# Create the sales table
Base.metadata.create_all(engine, tables=[Sale.__table__])
print("Sales table created")
```

## Complete Schema Creation

Now let's see all our models together and create the complete schema:

### Complete Bookstore Models

```python
from sqlalchemy import create_engine, String, ForeignKey, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import date
from decimal import Decimal
from typing import Optional

class Base(DeclarativeBase):
    pass

class Author(Base):
    __tablename__ = "authors"
    __table_args__ = {'extend_existing': True} 
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    birth_year: Mapped[Optional[int]]
    
    books: Mapped[list["Book"]] = relationship(back_populates="author")
    
    def __repr__(self):
        return f"Author(id={self.id}, name={self.name!r})"

class Publisher(Base):
    __tablename__ = "publishers"
    __table_args__ = {'extend_existing': True} 
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(50))
    
    books: Mapped[list["Book"]] = relationship(back_populates="publisher")
    
    def __repr__(self):
        return f"Publisher(id={self.id}, name={self.name!r})"

class Book(Base):
    __tablename__ = "books"
    __table_args__ = {'extend_existing': True} 
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    isbn: Mapped[str] = mapped_column(String(13), unique=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    publisher_id: Mapped[int] = mapped_column(ForeignKey("publishers.id"))
    
    author: Mapped["Author"] = relationship(back_populates="books")
    publisher: Mapped["Publisher"] = relationship(back_populates="books")
    sales: Mapped[list["Sale"]] = relationship(back_populates="book")
    
    def __repr__(self):
        return f"Book(id={self.id}, title={self.title!r})"

class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = {'extend_existing': True} 
    
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    quantity: Mapped[int]
    sale_date: Mapped[date]
    
    book: Mapped["Book"] = relationship(back_populates="sales")
    
    def __repr__(self):
        return f"Sale(id={self.id}, quantity={self.quantity})"

print("All models defined")
```

### Create All Tables at Once

```python
import os

# Drop the database if it exists
if os.path.exists("bookstore.db"):
    os.remove("bookstore.db")

# Create engine
engine = create_engine("sqlite:///bookstore.db", echo=True)

# Create all tables
Base.metadata.create_all(engine)

print("\n✓ Bookstore database created successfully!")
print("Tables: authors, publishers, books, sales")
```

### Verify Complete Schema

```python
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"\nTables in bookstore.db: {tables}")

for table_name in tables:
    columns = inspector.get_columns(table_name)
    foreign_keys = inspector.get_foreign_keys(table_name)
    
    print(f"\n{table_name.upper()} Table:")
    print("  Columns:")
    for col in columns:
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        print(f"    - {col['name']}: {col['type']} {nullable}")
    
    if foreign_keys:
        print("  Foreign Keys:")
        for fk in foreign_keys:
            print(f"    - {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}")
```

## Python Type to SQL Type Mapping

SQLAlchemy automatically maps Python types to SQL types:

| Python Type | SQLAlchemy Type | SQL Type (SQLite) | SQL Type (SQL Server) |
|-------------|-----------------|-------------------|-----------------------|
| `int` | Integer | INTEGER | INT |
| `str` | String/Text | VARCHAR/TEXT | VARCHAR/NVARCHAR |
| `float` | Float | REAL | FLOAT |
| `bool` | Boolean | BOOLEAN | BIT |
| `datetime` | DateTime | TIMESTAMP | DATETIME |
| `date` | Date | DATE | DATE |
| `Decimal` | Numeric | NUMERIC | DECIMAL |
| `bytes` | LargeBinary | BLOB | VARBINARY |

## Column Constraints

### Primary Keys

```python
# Auto-incrementing primary key
id: Mapped[int] = mapped_column(primary_key=True)
```

### Unique Constraints

```python
# Single column unique
isbn: Mapped[str] = mapped_column(String(13), unique=True)

# Multiple column unique (in __table_args__)
from sqlalchemy import UniqueConstraint

class Book(Base):
    __tablename__ = "books"
    # ... columns ...
    
    __table_args__ = (
        UniqueConstraint('title', 'author_id', name='unique_title_per_author'),
    )
```

### Not Null vs Nullable

```python
# Required (NOT NULL) - default for Mapped[type]
name: Mapped[str] = mapped_column(String(100))

# Optional (NULL allowed) - use Optional[]
birth_year: Mapped[Optional[int]]
subtitle: Mapped[Optional[str]] = mapped_column(String(200))
```

### Default Values

```python
from datetime import datetime

# Python-side default
created_at: Mapped[datetime] = mapped_column(default=datetime.now)
is_active: Mapped[bool] = mapped_column(default=True)

# Database-side default
quantity: Mapped[int] = mapped_column(server_default="0")
```

## Relationships Explained

### One-to-Many Relationship

**Example:** One author has many books

```python
class Author(Base):
    __tablename__ = "authors"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    
    # One author -> many books
    books: Mapped[list["Book"]] = relationship(back_populates="author")

class Book(Base):
    __tablename__ = "books"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    
    # Foreign key (in database)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    
    # Relationship (ORM navigation - not in database)
    author: Mapped["Author"] = relationship(back_populates="books")
```

**Key points:**
- `ForeignKey("authors.id")` creates the actual database constraint
- `relationship()` is for ORM navigation (Python-side only)
- `back_populates` establishes bidirectional relationship

### Using Relationships

```python
from sqlalchemy.orm import Session

with Session(engine) as session:
    # Create author with books
    author = Author(name="J.K. Rowling", birth_year=1965)
    author.books = [
        Book(
            title="Harry Potter and the Philosopher's Stone",
            isbn="9780747532699",
            price=Decimal("19.99"),
            publisher_id=1  # Assuming publisher exists
        ),
        Book(
            title="Harry Potter and the Chamber of Secrets",
            isbn="9780747538493",
            price=Decimal("19.99"),
            publisher_id=1
        ),
    ]
    
    session.add(author)
    session.commit()
    
    print(f"Created {author.name} with {len(author.books)} books")
```

## Creating the Same Schema on SQL Server

The beauty of ORMs is database portability. Here's how to create the same schema on SQL Server:

### SQL Server Connection

```python
# SQL Server connection string
sqlserver_engine = create_engine(
    "mssql+pyodbc://SA:61eF92j4VTtl@localhost:1433/master"
    "?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes",
    echo=True
)
```

### Create Database on SQL Server

```python
import pyodbc

# Connect to master database to create our database
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=master;"
    "UID=SA;"
    "PWD=61eF92j4VTtl;"
    "TrustServerCertificate=yes;"
)
conn.autocommit = True
cursor = conn.cursor()

# Drop if exists, then create
try:
    cursor.execute("DROP DATABASE IF EXISTS BookstoreDB")
    print("Dropped existing BookstoreDB")
except:
    pass

cursor.execute("CREATE DATABASE BookstoreDB")
print("Created BookstoreDB")

conn.close()
```

### Create Tables on SQL Server

```python
# Connect to the new database
sqlserver_engine = create_engine(
    "mssql+pyodbc://SA:61eF92j4VTtl@localhost:1433/BookstoreDB"
    "?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes",
    echo=True
)

# Create all tables (same models!)
Base.metadata.create_all(sqlserver_engine)

print("✓ Tables created on SQL Server")
```

### Verify SQL Server Schema

```python
from sqlalchemy import inspect

inspector = inspect(sqlserver_engine)
tables = inspector.get_table_names()

print(f"\nTables in SQL Server BookstoreDB: {tables}")
```

**The same model code works on both databases!** Only the connection string changes.

## Database Configuration Pattern

For easy switching between databases:

```python
# Database configuration
SQLITE_URL = "sqlite:///bookstore.db"
SQLSERVER_URL = (
    "mssql+pyodbc://SA:61eF92j4VTtl@localhost:1433/BookstoreDB"
    "?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
)

# Choose database
USE_SQLSERVER = False  # Change to True to use SQL Server

database_url = SQLSERVER_URL if USE_SQLSERVER else SQLITE_URL
engine = create_engine(database_url, echo=True)

print(f"Using database: {database_url}")
```

## Advanced: Indexes for Performance

Add indexes for frequently queried columns:

```python
from sqlalchemy import Index

class Book(Base):
    __tablename__ = "books"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)  # Simple index
    isbn: Mapped[str] = mapped_column(String(13), unique=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"), index=True)
    publisher_id: Mapped[int] = mapped_column(ForeignKey("publishers.id"))
    
    # Composite index
    __table_args__ = (
        Index('idx_author_publisher', 'author_id', 'publisher_id'),
    )
```

## Dropping and Recreating Tables

Useful during development:

```python
# Drop all tables
Base.metadata.drop_all(engine)
print("All tables dropped")

# Recreate all tables
Base.metadata.create_all(engine)
print("All tables recreated")
```

## Practice Exercises

### Exercise 1: Add Book Ratings

Extend the schema to support book ratings:
- Create a `Rating` model
- Add fields: id, book_id, rating (1-5), review_text, review_date
- Add relationship to Book

<details>
<summary>Solution</summary>

```python
class Rating(Base):
    __tablename__ = "ratings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    rating: Mapped[int]  # 1-5
    review_text: Mapped[Optional[str]] = mapped_column(String(500))
    review_date: Mapped[date]
    
    book: Mapped["Book"] = relationship(back_populates="ratings")

# Update Book model
class Book(Base):
    __tablename__ = "books"
    # ... existing fields ...
    
    ratings: Mapped[list["Rating"]] = relationship(back_populates="book")
```

</details>

### Exercise 2: Add Timestamps Mixin

Create a mixin that adds created_at and updated_at to any model:

<details>
<summary>Solution</summary>

```python
from datetime import datetime
from sqlalchemy import func

class TimestampMixin:
    """Mixin to add created_at and updated_at to models."""
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now,
        onupdate=datetime.now
    )

# Use it in your models
class Book(Base, TimestampMixin):
    __tablename__ = "books"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    # ... other fields ...
    # created_at and updated_at added automatically
```

</details>

## Key Takeaways

- **Models are Python classes** that represent database tables
- **`Mapped[type]`** provides type hints for columns
- **`mapped_column()`** configures column properties
- **Relationships** use `relationship()` for ORM navigation
- **Foreign keys** use `ForeignKey()` to link tables
- **Same models work across databases** - only connection string changes
- **Always enable `echo=True`** to see generated SQL
- **Schema as code** - version controlled, reproducible
- **Bookstore database** - our domain for practicing CRUD operations

## What's Next?

Now that we've defined our Bookstore models, let's learn how to perform CRUD operations (Create, Read, Update, Delete) with them.

**Next lesson:** [CRUD Operations - Working with Data](04-crud-operations.md)

---

[← Back: ORM Concepts](02-orm-concepts.md) | [Course Home](README.md) | [Next: CRUD Operations →](04-crud-operations.md)
