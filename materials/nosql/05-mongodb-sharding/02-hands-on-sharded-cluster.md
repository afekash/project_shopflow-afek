# Hands-On: Sharded Cluster

## Setup

All infrastructure is in `demo-app/sharded-cluster/`. This cluster takes about 2 minutes to initialize.

```bash
cd materials/nosql/demo-app/sharded-cluster
docker compose up -d
bash init-sharding.sh
```

The init script will:
1. Initialize the config server replica set
2. Initialize shard 1 and shard 2 as replica sets
3. Register both shards with mongos
4. Create two sharded collections: `events_hashed` and `events_ranged`
5. Insert 50,000 test documents into each

```bash
docker compose ps
# 10 containers: cfg1/2/3, shard1a/b/c, shard2a/b/c, mongos
```

Connect to the cluster via `mongos` -- this is the single entry point for all operations:

```javascript
mongosh "mongodb://localhost:27017"
```

## Exercise 1: Explore the Cluster with sh.status()

`sh.status()` is your primary tool for understanding the state of a sharded cluster. It shows which shards exist, which collections are sharded, and how chunks are distributed.

```javascript
sh.status()
```

Key sections in the output:

**Shards section** -- lists registered shards:
```
shards:
  {  _id: 'shard1rs',  host: 'shard1rs/shard1a:27017,shard1b:27017,shard1c:27017',  state: 1 }
  {  _id: 'shard2rs',  host: 'shard2rs/shard2a:27017,shard2b:27017,shard2c:27017',  state: 1 }
```

**Databases section** -- shows which databases have sharding enabled:

```
databases:
  {  _id: 'demo',  primary: 'shard1rs',  partitioned: true }
```

**Collections section** -- shows sharded collections and their chunk distribution:
```
demo.events_hashed
  shard key: { user_id: 'hashed' }
  chunks:
    shard1rs: 2
    shard2rs: 2
  
demo.events_ranged
  shard key: { user_id: 1 }
  chunks:
    shard1rs: 1
    shard2rs: 1
```

Now check chunk distribution for a specific collection:
```javascript
use demo
db.events_hashed.getShardDistribution()
```

Output:
```
Shard shard1rs at shard1rs/shard1a:27017,...
 data : 14.12MiB docs : 25234 estimated data per chunk : 7.06MiB
Shard shard2rs at shard2rs/shard2a:27017,...
 data : 13.98MiB docs : 24766 estimated data per chunk : 6.99MiB
Totals
 data : 28.1MiB docs : 50000 chunks : 4
 Shard shard1rs contains 50.47% data, 50.47% docs in cluster, avg obj size on shard : 571B
 Shard shard2rs contains 49.53% data, 49.53% docs in cluster, avg obj size on shard : 573B
```

**The hashed collection is split almost exactly 50/50 between shards** -- this is the hashed sharding strategy working correctly.

## Exercise 2: Shard Key in Filter → Targeted Query

A query that includes the shard key lets `mongos` route to exactly the right shard.

```javascript
// Query with shard key: mongos knows which shard owns user_0001
db.events_hashed.find({ user_id: "user_0001" }).explain("executionStats")
```

Read the explain output carefully:

```javascript
{
  "queryPlanner": {
    "mongosPlannerVersion": 1,
    "winningPlan": {
      "stage": "SINGLE_SHARD",       // ← Only ONE shard was contacted
      "shards": [
        {
          "shardName": "shard1rs",   // ← Routed to shard1 specifically
          "connectionString": "shard1rs/shard1a:27017,...",
          "winningPlan": {
            "stage": "FETCH",
            "inputStage": { "stage": "IXSCAN", "indexName": "user_id_hashed" }
          }
        }
      ]
    }
  },
  "executionStats": {
    "nReturned": 50,                 // 50 events for user_0001
    "totalKeysExamined": 50,
    "totalDocsExamined": 50,
    "executionTimeMillis": 3         // Fast: only 1 shard queried
  }
}
```

