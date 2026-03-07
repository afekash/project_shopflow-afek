---
kernelspec:
  name: python3
  language: python
  display_name: Python 3
---

# Interface Specification: E-Commerce Polyglot Data Pipeline

This document is the contract between the scaffold and the test/seed agents. It defines:

- All application use cases (one per access pattern demonstrated)
- Every `DBAccess` method signature, parameter types, return shapes, and side effects
- All API endpoints and their request/response models
- The Postgres schema (all tables, columns, constraints)
- MongoDB collection shapes
- Redis key patterns
- Neo4j graph schema

Do not implement anything not listed here without discussing with the instructor first.

---

## Use Cases

Each use case demonstrates why a specific database is the right tool for that access pattern.

### UC1 — Place an Order (PostgreSQL: ACID Transaction)

The defining Postgres use case. Placing an order must atomically:
1. Validate that every requested product has sufficient stock
2. Create the `orders` row
3. Create all `order_items` rows
4. Decrement `stock_quantity` for each product

If any product has insufficient stock, the entire transaction rolls back — no partial order, no inventory leak. This is why Postgres is the source of truth.

After the Postgres transaction succeeds, best-effort secondary writes go to:
- **Phase 1:** MongoDB — save a denormalized order snapshot
- **Phase 2:** Redis — `DECR` inventory counters
- **Phase 3:** Neo4j — `MERGE` co-purchase edges between all products in the order

If any secondary write fails, the order is still valid. The error is logged, not raised.

**DBAccess method:** `create_order`
**API endpoint:** `POST /orders`

---

### UC2 — Revenue by Category (PostgreSQL: SQL Aggregation)

An analytical query that JOINs `orders`, `order_items`, and `products` to compute total revenue per product category. Demonstrates why a normalized relational schema with typed columns is the right tool for aggregations — `GROUP BY` and `SUM` work naturally across all categories without any conditional logic.

**DBAccess method:** `revenue_by_category`
**API endpoint:** `GET /analytics/revenue-by-category`

---

### UC3 — Get Product (MongoDB: Denormalized Single Read)

Fetch a complete product document — with all category-specific fields — in a single read. An electronics product has `category_fields.cpu`, `category_fields.ram_gb` inline. A clothing product has `category_fields.sizes` as an array. No joins, no conditional table selection.

In Phase 2, this method gains a Redis cache-aside layer transparently: check Redis first, on cache miss fetch from MongoDB and store with a 300-second TTL.

Contrasts directly with UC5 (the Postgres relational version of the same operation) to make the polyglot trade-off tangible.

**DBAccess method:** `get_product`
**API endpoint:** `GET /products/{product_id}`

---

### UC4 — Order Snapshot Lifecycle (MongoDB: Denormalized Snapshots)

When an order is placed, a denormalized snapshot is written to MongoDB with the customer name/email and product names/prices embedded at the time of purchase. If a product's name or price changes later, the snapshot preserves the original values.

Retrieving a customer's order history is a single MongoDB query — no joins across four tables as you would need in Postgres.

**DBAccess methods:** `save_order_snapshot` (called internally by `create_order`), `get_order_history`, `get_order`
**API endpoints:** `GET /customers/{customer_id}/orders`, `GET /orders/{order_id}`

---

### UC5 — Search Products (MongoDB: Flexible Query)

Filter the product catalog by category and/or a text search on product name. All five product categories live in a single MongoDB collection — no need to UNION across category-specific tables as you would in Postgres.

**DBAccess method:** `search_products`
**API endpoint:** `GET /products?category=...&q=...`

---

### UC6 — Product Cache (Redis: Cache-Aside + Invalidation)

Read-heavy product detail pages benefit from sub-millisecond Redis reads. The cache-aside pattern:
1. Check Redis key `product:{product_id}`
2. On hit: return cached dict (deserialized from JSON)
3. On miss: fetch from MongoDB, serialize to JSON, `SET` in Redis with `EX 300`, return

When product data changes in MongoDB, actively `DEL` the Redis key so the next read fetches fresh data.

This behavior is transparent to the route layer — `get_product` always returns the same shape regardless of whether the data came from Redis or MongoDB.

**DBAccess methods:** cache-aside integrated into `get_product`, `invalidate_product_cache`
**API endpoint:** transparent — no new endpoint, behavior of `GET /products/{product_id}` changes in Phase 2

---

