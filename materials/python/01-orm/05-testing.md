---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Testing and Database Lifecycle

## Overview

One of the biggest advantages of ORMs is the ability to create test databases instantly. This lesson covers:

1. **Database lifecycle management** — creating and dropping SQLite databases programmatically
2. **In-memory testing** — instant, isolated test databases
3. **pytest fixtures** — clean environment per test
4. **Factory patterns** — reusable test data generation

## Database Lifecycle with SQLite

### Create a SQLite Database

```{code-cell} python
from sqlalchemy import create_engine, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import inspect

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id:    Mapped[int] = mapped_column(primary_key=True)
    name:  Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))

engine = create_engine("sqlite:///lifecycle_demo.db", echo=False)
Base.metadata.create_all(engine)

print("Tables:", inspect(engine).get_table_names())
```

### Verify the File Exists

```{code-cell} python
import os

path = "lifecycle_demo.db"
if os.path.exists(path):
    print(f"File exists: {path} ({os.path.getsize(path)} bytes)")
```

### Drop the Database (Delete the File)

```{code-cell} python
import os

path = "lifecycle_demo.db"
if os.path.exists(path):
    os.remove(path)
    print(f"Deleted: {path}")

print("Exists after drop:", os.path.exists(path))
```

## In-Memory SQLite for Testing

`sqlite:///:memory:` creates a complete database that lives entirely in RAM:

```{code-cell} python
from sqlalchemy import create_engine

memory_engine = create_engine("sqlite:///:memory:", echo=False)
Base.metadata.create_all(memory_engine)

print("Tables in memory DB:", inspect(memory_engine).get_table_names())
```

**Benefits:**
- Created in milliseconds
- No cleanup needed — disappears when the process ends
- Each connection can have its own isolated database
- No disk I/O — fast test execution

### Quick In-Memory Test

```{code-cell} python
engine = create_engine("sqlite:///:memory:", echo=False)
Base.metadata.create_all(engine)

with Session(engine) as session:
    user = User(name="Test User", email="test@example.com")
    session.add(user)
    session.commit()

    assert user.id is not None
    assert user.name == "Test User"
    print("In-memory test passed")
# Database gone after this point
```

## Testing with pytest

`ipytest` lets us run pytest tests directly inside notebook cells.

```{code-cell} python
import ipytest
ipytest.autoconfig()
```

### Basic Fixture

```{code-cell} python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

@pytest.fixture
def db_session():
    """Provides a fresh in-memory database per test."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    # Engine (and in-memory database) destroyed here

def test_create_user(db_session):
    user = User(name="Alice", email="alice@example.com")
    db_session.add(user)
    db_session.commit()

    assert user.id == 1
    assert user.name == "Alice"

def test_query_user(db_session):
    user = User(name="Bob", email="bob@example.com")
    db_session.add(user)
    db_session.commit()

    found = db_session.get(User, user.id)
    assert found.name == "Bob"

ipytest.run()
```

### Testing Bookstore Models

