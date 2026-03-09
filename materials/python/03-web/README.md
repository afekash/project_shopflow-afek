# Web APIs for Data Engineers

A focused introduction to HTTP APIs, FastAPI, and Pydantic. This module covers just enough to understand how web frameworks work and how data flows from an HTTP request into your database code.

**Total Duration:** ~25 minutes

```{note}
This module requires the web lab. Run `make lab-web` before starting.
```

## Learning Objectives

By the end of this module, you will:

- Understand what an HTTP API is and how a web framework maps URLs to Python functions
- Read and understand a FastAPI route handler and a Pydantic model
- Know how the scaffolded API layer in the capstone project calls your `DBAccess` methods

## Prerequisites

- Python type hints (`int`, `str`, `list[str]`, etc.)
- Dataclasses (`@dataclass`, fields, types)
- Basic Python OOP (classes, methods)

## Learning Path

| Lesson | Duration | Topics | Key Concepts |
|--------|----------|--------|--------------|
| [01 - How Web APIs Work](01-how-web-apis-work.md) | ~5 min | HTTP basics | Client-server, GET/POST, status codes, JSON |
| [02 - Running a Real Server](02-running-a-real-server.md) | ~5 min | uvicorn, live server | ASGI, uvicorn, port binding, Swagger UI |
| [03 - FastAPI Routes](03-fastapi-routes.md) | ~10 min | Building endpoints | Decorators, path params, query params, POST body, Swagger UI |
| [04 - Pydantic Models](04-pydantic-models.md) | ~7 min | Input validation | BaseModel, ValidationError, nested models, response_model |
| [05 - Connecting to the Project](05-connecting-to-the-project.md) | ~5 min | Project context | Full request flow, what's scaffolded, where DBAccess fits |

**Total:** ~32 minutes

## Course Navigation

- **Previous**: [Python Essentials ←](../02-python-essentials/README.md)
- **Course Home**: [Data Engineering Course](../../README.md)
