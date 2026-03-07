---
kernelspec:
  name: python3
  language: python
  display_name: Python 3
---

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

Connect to the cluster via `mongos` — this is the single entry point for all operations. Run this setup cell once before starting the exercises:

```{code-cell} python
from pymongo import MongoClient
import datetime

# Connect through mongos — shards are completely transparent
client = MongoClient("mongodb://localhost:27017")
db = client["demo"]

def explain(collection_name, filter_doc):
    """Run explain with executionStats verbosity."""
    return db.command({
        "explain": {"find": collection_name, "filter": filter_doc},
        "verbosity": "executionStats"
    })
```

## Exercise 1: Explore the Cluster State

Use Python to inspect the state of the sharded cluster — which shards exist, which collections are sharded, and how chunks are distributed.

```{code-cell} python
# List all registered shards
shards = client.admin.command("listShards")["shards"]
print("=== Shards ===")
for s in shards:
    print(f"  {s['_id']}: {s['host']}")

# List databases and their primary shards
print("\n=== Databases ===")
for db_doc in client["config"].databases.find():
    print(f"  {db_doc['_id']}: primary={db_doc['primary']}")

# Chunk distribution per collection per shard
print("\n=== Collections ===")
config = client["config"]
for coll in config.collections.find({"dropped": {"$ne": True}}):
    ns = coll["_id"]
    counts = {}
    for chunk in config.chunks.find({"uuid": coll.get("uuid")}):
        counts[chunk["shard"]] = counts.get(chunk["shard"], 0) + 1
    print(f"  {ns} — shard key: {coll['key']}")
    for shard, n in counts.items():
        print(f"    {shard}: {n} chunk(s)")
```

Expected output:
```
=== Shards ===
  shard1rs: shard1rs/shard1a:27017,shard1b:27017,shard1c:27017
  shard2rs: shard2rs/shard2a:27017,shard2b:27017,shard2c:27017

=== Databases ===
  demo: primary=shard1rs

=== Collections ===
  demo.events_hashed — shard key: {'user_id': 'hashed'}
    shard1rs: 2 chunk(s)
    shard2rs: 2 chunk(s)
  demo.events_ranged — shard key: {'user_id': 1}
    shard1rs: 1 chunk(s)
    shard2rs: 1 chunk(s)
```

Now check document distribution across shards:

```{code-cell} python
stats = db.command("collStats", "events_hashed")
total_docs = stats["count"]
print(f"Total: {stats['size'] / 1024**2:.2f} MiB  |  {total_docs} docs")
for shard, s in stats.get("shards", {}).items():
    pct = s["count"] / total_docs * 100
    print(f"  {shard}: {s['count']} docs ({pct:.1f}%)")
```

Output:
```
Total: 7.25 MiB  |  50000 docs
  shard1rs: 24200 docs (48.4%)
  shard2rs: 25800 docs (51.6%)
```

**The hashed collection is split almost exactly 50/50 between shards** — this is the hashed sharding strategy working correctly.

## Exercise 2: Shard Key in Filter → Targeted Query

A query that includes the shard key lets `mongos` route to exactly the right shard.

```{code-cell} python
# Query with shard key: mongos knows which shard owns user_0001
plan = explain("events_hashed", {"user_id": "user_0001"})

winning = plan["queryPlanner"]["winningPlan"]
stats   = plan["executionStats"]

print("Stage:         ", winning["stage"])                  # SINGLE_SHARD
print("Shard routed:  ", winning["shards"][0]["shardName"]) # shard1rs or shard2rs
print("Docs examined: ", stats["totalDocsExamined"])        # 50
print("Docs returned: ", stats["nReturned"])                # 50
print("Time (ms):     ", stats["executionTimeMillis"])      # ~1 ms
```

Expected output:
```
Stage:          SINGLE_SHARD        ← Only ONE shard was contacted
Shard routed:   shard1rs
Docs examined:  50
Docs returned:  50
Time (ms):      1                   ← Fast: only 1 shard queried
```

