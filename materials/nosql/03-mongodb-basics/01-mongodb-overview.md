# MongoDB Overview and Setup

## What Is MongoDB?

MongoDB is the most popular document store and one of the most widely deployed NoSQL databases. Founded in 2007 (originally called 10gen), it was built to address the schema rigidity and horizontal scaling limitations of relational databases for web-scale applications.

Today MongoDB is used at scale by companies like Adobe, eBay, Forbes, and LinkedIn for use cases ranging from content management to real-time analytics.

## Core Concepts: From SQL to MongoDB

If you know SQL, this mapping will orient you quickly:

| SQL | MongoDB | Notes |
|-----|---------|-------|
| Database | Database | Same concept |
| Table | Collection | No enforced schema |
| Row | Document | BSON, up to 16MB |
| Column | Field | Can be nested, array |
| Primary key | `_id` field | Auto-generated ObjectId if omitted |
| Foreign key | Reference (manual) or embedded | No JOIN enforcement |
| INDEX | Index | B-tree by default |
| VIEW | View | Aggregation pipeline |
| Stored procedure | Server-side JS (rare) | Generally avoided |

## BSON: Why Not Plain JSON?

MongoDB stores documents in **BSON** (Binary JSON). While JSON is text-based, BSON is a binary format that:

- **Adds types** that JSON doesn't support: `Date`, `ObjectId`, `Binary`, `Decimal128`, `int32`, `int64`
- **Is faster to parse**: The binary format is directly machine-readable, not text that needs parsing
- **Is traversable**: BSON encodes the length of each field, so the parser can skip to any field without reading the entire document

```
JSON:  { "name": "Alice", "age": 32 }
       Text string, 26 bytes

BSON:  \x1b\x00\x00\x00          (document length: 27 bytes)
       \x02 name\x00 \x06\x00\x00\x00 Alice\x00   (string field: name)
       \x10 age\x00  \x20\x00\x00\x00              (int32 field: age = 32)
       \x00                                         (document terminator)
```

When you work with MongoDB, you use JSON syntax in mongosh and Python dicts in pymongo -- the driver handles BSON serialization transparently.

## Setting Up MongoDB with Docker

Start a single MongoDB node (for this module; replica sets and sharding come later):

```bash
docker run --rm -d --name mongodb -p 27017:27017 mongo:8

# Verify it's running
docker ps | grep mongodb
docker logs mongodb
```

MongoDB is now accessible at `mongodb://localhost:27017`.

## Connecting with mongosh

`mongosh` is the official MongoDB shell. It's a JavaScript REPL with MongoDB-specific helpers.

```bash
# Connect to local instance
mongosh "mongodb://localhost:27017"

# Or simply
mongosh
```

You should see:
```
Current Mongosh Log ID: 65f1234567890abcdef12345
Connecting to: mongodb://127.0.0.1:27017/?directConnection=true
Using MongoDB: 7.0.x
Using Mongosh: 2.x.x

test>
```

### Navigating the Shell

```javascript
// Show all databases
show dbs

// Switch to a database (creates it when you first insert data)
use ecommerce

// Show collections in the current database
show collections

// Show current database
db

// Exit
exit
```

## Working with Documents: Quick Reference

This is enough to work through the exercises. We won't go deep on query syntax -- the goal is to understand the architecture.

All examples below use **pymongo**, Python's MongoDB driver. Run these in a Jupyter notebook or Python script. Start every session with this setup cell:

```python
from pymongo import MongoClient
from bson import ObjectId
import datetime

# Connect to the local MongoDB instance
client = MongoClient("mongodb://localhost:27017")
db = client["ecommerce"]  # created automatically on first write
```

### Inserting Documents

