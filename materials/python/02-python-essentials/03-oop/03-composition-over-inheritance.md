---
kernelspec:
  name: python3
  language: python
  display_name: Python 3
---

# Composition Over Inheritance

"Composition over inheritance" is a design principle that favors building functionality by combining objects rather than inheriting from parent classes. This lesson explores why deep inheritance hierarchies become problematic and how composition provides a more flexible alternative.

## The Inheritance Trap

Inheritance seems elegant at first: create a base class, derive specialized versions. But as hierarchies grow, they become rigid and hard to change.

### Example: The Classic Problem

```{code-cell} python
class Animal:
    def __init__(self, name):
        self.name = name
    
    def eat(self):
        print(f"{self.name} is eating")

class Dog(Animal):
    def bark(self):
        print(f"{self.name} barks")

class GuideDog(Dog):
    def guide(self):
        print(f"{self.name} is guiding")

class TherapyDog(Dog):
    def provide_therapy(self):
        print(f"{self.name} provides therapy")

# Now you want a dog that's BOTH a guide dog and therapy dog
class TherapyGuideDog(GuideDog, TherapyDog):
    pass

# Multiple inheritance can work, but what about:
# - A herding dog that's also a therapy dog?
# - A dog that does all three: guide, therapy, herd?
# - Combinations explode: 2^N subclasses for N capabilities!
```

**The "banana-gorilla-jungle" problem**: You wanted a banana (one feature), but got a gorilla holding the banana (base class), and the entire jungle (all inherited baggage).

### The Diamond Problem

Multiple inheritance can create ambiguity:

```{code-cell} python
class A:
    def method(self):
        print("A's method")

class B(A):
    def method(self):
        print("B's method")

class C(A):
    def method(self):
        print("C's method")

class D(B, C):  # Diamond: A <- B <- D, A <- C <- D
    pass

d = D()
d.method()  # Which method? B's or C's?

# Python uses Method Resolution Order (MRO) to decide
print(D.__mro__)
# (<class 'D'>, <class 'B'>, <class 'C'>, <class 'A'>, <class 'object'>)
# B comes before C, so B's method is called
```

**Advanced Note**: Python's MRO uses C3 linearization to create a consistent order. But relying on MRO is fragile—changes to the hierarchy break unexpectedly.

### Realistic Example: Data Processors

```python
# Bad: inheritance-based design
class BaseProcessor:
    def process(self, data):
        print("Base processing")
        return data

class CsvProcessor(BaseProcessor):
    def process(self, data):
        print("CSV-specific processing")
        return super().process(data)

class ValidatedCsvProcessor(CsvProcessor):
    def process(self, data):
        print("Validating CSV")
        return super().process(data)

class TransformedValidatedCsvProcessor(ValidatedCsvProcessor):
    def process(self, data):
        print("Transforming validated CSV")
        return super().process(data)

# Problems:
# 1. Deep hierarchy (4 levels)
# 2. Hard to reuse: can't use validation without CSV
# 3. Rigid: adding JSON support requires duplicating the hierarchy
# 4. Testing nightmare: must instantiate entire chain
```

## What is Composition?

Composition means building functionality by **combining objects** rather than inheriting behavior.

**Instead of "is-a", think "has-a":**

- Inheritance: A `GuideDog` **is-a** `Dog`
- Composition: A `Dog` **has-a** list of abilities

```{code-cell} python
# Good: composition-based design
class Ability:
    """Base class for abilities (could also be a Protocol)"""
    def execute(self, subject):
        raise NotImplementedError

class GuidingAbility(Ability):
    def execute(self, subject):
        print(f"{subject.name} is guiding")

class TherapyAbility(Ability):
    def execute(self, subject):
        print(f"{subject.name} provides therapy")

class HerdingAbility(Ability):
    def execute(self, subject):
        print(f"{subject.name} is herding")

class Dog:
    def __init__(self, name, abilities=None):
        self.name = name
        self.abilities = abilities or []
    
    def perform_abilities(self):
        for ability in self.abilities:
            ability.execute(self)

# Now creating combinations is trivial:
guide_dog = Dog("Max", [GuidingAbility()])
therapy_dog = Dog("Buddy", [TherapyAbility()])
super_dog = Dog("Hero", [GuidingAbility(), TherapyAbility(), HerdingAbility()])

guide_dog.perform_abilities()
super_dog.perform_abilities()

# Easy to add new abilities without modifying Dog
class SearchAndRescueAbility(Ability):
    def execute(self, subject):
        print(f"{subject.name} is searching and rescuing")

rescue_dog = Dog("Rex", [SearchAndRescueAbility(), TherapyAbility()])
rescue_dog.perform_abilities()
```

**Benefits:**

- **Flexible**: Any combination of abilities
- **Reusable**: Abilities work with any subject
- **Testable**: Test abilities independently
- **Extensible**: Add new abilities without changing `Dog`

## Composition in Practice

### Example: Report Generator

**Bad: Inheritance**

