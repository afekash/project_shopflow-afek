---
kernelspec:
  name: python3
  language: python
  display_name: Python 3
---

# Generics

Generics allow you to write functions and classes that work with multiple types while maintaining type safety. Instead of using `Any` (which disables type checking), generics let you say "this works with any type, but maintains consistency."

## The Problem Generics Solve

Without generics, you have two bad options:

```python
# Option 1: Specific types (not reusable)
def first_int(items: list[int]) -> int:
    return items[0]

def first_str(items: list[str]) -> str:
    return items[0]

# Need a separate function for each type!

# Option 2: Any (loses type safety)
from typing import Any

def first(items: list[Any]) -> Any:
    return items[0]

# Type checker doesn't know what type is returned
result = first([1, 2, 3])
# result + "string"  # Type checker won't catch this error!
```

**Generics provide a third option: reusable + type-safe**

```{code-cell} python
from typing import TypeVar

T = TypeVar('T')

def first(items: list[T]) -> T:
    """Return first item, preserving its type"""
    return items[0]

# Type checker knows the return type based on input
numbers = [1, 2, 3]
num = first(numbers)  # Type checker knows num is int
# num + "string"  # Error: can't add str to int

strings = ["a", "b", "c"]
text = first(strings)  # Type checker knows text is str
# text + 10  # Error: can't add int to str
```

## TypeVar: Generic Functions

`TypeVar` creates a type variable that represents "some type":

```{code-cell} python
from typing import TypeVar

T = TypeVar('T')

def reverse(items: list[T]) -> list[T]:
    """Reverse a list, preserving element type"""
    return items[::-1]

# Works with any type
numbers = reverse([1, 2, 3])  # list[int]
words = reverse(["a", "b", "c"])  # list[str]

print(f"Reversed numbers: {numbers}")
print(f"Reversed words: {words}")

# More complex: function with two type variables
T = TypeVar('T')
U = TypeVar('U')

def pair(first: T, second: U) -> tuple[T, U]:
    """Create a tuple from two values of potentially different types"""
    return (first, second)

p1 = pair(1, "one")  # tuple[int, str]
p2 = pair("hello", 42)  # tuple[str, int]

print(f"Pair 1: {p1}")
print(f"Pair 2: {p2}")
```

### Bounded TypeVars

Constrain what types a TypeVar can be:

```{code-cell} python
from typing import TypeVar

# Only numeric types
Number = TypeVar('Number', int, float)

def add(a: Number, b: Number) -> Number:
    """Add two numbers (int or float)"""
    return a + b

# Works
result1 = add(5, 3)  # int + int = int
result2 = add(5.5, 3.2)  # float + float = float

print(f"5 + 3 = {result1}")
print(f"5.5 + 3.2 = {result2}")

# Type checker would flag:
# add("hello", "world")  # Error: str not in (int, float)

# Upper bound: must be subclass of specified type
from typing import TypeVar

T = TypeVar('T', bound='Comparable')

class Comparable:
    def __lt__(self, other):
        raise NotImplementedError

def max_item(items: list[T]) -> T:
    """Find maximum item (requires comparison)"""
    return max(items)

# Works with any comparable type
print(max_item([1, 5, 3, 2]))
print(max_item(["apple", "zebra", "banana"]))
```

## Generic Classes

Classes can also be generic:

```{code-cell} python
from typing import Generic, TypeVar

T = TypeVar('T')

class Box(Generic[T]):
    """A container that holds a value of type T"""
    
    def __init__(self, value: T):
        self._value = value
    
    def get(self) -> T:
        return self._value
    
    def set(self, value: T):
        self._value = value

# Create boxes with different types
int_box = Box(42)
str_box = Box("hello")

# Type checker knows the types
num = int_box.get()  # int
text = str_box.get()  # str

print(f"Int box: {num}")
print(f"Str box: {text}")

# Type checker catches errors
# int_box.set("wrong type")  # Error: expected int, got str
```

### Practical Example: Generic Repository

