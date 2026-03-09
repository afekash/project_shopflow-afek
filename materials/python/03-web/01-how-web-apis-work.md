---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# How Web APIs Work

```{note}
This lesson requires the web lab. Run `make lab-web` before starting.
```

You've spent this course working with databases directly — connecting, querying, closing. But in a real application, database calls are triggered by HTTP requests from a client. Before writing any FastAPI code, let's understand the model it's built on.

## The Client-Server Model

A web API is a program that listens on a network address for incoming requests and sends back responses. The client (a browser, a mobile app, a test script) speaks the same language as the server: HTTP.

```
┌──────────────────────┐                    ┌────────────────────────┐
│  Client              │   HTTP Request      │  Server (FastAPI)      │
│                      │  ─────────────────▶ │                        │
│  - Browser           │                    │  Receives the request  │
│  - Swagger UI        │   HTTP Response     │  Calls your Python fn  │
│  - Test script       │  ◀───────────────── │  Returns the result    │
└──────────────────────┘                    └────────────────────────┘
```

Every request specifies two things:

- **Method** — the type of action. `GET` reads data, `POST` creates data.
- **Path** — the URL path that identifies the resource, like `/products` or `/orders/42`.

## Endpoints

An **endpoint** is the combination of a method and a path. `GET /products` and `POST /products` are two different endpoints even though they share a path.

In FastAPI, each endpoint maps to exactly one Python function. When the server receives `GET /products`, it calls your function and returns what the function returns. The whole job of a web framework is to make that wiring easy.

## HTTP Status Codes

Every response carries a numeric status code:

| Code | Meaning |
|------|---------|
| `200` | OK — request succeeded |
| `201` | Created — a new resource was created |
| `404` | Not Found — the resource doesn't exist |
| `422` | Unprocessable — the request body failed validation |

FastAPI sets the right code automatically based on what you return or what exception you raise.

## JSON: The Data Format

Requests and responses carry data as JSON. A client sends a JSON body when creating a resource; the server responds with a JSON body representing the result.

```
POST /orders
Content-Type: application/json

{
  "customer_id": 7,
  "items": [
    { "product_id": 1, "quantity": 2 },
    { "product_id": 3, "quantity": 1 }
  ]
}
```

The server parses that JSON into Python objects, calls your function, and serializes the return value back to JSON for the response.

## Seeing It in Practice

The `TestClient` from FastAPI lets you send real HTTP requests in-process — no running server needed. Here's the entire request cycle visible at once:

```{code-cell} python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/products")
def list_products():
    return [
        {"id": 1, "name": "Laptop Pro", "price": 1299.99},
        {"id": 2, "name": "Wool Sweater", "price": 49.99},
    ]

client = TestClient(app)
response = client.get("/products")

print("Status code:", response.status_code)   # 200
print("Body:", response.json())
```

The `response.status_code` is `200` because the function returned normally. The body is the list serialized to JSON — FastAPI handles that automatically.

```{code-cell} python
from fastapi import HTTPException

@app.get("/products/{product_id}")
def get_product(product_id: int):
    products = {1: {"id": 1, "name": "Laptop Pro", "price": 1299.99}}
    if product_id not in products:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return products[product_id]

response = client.get("/products/999")
print("Status code:", response.status_code)   # 404
print("Body:", response.json())               # {'detail': 'Product 999 not found'}
```

## Summary

| Concept | Meaning |
|---------|---------|
| HTTP method | The action type: `GET` reads, `POST` creates |
| Path | The URL segment that identifies a resource |
| Endpoint | A method + path pair, mapped to one Python function |
| Status code | Numeric result: 200 OK, 404 Not Found, etc. |
| JSON | The data format for both requests and responses |

**Navigation:**
- **Next**: [Running a Real Server →](02-running-a-real-server.md)
- **Home**: [Web APIs Module](README.md)
