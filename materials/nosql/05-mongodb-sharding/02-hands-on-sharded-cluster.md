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

Connect to the cluster via `mongos` -- this is the single entry point for all operations.

For admin/cluster commands use mongosh:

```javascript
mongosh "mongodb://localhost:27017"
```

For all data operations use Python. Run this setup cell once before starting the exercises:

```python
from pymongo import MongoClient
import datetime
import pprint

# Connect through mongos — shards are completely transparent
client = MongoClient("mongodb://localhost:27017")
db = client["demo"]
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

```python
# Query with shard key: mongos knows which shard owns user_0001
plan = db.events_hashed.find({"user_id": "user_0001"}).explain("executionStats")

winning = plan["queryPlanner"]["winningPlan"]
stats   = plan["executionStats"]

print("Stage:         ", winning["stage"])                  # SINGLE_SHARD
print("Shard routed:  ", winning["shards"][0]["shardName"]) # shard1rs (or shard2rs)
print("Docs examined: ", stats["totalDocsExamined"])        # 50
print("Docs returned: ", stats["nReturned"])                # 50
print("Time (ms):     ", stats["executionTimeMillis"])      # ~3 ms
```

Expected explain output (annotated):
```
Stage:          SINGLE_SHARD        ← Only ONE shard was contacted
Shard routed:   shard1rs            ← Routed to shard1 specifically
Docs examined:  50
Docs returned:  50
Time (ms):      3                   ← Fast: only 1 shard queried
```

**`SINGLE_SHARD`**: `mongos` used the hashed shard key to determine that `user_0001`'s data lives on `shard1rs` and routed the query there exclusively. `shard2rs` was never contacted.

Try different users and observe they may route to different shards:

```python
for uid in ["user_0001", "user_0500", "user_0999"]:
    plan = db.events_hashed.find({"user_id": uid}).explain("executionStats")
    shard = plan["queryPlanner"]["winningPlan"]["shards"][0]["shardName"]
    print(f"{uid}  →  {shard}")
```

## Exercise 3: No Shard Key → Scatter-Gather

Now query without the shard key -- `mongos` has no choice but to ask every shard.

```python
# Query WITHOUT shard key: mongos must contact all shards
plan = db.events_hashed.find({"event_type": "purchase"}).explain("executionStats")

winning = plan["queryPlanner"]["winningPlan"]
stats   = plan["executionStats"]

print("Stage:          ", winning["stage"])       # SHARD_MERGE
shards_hit = [s["shardName"] for s in winning["shards"]]
print("Shards queried: ", shards_hit)             # ['shard1rs', 'shard2rs']
shard_stages = [s["winningPlan"]["stage"] for s in winning["shards"]]
print("Per-shard stage:", shard_stages)           # ['COLLSCAN', 'COLLSCAN']
print("Docs examined:  ", stats["totalDocsExamined"])  # 50,000
print("Docs returned:  ", stats["nReturned"])          # ~12,500
print("Time (ms):      ", stats["executionTimeMillis"]) # ~45 ms
```

Expected output:
```
Stage:           SHARD_MERGE          ← Multiple shards contacted, results merged
Shards queried:  ['shard1rs', 'shard2rs']
Per-shard stage: ['COLLSCAN', 'COLLSCAN']  ← full scan on each shard
Docs examined:   50000                ← ALL 50K documents across both shards
Docs returned:   12502
Time (ms):       45                   ← Slower: both shards scanned, results merged
```

**`SHARD_MERGE`**: `mongos` had to ask both shards, each performed a collection scan, and `mongos` merged the results. The query touched 50,000 documents to return ~12,500 -- a full scatter-gather.

**Performance comparison**:


| Query                        | Stage        | Shards Contacted | Docs Examined | Time  |
| ---------------------------- | ------------ | ---------------- | ------------- | ----- |
| `{ user_id: "user_0001" }`   | SINGLE_SHARD | 1                | 50            | ~3ms  |
| `{ event_type: "purchase" }` | SHARD_MERGE  | 2                | 50,000        | ~45ms |


This is why shard key selection matters: your most frequent queries should include the shard key.

## Exercise 4: Adding an Index on a Sharded Collection

Even with sharding, you still need indexes for efficient queries within each shard. Create an index on `event_type`:

```python
# create_index() on a sharded collection propagates to ALL shards automatically
db.events_hashed.create_index([("event_type", 1)])
print("Index created on all shards")

# Run the scatter-gather query again — same query, now with an index
plan2 = db.events_hashed.find({"event_type": "purchase"}).explain("executionStats")

winning2 = plan2["queryPlanner"]["winningPlan"]
stats2   = plan2["executionStats"]

