---
kernelspec:
  name: python3
  language: python
  display_name: Python 3
---

# Primitive Types

Python's primitive types are the building blocks of all data structures. Understanding their characteristics and edge cases helps you write correct, efficient code.

## The Five Primitive Types

Python has five built-in primitive types:

1. `int` - integers
2. `float` - floating-point numbers
3. `bool` - booleans
4. `str` - strings
5. `None` - the null value

Let's explore each in detail.

## Integers: Arbitrary Precision

Unlike languages like Java or C where integers have fixed sizes (32-bit, 64-bit), Python integers can be arbitrarily large.

```{code-cell} python
# No overflow in Python
small = 42
large = 10 ** 100  # 1 followed by 100 zeros
huge = 2 ** 1000   # 2 to the power of 1000

print(f"Small: {small}")
print(f"Large: {large}")
print(f"Huge has {len(str(huge))} digits")

# In Java, this would overflow. In Python, it just works.
result = huge * huge
print(f"Huge squared has {len(str(result))} digits")
```

**When to use `int`:**

- Counting (rows processed, records inserted)
- IDs and primary keys
- Exact arithmetic (money calculations should use `Decimal`, not float)

```{code-cell} python
# Common int operations in data engineering
records_processed = 0
batch_size = 1000

for batch_id in range(10):
    # Process batch...
    records_processed += batch_size

print(f"Processed {records_processed} records")

# Integer division vs float division
print(f"17 / 5 = {17 / 5}")   # Float division: 3.4
print(f"17 // 5 = {17 // 5}") # Integer division: 3
print(f"17 % 5 = {17 % 5}")   # Modulo (remainder): 2
```

**Advanced Note: Object Identity and Interning**

Python interns (caches) small integers for performance:

```{code-cell} python
a = 256
b = 256
print(f"a is b: {a is b}")  # True - same object

c = 257
d = 257
print(f"c is d: {c is d}")  # False (usually) - different objects

# This is an optimization: small integers (-5 to 256) are pre-created
# and reused to save memory. Don't rely on this behavior; always use
# == for equality, not 'is'.
```

## Floats: IEEE 754 and Floating Point Gotchas

Python floats are 64-bit IEEE 754 floating-point numbers. They're fast but imprecise.

```{code-cell} python
# The classic floating point problem
a = 0.1
b = 0.2
c = a + b

print(f"0.1 + 0.2 = {c}")
print(f"Is it 0.3? {c == 0.3}")  # False!

# Why? Binary representation of 0.1 and 0.2 is not exact
print(f"Actual value: {c:.20f}")  # 0.30000000000000004441
```

**When precision matters, use `Decimal`:**

```{code-cell} python
from decimal import Decimal

# For financial calculations or when exact precision is required
price = Decimal("19.99")
quantity = Decimal("3")
total = price * quantity

print(f"Total: ${total}")  # Exact: $59.97

# Compare to float
float_total = 19.99 * 3
print(f"Float total: ${float_total}")  # Still accurate here, but can drift
```

**When to use `float`:**

- Scientific calculations where small errors are acceptable
- Performance-critical code (floats are faster than Decimal)
- Working with NumPy/pandas (they use floats internally)

```{code-cell} python
# Common float operations in data engineering
import math

# Calculating percentages
total_records = 10_000
error_records = 37
error_rate = (error_records / total_records) * 100

print(f"Error rate: {error_rate:.2f}%")

# Working with infinity and NaN
infinity = float('inf')
negative_infinity = float('-inf')
not_a_number = float('nan')

print(f"Infinity: {infinity}")
print(f"Is infinite? {math.isinf(infinity)}")
print(f"NaN: {not_a_number}")
print(f"Is NaN? {math.isnan(not_a_number)}")

# NaN is special: it's not equal to itself
print(f"NaN == NaN: {not_a_number == not_a_number}")  # False!
```

## Booleans: Subclass of Int

Python's `bool` type is actually a subclass of `int` with two values: `True` (1) and `False` (0).

