# Indexes and Performance

## Why Indexes Matter

Without an index, MongoDB must examine every document in a collection to find matching results. This is called a **collection scan (COLLSCAN)**. On a collection of 10 million documents, a COLLSCAN reads all 10 million documents for every query -- even if only 5 match.

An index is a separate data structure that maps field values to the documents that contain them. MongoDB can find matching documents by consulting the index first, then fetching only the relevant documents. This is called an **index scan (IXSCAN)**.

If you know SQL indexes, MongoDB indexes follow the same B-tree concept. The key difference: MongoDB indexes work on document fields, including nested fields and array elements.

## How MongoDB Indexes Work

> **Core Concept:** See [Trees for Storage](../../core-concepts/02-data-structures/02-trees-for-storage.md) for how B-trees and B+ trees work -- node structure, depth, why they're optimized for disk, and the difference between clustered and non-clustered indexes.

MongoDB's default index type is a **B-tree** (same as PostgreSQL and SQL Server). MongoDB uses B-trees for the same reason you saw them in SQL indexes -- they provide O(log n) for both point lookups and range scans. Same data structure, applied to documents instead of rows.

The B-tree stores index key values in sorted order, enabling:

- **Equality queries**: Find documents where `price = 1299` → O(log n) lookup
- **Range queries**: Find documents where `price > 500` → O(log n) to find start + sequential scan
- **Sorting**: If the query result must be sorted by an indexed field, the B-tree is already sorted → no sort step needed

```mermaid
graph TD
    Query["Query: price > 500"] --> IndexScan["Index Scan\nB-tree on 'price'"]
    IndexScan --> Locate["Locate first entry > 500\nO(log n)"]
    Locate --> Traverse["Traverse remaining entries\n(sequential, fast)"]
    Traverse --> DocFetch["Fetch matching documents\nby _id reference"]
    DocFetch --> Result["Return results"]
    
    Query2["Query: price > 500 (no index)"] --> CollScan["Collection Scan\nExamine ALL documents"]
    CollScan --> Result2["Return results\n(read entire collection)"]
```

## Index Types

### Single Field Index

Index on one field. Supports equality, range, and sort on that field.

```python
# Create an index on the price field (1 = ascending, -1 = descending)
db.products.create_index([("price", 1)])

# These queries will use the index:
list(db.products.find({"price": 1299}))
list(db.products.find({"price": {"$gt": 500, "$lt": 1000}}))
list(db.products.find({}).sort("price", 1))
```

### Compound Index

Index on multiple fields. The order of fields matters significantly.

```python
import pymongo

# Index on category (ascending) + price (descending)
db.products.create_index([("category", 1), ("price", -1)])

# Queries that use this index:
list(db.products.find({"category": "electronics"}))                               # prefix match
list(db.products.find({"category": "electronics", "price": {"$gt": 500}}))       # both fields
list(db.products.find({"category": "electronics"}).sort("price", -1))            # prefix + sort

# This query CANNOT use the compound index efficiently (doesn't start with 'category'):
list(db.products.find({"price": {"$gt": 500}}))
```

**The ESR Rule** (Equality, Sort, Range): Structure compound indexes so that:
1. **Equality** fields come first (fields queried with `=`)
2. **Sort** fields come next
3. **Range** fields come last (fields with `$gt`, `$lt`, `$in`)

```python
# Query: find electronics, sorted by name, with price > 500
# Optimal compound index follows ESR:
db.products.create_index([
    ("category", 1),   # E: equality (category = "electronics")
    ("name", 1),       # S: sort (sort by name)
    ("price", 1),      # R: range (price > 500)
])
```

### Multikey Index (Arrays)

When you index a field that contains an array, MongoDB creates index entries for each element in the array. This allows efficient queries like "find documents where array contains value X."

```python
# Products have a tags array: ["laptop", "gaming", "portable"]
db.products.create_index([("tags", 1)])   # automatically a multikey index

# Now this query is fast:
list(db.products.find({"tags": "gaming"}))   # finds any document with "gaming" in tags
```

One compound index can only have one multikey field.

### Hashed Index

Instead of the natural value, stores the hash of the field value. Supports only equality queries (no range, no sort). Used primarily as shard keys (covered in the sharding module).

```python
db.users.create_index([("user_id", "hashed")])

# Supports equality:
db.users.find_one({"user_id": "user_42"})

# Does NOT support range:
# db.users.find({"user_id": {"$gt": "user_40"}})  ← won't use the hashed index
```

### TTL Index (Time-To-Live)

Automatically deletes documents after a specified time period. A background process runs every 60 seconds and removes expired documents.

```python
# Delete session documents 30 minutes after their created_at time
db.sessions.create_index([("created_at", 1)], expireAfterSeconds=1800)

# Or expire at a specific datetime stored in the document
db.events.create_index([("expires_at", 1)], expireAfterSeconds=0)
```

### Text Index

