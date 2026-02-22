# Documents and Data Modeling

## The Central Question: Embed or Reference?

Every MongoDB schema design decision comes down to one question:

> **Should related data be embedded inside a document, or stored separately and referenced?**

This is the MongoDB equivalent of normalization decisions in relational databases, but the trade-offs are different.

```
Embedded (denormalized):          Referenced (normalized):
                                  
{ order: {                        { order: {
    _id: "order_1",                   _id: "order_1",
    customer: {                       customer_id: "user_42",   ← reference
      name: "Alice",                  items: ["prod_1", "prod_2"]
      email: "alice@..."
    },
    items: [                      // customer fetched separately:
      { name: "Laptop",           // db.users.findOne({_id: "user_42"})
        price: 1299 }
    ]
  }
}
```

The right choice depends on how data is accessed, how it changes, and how large it can grow.

## When to Embed

Embedding wins when:

### 1. Data is always accessed together
If you always need the customer's address when you fetch an order, embed the address in the order document. One database round-trip instead of two.

```javascript
// Good: address embedded in order (accessed together)
{
  _id: "order_1",
  customer_id: "user_42",
  shipping_address: {         // snapshot at time of order
    street: "123 Main St",
    city: "Tel Aviv",
    zip: "6120001"
  },
  items: [...]
}
```

Note: embedding the **snapshot** of the address (not a reference) is actually correct here. If the customer later updates their address, old orders should still show the address it was shipped to.

### 2. One-to-one relationships
A user has exactly one profile. A document has exactly one metadata blob.

```javascript
{
  _id: "user_42",
  email: "alice@example.com",
  profile: {                  // always one, always fetched with user
    bio: "Data engineer",
    avatar_url: "https://...",
    theme: "dark"
  }
}
```

### 3. One-to-few relationships
A blog post has a handful of tags. A product has a few images. An order has a handful of line items.

```javascript
{
  _id: "post_1",
  title: "Introduction to MongoDB",
  content: "...",
  tags: ["mongodb", "nosql", "database"],   // few, bounded, accessed with post
  images: [
    { url: "https://cdn.example.com/img1.jpg", alt: "Diagram" }
  ]
}
```

**Rule of thumb**: If the array won't grow beyond ~100 elements, embedding is usually correct.

## When to Reference

Reference (normalize) when:

### 1. One-to-many with unbounded growth
A user's comment history can grow without limit. Embedding all comments inside the user document would eventually hit the 16MB document size limit.

```javascript
// Bad: unbounded array in user document
{ _id: "user_42", comments: [ ...potentially thousands... ] }

// Good: comments as separate documents with reference to user
// comments collection:
{ _id: "comment_1", user_id: "user_42", post_id: "post_1", text: "Great article!", created_at: ISODate("2024-01-15") }
{ _id: "comment_2", user_id: "user_42", post_id: "post_2", text: "Helpful!", created_at: ISODate("2024-01-16") }
```

### 2. Many-to-many relationships
A student enrolls in many courses. A course has many students. This is naturally a join table in SQL; in MongoDB, you reference in one or both directions.

```javascript
// students collection
{ _id: "student_1", name: "Alice", enrolled_course_ids: ["course_101", "course_202"] }

// courses collection  
{ _id: "course_101", title: "Data Engineering", enrolled_count: 45 }
```

### 3. Data changes independently
A product's price changes frequently. If you embed the product details in every order, you'd need to update all orders when the price changes -- or you'd have inconsistent historical data. Better to store product details separately and only embed a snapshot at order time.

```javascript
// products collection (source of truth, changes over time)
{ _id: "prod_1", name: "Laptop Pro 15", price: 1199.99, stock: 42 }

// orders collection (snapshot at time of purchase)
{ _id: "order_1", items: [{ product_id: "prod_1", name: "Laptop Pro 15", price_paid: 1299.99 }] }
```

### 4. Data accessed independently
If you sometimes query users without needing their full order history, and sometimes query orders without needing the full user profile, keeping them separate avoids loading data you don't need.

## The 16MB Document Limit

MongoDB enforces a **16MB maximum document size**. This is both a practical limit and a design guardrail -- documents that approach this size have almost certainly been modeled incorrectly.

A 16MB document with embedded arrays likely has an unbounded growth problem that should be resolved by storing those arrays as separate documents.

**Practical limits that trigger a redesign:**
- An array with thousands of elements → extract to a collection with a reference
- A document that grows over time (append-only arrays) → extract to a collection
- A document that is often partially loaded → consider splitting into multiple documents

## Practical Example: E-Commerce System

Let's model a product catalog and order system, applying these principles.

### Products Collection