```{code-cell} python
# True and False are integers
print(f"True == 1: {True == 1}")    # True
print(f"False == 0: {False == 0}")  # True
print(f"True + True: {True + True}")  # 2

# You can do math with booleans (but you shouldn't)
result = True * 5 + False
print(f"True * 5 + False = {result}")  # 5
```

### Truthy and Falsy Values

Every Python object has a boolean value in a boolean context:

```{code-cell} python
# Falsy values (evaluate to False)
falsy_values = [
    False,
    None,
    0,
    0.0,
    "",
    [],
    {},
    set(),
]

for value in falsy_values:
    if not value:
        print(f"{repr(value)} is falsy")

# Everything else is truthy
truthy_values = [
    True,
    1,
    -1,
    0.1,
    "any string",
    [1, 2, 3],
    {"key": "value"},
]

for value in truthy_values:
    if value:
        print(f"{repr(value)} is truthy")
```

**Practical implications:**

```{code-cell} python
# Checking if a list is empty
items = []

# Pythonic way (uses truthiness)
if items:
    print("Has items")
else:
    print("Empty list")

# Explicit way (less Pythonic)
if len(items) > 0:
    print("Has items")
else:
    print("Empty list")

# Checking for None vs empty
data = None

if data:
    print("Has data")  # Won't execute
else:
    print("No data or empty")

# If you specifically want to check for None:
if data is None:
    print("Data is None")
```

## Strings: Immutable Unicode

Python strings are immutable sequences of Unicode characters.

```{code-cell} python
# String creation
single = 'single quotes'
double = "double quotes"
triple = """triple quotes
can span
multiple lines"""

# Python doesn't care which you use for simple strings
print(f"Single == double: {single == 'single quotes'}")

# Unicode support is built-in
emoji = "🐍 Python 🚀"
chinese = "你好"
hebrew = "מה הולך"

print(f"Emoji: {emoji}")
print(f"Hebrew: {hebrew}")
print(f"Chinese: {chinese}")

# String length counts characters, not bytes
print(f"Length of '{emoji}': {len(emoji)} characters")
```

### String Immutability

```{code-cell} python
# Strings cannot be modified in-place
text = "Hello"

# This doesn't modify text; it creates a new string
new_text = text.replace("H", "J")

print(f"Original: {text}")
print(f"New: {new_text}")

# Common mistake: trying to modify by index
# text[0] = "J"  # TypeError: 'str' object does not support item assignment

# Instead, create a new string
text = "J" + text[1:]
print(f"Modified: {text}")
```

**Why immutability matters:**

- Strings can be dictionary keys (must be hashable)
- Safe to share strings across threads
- Python can optimize string operations

### Common String Operations

```{code-cell} python
# String methods return new strings (immutability)
text = "  Python Programming  "

print(f"Original: '{text}'")
print(f"Lower: '{text.lower()}'")
print(f"Upper: '{text.upper()}'")
print(f"Strip: '{text.strip()}'")
print(f"Replace: '{text.replace('Python', 'Rust')}'")

# Splitting and joining
csv_line = "Alice,25,Engineer"
fields = csv_line.split(",")
print(f"Split: {fields}")

# Join list into string
joined = " | ".join(fields)
print(f"Joined: {joined}")

# Check membership
if "Python" in text:
    print("Found 'Python' in text")

# Formatting
name = "Alice"
age = 25
role = "Engineer"

# f-strings (Python 3.6+, preferred)
message = f"{name} is a {age}-year-old {role}"
print(message)

# Format method (older, still useful)
message = "{} is a {}-year-old {}".format(name, age, role)
print(message)

# Named placeholders
message = "{name} is a {age}-year-old {role}".format(name=name, age=age, role=role)
print(message)
```

### str vs bytes

```{code-cell} python
# str is for text (Unicode characters)
text = "Hello 🌍"
print(f"Text: {text}, type: {type(text)}")

# bytes is for binary data
binary = b"Hello"
print(f"Bytes: {binary}, type: {type(binary)}")

# Encoding: str → bytes
encoded = text.encode("utf-8")
print(f"Encoded: {encoded}")

# Decoding: bytes → str
decoded = encoded.decode("utf-8")
print(f"Decoded: {decoded}")

# When to use bytes:
# - Reading/writing binary files
# - Network protocols
# - Cryptography
# - Interfacing with C libraries
```