`**SINGLE_SHARD**`: `mongos` used the hashed shard key to determine that `user_0001`'s data lives on `shard1rs` and routed the query there exclusively. `shard2rs` was never contacted.

Try different users and observe they route to different shards:
```javascript
db.events_hashed.find({ user_id: "user_0500" }).explain("executionStats")
// Check winningPlan.shards[0].shardName -- might route to shard2rs
```

## Exercise 3: No Shard Key → Scatter-Gather

Now query without the shard key -- `mongos` has no choice but to ask every shard.

```javascript
// Query WITHOUT shard key: mongos must ask all shards
db.events_hashed.find({ event_type: "purchase" }).explain("executionStats")
```

Output:
```javascript
{
  "queryPlanner": {
    "winningPlan": {
      "stage": "SHARD_MERGE",        // ← Multiple shards contacted, results merged
      "shards": [
        {
          "shardName": "shard1rs",   // ← Shard 1 queried
          "winningPlan": { "stage": "COLLSCAN" }  // full scan on this shard
        },
        {
          "shardName": "shard2rs",   // ← Shard 2 ALSO queried
          "winningPlan": { "stage": "COLLSCAN" }  // full scan on this shard too
        }
      ]
    }
  },
  "executionStats": {
    "nReturned": 12502,
    "totalDocsExamined": 50000,      // ← Examined ALL 50K documents across both shards
    "executionTimeMillis": 45        // Slower: both shards scanned, results merged
  }
}
```

`**SHARD_MERGE**`: `mongos` had to ask both shards, each performed a collection scan, and `mongos` merged the results. The query touched 50,000 documents to return ~12,500 -- a full scatter-gather.

**Performance comparison**:


| Query                        | Stage        | Shards Contacted | Docs Examined | Time  |
| ---------------------------- | ------------ | ---------------- | ------------- | ----- |
| `{ user_id: "user_0001" }`   | SINGLE_SHARD | 1                | 50            | ~3ms  |
| `{ event_type: "purchase" }` | SHARD_MERGE  | 2                | 50,000        | ~45ms |


This is why shard key selection matters: your most frequent queries should include the shard key.

## Exercise 4: Adding an Index on a Sharded Collection

Even with sharding, you still need indexes for efficient queries within each shard. Create an index on `event_type`:

```javascript
// Create an index on event_type (applies to ALL shards automatically)
db.events_hashed.createIndex({ event_type: 1 })

// Now run the scatter-gather query again
db.events_hashed.find({ event_type: "purchase" }).explain("executionStats")
```

Updated output:

```javascript
{
  "winningPlan": {
    "stage": "SHARD_MERGE",          // still scatter-gather (no shard key)
    "shards": [
      { "shardName": "shard1rs",
        "winningPlan": { "stage": "FETCH",
          "inputStage": { "stage": "IXSCAN", "indexName": "event_type_1" }
        }
      },
      { "shardName": "shard2rs",
        "winningPlan": { "stage": "FETCH",
          "inputStage": { "stage": "IXSCAN", "indexName": "event_type_1" }  
        }
      }
    ]
  },
  "executionStats": {
    "nReturned": 12502,
    "totalDocsExamined": 12502,      // ← Only examined matching docs
    "executionTimeMillis": 18        // Faster: index used on each shard
  }
}
```

It's still `SHARD_MERGE` (both shards contacted) but now each shard uses its local index -- `totalDocsExamined` dropped from 50,000 to 12,502. Scatter-gather + good indexes is acceptable; scatter-gather + collection scan is not.

## Exercise 5: Hashed vs Ranged Distribution

Compare how hashed and ranged sharding distribute data differently.

```javascript
// Hashed collection distribution
db.events_hashed.getShardDistribution()
// Expect: ~50% on each shard (hashed shard key distributes evenly)

// Ranged collection distribution
db.events_ranged.getShardDistribution()
// Because user_id is "user_0001" to "user_1000" alphabetically,
// the split point matters. Initial chunks may be uneven.
```

Now observe the range query behavior:

```javascript
// Range query on ranged collection
db.events_ranged.find({
  user_id: { $gte: "user_0001", $lte: "user_0100" }
}).explain("executionStats")
// May be SINGLE_SHARD if the range falls within one shard's key range
// or SHARD_MERGE if it spans the shard boundary

// Same range query on hashed collection
db.events_hashed.find({
  user_id: { $gte: "user_0001", $lte: "user_0100" }
}).explain("executionStats")
// Will be SHARD_MERGE: hashing destroys ordering, can't do targeted range queries
```

**Key insight**: Hashed sharding gives you even write distribution but costs you range query efficiency. Ranged sharding preserves range query locality but risks hot spots on monotonic keys.

## Exercise 6: Connect via pymongo (Application View)

The application doesn't need to know about shards at all -- it just connects to `mongos`:

```bash
cd demo-app/app
python sharding_demo.py
```

The script demonstrates:

1. Connecting through mongos (transparent to the application)
2. Inserting data (mongos routes to correct shard)
3. Reading data with and without shard key (mongos handles routing)
4. Verifying which shard actually stored specific documents

```python
from pymongo import MongoClient

# Application connects to mongos only -- no shard addresses
client = MongoClient("mongodb://localhost:27017")
db = client["demo"]

# Insert -- mongos decides which shard based on user_id hash
db.events_hashed.insert_one({
    "user_id": "user_0042",
    "event_type": "purchase",
    "timestamp": datetime.now()
})

# Query -- mongos routes to shard that owns user_0042
result = db.events_hashed.find_one({"user_id": "user_0042"})
```

## Exercise 7: Tracing Query Routing in Logs

Enable profiling on mongos to see routing decisions in logs:

```javascript
// Enable verbose logging for query routing
db.setProfilingLevel(2)   // profile all operations

// Run a query
db.events_hashed.find({ user_id: "user_0001" }).toArray()

// View the profile log
db.system.profile.find().sort({ ts: -1 }).limit(1).pretty()
```

Or watch the mongos container logs directly as you run queries:

```bash
# In a separate terminal, watch mongos logs
docker logs mongos -f --tail=0
```

In another terminal, run queries:

```javascript
mongosh "mongodb://localhost:27017"
use demo
db.events_hashed.find({ user_id: "user_0001" }).toArray()
db.events_hashed.find({ event_type: "purchase" }).toArray()
```

The mongos logs will show which shards were contacted for each query, confirming what `explain()` told you.

## Understanding the sh.status() Chunk Map

After exercises, the balancer may have run and created more chunks. Check again:

```javascript
sh.status()
```

Look for the `chunks:` section under each sharded collection. With 50K documents at ~573 bytes average:

- Total data: ~28MB per collection
- Default chunk size: 128MB
- Expected: 1 chunk per shard initially (data too small to trigger splits)

If you insert millions of documents, you'd see chunks split and the balancer move them:

```javascript
// Watch the balancer running
sh.isBalancerRunning()    // true when actively moving chunks

// See recent balancer operations in the config database
use config
db.changelog.find({ what: "moveChunk.from" }).sort({ time: -1 }).limit(5).pretty()
```

## Cleanup

```bash
cd demo-app/sharded-cluster
docker compose down -v    # removes all containers and data volumes
```

## Key Takeaways

- Applications connect to `mongos` only -- shards are transparent to the application
- `sh.status()` and `getShardDistribution()` are your primary observability tools
- **Targeted queries** (`SINGLE_SHARD`) use the shard key to route to exactly the right shard -- fast
- **Scatter-gather** (`SHARD_MERGE`) queries without the shard key hit all shards -- use indexes to mitigate
- Adding an index on a sharded collection creates the index on all shards automatically
- **Hashed sharding**: even write distribution, range queries always scatter-gather
- **Ranged sharding**: range queries can be targeted, monotonic keys risk hot spots
- The balancer continuously moves chunks to maintain even distribution -- it's invisible to applications

---

**Next:** [Theory Exercises →](../06-exercises/01-nosql-theory-exercises.md)

---

[← Back: Sharding Architecture](01-sharding-architecture.md) | [Course Home](../README.md)