---
kernelspec:
  name: python3
  language: python
  display_name: Python 3
---

# Collections

Python provides four primary collection types: `list`, `tuple`, `dict`, and `set`. Each has distinct characteristics that make it suitable for different scenarios. Understanding when to use which collection is crucial for writing efficient, readable code.

## Lists: Ordered, Mutable Collections

Lists are Python's most versatile collection type: ordered, mutable, and can contain any type of element.

```{code-cell} python
# Creating lists
empty = []
numbers = [1, 2, 3, 4, 5]
mixed = [1, "two", 3.0, True, None]  # Heterogeneous elements
nested = [[1, 2], [3, 4], [5, 6]]

print(f"Numbers: {numbers}")
print(f"Mixed types: {mixed}")
print(f"Nested: {nested}")
```

### Common List Operations

```{code-cell} python
# Adding elements
fruits = ["apple", "banana"]
fruits.append("cherry")  # Add to end: O(1)
print(f"After append: {fruits}")

fruits.insert(0, "avocado")  # Insert at position: O(n)
print(f"After insert at 0: {fruits}")

# Removing elements
fruits.remove("banana")  # Remove first occurrence: O(n)
print(f"After remove: {fruits}")

last = fruits.pop()  # Remove and return last: O(1)
print(f"Popped: {last}, Remaining: {fruits}")

# Accessing elements
print(f"First fruit: {fruits[0]}")
print(f"Last fruit: {fruits[-1]}")

# Slicing
numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
print(f"First three: {numbers[:3]}")
print(f"Last three: {numbers[-3:]}")
print(f"Every other: {numbers[::2]}")
print(f"Reversed: {numbers[::-1]}")

# Length and membership
print(f"Length: {len(fruits)}")
print(f"'apple' in fruits: {'apple' in fruits}")  # O(n)
```

### List Comprehensions

List comprehensions provide a concise way to create lists:

```{code-cell} python
# Traditional loop
squares = []
for x in range(10):
    squares.append(x ** 2)
print(f"Squares: {squares}")

# List comprehension (preferred)
squares = [x ** 2 for x in range(10)]
print(f"Squares: {squares}")

# With condition
evens = [x for x in range(20) if x % 2 == 0]
print(f"Evens: {evens}")

# Data engineering example: filtering records
records = [
    {"name": "Alice", "age": 25, "status": "active"},
    {"name": "Bob", "age": 30, "status": "inactive"},
    {"name": "Charlie", "age": 35, "status": "active"},
]

active_names = [r["name"] for r in records if r["status"] == "active"]
print(f"Active users: {active_names}")

# Nested comprehensions
matrix = [[i * j for j in range(3)] for i in range(3)]
print(f"Multiplication table:\n{matrix}")
```

### Performance Characteristics

```{code-cell} python
import time

# Append is O(1) - fast even for large lists
large_list = []
start = time.perf_counter()
for i in range(100_000):
    large_list.append(i)
elapsed = time.perf_counter() - start
print(f"Appending 100k items: {elapsed:.4f} seconds")

# Insert at beginning is O(n) - slow for large lists
small_list = []
start = time.perf_counter()
for i in range(1000):
    small_list.insert(0, i)  # Inefficient!
elapsed = time.perf_counter() - start
print(f"Inserting 1k items at beginning: {elapsed:.4f} seconds")

# Membership check is O(n) - slow for large lists
start = time.perf_counter()
result = 99_999 in large_list
elapsed = time.perf_counter() - start
print(f"Membership check in 100k list: {elapsed:.6f} seconds")
```

**At Scale: When Lists Break Down**

Lists load entirely into memory. For large datasets:

```python
# Bad: loading entire dataset into memory
# records = [process(row) for row in fetch_all_records()]  # Memory explosion!

# Good: use generators for streaming
def process_records():
    for row in fetch_all_records():
        yield process(row)

# Now you can iterate without loading everything:
# for record in process_records():
#     save_to_db(record)

# This is how pandas works internally for large datasets (chunking)
```

## Tuples: Ordered, Immutable Collections

Tuples are like lists but immutable. Once created, they cannot be modified.

```{code-cell} python
# Creating tuples
empty = ()
single = (42,)  # Note the comma - (42) is just an int!
coordinates = (10, 20)
rgb_color = (255, 128, 0)

print(f"Coordinates: {coordinates}")
print(f"RGB: {rgb_color}")

# Tuples can be heterogeneous
person = ("Alice", 25, "Engineer")
print(f"Person: {person}")

# Accessing elements (same as lists)
name = person[0]
age = person[1]
role = person[2]
print(f"{name} is a {age}-year-old {role}")
```

### Tuple Unpacking