**Common gotcha: opening files in wrong mode**

```python
# Text mode (default) - returns str
with open("example.txt", "w") as f:
    f.write("Hello 🌍")

with open("example.txt", "r") as f:
    content = f.read()
    print(f"Type: {type(content)}, Content: {content}")

# Binary mode - returns bytes
with open("example.txt", "rb") as f:
    content = f.read()
    print(f"Type: {type(content)}, Content: {content}")
```

## None: The Singleton

`None` is Python's null value. There's only one `None` object in the entire Python process.

```{code-cell} python
a = None
b = None

# None is a singleton: there's only one
print(f"a is b: {a is b}")  # True

# Check for None using 'is', not '=='
if a is None:
    print("a is None")

# Why 'is' instead of '=='?
# 'is' checks object identity (same object)
# '==' checks value equality

# For None, they're equivalent, but 'is' is faster and more explicit
print(f"a == None: {a == None}")  # True, but don't do this
print(f"a is None: {a is None}")  # Preferred
```

**When to use `None`:**

```{code-cell} python
# Default function arguments
def fetch_data(limit=None):
    if limit is None:
        limit = 100  # Default value
    print(f"Fetching {limit} records")

fetch_data()
fetch_data(50)

# Optional values
def find_user(user_id):
    # Imagine this queries a database
    if user_id == 999:
        return {"id": 999, "name": "Alice"}
    return None  # User not found

user = find_user(999)
if user is not None:
    print(f"Found user: {user['name']}")
else:
    print("User not found")

# Distinguish between "no value" and "empty value"
results = []  # Empty list (we got results, just zero of them)
results = None  # No results (query failed or not executed)

if results is None:
    print("Query failed")
elif not results:
    print("Query succeeded but returned no rows")
else:
    print(f"Query returned {len(results)} rows")
```

## Advanced: Python's Object Model

Everything in Python is an object, including primitive types.

```{code-cell} python
# Primitives are objects
x = 42
print(f"Type: {type(x)}")
print(f"ID (memory address): {id(x)}")
print(f"Methods: {dir(x)[:5]}...")  # Integers have methods!

# Even methods are objects
print(f"Type of int.bit_length: {type(x.bit_length)}")

# This is why you can do:
num = 42
binary_length = num.bit_length()
print(f"{num} requires {binary_length} bits")

# Everything inherits from object
print(f"int inherits from: {int.__bases__}")
print(f"str inherits from: {str.__bases__}")
print(f"bool inherits from: {bool.__bases__}")  # bool is a subclass of int!
```

**Object identity with `id()`:**

```{code-cell} python
# id() returns the memory address of an object
a = [1, 2, 3]
b = [1, 2, 3]
c = a

print(f"id(a): {id(a)}")
print(f"id(b): {id(b)}")
print(f"id(c): {id(c)}")

print(f"a == b: {a == b}")  # True (same value)
print(f"a is b: {a is b}")  # False (different objects)
print(f"a is c: {a is c}")  # True (same object)
```

## Summary

| Type | Mutable | Key Characteristics | Common Use Cases |
|------|---------|---------------------|------------------|
| `int` | No | Arbitrary precision, no overflow | Counting, IDs, exact math |
| `float` | No | IEEE 754, approximate | Scientific calculations, percentages |
| `bool` | No | Subclass of int, truthy/falsy | Conditions, flags |
| `str` | No | Unicode, immutable | Text processing, keys |
| `None` | N/A | Singleton null value | Missing data, default values |

**Key Takeaways:**

- Use `Decimal` for exact precision (finance, money)
- Check for `None` using `is None`, not `== None`
- Strings are immutable; methods return new strings
- Everything in Python is an object
- Understand truthy/falsy for idiomatic Python code

---

**Navigation:**
- **Previous**: [← Dependency Management](../01-project-setup/02-dependency-management.md)
- **Next**: [Collections →](02-collections.md)
- **Home**: [Python Essentials](../README.md)
