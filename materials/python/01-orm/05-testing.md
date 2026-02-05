# Testing and Database Lifecycle

## Overview

One of the biggest advantages of ORMs is the ability to create test databases instantly and manage database lifecycles programmatically. This lesson covers:

1. **Database lifecycle management** - Creating and dropping databases
2. **Testing with in-memory databases** - Fast, isolated tests
3. **Factory patterns** - Reusable test data generation

## Database Lifecycle Management

Before we dive into testing, let's learn how to create and drop databases programmatically for both SQLite and SQL Server.

## Managing SQLite Databases

### Create SQLite Database

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import String

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))

# Create database file
engine = create_engine("sqlite:///test_bookstore.db", echo=True)
Base.metadata.create_all(engine)

print("✓ SQLite database created: test_bookstore.db")
```

### Verify SQLite Database Exists

```python
import os

db_path = "test_bookstore.db"
if os.path.exists(db_path):
    size = os.path.getsize(db_path)
    print(f"✓ Database file exists: {db_path} ({size} bytes)")
else:
    print("✗ Database file not found")
```

### Drop SQLite Database

```python
import os

db_path = "test_bookstore.db"

if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✓ Deleted database: {db_path}")
else:
    print("Database file doesn't exist")
```

### Verify Deletion

```python
import os

db_path = "test_bookstore.db"
if not os.path.exists(db_path):
    print("✓ Confirmed: Database file deleted")
else:
    print("✗ Database file still exists")
```

## Managing SQL Server Databases

### Create SQL Server Database

```python
import pyodbc

# Connect to master database to create/drop databases
connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=master;"
    "UID=SA;"
    "PWD=61eF92j4VTtl;"
    "TrustServerCertificate=yes;"
)

conn = pyodbc.connect(connection_string)
conn.autocommit = True  # Required for CREATE/DROP DATABASE
cursor = conn.cursor()

# Create database
try:
    cursor.execute("CREATE DATABASE TestBookstore")
    print("✓ SQL Server database created: TestBookstore")
except Exception as e:
    print(f"Note: {e}")

conn.close()
```

### Verify SQL Server Database

```python
import pyodbc

connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=master;"
    "UID=SA;"
    "PWD=61eF92j4VTtl;"
    "TrustServerCertificate=yes;"
)

conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

# List databases
cursor.execute("SELECT name FROM sys.databases WHERE name = 'TestBookstore'")
result = cursor.fetchone()

if result:
    print(f"✓ Database exists: {result[0]}")
else:
    print("✗ Database not found")

conn.close()
```

### Create Tables in SQL Server Database

```python
from sqlalchemy import create_engine

# Connect to the new database
engine = create_engine(
    "mssql+pyodbc://SA:61eF92j4VTtl@localhost:1433/TestBookstore"
    "?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes",
    echo=True
)

# Create tables
Base.metadata.create_all(engine)

print("✓ Tables created in TestBookstore")
```

### Drop SQL Server Database

```python
import pyodbc

connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=master;"
    "UID=SA;"
    "PWD=61eF92j4VTtl;"
    "TrustServerCertificate=yes;"
)

conn = pyodbc.connect(connection_string)
conn.autocommit = True
cursor = conn.cursor()

# Drop database (disconnect users first)
try:
    cursor.execute("""
        IF EXISTS (SELECT name FROM sys.databases WHERE name = 'TestBookstore')
        BEGIN
            ALTER DATABASE TestBookstore SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
            DROP DATABASE TestBookstore;
        END
    """)
    print("✓ SQL Server database dropped: TestBookstore")
except Exception as e:
    print(f"Error: {e}")

conn.close()
```

## Database Management Helpers

Let's create reusable helper functions:

### SQLite Helper Functions

```python
import os
from sqlalchemy import create_engine

def create_sqlite_db(db_name, base_class):
    """Create SQLite database with tables."""
    db_path = f"{db_name}.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    base_class.metadata.create_all(engine)
    return engine, db_path

def drop_sqlite_db(db_path):
    """Drop SQLite database."""
    if os.path.exists(db_path):
        os.remove(db_path)
        return True
    return False

# Test the helpers
engine, path = create_sqlite_db("helper_test", Base)
print(f"✓ Created: {path}")

dropped = drop_sqlite_db(path)
print(f"✓ Dropped: {dropped}")
```

### SQL Server Helper Functions

```python
import pyodbc
from sqlalchemy import create_engine

def create_sqlserver_db(db_name, base_class=None):
    """Create SQL Server database and optionally create tables."""
    connection_string = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=master;"
        "UID=SA;"
        "PWD=61eF92j4VTtl;"
        "TrustServerCertificate=yes;"
    )
    
    conn = pyodbc.connect(connection_string)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Create database
    cursor.execute(f"CREATE DATABASE {db_name}")
    conn.close()
    
    # Create tables if base class provided
    if base_class:
        engine = create_engine(
            f"mssql+pyodbc://SA:61eF92j4VTtl@localhost:1433/{db_name}"
            f"?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes",
            echo=False
        )
        base_class.metadata.create_all(engine)
        return engine
    
    return None

