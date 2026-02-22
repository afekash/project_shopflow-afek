# Hands-On: Replica Set

## Setup

All infrastructure is in `demo-app/replica-set/`. Start the cluster:

```bash
cd materials/nosql/demo-app/replica-set
docker compose up -d
bash init-replica.sh
```

You should see all three containers running and the init script confirming the replica set is formed with test data inserted.

```bash
docker compose ps
# NAME      STATUS    PORTS
# mongo1    running   0.0.0.0:27017->27017/tcp
# mongo2    running   0.0.0.0:27018->27017/tcp
# mongo3    running   0.0.0.0:27019->27017/tcp
```

## Understanding the Replica Set Config

Connect to the primary and examine the replica set:

```javascript
// Connect to primary
mongosh "mongodb://localhost:27018"

// View the replica set configuration
rs.conf()
// Shows: _id: "rs0", members array with hosts and priorities
// mongo1 has priority: 2, others have priority: 1
// Higher priority = more likely to be elected primary

// View the current status of all members
rs.status()
```

### Reading `rs.status()` Output

The `members` array is the most important part:

```javascript
{
  members: [
    {
      _id: 0,
      name: "mongo1:27017",
      health: 1,                    // 1 = healthy, 0 = unreachable
      state: 1,                     // 1 = PRIMARY, 2 = SECONDARY, 6 = UNKNOWN
      stateStr: "PRIMARY",
      uptime: 120,
      optime: { ts: Timestamp(1708440000, 5), t: NumberLong(1) },
      optimeDate: ISODate("2024-02-20T..."),
      lastHeartbeatMessage: "",
      syncSourceHost: ""            // primary has no sync source
    },
    {
      _id: 1,
      name: "mongo2:27017",
      health: 1,
      state: 2,
      stateStr: "SECONDARY",
      uptime: 115,
      optime: { ts: Timestamp(1708440000, 5), t: NumberLong(1) },
      optimeDurable: { ts: Timestamp(1708440000, 5), t: NumberLong(1) },
      lastHeartbeat: ISODate("2024-02-20T..."),
      syncSourceHost: "mongo1:27017"  // replicating from primary
    },
    // ... mongo3 similar to mongo2
  ]
}
```

**Key fields to watch**: `stateStr` (PRIMARY/SECONDARY/RECOVERING/DOWN), `optime` (how far along the oplog), `syncSourceHost` (who this member replicates from).

Check replication lag:
```javascript
// See how far secondaries lag behind the primary
rs.printSecondaryReplicationInfo()
// Output:
// source: mongo2:27017
//   syncedTo: Thu Feb 20 2024 10:00:00
//   0 secs (0 hrs) behind the primary
```

## Python Setup

All data operations in these exercises use pymongo. Run this cell once before starting:

```python
from pymongo import MongoClient, ReadPreference
from pymongo.write_concern import WriteConcern
import time, datetime

RS_URI = "mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=rs0"
client = MongoClient(RS_URI)
db = client["demo"]
```

## Exercise 1: Observe Replication

**Goal**: Write to the primary and read the same data from a secondary.

**Step 1**: Verify which node is the primary (mongosh admin check):

```javascript
// In mongosh — rs.* commands are admin-only
mongosh "mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=rs0"
rs.isMaster().primary   // should show "mongo1:27017"
```

**Step 2**: Insert a document on the primary using Python:

```python
result = db.events.insert_one({
    "type": "page_view",
    "user": "alice",
    "url": "/products/laptop",
    "timestamp": datetime.datetime.utcnow(),
})
print("Inserted:", result.inserted_id)
```

**Step 3**: Read the same document from a secondary:

```python
# By default the driver reads from the primary. Force a secondary read:
secondary_db = client.get_database("demo", read_preference=ReadPreference.SECONDARY)

# Allow a moment for replication
time.sleep(0.5)

docs = list(secondary_db.events.find({"type": "page_view"}))
print(f"Found on secondary: {len(docs)} document(s)")
print(docs[0])
# The document written on the primary is already here — it replicated!
```

**Step 4**: Observe replication lag under heavy write load:

```python
# Rapid bulk insert on the primary
batch = [{"i": i, "ts": datetime.datetime.utcnow()} for i in range(10_000)]
db.events.insert_many(batch)
print("Inserted 10,000 documents")
```

Then check lag in mongosh (admin command):

```javascript
// In mongosh — check how far secondaries lag behind the primary
rs.printSecondaryReplicationInfo()
// source: mongo2:27017
//   0 secs (0 hrs) behind the primary
```

**What you observed**: Writes on the primary are asynchronously replicated to secondaries. Under light load, replication is near-instant. Under heavy write load, there may be a brief lag.

## Exercise 2: Simulate Failover

**Goal**: Kill the primary and watch a new primary be elected automatically.

**Step 1**: Verify the current primary and start a status watch loop (mongosh admin):

```javascript
// In mongosh
mongosh "mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=rs0"
rs.isMaster().primary   // "mongo1:27017"

// Keep this running to watch the election in real time
while (true) {
  let status = rs.status().members.map(m => `${m.name}: ${m.stateStr}`)
  print(status.join(", "))
  sleep(1000)
}
```

**Step 2**: Kill the primary in a new terminal:

```bash
docker compose stop mongo1
```

Watch the monitor loop output:
```
mongo1:27017: PRIMARY,  mongo2:27017: SECONDARY, mongo3:27017: SECONDARY
mongo1:27017: UNKNOWN,  mongo2:27017: SECONDARY, mongo3:27017: SECONDARY  ← primary gone
mongo1:27017: UNKNOWN,  mongo2:27017: PRIMARY,   mongo3:27017: SECONDARY  ← new primary!
```

The election typically completes in **10-20 seconds**.

**Step 3**: Verify data survived and write to the new primary using Python:

```python
# The pymongo client auto-discovers the new primary — no reconnect needed
print("Primary now:", client.primary)

count = db.events.count_documents({})
print(f"All {count} documents survived the failover")

# Write to the new primary
db.events.insert_one({"type": "post_failover_write", "timestamp": datetime.datetime.utcnow()})
print("Post-failover write succeeded")
```

Confirm in mongosh which node is now primary (admin check):

```javascript
// In mongosh — connect to the new primary
mongosh "mongodb://localhost:27018"
rs.isMaster().primary   // now "mongo2:27017"
```

**Bring the old primary back** (it will rejoin as a secondary):

```bash
docker compose start mongo1
```

Wait ~15 seconds for mongo1 to sync, then verify with Python:

```python
time.sleep(15)

# Connect directly to the old primary (now a secondary) to confirm it caught up
old_primary = MongoClient("mongodb://localhost:27017", directConnection=True)
old_primary_db = old_primary.get_database(
    "demo", read_preference=ReadPreference.SECONDARY_PREFERRED
)
doc = old_primary_db.events.find_one({"type": "post_failover_write"})
print("Post-failover write visible on rejoined node:", doc is not None)
# True — mongo1 caught up via the oplog
```

**What you observed**: MongoDB automatically detected the primary failure, elected a new primary without manual intervention, and maintained data integrity. The old primary rejoined as a secondary and caught up automatically via the oplog.

## Exercise 3: Read Preferences with pymongo

**Goal**: Use Python to connect to the replica set and demonstrate read routing.

```python
# Uses the RS_URI client from the Python Setup cell above

# Default: reads go to the primary (always fresh data)
db_primary = client.get_database("demo", read_preference=ReadPreference.PRIMARY)
doc = db_primary.events.find_one({})
info = db_primary.command("isMaster")
print(f"Primary read — served by: {info.get('me')}  (isPrimary: {info.get('ismaster')})")

# Offload reads to secondaries (slightly stale, but offloads the primary)
db_secondary = client.get_database("demo", read_preference=ReadPreference.SECONDARY)
doc = db_secondary.events.find_one({})
info = db_secondary.command("isMaster")
print(f"Secondary read — served by: {info.get('me')}  (isPrimary: {info.get('ismaster')})")

# Prefer secondary, fall back to primary if no secondary is available
db_sec_pref = client.get_database("demo", read_preference=ReadPreference.SECONDARY_PREFERRED)
doc = db_sec_pref.events.find_one({})
print(f"Secondary-preferred — returned: {doc['type'] if doc else None}")
```