```{code-cell} python
from typing import Generic, TypeVar, Optional, List
from dataclasses import dataclass

T = TypeVar('T')

class Repository(Generic[T]):
    """Generic repository for any entity type"""
    
    def __init__(self):
        self._storage: dict[int, T] = {}
        self._next_id = 1
    
    def save(self, entity: T) -> int:
        """Save entity and return its ID"""
        entity_id = self._next_id
        self._storage[entity_id] = entity
        self._next_id += 1
        return entity_id
    
    def find_by_id(self, entity_id: int) -> Optional[T]:
        """Find entity by ID"""
        return self._storage.get(entity_id)
    
    def find_all(self) -> List[T]:
        """Get all entities"""
        return list(self._storage.values())
    
    def delete(self, entity_id: int):
        """Delete entity by ID"""
        if entity_id in self._storage:
            del self._storage[entity_id]

# Define entity types
@dataclass
class User:
    name: str
    email: str

@dataclass
class Product:
    name: str
    price: float

# Create typed repositories
user_repo = Repository[User]()
product_repo = Repository[Product]()

# Save entities
user_id = user_repo.save(User("Alice", "alice@example.com"))
product_id = product_repo.save(Product("Laptop", 999.99))

# Type checker knows the return types
user = user_repo.find_by_id(user_id)  # Optional[User]
product = product_repo.find_by_id(product_id)  # Optional[Product]

if user:
    print(f"User: {user.name}, {user.email}")

if product:
    print(f"Product: {product.name}, ${product.price}")

# Type checker catches errors
# user_repo.save(Product("Wrong", 10.0))  # Error: expected User, got Product
```

## Generic Protocols

Combine Protocols (from the interfaces lesson) with generics:

```{code-cell} python
from typing import Protocol, TypeVar, List

T = TypeVar('T')

class Comparable(Protocol):
    """Protocol for objects that can be compared"""
    def __lt__(self, other) -> bool:
        ...

def sort_items(items: List[T]) -> List[T]:
    """Sort any list of comparable items"""
    return sorted(items)

# Works with any comparable type
numbers = sort_items([3, 1, 4, 1, 5])
words = sort_items(["zebra", "apple", "banana"])

print(f"Sorted numbers: {numbers}")
print(f"Sorted words: {words}")

# Generic protocol example
T = TypeVar('T')

class DataSource(Protocol[T]):
    """Protocol for data sources that produce items of type T"""
    def fetch(self) -> List[T]:
        ...

class CsvDataSource:
    def fetch(self) -> List[dict]:
        return [{"id": 1, "name": "Alice"}]

class IntDataSource:
    def fetch(self) -> List[int]:
        return [1, 2, 3, 4, 5]

def process_source(source: DataSource[T]) -> List[T]:
    """Process any data source, preserving item type"""
    return source.fetch()

# Type checker knows the return types
csv_data = process_source(CsvDataSource())  # List[dict]
int_data = process_source(IntDataSource())  # List[int]

print(f"CSV data: {csv_data}")
print(f"Int data: {int_data}")
```

## Practical Example: Generic Pipeline

```{code-cell} python
from typing import Generic, TypeVar, Callable, List

InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')

class Pipeline(Generic[InputT, OutputT]):
    """Generic data pipeline that transforms InputT to OutputT"""
    
    def __init__(self, transformer: Callable[[InputT], OutputT]):
        self.transformer = transformer
    
    def process(self, items: List[InputT]) -> List[OutputT]:
        """Transform each input item to output type"""
        return [self.transformer(item) for item in items]
    
    def process_one(self, item: InputT) -> OutputT:
        """Transform a single item"""
        return self.transformer(item)

# Example: int -> str pipeline
def int_to_str(n: int) -> str:
    return f"Number: {n}"

int_str_pipeline = Pipeline[int, str](int_to_str)
result = int_str_pipeline.process([1, 2, 3])
print(f"Pipeline result: {result}")  # ["Number: 1", "Number: 2", "Number: 3"]

# Example: dict -> float pipeline (extract value)
def extract_price(record: dict) -> float:
    return record["price"]

dict_float_pipeline = Pipeline[dict, float](extract_price)
records = [{"price": 10.5}, {"price": 20.3}, {"price": 15.7}]
prices = dict_float_pipeline.process(records)
print(f"Extracted prices: {prices}")  # [10.5, 20.3, 15.7]

# Chain pipelines
def double(n: float) -> float:
    return n * 2

double_pipeline = Pipeline[float, float](double)

# Extract prices then double them
extracted = dict_float_pipeline.process(records)
doubled = double_pipeline.process(extracted)
print(f"Doubled prices: {doubled}")  # [21.0, 40.6, 31.4]
```

## Generic with Multiple Type Parameters

```{code-cell} python
from typing import Generic, TypeVar

K = TypeVar('K')
V = TypeVar('V')

class Cache(Generic[K, V]):
    """Generic cache with key type K and value type V"""
    
    def __init__(self):
        self._data: dict[K, V] = {}
    
    def get(self, key: K) -> V | None:
        return self._data.get(key)
    
    def set(self, key: K, value: V):
        self._data[key] = value
    
    def has(self, key: K) -> bool:
        return key in self._data

# String keys, int values
int_cache = Cache[str, int]()
int_cache.set("count", 42)
count = int_cache.get("count")
print(f"Count: {count}")

# Int keys, list values
list_cache = Cache[int, list[str]]()
list_cache.set(1, ["a", "b", "c"])
items = list_cache.get(1)
print(f"Items: {items}")

# Type checker catches errors
# int_cache.set("key", "wrong")  # Error: expected int, got str
# int_cache.set(123, 456)  # Error: expected str key, got int
```