### UC7 — Recently Viewed Products (Redis: List Data Structure)

Per-customer list of recently viewed product IDs, maintained with Redis List operations:
- `LPUSH recently_viewed:{customer_id} {product_id}` — prepend to head
- `LTRIM recently_viewed:{customer_id} 0 9` — cap at 10 entries
- `LRANGE recently_viewed:{customer_id} 0 9` — retrieve in order (most recent first)

Demonstrates atomic list operations as a natural fit for an ordered, bounded per-user data structure.

**DBAccess methods:** `record_product_view`, `get_recently_viewed`
**API endpoints:** `POST /customers/{customer_id}/viewed/{product_id}`, `GET /customers/{customer_id}/recently-viewed`

---

### UC8 — Product Recommendations (Neo4j: Graph Traversal)

"Customers who bought X also bought Y." The recommendation graph is built by processing historical orders: for each order containing products A, B, C, create `BOUGHT_TOGETHER` edges A↔B, A↔C, B↔C and increment their `weight` property. A Cypher traversal returns the highest-weight neighbors of any product node.

The equivalent SQL would be a self-join on `order_items` — feasible for 1 hop but exponentially complex for 2+ hops. The Cypher query handles multi-hop traversal with a simple path length parameter.

**DBAccess methods:** `seed_recommendation_graph`, `get_recommendations`
**API endpoint:** `GET /products/{product_id}/recommendations?limit=5`

---

## DBAccess Method Signatures

All methods return plain Python dicts (not Pydantic models). The route layer handles serialization.

Business rule violations raise `ValueError`. Missing resources return `None` (single-item methods) or `[]` (list methods). Unimplemented phase methods raise `NotImplementedError("Phase N: implement <method_name>")`.

### Constructor

```{code-cell} python
class DBAccess:
    def __init__(
        self,
        pg_session_factory,   # sqlalchemy.orm.sessionmaker bound to Postgres engine
        mongo_db,             # pymongo.database.Database
        redis_client=None,    # redis.Redis | None  (None until Phase 2)
        neo4j_driver=None,    # neo4j.Driver | None (None until Phase 3)
    ) -> None:
```

---

### Phase 1 Methods

#### `create_order`

```{code-cell} python
def create_order(self, customer_id: int, items: list[dict]) -> dict:
```

**Input `items` shape:**
```{code-cell} python
[{"product_id": int, "quantity": int}, ...]
```

**Returns:**
```{code-cell} python
{
    "order_id": int,
    "customer_id": int,
    "status": "completed",
    "total_amount": float,      # sum of quantity * unit_price across all items
    "created_at": str,          # ISO 8601, e.g. "2024-03-15T10:30:00"
    "items": [
        {
            "product_id": int,
            "product_name": str,
            "quantity": int,
            "unit_price": float # price at time of order (from products.price)
        },
        ...
    ]
}
```

**Side effects — Postgres (all in one `session.begin()` transaction):**
- `SELECT` each product row with a lock to read current `stock_quantity` and `price`
- `INSERT` into `orders`: `customer_id`, `status="completed"`, `total_amount`, `created_at=now()`
- `INSERT` into `order_items`: one row per item with `order_id`, `product_id`, `quantity`, `unit_price`
- `UPDATE products SET stock_quantity = stock_quantity - quantity` for each item

**Side effects — MongoDB (Phase 1, best-effort after Postgres commits):**
- Call `save_order_snapshot(...)` to insert into `order_snapshots`

**Side effects — Redis (Phase 2, best-effort):**
- `DECR inventory:{product_id}` by `quantity` for each item

**Side effects — Neo4j (Phase 3, best-effort):**
- `MERGE` `BOUGHT_TOGETHER` edges between every pair of product IDs in the order

**Errors:**
- Raises `ValueError(f"Insufficient stock for product {product_id}")` if any product's `stock_quantity < requested quantity`. The Postgres transaction is rolled back. No MongoDB snapshot is written. No Redis/Neo4j updates.

---

#### `get_product`

```{code-cell} python
def get_product(self, product_id: int) -> dict | None:
```

**Returns:**
```{code-cell} python
{
    "id": int,
    "name": str,
    "price": float,
    "stock_quantity": int,
    "category": str,        # "electronics" | "clothing" | "books" | "food" | "home"
    "description": str,
    "category_fields": {    # shape varies by category — see below
        ...
    }
}
```

