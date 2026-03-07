---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Schema Migrations with Alembic

## Overview

As your application evolves, your database schema needs to change — new columns, new tables, modified constraints. These changes must be tracked, versioned, and deployed reliably across all environments.

**Schema migrations** treat database changes as version-controlled code. Instead of manually running SQL scripts, you create migration files that can be applied and rolled back automatically.

This lesson covers:

1. **Why migrations matter** — problems they solve
2. **Alembic fundamentals** — SQLAlchemy's migration tool
3. **Migration workflow** — create, apply, rollback
4. **Best practices** — safe, reversible migrations

## Why Migrations Matter

### The Problem Without Migrations

```python
# Week 1 — initial model
class Book(Base):
    __tablename__ = "books"
    id:    Mapped[int]     = mapped_column(primary_key=True)
    title: Mapped[str]     = mapped_column(String(200))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
```

You deploy to production. Database is created.

```python
# Week 3 — product owner wants page counts
class Book(Base):
    __tablename__ = "books"
    id:         Mapped[int]           = mapped_column(primary_key=True)
    title:      Mapped[str]           = mapped_column(String(200))
    price:      Mapped[Decimal]       = mapped_column(Numeric(10, 2))
    page_count: Mapped[Optional[int]]  # NEW COLUMN
```

**Without migrations:** how do you add `page_count` to production? Manual `ALTER TABLE`? What if you forget? How do teammates get this change? How do you rollback?

**With migrations:**

```bash
alembic revision --autogenerate -m "add page_count to books"
alembic upgrade head
```

Done. Version controlled. Reversible. Trackable.

### Benefits

| Benefit | Explanation |
|---------|-------------|
| Version control | Schema changes tracked in git alongside code |
| Automation | Apply changes automatically across environments |
| Reversibility | Rollback bad changes safely |
| Documentation | Clear history of all schema changes |
| Team coordination | Everyone gets the same schema changes |
| CI/CD integration | Deploy schema with code |

## What is Alembic?

Alembic is SQLAlchemy's migration tool — think of it as "Git for your database schema."

**Key features:**
- **Autogeneration** — detects model changes automatically
- **SQL generation** — creates appropriate SQL for your database
- **Version tracking** — maintains migration history in the database
- **Reversibility** — `upgrade()` and `downgrade()` per migration
- **Database agnostic** — PostgreSQL, MySQL, SQLite, and more

## Working Directory

All commands in this lesson run from the `alembic-demo/` directory. Let's create it:

```{code-cell} python
%%bash
mkdir -p alembic-demo
echo "Working directory ready"
```

## Project Files

### `models.py`

```{code-cell} python
%%bash
cat > alembic-demo/models.py << 'EOF'
from sqlalchemy import String, ForeignKey, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
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

class Publisher(Base):
    __tablename__ = "publishers"
    id:      Mapped[int]          = mapped_column(primary_key=True)
    name:    Mapped[str]          = mapped_column(String(100))
    country: Mapped[str]          = mapped_column(String(50))
    books:   Mapped[list["Book"]] = relationship(back_populates="publisher")

class Book(Base):
    __tablename__ = "books"
    id:           Mapped[int]         = mapped_column(primary_key=True)
    title:        Mapped[str]         = mapped_column(String(200))
    isbn:         Mapped[str]         = mapped_column(String(13), unique=True)
    price:        Mapped[Decimal]     = mapped_column(Numeric(10, 2))
    author_id:    Mapped[int]         = mapped_column(ForeignKey("authors.id"))
    publisher_id: Mapped[int]         = mapped_column(ForeignKey("publishers.id"))
    author:       Mapped["Author"]    = relationship(back_populates="books")
    publisher:    Mapped["Publisher"] = relationship(back_populates="books")
EOF
echo "models.py written"
```

## Initializing Alembic

```{code-cell} python
%%bash
cd alembic-demo && alembic init migrations
echo "Alembic initialized"
```

**This creates:**

```
alembic-demo/
├── alembic.ini           ← Alembic config
├── models.py             ← our models
└── migrations/
    ├── env.py            ← environment / connection config
    ├── script.py.mako    ← migration file template
    ├── README
    └── versions/         ← migration files go here
```

