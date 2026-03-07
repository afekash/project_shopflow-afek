---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Defining Models: Tables as Python Classes

## Overview

In ORMs, database tables are represented as Python classes, and rows become instances of those classes. This lesson covers how to define models using SQLAlchemy 2.0's declarative syntax.

We'll build a **Bookstore database** that we'll use throughout the rest of this module for practicing ORM operations. All examples use SQLite — no sidecar needed.

## Core Concept: Models = Tables

A **model** is a Python class that represents a database table:

```python
class Author(Base):
    __tablename__ = "authors"
    id:   Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

# SQLAlchemy generates:
# CREATE TABLE authors (
#     id   INTEGER PRIMARY KEY,
#     name VARCHAR(100) NOT NULL
# )
```

**Key insight:** The ORM translates your Python class into SQL DDL and generates SQL queries based on your model structure.

## The Bookstore Domain

Throughout this module we'll build a **Bookstore database** with:

- **Authors** — writers of books
- **Publishers** — companies that publish books
- **Books** — products in the bookstore
- **Sales** — records of book purchases

## Setting Up SQLAlchemy 2.0

### Imports and Base Class

```{code-cell} python
from sqlalchemy import create_engine, String, ForeignKey, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from datetime import date
from decimal import Decimal
from typing import Optional

class Base(DeclarativeBase):
    pass

print("Base class defined")
```

### Create a SQLite Engine

```{code-cell} python
engine = create_engine("sqlite:///bookstore.db", echo=True)
print(f"Engine: {engine.url}")
```

`echo=True` prints every SQL statement — essential for learning what the ORM actually does.

## Progressive Model Building

### Step 1: Author

```{code-cell} python
class Author(Base):
    __tablename__ = "authors"

    id:         Mapped[int]           = mapped_column(primary_key=True)
    name:       Mapped[str]           = mapped_column(String(100))
    birth_year: Mapped[Optional[int]]

    def __repr__(self):
        return f"Author(id={self.id}, name={self.name!r}, birth_year={self.birth_year})"

Base.metadata.create_all(engine, tables=[Author.__table__])
print("authors table created")
```

### Verify the Table

```{code-cell} python
from sqlalchemy import inspect

inspector = inspect(engine)
print("Tables:", inspector.get_table_names())

for col in inspector.get_columns("authors"):
    print(f"  {col['name']}: {col['type']} (nullable={col['nullable']})")
```

### Step 2: Publisher

```{code-cell} python
class Publisher(Base):
    __tablename__ = "publishers"

    id:      Mapped[int] = mapped_column(primary_key=True)
    name:    Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(50))

    def __repr__(self):
        return f"Publisher(id={self.id}, name={self.name!r}, country={self.country!r})"

Base.metadata.create_all(engine, tables=[Publisher.__table__])
print("publishers table created")
```

### Step 3: Book with Foreign Keys

```{code-cell} python
class Book(Base):
    __tablename__ = "books"

    id:           Mapped[int]     = mapped_column(primary_key=True)
    title:        Mapped[str]     = mapped_column(String(200))
    isbn:         Mapped[str]     = mapped_column(String(13), unique=True)
    price:        Mapped[Decimal] = mapped_column(Numeric(10, 2))
    author_id:    Mapped[int]     = mapped_column(ForeignKey("authors.id"))
    publisher_id: Mapped[int]     = mapped_column(ForeignKey("publishers.id"))

    author:    Mapped["Author"]    = relationship(back_populates="books")
    publisher: Mapped["Publisher"] = relationship(back_populates="books")

    def __repr__(self):
        return f"Book(id={self.id}, title={self.title!r}, price={self.price})"

print("Book model defined")
```

Relationships use `relationship()` for Python-side navigation; the actual FK constraint is on `ForeignKey(...)`. Now add the reverse side to `Author` and `Publisher`:

```{code-cell} python
# Patch relationships onto the already-registered classes
Author.books    = relationship("Book", back_populates="author")
Publisher.books = relationship("Book", back_populates="publisher")

Base.metadata.create_all(engine, tables=[Book.__table__])
print("books table created")
```

### Step 4: Sale

