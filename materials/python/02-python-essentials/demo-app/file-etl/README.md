# File ETL Demo Application

A demonstration ETL (Extract, Transform, Load) application that showcases all concepts from the Python Essentials lesson:

- Project setup with uv
- Data structures for processing records
- Object-oriented design with inheritance and composition
- Type hints and generics for type safety

## What It Demonstrates

This application reads customer and order data from CSV and JSON files, validates and transforms the data, and loads it into a SQL Server database.

**Key patterns shown:**

1. **Generic file readers**: `FileReader[T]` works with any data type
2. **Dataclass models**: Typed `Customer` and `Order` models
3. **Composition**: Readers, validators, and loaders are composed, not inherited
4. **Type safety**: Full type hints with generics throughout

## Project Structure

```
file-etl/
├── pyproject.toml          # Project metadata and dependencies
├── README.md               # This file
├── src/
│   └── file_etl/
│       ├── __init__.py     # Package initialization
│       ├── main.py         # Pipeline orchestration
│       ├── models.py       # Customer and Order dataclasses
│       ├── readers.py      # Generic file readers (CSV, JSON)
│       └── loader.py       # SQL Server loader
└── data/
    ├── customers.csv       # Sample customer data
    └── orders.json         # Sample order data
```

## Setup

### Prerequisites

- Python 3.10 or higher
- SQL Server (local or remote)
- uv installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Installation

```bash
# Clone or navigate to the project directory
cd file-etl

# Install dependencies
uv sync

# Or if using pip:
pip install -e .
```

### Database Setup

Create the target database and tables:

```sql
-- Create database
CREATE DATABASE demo_etl;
GO

USE demo_etl;
GO

-- Create customers table
CREATE TABLE customers (
    id INT PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    email NVARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT GETDATE()
);

-- Create orders table
CREATE TABLE orders (
    id INT PRIMARY KEY,
    customer_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status NVARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
```

## Running the Application

```bash
# Run with uv
uv run python -m file_etl.main

# Or activate virtual environment and run
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python -m file_etl.main
```

### Configuration

The application connects to SQL Server using:

- **Server**: `localhost`
- **Database**: `demo_etl`
- **Authentication**: Windows Authentication (Trusted_Connection)

To use different settings, modify the connection string in `main.py`:

```python
connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=your_db;UID=user;PWD=pass"
```

## Code Walkthrough

### 1. Models (`models.py`)

Dataclasses define the shape of our data:

```python
@dataclass
class Customer:
    id: int
    name: str
    email: str
```

**Concepts**: Dataclasses, type hints, data validation

### 2. Readers (`readers.py`)

Generic readers work with any data type:

```python
class FileReader(Generic[T], ABC):
    @abstractmethod
    def read(self) -> List[T]:
        pass

class CsvReader(FileReader[T]):
    # Reads CSV and converts to type T
    ...
```

**Concepts**: Generics, abstract base classes, inheritance, protocols

### 3. Loader (`loader.py`)

Generic loader inserts any type into SQL Server:

```python
class SqlServerLoader(Generic[T]):
    def load(self, records: List[T], table: str):
        # Uses dataclass fields to build INSERT statements
        ...
```

**Concepts**: Generics, composition, error handling

### 4. Main Pipeline (`main.py`)

Orchestrates the ETL process:

```python
# Read customers from CSV
customer_reader = CsvReader[Customer]("data/customers.csv", Customer)
customers = customer_reader.read()

# Load to database
loader = SqlServerLoader[Customer](connection_string)
loader.load(customers, "customers")
```

**Concepts**: Composition, dependency injection, type safety

## Sample Data

### `data/customers.csv`

```csv
id,name,email
1,Alice Johnson,alice@example.com
2,Bob Smith,bob@example.com
3,Charlie Brown,charlie@example.com
```

### `data/orders.json`

```json
[
    {"id": 101, "customer_id": 1, "amount": 150.50, "status": "completed"},
    {"id": 102, "customer_id": 2, "amount": 200.00, "status": "pending"},
    {"id": 103, "customer_id": 1, "amount": 75.25, "status": "completed"}
]
```

## Type Checking

The project is fully typed and can be checked with mypy:

```bash
# Run type checker
uv run mypy src/file_etl

# Should output: Success: no issues found
```

## Extending the Application

### Adding a New File Format

To add XML support:

1. Create `XmlReader[T]` in `readers.py`
2. Implement the `read()` method
3. Use it in `main.py` just like CSV or JSON readers

No changes needed to `SqlServerLoader` or models—composition makes this easy!

### Adding a New Entity Type

To add products:

1. Define `Product` dataclass in `models.py`
2. Create sample data file
3. Use existing readers and loader with `Product` type

The generic design handles it automatically.

## Key Takeaways

This demo shows:

- **Project structure**: src layout, pyproject.toml, proper packaging
- **Data structures**: Lists, dicts, dataclasses for different use cases
- **OOP**: Inheritance for shared behavior, composition for flexibility
- **Type safety**: Generics ensure correctness at compile time

## Next Steps

- Modify the code to add transformations (e.g., uppercase names)
- Add error handling for invalid records
- Implement batch loading for large datasets
- Add unit tests using pytest

## Troubleshooting

### Import errors

Make sure you're running from the project root and the package is installed:

```bash
pip install -e .
```

### Database connection errors

- Verify SQL Server is running
- Check ODBC driver is installed: `odbcinst -q -d`
- Test connection string with a simple script

### Type checking errors

Run mypy with verbose output:

```bash
mypy --show-error-codes src/file_etl
```

---

**Related Lessons:**

- [Project Setup](../../01-project-setup/01-creating-a-python-project.md)
- [Data Structures](../../02-data-structures/02-collections.md)
- [Object-Oriented Python](../../03-oop/01-object-oriented-python.md)
- [Type Hints](../../04-typing/01-type-hints.md)
- [Generics](../../04-typing/02-generics.md)