```{code-cell} python
import pytest
from sqlalchemy import create_engine, select, String, ForeignKey, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from decimal import Decimal
from typing import Optional

class BookstoreBase(DeclarativeBase):
    pass

class Author(BookstoreBase):
    __tablename__ = "authors"
    id:         Mapped[int]           = mapped_column(primary_key=True)
    name:       Mapped[str]           = mapped_column(String(100))
    birth_year: Mapped[Optional[int]]
    books:      Mapped[list["Book"]]  = relationship(back_populates="author")

class Publisher(BookstoreBase):
    __tablename__ = "publishers"
    id:      Mapped[int]          = mapped_column(primary_key=True)
    name:    Mapped[str]          = mapped_column(String(100))
    country: Mapped[str]          = mapped_column(String(50))
    books:   Mapped[list["Book"]] = relationship(back_populates="publisher")

class Book(BookstoreBase):
    __tablename__ = "books"
    id:           Mapped[int]         = mapped_column(primary_key=True)
    title:        Mapped[str]         = mapped_column(String(200))
    isbn:         Mapped[str]         = mapped_column(String(13), unique=True)
    price:        Mapped[Decimal]     = mapped_column(Numeric(10, 2))
    author_id:    Mapped[int]         = mapped_column(ForeignKey("authors.id"))
    publisher_id: Mapped[int]         = mapped_column(ForeignKey("publishers.id"))
    author:       Mapped["Author"]    = relationship(back_populates="books")
    publisher:    Mapped["Publisher"] = relationship(back_populates="books")

@pytest.fixture
def bookstore_session():
    """Fresh bookstore database seeded with one author and publisher."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    BookstoreBase.metadata.create_all(engine)
    with Session(engine) as session:
        author    = Author(name="Test Author", birth_year=1970)
        publisher = Publisher(name="Test Publisher", country="USA")
        session.add_all([author, publisher])
        session.commit()
        yield session

def test_create_book(bookstore_session):
    author    = bookstore_session.scalars(select(Author)).first()
    publisher = bookstore_session.scalars(select(Publisher)).first()

    book = Book(
        title="Test Book",
        isbn="1234567890123",
        price=Decimal("19.99"),
        author_id=author.id,
        publisher_id=publisher.id,
    )
    bookstore_session.add(book)
    bookstore_session.commit()

    assert book.id is not None
    assert book.title == "Test Book"

def test_book_relationships(bookstore_session):
    author    = bookstore_session.scalars(select(Author)).first()
    publisher = bookstore_session.scalars(select(Publisher)).first()

    book = Book(
        title="Relationship Test",
        isbn="9999999999999",
        price=Decimal("29.99"),
        author=author,
        publisher=publisher,
    )
    bookstore_session.add(book)
    bookstore_session.commit()

    assert book.author.name    == "Test Author"
    assert book.publisher.name == "Test Publisher"
    assert len(author.books)   == 1

def test_query_by_price(bookstore_session):
    author    = bookstore_session.scalars(select(Author)).first()
    publisher = bookstore_session.scalars(select(Publisher)).first()

    cheap     = Book(title="Cheap",     isbn="1111111111111", price=Decimal("9.99"),  author_id=author.id, publisher_id=publisher.id)
    expensive = Book(title="Expensive", isbn="2222222222222", price=Decimal("99.99"), author_id=author.id, publisher_id=publisher.id)
    bookstore_session.add_all([cheap, expensive])
    bookstore_session.commit()

    results = bookstore_session.scalars(select(Book).where(Book.price > Decimal("50.00"))).all()
    assert len(results) == 1
    assert results[0].title == "Expensive"

ipytest.run()
```

## Factory Pattern

Factories encapsulate test data creation, keeping tests focused on behaviour:

```{code-cell} python
from decimal import Decimal

class AuthorFactory:
    @staticmethod
    def create(session, name="Default Author", birth_year=1970):
        author = Author(name=name, birth_year=birth_year)
        session.add(author)
        session.commit()
        return author

class PublisherFactory:
    @staticmethod
    def create(session, name="Default Publisher", country="USA"):
        publisher = Publisher(name=name, country=country)
        session.add(publisher)
        session.commit()
        return publisher

class BookFactory:
    _isbn_counter = 1_000_000_000_000

    @classmethod
    def create(cls, session, title="Default Book", price=Decimal("19.99"), author=None, publisher=None):
        if author    is None: author    = AuthorFactory.create(session)
        if publisher is None: publisher = PublisherFactory.create(session)

        isbn = str(cls._isbn_counter)
        cls._isbn_counter += 1

        book = Book(title=title, isbn=isbn, price=price, author=author, publisher=publisher)
        session.add(book)
        session.commit()
        return book

print("Factories defined")
```

```{code-cell} python
@pytest.fixture
def bs():
    engine = create_engine("sqlite:///:memory:", echo=False)
    BookstoreBase.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_with_factories(bs):
    author    = AuthorFactory.create(bs, name="Factory Author")
    publisher = PublisherFactory.create(bs, name="Factory Publisher")
    book      = BookFactory.create(bs, title="Factory Book", price=Decimal("25.99"),
                                   author=author, publisher=publisher)

    assert book.title          == "Factory Book"
    assert book.author.name    == "Factory Author"
    assert book.publisher.name == "Factory Publisher"

ipytest.run()
```

## Key Takeaways

- **SQLite lifecycle**: create with `create_engine()`, drop with `os.remove()`
- **In-memory SQLite** is perfect for testing — instant, isolated, zero cleanup
- **pytest fixtures** provide a fresh database per test — no test interference
- **Factory pattern** keeps test setup DRY and readable
- **Test isolation** is the rule: each test starts with a clean state

## What's Next?

**Next lesson:** [Schema Migrations with Alembic](06-schema-migrations.md)

---

[← Back: CRUD Operations](04-crud-operations.md) | [Course Home](README.md) | [Next: Schema Migrations →](06-schema-migrations.md)