**`SINGLE_SHARD`**: `mongos` used the hashed shard key to determine which shard owns `user_0001` and routed exclusively there. The other shard was never contacted.

Try different users and observe they may route to different shards:

```{code-cell} python
for uid in ["user_0001", "user_0500", "user_0999"]:
    plan = explain("events_hashed", {"user_id": uid})
    shard = plan["queryPlanner"]["winningPlan"]["shards"][0]["shardName"]
    print(f"{uid}  →  {shard}")
```

## Exercise 3: No Shard Key → Scatter-Gather

Now query without the shard key — `mongos` has no choice but to ask every shard.

```{code-cell} python
# Query WITHOUT shard key: mongos must contact all shards
plan = explain("events_hashed", {"event_type": "purchase"})

winning = plan["queryPlanner"]["winningPlan"]
stats   = plan["executionStats"]

print("Stage:          ", winning["stage"])       # SHARD_MERGE
shards_hit = [s["shardName"] for s in winning["shards"]]
print("Shards queried: ", shards_hit)             # ['shard1rs', 'shard2rs']
print("Docs examined:  ", stats["totalDocsExamined"])  # 50,000
print("Docs returned:  ", stats["nReturned"])          # ~12,500
print("Time (ms):      ", stats["executionTimeMillis"]) # ~23 ms
```

Expected output:
```
Stage:           SHARD_MERGE          ← Multiple shards contacted, results merged
Shards queried:  ['shard1rs', 'shard2rs']
Docs examined:   50000                ← ALL 50K documents across both shards
Docs returned:   12500
Time (ms):       23                   ← Slower: both shards scanned, results merged
```

**`SHARD_MERGE`**: `mongos` had to ask both shards and merge the results. The query touched 50,000 documents to return ~12,500 — a full scatter-gather.

**Performance comparison**:

| Query                        | Stage        | Shards Contacted | Docs Examined | Time  |
| ---------------------------- | ------------ | ---------------- | ------------- | ----- |
| `{ user_id: "user_0001" }`   | SINGLE_SHARD | 1                | 50            | ~1ms  |
| `{ event_type: "purchase" }` | SHARD_MERGE  | 2                | 50,000        | ~23ms |

This is why shard key selection matters: your most frequent queries should include the shard key.

## Exercise 4: Adding an Index on a Sharded Collection

Even with sharding, you still need indexes for efficient queries within each shard. Create an index on `event_type`:

```{code-cell} python
# create_index() on a sharded collection propagates to ALL shards automatically
db.events_hashed.create_index([("event_type", 1)])
print("Index created on all shards")

# Run the scatter-gather query again — same query, now with an index
plan2 = explain("events_hashed", {"event_type": "purchase"})

stats2 = plan2["executionStats"]
print("Docs examined:  ", stats2["totalDocsExamined"])  # ~12,500 — down from 50,000!
print("Docs returned:  ", stats2["nReturned"])
print("Time (ms):      ", stats2["executionTimeMillis"]) # ~7 ms
```

Expected output:
```
Docs examined:   12500   ← down from 50,000!
Docs returned:   12500
Time (ms):       7       ← faster: index used on each shard
```

It's still `SHARD_MERGE` (both shards contacted) but now each shard uses its local index — `totalDocsExamined` dropped from 50,000 to 12,500. Scatter-gather + good indexes is acceptable; scatter-gather + no index is not.

## Exercise 5: Hashed vs Ranged Distribution

Compare how hashed and ranged sharding distribute data differently:

```{code-cell} python
for coll_name in ("events_hashed", "events_ranged"):
    stats = db.command("collStats", coll_name)
    total = stats["count"]
    print(f"\n=== {coll_name} ===")
    for shard, s in stats.get("shards", {}).items():
        pct = s["count"] / total * 100
        print(f"  {shard}: {s['count']} docs ({pct:.1f}%)")
# events_hashed: expect ~50% on each shard (hashed key distributes evenly)
# events_ranged: may be uneven — the split point between alphabetical ranges determines distribution
```

