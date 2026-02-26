# FastAPI Routes

FastAPI turns a regular Python function into an HTTP endpoint with a single decorator. This file shows how that works, covering the patterns you'll see in the scaffolded project code.

## Setup

```bash
pip install fastapi "uvicorn[standard]" httpx
```

## Your First Route

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/products")
def list_products():
    return [
        {"id": 1, "name": "Laptop Pro", "price": 1299.99},
        {"id": 2, "name": "Wool Sweater", "price": 49.99},
    ]
```

`@app.get("/products")` registers `list_products` as the handler for `GET /products`. Whatever the function returns is automatically serialized to JSON. That's the whole model -- a decorator maps a URL to a function.

To start the server from the command line:

```bash
uvicorn main:app --reload
```

Then open `http://localhost:8000/products` in a browser, or `http://localhost:8000/docs` for the interactive Swagger UI.

## Running Routes in a Notebook

Since a running server isn't practical inside a notebook, FastAPI ships with a `TestClient` that sends requests in-process. Use it whenever you want to run route code without starting a server:

```python
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
print(response.status_code)  # Result: 200
print(response.json())
# Result: [{'id': 1, 'name': 'Laptop Pro', 'price': 1299.99}, {'id': 2, 'name': 'Wool Sweater', 'price': 49.99}]
```

The `TestClient` approach is identical in behavior to a real HTTP client -- it just skips the network.

## Path Parameters

To capture a value from the URL, wrap it in curly braces in the path string and add a matching typed parameter to the function:

```python
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

products = {
    1: {"id": 1, "name": "Laptop Pro", "price": 1299.99},
    2: {"id": 2, "name": "Wool Sweater", "price": 49.99},
}

app = FastAPI()

@app.get("/products/{product_id}")
def get_product(product_id: int):
    if product_id not in products:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return products[product_id]

client = TestClient(app)

response = client.get("/products/1")
print(response.json())  # Result: {'id': 1, 'name': 'Laptop Pro', 'price': 1299.99}

response = client.get("/products/99")
print(response.status_code)   # Result: 404
print(response.json())        # Result: {'detail': 'Product 99 not found'}
```

FastAPI uses the `int` type hint to convert the URL string automatically. If the caller passes `/products/abc`, FastAPI returns `422 Unprocessable` before your function is even called.

`HTTPException` is how you signal an error response. Raise it with a status code and a message -- FastAPI formats the JSON response.

## Query Parameters

Parameters added to the function signature that are *not* in the path become query parameters (the `?key=value` part of a URL):

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

all_products = [
    {"id": 1, "name": "Laptop Pro", "category": "electronics"},
    {"id": 2, "name": "Wool Sweater", "category": "clothing"},
    {"id": 3, "name": "Python Cookbook", "category": "books"},
]

app = FastAPI()

@app.get("/products")
def list_products(category: str = None):
    if category:
        return [p for p in all_products if p["category"] == category]
    return all_products

client = TestClient(app)

response = client.get("/products?category=clothing")
print(response.json())
# Result: [{'id': 2, 'name': 'Wool Sweater', 'category': 'clothing'}]

response = client.get("/products")
print(len(response.json()))  # Result: 3
```

## POST: Receiving Data

A `POST` route receives data in the request body. Declare a Pydantic model for the expected shape and FastAPI will parse and validate the incoming JSON automatically:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

app = FastAPI()

class CreateOrderRequest(BaseModel):
    customer_id: int
    items: list[dict]

@app.post("/orders")
def create_order(order: CreateOrderRequest):
    return {
        "status": "created",
        "customer_id": order.customer_id,
        "item_count": len(order.items),
    }

client = TestClient(app)
response = client.post("/orders", json={
    "customer_id": 7,
    "items": [{"product_id": 1, "quantity": 2}],
})
print(response.json())
# Result: {'status': 'created', 'customer_id': 7, 'item_count': 1}
```

FastAPI sees that `order` is typed as `CreateOrderRequest` (a Pydantic model) and treats it as a request body -- not a path or query parameter.

## Swagger UI

When the server is running, FastAPI auto-generates a fully interactive API browser at `http://localhost:8000/docs`. It lists every route, shows the expected JSON shape for request bodies, and lets you send real requests and see real responses without writing a single line of client code.

In the capstone project, Swagger UI is your primary tool for manually testing your `DBAccess` methods end-to-end. Start the server, open `/docs`, and try placing an order -- your implementation handles what happens next.

**Navigation:**
- **Previous**: [← How Web APIs Work](01-how-web-apis-work.md)
- **Next**: [Pydantic Models →](03-pydantic-models.md)
- **Home**: [Web APIs Module](README.md)