Enables full-text search across string fields.

```python
db.articles.create_index([("title", "text"), ("content", "text")])
list(db.articles.find({"$text": {"$search": "mongodb replication"}}))
```

## The `explain()` Method

`explain()` is the most important tool for understanding index usage and query performance. Always use it before and after adding indexes in production.

```python
import pprint

plan = db.products.find(
    {"category": "electronics", "price": {"$gt": 500}}
).explain("executionStats")
pprint.pprint(plan)
```

### Reading the Output

The critical fields to look at:

```javascript
{
  "queryPlanner": {
    "winningPlan": {
      "stage": "FETCH",                    // outer stage: fetch documents by _id
      "inputStage": {
        "stage": "IXSCAN",                 // ← GOOD: using an index
        "keyPattern": { "category": 1, "price": -1 },
        "indexName": "category_1_price_-1",
        "direction": "forward"
      }
    }
  },
  "executionStats": {
    "executionSuccess": true,
    "nReturned": 23,                        // documents returned to client
    "totalKeysExamined": 23,               // index entries examined
    "totalDocsExamined": 23,               // documents fetched from disk
    "executionTimeMillis": 2               // total query time
  }
}
```

**What to look for:**

| Field | Good | Bad |
|-------|------|-----|
| `stage` | `IXSCAN` | `COLLSCAN` |
| `nReturned` vs `totalDocsExamined` | Close to each other | `totalDocsExamined` >> `nReturned` |
| `executionTimeMillis` | Low | High (relative to data size) |
| `totalKeysExamined` vs `nReturned` | Close | Much higher (index not selective) |

**COLLSCAN**: Examined every document in the collection. Add an index.

**`totalDocsExamined` >> `nReturned`**: The index found candidates but the database had to read many documents and discard them. The index may not be selective enough, or you need a better compound index.

## Hands-On Exercise: Index Impact

This exercise demonstrates the difference between a collection scan and an index scan on 100,000 documents. Run each cell in sequence in a Jupyter notebook.

### Setup: Connect and Generate Test Data

```python
from pymongo import MongoClient
import random
import datetime
import pprint
import time

client = MongoClient("mongodb://localhost:27017")
db = client["indexdemo"]

# Drop collection if it exists from a previous run
db.products.drop()

categories = ["electronics", "clothing", "furniture", "books", "sports"]
brands = ["BrandA", "BrandB", "BrandC", "BrandD", "BrandE"]

# Insert 100,000 documents in batches of 1,000
batch = []
now = datetime.datetime.utcnow()
for i in range(100_000):
    batch.append({
        "sku": f"PROD-{i:06d}",
        "name": f"Product {i}",
        "category": categories[i % 5],
        "brand": brands[i % 5],
        "price": round(random.uniform(10, 2010), 2),
        "stock": random.randint(0, 499),
        "created_at": now - datetime.timedelta(seconds=random.randint(0, 365 * 24 * 3600)),
    })
    if len(batch) == 1000:
        db.products.insert_many(batch)
        batch = []

print(db.products.count_documents({}), "documents inserted")  # should be 100,000
```

### Step 1: Query Without an Index (COLLSCAN)

```python
# Check existing indexes — only the default _id index should be present
print(db.products.index_information())

# Run a query and inspect the execution plan
plan = db.products.find(
    {"category": "electronics", "price": {"$gt": 800}}
).explain("executionStats")

stats = plan["executionStats"]
stage = plan["queryPlanner"]["winningPlan"].get("stage", "")
# If nested, find the COLLSCAN stage
if "inputStage" in plan["queryPlanner"]["winningPlan"]:
    stage = plan["queryPlanner"]["winningPlan"]["inputStage"].get("stage", stage)

print(f"Stage:              {stage}")                          # COLLSCAN
print(f"Docs examined:      {stats['totalDocsExamined']}")    # 100,000
print(f"Docs returned:      {stats['nReturned']}")            # ~20,000
print(f"Execution time:     {stats['executionTimeMillis']} ms")  # ~80–300 ms
```

Look at the output:
- `Stage`: should be `COLLSCAN`
- `Docs examined`: 100,000 (scanned entire collection)
- `Docs returned`: ~20,000 (electronics is 1/5 of data, price > 800 is roughly half)
- `Execution time`: probably 80–300 ms

### Step 2: Add an Index and Compare

```python
# Create a compound index following the ESR rule:
# category (equality) comes before price (range)
db.products.create_index([("category", 1), ("price", 1)])

# Run the SAME query again
plan2 = db.products.find(
    {"category": "electronics", "price": {"$gt": 800}}
).explain("executionStats")

stats2 = plan2["executionStats"]
winning = plan2["queryPlanner"]["winningPlan"]
ixscan_stage = winning.get("inputStage", {}).get("stage", winning.get("stage", ""))

print(f"Stage:              {ixscan_stage}")                    # IXSCAN
print(f"Docs examined:      {stats2['totalDocsExamined']}")    # ~20,000
print(f"Docs returned:      {stats2['nReturned']}")
print(f"Execution time:     {stats2['executionTimeMillis']} ms")  # ~10–50 ms
```

