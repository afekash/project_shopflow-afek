---
kernelspec:
  name: python3
  language: python
  display_name: Python 3
---

# Interfaces in Python

An **interface** is a contract that defines what methods a class must implement, without specifying how. Interfaces enable decoupling, testability, and swappable implementations. Python offers two approaches: Abstract Base Classes (ABCs) and Protocols.

## What is an Interface?

In languages like Java or C#, you define an interface explicitly:

```{code-cell} python
# Java/C# style (pseudocode)
# interface DataSource {
#     List<Record> fetch();
#     void close();
# }
# 
# class DatabaseSource implements DataSource {
#     List<Record> fetch() { /* implementation */ }
#     void close() { /* implementation */ }
# }
```

The interface says: "Any class implementing `DataSource` **must** have `fetch()` and `close()` methods."

**Why interfaces matter:**

1. **Decoupling**: Code depends on interfaces, not concrete classes
2. **Testability**: Swap real implementations with mocks
3. **Polymorphism**: Different implementations, same interface

Python doesn't have an `interface` keyword, but provides two mechanisms: **Abstract Base Classes** and **Protocols**.

## Abstract Base Classes (ABCs)

ABCs define interfaces explicitly with `abc.ABC` and `@abstractmethod`:

```{code-cell} python
from abc import ABC, abstractmethod
from typing import List

class DataSource(ABC):
    """Abstract interface for data sources"""
    
    @abstractmethod
    def fetch(self) -> List[dict]:
        """Fetch records from the source"""
        pass
    
    @abstractmethod
    def close(self):
        """Close the connection"""
        pass

# Concrete implementation
class CsvDataSource(DataSource):
    def __init__(self, filepath):
        self.filepath = filepath
    
    def fetch(self) -> List[dict]:
        import csv
        with open(self.filepath, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def close(self):
        print(f"Closed CSV file: {self.filepath}")

class ApiDataSource(DataSource):
    def __init__(self, url):
        self.url = url
    
    def fetch(self) -> List[dict]:
        # Simulate API call
        print(f"Fetching from API: {self.url}")
        return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    
    def close(self):
        print(f"Closed API connection: {self.url}")

# Usage: work with any DataSource implementation
def process_data(source: DataSource):
    try:
        data = source.fetch()
        print(f"Fetched {len(data)} records")
        return data
    finally:
        source.close()

csv_source = CsvDataSource("data.csv")
api_source = ApiDataSource("https://api.example.com/data")

# Same function works with both
# process_data(csv_source)
# process_data(api_source)
```

### What Happens If You Forget to Implement?

```{code-cell} python
from abc import ABC, abstractmethod

class DataSource(ABC):
    @abstractmethod
    def fetch(self):
        pass

# Forgot to implement fetch()
class BrokenSource(DataSource):
    def __init__(self):
        pass

# This raises TypeError at instantiation
try:
    broken = BrokenSource()
except TypeError as e:
    print(f"Error: {e}")
    # Error: Can't instantiate abstract class BrokenSource with abstract method fetch
```

**Key point**: ABCs enforce the contract at **runtime** when you try to instantiate.

### Abstract Properties

You can also require properties:

```{code-cell} python
from abc import ABC, abstractmethod

class Configurable(ABC):
    @property
    @abstractmethod
    def config_name(self) -> str:
        """The configuration name"""
        pass
    
    @abstractmethod
    def load_config(self):
        """Load configuration"""
        pass

class AppConfig(Configurable):
    @property
    def config_name(self) -> str:
        return "app_config"
    
    def load_config(self):
        print(f"Loading {self.config_name}")

config = AppConfig()
config.load_config()
print(f"Config name: {config.config_name}")
```

## Protocols: Structural Typing

Protocols define interfaces **implicitly** using Python's duck typing: "if it walks like a duck and quacks like a duck, it's a duck."

```{code-cell} python
from typing import Protocol, List

class DataSource(Protocol):
    """Protocol: any class with fetch() and close() is a DataSource"""
    
    def fetch(self) -> List[dict]:
        ...
    
    def close(self):
        ...

# No inheritance needed!
class CsvDataSource:
    def __init__(self, filepath):
        self.filepath = filepath
    
    def fetch(self) -> List[dict]:
        import csv
        with open(self.filepath, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def close(self):
        print(f"Closed CSV file: {self.filepath}")

class ApiDataSource:
    def __init__(self, url):
        self.url = url
    
    def fetch(self) -> List[dict]:
        return [{"id": 1, "name": "Alice"}]
    
    def close(self):
        print(f"Closed API: {self.url}")

# Type checker verifies these satisfy DataSource protocol
def process_data(source: DataSource) -> List[dict]:
    try:
        data = source.fetch()
        print(f"Fetched {len(data)} records")
        return data
    finally:
        source.close()

# Both work without inheriting from DataSource
csv_source = CsvDataSource("data.csv")
api_source = ApiDataSource("https://api.example.com")

# Type checkers (mypy) verify these match the protocol
# process_data(csv_source)  # OK
# process_data(api_source)  # OK
```

