# FastAPI Demo App

A self-contained product catalog API that demonstrates the FastAPI and Pydantic concepts from the Web APIs lesson. No database setup required — all data is stored in memory while the server is running.

## What's in This App

| Route | Method | What it does |
|-------|--------|-------------|
| `/` | GET | Lists all available routes |
| `/products` | GET | Lists all products (add `?category=electronics` to filter) |
| `/products/{id}` | GET | Returns one product by ID, 404 if not found |
| `/orders` | POST | Places an order: validates stock, deducts inventory, returns receipt |
| `/orders` | GET | Lists all orders placed this session |
| `/orders/{id}` | GET | Returns one order by ID |

## Run

Start the web lab (`make lab-web`), then from inside the workspace:

```bash
uvicorn main:app --reload
```

The `--reload` flag restarts the server automatically when you edit `main.py`.

## Try It

Once running, open **http://localhost:8000/docs** in your browser. You'll see the Swagger UI with all endpoints listed.

### Things to try in Swagger UI

**1. Browse products**

`GET /products` → expand and click "Try it out" → Execute. You'll see 6 products across three categories.

**2. Filter by category**

`GET /products` → Try it out → set `category` to `electronics` → Execute.

**3. Get a product that doesn't exist**

`GET /products/{product_id}` → Try it out → set `product_id` to `999` → Execute. Observe the `404` response.

**4. Place a valid order**

`POST /orders` → Try it out → paste this body:

```json
{
  "customer_name": "Alice",
  "items": [
    { "product_id": 1, "quantity": 2 },
    { "product_id": 5, "quantity": 1 }
  ]
}
```

Observe the `201` response with the full receipt including line items and total. Then `GET /products/1` to confirm the stock decreased from 10 to 8.

**5. Trigger a stock error**

Try to order 100 units of product 1 (only 8 left after step 4):

```json
{
  "customer_name": "Bob",
  "items": [{ "product_id": 1, "quantity": 100 }]
}
```

Observe the `400` response: `Insufficient stock for 'Laptop Pro 16': requested 100, available 8`.

**6. Trigger a validation error**

Send an order with `quantity: 0`:

```json
{
  "customer_name": "Charlie",
  "items": [{ "product_id": 2, "quantity": 0 }]
}
```

Observe the `422 Unprocessable Entity` response from Pydantic validation — `quantity must be at least 1`.

## What to Notice

- **Pydantic validation fires before your code** — a `422` response means the request body was malformed. FastAPI handles this automatically.
- **`response_model` shapes the output** — the route for `GET /products` returns raw dicts internally, but FastAPI filters and validates them through `ProductResponse` before sending.
- **Stock is shared state** — place two orders and check that stock decrements accumulate. Restart the server to reset.
- **Swagger UI is auto-generated** — you didn't write any documentation. FastAPI generated it from your type hints and docstrings.