Now observe:
- `Stage`: `IXSCAN` (using the index)
- `Docs examined`: ~20,000 (only the documents that actually match)
- `Execution time`: probably 10–50 ms — significantly faster

### Step 3: Covered Query (Even Faster)

A **covered query** is one where the index contains all the fields the query needs — MongoDB never needs to fetch the actual documents.

```python
# This index covers: category (filter), price (filter), name (projection)
db.products.create_index([("category", 1), ("price", 1), ("name", 1)])

# Query that only asks for fields contained in the index
plan3 = db.products.find(
    {"category": "electronics", "price": {"$gt": 800}},
    {"category": 1, "price": 1, "name": 1, "_id": 0}   # project only indexed fields
).explain("executionStats")

stats3 = plan3["executionStats"]
print(f"Docs examined:  {stats3['totalDocsExamined']}")   # 0 — no document fetch!
print(f"Docs returned:  {stats3['nReturned']}")
print(f"Execution time: {stats3['executionTimeMillis']} ms")
```

Look for `Docs examined: 0` — MongoDB served the entire result from the index without reading a single document. This is the fastest possible query.

### Step 4: Observe the Write Cost

```python
# Drop all non-_id indexes to get a clean baseline
db.products.drop_indexes()

# Measure insert time WITHOUT indexes
batch_no_idx = [{"sku": f"BATCH-{i}", "category": "electronics", "price": 999, "stock": 10}
                for i in range(1000)]
t0 = time.time()
db.products.insert_many(batch_no_idx)
t_no_idx = (time.time() - t0) * 1000
print(f"Insert without indexes: {t_no_idx:.0f} ms")

# Recreate the compound index
db.products.create_index([("category", 1), ("price", 1)])

# Measure insert time WITH the index
batch_with_idx = [{"sku": f"BATCH2-{i}", "category": "electronics", "price": 999, "stock": 10}
                  for i in range(1000)]
t1 = time.time()
db.products.insert_many(batch_with_idx)
t_with_idx = (time.time() - t1) * 1000
print(f"Insert with index:      {t_with_idx:.0f} ms")
print(f"Overhead per insert:    {(t_with_idx - t_no_idx) / 1000:.2f} ms")
```

You'll see inserts are slower with indexes — the B-tree must be updated for every write.

## Index Overhead and Best Practices

**Indexes cost:**
- **Write overhead**: Every insert/update/delete must update all indexes on the collection
- **Storage**: Each index is a separate B-tree on disk (can be 10-50% of collection size)
- **Memory**: Frequently used indexes should fit in RAM (WiredTiger cache)

**Index best practices:**
- Index fields used in frequent `find()` filters and `sort()` operations
- Prefer compound indexes over many single-field indexes
- Avoid indexing fields with low cardinality (e.g., a boolean `is_active` field)
- Use `explain()` to verify that your queries use the index you created
- Audit unused indexes with `db.collection.aggregate([{$indexStats: {}}])`

```python
# Find indexes that haven't been used (low or zero accesses.ops)
for stat in db.products.aggregate([{"$indexStats": {}}]):
    print(stat["name"], "→ ops:", stat["accesses"]["ops"])
```

## Connecting to Sharding

**Hashed indexes** are the foundation of MongoDB's hashed sharding. When you create a hashed index on a field and use it as a shard key, MongoDB distributes documents evenly across shards regardless of the field's natural ordering.

This becomes important in the sharding module -- if your shard key is a monotonically increasing value (like a timestamp or auto-increment ID), all new writes land on the same shard. A hashed shard key distributes the writes evenly.

```python
# Preview: hashed index as shard key ensures even write distribution
db.events.create_index([("user_id", "hashed")])
# sh.shardCollection("mydb.events", {"user_id": "hashed"})  ← run in mongosh as admin
```

(Covered in depth in [05 - Sharding Architecture](../05-mongodb-sharding/01-sharding-architecture.md))

## Summary

- Without indexes: COLLSCAN examines every document -- O(n)
- With an index: IXSCAN examines only matching entries -- O(log n) + result set
- **Compound indexes** follow the ESR rule: Equality → Sort → Range
- **Multikey indexes** automatically handle array fields
- **TTL indexes** expire documents automatically
- `explain("executionStats")` is your primary tool for verifying index usage
- **Covered queries** (result entirely from index, `totalDocsExamined: 0`) are the fastest possible
- Indexes speed up reads but slow down writes -- index strategically

---

**Next:** [Replica Set Architecture →](../04-mongodb-replication/01-replica-set-architecture.md)

---

[← Back: Data Modeling](02-documents-and-data-modeling.md) | [Course Home](../README.md)