**What to observe**: the `me` field tells you which replica set member handled each read. Secondary reads route to a different host than the primary, demonstrating actual load distribution.

## Exercise 4: Write Concerns with pymongo

**Goal**: Measure the latency difference between `w=1` and `w="majority"`.

```python
# Uses the RS_URI client and db from the Python Setup cell above
N = 100

# w=1 — only the primary acknowledges before returning
coll_w1 = db.get_collection("wc_test", write_concern=WriteConcern(w=1))
t0 = time.time()
for i in range(N):
    coll_w1.insert_one({"i": i, "wc": 1})
t1 = (time.time() - t0) * 1000
print(f"w=1       — {N} inserts: {t1:.0f} ms  (avg {t1/N:.1f} ms/op)")

# w="majority" — waits for 2 of 3 nodes to confirm
coll_maj = db.get_collection("wc_test", write_concern=WriteConcern(w="majority"))
t2 = time.time()
for i in range(N):
    coll_maj.insert_one({"i": i, "wc": "majority"})
t3 = (time.time() - t2) * 1000
print(f"w=majority — {N} inserts: {t3:.0f} ms  (avg {t3/N:.1f} ms/op)")

print(f"Overhead per op: +{(t3-t1)/N:.1f} ms")
```

**Expected results**: `w="majority"` will be 5-20 ms slower per operation. The trade-off: with `w=1`, a write acknowledged by only the primary could be lost if the primary crashes before replicating. With `w="majority"`, the write is on at least 2 of 3 nodes -- it will survive a single-node failure.

## Exercise 5: Inspect the Oplog

**Goal**: See exactly what the oplog looks like during writes.

```javascript
mongosh "mongodb://localhost:27017"

// Switch to the local database where the oplog lives
use local
db.oplog.rs.find().sort({ $natural: -1 }).limit(5).pretty()
```

Output looks like:
```javascript
{
  lsid: { ... },
  ts: Timestamp({ t: 1708440125, i: 1 }),
  t: Long("1"),
  op: "i",          // operation: i=insert, u=update, d=delete, c=command
  ns: "demo.events",
  o: {              // the document as stored (for inserts)
    _id: ObjectId("..."),
    type: "page_view",
    user: "alice"
  }
}
```

Notice that `$inc` and `$push` operations are **rewritten as absolute values** in the oplog:
```javascript
// Your application code:
db.counters.updateOne({ _id: "views" }, { $inc: { count: 1 } })

// What appears in the oplog (idempotent form):
{
  op: "u",
  ns: "demo.counters",
  o: { $v: 2, diff: { u: { count: 42 } } },  // absolute value, not relative increment
  o2: { _id: "views" }
}
```

Check the oplog window -- how far back in time the oplog covers:
```javascript
rs.printReplicationInfo()
// configured oplog size:   1024 MB
// log length start to end: 4 hrs 12 min (0.18 days)
// oplog first event time:  Thu Feb 20 2024 10:00:00
// oplog last event time:   Thu Feb 20 2024 14:12:00
// now:                     Thu Feb 20 2024 14:12:15
```

If a secondary is down longer than the oplog window, it cannot re-sync automatically -- it must be re-initialized from scratch. This is why oplog size matters for operational resilience.

## Cleanup

```bash
cd demo-app/replica-set
docker compose down -v    # -v removes the data volumes
```

## Key Takeaways

- Replica sets provide automatic failover -- no manual intervention needed
- Election completes in ~10-30 seconds; applications should handle brief errors during this window
- The oplog is the replication mechanism -- understanding it helps debug lag and resync scenarios
- Write concern (`w:majority`) adds latency but guarantees durability across node failures
- Read preference enables secondary reads for analytics -- but reads may be slightly stale
- The old primary automatically rejoins as a secondary and catches up via the oplog

---

**Next:** [Sharding Architecture →](../05-mongodb-sharding/01-sharding-architecture.md)

---

[← Back: Replica Set Architecture](01-replica-set-architecture.md) | [Course Home](../README.md)