```python
class ReportGenerator:
    def generate(self):
        data = self.fetch_data()
        formatted = self.format_data(data)
        self.export(formatted)

class CsvReportGenerator(ReportGenerator):
    def fetch_data(self):
        return "CSV data"
    
    def format_data(self, data):
        return f"CSV formatted: {data}"
    
    def export(self, formatted):
        print(f"Exporting to file: {formatted}")

class JsonApiReportGenerator(ReportGenerator):
    def fetch_data(self):
        return "API data"
    
    def format_data(self, data):
        return f"JSON formatted: {data}"
    
    def export(self, formatted):
        print(f"Sending to API: {formatted}")

# Problem: Want CSV data with JSON format and API export?
# Need to create yet another subclass!
```

**Good: Composition**

```{code-cell} python
from typing import Protocol

class DataSource(Protocol):
    def fetch(self) -> str:
        ...

class Formatter(Protocol):
    def format(self, data: str) -> str:
        ...

class Exporter(Protocol):
    def export(self, formatted: str):
        ...

# Implementations
class CsvDataSource:
    def fetch(self) -> str:
        return "CSV data"

class ApiDataSource:
    def fetch(self) -> str:
        return "API data"

class JsonFormatter:
    def format(self, data: str) -> str:
        return f"JSON: {data}"

class XmlFormatter:
    def format(self, data: str) -> str:
        return f"<data>{data}</data>"

class FileExporter:
    def export(self, formatted: str):
        print(f"Exporting to file: {formatted}")

class ApiExporter:
    def export(self, formatted: str):
        print(f"Sending to API: {formatted}")

# Composed report generator
class ReportGenerator:
    def __init__(self, source: DataSource, formatter: Formatter, exporter: Exporter):
        self.source = source
        self.formatter = formatter
        self.exporter = exporter
    
    def generate(self):
        data = self.source.fetch()
        formatted = self.formatter.format(data)
        self.exporter.export(formatted)

# Now any combination works:
csv_json_file = ReportGenerator(
    source=CsvDataSource(),
    formatter=JsonFormatter(),
    exporter=FileExporter()
)

api_xml_api = ReportGenerator(
    source=ApiDataSource(),
    formatter=XmlFormatter(),
    exporter=ApiExporter()
)

csv_json_file.generate()
api_xml_api.generate()

# Want to add a new formatter? Just implement the protocol:
class CsvFormatter:
    def format(self, data: str) -> str:
        return f"CSV: {data}"

# Works immediately without modifying ReportGenerator
csv_csv_file = ReportGenerator(
    source=CsvDataSource(),
    formatter=CsvFormatter(),
    exporter=FileExporter()
)
```

**This is dependency injection**: passing dependencies through the constructor instead of creating them internally or inheriting them.

## Refactoring from Inheritance to Composition

Let's refactor a realistic data processing pipeline:

### Before: Inheritance-Heavy

```{code-cell} python
class BaseProcessor:
    def process(self, data):
        return data

class CsvProcessor(BaseProcessor):
    def process(self, data):
        print("Reading CSV")
        # CSV-specific logic
        return super().process(data)

class ValidatedCsvProcessor(CsvProcessor):
    def process(self, data):
        print("Validating")
        # Validation logic
        return super().process(data)

class TransformedValidatedCsvProcessor(ValidatedCsvProcessor):
    def process(self, data):
        print("Transforming")
        # Transform logic
        return super().process(data)

# Problems:
# - Can't reuse validation without CSV
# - Can't add JSON support without duplicating hierarchy
# - Testing requires full chain
```

### After: Composition-Based

```{code-cell} python
from typing import Protocol, List

# Define component interfaces
class Reader(Protocol):
    def read(self) -> List[dict]:
        ...

class Validator(Protocol):
    def validate(self, data: List[dict]) -> List[dict]:
        ...

class Transformer(Protocol):
    def transform(self, data: List[dict]) -> List[dict]:
        ...

class Writer(Protocol):
    def write(self, data: List[dict]):
        ...

# Implementations
class CsvReader:
    def __init__(self, filepath):
        self.filepath = filepath
    
    def read(self) -> List[dict]:
        print(f"Reading CSV from {self.filepath}")
        return [{"id": 1, "name": "Alice"}]

class JsonReader:
    def __init__(self, filepath):
        self.filepath = filepath
    
    def read(self) -> List[dict]:
        print(f"Reading JSON from {self.filepath}")
        return [{"id": 1, "name": "Bob"}]

class SchemaValidator:
    def validate(self, data: List[dict]) -> List[dict]:
        print("Validating schema")
        return [row for row in data if "id" in row and "name" in row]

class UppercaseTransformer:
    def transform(self, data: List[dict]) -> List[dict]:
        print("Transforming to uppercase")
        return [{"id": row["id"], "name": row["name"].upper()} for row in data]

class DatabaseWriter:
    def write(self, data: List[dict]):
        print(f"Writing {len(data)} records to database")

# Composed processor
class Processor:
    def __init__(
        self,
        reader: Reader,
        validator: Validator,
        transformer: Transformer,
        writer: Writer
    ):
        self.reader = reader
        self.validator = validator
        self.transformer = transformer
        self.writer = writer
    
    def process(self):
        data = self.reader.read()
        validated = self.validator.validate(data)
        transformed = self.transformer.transform(validated)
        self.writer.write(transformed)

# Use: CSV -> validate -> transform -> DB
csv_processor = Processor(
    reader=CsvReader("data.csv"),
    validator=SchemaValidator(),
    transformer=UppercaseTransformer(),
    writer=DatabaseWriter()
)

csv_processor.process()

# JSON with same pipeline: just swap the reader!
json_processor = Processor(
    reader=JsonReader("data.json"),
    validator=SchemaValidator(),
    transformer=UppercaseTransformer(),
    writer=DatabaseWriter()
)

json_processor.process()

# Want validation but no transformation? Easy:
class NoOpTransformer:
    def transform(self, data: List[dict]) -> List[dict]:
        return data

simple_processor = Processor(
    reader=CsvReader("data.csv"),
    validator=SchemaValidator(),
    transformer=NoOpTransformer(),
    writer=DatabaseWriter()
)
```