```{code-cell} python
class Sale(Base):
    __tablename__ = "sales"

    id:        Mapped[int]  = mapped_column(primary_key=True)
    book_id:   Mapped[int]  = mapped_column(ForeignKey("books.id"))
    quantity:  Mapped[int]
    sale_date: Mapped[date]

    book: Mapped["Book"] = relationship(back_populates="sales")

    def __repr__(self):
        return f"Sale(id={self.id}, book_id={self.book_id}, quantity={self.quantity}, date={self.sale_date})"

Book.sales = relationship("Sale", back_populates="book")

Base.metadata.create_all(engine, tables=[Sale.__table__])
print("sales table created")
```

## Complete Schema — Fresh Start

In practice you define all models together, then call `create_all` once:

```{code-cell} python
import os
from sqlalchemy import create_engine, String, ForeignKey, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import date
from decimal import Decimal
from typing import Optional

class Base(DeclarativeBase):
    pass

class Author(Base):
    __tablename__ = "authors"
    id:         Mapped[int]           = mapped_column(primary_key=True)
    name:       Mapped[str]           = mapped_column(String(100))
    birth_year: Mapped[Optional[int]]
    books:      Mapped[list["Book"]]  = relationship(back_populates="author")
    def __repr__(self): return f"Author(id={self.id}, name={self.name!r})"

class Publisher(Base):
    __tablename__ = "publishers"
    id:      Mapped[int]           = mapped_column(primary_key=True)
    name:    Mapped[str]           = mapped_column(String(100))
    country: Mapped[str]           = mapped_column(String(50))
    books:   Mapped[list["Book"]]  = relationship(back_populates="publisher")
    def __repr__(self): return f"Publisher(id={self.id}, name={self.name!r})"

class Book(Base):
    __tablename__ = "books"
    id:           Mapped[int]          = mapped_column(primary_key=True)
    title:        Mapped[str]          = mapped_column(String(200))
    isbn:         Mapped[str]          = mapped_column(String(13), unique=True)
    price:        Mapped[Decimal]      = mapped_column(Numeric(10, 2))
    author_id:    Mapped[int]          = mapped_column(ForeignKey("authors.id"))
    publisher_id: Mapped[int]          = mapped_column(ForeignKey("publishers.id"))
    author:       Mapped["Author"]     = relationship(back_populates="books")
    publisher:    Mapped["Publisher"]  = relationship(back_populates="books")
    sales:        Mapped[list["Sale"]] = relationship(back_populates="book")
    def __repr__(self): return f"Book(id={self.id}, title={self.title!r})"

class Sale(Base):
    __tablename__ = "sales"
    id:        Mapped[int]   = mapped_column(primary_key=True)
    book_id:   Mapped[int]   = mapped_column(ForeignKey("books.id"))
    quantity:  Mapped[int]
    sale_date: Mapped[date]
    book:      Mapped["Book"] = relationship(back_populates="sales")
    def __repr__(self): return f"Sale(id={self.id}, quantity={self.quantity})"

# Drop and recreate for a clean slate
if os.path.exists("bookstore.db"):
    os.remove("bookstore.db")

engine = create_engine("sqlite:///bookstore.db", echo=True)
Base.metadata.create_all(engine)

print("\nBookstore database created!")
print("Tables:", inspect(engine).get_table_names())
```

### Inspect the Full Schema

```{code-cell} python
from sqlalchemy import inspect

inspector = inspect(engine)
for table_name in inspector.get_table_names():
    print(f"\n{table_name.upper()}")
    for col in inspector.get_columns(table_name):
        nullable = "NULL" if col["nullable"] else "NOT NULL"
        print(f"  {col['name']}: {col['type']} {nullable}")
    for fk in inspector.get_foreign_keys(table_name):
        print(f"  FK: {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}")
```

## Python Type → SQL Type Mapping

| Python Type | SQLAlchemy Type | SQLite | PostgreSQL |
|-------------|-----------------|--------|------------|
| `int` | Integer | INTEGER | INTEGER |
| `str` | String / Text | VARCHAR / TEXT | VARCHAR / TEXT |
| `float` | Float | REAL | DOUBLE PRECISION |
| `bool` | Boolean | BOOLEAN | BOOLEAN |
| `datetime` | DateTime | TIMESTAMP | TIMESTAMP |
| `date` | Date | DATE | DATE |
| `Decimal` | Numeric | NUMERIC | NUMERIC |

