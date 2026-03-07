---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# CRUD Operations: Working with Data

## Overview

CRUD — Create, Read, Update, Delete — are the fundamental operations for working with data. This lesson covers how to perform them using SQLAlchemy's ORM with our **Bookstore database**.

## Setup

Define the models and create a fresh database. This cell must run first.

```{code-cell} python
import os
from sqlalchemy import create_engine, String, ForeignKey, Numeric, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
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
    id:        Mapped[int]    = mapped_column(primary_key=True)
    book_id:   Mapped[int]    = mapped_column(ForeignKey("books.id"))
    quantity:  Mapped[int]
    sale_date: Mapped[date]
    book:      Mapped["Book"] = relationship(back_populates="sales")
    def __repr__(self): return f"Sale(id={self.id}, quantity={self.quantity}, date={self.sale_date})"

if os.path.exists("bookstore.db"):
    os.remove("bookstore.db")

engine = create_engine("sqlite:///bookstore.db", echo=True)
Base.metadata.create_all(engine)
print("Database ready")
```

## The Session

The **Session** is the gateway to all database operations in SQLAlchemy ORM:

```{code-cell} python
with Session(engine) as session:
    print(f"Session: {session}")
```

**Key responsibilities:**
- Tracks changes to objects (Unit of Work pattern)
- Manages transactions (commit / rollback)
- Executes queries
- Handles connection pooling

## CREATE: Adding Records

### Single Record

```{code-cell} python
with Session(engine) as session:
    author = Author(name="George Orwell", birth_year=1903)
    session.add(author)
    print(f"Before commit — id: {author.id}")  # None until committed

    session.commit()
    print(f"After commit  — id: {author.id}")  # assigned by DB
```

### Multiple Records with `add_all`

```{code-cell} python
with Session(engine) as session:
    authors = [
        Author(name="J.K. Rowling",   birth_year=1965),
        Author(name="Stephen King",   birth_year=1947),
        Author(name="Agatha Christie",birth_year=1890),
    ]
    session.add_all(authors)
    session.commit()

    print("Created authors:")
    for a in authors:
        print(f"  {a.id}: {a.name}")
```

### Create Publishers

```{code-cell} python
with Session(engine) as session:
    publishers = [
        Publisher(name="Penguin Books", country="UK"),
        Publisher(name="Bloomsbury",    country="UK"),
        Publisher(name="Scribner",      country="USA"),
    ]
    session.add_all(publishers)
    session.commit()

    for p in publishers:
        print(f"  {p.id}: {p.name} ({p.country})")
```

### Create Books

```{code-cell} python
with Session(engine) as session:
    orwell  = session.scalars(select(Author).where(Author.name == "George Orwell")).first()
    rowling = session.scalars(select(Author).where(Author.name == "J.K. Rowling")).first()
    penguin = session.scalars(select(Publisher).where(Publisher.name == "Penguin Books")).first()
    bloom   = session.scalars(select(Publisher).where(Publisher.name == "Bloomsbury")).first()

    books = [
        Book(title="1984",         isbn="9780451524935", price=Decimal("15.99"), author=orwell,  publisher=penguin),
        Book(title="Animal Farm",  isbn="9780451526342", price=Decimal("13.99"), author=orwell,  publisher=penguin),
        Book(title="Harry Potter and the Philosopher's Stone",
                                   isbn="9780747532699", price=Decimal("19.99"), author=rowling, publisher=bloom),
    ]
    session.add_all(books)
    session.commit()

    for b in books:
        print(f"  {b.id}: {b.title}")
```

### Create via Relationship

```{code-cell} python
with Session(engine) as session:
    king     = session.scalars(select(Author).where(Author.name == "Stephen King")).first()
    scribner = session.scalars(select(Publisher).where(Publisher.name == "Scribner")).first()

    king.books.append(
        Book(title="The Shining", isbn="9780307743657", price=Decimal("18.99"), publisher=scribner)
    )
    session.commit()
    print(f"{king.name} now has {len(king.books)} book(s)")
```