**Key difference from ABC**: No runtime check! If you pass an object without `fetch()` or `close()`, it fails when you **call** the method, not when you create the object.

```{code-cell} python
from typing import Protocol

class DataSource(Protocol):
    def fetch(self):
        ...

class BrokenSource:
    pass

# No error at instantiation (unlike ABC)
broken = BrokenSource()

# Error when you try to use it
try:
    # broken.fetch()  # AttributeError at runtime
    pass
except AttributeError as e:
    print(f"Error: {e}")
```

**Type checkers catch this at development time:**

```{code-cell} python
# mypy will flag this as an error:
# def process_data(source: DataSource):
#     ...
# 
# process_data(BrokenSource())  # mypy: error: Missing "fetch" method
```

## ABC vs Protocol: When to Use Which

| Feature | ABC | Protocol |
|---------|-----|----------|
| **Inheritance** | Explicit (must inherit) | Implicit (duck typing) |
| **Runtime check** | Yes (at instantiation) | No (at method call) |
| **Type checking** | By inheritance | By structure |
| **Best for** | You control the hierarchy | Third-party code, loose coupling |

### When to Use ABC

Use ABCs when you **own the implementations** and want runtime enforcement:

```{code-cell} python
from abc import ABC, abstractmethod

class DatabaseConnection(ABC):
    """All DB connections must implement these methods"""
    
    @abstractmethod
    def execute(self, query: str):
        pass
    
    @abstractmethod
    def close(self):
        pass

class PostgresConnection(DatabaseConnection):
    def execute(self, query: str):
        print(f"Executing on Postgres: {query}")
    
    def close(self):
        print("Closed Postgres connection")

class MySqlConnection(DatabaseConnection):
    def execute(self, query: str):
        print(f"Executing on MySQL: {query}")
    
    def close(self):
        print("Closed MySQL connection")

# Factory function returns any DatabaseConnection
def get_connection(db_type: str) -> DatabaseConnection:
    if db_type == "postgres":
        return PostgresConnection()
    elif db_type == "mysql":
        return MySqlConnection()
    raise ValueError(f"Unknown database type: {db_type}")

conn = get_connection("postgres")
conn.execute("SELECT * FROM users")
conn.close()
```

### When to Use Protocol

Use Protocols when working with **third-party code** or when you want **loose coupling**:

```{code-cell} python
from typing import Protocol

class Renderable(Protocol):
    """Anything with a render() method can be rendered"""
    def render(self) -> str:
        ...

# Your code
class Template:
    def __init__(self, content):
        self.content = content
    
    def render(self) -> str:
        return f"<html>{self.content}</html>"

# Third-party library class (you don't control)
class MarkdownDocument:
    def __init__(self, text):
        self.text = text
    
    def render(self) -> str:
        return f"# {self.text}"  # Simplified markdown

# Function works with anything that has render()
def display(item: Renderable):
    print(item.render())

# Both work without modifying their class definitions
template = Template("Hello")
doc = MarkdownDocument("Title")

display(template)
display(doc)
```

**Practical guidance:**

- **Prefer Protocol for type hints**: More flexible, works with existing code
- **Use ABC for runtime enforcement**: When you need to ensure methods are implemented before instantiation
- **Combine both**: Use ABC for your own hierarchy, Protocol for type hints in public APIs

## Practical Example: Notification System

Let's build a notification system that demonstrates both approaches.

### Version 1: Using ABC