```{code-cell} python
# Unpacking tuples
coordinates = (10, 20)
x, y = coordinates
print(f"x={x}, y={y}")

# Multiple assignment uses tuples under the hood
a, b, c = 1, 2, 3
print(f"a={a}, b={b}, c={c}")

# Swapping variables (Pythonic!)
a, b = b, a
print(f"After swap: a={a}, b={b}")

# Extended unpacking
numbers = [1, 2, 3, 4, 5]
first, *middle, last = numbers
print(f"First: {first}, Middle: {middle}, Last: {last}")

# Unpacking in loops
people = [
    ("Alice", 25),
    ("Bob", 30),
    ("Charlie", 35),
]

for name, age in people:
    print(f"{name} is {age} years old")
```

### Named Tuples

Named tuples provide attribute access while keeping tuple immutability:

```{code-cell} python
from collections import namedtuple

# Define a named tuple type
Point = namedtuple("Point", ["x", "y"])
Person = namedtuple("Person", ["name", "age", "role"])

# Create instances
p = Point(10, 20)
alice = Person("Alice", 25, "Engineer")

# Access by index (like regular tuples)
print(f"Point: ({p[0]}, {p[1]})")

# Access by name (more readable!)
print(f"Point: ({p.x}, {p.y})")
print(f"{alice.name} is a {alice.age}-year-old {alice.role}")

# Named tuples are still tuples
print(f"Is tuple? {isinstance(alice, tuple)}")

# Immutable
# alice.age = 26  # AttributeError!

# Create modified copy
alice_older = alice._replace(age=26)
print(f"Original: {alice.age}, Modified: {alice_older.age}")
```

**When to use tuples instead of lists:**

```{code-cell} python
# 1. Function return values (multiple values)
def get_user_info():
    return ("Alice", 25, "Engineer")

name, age, role = get_user_info()

# 2. Dictionary keys (tuples are hashable, lists aren't)
locations = {
    (0, 0): "origin",
    (1, 0): "right",
    (0, 1): "up",
}
print(f"Location at (1,0): {locations[(1, 0)]}")

# 3. Immutable data (coordinates, RGB colors, database rows)
coordinates = (40.7128, -74.0060)  # NYC lat/long
# coordinates[0] = 40.0  # TypeError!

# 4. Slightly faster than lists
import sys
print(f"List size: {sys.getsizeof([1, 2, 3])} bytes")
print(f"Tuple size: {sys.getsizeof((1, 2, 3))} bytes")
```

## Dictionaries: Key-Value Pairs

Dictionaries map keys to values with O(1) average lookup time. As of Python 3.7+, they preserve insertion order.

```{code-cell} python
# Creating dictionaries
empty = {}
user = {"name": "Alice", "age": 25, "role": "Engineer"}
print(f"User: {user}")

# Alternative: dict() constructor
user2 = dict(name="Bob", age=30, role="Analyst")
print(f"User2: {user2}")

# Accessing values
print(f"Name: {user['name']}")
print(f"Age: {user['age']}")

# KeyError if key doesn't exist
# print(user["salary"])  # KeyError!

# Use .get() for safe access
salary = user.get("salary")
print(f"Salary: {salary}")  # None

# Provide default value
salary = user.get("salary", 0)
print(f"Salary with default: {salary}")  # 0
```

### Common Dictionary Operations

```{code-cell} python
# Adding/updating entries
config = {"host": "localhost", "port": 5432}
config["database"] = "mydb"  # Add new key
config["port"] = 5433  # Update existing key
print(f"Config: {config}")

# Removing entries
del config["database"]  # Remove key
print(f"After del: {config}")

port = config.pop("port")  # Remove and return value
print(f"Popped port: {port}, Remaining: {config}")

# Iterating
user = {"name": "Alice", "age": 25, "role": "Engineer"}

# Keys
for key in user:  # or user.keys()
    print(f"Key: {key}")

# Values
for value in user.values():
    print(f"Value: {value}")

# Key-value pairs
for key, value in user.items():
    print(f"{key}: {value}")

# Merging dictionaries (Python 3.9+)
defaults = {"timeout": 30, "retries": 3}
custom = {"timeout": 60}
merged = defaults | custom  # custom overrides defaults
print(f"Merged: {merged}")

# Alternative (works in older Python)
merged = {**defaults, **custom}
print(f"Merged (old syntax): {merged}")
```

### Dictionary Comprehensions

