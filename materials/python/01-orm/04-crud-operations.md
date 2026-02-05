# CRUD Operations: Working with Data

## Overview

CRUD stands for Create, Read, Update, Delete - the fundamental operations for working with data. This lesson covers how to perform these operations using SQLAlchemy's ORM with our **Bookstore database**.

## Setup: Import Models and Connect

Let's set up our Bookstore database and models:

### Import Dependencies

```python
from sqlalchemy import create_engine, String, ForeignKey, Numeric, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from datetime import date
from decimal import Decimal
from typing import Optional
```

### Define Models

```python
class Base(DeclarativeBase):
    pass

class Author(Base):
    __tablename__ = "authors"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    birth_year: Mapped[Optional[int]]
    
    books: Mapped[list["Book"]] = relationship(back_populates="author")
    
    def __repr__(self):
        return f"Author(id={self.id}, name={self.name!r})"

class Publisher(Base):
    __tablename__ = "publishers"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(50))
    
    books: Mapped[list["Book"]] = relationship(back_populates="publisher")
    
    def __repr__(self):
        return f"Publisher(id={self.id}, name={self.name!r})"

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
    sales: Mapped[list["Sale"]] = relationship(back_populates="book")
    
    def __repr__(self):
        return f"Book(id={self.id}, title={self.title!r})"

class Sale(Base):
    __tablename__ = "sales"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    quantity: Mapped[int]
    sale_date: Mapped[date]
    
    book: Mapped["Book"] = relationship(back_populates="sales")
    
    def __repr__(self):
        return f"Sale(id={self.id}, quantity={self.quantity}, date={self.sale_date})"

print("Models defined")
```

### Create Database and Tables

```python
# Create engine
engine = create_engine("sqlite:///bookstore.db", echo=True)

# Drop existing tables (start fresh)
Base.metadata.drop_all(engine)

# Create all tables
Base.metadata.create_all(engine)

print("✓ Database ready")
```

## The Session: Your Gateway to the Database

The **Session** is the core interface for all database operations in SQLAlchemy:

```python
# Create a session
with Session(engine) as session:
    # All database operations happen here
    # Session automatically closes when exiting 'with' block
    print(f"Session created: {session}")
```

**Key responsibilities of the Session:**
- Tracks changes to objects (Unit of Work pattern)
- Manages transactions (commit/rollback)
- Executes queries
- Handles connection pooling

## CREATE: Adding New Records

### Create a Single Author

```python
with Session(engine) as session:
    # Create an author object
    author = Author(name="George Orwell", birth_year=1903)
    
    # Add to session (not yet in database)
    session.add(author)
    print(f"Author added to session: {author}")
    print(f"ID before commit: {author.id}")  # None
```

### Commit to Save

```python
with Session(engine) as session:
    author = Author(name="George Orwell", birth_year=1903)
    session.add(author)
    
    # Commit to save to database
    session.commit()
    
    # Now ID is assigned
    print(f"✓ Author saved with ID: {author.id}")
```

### Create Multiple Authors

```python
with Session(engine) as session:
    authors = [
        Author(name="J.K. Rowling", birth_year=1965),
        Author(name="Stephen King", birth_year=1947),
        Author(name="Agatha Christie", birth_year=1890),
    ]
    
    # Add all at once
    session.add_all(authors)
    session.commit()
    
    print(f"✓ Created {len(authors)} authors:")
    for author in authors:
        print(f"  {author.id}: {author.name}")
```

### Create Publishers

```python
with Session(engine) as session:
    publishers = [
        Publisher(name="Penguin Books", country="UK"),
        Publisher(name="Bloomsbury", country="UK"),
        Publisher(name="Scribner", country="USA"),
    ]
    
    session.add_all(publishers)
    session.commit()
    
    print(f"✓ Created {len(publishers)} publishers:")
    for pub in publishers:
        print(f"  {pub.id}: {pub.name} ({pub.country})")
```

### Create Books with Relationships

```python
with Session(engine) as session:
    # Get authors and publishers
    orwell = session.scalars(select(Author).where(Author.name == "George Orwell")).first()
    rowling = session.scalars(select(Author).where(Author.name == "J.K. Rowling")).first()
    
    penguin = session.scalars(select(Publisher).where(Publisher.name == "Penguin Books")).first()
    bloomsbury = session.scalars(select(Publisher).where(Publisher.name == "Bloomsbury")).first()
    
    # Create books
    books = [
        Book(
            title="1984",
            isbn="9780451524935",
            price=Decimal("15.99"),
            author_id=orwell.id,
            publisher_id=penguin.id
        ),
        Book(
            title="Animal Farm",
            isbn="9780451526342",
            price=Decimal("13.99"),
            author_id=orwell.id,
            publisher_id=penguin.id
        ),
        Book(
            title="Harry Potter and the Philosopher's Stone",
            isbn="9780747532699",
            price=Decimal("19.99"),
            author_id=rowling.id,
            publisher_id=bloomsbury.id
        ),
    ]
    
    session.add_all(books)
    session.commit()
    
    print(f"✓ Created {len(books)} books:")
    for book in books:
        print(f"  {book.id}: {book.title} by author ID {book.author_id}")
```

