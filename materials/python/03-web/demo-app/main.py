"""
FastAPI Demo: Mini Product Catalog

A self-contained FastAPI application that demonstrates all concepts from the
Web APIs lesson. No database required -- all data lives in memory.

Run:
    uvicorn main:app --reload

Then open:
    http://localhost:8000/docs   ← interactive Swagger UI
    http://localhost:8000        ← API root with available routes
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

app = FastAPI(
    title="Product Catalog Demo",
    description="A minimal e-commerce API demonstrating FastAPI and Pydantic. "
                "All data is in-memory -- no database needed.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# In-memory data store
# ---------------------------------------------------------------------------

_products: list[dict] = [
    {"id": 1, "name": "Laptop Pro 16", "price": 1299.99, "stock": 10, "category": "electronics"},
    {"id": 2, "name": "Wireless Mouse", "price": 29.99,  "stock": 50, "category": "electronics"},
    {"id": 3, "name": "Wool Sweater",   "price": 49.99,  "stock": 25, "category": "clothing"},
    {"id": 4, "name": "Running Shoes",  "price": 89.99,  "stock": 15, "category": "clothing"},
    {"id": 5, "name": "Python Cookbook","price": 39.99,  "stock": 30, "category": "books"},
    {"id": 6, "name": "Clean Code",     "price": 34.99,  "stock": 20, "category": "books"},
]

_orders: list[dict] = []
_next_order_id = 1


def _find_product(product_id: int) -> dict | None:
    return next((p for p in _products if p["id"] == product_id), None)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    category: str


class OrderItem(BaseModel):
    product_id: int
    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("quantity must be at least 1")
        return v


class CreateOrderRequest(BaseModel):
    customer_name: str
    items: list[OrderItem]


class OrderLineItem(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float


class OrderResponse(BaseModel):
    order_id: int
    customer_name: str
    items: list[OrderLineItem]
    total: float
    status: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Product Catalog Demo API",
        "docs": "http://localhost:8000/docs",
        "endpoints": [
            "GET  /products                  -- list all products",
            "GET  /products?category=books   -- filter by category",
            "GET  /products/{id}             -- get one product",
            "POST /orders                    -- place an order",
            "GET  /orders                    -- list all orders",
            "GET  /orders/{id}              -- get one order",
        ],
    }


@app.get("/products", response_model=list[ProductResponse])
def list_products(category: str | None = None):
    """
    Return all products. Pass ?category=electronics (or clothing, books)
    to filter by category.
    """
    if category:
        filtered = [p for p in _products if p["category"] == category]
        if not filtered:
            raise HTTPException(status_code=404, detail=f"No products found in category '{category}'")
        return filtered
    return _products


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    """Return a single product by ID."""
    product = _find_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return product


@app.post("/orders", response_model=OrderResponse, status_code=201)
def create_order(order: CreateOrderRequest):
    """
    Place an order. Each item must reference an existing product with
    sufficient stock. Stock is decremented on success.
    """
    global _next_order_id

    line_items: list[dict] = []
    total = 0.0

    for item in order.items:
        product = _find_product(item.product_id)
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item.product_id} not found",
            )
        if product["stock"] < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{product['name']}': "
                       f"requested {item.quantity}, available {product['stock']}",
            )
        subtotal = round(product["price"] * item.quantity, 2)
        line_items.append({
            "product_id": product["id"],
            "product_name": product["name"],
            "quantity": item.quantity,
            "unit_price": product["price"],
            "subtotal": subtotal,
        })
        total += subtotal
        product["stock"] -= item.quantity  # decrement in-memory stock

    order_record = {
        "order_id": _next_order_id,
        "customer_name": order.customer_name,
        "items": line_items,
        "total": round(total, 2),
        "status": "confirmed",
    }
    _orders.append(order_record)
    _next_order_id += 1
    return order_record


@app.get("/orders", response_model=list[OrderResponse])
def list_orders():
    """Return all orders placed since the server started."""
    return _orders


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int):
    """Return a single order by ID."""
    order = next((o for o in _orders if o["order_id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return order
