# Capstone Project: E-Commerce Polyglot Data Pipeline

## What Is This Project?

A hands-on, incremental project where students build a realistic e-commerce backend that stores and retrieves data across four different database technologies. Students implement a unified data access layer -- designing schemas, writing database interaction code, and orchestrating cross-database operations -- while the web framework and API layer are pre-built scaffolding.

The project runs as a thread through the second half of the course. Each phase introduces a new database technology immediately after students learn it in the corresponding lesson, so theory is applied to practice within the same session.

**Students will build:** A Python backend for an online store that processes orders, manages a product catalog, serves cached data, and generates product recommendations -- each capability powered by the database technology best suited for it.

---

## Why This Project?

### The Core Teaching Goal

Students should experience **polyglot persistence** firsthand -- the practice of using multiple storage systems in one application, each chosen for its strengths on specific access patterns. This is how data-intensive systems actually work in industry (Netflix, Uber, Airbnb all use 5+ database technologies), but it's hard to appreciate from theory alone.

The project makes the trade-offs concrete:

- "Why can't we just put everything in Postgres?" → Fetch a product from the normalized schema: you need to JOIN `products` with `product_electronics` or `product_clothing` or `product_books` depending on the category -- and you don't know which table until you check. From MongoDB: one `find_one()`, done.
- "Why can't we just use MongoDB for everything?" → Try running `SELECT SUM(quantity * unit_price) FROM order_items GROUP BY category` as a `$lookup` aggregation pipeline. Feel the pain of no native joins.
- "Why do we need Redis?" → Measure the latency of fetching the same product from MongoDB 1,000 times vs. a Redis `GET`. See the numbers.
- "Why Neo4j for recommendations?" → Write the recursive CTE in Postgres that finds "products frequently bought together within 2 hops." Then write the Cypher query. Compare complexity and performance.

### Why E-Commerce?

We considered three domains (e-commerce, log analytics, online learning platform) and chose e-commerce because:

1. **Zero domain explanation needed** -- every student understands products, orders, and shopping carts
2. **Natural fit for all four databases** -- the justification for each DB is genuine, not forced
3. **Matches existing course material** -- the polyglot persistence lesson (`core-concepts/06-architecture-patterns/03-polyglot-persistence.md`) already uses e-commerce as its primary example
4. **Data generation is straightforward** -- realistic seed data is easy to produce

### Why Not Just Read JSON Events from Files?

In a real e-commerce system, the backend service has direct access to the database. An order doesn't arrive as a JSON file to be batch-processed -- it arrives as an HTTP request that must be validated (is there enough inventory?) and persisted (ACID transaction) in real time. If inventory is insufficient, the order is rejected immediately.

Processing orders from files would skip the transactional aspect entirely and miss the main reason Postgres is the right choice for this workload. Using a web framework (FastAPI) makes the data flow realistic: request → validate → persist → respond.

Since students don't know web frameworks, we scaffold the API layer entirely. Students only implement the data interactions.

---

## Design Decisions

### Decision 1: Scaffold the Web Layer, Students Build the Data Layer

**Problem:** Students need a realistic application context but don't know HTTP, REST, or web frameworks.

**Decision:** Pre-build the FastAPI application (routes, request/response models, app lifecycle). Students implement a single `DBAccess` class that the scaffolded routes call.

**Why FastAPI specifically:**
- Uses type hints and Pydantic (similar to dataclasses students already know)
- Auto-generates Swagger UI at `/docs` -- students can test interactively without learning curl or Postman
- Minimal boilerplate -- a route handler is just a typed Python function

**What students see:** A route handler that calls `db.create_order(order_data)`. They implement what `create_order` does.

**What students don't need to understand:** HTTP methods, status codes, middleware, ASGI, async/await. The scaffolded code uses synchronous handlers to avoid introducing async concepts.

### Decision 2: PostgreSQL Instead of SQL Server

**Problem:** The SQL course uses SQL Server (via pyodbc). The project uses PostgreSQL.

**Decision:** Switch to PostgreSQL for the project.

**Why:**
- PostgreSQL is the industry standard for OLTP in data engineering and the broader open-source ecosystem
- Runs natively in Docker on all platforms without ODBC driver installation issues
- Better ecosystem for polyglot setups (most tutorials, examples, and tools assume Postgres)
- Students already know SQLAlchemy, which abstracts the driver -- the ORM code is identical

**Impact on students:** Minimal. They learned DB-API patterns (connect, cursor, execute, fetch, close) that work identically with psycopg2. SQLAlchemy ORM code doesn't change at all. The only visible difference is the connection string.

### Decision 3: Neo4j Instead of ArangoDB

**Problem:** Students need a graph database for the recommendation engine. The graph databases lesson covers Neo4j (Cypher) as the primary example. ArangoDB would require teaching a new query language (AQL).

**Decision:** Use Neo4j with the community edition Docker image.

**Why:**
- Students already learned Cypher syntax in the graph databases lesson -- no new query language needed
- Neo4j Browser (localhost:7474) provides visual graph exploration that makes the data tangible
- The Python driver (`neo4j` package) is well-documented and straightforward
- Community edition limits (single database, no clustering) don't affect this project at all

