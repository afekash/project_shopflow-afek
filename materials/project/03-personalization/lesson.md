# Phase 3: Personalization

## The Situation

ShopFlow is growing. The catalog now has thousands of products. The problem the product team brings to engineering isn't performance or correctness this time — it's discovery.

"Customers can't find things," the Head of Product says. "Search helps when you know what you're looking for. But we want to surface products people didn't know they wanted."

The team has been looking at what other retailers do. The most common approach: *customers who bought this also bought that*. If many orders contain both a laptop and a laptop stand, any customer looking at laptops should be shown laptop stands.

The data to build this already exists. Every order ever placed is in the system. Every order is a signal: these products were wanted by the same person at the same time.

---

## Discussion: How Do You Model "Also Bought"?

You have order history. You need to find products that frequently appear together in orders. Think about how you'd approach this.

**Start with the data you have:**
- An order contains a list of product IDs
- Any pair of products in the same order is a signal: "these were bought together"
- The more orders that contain a given pair, the stronger the signal

**Think about what you're trying to query:**
- Given a product, find all other products that frequently appear with it in orders
- "Frequently" means: rank by how often the pair appears together

**Now model it as a data structure:**
- What is a node? What is an edge? What does the edge represent?
- What property on the edge captures the strength of the relationship?
- When the same pair appears in another order, what happens to the edge?

**Consider the query:**
- You start at one product. You want its neighbors, ranked by edge weight.
- How many hops do you need for basic recommendations? What about "customers who bought X → also bought Y → also bought Z"?
- Write out what this query looks like. Now write what the equivalent SQL would look like. Compare.

**Consider scale:**
- With 50 products there are at most 1,225 possible pairs. With 5,000 products, there are ~12 million.
- The query is always: "give me the top N neighbors of this node." Does that query get slower as the graph grows?
- What about the equivalent SQL self-join as the order history grows?

---

## What You Need to Build

Two methods: one builds the graph from historical order data, one traverses it to produce recommendations.

---

## Definition of Done

### 1. `seed_recommendation_graph`

**What it enables:** Building the co-purchase relationship graph from historical order data.

For every order, every unique pair of products in that order forms a relationship: "these were bought together." If the same pair appears in multiple orders, the strength of that relationship increases by one for each additional order. When `create_order` is called in Phase 1+, it also updates the graph for the new order.

This method is also called by the seed script after historical orders are loaded.

**Signature:**
```python
def seed_recommendation_graph(self, orders: list[dict]) -> None:
    # orders: [{"order_id": int, "product_ids": [int, ...]}, ...]
```

**Accepted when:**
- After seeding, a product that appeared in multiple orders alongside another product has a stronger relationship to it than a product that only co-appeared once
- Products not found in the catalog are silently skipped — no error
- Calling this again with the same orders increments relationship strengths further (it is additive, not idempotent)
- Product nodes store the product name as it was at seeding time

---

### 2. `get_recommendations`

**What it enables:** Returning a ranked list of products to recommend alongside a given product.

Recommendations are ranked by co-purchase frequency: the more often two products appear together in orders, the higher the recommendation score.

**Signature:**
```python
def get_recommendations(self, product_id: int, limit: int = 5) -> list[dict]:
```

**Accepted when:**
- Returns a list of `{"product_id": int, "name": str, "score": int}` dicts
- Sorted by `score` descending (highest co-purchase frequency first)
- The queried product itself is never in the results
- Returns at most `limit` results
- Returns an empty list if the product has no co-purchase relationships

---

## Before You Move On

With the graph in place, explore it:

- Open the graph database browser and visualize the product network. Which products are the most connected?
- Call `GET /products/{id}/recommendations` for a product that appears in many orders. Then call it for a product that appears in only one order. Compare the results.
- Try to write the equivalent query in SQL (hint: you need a self-join on `order_items`, grouped by product pair, sorted by count). Compare the Cypher and SQL versions.

Consider: what would it take to extend recommendations to two hops — "customers who bought X also bought Y, which is also bought alongside Z"? How does that change the Cypher query? How does it change the SQL?
