# Schema Migrations with Alembic

## Overview

As your application evolves, your database schema needs to change. Adding columns, creating tables, modifying constraints - these changes need to be tracked, versioned, and deployed reliably across all environments (development, staging, production).

**Schema migrations** solve this problem by treating database changes as version-controlled code. Instead of manually running SQL scripts, you create migration files that can be applied and rolled back automatically.

This lesson covers:

1. **Why migrations matter** - Problems they solve, benefits they provide
2. **Alembic fundamentals** - SQLAlchemy's migration tool
3. **Migration workflow** - Create, review, apply, rollback
4. **Best practices** - Writing safe, reversible migrations

## Why Migrations Matter

### The Problem Without Migrations

Imagine this scenario:

```python
# Week 1: Your Book model
class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
```

You deploy to production. Database is created.

```python
# Week 3: Product owner wants page counts
class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    page_count: Mapped[Optional[int]]  # NEW COLUMN
```

**Without migrations:**
- How do you add `page_count` to production?
- Manual `ALTER TABLE` script? What if you forget?
- How do teammates get this change?
- How do you rollback if something breaks?

**With migrations:**
```bash
# Generate migration automatically
alembic revision --autogenerate -m "add page_count to books"

# Apply to all environments
alembic upgrade head
```

Done. Version controlled. Reversible. Trackable.

### Benefits of Migrations

1. **Version Control** - Schema changes tracked in git
2. **Automation** - Apply changes automatically across environments
3. **Reversibility** - Rollback bad changes safely
4. **Documentation** - Clear history of all schema changes
5. **Team Coordination** - Everyone gets same schema changes
6. **CI/CD Integration** - Deploy schema with code

## The Bookstore Models

For this lesson, we'll work with a simple bookstore database. Here are the complete model definitions you'll need:

```python
from sqlalchemy import String, ForeignKey, Numeric, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from decimal import Decimal
from typing import Optional

class Base(DeclarativeBase):
    pass

class Author(Base):
    """Authors write books."""
    __tablename__ = "authors"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    birth_year: Mapped[Optional[int]]
    
    # Relationship
    books: Mapped[list["Book"]] = relationship(back_populates="author")

class Publisher(Base):
    """Publishers publish books."""
    __tablename__ = "publishers"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(50))
    
    # Relationship
    books: Mapped[list["Book"]] = relationship(back_populates="publisher")

class Book(Base):
    """Books in the bookstore."""
    __tablename__ = "books"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    isbn: Mapped[str] = mapped_column(String(13), unique=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    
    # Foreign keys
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    publisher_id: Mapped[int] = mapped_column(ForeignKey("publishers.id"))
    
    # Relationships
    author: Mapped["Author"] = relationship(back_populates="books")
    publisher: Mapped["Publisher"] = relationship(back_populates="books")
```

**Save this as `models.py`** - you'll need it for Alembic configuration.

## What is Alembic?

Alembic is SQLAlchemy's migration tool. Think of it as "Git for your database schema."

**Key features:**
- **Autogeneration** - Detects model changes automatically
- **SQL generation** - Creates appropriate SQL for your database
- **Version tracking** - Maintains migration history
- **Reversibility** - Up and down migrations
- **Database agnostic** - Works with PostgreSQL, MySQL, SQLite, etc.

## Installing Alembic

```bash
pip install alembic
```

Or with uv:

```bash
uv pip install alembic
```

Verify installation:

```bash
alembic --version
```

## Initializing Alembic

```bash
alembic init migrations
```

**This creates:**
```
your_project/
├── migrations/
│   ├── versions/          # Migration files go here
│   ├── env.py            # Alembic environment config
│   ├── script.py.mako    # Migration template
│   └── README
├── alembic.ini           # Alembic config file
└── models.py             # Your SQLAlchemy models
```

## Configure Alembic

### Step 1: Set Database URL

Edit `alembic.ini`:

```ini
# alembic.ini
[alembic]
# Connection string
sqlalchemy.url = sqlite:///bookstore.db
```

Or use environment variables (better):

```python
# migrations/env.py
from os import environ

# Get connection string from environment
config.set_main_option(
    "sqlalchemy.url",
    environ.get("DATABASE_URL", "sqlite:///bookstore.db")
)
```

### Step 2: Point Alembic to Your Models

Edit `migrations/env.py`:

```python
# migrations/env.py
from myapp.models import Base  # Your Base class

# Set target metadata
target_metadata = Base.metadata
```

**Important:** Replace `myapp.models` with the actual import path to your models.

## Creating Your First Migration

```bash
# Autogenerate migration from model changes
alembic revision --autogenerate -m "create bookstore tables"
```

**This creates a migration file:**

```python
# migrations/versions/abc123_create_bookstore_tables.py
"""create bookstore tables

Revision ID: abc123
Revises: 
Create Date: 2024-02-04 10:30:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create authors table
    op.create_table(
        'authors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('birth_year', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create publishers table
    op.create_table(
        'publishers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('country', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create books table
    op.create_table(
        'books',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('isbn', sa.String(length=13), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('publisher_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['authors.id']),
        sa.ForeignKeyConstraint(['publisher_id'], ['publishers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('isbn')
    )

def downgrade():
    op.drop_table('books')
    op.drop_table('publishers')
    op.drop_table('authors')
```

### Understanding the Migration File

**Metadata:**
- `revision` - Unique ID for this migration
- `down_revision` - Previous migration (None for first)
- `branch_labels` - For branching migrations
- `depends_on` - For dependencies

**Functions:**
- `upgrade()` - Apply the migration (move forward)
- `downgrade()` - Rollback the migration (move backward)

**Important:** Always review generated migrations. Autogeneration is smart but not perfect.

## Applying Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Output:
# INFO  [alembic.runtime.migration] Running upgrade  -> abc123, create bookstore tables
```

**What happens:**
1. Alembic checks current database version
2. Determines which migrations need to run
3. Executes `upgrade()` function for each migration
4. Updates `alembic_version` table with current version

### Verify Migration Applied

```python
from sqlalchemy import create_engine, inspect

engine = create_engine("sqlite:///bookstore.db")
inspector = inspect(engine)

# List all tables
tables = inspector.get_table_names()
print("Tables:", tables)

# Output: Tables: ['alembic_version', 'authors', 'books', 'publishers']
```

## Rolling Back Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade abc123

# Rollback everything
alembic downgrade base
```

**What happens:**
1. Alembic identifies current version
2. Determines which migrations to undo
3. Executes `downgrade()` functions in reverse order
4. Updates `alembic_version` table

## Migration Workflow Example

Let's walk through a complete workflow: adding a new column to the Book model.

### Step 1: Add a new column to Book model

```python
class Book(Base):
    __tablename__ = "books"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    isbn: Mapped[str] = mapped_column(String(13), unique=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    publisher_id: Mapped[int] = mapped_column(ForeignKey("publishers.id"))
    
    # NEW COLUMN
    page_count: Mapped[Optional[int]]
```

### Step 2: Generate migration

```bash
alembic revision --autogenerate -m "add page_count to books"
```

### Step 3: Review generated migration

```python
# migrations/versions/def456_add_page_count_to_books.py
def upgrade():
    op.add_column('books', sa.Column('page_count', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('books', 'page_count')
```