**Benefits of the refactor:**

1. **Reusable components**: Each piece works independently
2. **Easy testing**: Test `SchemaValidator` without `CsvReader`
3. **Flexible**: Any combination of reader/validator/transformer/writer
4. **No hierarchy**: Flat structure, easier to understand

## When to Use Inheritance vs Composition

| Scenario | Use Inheritance | Use Composition |
|----------|----------------|-----------------|
| True "is-a" relationship | ✓ (e.g., `Dog` is an `Animal`) | |
| "Has-a" or "uses-a" relationship | | ✓ (e.g., `Dog` has `Abilities`) |
| Small hierarchy (1-2 levels) | ✓ | |
| Deep hierarchy (3+ levels) | | ✓ |
| Need to share implementation | ✓ (with caution) | ✓ (via composition) |
| Need flexibility/combinations | | ✓ |
| Framework requires it | ✓ (e.g., Django models) | |
| You control all code | Either | Prefer composition |
| Third-party integration | | ✓ |

**Rule of thumb:**

```{code-cell} python
# Good use of inheritance: shallow, true "is-a"
class Vehicle:
    def start(self):
        print("Starting vehicle")

class Car(Vehicle):
    pass

# Prefer composition: flexible behavior
class Car:
    def __init__(self, engine, transmission):
        self.engine = engine
        self.transmission = transmission
    
    def start(self):
        self.engine.start()
```

## Advanced: Mixins as a Middle Ground

Mixins are small classes that provide specific functionality. They're a compromise between inheritance and composition.

```{code-cell} python
class TimestampMixin:
    """Adds created_at and updated_at tracking"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from datetime import datetime
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def touch(self):
        from datetime import datetime
        self.updated_at = datetime.now()

class LoggingMixin:
    """Adds logging capability"""
    def log(self, message):
        print(f"[{self.__class__.__name__}] {message}")

class DataRecord(TimestampMixin, LoggingMixin):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.log(f"Created with data: {data}")

record = DataRecord({"id": 1, "name": "Alice"})
record.touch()
record.log("Updated")
print(f"Created: {record.created_at}")
```

**When mixins make sense:**

- Cross-cutting concerns (logging, timestamps, serialization)
- Framework integration (Django uses mixins heavily)
- Small, focused functionality

**When mixins are an anti-pattern:**

- Deep mixin chains (becomes inheritance problem again)
- Mixins with state dependencies (hard to reason about)
- When composition would be clearer

**Generally, prefer composition over mixins** unless you're working in a framework that encourages mixins.

## Summary

| Approach | Structure | Flexibility | Use Case |
|----------|-----------|-------------|----------|
| **Inheritance** | Tree hierarchy | Low (rigid) | True "is-a", shallow trees |
| **Composition** | Object graph | High (any combination) | "Has-a", flexible behavior |
| **Mixins** | Multiple inheritance | Medium | Cross-cutting concerns |

**Key Takeaways:**

- **Inheritance** creates rigid hierarchies that are hard to change
- **Composition** provides flexibility by combining objects
- **Favor composition** for most real-world scenarios
- **Use inheritance** for shallow "is-a" relationships (1-2 levels)
- **Dependency injection** (passing dependencies to constructors) enables composition

**Practical advice:**

```{code-cell} python
# Start with composition by default
class Pipeline:
    def __init__(self, reader, processor, writer):
        self.reader = reader
        self.processor = processor
        self.writer = writer

# Only use inheritance when there's a clear "is-a"
class SpecializedReader(BaseReader):
    pass  # Only if SpecializedReader truly IS-A BaseReader
```

**In the demo ETL project**, composition is used heavily:

- `FileReader` implementations are composed, not deeply inherited
- `SqlServerLoader` is injected as a dependency
- Pipeline orchestrates composed components

---

**Navigation:**
- **Previous**: [← Interfaces in Python](02-interfaces-in-python.md)
- **Next**: [Type Hints →](../04-typing/01-type-hints.md)
- **Home**: [Python Essentials](../README.md)