**Community edition constraints verified:**
- Single database per server → we only need one
- No clustering/HA → single instance is fine for development
- No role-based access → admin-only auth is sufficient
- APOC procedures available → useful but not required
- No hard limits on nodes/relationships for our data volume (~50 products, ~200 edges)

### Decision 4: Incremental Phases Tied to Lessons

**Problem:** A four-database project is overwhelming if presented all at once.

**Decision:** Three implementation phases, each unlocked after the corresponding lesson:

| Phase | Databases | Unlocked After |
|-------|-----------|---------------|
| Phase 1 | PostgreSQL + MongoDB | MongoDB Basics lesson |
| Phase 2 | + Redis | Redis lesson (new) |
| Phase 3 | + Neo4j | Neo4j lesson (new) |

Each phase has its own test suite. Students run tests to verify correctness. Previous phase tests must continue to pass (regression).

**Why this order:**
- Phase 1 (Postgres + MongoDB) is the foundation. It demonstrates the core polyglot pattern: relational for transactions, document store for flexible schemas. Students can work on this immediately since they know both SQL/ORM and MongoDB.
- Phase 2 (Redis) adds a performance optimization layer. This only makes sense once the base system exists -- you can't cache what doesn't exist yet.
- Phase 3 (Neo4j) adds an analytical/recommendation layer built from the order data. This requires historical orders to exist, so it naturally comes last.

### Decision 5: End-to-End Tests Against Real Databases

**Problem:** Students need clear success criteria. "Implement the data layer" is too vague.

**Decision:** Provide pytest test suites for each phase that serve as executable specifications. All tests run end-to-end against real databases -- no mocks, no fakes, no in-memory substitutes.

**Why no mocks:** Docker Compose provides all four databases locally. There is no reason to mock what you can run for real. Mocking database interactions hides bugs (your mock behaves how you *think* the database works, not how it *actually* works). End-to-end tests against real databases give genuine confidence that the code works.

**How it works:**
- Students learned pytest in the ORM testing lesson -- the framework is familiar
- `conftest.py` connects to the real databases running in Docker Compose
- Each test creates its own data, exercises the `DBAccess` method, and verifies the result in the actual database
- Tests clean up after themselves (truncate tables, drop collections) so they're independent
- Red → green workflow gives immediate feedback

### Decision 6: Unified DBAccess Class (Federated Data Access)

**Problem:** In a polyglot system, the application needs to interact with multiple databases. The question is how to organize that code.

**Decision:** A single `DBAccess` class owns all database interactions. Each method uses whichever database(s) are appropriate for the operation. Some methods use one database; others orchestrate writes across multiple databases in a single call.

```python
class DBAccess:
    def __init__(self, postgres, mongo, redis=None, neo4j=None):
        ...

    # Uses Postgres (ACID transaction) + MongoDB (snapshot) + Redis (counter) + Neo4j (graph)
    def create_order(self, customer_id, items): ...

    # Uses MongoDB (flexible document) or Redis (cache hit)
    def get_product(self, product_id): ...

    # Uses Postgres (SQL joins and aggregations)
    def revenue_by_category(self): ...

    # Uses Neo4j (graph traversal)
    def get_recommendations(self, product_id): ...

    # Uses Redis (list data structure)
    def get_recently_viewed(self, customer_id): ...
```

**Why a single class instead of separate repository classes per database:**

The point of polyglot persistence is that each database serves a specific access pattern -- not that each database is an interchangeable implementation of the same interface. Splitting the code into `PostgresOrderRepository`, `MongoProductRepository`, `RedisCache`, etc. organizes around *databases*. But the application doesn't think in databases -- it thinks in operations: "create an order," "get a product," "find recommendations."

A single `DBAccess` class organizes around *what the application needs*. The fact that `create_order()` writes to four databases is an implementation detail inside the method. The route handler just calls `db.create_order(...)` and gets a result. This is federated data access: the data layer presents a unified interface to the application while internally routing each operation to the right storage engine.

This also makes cross-database operations natural. When `create_order()` needs to write to Postgres (order), MongoDB (snapshot), Redis (counter), and Neo4j (graph), it does so in a single method body. No need for a service layer to orchestrate calls to four separate repository objects.

### Decision 7: Normalized Product Schema in Postgres

**Problem:** Products have category-specific attributes (electronics have CPU specs, clothing has sizes, books have ISBNs). How should this be modeled?

**Decision:** Both Postgres and MongoDB store the complete product data, but modeled differently:

- **Postgres:** Normalized. A base `products` table with shared fields, plus category-specific tables (`product_electronics`, `product_clothing`, `product_books`) joined by foreign key. Three categories -- enough to demonstrate the pattern without excessive boilerplate.
- **MongoDB:** Denormalized. Each product is a single document with all fields (shared + category-specific) in one place.

**Why model the same data both ways:**

This is the most important design decision in the project. If Postgres only stored orders and MongoDB only stored products, students would see two databases doing *different things* -- which is just task separation, not polyglot persistence. By storing the same product data in both systems (normalized in Postgres, denormalized in MongoDB), students directly experience *why* the same data benefits from different representations depending on the access pattern:

- **Need to display a product page?** → MongoDB: one `find_one()` returns everything. Postgres: `SELECT ... FROM products JOIN product_electronics ON ...` -- and you need conditional logic to know which category table to join.
- **Need to run an analytics query?** → Postgres: `SELECT category, SUM(price * stock) FROM products GROUP BY category` works naturally across all categories. MongoDB: `$group` aggregation works too, but the normalized structure with typed tables makes SQL aggregations cleaner.
- **Need to add a new product category?** → MongoDB: just insert documents with a new `category` field and whatever fields that category needs. Postgres: write a migration to create a new `product_furniture` table, define columns, deploy.

Students don't just read about these trade-offs in a slide -- they implement both and compare.

### Decision 8: Git as Part of the Workflow

**Problem:** Students need git practice beyond cloning and committing to an existing repo.

**Decision:** Students create their own repository from scratch, receive the scaffold as starter files, and follow a branch-per-phase workflow.

**Git skills practiced:**
- Repository creation and initial commit
- `.gitignore` for `.env`, `__pycache__`, `.venv`
- Feature branches (`feature/phase-1`, `feature/phase-2`, `feature/phase-3`)
- Multiple meaningful commits within a branch
- Merging to `main` after each phase

Three full branch → implement → test → merge cycles give solid practice.

---

## What Each Database Does (and Why)

The same core data (products, customers, orders) lives in multiple databases, each storing the representation optimized for its access pattern. This is the essence of polyglot persistence: the data is the same, but the retrieval logic determines which database serves each operation.

### PostgreSQL -- Source of Truth for Transactions and Analytics

**Stores:** Customers, products (normalized across base + category tables), orders, order items.

**Schema:**
```
customers
  id, name, email, created_at

products
  id, name, price, stock_quantity, category, description

product_electronics (product_id FK → products)
  cpu, ram_gb, storage_gb, screen_inches

product_clothing (product_id FK → products)
  material
  + clothing_sizes (clothing_id FK, size)
  + clothing_colors (clothing_id FK, color)

product_books (product_id FK → products)
  isbn, author, page_count, genre

orders
  id, customer_id FK, status, total_amount, created_at

order_items
  id, order_id FK, product_id FK, quantity, unit_price
```

**Why Postgres for this:**
- Creating an order must be ACID: check inventory, create order, create line items, decrement stock -- all atomically. If any step fails, everything rolls back.
- Analytical queries need SQL: "revenue per category this month," "top customers by lifetime value," "products with low stock." JOINs and aggregations are natural here.
- Relational integrity: an order item references a product and an order via foreign keys. A product can't be deleted while orders reference it. Stock can't go negative (`CHECK` constraint).

**What students implement in DBAccess:**
- SQLAlchemy ORM models for all tables (base + 3 category tables)
- `create_order()`: transactional logic in a single `session.begin()`
- `revenue_by_category()`, `get_customer_order_history()`: SQL aggregations and joins
### MongoDB -- Flexible Product Catalog + Order Snapshots

**Stores:** Full product catalog (denormalized documents), order snapshots (denormalized with embedded details).

**Why MongoDB for this:**
- Product catalog: the same product data that requires 4+ tables in Postgres is a single document in MongoDB. An electronics product has `specs.cpu`, `specs.ram_gb` inline. A clothing product has `sizes: ["S", "M", "L"]` and `colors: ["navy"]` inline. No joins, no conditional table selection.
- Order snapshots: when a customer views their order history, the response should include product names, prices at time of purchase, and customer details -- all in one read, not a multi-table JOIN. If a product name changes later, the snapshot preserves the original.
- Adding a new product category (e.g., furniture) requires zero schema changes -- just insert documents with the new fields.

**What students implement in DBAccess:**
- `get_product()`: fetch a complete product document in one read
- `search_products()`: filter by category, text search by name
- `save_order_snapshot()`: create denormalized snapshot with embedded product and customer details
- `get_order_history()`: list snapshots by customer

### Redis -- Caching and Real-Time Counters

**Stores:** Cached product details, inventory counters, recently viewed product lists.

**Why Redis for this:**
- Product detail pages are read-heavy. Fetching from MongoDB on every request is wasteful. Redis serves cached product data in < 1ms with automatic TTL expiry.
- Real-time inventory count: `DECR` is atomic and O(1). Checking "is this product in stock?" should not require a Postgres query under load.
- Recently viewed products: a per-customer list using Redis Lists. `LPUSH` + `LTRIM` keeps the last N items. This access pattern (append to head, trim tail, read full list) is exactly what Redis Lists are designed for.

**What students implement in DBAccess:**
- `get_product()` gains a Redis cache check before falling through to MongoDB
- `create_order()` gains a Redis `DECR` for the inventory counter
- `record_product_view()`, `get_recently_viewed()`: Redis list operations
- `invalidate_product_cache()`: cache invalidation on product update

### Neo4j -- Product Recommendation Graph

**Stores:** Product nodes, `BOUGHT_TOGETHER` edges weighted by co-occurrence count.