**`category_fields` by category:**
```{code-cell} python
# electronics
{"cpu": str, "ram_gb": int, "storage_gb": int, "screen_inches": float}

# clothing
{"material": str, "sizes": [str], "colors": [str]}

# books
{"isbn": str, "author": str, "page_count": int, "genre": str}

# food
{"weight_g": int, "organic": bool, "allergens": [str]}

# home
{
    "dimensions": {"width": float, "height": float, "depth": float},
    "material": str,
    "assembly_required": bool
}
```

**Phase 1 behavior:** Query `product_catalog` collection in MongoDB by `id` field (not `_id`). Return `None` if not found.

**Phase 2 behavior (cache-aside added to same method):**
1. Check Redis key `product:{product_id}` — if present, `json.loads` the value and return
2. On miss: fetch from MongoDB
3. If found: `redis.set(f"product:{product_id}", json.dumps(product), ex=300)`, then return
4. If not found in MongoDB: return `None`

---

#### `search_products`

```{code-cell} python
def search_products(
    self,
    category: str | None = None,
    q: str | None = None,
) -> list[dict]:
```

**Returns:** List of product dicts (each with same shape as `get_product` return). Empty list if no matches.

**Behavior:**
- If `category` is provided: filter MongoDB documents where `category == category`
- If `q` is provided: case-insensitive substring match on `name` field (use `{"$regex": q, "$options": "i"}`)
- Both filters can be combined (AND semantics)
- If neither is provided: return all products

---

#### `save_order_snapshot`

```{code-cell} python
def save_order_snapshot(
    self,
    order_id: int,
    customer: dict,
    items: list[dict],
    total_amount: float,
    status: str,
    created_at: str,
) -> str:
```

**Input shapes:**
```{code-cell} python
# customer
{"id": int, "name": str, "email": str}

# items (each)
{"product_id": int, "product_name": str, "quantity": int, "unit_price": float}
```

**Returns:** The MongoDB `inserted_id` as a string (str of ObjectId).

**Side effect:** Inserts one document into the `order_snapshots` collection:
```{code-cell} python
{
    "order_id": int,
    "customer": {"id": int, "name": str, "email": str},
    "items": [
        {"product_id": int, "product_name": str, "quantity": int, "unit_price": float},
        ...
    ],
    "total_amount": float,
    "status": str,
    "created_at": str   # ISO 8601 string, same value passed from create_order
}
```

Called internally by `create_order` after the Postgres transaction commits. Not called directly by routes.

---

#### `get_order`

```{code-cell} python
def get_order(self, order_id: int) -> dict | None:
```

**Returns:** The order snapshot document (same shape as stored, minus `_id`), or `None` if not found.

```{code-cell} python
{
    "order_id": int,
    "customer": {"id": int, "name": str, "email": str},
    "items": [{"product_id": int, "product_name": str, "quantity": int, "unit_price": float}],
    "total_amount": float,
    "status": str,
    "created_at": str
}
```

Reads from MongoDB `order_snapshots` collection, filtering by `order_id` field.

---

#### `get_order_history`

```{code-cell} python
def get_order_history(self, customer_id: int) -> list[dict]:
```

**Returns:** List of order snapshot dicts for the given customer, ordered by `created_at` descending. Empty list if no orders found.

Each element has the same shape as the `get_order` return value.

Reads from MongoDB `order_snapshots` collection, filtering by `customer.id == customer_id`, sorted by `created_at` descending (`-1`).

---

#### `revenue_by_category`

```{code-cell} python
def revenue_by_category(self) -> list[dict]:
```

**Returns:**
```{code-cell} python
[
    {"category": str, "total_revenue": float},
    ...
]
```

Sorted by `total_revenue` descending.

**Implementation:** Postgres SQL aggregation:
```sql
SELECT p.category, SUM(oi.quantity * oi.unit_price) AS total_revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
JOIN products p ON p.id = oi.product_id
GROUP BY p.category
ORDER BY total_revenue DESC
```

---

### Phase 2 Methods

#### `init_inventory_counters`

```{code-cell} python
def init_inventory_counters(self) -> None:
```

**Side effect:** For each product row in Postgres `products` table, set Redis key `inventory:{product_id}` to the product's current `stock_quantity` value (integer string).

Called at application startup (from `db.py` init) and optionally by the seed script after loading products.

---

#### `invalidate_product_cache`