### Create Using Relationships

```python
with Session(engine) as session:
    # Get Stephen King
    king = session.scalars(select(Author).where(Author.name == "Stephen King")).first()
    scribner = session.scalars(select(Publisher).where(Publisher.name == "Scribner")).first()
    
    # Create books using the relationship
    king.books.append(
        Book(
            title="The Shining",
            isbn="9780307743657",
            price=Decimal("18.99"),
            publisher=scribner
        )
    )
    
    session.commit()
    
    print(f"✓ Added book to {king.name}")
    print(f"  {king.name} now has {len(king.books)} book(s)")
```

## READ: Querying Data

### Get by Primary Key

```python
with Session(engine) as session:
    # Most efficient way to get a single record
    author = session.get(Author, 1)
    
    if author:
        print(f"Found: {author.name}")
    else:
        print("Author not found")
```

### Query All Records

```python
with Session(engine) as session:
    # Get all authors
    stmt = select(Author)
    authors = session.scalars(stmt).all()
    
    print(f"All authors ({len(authors)} total):")
    for author in authors:
        print(f"  {author.id}: {author.name} (born {author.birth_year})")
```

### Query with Filter

```python
with Session(engine) as session:
    # Authors born after 1950
    stmt = select(Author).where(Author.birth_year > 1950)
    modern_authors = session.scalars(stmt).all()
    
    print("Authors born after 1950:")
    for author in modern_authors:
        print(f"  {author.name} (born {author.birth_year})")
```

### Query with Multiple Conditions

```python
with Session(engine) as session:
    # UK publishers
    stmt = select(Publisher).where(Publisher.country == "UK")
    uk_publishers = session.scalars(stmt).all()
    
    print("UK Publishers:")
    for pub in uk_publishers:
        print(f"  {pub.name}")
```

### Query with LIKE

```python
with Session(engine) as session:
    # Books with "Harry" in title
    stmt = select(Book).where(Book.title.like("%Harry%"))
    harry_books = session.scalars(stmt).all()
    
    print("Books with 'Harry' in title:")
    for book in harry_books:
        print(f"  {book.title}")
```

### Ordering Results

```python
with Session(engine) as session:
    # Books ordered by price (descending)
    stmt = select(Book).order_by(Book.price.desc())
    books = session.scalars(stmt).all()
    
    print("Books by price (highest first):")
    for book in books:
        print(f"  ${book.price}: {book.title}")
```

### Limiting Results

```python
with Session(engine) as session:
    # Get top 3 most expensive books
    stmt = select(Book).order_by(Book.price.desc()).limit(3)
    top_books = session.scalars(stmt).all()
    
    print("Top 3 most expensive books:")
    for book in top_books:
        print(f"  ${book.price}: {book.title}")
```

### Using Relationships to Navigate

```python
with Session(engine) as session:
    # Get an author
    author = session.get(Author, 1)
    
    print(f"{author.name}'s books:")
    for book in author.books:
        print(f"  - {book.title} (${book.price})")
```

### Query with JOIN

```python
with Session(engine) as session:
    # Get books with their author names
    stmt = (
        select(Book.title, Book.price, Author.name)
        .join(Author)
        .where(Book.price > Decimal("15.00"))
    )
    
    results = session.execute(stmt).all()
    
    print("Books over $15 with authors:")
    for title, price, author_name in results:
        print(f"  {title} by {author_name}: ${price}")
```

### Count Records

```python
with Session(engine) as session:
    # Count all books
    stmt = select(func.count(Book.id))
    count = session.scalar(stmt)
    
    print(f"Total books in database: {count}")
```

### Aggregations

```python
with Session(engine) as session:
    # Average book price
    stmt = select(func.avg(Book.price))
    avg_price = session.scalar(stmt)
    
    print(f"Average book price: ${avg_price:.2f}")
    
    # Min and max
    stmt_min = select(func.min(Book.price))
    stmt_max = select(func.max(Book.price))
    
    min_price = session.scalar(stmt_min)
    max_price = session.scalar(stmt_max)
    
    print(f"Price range: ${min_price} - ${max_price}")
```

### Group By

