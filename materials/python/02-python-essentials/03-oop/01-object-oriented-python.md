# Object-Oriented Python

Object-oriented programming (OOP) is a way to organize code by bundling data and the functions that operate on that data into reusable units called **classes**. This lesson covers why OOP exists, how to use it in Python, and practical patterns for data engineering.

## Why OOP Exists

As projects grow, procedural code becomes hard to manage. Let's see the problem:

```python
# Procedural approach: processing CSV and JSON files
import csv
import json

def read_csv(filepath):
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def read_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def validate_csv_data(data):
    valid = []
    for row in data:
        if 'id' in row and 'name' in row:
            valid.append(row)
    return valid

def validate_json_data(data):
    valid = []
    for item in data:
        if 'id' in item and 'name' in item:
            valid.append(item)
    return valid

def process_csv(filepath):
    data = read_csv(filepath)
    validated = validate_csv_data(data)
    # Transform...
    return validated

def process_json(filepath):
    data = read_json(filepath)
    validated = validate_json_data(data)
    # Transform...
    return validated

# Usage
csv_data = process_csv('data.csv')
json_data = process_json('data.json')
```

**Problems:**

1. Code duplication: `validate_csv_data` and `validate_json_data` are nearly identical
2. No clear organization: functions are scattered, hard to find what operates on what
3. Hard to extend: adding XML support means creating 3 more functions
4. Global state: no way to configure behavior per file type

**OOP solution: bundle related data and behavior:**

```python
import csv
import json

class FileReader:
    def __init__(self, filepath):
        self.filepath = filepath
    
    def read(self):
        raise NotImplementedError("Subclasses must implement read()")
    
    def validate(self, data):
        """Common validation logic"""
        valid = []
        for item in data:
            if 'id' in item and 'name' in item:
                valid.append(item)
        return valid
    
    def process(self):
        data = self.read()
        validated = self.validate(data)
        return validated

class CsvReader(FileReader):
    def read(self):
        with open(self.filepath, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)

class JsonReader(FileReader):
    def read(self):
        with open(self.filepath, 'r') as f:
            return json.load(f)

# Usage: polymorphic - same interface, different implementations
readers = [
    CsvReader('data.csv'),
    JsonReader('data.json'),
]

for reader in readers:
    data = reader.process()  # Works for any reader type
    print(f"Processed {len(data)} records from {reader.filepath}")
```

**Benefits:**

- **Encapsulation**: `filepath` and reading logic are bundled together
- **Reusability**: `validate()` is shared across all readers
- **Extensibility**: Add XML support by creating `XmlReader(FileReader)`
- **Polymorphism**: Process any reader type with the same code

This is the core idea of OOP: organize code around objects that represent things in your domain.

## The Four Pillars (Briefly)

OOP is often described with four principles. Here's what they mean in practice:

**1. Encapsulation:** Bundle data and methods that operate on it

```python
class BankAccount:
    def __init__(self, balance):
        self._balance = balance  # "Private" by convention
    
    def deposit(self, amount):
        if amount > 0:
            self._balance += amount
    
    def get_balance(self):
        return self._balance

account = BankAccount(100)
account.deposit(50)
print(f"Balance: ${account.get_balance()}")
# Don't access account._balance directly (violates encapsulation)
```

**2. Inheritance:** Reuse code by deriving from a base class

```python
class Animal:
    def speak(self):
        return "Some sound"

class Dog(Animal):
    def speak(self):
        return "Woof!"

class Cat(Animal):
    def speak(self):
        return "Meow!"

animals = [Dog(), Cat()]
for animal in animals:
    print(animal.speak())
```

**3. Polymorphism:** Same interface, different implementations

```python
# Already seen above: different readers, same .process() method
```

**4. Abstraction:** Hide complexity behind simple interfaces

```python
# User doesn't need to know CSV parsing details:
reader = CsvReader('data.csv')
data = reader.process()  # Simple interface, complex implementation hidden
```

In practice, focus on **encapsulation** (organizing code) and **inheritance** (reusing code). The others follow naturally.

## Classes in Python

### Basic Class Definition

```python
class DataPipeline:
    """A simple data processing pipeline."""
    
    # Class attribute (shared by all instances)
    version = "1.0"
    
    def __init__(self, name, source):
        """Constructor: called when creating an instance"""
        # Instance attributes (unique per instance)
        self.name = name
        self.source = source
        self.records_processed = 0
    
    def run(self):
        """Instance method: has access to self"""
        print(f"Running pipeline: {self.name}")
        self.records_processed += 100
        return self.records_processed
    
    def __str__(self):
        """String representation for humans"""
        return f"DataPipeline({self.name})"
    
    def __repr__(self):
        """String representation for developers"""
        return f"DataPipeline(name='{self.name}', source='{self.source}')"

# Create instances
pipeline1 = DataPipeline("ETL Job", "database")
pipeline2 = DataPipeline("Stream Processor", "kafka")

# Call methods
pipeline1.run()
print(f"{pipeline1.name} processed {pipeline1.records_processed} records")

# __str__ is used by print()
print(pipeline1)

# __repr__ is used in interactive shell and debugging
print(repr(pipeline2))

# Class attribute is shared
print(f"Version: {DataPipeline.version}")
```