**Looks good!** The migration:
- Adds nullable column (safe - won't break existing rows)
- Has proper downgrade (reversible)
- Uses correct data type

### Step 4: Apply migration

```bash
alembic upgrade head
```

### Step 5: Verify the change

```python
from sqlalchemy import create_engine, inspect

engine = create_engine("sqlite:///bookstore.db")
inspector = inspect(engine)

# Get book table columns
columns = inspector.get_columns('books')
for col in columns:
    print(f"{col['name']}: {col['type']}")

# Output includes:
# page_count: INTEGER
```

## Viewing Migration History

```bash
# Show all migrations
alembic history

# Show current version
alembic current

# Output:
# abc123 (head), create bookstore tables
# def456, add page_count to books
```

### Detailed History

```bash
# Show full history with details
alembic history --verbose
```

## Common Migration Operations

### Adding a Column

```python
def upgrade():
    op.add_column('books', sa.Column('rating', sa.Numeric(2, 1), nullable=True))

def downgrade():
    op.drop_column('books', 'rating')
```

### Dropping a Column

```python
def upgrade():
    op.drop_column('books', 'old_field')

def downgrade():
    # Recreate if needed (careful with data loss!)
    op.add_column('books', sa.Column('old_field', sa.String(50), nullable=True))
```

### Adding an Index

```python
def upgrade():
    op.create_index('ix_books_title', 'books', ['title'])

def downgrade():
    op.drop_index('ix_books_title', 'books')
```

### Modifying a Column

```python
def upgrade():
    # Make column non-nullable
    op.alter_column('books', 'title',
                    existing_type=sa.String(200),
                    nullable=False)

def downgrade():
    # Make column nullable again
    op.alter_column('books', 'title',
                    existing_type=sa.String(200),
                    nullable=True)
```

### Creating a Table

```python
def upgrade():
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('book_id', sa.Integer(), sa.ForeignKey('books.id')),
        sa.Column('rating', sa.Integer()),
        sa.Column('comment', sa.Text())
    )

def downgrade():
    op.drop_table('reviews')
```

## Data Migrations

Sometimes you need to migrate data, not just schema:

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
    # Add new column
    op.add_column('books', sa.Column('rating', sa.Numeric(2, 1), nullable=True))
    
    # Migrate data: set default rating for existing books
    books_table = table('books',
        column('id', sa.Integer),
        column('rating', sa.Numeric)
    )
    
    op.execute(
        books_table.update().values(rating=5.0)
    )

def downgrade():
    op.drop_column('books', 'rating')
```

## Advanced Topics

### Multiple Databases

Support different databases in one migration:

```python
def upgrade():
    # Get database bind
    bind = op.get_bind()
    
    if bind.dialect.name == 'postgresql':
        # PostgreSQL-specific
        op.execute("CREATE INDEX CONCURRENTLY idx_books_title ON books(title)")
    else:
        # Generic fallback
        op.create_index('idx_books_title', 'books', ['title'])
```

### Branching Migrations

When multiple developers create migrations simultaneously:

```bash
# Merge branches
alembic merge -m "merge heads" head1 head2
```

### Custom Migration Template

Edit `migrations/script.py.mako` to customize migration template.

## Migration Best Practices

### 1. Always Review Generated Migrations

Autogeneration is not perfect:
- May miss renamed columns (sees as drop + add)
- May not detect all constraint changes
- Won't generate data migrations

**Always review and edit before applying.**

### 2. Test Migrations

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Test upgrade again
alembic upgrade head
```

### 3. Make Migrations Reversible

Always provide proper `downgrade()`:

```python
# Good
def upgrade():
    op.add_column('books', sa.Column('rating', sa.Integer()))

def downgrade():
    op.drop_column('books', 'rating')

# Bad
def downgrade():
    pass  # Not reversible!
```

### 4. One Logical Change Per Migration

```python
# Good: Focused migration
# "add_page_count_to_books.py"

# Bad: Multiple unrelated changes
# "add_page_count_and_change_author_and_add_reviews.py"
```

### 5. Handle Existing Data

When adding non-nullable columns:

```python
def upgrade():
    # Step 1: Add nullable column
    op.add_column('books', sa.Column('page_count', sa.Integer(), nullable=True))
    
    # Step 2: Populate with defaults
    op.execute("UPDATE books SET page_count = 0 WHERE page_count IS NULL")
    
    # Step 3: Make non-nullable
    op.alter_column('books', 'page_count', nullable=False)
```

### 6. Use Transactions

Migrations run in transactions by default. Be careful with:
- DDL on some databases (MySQL)
- Large data migrations
- Operations that can't rollback

### 7. Version Control Everything

```bash
git add migrations/versions/abc123_create_bookstore_tables.py
git commit -m "Add initial bookstore schema migration"
```

## Migrations in CI/CD

### Development Workflow

```bash
# 1. Create migration
alembic revision --autogenerate -m "add feature"

# 2. Review and edit

# 3. Test locally
alembic upgrade head

# 4. Commit
git add migrations/versions/...
git commit -m "Add feature migration"
```

### Production Deployment

```bash
# In deployment script
alembic upgrade head
```

### Rollback Plan

```bash
# If deployment fails
alembic downgrade -1
```

## Common Issues and Solutions

### Issue: "Target database is not up to date"

```bash
# Check current version
alembic current

# Check history
alembic history

# Upgrade to head
alembic upgrade head
```

### Issue: Migration conflicts

```bash
# Multiple heads detected
alembic heads

# Merge them
alembic merge -m "merge heads" head1 head2
```

### Issue: Autogeneration missed changes

Edit migration manually:

```python
def upgrade():
    # Add missed operation
    op.create_index('idx_name', 'table', ['column'])
```

## Key Takeaways

- **Migrations treat schema as code** - Version controlled, reviewable, deployable
- **Alembic autogeneration** - Detects model changes automatically
- **Always review** - Autogeneration is smart but not perfect
- **Reversible migrations** - Proper `downgrade()` enables rollback
- **Test thoroughly** - Upgrade, downgrade, upgrade again
- **One change per migration** - Keeps history clean and debuggable
- **Handle existing data** - Consider impact on production data
- **CI/CD integration** - Deploy schema with code automatically

## Practice Exercises

### Exercise 1: Complete Migration Workflow

1. Set up Alembic in a new project
2. Create the bookstore models
3. Generate initial migration
4. Apply migration and verify tables created
5. Add a `rating` column to Book (Decimal, 1-5)
6. Generate migration for rating column
7. Apply migration
8. Test rollback and upgrade

### Exercise 2: Data Migration

1. Add an `active` column to Author (Boolean, default True)
2. Create migration that:
   - Adds the column as nullable
   - Sets all existing authors to active=True
   - Makes column non-nullable
3. Test upgrade and downgrade

### Exercise 3: Complex Schema Change

1. Add a new Reviews table:
   - id (primary key)
   - book_id (foreign key to books)
   - rating (Integer, 1-5)
   - comment (Text)
   - created_at (DateTime)
2. Generate migration
3. Review and adjust if needed
4. Apply migration
5. Add sample review data
6. Test rollback (should cascade delete reviews)

### Exercise 4: Production Scenario

1. Create a migration to rename a column (hint: requires manual migration, not autogenerate)
2. Write a data migration to backfill a new column based on existing data
3. Create a migration that works on both SQLite and PostgreSQL

## Advanced Note: Migration Strategies at Scale

At scale, migrations require careful planning:

**Blue-Green Deployments:**
- Migrations must be backward compatible
- Old code must work with new schema
- Deploy in phases: schema, then code

**Zero-Downtime Migrations:**
- Add new column as nullable
- Deploy code to use new column
- Backfill data
- Make column non-nullable
- Drop old column in separate deployment

**Large Table Migrations:**
- PostgreSQL: `CREATE INDEX CONCURRENTLY`
- Batch updates for data migrations
- Consider maintenance windows

**Multiple Databases:**
- Separate migration branches per database
- Or conditional migrations per dialect

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Core Reference](https://docs.sqlalchemy.org/en/14/core/)
- [Database Migration Best Practices](https://www.brunton-spall.co.uk/post/2014/05/06/database-migrations-done-right/)

---

[← Back: Testing and Database Lifecycle](05-testing-and-migrations.md) | [Course Home](README.md) | [Main Course Home](../../README.md)