```{code-cell} python
# Create dict from lists
keys = ["name", "age", "role"]
values = ["Alice", 25, "Engineer"]
user = {k: v for k, v in zip(keys, values)}
print(f"User: {user}")

# Transform existing dict
prices = {"apple": 1.0, "banana": 0.5, "cherry": 2.0}
prices_usd_to_eur = {fruit: price * 0.85 for fruit, price in prices.items()}
print(f"Prices in EUR: {prices_usd_to_eur}")

# Filter dict
expensive = {fruit: price for fruit, price in prices.items() if price > 1.0}
print(f"Expensive fruits: {expensive}")

# Data engineering: grouping records
records = [
    {"city": "NYC", "temp": 70},
    {"city": "LA", "temp": 80},
    {"city": "NYC", "temp": 72},
    {"city": "LA", "temp": 85},
]

# Group by city (using dict of lists)
by_city = {}
for record in records:
    city = record["city"]
    if city not in by_city:
        by_city[city] = []
    by_city[city].append(record["temp"])

print(f"Temps by city: {by_city}")
```

### defaultdict for Cleaner Grouping

```{code-cell} python
from collections import defaultdict

# Same grouping, cleaner code
records = [
    {"city": "NYC", "temp": 70},
    {"city": "LA", "temp": 80},
    {"city": "NYC", "temp": 72},
    {"city": "LA", "temp": 85},
]

by_city = defaultdict(list)  # Automatically creates empty list for new keys
for record in records:
    by_city[record["city"]].append(record["temp"])

print(f"Temps by city: {dict(by_city)}")

# Other useful defaults
counter = defaultdict(int)  # Auto-initialize to 0
counter["apple"] += 1
counter["banana"] += 1
counter["apple"] += 1
print(f"Counts: {dict(counter)}")
```

**Advanced Note: Hash Tables Under the Hood**

Dictionaries use hash tables for O(1) lookup:

```{code-cell} python
# Keys must be hashable
key = "name"
print(f"Hash of '{key}': {hash(key)}")

# Immutable types are hashable
print(f"Hash of 42: {hash(42)}")
print(f"Hash of (1,2): {hash((1, 2))}")

# Mutable types are NOT hashable
# print(hash([1, 2]))  # TypeError: unhashable type: 'list'
# print(hash({"a": 1}))  # TypeError: unhashable type: 'dict'

# This is why lists can't be dict keys:
# locations = {[0, 0]: "origin"}  # TypeError!

# Use tuples instead:
locations = {(0, 0): "origin"}
print(f"Locations: {locations}")

# Hash collisions: different keys with same hash (rare but possible)
# Python handles this internally with chaining/open addressing
```

**Real-world use cases:**

```{code-cell} python
# 1. Configuration objects
config = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "mydb",
    },
    "cache": {
        "enabled": True,
        "ttl": 3600,
    },
}

# 2. API responses
api_response = {
    "status": "success",
    "data": [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ],
    "meta": {
        "total": 2,
        "page": 1,
    },
}

# 3. Caching
cache = {}

def expensive_computation(x):
    if x in cache:
        return cache[x]
    result = x ** 2  # Simulate expensive operation
    cache[x] = result
    return result

print(f"First call: {expensive_computation(10)}")
print(f"Cached call: {expensive_computation(10)}")
print(f"Cache: {cache}")
```

## Sets: Unordered, Unique Elements

Sets store unique elements with O(1) membership testing.

```{code-cell} python
# Creating sets
empty = set()  # Note: {} creates an empty dict, not set!
numbers = {1, 2, 3, 4, 5}
duplicates = {1, 2, 2, 3, 3, 3}  # Duplicates removed automatically
print(f"Numbers: {numbers}")
print(f"Duplicates removed: {duplicates}")

# From list (deduplication)
items = [1, 2, 2, 3, 3, 3, 4, 4, 4, 4]
unique = set(items)
print(f"Unique items: {unique}")
```

### Set Operations

```{code-cell} python
# Mathematical set operations
a = {1, 2, 3, 4, 5}
b = {4, 5, 6, 7, 8}

# Union: all elements from both sets
print(f"Union: {a | b}")
print(f"Union: {a.union(b)}")

# Intersection: elements in both sets
print(f"Intersection: {a & b}")
print(f"Intersection: {a.intersection(b)}")

# Difference: elements in a but not in b
print(f"Difference: {a - b}")
print(f"Difference: {a.difference(b)}")

# Symmetric difference: elements in either set but not both
print(f"Symmetric diff: {a ^ b}")
print(f"Symmetric diff: {a.symmetric_difference(b)}")

# Subset/superset
x = {1, 2}
y = {1, 2, 3, 4}
print(f"{x} is subset of {y}: {x.issubset(y)}")
print(f"{y} is superset of {x}: {y.issuperset(x)}")
```

### When to Use Sets