def drop_sqlserver_db(db_name):
    """Drop SQL Server database."""
    connection_string = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=master;"
        "UID=SA;"
        "PWD=61eF92j4VTtl;"
        "TrustServerCertificate=yes;"
    )
    
    conn = pyodbc.connect(connection_string)
    conn.autocommit = True
    cursor = conn.cursor()
    
    cursor.execute(f"""
        IF EXISTS (SELECT name FROM sys.databases WHERE name = '{db_name}')
        BEGIN
            ALTER DATABASE {db_name} SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
            DROP DATABASE {db_name};
        END
    """)
    
    conn.close()

# Test (commented out to avoid actual database operations)
# engine = create_sqlserver_db("HelperTest", Base)
# print("✓ Created SQL Server database with tables")
# drop_sqlserver_db("HelperTest")
# print("✓ Dropped SQL Server database")
```

## Testing with In-Memory SQLite

The killer feature: `sqlite:///:memory:` creates a complete database in RAM.

### Why In-Memory Databases are Perfect for Testing

```python
from sqlalchemy import create_engine

# Regular file-based database
file_engine = create_engine("sqlite:///test.db")

# In-memory database - exists only in RAM
memory_engine = create_engine("sqlite:///:memory:")

print("File database:", file_engine.url)
print("Memory database:", memory_engine.url)
```

**Benefits:**
- Created instantly (milliseconds)
- No cleanup needed (disappears when process ends)
- Isolated (each connection gets its own database)
- Fast (no disk I/O)

### Basic In-Memory Test

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Create in-memory database
engine = create_engine("sqlite:///:memory:", echo=False)

# Create tables
Base.metadata.create_all(engine)

# Use it
with Session(engine) as session:
    user = User(name="Test User", email="test@example.com")
    session.add(user)
    session.commit()
    
    # Verify
    assert user.id is not None
    assert user.name == "Test User"
    
    print("✓ In-memory test passed")

# Database disappears here
```

## Testing with pytest

### Install pytest

```python
import ipytest
ipytest.autoconfig()
```

### Basic Test Fixture

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

@pytest.fixture
def db_session():
    """Provides a fresh database session for each test."""
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Provide session to test
    with Session(engine) as session:
        yield session
    
    # Database automatically destroyed

def test_create_user(db_session):
    """Test user creation."""
    user = User(name="Alice", email="alice@example.com")
    db_session.add(user)
    db_session.commit()
    
    assert user.id == 1
    assert user.name == "Alice"

def test_query_user(db_session):
    """Test user query."""
    # Fresh database for this test too!
    user = User(name="Bob", email="bob@example.com")
    db_session.add(user)
    db_session.commit()
    
    # Query
    found = db_session.get(User, user.id)
    assert found.name == "Bob"

ipytest.run()
```

### Testing the Bookstore Models

```python
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from decimal import Decimal

# Import our Bookstore models
from sqlalchemy import String, ForeignKey, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional

class Base(DeclarativeBase):
    pass

class Author(Base):
    __tablename__ = "authors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    birth_year: Mapped[Optional[int]]
    books: Mapped[list["Book"]] = relationship(back_populates="author")

class Publisher(Base):
    __tablename__ = "publishers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(50))
    books: Mapped[list["Book"]] = relationship(back_populates="publisher")

class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    isbn: Mapped[str] = mapped_column(String(13), unique=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    publisher_id: Mapped[int] = mapped_column(ForeignKey("publishers.id"))
    author: Mapped["Author"] = relationship(back_populates="books")
    publisher: Mapped["Publisher"] = relationship(back_populates="books")

@pytest.fixture
def bookstore_session():
    """Fresh bookstore database for each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    with Session(engine) as session:
        # Seed with basic data
        author = Author(name="Test Author", birth_year=1970)
        publisher = Publisher(name="Test Publisher", country="USA")
        session.add_all([author, publisher])
        session.commit()
        
        yield session

def test_create_book(bookstore_session):
    """Test creating a book."""
    author = bookstore_session.scalars(select(Author)).first()
    publisher = bookstore_session.scalars(select(Publisher)).first()
    
    book = Book(
        title="Test Book",
        isbn="1234567890123",
        price=Decimal("19.99"),
        author_id=author.id,
        publisher_id=publisher.id
    )
    
    bookstore_session.add(book)
    bookstore_session.commit()
    
    assert book.id is not None
    assert book.title == "Test Book"

def test_book_relationships(bookstore_session):
    """Test book relationships."""
    author = bookstore_session.scalars(select(Author)).first()
    publisher = bookstore_session.scalars(select(Publisher)).first()
    
    book = Book(
        title="Relationship Test",
        isbn="9999999999999",
        price=Decimal("29.99"),
        author=author,
        publisher=publisher
    )
    
    bookstore_session.add(book)
    bookstore_session.commit()
    
    # Test relationships
    assert book.author.name == "Test Author"
    assert book.publisher.name == "Test Publisher"
    assert len(author.books) == 1

def test_query_expensive_books(bookstore_session):
    """Test querying books by price."""
    author = bookstore_session.scalars(select(Author)).first()
    publisher = bookstore_session.scalars(select(Publisher)).first()
    
    # Add books with different prices
    cheap_book = Book(
        title="Cheap Book",
        isbn="1111111111111",
        price=Decimal("9.99"),
        author_id=author.id,
        publisher_id=publisher.id
    )
    expensive_book = Book(
        title="Expensive Book",
        isbn="2222222222222",
        price=Decimal("99.99"),
        author_id=author.id,
        publisher_id=publisher.id
    )
    
    bookstore_session.add_all([cheap_book, expensive_book])
    bookstore_session.commit()
    
    # Query expensive books
    stmt = select(Book).where(Book.price > Decimal("50.00"))
    expensive_books = bookstore_session.scalars(stmt).all()
    
    assert len(expensive_books) == 1
    assert expensive_books[0].title == "Expensive Book"

ipytest.run()
```

