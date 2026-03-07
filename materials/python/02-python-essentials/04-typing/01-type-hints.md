---
kernelspec:
  name: python3
  language: python
  display_name: Python 3
---

# Type Hints

Type hints are optional annotations that specify what types variables, function parameters, and return values should have. While Python remains dynamically typed, type hints provide documentation, IDE support, and early bug detection through static analysis.

## Why Typing Matters

Consider these two functions:

```{code-cell} python
# Without type hints
def process_records(data, config):
    result = []
    for item in data:
        if item.get(config["key"]) > config["threshold"]:
            result.append(item)
    return result

# With type hints
def process_records(data: list[dict], config: dict[str, int]) -> list[dict]:
    result = []
    for item in data:
        if item.get(config["key"]) > config["threshold"]:
            result.append(item)
    return result
```

**Without hints**: You must read the implementation or documentation to understand what arguments are expected.

**With hints**: The function signature tells you:
- `data` is a list of dictionaries
- `config` is a dict with string keys and int values
- Returns a list of dictionaries

**Benefits for teams:**

1. **Documentation**: Types are verified documentation (can't drift from code)
2. **IDE support**: Autocomplete, refactoring, navigation all work better
3. **Early bug detection**: Catch type errors before running code
4. **Onboarding**: New team members understand code faster

```{code-cell} python
# Demonstrating IDE benefits
def get_user(user_id: int) -> dict[str, str]:
    """Fetch user by ID"""
    return {"id": str(user_id), "name": "Alice", "email": "alice@example.com"}

# IDE knows the return type is dict[str, str]
user = get_user(1)
# Autocomplete will suggest: user["name"], user["email"], etc.
name = user["name"]  # IDE knows this is a string
```

## Basic Type Hints

### Primitive Types

```{code-cell} python
# Variables (optional, but helps clarity)
age: int = 25
price: float = 19.99
is_active: bool = True
name: str = "Alice"

# Function parameters and return types
def greet(name: str) -> str:
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    return a + b

def calculate_discount(price: float, discount: float) -> float:
    return price * (1 - discount)

# Test the functions
print(greet("Alice"))
print(add(5, 3))
print(calculate_discount(100.0, 0.2))
```

### None and Optional Values

```{code-cell} python
# Function that might return None
def find_user(user_id: int) -> dict | None:
    """Returns user dict or None if not found"""
    if user_id == 1:
        return {"id": 1, "name": "Alice"}
    return None

# Usage
user = find_user(1)
if user is not None:
    print(f"Found: {user['name']}")
else:
    print("User not found")

# Type checkers know user might be None
# This would be flagged by mypy:
# print(user["name"])  # Error: user could be None

# Multiple returns example
def fetch_config(env: str) -> dict[str, str] | None:
    """Returns config for environment or None"""
    configs = {
        "dev": {"host": "localhost", "port": "8000"},
        "prod": {"host": "api.example.com", "port": "443"}
    }
    return configs.get(env)

config = fetch_config("dev")
if config:
    print(f"Host: {config['host']}")
```

## Collection Types

### Lists, Dicts, Sets, Tuples

```{code-cell} python
# Lists of specific types
numbers: list[int] = [1, 2, 3, 4, 5]
names: list[str] = ["Alice", "Bob", "Charlie"]

# Dictionaries
user: dict[str, str] = {"name": "Alice", "email": "alice@example.com"}
scores: dict[str, int] = {"Alice": 95, "Bob": 87}
config: dict[str, int] = {"timeout": 30, "retries": 3}

# Sets
unique_ids: set[int] = {1, 2, 3}
tags: set[str] = {"python", "data", "engineering"}

# Tuples (fixed length)
point: tuple[int, int] = (10, 20)
person: tuple[str, int, str] = ("Alice", 25, "Engineer")

# Variable length tuples
numbers: tuple[int, ...] = (1, 2, 3, 4, 5)  # Any number of ints
```

### Nested Collections

```{code-cell} python
# List of dictionaries (common in data engineering)
records: list[dict[str, str]] = [
    {"name": "Alice", "city": "NYC"},
    {"name": "Bob", "city": "LA"},
]

# Dictionary of lists
groups: dict[str, list[str]] = {
    "admins": ["alice", "bob"],
    "users": ["charlie", "david"],
}

# Complex nesting
api_response: dict[str, list[dict[str, int]]] = {
    "results": [
        {"id": 1, "score": 95},
        {"id": 2, "score": 87},
    ]
}

# More examples
users_by_city: dict[str, list[dict[str, str | int]]] = {
    "NYC": [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
    ],
    "LA": [
        {"name": "Charlie", "age": 35},
    ]
}
```

## Union Types

Sometimes a value can be one of several types:

```{code-cell} python
# Union types with | operator
def process_id(user_id: int | str) -> str:
    """Accept int or str ID, return str"""
    return str(user_id)

# Usage
print(process_id(123))
print(process_id("user_456"))

# Practical example: function that accepts different config types
def load_config(source: str | dict) -> dict:
    """Load config from filepath (str) or dict"""
    if isinstance(source, str):
        # Load from file
        return {"loaded": "from file", "path": source}
    else:
        # Already a dict
        return source

config1 = load_config("config.json")
config2 = load_config({"key": "value"})
print(config1)
print(config2)

# Multiple types
def format_value(value: int | float | str) -> str:
    """Format different types as strings"""
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return value

print(format_value(10))
print(format_value(10.5))
print(format_value("text"))
```

## Type Checking with mypy

Type hints are checked by **static type checkers** like `mypy`. They analyze your code without running it.

### Installing and Running mypy

```{code-cell} python
# Installation (would be done via command line)
# pip install mypy

# Example file: example.py
def add(a: int, b: int) -> int:
    return a + b

def greet(name: str) -> str:
    return f"Hello, {name}!"

# Correct usage
result = add(5, 3)
message = greet("Alice")

# Type errors (mypy will catch these)
# wrong = add("5", "3")  # Error: Expected int, got str
# wrong_message = greet(123)  # Error: Expected str, got int
```

Run mypy from command line:

**Run this in your terminal:**

```bash
mypy example.py
# If there are errors:
# example.py:10: error: Argument 1 to "add" has incompatible type "str"; expected "int"
# example.py:11: error: Argument 1 to "greet" has incompatible type "int"; expected "str"
```

### Configuring mypy

Create `pyproject.toml`:

**Run this in the Jupyter notebook:**

```{code-cell} python
# Example mypy configuration (as Python string for Jupytext)
mypy_config = """
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
check_untyped_defs = true

# Per-module options
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
"""

print("mypy configuration for pyproject.toml:")
print(mypy_config)
```

**Common mypy flags:**

- `--strict`: Enable all optional checks (recommended for new projects)
- `--ignore-missing-imports`: Ignore imports without type stubs
- `--disallow-untyped-defs`: Require type hints on all functions

```{code-cell} python
# Demonstrating type errors mypy catches
def calculate_total(items: list[dict[str, int]]) -> int:
    total = 0
    for item in items:
        total += item["price"]
    return total

# This would pass runtime but mypy catches the error:
# items = [{"price": "10"}, {"price": "20"}]  # Strings, not ints!
# calculate_total(items)  # mypy: Argument 1 has incompatible type

# Correct version:
items = [{"price": 10}, {"price": 20}]
total = calculate_total(items)
print(f"Total: {total}")
```

## Practical Examples

### Type Hints for Data Engineering

```{code-cell} python
from dataclasses import dataclass

@dataclass
class DataRecord:
    id: int
    name: str
    value: float
    tags: list[str]

def load_records(filepath: str) -> list[DataRecord]:
    """Load records from file"""
    # Simulate loading
    return [
        DataRecord(1, "Record 1", 10.5, ["tag1", "tag2"]),
        DataRecord(2, "Record 2", 20.3, ["tag3"]),
    ]

def filter_records(
    records: list[DataRecord],
    min_value: float,
    required_tag: str | None = None
) -> list[DataRecord]:
    """Filter records by value and optional tag"""
    result = []
    for record in records:
        if record.value >= min_value:
            if required_tag is None or required_tag in record.tags:
                result.append(record)
    return result

def aggregate_by_tag(records: list[DataRecord]) -> dict[str, float]:
    """Sum values grouped by tag"""
    totals: dict[str, float] = {}
    for record in records:
        for tag in record.tags:
            totals[tag] = totals.get(tag, 0.0) + record.value
    return totals

# Usage with full type safety
records = load_records("data.csv")
filtered = filter_records(records, min_value=15.0, required_tag="tag3")
aggregated = aggregate_by_tag(records)

print(f"Loaded {len(records)} records")
print(f"Filtered: {len(filtered)} records")
print(f"Aggregated: {aggregated}")
```

### Type Hints for APIs

```{code-cell} python
from dataclasses import dataclass

@dataclass
class ApiResponse:
    status: str
    data: list[dict[str, str]]
    error: str | None = None

def fetch_users(api_url: str, limit: int = 10) -> ApiResponse:
    """Fetch users from API"""
    # Simulate API call
    return ApiResponse(
        status="success",
        data=[
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": "Bob"},
        ][:limit],
        error=None
    )

def parse_response(response: ApiResponse) -> list[dict[str, str]]:
    """Extract data from API response"""
    if response.status != "success":
        raise ValueError(f"API error: {response.error}")
    return response.data

# Usage
response = fetch_users("https://api.example.com/users", limit=5)
users = parse_response(response)
print(f"Fetched {len(users)} users")
```

## Advanced: TYPE_CHECKING

Sometimes you need types only for type checking, not at runtime. Use `TYPE_CHECKING`:

```{code-cell} python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # These imports only happen during type checking, not at runtime
    # Useful for avoiding circular imports
    from expensive_module import ExpensiveClass

def process_data(data: "ExpensiveClass") -> str:
    """Process data using forward reference"""
    # ExpensiveClass is only imported during type checking
    return f"Processed: {data}"

# Alternative: use string annotations (Python 3.7+)
def process_data_alt(data: "list[dict]") -> str:
    """String annotations are evaluated lazily"""
    return f"Processed {len(data)} items"
```

**Why this matters**: Avoids circular import issues in large codebases where modules depend on each other.

## Common Patterns

### Callable Types

```{code-cell} python
from typing import Callable

# Function that takes a function as argument
def apply_operation(
    numbers: list[int],
    operation: Callable[[int], int]
) -> list[int]:
    """Apply operation to each number"""
    return [operation(n) for n in numbers]

# Usage
def square(x: int) -> int:
    return x * x

def double(x: int) -> int:
    return x * 2

numbers = [1, 2, 3, 4, 5]
squared = apply_operation(numbers, square)
doubled = apply_operation(numbers, double)

print(f"Squared: {squared}")
print(f"Doubled: {doubled}")

# Callable with multiple arguments
def apply_reducer(
    numbers: list[int],
    reducer: Callable[[int, int], int],
    initial: int
) -> int:
    """Apply reducer function (like reduce())"""
    result = initial
    for n in numbers:
        result = reducer(result, n)
    return result

def add(a: int, b: int) -> int:
    return a + b

total = apply_reducer([1, 2, 3, 4, 5], add, 0)
print(f"Total: {total}")
```

### Any and TypeVar (Preview)

```{code-cell} python
from typing import Any

# Any: opt-out of type checking (use sparingly)
def process_anything(data: Any) -> Any:
    """Accepts anything, returns anything"""
    return data

# This passes type checking but isn't safe
result = process_anything("string")
# result + 10  # Runtime error, but mypy doesn't catch it

# Better: use specific types or generics (covered in next lesson)
```

## Summary

| Concept | Syntax | Use Case |
|---------|--------|----------|
| **Basic types** | `int`, `str`, `float`, `bool` | Function parameters, return types |
| **Collections** | `list[int]`, `dict[str, int]` | Typed containers |
| **Optional** | `int \| None` | Values that might be None |
| **Union** | `int \| str` | Multiple possible types |
| **Any** | `Any` | Opt-out of type checking (use rarely) |

**Best Practices:**

1. **Start with function signatures**: Type parameters and return values first
2. **Use built-in syntax**: `list[int]`, `dict[str, int]`, `int | None` (Python 3.9+)
3. **Run mypy regularly**: Integrate into CI/CD pipeline
4. **Don't use `Any`** unless absolutely necessary
5. **Type public APIs**: Internal functions can be less strict

**In Large Projects:**

- Types are **documentation that's verified**
- IDE navigation and refactoring become reliable
- Catch bugs before runtime (especially in data pipelines)
- Onboarding new developers is faster

**Next lesson**: Generics allow you to write type-safe code that works with multiple types while maintaining type checking.

---

**Navigation:**
- **Previous**: [← Composition Over Inheritance](../03-oop/03-composition-over-inheritance.md)
- **Next**: [Generics →](02-generics.md)
- **Home**: [Python Essentials](../README.md)
