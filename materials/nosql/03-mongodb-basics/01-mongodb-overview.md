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
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:7

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

### Inserting Documents

```javascript
// Insert one document
db.products.insertOne({
  name: "Laptop Pro 15",
  price: 1299.99,
  category: "electronics",
  stock: 45,
  specs: {
    ram: "16GB",
    storage: "512GB SSD",
    screen: "15.6 inch"
  },
  tags: ["laptop", "gaming", "portable"]
})

// Insert many documents
db.products.insertMany([
  { name: "Wireless Mouse", price: 29.99, category: "electronics", stock: 200 },
  { name: "USB-C Hub",      price: 49.99, category: "electronics", stock: 150 },
  { name: "Monitor 27\"",   price: 399.99, category: "electronics", stock: 30 }
])
```

MongoDB automatically generates an `_id` field of type `ObjectId` if you don't provide one.

### Finding Documents

```javascript
// Find all documents
db.products.find()

// Find with filter
db.products.find({ category: "electronics" })

// Find with projection (select specific fields)
db.products.find({ category: "electronics" }, { name: 1, price: 1, _id: 0 })

// Find one document
db.products.findOne({ name: "Laptop Pro 15" })

// Query operators
db.products.find({ price: { $gt: 100 } })          // price > 100
db.products.find({ price: { $gte: 100, $lte: 500 } }) // 100 <= price <= 500
db.products.find({ tags: "gaming" })               // array contains "gaming"
db.products.find({ "specs.ram": "16GB" })          // nested field query

// Count
db.products.countDocuments({ category: "electronics" })
```

### Updating Documents

```javascript
// Update one document
db.products.updateOne(
  { name: "Laptop Pro 15" },           // filter
  { $set: { price: 1199.99, stock: 42 } }  // update
)

// Update many documents
db.products.updateMany(
  { category: "electronics" },
  { $inc: { stock: -1 } }              // decrement stock by 1
)

// Upsert: update if exists, insert if not
db.products.updateOne(
  { name: "Keyboard Pro" },
  { $set: { price: 89.99, category: "electronics" } },
  { upsert: true }
)
```

### Deleting Documents

```javascript
// Delete one
db.products.deleteOne({ name: "USB-C Hub" })

// Delete many
db.products.deleteMany({ stock: 0 })
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
| Creating and analyzing indexes | mongosh |
| Running explain plans | mongosh |
| Exploring data interactively | mongosh |
| Application code, connection strings | pymongo |
| Read preferences and write concerns in code | pymongo |
| Observing failover from app perspective | pymongo |

**MongoDB Compass** is a GUI application that gives a visual view of collections, documents, and index usage. It's a convenient exploration tool but all exercises in this course use mongosh or pymongo.

## Summary

- MongoDB stores BSON documents in collections (no fixed schema)
- ObjectId encodes timestamp + machine info + counter for uniqueness without coordination
- mongosh is a JavaScript REPL -- use it for all admin and exploration work
- The pymongo driver for Python handles BSON serialization transparently
- Basic CRUD operations: `insertOne`, `find`, `updateOne`, `deleteOne` -- enough to get started

---

**Next:** [Data Modeling: Embed vs Reference →](02-documents-and-data-modeling.md)

---

[← Back: Choosing the Right Database](../02-nosql-types/05-choosing-the-right-database.md) | [Course Home](../README.md)