Now observe range query routing behavior:

```{code-cell} python
# Range query on ranged collection — may be targeted to one shard
plan_ranged = explain("events_ranged", {"user_id": {"$gte": "user_0001", "$lte": "user_0100"}})
print("=== Ranged collection, range query ===")
print("Stage:", plan_ranged["queryPlanner"]["winningPlan"]["stage"])
print("Docs examined:", plan_ranged["executionStats"]["totalDocsExamined"])

# Range query on hashed collection — always SHARD_MERGE: hashing destroys ordering
plan_hashed = explain("events_hashed", {"user_id": {"$gte": "user_0001", "$lte": "user_0100"}})
print("\n=== Hashed collection, range query ===")
print("Stage:", plan_hashed["queryPlanner"]["winningPlan"]["stage"])  # SHARD_MERGE
print("Docs examined:", plan_hashed["executionStats"]["totalDocsExamined"])
```

**Key insight**: Hashed sharding gives you even write distribution but costs you range query efficiency. Ranged sharding preserves range query locality but risks hot spots on monotonic keys.

## Exercise 6: Connect via pymongo (Application View)

The application doesn't need to know about shards at all — it just connects to `mongos`.

```{code-cell} python
# Insert — mongos decides which shard based on the user_id hash
result = db.events_hashed.insert_one({
    "user_id": "user_9999",
    "event_type": "purchase",
    "timestamp": datetime.datetime.now(datetime.timezone.utc),
})
print("Inserted:", result.inserted_id)

# Query — mongos routes to the shard that owns user_9999
doc = db.events_hashed.find_one({"user_id": "user_9999"})
print("Retrieved:", doc["user_id"], doc["event_type"])

# Verify routing
plan = explain("events_hashed", {"user_id": "user_9999"})
print("Routed to shard:", plan["queryPlanner"]["winningPlan"]["shards"][0]["shardName"])
```

**The application code is identical to single-node MongoDB.** `mongos` handles all routing transparently — no shard addresses, no sharding logic in application code.

## Understanding the Chunk Map

After exercises, the balancer may have run and created more chunks. Re-check the distribution:

```{code-cell} python
config = client["config"]
for coll in config.collections.find({"dropped": {"$ne": True}}):
    counts = {}
    for chunk in config.chunks.find({"uuid": coll.get("uuid")}):
        counts[chunk["shard"]] = counts.get(chunk["shard"], 0) + 1
    print(f"{coll['_id']}: {counts}")

# Check if the balancer is actively moving chunks right now
status = client.admin.command("balancerStatus")
print("Balancer running:", status.get("inBalancerRound", False))
```

With 50K documents at ~145 bytes average:
- Total data: ~7MB per collection
- Default chunk size: 128MB
- Expected: 1–2 chunks per shard initially (data too small to trigger splits)

## Cleanup

```bash
cd demo-app/sharded-cluster
docker compose down -v    # removes all containers and data volumes
```

## Key Takeaways

- Applications connect to `mongos` only — shards are transparent to the application
- `listShards`, `collStats`, and the `config` database are your primary observability tools
- **Targeted queries** (`SINGLE_SHARD`) use the shard key to route to exactly the right shard — fast
- **Scatter-gather** (`SHARD_MERGE`) queries without the shard key hit all shards — use indexes to mitigate
- Adding an index on a sharded collection creates the index on all shards automatically
- **Hashed sharding**: even write distribution, range queries always scatter-gather
- **Ranged sharding**: range queries can be targeted, monotonic keys risk hot spots
- The balancer continuously moves chunks to maintain even distribution — it's invisible to applications

---

**Next:** [Theory Exercises →](../06-exercises/01-nosql-theory-exercises.md)

---

[← Back: Sharding Architecture](01-sharding-architecture.md) | [Course Home](../README.md)
