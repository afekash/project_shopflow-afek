---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Running a Real Server

```{note}
This lesson requires the web lab. Run `make lab-web` before starting.
```

The `TestClient` you saw in the intro is convenient for testing, but it never binds a port. Real deployments run through **uvicorn** — an ASGI server that actually listens on TCP, accepts connections, and hands requests to your FastAPI app.

## What uvicorn does

```
┌──────────────────┐    TCP :8000    ┌────────────────┐    ASGI    ┌─────────────────┐
│  Browser / curl  │ ──────────────▶ │    uvicorn     │ ─────────▶ │  FastAPI app    │
│                  │ ◀────────────── │  (HTTP server) │ ◀───────── │  (your routes)  │
└──────────────────┘                 └────────────────┘            └─────────────────┘
```

FastAPI speaks ASGI — a Python interface for async web servers. uvicorn implements the server side of that interface. You never interact with uvicorn directly in your application code; you just point it at the app object and it does the rest.

## Starting a server from a notebook cell

Write a small app to disk and start uvicorn in the background:

```{code-cell} python
%%bash
cat > /tmp/demo_app.py << 'EOF'
from fastapi import FastAPI

app = FastAPI()

PRODUCTS = [
    {"id": 1, "name": "Laptop Pro", "price": 1299.99},
    {"id": 2, "name": "Wool Sweater", "price": 49.99},
    {"id": 3, "name": "Coffee Grinder", "price": 89.00},
]

@app.get("/products")
def list_products():
    return PRODUCTS

@app.get("/products/{product_id}")
def get_product(product_id: int):
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
EOF

# Start uvicorn in the background, redirect logs to a file
uvicorn demo_app:app --app-dir /tmp --host 0.0.0.0 --port 8000 > /tmp/uvicorn.log 2>&1 &
echo "uvicorn PID: $!"
sleep 1
cat /tmp/uvicorn.log
```

Once the cell runs you can open these URLs in your browser:

- **`http://localhost:8000/products`** — returns the full product list as JSON
- **`http://localhost:8000/products/1`** — returns a single product
- **`http://localhost:8000/docs`** — the auto-generated Swagger UI, fully interactive

FastAPI generates that Swagger UI from your route definitions and type hints with no extra work on your part.

## Stopping the server

When you're done, stop uvicorn so the port is free again:

```{code-cell} python
%%bash
pkill -f "uvicorn demo_app:app" && echo "server stopped" || echo "server was not running"
```

## How this maps to production

In production you start uvicorn from the command line or a process manager:

```bash
uvicorn myapp.main:app --host 0.0.0.0 --port 8000 --workers 4
```

For higher-traffic services, Gunicorn manages a pool of uvicorn worker processes:

```bash
gunicorn myapp.main:app -k uvicorn.workers.UvicornWorker --workers 4
```

The FastAPI code is identical either way — uvicorn and Gunicorn are infrastructure concerns that sit outside your application.

## TestClient for everything else in this course

Keeping a real server running inside a Jupyter kernel adds noise: you have to manage processes, wait for startup, and clean up ports. For learning and testing, `TestClient` gives you the same HTTP semantics — real request parsing, real status codes, real validation — without any of that overhead.

All remaining exercises in this module use `TestClient`. When you ship to production, swap it for uvicorn. That's the only difference.

**Navigation:**
- **Previous**: [How Web APIs Work ←](01-how-web-apis-work.md)
- **Next**: [FastAPI Routes →](03-fastapi-routes.md)
- **Home**: [Web APIs Module](README.md)