```{code-cell} python
def invalidate_product_cache(self, product_id: int) -> None:
```

**Side effect:** `DEL product:{product_id}` from Redis. No-op if the key doesn't exist. Used when a product's data is updated in MongoDB.

---

#### `record_product_view`

```{code-cell} python
def record_product_view(self, customer_id: int, product_id: int) -> None:
```

**Side effect:**
1. `LPUSH recently_viewed:{customer_id} {product_id}` — prepend product ID (as string) to the list head
2. `LTRIM recently_viewed:{customer_id} 0 9` — keep only the 10 most recent entries

---

#### `get_recently_viewed`

```{code-cell} python
def get_recently_viewed(self, customer_id: int) -> list[int]:
```

**Returns:** List of up to 10 product IDs (as `int`, not `str`), most recently viewed first. Empty list if no views have been recorded for this customer.

**Implementation:** `LRANGE recently_viewed:{customer_id} 0 9`, then convert each element from string to `int`.

---

### Phase 3 Methods

#### `seed_recommendation_graph`

```{code-cell} python
def seed_recommendation_graph(self, orders: list[dict]) -> None:
```

**Input `orders` shape:**
```{code-cell} python
[
    {"order_id": int, "product_ids": [int, ...]},
    ...
]
```

**Side effect:** For each order, process every unique pair `(a, b)` from `product_ids`:
```cypher
MERGE (a:Product {id: $id_a})
ON CREATE SET a.name = $name_a
MERGE (b:Product {id: $id_b})
ON CREATE SET b.name = $name_b
MERGE (a)-[r:BOUGHT_TOGETHER]-(b)
ON CREATE SET r.weight = 1
ON MATCH SET r.weight = r.weight + 1
```

Product names for the nodes are looked up from MongoDB `product_catalog` by `id`. Skip pairs where a product is not found.

Called by the seed script after loading historical orders.

---

#### `get_recommendations`

```{code-cell} python
def get_recommendations(self, product_id: int, limit: int = 5) -> list[dict]:
```

**Returns:**
```{code-cell} python
[
    {"product_id": int, "name": str, "score": int},  # score = BOUGHT_TOGETHER edge weight
    ...
]
```

Sorted by `score` descending. The queried product itself is never included in the results. Returns empty list if no `BOUGHT_TOGETHER` edges exist for this product.

**Cypher:**
```cypher
MATCH (p:Product {id: $product_id})-[r:BOUGHT_TOGETHER]-(rec:Product)
RETURN rec.id AS product_id, rec.name AS name, r.weight AS score
ORDER BY r.weight DESC
LIMIT $limit
```

---

## API Endpoints

### Error conventions (all routes)

| Condition | HTTP Status | Response body |
|-----------|-------------|---------------|
| Method not implemented yet | `501 Not Implemented` | `{"message": "Not implemented: <method_name>"}` |
| Business rule violation (ValueError) | `400 Bad Request` | `{"message": "<error message>"}` |
| Resource not found (None returned) | `404 Not Found` | `{"message": "<resource> not found"}` |
| Success | `200 OK` | resource body |
| Successful creation | `201 Created` | resource body |

### Products

| Method | Path | Query Params | Request Body | Response Model | DBAccess Method | Phase |
|--------|------|-------------|-------------|----------------|----------------|-------|
| `GET` | `/products` | `category: str \| None`, `q: str \| None` | — | `ProductListResponse` | `search_products` | 1 |
| `GET` | `/products/{product_id}` | — | — | `ProductResponse` | `get_product` | 1 |
| `GET` | `/products/{product_id}/recommendations` | `limit: int = 5` | — | `RecommendationListResponse` | `get_recommendations` | 3 |

### Orders

| Method | Path | Query Params | Request Body | Response Model | DBAccess Method | Phase |
|--------|------|-------------|-------------|----------------|----------------|-------|
| `POST` | `/orders` | — | `CreateOrderRequest` | `OrderResponse` | `create_order` | 1 |
| `GET` | `/orders/{order_id}` | — | — | `OrderSnapshotResponse` | `get_order` | 1 |

### Customers