**Why Neo4j for this:**
- "Customers who bought X also bought Y" is a graph traversal: follow `BOUGHT_TOGETHER` edges from product X, rank neighbors by edge weight, return top N.
- In Postgres, this would require a self-join on order_items grouped by co-occurrence -- feasible for 1 hop, but slow and complex for 2+ hops. In Cypher: `MATCH (p:Product {id: $id})-[r:BOUGHT_TOGETHER]-(rec) RETURN rec ORDER BY r.weight DESC LIMIT 5`.
- The Neo4j Browser visualization makes the recommendation graph tangible -- students can see clusters of frequently co-purchased products.

**What students implement in DBAccess:**
- `seed_recommendation_graph()`: process historical orders into product nodes and `BOUGHT_TOGETHER` edges
- `get_recommendations()`: Cypher traversal query
- `create_order()` gains a Neo4j graph update for the new co-purchase edges

---

## Knowledge Gaps and How We Address Them

Students have completed: Git, Python Essentials (OOP, dataclasses, Protocols, type hints, generics), SQL, Python ORM (SQLAlchemy), Docker/Compose, NoSQL theory (all types), and MongoDB (pymongo, data modeling, indexes).

| Gap | Severity | Approach | Time |
|-----|----------|----------|------|
| **FastAPI / HTTP APIs** | High | Teach minimally (~20 min): what an endpoint is, show one route, demo Swagger UI. Scaffold everything. | 20 min |
| **Pydantic models** | Medium | Mention "it's a dataclass that validates input." Pre-define all models in scaffold. | 5 min |
| **PostgreSQL vs SQL Server** | Low | Same DB-API pattern. Show connection string difference. SQLAlchemy abstracts the rest. | 2 min |
| **redis-py client** | Low | Maps 1:1 to Redis CLI commands from key-value stores lesson. Quick demo of `SET`/`GET`/`INCR`. | 10 min |
| **Neo4j Python driver** | Medium | Students know Cypher syntax. Show how to run Cypher from Python. Neo4j Browser for exploration. | 15 min |
| **Multiple DB connections** | Medium | Scaffold `db.py` module that initializes all connections and passes them to `DBAccess`. Students see it but don't build it. | 5 min |
| **Cross-DB consistency** | Conceptual | Discuss as part of Phase 1 implementation. Postgres is source of truth. MongoDB is best-effort secondary write. | 10 min |
| **Environment variables** | Low | Provide `.env.example`. Show `os.environ.get()`. | 2 min |
| **Docker Compose (4 services)** | None | They've done multi-node MongoDB clusters. Adding more services is the same pattern. | 0 min |

**Total pre-teaching overhead: ~45-60 minutes**, spread across the relevant lessons (not a single block).

---

## Project Structure

```
ecommerce-pipeline/
│
├── docker-compose.yml                  # All database services
├── .env.example                        # Connection strings template
├── pyproject.toml                      # Python dependencies
├── README.md                           # Student-facing setup instructions
│
├── seed_data/
│   ├── products.json                   # ~40 products across 5 categories
│   ├── customers.json                  # ~15 customers
│   └── historical_orders.json          # ~80 orders (for graph seeding)
│
├── src/
│   ├── api/                            # ── SCAFFOLDED (students don't modify) ──
│   │   ├── __init__.py
│   │   ├── app.py                      # FastAPI app, lifespan, startup/shutdown
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── products.py             # GET /products, GET /products/{id},
│   │       │                           # GET /products/{id}/recommendations
│   │       ├── orders.py               # POST /orders, GET /orders/{id}
│   │       └── customers.py            # GET /customers/{id}/orders,
│   │                                   # GET /customers/{id}/recently-viewed
│   │
│   ├── models/                         # ── SCAFFOLDED (students don't modify) ──
│   │   ├── __init__.py
│   │   ├── requests.py                 # CreateOrderRequest, etc. (Pydantic)
│   │   └── responses.py               # OrderResponse, ProductResponse, etc.
│   │
│   ├── db.py                           # ── SCAFFOLDED ── connection init, passes
│   │                                   #    clients to DBAccess constructor
│   ├── db_access.py                    # ── STUDENTS IMPLEMENT ──
│   │                                   #    Unified data access layer
│   └── postgres_models.py             # ── STUDENTS IMPLEMENT ──
│                                       #    SQLAlchemy ORM models
│
├── scripts/
│   └── seed.py                         # Load seed data into all databases
│
└── tests/
    ├── conftest.py                     # DB connections, cleanup, shared fixtures
    ├── test_phase1_postgres.py         # Phase 1: Postgres operations
    ├── test_phase1_mongo.py            # Phase 1: MongoDB operations
    ├── test_phase1_integration.py      # Phase 1: Cross-DB flows
    ├── test_phase2_redis.py            # Phase 2: Redis operations + cache flows
    └── test_phase3_neo4j.py            # Phase 3: Neo4j operations + recommendation flows
```

### What Is Scaffolded vs. What Students Build

| Layer | Scaffolded? | Why |
|-------|-------------|-----|
| `docker-compose.yml` | Yes | Infrastructure setup is not a learning objective |
| `api/` (FastAPI routes) | Yes | Web framework is not a learning objective |
| `models/` (Pydantic) | Yes | Request/response validation is not a learning objective |
| `db.py` | Yes | Connection management boilerplate |
| `tests/` | Yes | Tests are the specification |
| `scripts/seed.py` | Partially | Base structure scaffolded; students extend per phase |
| `postgres_models.py` | **Students build** | SQLAlchemy ORM models (base + 3 category tables) |
| `db_access.py` | **Students build** | All database interactions, all business logic |