## Column Options

### Nullable vs. Required

```python
name:       Mapped[str]           = mapped_column(String(100))  # NOT NULL (default)
birth_year: Mapped[Optional[int]]                               # NULL allowed
subtitle:   Mapped[Optional[str]] = mapped_column(String(200))  # NULL allowed
```

### Default Values

```python
from datetime import datetime

created_at: Mapped[datetime] = mapped_column(default=datetime.now)  # Python-side
is_active:  Mapped[bool]     = mapped_column(default=True)
quantity:   Mapped[int]      = mapped_column(server_default="0")    # DB-side
```

### Unique Constraints and Indexes

```python
from sqlalchemy import UniqueConstraint, Index

class Book(Base):
    __tablename__ = "books"
    isbn:      Mapped[str] = mapped_column(String(13), unique=True)         # single-column unique
    title:     Mapped[str] = mapped_column(String(200), index=True)         # simple index
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"), index=True)

    __table_args__ = (
        UniqueConstraint("title", "author_id", name="uq_title_per_author"),
        Index("ix_author_publisher", "author_id", "publisher_id"),
    )
```

## Relationships Explained

### One-to-Many

```python
class Author(Base):
    books: Mapped[list["Book"]] = relationship(back_populates="author")  # one Author → many Books

class Book(Base):
    author_id: Mapped[int]      = mapped_column(ForeignKey("authors.id"))  # DB constraint
    author:    Mapped["Author"] = relationship(back_populates="books")     # ORM navigation
```

- `ForeignKey(...)` creates the actual database constraint
- `relationship(...)` is Python-side only — no column in the database
- `back_populates` establishes a bidirectional link

### Using a Relationship to Create Records

```{code-cell} python
from sqlalchemy.orm import Session

with Session(engine) as session:
    pub = Publisher(name="Penguin Books", country="UK")
    session.add(pub)
    session.flush()  # get pub.id before commit

    author = Author(name="George Orwell", birth_year=1903)
    author.books = [
        Book(title="1984",        isbn="9780451524935", price=Decimal("15.99"), publisher=pub),
        Book(title="Animal Farm", isbn="9780451526342", price=Decimal("13.99"), publisher=pub),
    ]
    session.add(author)
    session.commit()

    print(f"Created {author.name} with {len(author.books)} books")
    for book in author.books:
        print(f"  {book.title}")
```

## Dropping and Recreating Tables

```{code-cell} python
# Drop all tables then recreate
Base.metadata.drop_all(engine)
print("All tables dropped")

Base.metadata.create_all(engine)
print("All tables recreated")
print("Tables:", inspect(engine).get_table_names())
```

## Practice Exercises

### Exercise 1: Add a Ratings Model

Extend the schema to support book ratings:

- `id`, `book_id` (FK), `rating` (int 1–5), `review_text` (optional), `review_date`
- Add a `ratings` relationship on `Book`

### Exercise 2: Timestamps Mixin

Create a `TimestampMixin` that adds `created_at` and `updated_at` to any model:

```python
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

class Book(Base, TimestampMixin):
    ...
```

## Key Takeaways

- **Models are Python classes** that represent database tables
- **`Mapped[type]`** provides type hints for columns
- **`mapped_column()`** configures column properties (constraints, defaults, indexes)
- **`relationship()`** is ORM navigation only — no database column
- **`ForeignKey()`** creates the actual database constraint
- **Same models work across databases** — only the connection string changes
- **Always enable `echo=True`** during learning to see generated SQL
- **`create_all` is idempotent** — safe to call multiple times

## What's Next?

Now that the Bookstore schema is defined, let's learn how to perform CRUD operations.

**Next lesson:** [CRUD Operations - Working with Data](04-crud-operations.md)

---

[← Back: ORM Concepts](02-orm-concepts.md) | [Course Home](README.md) | [Next: CRUD Operations →](04-crud-operations.md)
