# Python Essentials Exercises

These exercises reinforce the concepts from all four lesson sections: project setup, data structures, OOP, and type systems. Complete them in order, referring back to the lesson materials as needed.

---

## Exercise 1: Project Setup with uv

**Objective**: Create a new Python project using uv, add dependencies, and run a script.

**Duration**: ~15 minutes

### Tasks

1. Initialize a new project called `data-processor` using uv
2. Add the following dependencies:
   - `requests` (for API calls)
   - `pandas` (for data processing)
3. Create a script `src/data_processor/main.py` that:
   - Imports both libraries
   - Makes a GET request to `https://api.github.com/users/github`
   - Prints the username from the response
4. Run the script using `uv run`
5. Generate a lockfile and verify it exists

### Starting Point

```bash
# Your terminal commands here
uv init data-processor
cd data-processor
uv add requests pandas
# ... continue
```

<details>
<summary><strong>Solution</strong></summary>

```bash
# 1. Initialize project
uv init data-processor
cd data-processor

# 2. Add dependencies
uv add requests pandas

# 3. Create the script
mkdir -p src/data_processor
cat > src/data_processor/main.py << 'EOF'
import requests
import pandas as pd

def main():
    # Fetch GitHub user data
    response = requests.get("https://api.github.com/users/github")
    data = response.json()
    
    print(f"Username: {data['login']}")
    print(f"Name: {data['name']}")
    print(f"Public repos: {data['public_repos']}")
    
    # Demonstrate pandas is available
    df = pd.DataFrame([data])
    print(f"\nDataFrame shape: {df.shape}")

if __name__ == "__main__":
    main()
EOF

# 4. Run the script
uv run python src/data_processor/main.py

# 5. Verify lockfile exists
ls uv.lock
# uv.lock should be present
```

**Key concepts demonstrated:**
- `uv init` creates project structure
- `uv add` installs and updates `pyproject.toml`
- `uv.lock` captures exact versions
- `uv run` handles virtual environment automatically

</details>

### Bonus Challenge

Export requirements to a `requirements.txt` for Docker deployment:

```bash
uv pip freeze > requirements.txt
```

---

## Exercise 2: Data Structures

**Objective**: Given a dataset, perform filtering, grouping, and deduplication using appropriate data structures.

**Duration**: ~20 minutes

### Starting Data

```python
# Customer transactions
transactions = [
    {"customer_id": 1, "customer_name": "Alice", "amount": 100.0, "category": "electronics"},
    {"customer_id": 2, "customer_name": "Bob", "amount": 50.0, "category": "books"},
    {"customer_id": 1, "customer_name": "Alice", "amount": 200.0, "category": "electronics"},
    {"customer_id": 3, "customer_name": "Charlie", "amount": 75.0, "category": "books"},
    {"customer_id": 2, "customer_name": "Bob", "amount": 150.0, "category": "electronics"},
    {"customer_id": 1, "customer_name": "Alice", "amount": 50.0, "category": "books"},
]
```

### Tasks

1. **Filter**: Find all transactions over $100
2. **Group**: Calculate total amount spent per customer (use dict)
3. **Deduplicate**: Get unique customer IDs (use set)
4. **Count by category**: Count transactions per category (use defaultdict)
5. **Justify**: Explain why you chose each data structure

<details>
<summary><strong>Solution</strong></summary>

```python
from collections import defaultdict

transactions = [
    {"customer_id": 1, "customer_name": "Alice", "amount": 100.0, "category": "electronics"},
    {"customer_id": 2, "customer_name": "Bob", "amount": 50.0, "category": "books"},
    {"customer_id": 1, "customer_name": "Alice", "amount": 200.0, "category": "electronics"},
    {"customer_id": 3, "customer_name": "Charlie", "amount": 75.0, "category": "books"},
    {"customer_id": 2, "customer_name": "Bob", "amount": 150.0, "category": "electronics"},
    {"customer_id": 1, "customer_name": "Alice", "amount": 50.0, "category": "books"},
]

# 1. Filter: transactions over $100
high_value = [t for t in transactions if t["amount"] > 100]
print(f"High value transactions: {len(high_value)}")
for t in high_value:
    print(f"  {t['customer_name']}: ${t['amount']}")

# 2. Group: total per customer (dict)
customer_totals = {}
for t in transactions:
    customer_id = t["customer_id"]
    customer_totals[customer_id] = customer_totals.get(customer_id, 0) + t["amount"]

print(f"\nTotal per customer:")
for customer_id, total in customer_totals.items():
    print(f"  Customer {customer_id}: ${total}")

# 3. Deduplicate: unique customer IDs (set)
unique_customers = {t["customer_id"] for t in transactions}
print(f"\nUnique customers: {unique_customers}")
print(f"Count: {len(unique_customers)}")

# 4. Count by category (defaultdict)
category_counts = defaultdict(int)
for t in transactions:
    category_counts[t["category"]] += 1

print(f"\nTransactions per category:")
for category, count in category_counts.items():
    print(f"  {category}: {count}")

# 5. Justifications:
print("\n--- Justifications ---")
print("List comprehension: Simple filtering, preserves order")
print("Dict: O(1) lookup for customer totals, key-value mapping")
print("Set: O(1) membership test, automatic deduplication")
print("defaultdict: Auto-initializes counts, cleaner grouping code")
```