The project has exactly **two files** students need to implement: `postgres_models.py` (the schema definition) and `db_access.py` (all data operations). This keeps the scope clear and avoids students getting lost in file organization.

---

## Phase Breakdown

### Phase 0: Project Setup (~1 hour, in class)

**Prerequisites:** MongoDB Basics lesson completed.

**Objectives:**
- Create a personal git repository for the project
- Understand the scaffold structure
- Get all services running locally
- Understand the test-driven workflow

**In-Class Flow:**

1. **Git setup (10 min):** Students create a new GitHub repository. Clone locally. Copy scaffold files. Create `.gitignore` (`.env`, `__pycache__`, `.venv`, `*.pyc`). Initial commit and push.

2. **FastAPI 101 (20 min):** Minimal introduction:
   - "A FastAPI app maps URLs to Python functions"
   - Show one route handler: `POST /orders` → calls `db.create_order()`
   - Open Swagger UI at `localhost:8000/docs` -- "this is auto-generated, you can test endpoints here"
   - Show Pydantic model: "it's a dataclass that validates the incoming JSON"
   - Students do NOT need to understand: HTTP methods deeply, status codes, middleware, ASGI, async

3. **Docker Compose + verify (10 min):** `docker compose up -d`. Check that Postgres, MongoDB are accessible. Quick `mongosh` and `psql` smoke test.

4. **Test suite walkthrough (10 min):** Run `pytest tests/test_phase1_postgres.py -v` -- everything fails (red). Read through 3-4 test names. "Your job is to make these green."

5. **Project structure tour (10 min):** Walk through the directory tree. Show `db_access.py` -- "this is the file you implement. Each method uses whichever database is right for that operation." Show `db.py` -- "this gives you the database connections." Show a route handler -- "this calls your DBAccess methods."

**Git Checkpoint:** Scaffold committed to `main` branch.

---

### Phase 1: PostgreSQL + MongoDB (~3-4 hours, class + homework)

**Prerequisites:** SQL, ORM (SQLAlchemy), MongoDB Basics completed.

**Objectives:**
- Design a normalized relational schema for products (base + category tables)
- Design MongoDB document schemas for the same products (denormalized) and order snapshots
- Implement DBAccess methods for both databases
- Experience the core polyglot pattern: same data, different representations for different access patterns

**Part A -- Schema Design Discussion (45 min, in class)**

Instructor-led whiteboard session before anyone writes code:

**Postgres schema design:**
- Show two products side by side:
  ```json
  {"name": "Laptop Pro", "category": "electronics",
   "specs": {"cpu": "M3", "ram_gb": 18, "screen": 16.2}}

  {"name": "Wool Sweater", "category": "clothing",
   "sizes": ["S", "M", "L"], "colors": ["navy"], "material": "merino"}
  ```
- "How do you model both in Postgres?" → guide toward the normalized solution: `products` base table + `product_electronics` + `product_clothing` + `product_books` (3 categories). Foreign keys, `CHECK` constraints.
- "What does fetching a complete product look like?" → `SELECT ... FROM products JOIN product_electronics ON ...` -- and you need to know which table to join first.
- Guide the orders schema: `customers`, `orders`, `order_items` with foreign keys and constraints (`CHECK stock_quantity >= 0`).

**MongoDB schema design:**
- "Now model the same products in MongoDB." → each product is one document with everything inline. No joins needed. No conditional table logic.
- Discuss order snapshots: "If the product name changes next month, should the customer's old order show the new name?" → denormalized snapshot with embedded product and customer details.
- Expected result: two collections -- `product_catalog` and `order_snapshots`.

**Key discussion point:** "Both databases have the complete product data. So why both?" → Different access patterns. Postgres is better for transactions and analytics. MongoDB is better for fetching a full product in one read and for handling schema flexibility.

**Part B -- Implementation (2-3 hours, lab/homework)**

Suggested order:

1. **SQLAlchemy models** (`postgres_models.py`): Define ORM models for `products`, `product_electronics`, `product_clothing`, `product_books`, `customers`, `orders`, `order_items`. Students know this from the ORM module. The category tables with foreign keys are a good practice of relationships they learned. (~30 min)

2. **Postgres methods in DBAccess**: Implement `create_order()` with transactional logic -- check inventory, create order + items, decrement stock, all in one `session.begin()`. Implement `revenue_by_category()`, `get_customer_order_history()`. (~45 min)

3. **MongoDB methods in DBAccess**: Implement `get_product()` that fetches a single document from the catalog. Implement `search_products()`, `save_order_snapshot()`, `get_order_history()`. (~30 min)

4. **Cross-DB method -- `create_order()`**: This method already writes to Postgres. Now add the MongoDB snapshot write. First encounter with cross-DB orchestration in a single method. Discussion point: "What if MongoDB is down? Does the order fail?" → Postgres is the source of truth. MongoDB snapshot is best-effort with error logging. The order is valid regardless. (~20 min)

