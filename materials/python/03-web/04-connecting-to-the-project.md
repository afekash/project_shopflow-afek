---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Connecting to the Project

Now that you understand endpoints, routes, and Pydantic models, here's how the capstone project uses them — and exactly where your code fits in.

## The Full Request Flow

When you (or a test) submit an order through Swagger UI, here's what happens:

```
Browser / Swagger UI
       │
       │  POST /orders
       │  { "customer_id": 7, "items": [{"product_id": 1, "quantity": 2}] }
       ▼
FastAPI route handler          ◀── pre-built in src/api/routes/orders.py
       │
       │  1. Parses JSON → CreateOrderRequest (Pydantic)
       │  2. Validates all fields (customer_id is int, items is a list, etc.)
       │  3. Calls db.create_order(customer_id, items)
       ▼
DBAccess.create_order()        ◀── YOU IMPLEMENT THIS
       │
       ├──▶  PostgreSQL    check inventory, create order row + items (ACID)
       ├──▶  MongoDB       save denormalized order snapshot
       ├──▶  Redis         decrement inventory counter
       └──▶  Neo4j         add BOUGHT_TOGETHER edges
       │
       ▼
FastAPI serializes the return value → JSON response → back to client
```

The web layer handles steps 1–3 automatically. Your job starts at `DBAccess.create_order()`.

## What the Scaffolded Route Looks Like

Here's a simplified version of the `POST /orders` handler from `src/api/routes/orders.py`. Read through it — you'll recognize all the pieces:

```{code-cell} python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

# --- Models (pre-built in src/models/requests.py) ---

class OrderItem(BaseModel):
    product_id: int
    quantity: int

class CreateOrderRequest(BaseModel):
    customer_id: int
    items: list[OrderItem]

# --- Your class (db_access.py) ---

class DBAccess:
    def create_order(self, customer_id: int, items: list[dict]) -> dict:
        raise NotImplementedError("implement me")

# --- Route handler (pre-built in src/api/routes/orders.py) ---

app = FastAPI()
db = DBAccess()

@app.post("/orders")
def create_order_route(order: CreateOrderRequest):
    result = db.create_order(
        customer_id=order.customer_id,
        items=[{"product_id": i.product_id, "quantity": i.quantity} for i in order.items],
    )
    return result

client = TestClient(app)
try:
    client.post("/orders", json={"customer_id": 7, "items": [{"product_id": 1, "quantity": 2}]})
except NotImplementedError:
    print("Route reached DBAccess — wiring works, method not yet implemented")
```

The HTTP layer, Pydantic parsing, and routing are invisible to you. You only implement the body of `create_order()`.

## Other Routes You'll Drive Through

Every `DBAccess` method you implement is called by a corresponding pre-built route:

| Route | Handler calls | You implement |
|-------|--------------|---------------|
| `GET /products` | `db.get_products(category)` | Reads from MongoDB (or Redis cache) |
| `GET /products/{id}` | `db.get_product(product_id)` | Cache-aside: Redis → MongoDB |
| `POST /orders` | `db.create_order(customer_id, items)` | Writes to all four databases |
| `GET /orders/{id}` | `db.get_order(order_id)` | Reads from MongoDB snapshots |
| `GET /customers/{id}/orders` | `db.get_customer_order_history(customer_id)` | Reads from MongoDB |
| `GET /products/{id}/recommendations` | `db.get_recommendations(product_id)` | Traverses Neo4j graph |
| `GET /customers/{id}/recently-viewed` | `db.get_recently_viewed(customer_id)` | Reads Redis list |

## What's Scaffolded vs What You Build

| Layer | Scaffolded? | Where |
|-------|-------------|-------|
| FastAPI app and lifecycle | Yes | `src/api/app.py` |
| All route handlers | Yes | `src/api/routes/` |
| All Pydantic models | Yes | `src/models/` |
| Database connection setup | Yes | `src/db.py` |
| Test suites | Yes | `tests/` |
| SQLAlchemy ORM models | **You build** | `src/postgres_models.py` |
| All `DBAccess` methods | **You build** | `src/db_access.py` |

**Navigation:**
- **Previous**: [← Pydantic Models](03-pydantic-models.md)
- **Home**: [Web APIs Module](README.md)