**Output:**
```
High value transactions: 2
  Alice: $200.0
  Bob: $150.0

Total per customer:
  Customer 1: $350.0
  Customer 2: $200.0
  Customer 3: $75.0

Unique customers: {1, 2, 3}
Count: 3

Transactions per category:
  electronics: 3
  books: 3
```

</details>

### Bonus Challenge

Calculate the average transaction amount per category using the grouped data.

---

## Exercise 3: OOP Refactoring

**Objective**: Refactor procedural code into an object-oriented design using inheritance and composition.

**Duration**: ~20 minutes

### Starting Code (Procedural)

```python
import csv
import json

def read_csv_file(filepath):
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def read_json_file(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def validate_records(records):
    valid = []
    for record in records:
        if 'id' in record and 'value' in record:
            try:
                int(record['id'])
                float(record['value'])
                valid.append(record)
            except (ValueError, KeyError):
                pass
    return valid

def process_csv(filepath):
    data = read_csv_file(filepath)
    return validate_records(data)

def process_json(filepath):
    data = read_json_file(filepath)
    return validate_records(data)
```

### Tasks

1. Create a base class `FileProcessor` with a `process()` method
2. Implement `CsvProcessor` and `JsonProcessor` subclasses
3. Move validation logic into the base class
4. Add a `__str__` method to show the processor type
5. Demonstrate polymorphism by processing different file types with the same code

<details>
<summary><strong>Solution</strong></summary>

```python
import csv
import json
from abc import ABC, abstractmethod

class FileProcessor(ABC):
    """Base class for file processors"""
    
    def __init__(self, filepath):
        self.filepath = filepath
    
    @abstractmethod
    def read(self):
        """Subclasses must implement file reading"""
        pass
    
    def validate(self, records):
        """Common validation logic"""
        valid = []
        for record in records:
            if 'id' in record and 'value' in record:
                try:
                    int(record['id'])
                    float(record['value'])
                    valid.append(record)
                except (ValueError, KeyError):
                    pass
        return valid
    
    def process(self):
        """Template method: read then validate"""
        data = self.read()
        validated = self.validate(data)
        return validated
    
    def __str__(self):
        return f"{self.__class__.__name__}('{self.filepath}')"

class CsvProcessor(FileProcessor):
    """Process CSV files"""
    
    def read(self):
        with open(self.filepath, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)

class JsonProcessor(FileProcessor):
    """Process JSON files"""
    
    def read(self):
        with open(self.filepath, 'r') as f:
            data = json.load(f)
            # Ensure it's a list
            return data if isinstance(data, list) else [data]

# Usage: polymorphism in action
def process_files(processors):
    """Process multiple files with different processors"""
    all_results = []
    for processor in processors:
        print(f"Processing with {processor}")
        results = processor.process()
        print(f"  Valid records: {len(results)}")
        all_results.extend(results)
    return all_results

# Create sample test files
with open('test_data.csv', 'w') as f:
    f.write('id,value,name\n')
    f.write('1,10.5,Alice\n')
    f.write('2,20.3,Bob\n')
    f.write('invalid,data,Charlie\n')

with open('test_data.json', 'w') as f:
    json.dump([
        {"id": "3", "value": "30.7", "name": "David"},
        {"id": "4", "value": "40.2", "name": "Eve"},
        {"id": "bad", "value": "invalid", "name": "Frank"},
    ], f)

# Polymorphic processing
processors = [
    CsvProcessor('test_data.csv'),
    JsonProcessor('test_data.json'),
]

all_data = process_files(processors)
print(f"\nTotal valid records: {len(all_data)}")

# Clean up test files
import os
os.remove('test_data.csv')
os.remove('test_data.json')
```

**Key concepts demonstrated:**
- **Inheritance**: `CsvProcessor` and `JsonProcessor` inherit from `FileProcessor`
- **Abstract methods**: `read()` must be implemented by subclasses
- **Template method pattern**: `process()` defines the algorithm in base class
- **Polymorphism**: `process_files()` works with any `FileProcessor`

</details>

### Bonus Challenge

Add a third processor type `XmlProcessor` that reads XML files. The base class should handle it without modification.

---

## Exercise 4: Type Hints and Generics

**Objective**: Take untyped code, add proper type hints including generics, and verify with mypy.

**Duration**: ~15 minutes

### Starting Code (Untyped)

```python
def fetch_items(source):
    """Fetch items from a source"""
    return source.get_items()

def filter_items(items, predicate):
    """Filter items using predicate function"""
    return [item for item in items if predicate(item)]

def transform_items(items, transformer):
    """Transform each item"""
    return [transformer(item) for item in items]

class DataSource:
    def __init__(self, data):
        self.data = data
    
    def get_items(self):
        return self.data

# Usage
source = DataSource([1, 2, 3, 4, 5])
items = fetch_items(source)
evens = filter_items(items, lambda x: x % 2 == 0)
doubled = transform_items(evens, lambda x: x * 2)
print(doubled)
```

