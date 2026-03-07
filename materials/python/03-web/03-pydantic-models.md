---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Pydantic Models

```{note}
This lesson requires the web lab. Run `make lab-web` before starting.
```

Pydantic's `BaseModel` looks almost identical to a Python dataclass but adds one critical feature: it validates that the data you pass actually matches the declared types. FastAPI uses Pydantic to parse incoming request bodies — if the JSON doesn't match the model, the request is rejected with a clear error before your code runs.

## Dataclass vs BaseModel

The syntax is nearly the same, but the behavior on bad input is very different:

```{code-cell} python
from dataclasses import dataclass
from pydantic import BaseModel

# Standard dataclass: no runtime validation
@dataclass
class OrderItemDC:
    product_id: int
    quantity: int

bad = OrderItemDC(product_id="not-a-number", quantity=2)
print(type(bad.product_id))   # <class 'str'>  — silently accepted!

# Pydantic model: validates on creation
class OrderItemPM(BaseModel):
    product_id: int
    quantity: int

good = OrderItemPM(product_id=1, quantity=2)
print(type(good.product_id))  # <class 'int'>
```

The dataclass stores whatever you pass. Pydantic coerces compatible types (e.g. the string `"1"` becomes `1`) and rejects incompatible ones.

## Validation Errors

When input can't be converted to the declared type, Pydantic raises a `ValidationError` with a clear description of every problem:

```{code-cell} python
from pydantic import BaseModel, ValidationError

class OrderItemPM(BaseModel):
    product_id: int
    quantity: int

try:
    item = OrderItemPM(product_id="abc", quantity=-1)
except ValidationError as e:
    print(e)
# 1 validation error for OrderItemPM
# product_id
#   Input should be a valid integer, unable to parse string as an integer [...]
```

In FastAPI, this `ValidationError` is automatically caught and turned into a `422 Unprocessable Entity` HTTP response — the client sees a JSON error message, and your route function is never invoked.

## Nested Models

Models can contain other models. This is how you represent structured request payloads:

```{code-cell} python
from pydantic import BaseModel

class OrderItem(BaseModel):
    product_id: int
    quantity: int

class CreateOrderRequest(BaseModel):
    customer_id: int
    items: list[OrderItem]

order = CreateOrderRequest(
    customer_id=7,
    items=[
        {"product_id": 1, "quantity": 2},
        {"product_id": 3, "quantity": 1},
    ],
)
print(order.customer_id)           # 7
print(order.items[0].product_id)   # 1
print(order.items[0].quantity)     # 2
```

The dicts in the `items` list are automatically converted to `OrderItem` instances. You don't call the constructor yourself — Pydantic handles the nesting.

## Optional Fields and Defaults

Fields can have default values. A field typed as `type | None` with a default of `None` is optional — the client may omit it:

```{code-cell} python
from pydantic import BaseModel

class ProductFilter(BaseModel):
    category: str | None = None
    max_price: float | None = None
    in_stock_only: bool = False

f1 = ProductFilter()
print(f1.category)       # None
print(f1.in_stock_only)  # False

f2 = ProductFilter(category="electronics", in_stock_only=True)
print(f2.category)       # electronics
print(f2.in_stock_only)  # True
```

## Using Pydantic Models in FastAPI

Pydantic models serve two roles in FastAPI.

**Request body** — declare the model as a function parameter, and FastAPI parses the request body into it:

```{code-cell} python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

app = FastAPI()

class OrderItem(BaseModel):
    product_id: int
    quantity: int

class CreateOrderRequest(BaseModel):
    customer_id: int
    items: list[OrderItem]

@app.post("/orders")
def create_order(order: CreateOrderRequest):
    total_items = sum(i.quantity for i in order.items)
    return {"customer_id": order.customer_id, "total_items": total_items}

client = TestClient(app)
response = client.post("/orders", json={
    "customer_id": 7,
    "items": [{"product_id": 1, "quantity": 3}, {"product_id": 2, "quantity": 1}],
})
print(response.json())
# {'customer_id': 7, 'total_items': 4}
```

**Response model** — pass a model to `response_model` and FastAPI validates *and* filters the response, stripping any fields the model doesn't declare:

```{code-cell} python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

app = FastAPI()

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float

@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    return {"id": product_id, "name": "Laptop Pro", "price": 1299.99, "internal_cost": 800.0}

client = TestClient(app)
response = client.get("/products/1")
print(response.json())
# {'id': 1, 'name': 'Laptop Pro', 'price': 1299.99}
# Note: 'internal_cost' is stripped — it's not in ProductResponse
```

In the capstone project, all Pydantic models are pre-defined in `src/models/requests.py` and `src/models/responses.py`. Your `DBAccess` methods receive the already-parsed values as plain Python types (`int`, `str`, `list`). You never instantiate a Pydantic model yourself.

**Navigation:**
- **Previous**: [← FastAPI Routes](02-fastapi-routes.md)
- **Next**: [Connecting to the Project →](04-connecting-to-the-project.md)
- **Home**: [Web APIs Module](README.md)