| Method | Path | Query Params | Request Body | Response Model | DBAccess Method | Phase |
|--------|------|-------------|-------------|----------------|----------------|-------|
| `GET` | `/customers/{customer_id}/orders` | — | — | `OrderHistoryResponse` | `get_order_history` | 1 |
| `POST` | `/customers/{customer_id}/viewed/{product_id}` | — | — | `MessageResponse` | `record_product_view` | 2 |
| `GET` | `/customers/{customer_id}/recently-viewed` | — | — | `RecentlyViewedResponse` | `get_recently_viewed` | 2 |

### Analytics

| Method | Path | Query Params | Request Body | Response Model | DBAccess Method | Phase |
|--------|------|-------------|-------------|----------------|----------------|-------|
| `GET` | `/analytics/revenue-by-category` | — | — | `RevenueByCategoryResponse` | `revenue_by_category` | 1 |

---

## Pydantic Request Models

```{code-cell} python
# requests.py

class OrderItemRequest(BaseModel):
    product_id: int
    quantity: int           # must be > 0

class CreateOrderRequest(BaseModel):
    customer_id: int
    items: list[OrderItemRequest]   # must be non-empty
```

---

## Pydantic Response Models

```{code-cell} python
# responses.py

class MessageResponse(BaseModel):
    message: str

# --- Products ---

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    stock_quantity: int
    category: str
    description: str
    category_fields: dict   # shape varies by category, see use case UC3

class ProductListResponse(BaseModel):
    products: list[ProductResponse]

# --- Orders ---

class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float

class OrderResponse(BaseModel):
    order_id: int
    customer_id: int
    status: str
    total_amount: float
    created_at: str
    items: list[OrderItemResponse]

class OrderCustomerEmbed(BaseModel):
    id: int
    name: str
    email: str

class OrderSnapshotResponse(BaseModel):
    order_id: int
    customer: OrderCustomerEmbed
    items: list[OrderItemResponse]
    total_amount: float
    status: str
    created_at: str

class OrderHistoryResponse(BaseModel):
    orders: list[OrderSnapshotResponse]

# --- Recommendations ---

class RecommendationResponse(BaseModel):
    product_id: int
    name: str
    score: int              # co-purchase edge weight

class RecommendationListResponse(BaseModel):
    recommendations: list[RecommendationResponse]

# --- Redis ---

class RecentlyViewedResponse(BaseModel):
    product_ids: list[int]

# --- Analytics ---

class CategoryRevenueResponse(BaseModel):
    category: str
    total_revenue: float

class RevenueByCategoryResponse(BaseModel):
    revenue: list[CategoryRevenueResponse]
```

---

## Postgres Schema

Students implement all models in `postgres_models.py` using SQLAlchemy 2.0 declarative API (`DeclarativeBase`, `Mapped`, `mapped_column`, `relationship`).

### `customers`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK, auto-increment |
| `name` | String(100) | NOT NULL |
| `email` | String(255) | NOT NULL, UNIQUE |
| `created_at` | DateTime | NOT NULL, server_default=`now()` |

### `products`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK, auto-increment |
| `name` | String(200) | NOT NULL |
| `price` | Numeric(10,2) | NOT NULL |
| `stock_quantity` | Integer | NOT NULL, CHECK `>= 0` |
| `category` | String(50) | NOT NULL |
| `description` | Text | nullable |

### `product_electronics` (1:1 with `products`)

| Column | Type | Constraints |
|--------|------|-------------|
| `product_id` | Integer | PK + FK → `products.id` |
| `cpu` | String(100) | nullable |
| `ram_gb` | Integer | nullable |
| `storage_gb` | Integer | nullable |
| `screen_inches` | Numeric(4,1) | nullable |

### `product_clothing` (1:1 with `products`)

| Column | Type | Constraints |
|--------|------|-------------|
| `product_id` | Integer | PK + FK → `products.id` |
| `material` | String(100) | nullable |

### `clothing_sizes` (many-to-1 with `product_clothing`)

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK, auto-increment |
| `clothing_id` | Integer | FK → `product_clothing.product_id`, NOT NULL |
| `size` | String(10) | NOT NULL |

### `clothing_colors` (many-to-1 with `product_clothing`)

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK, auto-increment |
| `clothing_id` | Integer | FK → `product_clothing.product_id`, NOT NULL |
| `color` | String(50) | NOT NULL |

### `product_books` (1:1 with `products`)

| Column | Type | Constraints |
|--------|------|-------------|
| `product_id` | Integer | PK + FK → `products.id` |
| `isbn` | String(13) | nullable, UNIQUE |
| `author` | String(200) | nullable |
| `page_count` | Integer | nullable |
| `genre` | String(50) | nullable |