## READ: Querying Data

### Get by Primary Key

```{code-cell} python
with Session(engine) as session:
    author = session.get(Author, 1)
    print(f"Found: {author}")
```

### All Records

```{code-cell} python
with Session(engine) as session:
    authors = session.scalars(select(Author)).all()
    for a in authors:
        print(f"  {a.id}: {a.name} (born {a.birth_year})")
```

### Filter

```{code-cell} python
with Session(engine) as session:
    stmt = select(Author).where(Author.birth_year > 1950)
    for a in session.scalars(stmt):
        print(f"  {a.name} (born {a.birth_year})")
```

### LIKE

```{code-cell} python
with Session(engine) as session:
    stmt = select(Book).where(Book.title.like("%Harry%"))
    for b in session.scalars(stmt):
        print(f"  {b.title}")
```

### Order and Limit

```{code-cell} python
with Session(engine) as session:
    stmt = select(Book).order_by(Book.price.desc()).limit(3)
    for b in session.scalars(stmt):
        print(f"  ${b.price}: {b.title}")
```

### Navigate Relationships

```{code-cell} python
with Session(engine) as session:
    author = session.get(Author, 1)
    print(f"{author.name}'s books:")
    for book in author.books:
        print(f"  - {book.title} (${book.price})")
```

### JOIN Query

```{code-cell} python
with Session(engine) as session:
    stmt = (
        select(Book.title, Book.price, Author.name.label("author_name"))
        .join(Author)
        .where(Book.price > Decimal("15.00"))
    )
    for title, price, author_name in session.execute(stmt):
        print(f"  {title} by {author_name}: ${price}")
```

### Aggregations

```{code-cell} python
with Session(engine) as session:
    count    = session.scalar(select(func.count(Book.id)))
    avg      = session.scalar(select(func.avg(Book.price)))
    min_p    = session.scalar(select(func.min(Book.price)))
    max_p    = session.scalar(select(func.max(Book.price)))
    print(f"Books: {count} | Avg: ${avg:.2f} | Range: ${min_p} – ${max_p}")
```

### Group By

```{code-cell} python
with Session(engine) as session:
    stmt = (
        select(Author.name, func.count(Book.id).label("book_count"))
        .join(Book)
        .group_by(Author.name)
        .order_by(func.count(Book.id).desc())
    )
    for author_name, book_count in session.execute(stmt):
        print(f"  {author_name}: {book_count} book(s)")
```

## UPDATE: Modifying Records

### Modify an Object

```{code-cell} python
with Session(engine) as session:
    book = session.get(Book, 1)
    print(f"Before: {book.title} — ${book.price}")
    book.price = Decimal("17.99")
    session.commit()
    print(f"After:  {book.title} — ${book.price}")
```

### Bulk Update

```{code-cell} python
from sqlalchemy import update

with Session(engine) as session:
    result = session.execute(
        update(Book).values(price=Book.price * Decimal("1.10"))
    )
    session.commit()
    print(f"Updated {result.rowcount} books (+10%)")
```

```{code-cell} python
with Session(engine) as session:
    for title, price in session.execute(select(Book.title, Book.price).order_by(Book.title)):
        print(f"  {title}: ${price:.2f}")
```

## DELETE: Removing Records

### Delete a Single Object

```{code-cell} python
with Session(engine) as session:
    test_author = Author(name="Temp Author", birth_year=2000)
    session.add(test_author)
    session.commit()
    temp_id = test_author.id
    print(f"Created temp author id={temp_id}")

with Session(engine) as session:
    author = session.get(Author, temp_id)
    session.delete(author)
    session.commit()
    print(f"Deleted author id={temp_id}")

with Session(engine) as session:
    gone = session.get(Author, temp_id)
    print("Confirmed deleted" if gone is None else "Still exists!")
```

### Bulk Delete