```{code-cell} python
from abc import ABC, abstractmethod

class Notifier(ABC):
    """Abstract base class for all notifiers"""
    
    @abstractmethod
    def send(self, message: str):
        """Send a notification"""
        pass

class EmailNotifier(Notifier):
    def __init__(self, recipient):
        self.recipient = recipient
    
    def send(self, message: str):
        print(f"Email to {self.recipient}: {message}")

class SlackNotifier(Notifier):
    def __init__(self, channel):
        self.channel = channel
    
    def send(self, message: str):
        print(f"Slack to #{self.channel}: {message}")

class LogNotifier(Notifier):
    def send(self, message: str):
        print(f"[LOG] {message}")

# Notification service sends to multiple notifiers
class NotificationService:
    def __init__(self, notifiers: list[Notifier]):
        self.notifiers = notifiers
    
    def notify_all(self, message: str):
        for notifier in self.notifiers:
            notifier.send(message)

# Usage
notifiers = [
    EmailNotifier("admin@example.com"),
    SlackNotifier("alerts"),
    LogNotifier(),
]

service = NotificationService(notifiers)
service.notify_all("System deployment complete!")
```

### Version 2: Using Protocol

```{code-cell} python
from typing import Protocol

class Notifier(Protocol):
    """Protocol: anything with send(message) is a notifier"""
    def send(self, message: str):
        ...

# No inheritance needed!
class EmailNotifier:
    def __init__(self, recipient):
        self.recipient = recipient
    
    def send(self, message: str):
        print(f"Email to {self.recipient}: {message}")

class SlackNotifier:
    def __init__(self, channel):
        self.channel = channel
    
    def send(self, message: str):
        print(f"Slack to #{self.channel}: {message}")

class LogNotifier:
    def send(self, message: str):
        print(f"[LOG] {message}")

# Works with any object that has send()
class NotificationService:
    def __init__(self, notifiers: list[Notifier]):
        self.notifiers = notifiers
    
    def notify_all(self, message: str):
        for notifier in self.notifiers:
            notifier.send(message)

# Now you can even add third-party notifiers:
class SmsGateway:  # From external library
    def send(self, message: str):
        print(f"SMS: {message}")

# Works without modifying SmsGateway
notifiers = [
    EmailNotifier("admin@example.com"),
    SlackNotifier("alerts"),
    LogNotifier(),
    SmsGateway(),  # Third-party class, no inheritance
]

service = NotificationService(notifiers)
service.notify_all("System deployment complete!")
```

**Advantage of Protocol**: `SmsGateway` didn't need to inherit from `Notifier`, yet type checkers know it satisfies the protocol.

## Runtime Protocol Checking (Optional)

Protocols are checked by type checkers (mypy), not at runtime. But you can opt-in to runtime checking:

```{code-cell} python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Drawable(Protocol):
    def draw(self):
        ...

class Circle:
    def draw(self):
        print("Drawing circle")

class Square:
    def area(self):
        print("Calculating area")

circle = Circle()
square = Square()

# Runtime check with isinstance
print(f"Circle is Drawable: {isinstance(circle, Drawable)}")  # True
print(f"Square is Drawable: {isinstance(square, Drawable)}")  # False
```

**Note**: Runtime checking with `@runtime_checkable` only checks method names, not signatures. For full validation, use type checkers.

## Summary

| Approach | Definition | Enforcement | Use When |
|----------|-----------|-------------|----------|
| **ABC** | Explicit inheritance + `@abstractmethod` | Runtime (at instantiation) | You control the hierarchy |
| **Protocol** | Duck typing + structural matching | Type checkers (mypy) | Working with third-party code |

**Key Takeaways:**

- **Interfaces** define contracts: "implement these methods"
- **ABCs** enforce contracts at runtime; use for your own class hierarchies
- **Protocols** enable duck typing with type safety; use for flexible APIs
- **Prefer Protocol** for type hints in public APIs (more flexible)
- **Use ABC** when you need runtime guarantees

**In practice:**

```{code-cell} python
# Good: Protocol for type hints (flexible)
from typing import Protocol

class Repository(Protocol):
    def save(self, entity): ...
    def find(self, id): ...

def process(repo: Repository):
    # Works with ANY object that has save() and find()
    ...

# Good: ABC for your own hierarchy (enforced)
from abc import ABC, abstractmethod

class BaseProcessor(ABC):
    @abstractmethod
    def process(self, data):
        pass

class CsvProcessor(BaseProcessor):
    def process(self, data):
        # Must implement or instantiation fails
        ...
```

**In the demo ETL project**, you'll see Protocols used for `FileReader[T]` to allow flexible implementations without forcing inheritance.

---

**Navigation:**
- **Previous**: [← Object-Oriented Python](01-object-oriented-python.md)
- **Next**: [Composition Over Inheritance →](03-composition-over-inheritance.md)
- **Home**: [Python Essentials](../README.md)