```javascript
// Product with embedded variants (one-to-few: most products have < 20 variants)
{
  _id: ObjectId("65f1234567890abcdef12345"),
  sku: "LAPTOP-PRO-15",
  name: "Laptop Pro 15",
  category: "electronics",
  brand: "TechBrand",
  description: "Professional laptop for developers",
  base_price: 1299.99,
  tags: ["laptop", "professional", "15-inch"],
  images: [
    { url: "https://cdn.example.com/laptop-front.jpg", primary: true },
    { url: "https://cdn.example.com/laptop-side.jpg", primary: false }
  ],
  variants: [
    { color: "Silver", ram: "16GB", storage: "512GB", sku_suffix: "SIL-16-512", stock: 45, price_modifier: 0 },
    { color: "Space Gray", ram: "32GB", storage: "1TB", sku_suffix: "GRY-32-1TB", stock: 12, price_modifier: 400 }
  ],
  specs: {
    screen_size: "15.6 inch",
    processor: "Intel Core i7-13th Gen",
    weight_kg: 1.8
  },
  created_at: ISODate("2024-01-01"),
  updated_at: ISODate("2024-02-15")
}
```

Variants are embedded because: they're always fetched with the product, bounded in number, and part of the same business entity.

### Orders Collection

```javascript
// Order with embedded line items (snapshot pattern)
{
  _id: ObjectId("65f9876543210fedcba98765"),
  order_number: "ORD-2024-001234",
  customer_id: ObjectId("65fabc123456789012345678"),  // reference to users
  status: "shipped",
  
  // Snapshot of shipping address at time of order
  shipping_address: {
    street: "123 Main St",
    city: "Tel Aviv",
    country: "IL",
    zip: "6120001"
  },
  
  // Embedded line items: snapshot of product details + price at time of purchase
  items: [
    {
      product_id: ObjectId("65f1234567890abcdef12345"),  // reference for lookup
      sku: "LAPTOP-PRO-15-SIL-16-512",
      name: "Laptop Pro 15 (Silver, 16GB, 512GB)",       // snapshot
      unit_price: 1299.99,                               // price at time of purchase
      quantity: 1,
      subtotal: 1299.99
    }
  ],
  
  subtotal: 1299.99,
  tax: 260.00,
  total: 1559.99,
  
  // Snapshot of payment info (not sensitive data)
  payment: {
    method: "credit_card",
    last_four: "4242",
    status: "captured"
  },
  
  created_at: ISODate("2024-02-20"),
  shipped_at: ISODate("2024-02-22")
}
```

**Design decisions explained:**
- `customer_id` is a reference (customer data accessed independently, customer profile changes over time)
- `shipping_address` is embedded as a snapshot (order history should show where it was shipped, not where the customer lives now)
- `items` are embedded as snapshots (price at purchase matters, product details at purchase matter for returns/receipts)
- `product_id` is kept in each item for lookups but we don't rely on it for the order's content

## Schema Validation

MongoDB lets you optionally define validation rules using JSON Schema. This gives you the benefits of schema flexibility (easy to evolve) with some enforcement on critical fields.

```javascript
db.createCollection("orders", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["customer_id", "items", "total", "status"],
      properties: {
        customer_id: { bsonType: "objectId" },
        status: {
          bsonType: "string",
          enum: ["pending", "confirmed", "shipped", "delivered", "cancelled"]
        },
        total: { bsonType: "number", minimum: 0 },
        items: {
          bsonType: "array",
          minItems: 1,
          items: {
            bsonType: "object",
            required: ["product_id", "quantity", "unit_price"],
            properties: {
              quantity: { bsonType: "int", minimum: 1 },
              unit_price: { bsonType: "number", minimum: 0 }
            }
          }
        }
      }
    }
  },
  validationAction: "error"  // reject invalid documents (or "warn" to log only)
})
```

This is optional and additive -- you can add validation to existing collections without modifying existing documents.

## Common Anti-Patterns

### Unbounded Arrays
```javascript
// Bad: array grows forever, will hit 16MB limit
{ _id: "user_42", activity_log: [ ...thousands of events... ] }

// Fix: separate collection
{ _id: "event_1", user_id: "user_42", type: "login", timestamp: ISODate("...") }
```

### Deeply Nested Documents
```javascript
// Bad: hard to query, hard to update, violates "you'll need to query this" rule
{ order: { customer: { address: { billing: { street: { ... } } } } } }

// Fix: flatten where possible, split into separate documents where logical
```

### Using MongoDB as a Relational Database
```javascript
// Bad: you've recreated foreign keys with no enforcement
{ _id: "order_1", customer_id: "user_42", product_ids: ["prod_1", "prod_2"] }
// This requires two more queries to assemble a complete order view.
// If you're doing this for every entity, use PostgreSQL.

// Fix: embed what's always accessed together, reference what's independent
```

### Polymorphic Collections Without a Type Field

```javascript
// Bad: can't tell what type a document is
{ _id: 1, data: "..." }
{ _id: 2, content: "..." }

// Good: include a discriminator field
{ _id: 1, type: "article", title: "...", content: "..." }
{ _id: 2, type: "video", title: "...", video_url: "...", duration: 342 }
```

## Key Takeaways

- **Embed** when data is always accessed together, bounded in size, and part of the same entity
- **Reference** when data grows unboundedly, changes independently, or is accessed separately
- **Snapshot** relational data at the point of a transaction (orders capture prices and addresses at purchase time)
- The 16MB document limit is a design guardrail -- hitting it means rethink the model
- Schema validation is optional but useful for critical fields in production

---

**Next:** [Indexes and Performance →](03-indexes-and-performance.md)

---

[← Back: MongoDB Overview](01-mongodb-overview.md) | [Course Home](../README.md)