```{code-cell} python
# 1. Deduplication
user_ids = [1, 2, 3, 2, 1, 4, 3, 5]
unique_ids = list(set(user_ids))
print(f"Unique user IDs: {unique_ids}")

# 2. Membership testing (O(1) vs list's O(n))
valid_statuses = {"active", "pending", "suspended"}
user_status = "active"

if user_status in valid_statuses:  # O(1) lookup
    print(f"Status '{user_status}' is valid")

# Compare to list lookup (O(n))
valid_statuses_list = ["active", "pending", "suspended"]
if user_status in valid_statuses_list:  # O(n) lookup
    print("Valid (but slower for large lists)")

# 3. Finding differences between datasets
old_users = {"alice", "bob", "charlie"}
new_users = {"bob", "charlie", "david", "eve"}

added = new_users - old_users
removed = old_users - new_users
unchanged = old_users & new_users

print(f"Added: {added}")
print(f"Removed: {removed}")
print(f"Unchanged: {unchanged}")

# 4. Data engineering: finding unique values in column
records = [
    {"city": "NYC", "country": "USA"},
    {"city": "LA", "country": "USA"},
    {"city": "London", "country": "UK"},
    {"city": "Paris", "country": "France"},
    {"city": "NYC", "country": "USA"},
]

unique_cities = {r["city"] for r in records}  # Set comprehension
print(f"Unique cities: {unique_cities}")
```

### frozenset: Immutable Sets

```{code-cell} python
# frozenset is to set what tuple is to list
immutable = frozenset([1, 2, 3])
print(f"Frozenset: {immutable}")

# Can be used as dict keys (hashable)
set_dict = {
    frozenset([1, 2]): "pair",
    frozenset([1, 2, 3]): "triple",
}
print(f"Set dict: {set_dict}")

# Regular sets can't be dict keys
# regular = {1, 2}
# set_dict[regular] = "pair"  # TypeError!
```

## Collection Comparison

| Collection | Ordered | Mutable | Duplicates | Lookup Time | Use Case |
|------------|---------|---------|------------|-------------|----------|
| **list** | Yes | Yes | Yes | O(n) | General sequences, ordered data |
| **tuple** | Yes | No | Yes | O(n) | Immutable sequences, dict keys, function returns |
| **dict** | Yes (3.7+) | Yes | Keys unique | O(1) | Key-value mappings, caching, config |
| **set** | No | Yes | No | O(1) | Uniqueness, membership testing, set operations |

### Choosing the Right Collection

```{code-cell} python
# Use list when:
# - You need ordering
# - Elements can be duplicates
# - You'll modify the collection frequently
tasks = ["task1", "task2", "task3"]
tasks.append("task4")

# Use tuple when:
# - Data shouldn't change
# - You need hashable collection (dict key)
# - Returning multiple values from function
def get_coordinates():
    return (10, 20)

# Use dict when:
# - You need key-value mapping
# - Fast lookup by key is important
# - Representing structured data
user = {"name": "Alice", "age": 25}

# Use set when:
# - Uniqueness matters
# - Fast membership testing needed
# - Set operations (union, intersection)
valid_codes = {"200", "201", "204"}
```

## At Scale: Memory and Performance

```{code-cell} python
import sys

# Memory usage comparison
list_data = [i for i in range(1000)]
tuple_data = tuple(list_data)
set_data = set(list_data)
dict_data = {i: i for i in range(1000)}

print(f"List:  {sys.getsizeof(list_data):,} bytes")
print(f"Tuple: {sys.getsizeof(tuple_data):,} bytes")
print(f"Set:   {sys.getsizeof(set_data):,} bytes")
print(f"Dict:  {sys.getsizeof(dict_data):,} bytes")

# Performance: membership testing
import time

data = list(range(100_000))
data_set = set(data)

# List lookup (O(n))
start = time.perf_counter()
result = 99_999 in data
list_time = time.perf_counter() - start

# Set lookup (O(1))
start = time.perf_counter()
result = 99_999 in data_set
set_time = time.perf_counter() - start

print(f"\nMembership test for 99,999:")
print(f"List: {list_time:.6f}s")
print(f"Set:  {set_time:.6f}s")
print(f"Speedup: {list_time / set_time:.1f}x")
```

## Summary

**Key Takeaways:**

- **Lists** are your default choice for ordered, mutable sequences
- **Tuples** for immutable data and function return values
- **Dicts** for key-value mappings with O(1) lookup
- **Sets** for uniqueness and fast membership testing

**Performance Rules:**

- Use sets for membership testing over large collections
- Use dicts for key-based lookups
- Use generators instead of lists for large datasets
- Lists: append is O(1), insert at beginning is O(n)

**Choosing wisely:**

- Need ordering? → list or tuple
- Need key-value mapping? → dict
- Need uniqueness? → set
- Is data immutable? → tuple or frozenset

---

**Navigation:**
- **Previous**: [← Primitive Types](01-primitive-types.md)
- **Next**: [Object-Oriented Python →](../03-oop/01-object-oriented-python.md)
- **Home**: [Python Essentials](../README.md)