## Advanced: Variance (Covariance and Contravariance)

**Advanced Note**: Generics have variance rules that affect subtyping. This is advanced, but important for library authors.

```{code-cell} python
from typing import TypeVar, Generic

# Covariant: preserves subtyping (output positions)
T_co = TypeVar('T_co', covariant=True)

class Producer(Generic[T_co]):
    """Produces items of type T_co"""
    def produce(self) -> T_co:
        ...

# Contravariant: reverses subtyping (input positions)
T_contra = TypeVar('T_contra', contravariant=True)

class Consumer(Generic[T_contra]):
    """Consumes items of type T_contra"""
    def consume(self, item: T_contra):
        ...

# For most cases, use invariant TypeVars (the default)
# Variance matters when working with inheritance and generics
```

**In practice**, most code uses invariant TypeVars. Covariance/contravariance matter when:
- Writing libraries that need precise subtyping rules
- Working with immutable containers (covariant)
- Working with callbacks/functions (contravariant in arguments)

## At Scale: Benefits in Large Codebases

Generics shine in large projects:

```{code-cell} python
from typing import Generic, TypeVar, Protocol
from dataclasses import dataclass

# Define a generic data model
T = TypeVar('T')

@dataclass
class ApiResponse(Generic[T]):
    """Generic API response wrapper"""
    status: int
    data: T | None
    error: str | None

# Strongly typed API clients
class UserClient:
    def get_user(self, user_id: int) -> ApiResponse[dict]:
        # IDE knows this returns ApiResponse[dict]
        return ApiResponse(200, {"id": user_id, "name": "Alice"}, None)

class OrderClient:
    def get_orders(self) -> ApiResponse[list[dict]]:
        # IDE knows this returns ApiResponse[list[dict]]
        return ApiResponse(200, [{"id": 1, "total": 100.0}], None)

# Generic response handler
def handle_response(response: ApiResponse[T]) -> T:
    """Extract data from response or raise error"""
    if response.status != 200 or response.data is None:
        raise ValueError(f"API error: {response.error}")
    return response.data

# Type checker tracks types through the chain
user_client = UserClient()
order_client = OrderClient()

user_data = handle_response(user_client.get_user(1))  # dict
orders = handle_response(order_client.get_orders())  # list[dict]

# IDE knows user_data is dict, orders is list[dict]
print(f"User: {user_data['name']}")
print(f"Orders: {len(orders)}")
```

**Benefits at scale:**

1. **Refactoring safety**: Change types in one place, type checker finds all affected code
2. **IDE navigation**: Jump to definition works across generic boundaries
3. **Documentation**: Generic types communicate intent clearly
4. **Onboarding**: New developers understand complex code faster with types

## Summary

| Concept | Purpose | Example |
|---------|---------|---------|
| **TypeVar** | Create type variables | `T = TypeVar('T')` |
| **Generic function** | Function that works with any type | `def first(items: list[T]) -> T` |
| **Generic class** | Class parameterized by type | `class Box(Generic[T])` |
| **Generic Protocol** | Protocol with type parameter | `class DataSource(Protocol[T])` |
| **Multiple parameters** | Multiple type variables | `class Cache(Generic[K, V])` |

**Key Takeaways:**

- **Generics** enable reusable, type-safe code
- **TypeVar** represents "some type" that's consistent within a function/class
- **Generic classes** can hold values of any type while maintaining type safety
- **Protocols + generics** provide flexible, type-safe interfaces
- **Prefer generics over Any** for better type checking

**Best Practices:**

```{code-cell} python
# Good: Generic function
def first(items: list[T]) -> T:
    return items[0]

# Bad: Using Any (loses type safety)
def first(items: list[Any]) -> Any:
    return items[0]

# Good: Generic class with clear purpose
class Repository(Generic[T]):
    def save(self, entity: T) -> int: ...
    def find(self, id: int) -> T | None: ...

# Good: Multiple type parameters when needed
class Transformer(Generic[InputT, OutputT]):
    def transform(self, input: InputT) -> OutputT: ...
```

**In the demo ETL project**, generics are used for:

- `FileReader[T]` - generic reader that produces items of type T
- `SqlServerLoader[T]` - generic loader that accepts items of type T
- Type-safe pipeline from file → model → database

---

**Navigation:**
- **Previous**: [← Type Hints](01-type-hints.md)
- **Next**: [Exercises →](../05-exercises/01-python-essentials-exercises.md)
- **Home**: [Python Essentials](../README.md)