5. **Seed script** (`scripts/seed.py`): Load products into both Postgres (normalized across tables) and MongoDB (denormalized documents). Load customers into Postgres. (~15 min)

**Test Suite (all end-to-end, no mocks):**

```
test_phase1_postgres.py:
  test_create_customer                          -- insert and retrieve from real Postgres
  test_create_product_with_category_fields      -- base + category table populated
  test_create_order_with_items                  -- order + line items, total calculated
  test_order_reduces_inventory                  -- stock decremented in real DB
  test_order_fails_insufficient_inventory       -- rollback verified in real DB
  test_revenue_by_category                      -- SQL aggregation returns correct sums

test_phase1_mongo.py:
  test_insert_electronics_product               -- document has 'specs' subdocument
  test_insert_clothing_product                  -- document has 'sizes' array
  test_search_products_by_category              -- filter returns correct set
  test_save_order_snapshot                       -- snapshot contains full embedded details
  test_snapshot_preserves_original_price        -- price at order time, not current
  test_get_order_history_by_customer            -- list snapshots for a customer

test_phase1_integration.py:
  test_full_order_flow                          -- order in Postgres AND snapshot in MongoDB
  test_order_snapshot_matches_postgres           -- cross-DB data consistency
  test_order_rejected_insufficient_stock        -- Postgres rejects, no snapshot created
  test_product_exists_in_both_dbs               -- same product queryable from both
  test_get_product_mongo_vs_postgres            -- compare: one read vs JOIN
```

Every test creates real data in the running databases, calls `DBAccess` methods, and verifies results by querying the actual databases. `conftest.py` handles cleanup between tests.

**Git Workflow:**
- Create branch `feature/phase-1`
- Commit after SQLAlchemy models pass model tests
- Commit after Postgres method tests pass
- Commit after MongoDB method tests pass
- Commit after integration tests pass
- Merge to `main`

**Teaching Moment -- Cross-DB Consistency:**

After students implement `create_order()`, discuss: "You write to Postgres, then MongoDB in the same method. What if the MongoDB write fails?" This connects directly to the polyglot persistence lesson's consistency challenges section. The correct answer for this project: Postgres is the source of truth. If MongoDB fails, log the error and continue. The order is valid. The snapshot can be rebuilt later from Postgres data. This is eventual consistency in practice.

---

### Interlude: MongoDB Replication & Sharding (existing lessons, no project code changes)

These lessons teach infrastructure concepts using the existing standalone exercises (replica set Docker cluster, sharded cluster). The project connects conceptually but doesn't change:

**After Replication lesson:** "Our project uses a single MongoDB node. In production, you'd run a replica set. What changes in our application code?" → Only the connection string. The driver handles failover transparently. Optionally, students can upgrade their `docker-compose.yml` to a 3-node replica set as a bonus exercise.

**After Sharding lesson:** "If our `order_snapshots` collection had 100 million documents, what shard key would you choose?" Design discussion:
- `{ customer_id: 1 }` → targeted queries per customer, but large customers create hot chunks
- `{ order_id: "hashed" }` → even distribution, but customer queries are scatter-gather
- `{ customer_id: 1, order_id: 1 }` → compound key, targeted per customer, good distribution within

No code changes -- this is a design discussion tied to the project's data model.

---

### Redis Lesson (new material, ~30 min hands-on)

**Prerequisites:** Key-value stores theory lesson completed (NoSQL types module).

Students already know Redis concepts (data structures, TTL, use cases, CLI commands) from the theory lesson. This session covers the Python client only:

- Install and connect: `redis.Redis(host='localhost', port=6379, decode_responses=True)`
- String operations: `SET`/`GET`/`INCR`/`DECR`/`EXPIRE` -- maps 1:1 to CLI they've seen
- Lists: `LPUSH`/`LTRIM`/`LRANGE`
- JSON values: `json.dumps()`/`json.loads()` for complex data
- Cache-aside pattern: check Redis → miss → fetch from DB → store in Redis → return

This is short because the theory is already learned. The client API is trivially mapped from the CLI commands.

---

### Phase 2: Add Redis (~1.5-2 hours, after Redis lesson)

**Prerequisites:** Key-value stores lesson + Redis hands-on session completed.

**Objectives:**
- Implement caching with TTL-based expiry
- Implement atomic counters for real-time inventory tracking
- Implement per-user data structures (recently viewed list)
- Experience cache invalidation -- the "hardest problem in computer science"

**Implementation:**

Students add new methods to `DBAccess` and modify existing ones:

1. **Add Redis to `docker-compose.yml`** (~5 min): Students add the Redis service.

2. **Modify `get_product()`**: Check Redis cache first. On miss, fetch from MongoDB, store in Redis with 5-minute TTL, return. On hit, return cached data.

3. **Add `invalidate_product_cache()`**: Delete the Redis key for a product. Called when product data changes in MongoDB.

4. **Modify `create_order()`**: After the Postgres transaction and MongoDB snapshot, also `DECR` the Redis inventory counter for each ordered product.

5. **Add `init_inventory_counters()`**: Populate Redis counters from Postgres `stock_quantity` values. Called at startup or by seed script.