## Configure Alembic

### Set the Database URL in `alembic.ini`

```{code-cell} python
%%bash
sed -i 's|sqlalchemy.url = .*|sqlalchemy.url = sqlite:///bookstore.db|' alembic-demo/alembic.ini
grep "sqlalchemy.url" alembic-demo/alembic.ini
```

### Point `env.py` to Our Models

```{code-cell} python
%%bash
cat > alembic-demo/migrations/env.py << 'EOF'
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import our models so autogenerate can compare against them
from models import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata  # autogenerate compares DB to this


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF
echo "env.py configured"
```

## Creating the First Migration

```{code-cell} python
%%bash
cd alembic-demo && alembic revision --autogenerate -m "create bookstore tables"
```

Alembic detected our three models and generated a migration file in `migrations/versions/`.

### View the Generated Migration

```{code-cell} python
%%bash
cat alembic-demo/migrations/versions/*.py
```

**Key parts:**

```python
def upgrade():
    # Creates all three tables with columns, FKs, and constraints

def downgrade():
    # Drops them in reverse order (respecting FK dependencies)
```

**Always review generated migrations** — autogenerate is smart but not perfect. It won't detect renamed columns and won't generate data migrations.

## Applying Migrations

```{code-cell} python
%%bash
cd alembic-demo && alembic upgrade head
```

```{code-cell} python
%%bash
cd alembic-demo && alembic current
```

```{code-cell} python
%%bash
cd alembic-demo && alembic history
```

### Verify Tables Were Created

```{code-cell} python
from sqlalchemy import create_engine, inspect

engine = create_engine("sqlite:///alembic-demo/bookstore.db")
print("Tables:", inspect(engine).get_table_names())
# includes 'alembic_version' — Alembic's internal tracking table
```

## Adding a Column — Migration Workflow

### Step 1: Update the Model

```{code-cell} python
%%bash
cat > alembic-demo/models.py << 'EOF'
from sqlalchemy import String, ForeignKey, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
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

class Publisher(Base):
    __tablename__ = "publishers"
    id:      Mapped[int]          = mapped_column(primary_key=True)
    name:    Mapped[str]          = mapped_column(String(100))
    country: Mapped[str]          = mapped_column(String(50))
    books:   Mapped[list["Book"]] = relationship(back_populates="publisher")

class Book(Base):
    __tablename__ = "books"
    id:           Mapped[int]           = mapped_column(primary_key=True)
    title:        Mapped[str]           = mapped_column(String(200))
    isbn:         Mapped[str]           = mapped_column(String(13), unique=True)
    price:        Mapped[Decimal]       = mapped_column(Numeric(10, 2))
    author_id:    Mapped[int]           = mapped_column(ForeignKey("authors.id"))
    publisher_id: Mapped[int]           = mapped_column(ForeignKey("publishers.id"))
    page_count:   Mapped[Optional[int]]  # NEW
    author:       Mapped["Author"]      = relationship(back_populates="books")
    publisher:    Mapped["Publisher"]   = relationship(back_populates="books")
EOF
echo "models.py updated"
```

### Step 2: Generate Migration

```{code-cell} python
%%bash
cd alembic-demo && alembic revision --autogenerate -m "add page_count to books"
```

### Step 3: Review It

```{code-cell} python
%%bash
ls alembic-demo/migrations/versions/
```

```{code-cell} python
%%bash
# Show the newest migration file
cd alembic-demo && cat migrations/versions/$(ls -t migrations/versions/ | head -1)
```

The generated migration should look like:

```python
def upgrade():
    op.add_column("books", sa.Column("page_count", sa.Integer(), nullable=True))

def downgrade():
    op.drop_column("books", "page_count")
```

### Step 4: Apply It

```{code-cell} python
%%bash
cd alembic-demo && alembic upgrade head
```

### Step 5: Verify

```{code-cell} python
from sqlalchemy import create_engine, inspect

engine = create_engine("sqlite:///alembic-demo/bookstore.db")
cols = {c["name"]: c["type"] for c in inspect(engine).get_columns("books")}
print("books columns:", list(cols.keys()))
assert "page_count" in cols
print("page_count column confirmed")
```