### Tasks

1. Add type hints to all functions (use generics where appropriate)
2. Make `DataSource` generic with `TypeVar`
3. Add type hints for lambda functions (use `Callable`)
4. Add return type annotations
5. Run mypy to verify (simulate by showing how types flow through the code)

<details>
<summary><strong>Solution</strong></summary>

```python
from typing import TypeVar, Generic, Callable, List

T = TypeVar('T')
U = TypeVar('U')

class DataSource(Generic[T]):
    """Generic data source that provides items of type T"""
    
    def __init__(self, data: List[T]):
        self.data = data
    
    def get_items(self) -> List[T]:
        return self.data

def fetch_items(source: DataSource[T]) -> List[T]:
    """Fetch items from a source, preserving type"""
    return source.get_items()

def filter_items(items: List[T], predicate: Callable[[T], bool]) -> List[T]:
    """Filter items using predicate function"""
    return [item for item in items if predicate(item)]

def transform_items(items: List[T], transformer: Callable[[T], U]) -> List[U]:
    """Transform each item from type T to type U"""
    return [transformer(item) for item in items]

# Usage with full type safety
int_source: DataSource[int] = DataSource([1, 2, 3, 4, 5])

# Type checker knows each step's type
items: List[int] = fetch_items(int_source)  # List[int]
evens: List[int] = filter_items(items, lambda x: x % 2 == 0)  # List[int]
doubled: List[int] = transform_items(evens, lambda x: x * 2)  # List[int]

print(f"Doubled evens: {doubled}")  # [4, 8]

# Example with type transformation (int -> str)
str_source: DataSource[str] = DataSource(["a", "b", "c"])
letters: List[str] = fetch_items(str_source)  # List[str]
uppercase: List[str] = transform_items(letters, lambda s: s.upper())  # List[str]
letter_codes: List[int] = transform_items(uppercase, lambda s: ord(s))  # List[int]

print(f"Letter codes: {letter_codes}")  # [65, 66, 67]

# Demonstrate type safety - these would be caught by mypy:
# wrong = filter_items(items, lambda x: x.upper())  # Error: int has no upper()
# wrong2 = transform_items(items, lambda x: x + "string")  # Error: can't add str to int
```

**How to verify with mypy:**

```bash
# Save the code above to typed_pipeline.py
# Run mypy
mypy typed_pipeline.py

# If all types are correct, mypy outputs:
# Success: no issues found in 1 source file
```

**Type flow diagram:**
```
DataSource[int] → fetch_items → List[int]
                                    ↓
                            filter_items → List[int]
                                    ↓
                            transform_items → List[int]

DataSource[str] → fetch_items → List[str]
                                    ↓
                            transform_items(lambda: str.upper) → List[str]
                                    ↓
                            transform_items(lambda: ord) → List[int]
```

</details>

### Bonus Challenge

Create a generic `Pipeline` class that chains `filter_items` and `transform_items` operations:

```python
class Pipeline(Generic[T]):
    def __init__(self, source: DataSource[T]):
        self.items = source.get_items()
    
    def filter(self, predicate: Callable[[T], bool]) -> 'Pipeline[T]':
        self.items = filter_items(self.items, predicate)
        return self
    
    def map(self, transformer: Callable[[T], U]) -> 'Pipeline[U]':
        # ... implement
        pass
```

---

## Additional Practice

### Challenge 1: Composition Over Inheritance

Refactor Exercise 3 to use composition instead of inheritance. Create separate `Reader`, `Validator`, and `Processor` classes that can be composed.

### Challenge 2: Complete ETL Pipeline

Build a small ETL pipeline that:
1. Reads data from a CSV file (use `csv` module)
2. Validates records (id and value fields exist and are correct types)
3. Transforms data (e.g., convert values to uppercase)
4. Writes to JSON file (use `json` module)

Use:
- Proper OOP design (classes, composition)
- Full type hints with generics
- Dataclasses for models

### Challenge 3: Generic Repository

Implement a generic `Repository[T]` with:
- `save(entity: T) -> int` (returns ID)
- `find_by_id(id: int) -> T | None`
- `find_all() -> List[T]`
- `delete(id: int) -> bool`

Test with at least two different entity types (e.g., `User`, `Product`).

---

## Summary

These exercises covered:

1. **Project Setup**: Using uv to create projects and manage dependencies
2. **Data Structures**: Choosing the right collection for each task
3. **OOP**: Refactoring procedural code to object-oriented design
4. **Type Hints**: Adding type safety with generics

**Next Steps:**

- Explore the [demo ETL project](../demo-app/file-etl/) to see all concepts integrated
- Review lesson materials for concepts you found challenging
- Practice building small projects using these patterns

---

**Navigation:**
- **Previous**: [← Generics](../04-typing/02-generics.md)
- **Next**: [Demo ETL Project →](../demo-app/file-etl/README.md)
- **Home**: [Python Essentials](../README.md)