```python
# Insert one document
result = db.products.insert_one({
    "name": "Laptop Pro 15",
    "price": 1299.99,
    "category": "electronics",
    "stock": 45,
    "specs": {
        "ram": "16GB",
        "storage": "512GB SSD",
        "screen": "15.6 inch"
    },
    "tags": ["laptop", "gaming", "portable"]
})
print(result.inserted_id)   # MongoDB-generated ObjectId

# Insert many documents
result = db.products.insert_many([
    {"name": "Wireless Mouse", "price": 29.99,  "category": "electronics", "stock": 200},
    {"name": "USB-C Hub",      "price": 49.99,  "category": "electronics", "stock": 150},
    {"name": 'Monitor 27"',    "price": 399.99, "category": "electronics", "stock": 30},
])
print(result.inserted_ids)  # list of ObjectIds
```

MongoDB automatically generates an `_id` field of type `ObjectId` if you don't provide one.

### Finding Documents

```python
# Find all documents (returns a cursor; convert to list to print)
all_products = list(db.products.find())

# Find with filter
electronics = list(db.products.find({"category": "electronics"}))

# Find with projection (include only name and price, exclude _id)
names_prices = list(db.products.find(
    {"category": "electronics"},
    {"name": 1, "price": 1, "_id": 0}
))

# Find one document
laptop = db.products.find_one({"name": "Laptop Pro 15"})

# Query operators
over_100       = list(db.products.find({"price": {"$gt": 100}}))           # price > 100
mid_range      = list(db.products.find({"price": {"$gte": 100, "$lte": 500}}))  # 100–500
gaming_laptops = list(db.products.find({"tags": "gaming"}))                # array contains value
ram_16gb       = list(db.products.find({"specs.ram": "16GB"}))             # nested field

# Count
count = db.products.count_documents({"category": "electronics"})
print(f"{count} electronics products")
```

### Updating Documents

```python
# Update one document
result = db.products.update_one(
    {"name": "Laptop Pro 15"},               # filter
    {"$set": {"price": 1199.99, "stock": 42}}  # update
)
print(f"Matched: {result.matched_count}, Modified: {result.modified_count}")

# Update many documents
result = db.products.update_many(
    {"category": "electronics"},
    {"$inc": {"stock": -1}}   # decrement stock by 1
)
print(f"Modified: {result.modified_count} documents")

# Upsert: update if exists, insert if not
db.products.update_one(
    {"name": "Keyboard Pro"},
    {"$set": {"price": 89.99, "category": "electronics"}},
    upsert=True
)
```

### Deleting Documents

```python
# Delete one document
result = db.products.delete_one({"name": "USB-C Hub"})
print(f"Deleted: {result.deleted_count}")

# Delete many documents
result = db.products.delete_many({"stock": 0})
print(f"Deleted: {result.deleted_count} out-of-stock products")
```

## Useful Admin Commands

```javascript
// Database stats
db.stats()

// Collection stats (document count, storage size, index sizes)
db.products.stats()

// Current operations
db.currentOp()

// MongoDB server info
db.serverStatus()

// List all indexes on a collection
db.products.getIndexes()

// Explain a query (covered in depth in the indexes module)
db.products.find({ price: { $gt: 500 } }).explain("executionStats")
```

## Tool Choice Reminder

| Task | Tool |
|------|------|
| Cluster administration, checking replica set status | mongosh |
| Server stats, oplog inspection | mongosh |
| CRUD operations, queries, aggregations | pymongo |
| Index creation and performance analysis | pymongo |
| Read preferences and write concerns in code | pymongo |
| Observing failover from app perspective | pymongo |

**MongoDB Compass** is a GUI application that gives a visual view of collections, documents, and index usage. It's a convenient exploration tool but all exercises in this course use pymongo (for data work) or mongosh (for admin).

## Summary

- MongoDB stores BSON documents in collections (no fixed schema)
- ObjectId encodes timestamp + machine info + counter for uniqueness without coordination
- mongosh is a JavaScript REPL -- use it for cluster administration and oplog inspection
- The pymongo driver for Python handles BSON serialization transparently; use it for all CRUD and queries
- Basic CRUD: `insert_one`, `find`, `update_one`, `delete_one` -- enough to get started

---

**Next:** [Data Modeling: Embed vs Reference →](02-documents-and-data-modeling.md)

---

[← Back: Choosing the Right Database](../02-nosql-types/05-choosing-the-right-database.md) | [Course Home](../README.md)