6. **Add `record_product_view()` and `get_recently_viewed()`**: `LPUSH` product ID to customer's Redis list, `LTRIM` to keep only last 10, `LRANGE` to retrieve.

**Test Suite (all end-to-end, no mocks):**

```
test_phase2_redis.py:
  test_product_cached_after_first_read       -- verify key exists in real Redis
  test_cache_expires_after_ttl               -- sleep, verify key gone, re-fetched from MongoDB
  test_cache_invalidated_on_update           -- update in MongoDB, verify Redis key deleted
  test_inventory_counter_decremented         -- place order, verify Redis DECR happened
  test_inventory_counter_matches_postgres    -- compare Redis counter to Postgres stock
  test_recently_viewed_adds_product          -- verify product in Redis list
  test_recently_viewed_max_length            -- add 15, verify only 10 stored
  test_recently_viewed_most_recent_first     -- verify ordering in Redis list
```

Tests verify actual Redis state -- `conftest.py` uses `redis.flushdb()` between tests.

**Git Workflow:** Branch `feature/phase-2`, implement, test, merge to `main`.

**Teaching Moment -- Cache Invalidation:**

"You update a product's price in MongoDB. A customer loads the product page. They see the old price from Redis cache. Is this a bug?" Discuss:
- TTL-based expiry: "The cache will correct itself in 5 minutes." Acceptable for most use cases.
- Active invalidation: "Delete the Redis key when you update MongoDB." More complex but immediately consistent.
- Students implement active invalidation, but discuss where TTL-only is good enough.

---

### Neo4j Lesson (new material, ~30 min hands-on)

**Prerequisites:** Graph databases theory lesson completed (Cypher syntax already learned).

Students know Cypher from the graph databases lesson but haven't executed it against a real database. This session covers:

- Docker: `neo4j:5` image, ports 7474 (browser) + 7687 (bolt)
- Neo4j Browser at `localhost:7474` -- visual graph exploration (this is the "wow" moment)
- Python driver: `from neo4j import GraphDatabase`, create driver, run Cypher queries
- Pattern: create nodes → create relationships → traverse

Quick demo: create 5 product nodes and 3 `BOUGHT_TOGETHER` edges in Neo4j Browser. Visually see the graph. Then do the same from Python.

---

### Phase 3: Add Neo4j (~2 hours, after Neo4j lesson)

**Prerequisites:** Graph databases lesson + Neo4j hands-on session completed.

**Objectives:**
- Model product co-purchase relationships as a graph
- Build the graph from historical order data
- Query recommendations via graph traversal
- Keep the graph updated as new orders arrive

**Implementation:**

Students add new methods to `DBAccess` and modify `create_order()` again:

1. **Add Neo4j to `docker-compose.yml`** (~5 min): Students add the Neo4j service with auth configuration.

2. **Add `seed_recommendation_graph()`**: Process `historical_orders.json`. For each order with products [A, B, C], create `BOUGHT_TOGETHER` edges: A↔B, A↔C, B↔C. If edge already exists, increment the `weight` property. Students write the Cypher: `MERGE (a)-[r:BOUGHT_TOGETHER]-(b) ON CREATE SET r.weight = 1 ON MATCH SET r.weight = r.weight + 1`.

3. **Add `get_recommendations()`**: Given a product ID, traverse `BOUGHT_TOGETHER` edges, return top N products by edge weight. Cypher: `MATCH (p:Product {id: $id})-[r:BOUGHT_TOGETHER]-(rec:Product) RETURN rec ORDER BY r.weight DESC LIMIT $limit`.

4. **Modify `create_order()`**: After Postgres + MongoDB + Redis, also update the Neo4j graph with new co-purchase edges for the products in this order. The method now orchestrates all four databases.

**Test Suite (all end-to-end, no mocks):**

```
test_phase3_neo4j.py:
  test_seed_creates_product_nodes              -- verify nodes in real Neo4j
  test_copurchase_edges_created                -- products in same order are connected
  test_edge_weight_reflects_frequency          -- 3 co-occurrences → weight=3 in Neo4j
  test_get_recommendations_returns_results     -- traversal returns related products
  test_recommendations_sorted_by_weight        -- highest weight first
  test_no_self_recommendation                  -- product doesn't recommend itself
  test_new_order_updates_graph                 -- full flow: create_order → verify Neo4j edges
```

Tests use the Neo4j driver to verify graph state directly.

**Git Workflow:** Branch `feature/phase-3`, implement, test, merge to `main`.

**Teaching Moment -- Graph vs. SQL:**

After students implement the Cypher query, show the equivalent SQL:

```sql
SELECT p2.product_id, COUNT(*) as copurchase_count
FROM order_items oi1
JOIN order_items oi2 ON oi1.order_id = oi2.order_id AND oi1.product_id != oi2.product_id
JOIN products p2 ON oi2.product_id = p2.id
WHERE oi1.product_id = $product_id
GROUP BY p2.product_id
ORDER BY copurchase_count DESC
LIMIT 5;
```

"This works for 1 hop. Now extend it to 2 hops -- products bought by people who bought products that were bought with yours." The SQL becomes a nightmare. The Cypher adds three characters: change `*1` to `*1..2` in the path pattern.