### Properties

Properties provide controlled access to attributes:

```python
class Temperature:
    def __init__(self, celsius):
        self._celsius = celsius
    
    @property
    def celsius(self):
        """Get temperature in Celsius"""
        return self._celsius
    
    @celsius.setter
    def celsius(self, value):
        """Set temperature in Celsius with validation"""
        if value < -273.15:
            raise ValueError("Temperature below absolute zero!")
        self._celsius = value
    
    @property
    def fahrenheit(self):
        """Computed property: Celsius to Fahrenheit"""
        return self._celsius * 9/5 + 32
    
    @fahrenheit.setter
    def fahrenheit(self, value):
        """Set temperature in Fahrenheit (converts to Celsius)"""
        self.celsius = (value - 32) * 5/9

# Usage: looks like attribute access, but runs methods
temp = Temperature(25)
print(f"{temp.celsius}°C = {temp.fahrenheit}°F")

temp.fahrenheit = 100  # Calls setter
print(f"{temp.celsius}°C = {temp.fahrenheit}°F")

# Validation works
try:
    temp.celsius = -300
except ValueError as e:
    print(f"Error: {e}")
```

## Inheritance

Inheritance allows you to create specialized classes from a base class:

```python
class FileReader:
    """Base class for file readers"""
    
    def __init__(self, filepath):
        self.filepath = filepath
    
    def read(self):
        """Must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement read()")
    
    def validate(self, data):
        """Common validation logic"""
        return [item for item in data if item.get('id')]
    
    def process(self):
        """Template method: defines the algorithm"""
        print(f"Reading {self.filepath}...")
        data = self.read()
        print(f"Validating {len(data)} records...")
        validated = self.validate(data)
        print(f"Valid records: {len(validated)}")
        return validated

class CsvReader(FileReader):
    """Specialized reader for CSV files"""
    
    def read(self):
        import csv
        with open(self.filepath, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)

class JsonReader(FileReader):
    """Specialized reader for JSON files"""
    
    def read(self):
        import json
        with open(self.filepath, 'r') as f:
            data = json.load(f)
            # Ensure it's a list
            return data if isinstance(data, list) else [data]

# Polymorphism: treat different readers the same way
def process_file(reader: FileReader):
    return reader.process()

# Both work with the same interface
# csv_data = process_file(CsvReader('data.csv'))
# json_data = process_file(JsonReader('data.json'))
```

### Method Overriding and `super()`

```python
class DataLoader:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        print(f"DataLoader initialized with: {connection_string}")
    
    def load(self, data):
        print(f"Loading {len(data)} records...")
        return len(data)

class BatchDataLoader(DataLoader):
    def __init__(self, connection_string, batch_size):
        # Call parent constructor
        super().__init__(connection_string)
        self.batch_size = batch_size
        print(f"Batch size set to: {batch_size}")
    
    def load(self, data):
        # Override parent method, add batching logic
        print(f"Batch loading {len(data)} records (batch_size={self.batch_size})...")
        total = 0
        for i in range(0, len(data), self.batch_size):
            batch = data[i:i + self.batch_size]
            # Call parent's load method for each batch
            total += super().load(batch)
        return total

# Usage
loader = BatchDataLoader("postgresql://localhost/db", batch_size=100)
loader.load([{"id": i} for i in range(250)])
```

## Dataclasses: The Modern Way

For classes that primarily hold data, use `@dataclass`:

```python
from dataclasses import dataclass, field
from typing import List

# Traditional class (verbose)
class PersonOld:
    def __init__(self, name, age, emails):
        self.name = name
        self.age = age
        self.emails = emails
    
    def __repr__(self):
        return f"Person(name={self.name!r}, age={self.age!r}, emails={self.emails!r})"
    
    def __eq__(self, other):
        if not isinstance(other, PersonOld):
            return False
        return (self.name == other.name and 
                self.age == other.age and 
                self.emails == other.emails)

# Dataclass (concise)
@dataclass
class Person:
    name: str
    age: int
    emails: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Called after __init__, for additional setup"""
        if self.age < 0:
            raise ValueError("Age cannot be negative")

# Auto-generated __init__, __repr__, __eq__
alice = Person("Alice", 25, ["alice@example.com"])
bob = Person("Bob", 30)  # Uses default empty list for emails

print(alice)  # Person(name='Alice', age=25, emails=['alice@example.com'])
print(bob)    # Person(name='Bob', age=30, emails=[])

# Equality comparison works
alice2 = Person("Alice", 25, ["alice@example.com"])
print(f"alice == alice2: {alice == alice2}")  # True
```

### Dataclass Features