```{code-cell} python
from sqlalchemy import delete

with Session(engine) as session:
    book = session.get(Book, 1)
    session.add_all([
        Sale(book=book, quantity=1, sale_date=date.today()),
        Sale(book=book, quantity=2, sale_date=date.today()),
    ])
    session.commit()
    print("Created test sales")

with Session(engine) as session:
    result = session.execute(delete(Sale).where(Sale.sale_date == date.today()))
    session.commit()
    print(f"Deleted {result.rowcount} sales")
```

## Transactions: Commit and Rollback

### Successful Transaction

```{code-cell} python
with Session(engine) as session:
    try:
        author = Author(name="Jane Austen", birth_year=1775)
        session.add(author)
        session.flush()  # get id without committing

        publisher = session.get(Publisher, 1)
        book = Book(
            title="Pride and Prejudice",
            isbn="9780141439518",
            price=Decimal("12.99"),
            author_id=author.id,
            publisher_id=publisher.id,
        )
        session.add(book)
        session.commit()
        print(f"Transaction OK — author: {author.name}, book: {book.title}")
    except Exception as e:
        print(f"Failed: {e}")
        raise
```

### Rollback on Error

```{code-cell} python
with Session(engine) as session:
    try:
        # First insert — valid ISBN
        session.add(Book(title="Test 1", isbn="0000000000001", price=Decimal("10.00"), author_id=1, publisher_id=1))
        session.commit()

        # Second insert — same ISBN, will fail
        session.add(Book(title="Test 2", isbn="0000000000001", price=Decimal("10.00"), author_id=1, publisher_id=1))
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error caught: {type(e).__name__}")
        print("Transaction rolled back")
```

## Complete Workflow: Add Book and Record Sale

```{code-cell} python
with Session(engine) as session:
    christie = session.scalars(select(Author).where(Author.name == "Agatha Christie")).first()
    penguin  = session.scalars(select(Publisher).where(Publisher.name == "Penguin Books")).first()

    new_book = Book(
        title="Murder on the Orient Express",
        isbn="9780062693662",
        price=Decimal("14.99"),
        author=christie,
        publisher=penguin,
    )
    session.add(new_book)
    session.commit()
    print(f"Added: {new_book.title} (id={new_book.id})")
```

```{code-cell} python
with Session(engine) as session:
    book = session.scalars(select(Book).where(Book.title.like("%Orient Express%"))).first()
    sale = Sale(book=book, quantity=3, sale_date=date.today())
    session.add(sale)
    session.commit()
    print(f"Recorded sale: {sale.quantity}x {book.title} on {sale.sale_date}")
```

```{code-cell} python
with Session(engine) as session:
    stmt = (
        select(Book.title, Author.name.label("author"), Sale.quantity, Sale.sale_date,
               (Book.price * Sale.quantity).label("revenue"))
        .join(Sale).join(Author)
        .order_by(Sale.sale_date.desc())
    )
    print(f"{'Date':<12} {'Book':<35} {'Author':<18} {'Qty':<5} {'Revenue'}")
    print("-" * 80)
    total = Decimal("0.00")
    for row in session.execute(stmt):
        print(f"{row.sale_date!s:<12} {row.title:<35} {row.author:<18} {row.quantity:<5} ${row.revenue:.2f}")
        total += row.revenue
    print("-" * 80)
    print(f"{'Total':>72} ${total:.2f}")
```

## Key Takeaways

- **Session manages everything** — all operations go through the session
- **`add()` stages changes** — doesn't write to the database yet
- **`commit()` saves changes** — writes to the database
- **`rollback()` discards changes** — undoes everything since last commit
- **`flush()`** syncs session to DB within the transaction (useful to get IDs early)
- **Unit of Work** — session tracks exactly what changed
- **Always use `with Session(engine):`** — ensures cleanup on exit
- **`echo=True`** — see the SQL being generated

## What's Next?

**Next lesson:** [Testing and Database Lifecycle](05-testing.md)

---

[← Back: Defining Models](03-defining-models.md) | [Course Home](README.md) | [Next: Testing →](05-testing.md)