### `orders`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK, auto-increment |
| `customer_id` | Integer | FK → `customers.id`, NOT NULL |
| `status` | String(20) | NOT NULL, default=`"completed"` |
| `total_amount` | Numeric(12,2) | NOT NULL |
| `created_at` | DateTime | NOT NULL, server_default=`now()` |

### `order_items`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK, auto-increment |
| `order_id` | Integer | FK → `orders.id`, NOT NULL |
| `product_id` | Integer | FK → `products.id`, NOT NULL |
| `quantity` | Integer | NOT NULL, CHECK `> 0` |
| `unit_price` | Numeric(10,2) | NOT NULL |

---

## MongoDB Collections

### `product_catalog`

One document per product. All five categories coexist in this collection.

```{code-cell} python
{
    "_id": ObjectId,          # auto-generated by MongoDB
    "id": int,                # matches Postgres products.id — used for cross-DB joins
    "name": str,
    "price": float,
    "stock_quantity": int,
    "category": str,          # "electronics" | "clothing" | "books" | "food" | "home"
    "description": str,
    "category_fields": {
        # shape varies — see UC3 for per-category definitions
    }
}
```

Index: `{"id": 1}` (unique) — for efficient `find_one({"id": product_id})` lookups.

### `order_snapshots`

One document per order. Fully denormalized — contains customer and product data at time of order.

```{code-cell} python
{
    "_id": ObjectId,
    "order_id": int,          # matches Postgres orders.id
    "customer": {
        "id": int,
        "name": str,
        "email": str
    },
    "items": [
        {
            "product_id": int,
            "product_name": str,
            "quantity": int,
            "unit_price": float
        }
    ],
    "total_amount": float,
    "status": str,
    "created_at": str         # ISO 8601 string
}
```

Indexes:
- `{"order_id": 1}` (unique) — for `get_order` lookups
- `{"customer.id": 1}` — for `get_order_history` lookups

---

## Redis Key Patterns

| Key Pattern | Redis Type | Value | TTL | Phase | Used by |
|-------------|-----------|-------|-----|-------|---------|
| `product:{product_id}` | String | JSON-serialized product dict | 300 seconds | 2 | `get_product`, `invalidate_product_cache` |
| `inventory:{product_id}` | String | Integer (stock count as string) | None (no TTL) | 2 | `create_order`, `init_inventory_counters` |
| `recently_viewed:{customer_id}` | List | Product ID strings (head = most recent) | None (no TTL) | 2 | `record_product_view`, `get_recently_viewed` |

Redis client initialized with `decode_responses=True` so all values come back as strings.

---

## Neo4j Graph Schema

### Nodes

**Label:** `Product`

| Property | Type | Notes |
|----------|------|-------|
| `id` | int | Matches Postgres/MongoDB product ID |
| `name` | str | Product name at time of seeding |

### Relationships

**Type:** `BOUGHT_TOGETHER` (undirected)

| Property | Type | Notes |
|----------|------|-------|
| `weight` | int | Number of orders in which both products appeared together |

The relationship is modeled as undirected (`MERGE (a)-[r:BOUGHT_TOGETHER]-(b)` without direction arrows). This means traversal from either product node returns the same recommendations.

---

## Connection Parameters

All connection details come from environment variables. The scaffold provides `.env.example` and `db.py` reads them via `os.environ.get`.

### Postgres (via SQLAlchemy)
```
POSTGRES_HOST  (default: localhost)
POSTGRES_PORT  (default: 5432)
POSTGRES_DB    (default: ecommerce)
POSTGRES_USER  (default: postgres)
POSTGRES_PASSWORD
```

Connection URL: `postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}`

### MongoDB (via pymongo)
```
MONGO_HOST  (default: localhost)
MONGO_PORT  (default: 27017)
MONGO_DB    (default: ecommerce)
```

### Redis (Phase 2, via redis-py)
```
REDIS_HOST  (default: localhost)
REDIS_PORT  (default: 6379)
```

Client created with `decode_responses=True`.

### Neo4j (Phase 3, via neo4j driver)
```
NEO4J_HOST       (default: localhost)
NEO4J_BOLT_PORT  (default: 7687)
NEO4J_USER       (default: neo4j)
NEO4J_PASSWORD
```

Bolt URI: `bolt://{host}:{port}`
