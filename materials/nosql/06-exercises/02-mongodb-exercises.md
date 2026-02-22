# MongoDB Exercises

Independent challenges that combine all the MongoDB concepts covered in this course. Work through each exercise on your own, then compare with classmates.

**Prerequisites**: Have the sharded cluster running (`demo-app/sharded-cluster/`).

---

## Exercise 1: Schema Design

**Domain**: A restaurant review platform (similar to Yelp).

The platform has:
- Restaurants (name, address, cuisine, hours, phone, photos)
- Users (name, email, profile photo, join date)
- Reviews (rating 1-5, text, photos, posted by a user, for a restaurant)
- Menus (each restaurant has a menu with categories and items)
- Reservations (user books a table at a restaurant, date/time, party size)

**Your tasks:**

1. Design the MongoDB schema. For each entity, decide:
   - Which fields to embed vs reference
   - What the document structure looks like
   - What the `_id` should be (ObjectId or something meaningful)
   - What collections you'll create

2. Justify each embed vs reference decision. For each, explain why you chose that approach.

3. Show the document structure for:
   - One restaurant with a menu (2 categories, 3 items each)
   - One review
   - One reservation

4. Identify which queries your schema supports efficiently and which it doesn't:
   - "Show me the top 10 highest-rated Italian restaurants in Tel Aviv"
   - "Show me all reviews by user X"
   - "Show me the menu for restaurant Y"
   - "Show me all upcoming reservations for restaurant Z"

**Things to consider:**
- Reviews per restaurant can grow into thousands -- embed or reference?
- Menu items can change frequently -- does this affect your decision?
- A user's review history might be accessed from their profile page -- how does this affect design?

---

## Exercise 2: Index Optimization

**Setup**: Create a collection with 200K documents in mongosh:

```javascript
use restaurant_db

let cuisines = ["italian", "chinese", "mexican", "japanese", "american", "indian"]
let cities = ["tel_aviv", "jerusalem", "haifa", "beer_sheva", "eilat"]

let docs = []
for (let i = 0; i < 200000; i++) {
  docs.push({
    name: "Restaurant " + i,
    city: cities[i % 5],
    cuisine: cuisines[i % 6],
    rating: Math.round((Math.random() * 4 + 1) * 10) / 10,  // 1.0 to 5.0
    price_range: [1,2,3,4][i % 4],   // $ to $$$$
    is_open: i % 7 !== 0,            // ~85% are open
    review_count: Math.floor(Math.random() * 500)
  })
  if (docs.length === 2000) { db.restaurants.insertMany(docs); docs = [] }
}
print(db.restaurants.countDocuments(), "restaurants inserted")
```

**Your tasks** (use `explain("executionStats")` for each):

1. **Query 1**: Find all Italian restaurants in Tel Aviv with rating ≥ 4.0, sorted by rating descending.
   - Run it without an index. Note: stage type, totalDocsExamined, executionTimeMillis.
   - Design the optimal index following the ESR rule. Create it.
   - Run it again. Compare the metrics.

2. **Query 2**: Find open restaurants with price range 1 or 2, sorted by review_count descending.
   - What's the challenge with indexing `is_open` (boolean, low cardinality)?
   - What index would you create? Explain your reasoning.
   - Test it.

3. **Covered query**: Design a query and index combination where `totalDocsExamined: 0`. Show the explain output proving no documents were fetched.

4. **Audit your indexes**:
   ```javascript
   db.restaurants.aggregate([{ $indexStats: {} }])
   ```
   Which indexes have actually been used? Are there any you should drop?

---

## Exercise 3: Replica Set Failover

**Setup**: Start the replica set from `demo-app/replica-set/`.

```bash
cd demo-app/replica-set
docker compose up -d
bash init-replica.sh
```

**Your tasks:**

1. **Identify the current primary**:
   Connect to the replica set URI and find which node is the current primary.
   
   ```
   mongosh "mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=rs0"
   ```

2. **Insert a document and confirm replication**:
   Insert a document on the primary. Wait 1 second. Read it from a secondary and confirm it's there.

3. **Simulate failover**:
   Stop the primary container. Time how long the election takes. Which node becomes the new primary?

4. **Verify data integrity**:
   Connect to the new primary. Confirm all previously inserted data is present. Insert a new document.

5. **Restore and reconcile**:
   Start the stopped container back up. Wait for it to rejoin. Verify it has the document inserted on the new primary during the failover. Explain why: how did it get that document?

6. **Write concern experiment**:
   Write a Python script (or mongosh loop) that inserts 50 documents with `w:1` and 50 documents with `w:majority`. Compare the total time. Calculate the per-operation overhead of majority write concern.

---

## Exercise 4: Shard Key Selection

**Scenario**: You're building a multi-tenant SaaS application. Each tenant is a company using your platform. Your largest customer has 500,000 records; most customers have 100-10,000 records. Total expected data: 50 million records across 5,000 tenants.

You need to shard a `records` collection. Consider these shard key candidates:

**Candidate A**: `{ _id: 1 }` (ranged, ObjectId)

**Candidate B**: `{ tenant_id: 1 }` (ranged)

**Candidate C**: `{ tenant_id: 1, record_id: 1 }` (compound ranged)

**Candidate D**: `{ tenant_id: "hashed" }` (hashed)

**Your tasks:**

1. For each candidate, explain:
   - How data is distributed across shards
   - What queries it supports efficiently (targeted) vs poorly (scatter-gather)
   - What problems it introduces (hot spots, poor cardinality, etc.)

2. Identify the best candidate. Justify your choice based on:
   - Distribution of data (consider that one tenant has 1% of all data)
   - Typical query patterns (most queries filter by tenant_id)
   - Write distribution

3. Are there scenarios where Candidate D (hashed tenant_id) is better than Candidate C? When?

4. **Bonus**: If you chose Candidate C, what is the risk if one tenant grows to 10 million records while others have 1,000? How would you mitigate this?

---

## Exercise 5: Observability Challenge

**Setup**: Use the sharded cluster from `demo-app/sharded-cluster/`.

Answer the following questions using only mongosh commands (`sh.status()`, `explain()`, `getShardDistribution()`, `rs.status()`, etc.):

1. How many total chunks exist in the `events_hashed` collection? How are they distributed?

2. Which shard owns the data for `user_id: "user_0042"`? Verify by running `explain()` on a query for this user.

3. Write a query where `totalDocsExamined` equals exactly `nReturned` (not more). Show the explain output. What does this mean?

4. Find the replication lag between the primary and secondary on shard 1. Is the replica set healthy?
   ```javascript
   // Connect to shard 1 primary
   mongosh "mongodb://localhost:27110"
   rs.printSecondaryReplicationInfo()
   ```

5. What is the oplog window on shard 1's primary? (How many hours does the oplog cover?) If a secondary were down for 2 hours, could it rejoin automatically?

---

[← Back: Theory Exercises](01-nosql-theory-exercises.md) | [Course Home](../README.md)