```python
with Session(engine) as session:
    # Count books per author
    stmt = (
        select(Author.name, func.count(Book.id).label('book_count'))
        .join(Book)
        .group_by(Author.name)
        .order_by(func.count(Book.id).desc())
    )
    
    results = session.execute(stmt).all()
    
    print("Books per author:")
    for author_name, book_count in results:
        print(f"  {author_name}: {book_count} book(s)")
```

## UPDATE: Modifying Records

### Update by Modifying Object

```python
with Session(engine) as session:
    # Get a book
    book = session.get(Book, 1)
    print(f"Before: {book.title} - ${book.price}")
    
    # Modify attributes
    book.price = Decimal("17.99")
    
    # Commit saves changes
    session.commit()
    
    print(f"After: {book.title} - ${book.price}")
```

### Verify Update

```python
with Session(engine) as session:
    # Re-query to verify
    book = session.get(Book, 1)
    print(f"Verified: {book.title} - ${book.price}")
```

### Update Multiple Fields

```python
with Session(engine) as session:
    # Get author
    author = session.scalars(select(Author).where(Author.name == "J.K. Rowling")).first()
    
    print(f"Before: {author.name}, birth year: {author.birth_year}")
    
    # Update multiple fields
    author.name = "J.K. Rowling CBE"
    author.birth_year = 1965  # Correct if needed
    
    session.commit()
    
    print(f"After: {author.name}, birth year: {author.birth_year}")
```

### Bulk Update

```python
from sqlalchemy import update

with Session(engine) as session:
    # Increase all book prices by 10%
    stmt = (
        update(Book)
        .values(price=Book.price * Decimal("1.10"))
    )
    
    result = session.execute(stmt)
    session.commit()
    
    print(f"✓ Updated {result.rowcount} book prices (+10%)")
```

### Verify Bulk Update

```python
with Session(engine) as session:
    stmt = select(Book.title, Book.price).order_by(Book.title)
    books = session.execute(stmt).all()
    
    print("Updated book prices:")
    for title, price in books:
        print(f"  {title}: ${price:.2f}")
```

## DELETE: Removing Records

### Delete Single Object

```python
with Session(engine) as session:
    # Create a test author to delete
    test_author = Author(name="Test Author", birth_year=2000)
    session.add(test_author)
    session.commit()
    
    author_id = test_author.id
    print(f"Created test author with ID: {author_id}")
```

```python
with Session(engine) as session:
    # Get and delete
    author = session.get(Author, author_id)
    
    if author:
        print(f"Deleting: {author.name}")
        session.delete(author)
        session.commit()
        print("✓ Author deleted")
```

### Verify Deletion

```python
with Session(engine) as session:
    # Try to get deleted author
    author = session.get(Author, author_id)
    
    if author:
        print(f"Still exists: {author.name}")
    else:
        print("✓ Confirmed: Author no longer exists")
```

### Bulk Delete

```python
from sqlalchemy import delete

with Session(engine) as session:
    # Add some test sales
    book = session.get(Book, 1)
    sales = [
        Sale(book_id=book.id, quantity=1, sale_date=date.today()),
        Sale(book_id=book.id, quantity=2, sale_date=date.today()),
    ]
    session.add_all(sales)
    session.commit()
    
    print(f"Created {len(sales)} test sales")
```

```python
with Session(engine) as session:
    # Delete all sales from today
    stmt = delete(Sale).where(Sale.sale_date == date.today())
    
    result = session.execute(stmt)
    session.commit()
    
    print(f"✓ Deleted {result.rowcount} sales from today")
```

## Transactions: Commit and Rollback

### Successful Transaction

```python
with Session(engine) as session:
    try:
        # Multiple operations
        author = Author(name="Jane Austen", birth_year=1775)
        session.add(author)
        session.flush()  # Get ID without committing
        
        publisher = session.get(Publisher, 1)
        
        book = Book(
            title="Pride and Prejudice",
            isbn="9780141439518",
            price=Decimal("12.99"),
            author_id=author.id,
            publisher_id=publisher.id
        )
        session.add(book)
        
        # All or nothing
        session.commit()
        print("✓ Transaction successful")
        print(f"  Created author: {author.name}")
        print(f"  Created book: {book.title}")
        
    except Exception as e:
        print(f"✗ Transaction failed: {e}")
        raise
```

### Transaction Rollback

```python
with Session(engine) as session:
    # Create a test record
    test_author = Author(name="Rollback Test", birth_year=1999)
    session.add(test_author)
    
    # Changes are in session but not committed
    print(f"Author in session: {test_author.name}")
    
    # Decide not to save
    session.rollback()
    
    print("✓ Changes rolled back")
```

### Verify Rollback

