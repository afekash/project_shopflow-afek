# Python Essentials for Data Engineering

A comprehensive lesson covering Python fundamentals essential for data engineering work: project setup, data structures, object-oriented programming, and type systems.

## Learning Objectives

By the end of this lesson, you will:

- Set up Python projects with modern tooling (pip and uv)
- Choose appropriate data structures for different scenarios
- Apply object-oriented patterns to organize data processing code
- Use type hints and generics to write maintainable, type-safe code
- Build a complete ETL application demonstrating these concepts

## Prerequisites

- Python 3.10+ installed on your system
- Basic Python syntax knowledge (variables, functions, loops)
- Familiarity with command-line operations

## Learning Path

| Section | Topic | Duration | Key Concepts |
|---------|-------|----------|--------------|
| **1. Project Setup** | | 40 min | |
| 1.1 | [Creating a Python Project](01-project-setup/01-creating-a-python-project.md) | 20 min | Virtual environments, project layout, running scripts |
| 1.2 | [Dependency Management](01-project-setup/02-dependency-management.md) | 20 min | pip vs uv, lockfiles, production deployment |
| **2. Data Structures** | | 55 min | |
| 2.1 | [Primitive Types](02-data-structures/01-primitive-types.md) | 20 min | int, float, bool, str, None |
| 2.2 | [Collections](02-data-structures/02-collections.md) | 35 min | list, tuple, dict, set with performance trade-offs |
| **3. Object-Oriented Python** | | 65 min | |
| 3.1 | [OOP Fundamentals](03-oop/01-object-oriented-python.md) | 30 min | Classes, inheritance, dataclasses |
| 3.2 | [Interfaces in Python](03-oop/02-interfaces-in-python.md) | 15 min | Abstract Base Classes vs Protocols |
| 3.3 | [Composition Over Inheritance](03-oop/03-composition-over-inheritance.md) | 20 min | When to compose instead of inherit |
| **4. Type Systems** | | 40 min | |
| 4.1 | [Type Hints](04-typing/01-type-hints.md) | 20 min | Basic types, collections, mypy |
| 4.2 | [Generics](04-typing/02-generics.md) | 20 min | TypeVar, Generic classes, Protocol |
| **5. Practice** | | 30 min | |
| 5.1 | [Exercises](05-exercises/01-python-essentials-exercises.md) | 20 min | Hands-on practice with all concepts |
| | [Demo ETL Project](demo-app/file-etl/) | 10 min | Complete working example |

**Total**: ~4 hours (240 minutes including breaks)

## Quick Start

All lesson materials are written as Jupytext-compatible Markdown. Each Python code block is executable as a notebook cell.

To convert markdown files to Jupyter notebooks, run:

**Run this in your terminal:**

```bash
# If you have jupytext installed
jupytext --to notebook materials/python/02-python-essentials/**/*.md
```

Or open the markdown files directly in VS Code with the Jupyter extension.

## Demo Application

The `demo-app/file-etl/` directory contains a complete ETL project that demonstrates all concepts from this lesson:

- Modern project setup with `uv`
- Typed data models using dataclasses
- Generic reader interfaces for CSV and JSON
- SQL Server loader with proper error handling
- Type-safe pipeline orchestration

See the [demo app README](demo-app/file-etl/README.md) for setup and usage instructions.

## Course Navigation

- **Next**: [Creating a Python Project →](01-project-setup/01-creating-a-python-project.md)
- **Course Home**: [Data Engineering Course](../../README.md)