print("Stage:          ", winning2["stage"])         # still SHARD_MERGE (no shard key)
per_shard = [(s["shardName"], s["winningPlan"].get("inputStage", {}).get("stage", s["winningPlan"]["stage"]))
             for s in winning2["shards"]]
print("Per-shard stage:", per_shard)                 # [('shard1rs', 'IXSCAN'), ('shard2rs', 'IXSCAN')]
print("Docs examined:  ", stats2["totalDocsExamined"])  # 12,502 — down from 50,000!
print("Docs returned:  ", stats2["nReturned"])          # 12,502
print("Time (ms):      ", stats2["executionTimeMillis"]) # ~18 ms
```

Expected output:
```
Stage:           SHARD_MERGE          ← still scatter-gather (no shard key)
Per-shard stage: [('shard1rs', 'IXSCAN'), ('shard2rs', 'IXSCAN')]
Docs examined:   12502                ← down from 50,000!
Docs returned:   12502
Time (ms):       18                   ← faster: index used on each shard
```

It's still `SHARD_MERGE` (both shards contacted) but now each shard uses its local index -- `totalDocsExamined` dropped from 50,000 to 12,502. Scatter-gather + good indexes is acceptable; scatter-gather + collection scan is not.

## Exercise 5: Hashed vs Ranged Distribution

Compare how hashed and ranged sharding distribute data differently. Use mongosh for the distribution overview (admin):

```javascript
// In mongosh
use demo
db.events_hashed.getShardDistribution()
// Expect: ~50% on each shard (hashed key distributes evenly)

db.events_ranged.getShardDistribution()
// May be uneven — the split point between alphabetical ranges determines distribution
```

Now observe range query routing behavior using Python:

```python
# Range query on ranged collection
# May be SINGLE_SHARD if the range falls within one shard's key range,
# or SHARD_MERGE if it spans the boundary
plan_ranged = db.events_ranged.find({
    "user_id": {"$gte": "user_0001", "$lte": "user_0100"}
}).explain("executionStats")

print("=== Ranged collection, range query ===")
print("Stage:", plan_ranged["queryPlanner"]["winningPlan"]["stage"])
print("Docs examined:", plan_ranged["executionStats"]["totalDocsExamined"])

# Same range query on hashed collection
# Will always be SHARD_MERGE: hashing destroys ordering
plan_hashed = db.events_hashed.find({
    "user_id": {"$gte": "user_0001", "$lte": "user_0100"}
}).explain("executionStats")

print("\n=== Hashed collection, range query ===")
print("Stage:", plan_hashed["queryPlanner"]["winningPlan"]["stage"])  # SHARD_MERGE
print("Docs examined:", plan_hashed["executionStats"]["totalDocsExamined"])  # all docs
```

**Key insight**: Hashed sharding gives you even write distribution but costs you range query efficiency. Ranged sharding preserves range query locality but risks hot spots on monotonic keys.

## Exercise 6: Connect via pymongo (Application View)

The application doesn't need to know about shards at all -- it just connects to `mongos`.

Run the cells below (they use the `client` and `db` from the Python Setup cell):

```python
# Insert — mongos decides which shard based on the user_id hash
result = db.events_hashed.insert_one({
    "user_id": "user_9999",
    "event_type": "purchase",
    "timestamp": datetime.datetime.utcnow(),
})
print("Inserted:", result.inserted_id)

# Query — mongos routes to the shard that owns user_9999
doc = db.events_hashed.find_one({"user_id": "user_9999"})
print("Retrieved:", doc["user_id"], doc["event_type"])
```

Verify which shard stored the document using the explain plan:

```python
plan = db.events_hashed.find({"user_id": "user_9999"}).explain("executionStats")
print("Routed to shard:", plan["queryPlanner"]["winningPlan"]["shards"][0]["shardName"])
```

**The application code is identical to single-node MongoDB.** `mongos` handles all routing transparently — no shard addresses, no sharding logic in application code.

## Exercise 7: Tracing Query Routing in Logs

Enable profiling on mongos to see routing decisions (mongosh admin):

```javascript
// In mongosh — setProfilingLevel and system.profile are admin operations
mongosh "mongodb://localhost:27017"
use demo
db.setProfilingLevel(2)   // profile all operations
```

Run queries from Python (the profiler will capture them):

```python
# These queries will be recorded by the profiler
list(db.events_hashed.find({"user_id": "user_0001"}))
list(db.events_hashed.find({"event_type": "purchase"}))
```

View the profile log in mongosh:

```javascript
// In mongosh
db.system.profile.find().sort({ ts: -1 }).limit(2).pretty()
```

Or watch the mongos container logs in real time as you run Python queries:

```bash
# In a separate terminal
docker logs mongos -f --tail=0
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