```python
with Session(engine) as session:
    # Check if rolled-back author exists
    stmt = select(Author).where(Author.name == "Rollback Test")
    author = session.scalars(stmt).first()
    
    if author:
        print("Author exists (shouldn't happen)")
    else:
        print("✓ Confirmed: Rolled-back author does not exist")
```

### Error Handling with Rollback

```python
with Session(engine) as session:
    try:
        # This will fail due to duplicate ISBN
        book1 = Book(
            title="Test Book 1",
            isbn="9999999999999",
            price=Decimal("10.00"),
            author_id=1,
            publisher_id=1
        )
        session.add(book1)
        session.commit()
        
        print("Book 1 created")
        
        # This will fail (duplicate ISBN)
        book2 = Book(
            title="Test Book 2",
            isbn="9999999999999",  # Same ISBN!
            price=Decimal("10.00"),
            author_id=1,
            publisher_id=1
        )
        session.add(book2)
        session.commit()  # This will fail
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error: {type(e).__name__}")
        print("✓ Transaction rolled back")
```

## Complete Example: Bookstore Operations

Let's put it all together with a realistic workflow:

### Add New Inventory

```python
with Session(engine) as session:
    # Check if author exists
    author = session.scalars(
        select(Author).where(Author.name == "Agatha Christie")
    ).first()
    
    # Get publisher
    penguin = session.scalars(
        select(Publisher).where(Publisher.name == "Penguin Books")
    ).first()
    
    # Add new book
    new_book = Book(
        title="Murder on the Orient Express",
        isbn="9780062693662",
        price=Decimal("14.99"),
        author=author,
        publisher=penguin
    )
    
    session.add(new_book)
    session.commit()
    
    print(f"✓ Added: {new_book.title} by {author.name}")
    print(f"  Book ID: {new_book.id}")
```

### Record a Sale

```python
with Session(engine) as session:
    # Find the book
    book = session.scalars(
        select(Book).where(Book.title.like("%Orient Express%"))
    ).first()
    
    # Record sale
    sale = Sale(
        book=book,
        quantity=3,
        sale_date=date.today()
    )
    
    session.add(sale)
    session.commit()
    
    print(f"✓ Recorded sale:")
    print(f"  Book: {book.title}")
    print(f"  Quantity: {sale.quantity}")
    print(f"  Date: {sale.sale_date}")
```

### Generate Sales Report

```python
with Session(engine) as session:
    # Get sales with book details
    stmt = (
        select(
            Book.title,
            Author.name.label('author_name'),
            Sale.quantity,
            Sale.sale_date,
            (Book.price * Sale.quantity).label('total_revenue')
        )
        .join(Sale)
        .join(Author)
        .order_by(Sale.sale_date.desc())
    )
    
    sales = session.execute(stmt).all()
    
    print("Sales Report:")
    print(f"{'Date':<12} {'Book':<40} {'Author':<20} {'Qty':<5} {'Revenue'}")
    print("-" * 90)
    
    total_revenue = Decimal("0.00")
    for sale in sales:
        print(f"{sale.sale_date} {sale.title:<40} {sale.author_name:<20} "
              f"{sale.quantity:<5} ${sale.total_revenue:.2f}")
        total_revenue += sale.total_revenue
    
    print("-" * 90)
    print(f"{'Total Revenue:':<77} ${total_revenue:.2f}")
```

## Practice Exercises

### Exercise 1: Inventory Management

1. Add 5 new books to the database
2. Query books under $15
3. Increase prices of all books by 5%
4. Find the most expensive book

### Exercise 2: Author Analytics

1. Find all authors with more than 1 book
2. Calculate total value of books per author (price × count)
3. Find authors born before 1950
4. Update an author's birth year

### Exercise 3: Sales Tracking

1. Create 10 random sales for different books
2. Calculate total revenue
3. Find best-selling book (most quantity sold)
4. Delete sales older than a certain date

## Key Takeaways

- **Session manages everything** - all operations go through session
- **`add()` stages changes** - doesn't write to database yet
- **`commit()` saves changes** - writes to database
- **`rollback()` discards changes** - undo everything
- **Unit of Work** - session tracks what changed
- **Always use context managers** - `with Session(engine):`
- **Enable `echo=True`** - see the SQL being generated
- **Relationships** - navigate between related objects easily
- **For bulk operations** - use `update()` and `delete()` statements

## What's Next?

You now know how to perform CRUD operations with ORM. The next lesson covers testing with in-memory databases and schema migrations with Alembic.

**Next lesson:** [Testing and Migrations](05-testing-and-migrations.md)

---

[← Back: Defining Models](03-defining-models.md) | [Course Home](README.md) | [Next: Testing and Migrations →](05-testing-and-migrations.md)