```python
from dataclasses import dataclass, field, asdict, astuple

@dataclass
class DataRecord:
    id: int
    name: str
    tags: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict, repr=False)  # Excluded from repr
    _internal: str = field(default="", init=False, repr=False)  # Not in __init__
    
    def __post_init__(self):
        self._internal = f"Record {self.id}"

record = DataRecord(1, "Test", tags=["python", "data"])
print(record)

# Convert to dict/tuple
print(f"As dict: {asdict(record)}")
print(f"As tuple: {astuple(record)}")

# Frozen dataclasses (immutable)
@dataclass(frozen=True)
class ImmutablePoint:
    x: int
    y: int

point = ImmutablePoint(10, 20)
# point.x = 30  # FrozenInstanceError!
```

**When to use dataclass vs regular class:**

- **Dataclass**: Class primarily holds data (models, configurations, DTOs)
- **Regular class**: Class has complex behavior, stateful operations, or needs fine-grained control

## Practical Patterns

### Repository Pattern

Separate data access logic from business logic:

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class User:
    id: int
    name: str
    email: str

class UserRepository:
    """Handles all database operations for Users"""
    
    def __init__(self, connection):
        self.connection = connection
        self._cache = {}
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Find user by ID"""
        if user_id in self._cache:
            return self._cache[user_id]
        
        # Simulate database query
        # cursor = self.connection.cursor()
        # cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        # row = cursor.fetchone()
        
        # For demo, return mock data
        user = User(user_id, f"User{user_id}", f"user{user_id}@example.com")
        self._cache[user_id] = user
        return user
    
    def find_all(self) -> List[User]:
        """Find all users"""
        # Simulate database query
        return [self.find_by_id(i) for i in range(1, 4)]
    
    def save(self, user: User):
        """Save user to database"""
        print(f"Saving user: {user}")
        self._cache[user.id] = user
        # self.connection.execute("INSERT OR REPLACE INTO users ...")

# Usage
repo = UserRepository(connection=None)  # Would be real DB connection
user = repo.find_by_id(1)
print(user)

all_users = repo.find_all()
for u in all_users:
    print(u.name)
```

### Strategy Pattern

Define a family of algorithms, encapsulate each one, and make them interchangeable:

```python
from dataclasses import dataclass
from typing import Protocol

@dataclass
class DataRecord:
    raw_data: str

# Define the strategy interface
class DataFormatter(Protocol):
    def format(self, data: DataRecord) -> str:
        ...

# Concrete strategies
class JsonFormatter:
    def format(self, data: DataRecord) -> str:
        import json
        return json.dumps({"data": data.raw_data})

class XmlFormatter:
    def format(self, data: DataRecord) -> str:
        return f"<data>{data.raw_data}</data>"

class CsvFormatter:
    def format(self, data: DataRecord) -> str:
        return f"data\n{data.raw_data}"

# Context: uses a formatter strategy
class DataExporter:
    def __init__(self, formatter: DataFormatter):
        self.formatter = formatter
    
    def export(self, records: List[DataRecord]) -> str:
        results = []
        for record in records:
            formatted = self.formatter.format(record)
            results.append(formatted)
        return "\n".join(results)

# Usage: swap formatters without changing exporter
records = [DataRecord("value1"), DataRecord("value2")]

json_exporter = DataExporter(JsonFormatter())
print("JSON format:")
print(json_exporter.export(records))

xml_exporter = DataExporter(XmlFormatter())
print("\nXML format:")
print(xml_exporter.export(records))
```

**This pattern appears in the demo ETL project**: different file readers implement the same interface, allowing the pipeline to work with any file format.

## When to Use Inheritance vs Composition

**Inheritance** (is-a relationship):

```python
class Vehicle:
    def start(self):
        print("Starting vehicle")

class Car(Vehicle):  # Car IS-A Vehicle
    pass

# Use when: true "is-a" relationship, small hierarchy (1-2 levels)
```

**Composition** (has-a relationship) - covered in depth in the next lesson:

```python
class Engine:
    def start(self):
        print("Engine started")

class Car:
    def __init__(self):
        self.engine = Engine()  # Car HAS-AN Engine
    
    def start(self):
        self.engine.start()

# Use when: "has-a" relationship, flexible behavior
```

**Rule of thumb:** Start with composition. Use inheritance only when there's a clear "is-a" relationship.

## Summary

| Concept | Key Points |
|---------|-----------|
| **Why OOP** | Organize code, bundle data + behavior, reduce duplication |
| **Encapsulation** | Bundle data with methods that operate on it |
| **Inheritance** | Reuse code with base classes and subclasses |
| **Dataclasses** | Modern way to define data-holding classes |
| **Patterns** | Repository (data access), Strategy (swappable algorithms) |

**Practical advice:**

- Use dataclasses for simple data containers
- Use regular classes when you need complex behavior
- Keep inheritance hierarchies shallow (1-2 levels)
- Prefer composition over inheritance (next lesson)
- Use `@property` for computed or validated attributes

**In the demo ETL project**, you'll see:

- Dataclasses for `Customer` and `Order` models
- Inheritance with `FileReader` base class
- Strategy pattern with different readers
- Repository-like pattern with `SqlServerLoader`

---

**Navigation:**
- **Previous**: [← Collections](../02-data-structures/02-collections.md)
- **Next**: [Interfaces in Python →](02-interfaces-in-python.md)
- **Home**: [Python Essentials](../README.md)