## Rolling Back

```{code-cell} python
%%bash
cd alembic-demo && alembic downgrade -1
```

```{code-cell} python
%%bash
cd alembic-demo && alembic current
```

```{code-cell} python
from sqlalchemy import create_engine, inspect

engine = create_engine("sqlite:///alembic-demo/bookstore.db")
cols = [c["name"] for c in inspect(engine).get_columns("books")]
print("books columns after rollback:", cols)
assert "page_count" not in cols
print("Rollback confirmed — page_count removed")
```

## Common Migration Operations

### Add a Column

```python
def upgrade():
    op.add_column("books", sa.Column("rating", sa.Numeric(2, 1), nullable=True))

def downgrade():
    op.drop_column("books", "rating")
```

### Add an Index

```python
def upgrade():
    op.create_index("ix_books_title", "books", ["title"])

def downgrade():
    op.drop_index("ix_books_title", "books")
```

### Modify a Column

```python
def upgrade():
    op.alter_column("books", "title", existing_type=sa.String(200), nullable=False)

def downgrade():
    op.alter_column("books", "title", existing_type=sa.String(200), nullable=True)
```

### Data Migration (Schema + Data Together)

```python
from sqlalchemy.sql import table, column

def upgrade():
    op.add_column("books", sa.Column("rating", sa.Numeric(2, 1), nullable=True))

    books_table = table("books", column("id", sa.Integer), column("rating", sa.Numeric))
    op.execute(books_table.update().values(rating=5.0))

def downgrade():
    op.drop_column("books", "rating")
```

## Migration Best Practices

### 1. Always Review Before Applying

Autogenerate is smart but not perfect:
- Renamed columns look like drop + add (data loss!)
- Some constraint changes are missed
- Data migrations are never generated automatically

### 2. Keep Migrations Reversible

```python
# Good — has a proper downgrade
def upgrade():
    op.add_column("books", sa.Column("rating", sa.Integer()))

def downgrade():
    op.drop_column("books", "rating")

# Bad — nothing to roll back
def downgrade():
    pass
```

### 3. One Logical Change Per Migration

```
# Good
add_page_count_to_books.py
add_reviews_table.py

# Bad
add_page_count_and_reviews_and_fix_authors.py
```

### 4. Handle Existing Data When Adding Non-Nullable Columns

```python
def upgrade():
    # Step 1: add nullable
    op.add_column("books", sa.Column("page_count", sa.Integer(), nullable=True))
    # Step 2: backfill
    op.execute("UPDATE books SET page_count = 0 WHERE page_count IS NULL")
    # Step 3: make non-nullable
    op.alter_column("books", "page_count", nullable=False)
```

### 5. Version Control Your Migrations

```bash
git add migrations/versions/
git commit -m "Add page_count to books"
```

## Alembic in CI/CD

### Development Workflow

```bash
# 1. Change model
# 2. Generate migration
alembic revision --autogenerate -m "describe the change"
# 3. Review the file
# 4. Test locally
alembic upgrade head
alembic downgrade -1
alembic upgrade head
# 5. Commit
git add migrations/versions/...
git commit -m "Migration: describe the change"
```

### Deployment

```bash
# Run as part of every deployment
alembic upgrade head
```

### Rollback Plan

```bash
alembic downgrade -1
```

## Cleanup

```{code-cell} python
%%bash
rm -rf alembic-demo/
echo "Demo directory removed"
```

## Key Takeaways

- **Migrations treat schema as code** — version controlled, reviewable, deployable
- **`alembic revision --autogenerate`** — detects model changes automatically
- **Always review** — autogenerate is helpful but not infallible
- **`upgrade()` / `downgrade()`** — both directions must work
- **Test upgrade → downgrade → upgrade** before committing
- **One change per migration** — keeps history clean and debuggable
- **Handle existing data** — consider impact on production rows
- **Commit migrations with the code** that requires them

---

[← Back: Testing](05-testing.md) | [Course Home](README.md)