---

## Wrap-Up Session (~30-45 min, after Phase 3)

**Full system demo:** Students start all services, seed all databases, and interact with the system through Swagger UI:

1. Browse products → served from MongoDB (or Redis cache on second load)
2. Place an order → `create_order()` writes to Postgres (ACID), MongoDB (snapshot), Redis (counter), Neo4j (graph) -- all in one method
3. View order history → read from MongoDB snapshots
4. View recommendations → traversed from Neo4j graph
5. View recently viewed → read from Redis list

**Observability exercise:** Verify each database has the expected data:
- `psql`: `SELECT * FROM orders;`
- `mongosh`: `db.order_snapshots.findOne()`
- `redis-cli`: `GET product:42`
- Neo4j Browser: visualize the product graph

**Reflection discussion:**
- "Which database would you remove first if forced to simplify?" → Redis (you'd tolerate slower reads)
- "Which one can you absolutely NOT remove?" → Postgres (source of truth, ACID)
- "What happens if Neo4j goes down? Do orders fail?" → No -- it's a secondary store, best effort
- "Where would you add Elasticsearch if you needed full-text search?" → Polyglot persistence keeps growing

---

## Seed Data

Three JSON files provide realistic data for testing and development:

### `products.json` (~40 products)

Products span 5 categories. MongoDB stores all 5 as documents. Postgres normalizes the first 3 into dedicated tables -- the remaining 2 categories (Food, Home) exist only in MongoDB, which itself demonstrates schema flexibility: MongoDB handles new categories without any migration.

| Category | Shared Fields | Category-Specific Fields | In Postgres? |
|----------|--------------|-------------------------|-------------|
| Electronics | name, price, stock | `specs`: cpu, ram_gb, storage_gb, screen_inches | Yes (normalized table) |
| Clothing | name, price, stock | `sizes`: [S,M,L,XL], `colors`: [...], `material` | Yes (normalized table) |
| Books | name, price, stock | `isbn`, `author`, `page_count`, `genre` | Yes (normalized table) |
| Food | name, price, stock | `weight_g`, `organic`, `allergens`: [...] | No (MongoDB only) |
| Home | name, price, stock | `dimensions`: {w,h,d}, `material`, `assembly_required` | No (MongoDB only) |

The two MongoDB-only categories are a deliberate teaching tool: "Adding Food and Home to Postgres would require two new migration files, two new tables, and changes to every product query. In MongoDB, they're already there."

### `customers.json` (~15 customers)

Name, email, address. Simple structured data.

### `historical_orders.json` (~80 orders)

Each order references a customer ID and 1-4 product IDs. Designed so that:
- Certain product pairs co-occur frequently (e.g., "Laptop" + "Mouse" in 10+ orders) to produce meaningful Neo4j recommendations
- Product variety is spread across customers to create interesting graphs
- Some products are popular (high order count), some are rare (low count)

All seed data files are small enough to inspect manually but large enough to produce meaningful results.

---

## Time Budget

| Session | Activity | In-Class | Homework |
|---------|----------|----------|----------|
| Phase 0 | Project setup, FastAPI 101, scaffold tour | 1 hr | -- |
| Phase 1 | Schema design discussion + implementation | 45 min discussion | 2-3 hrs |
| Replication | Existing lesson + project discussion | per existing plan | -- |
| Sharding | Existing lesson + shard key discussion | per existing plan | -- |
| Redis lesson | redis-py hands-on | 30 min | -- |
| Phase 2 | Redis implementation | 30 min walkthrough | 1-1.5 hrs |
| Neo4j lesson | Neo4j driver + Browser | 30 min | -- |
| Phase 3 | Neo4j implementation | 30 min walkthrough | 1.5-2 hrs |
| Wrap-up | Full demo + discussion | 30-45 min | -- |
| **Total** | | **~5 hrs** | **~5-6.5 hrs** |

---

## Technology Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12+ | Application language |
| FastAPI | latest | Web framework (scaffolded) |
| Pydantic | v2 | Request/response validation (scaffolded) |
| SQLAlchemy | 2.0+ | PostgreSQL ORM |
| psycopg2-binary | latest | PostgreSQL driver |
| pymongo | latest | MongoDB driver |
| redis | latest (redis-py) | Redis client |
| neo4j | latest | Neo4j driver |
| pytest | latest | Test framework |
| PostgreSQL | 16 | Relational database |
| MongoDB | 7 | Document database |
| Redis | 7 | Key-value store |
| Neo4j | 5 (community) | Graph database |
| Docker Compose | v2 | Container orchestration |

---

## What's Next

This README defines the **what** and **why**. The next steps are:

1. **Implementation plan** -- detailed specification for `db_access.py` (every method signature, parameters, return types, which databases each method uses) and `postgres_models.py` (complete schema)
2. **Build the scaffold** -- create the actual project skeleton with working FastAPI routes, Docker Compose, seed data, and test suites
3. **Build lesson materials** -- Redis hands-on lesson and Neo4j hands-on lesson as `.md` files following course conventions
4. **Write the instructor guide** -- classroom flow notes, discussion prompts, common student mistakes and how to address them