## Factory Pattern for Test Data

Create reusable factories for generating test data:

```python
from decimal import Decimal

class AuthorFactory:
    """Factory for creating test authors."""
    
    @staticmethod
    def create(session, name="Default Author", birth_year=1970):
        author = Author(name=name, birth_year=birth_year)
        session.add(author)
        session.commit()
        return author

class PublisherFactory:
    """Factory for creating test publishers."""
    
    @staticmethod
    def create(session, name="Default Publisher", country="USA"):
        publisher = Publisher(name=name, country=country)
        session.add(publisher)
        session.commit()
        return publisher

class BookFactory:
    """Factory for creating test books."""
    
    _isbn_counter = 1000000000000
    
    @staticmethod
    def create(session, title="Default Book", price=Decimal("19.99"), author=None, publisher=None):
        if author is None:
            author = AuthorFactory.create(session)
        if publisher is None:
            publisher = PublisherFactory.create(session)
        
        # Generate unique ISBN
        isbn = str(BookFactory._isbn_counter)
        BookFactory._isbn_counter += 1
        
        book = Book(
            title=title,
            isbn=isbn,
            price=price,
            author=author,
            publisher=publisher
        )
        
        session.add(book)
        session.commit()
        return book

# Example usage
@pytest.fixture
def bookstore_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_with_factories(bookstore_session):
    """Test using factories."""
    author = AuthorFactory.create(bookstore_session, name="Factory Author")
    publisher = PublisherFactory.create(bookstore_session, name="Factory Publisher")
    book = BookFactory.create(
        bookstore_session,
        title="Factory Book",
        price=Decimal("25.99"),
        author=author,
        publisher=publisher
    )
    
    assert book.title == "Factory Book"
    assert book.author.name == "Factory Author"
    assert book.publisher.name == "Factory Publisher"

ipytest.run()
```

## Key Takeaways

- **SQLite**: Create with `create_engine()`, drop with `os.remove()`
- **SQL Server**: Create/drop with `CREATE/DROP DATABASE` via pyodbc
- **In-memory SQLite** is perfect for testing - instant, isolated, zero setup
- **pytest fixtures** provide fresh databases per test
- **Factory pattern** simplifies test data creation
- **Database lifecycle** management is essential for testing and development
- **Test isolation** ensures each test runs in a clean environment

## Practice Exercises

### Exercise 1: Database Lifecycle

1. Create a new SQLite database called `library.db`
2. Create the bookstore tables
3. Add some sample data
4. Drop the database

### Exercise 2: Test Suite

Create a complete test suite for the Bookstore models:
- Test creating authors, publishers, books
- Test relationships
- Test queries with filters
- Test updates and deletes

### Exercise 3: Factory Testing

Create a complete factory-based test suite:
1. Build factories for all models (Author, Publisher, Book)
2. Add factory methods for common scenarios (cheap books, expensive books, prolific authors)
3. Create tests that use factories exclusively
4. Measure test performance compared to manual data creation

## Summary

You now understand:

1. ✓ **Database lifecycle management** - Creating and dropping SQLite and SQL Server databases programmatically
2. ✓ **In-memory testing** - Fast, isolated test databases with `sqlite:///:memory:`
3. ✓ **pytest integration** - Fixtures for clean test environments
4. ✓ **Factory patterns** - Reusable test data generation
5. ✓ **Test isolation** - Each test runs with a fresh database

**Next Steps:** Continue to [Lesson 06 - Schema Migrations](06-schema-migrations.md) to learn how to manage database schema changes with Alembic.

**Testing Benefits:**
- Fast test execution (milliseconds, not seconds)
- Complete isolation (no test interference)
- Reproducible (same starting state every time)
- Zero cleanup (in-memory databases disappear automatically)

**Remember:** In data engineering, you'll primarily use ORMs for:
- Application/operational databases
- Testing infrastructure
- Small-scale CRUD operations

For analytical workloads (Snowflake, BigQuery, Redshift), stick with drivers and raw SQL for precise control and cost optimization.

---

[← Back: CRUD Operations](04-crud-operations.md) | [Course Home](README.md) | [Next: Schema Migrations →](06-schema-migrations.md)
