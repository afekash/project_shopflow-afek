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

## Exercise 1: Observe Replication

**Goal**: Write to the primary and read the same data from a secondary.

```javascript
// Step 1: Connect to primary, verify which node it is
mongosh "mongodb://localhost:27017"
rs.isMaster().primary   // should show "mongo1:27017"

// Step 2: Insert a document on the primary
use demo
db.events.insertOne({
  type: "page_view",
  user: "alice",
  url: "/products/laptop",
  timestamp: new Date()
})

// Step 3: Open another terminal and connect to a secondary
// (in a new terminal)
mongosh "mongodb://localhost:27018"

// By default, secondaries reject reads to prevent accidental stale reads
db.events.find()
// MongoServerError: not primary and secondaryOk=false

// Enable secondary reads (for this session)
db.getMongo().setReadPref("secondary")
// OR in newer mongosh:
// use the readPreference option

// Now read from the secondary
db.events.find()
// You should see the document written on the primary -- it has replicated!

// Step 4: Observe replication lag
// Insert many documents rapidly on the primary
// (switch back to primary terminal)
use demo
for (let i = 0; i < 10000; i++) {
  db.events.insertOne({ i: i, ts: new Date() })
}

// On the secondary, watch rs.status() to see optime catching up
rs.printSecondaryReplicationInfo()
```

**What you observed**: Writes on the primary are asynchronously replicated to secondaries. Under light load, replication is near-instant. Under heavy write load, there may be a brief lag.

## Exercise 2: Simulate Failover

**Goal**: Kill the primary and watch a new primary be elected automatically.

```javascript
// Step 1: Verify the current primary
mongosh "mongodb://localhost:27017"
rs.isMaster().primary   // "mongo1:27017"

// Step 2: Open a watch loop on the primary to monitor status
// (keep this terminal open)
while (true) {
  let status = rs.status().members.map(m => `${m.name}: ${m.stateStr}`)
  print(status.join(", "))
  sleep(1000)
}
// Output: mongo1:27017: PRIMARY, mongo2:27017: SECONDARY, mongo3:27017: SECONDARY
```

Now kill the primary:

```bash
# In a NEW terminal -- stop the primary container
docker compose stop mongo1
```

Watch the monitor loop in the first terminal:
```
mongo1:27017: PRIMARY, mongo2:27017: SECONDARY, mongo3:27017: SECONDARY
mongo1:27017: UNKNOWN, mongo2:27017: SECONDARY, mongo3:27017: SECONDARY  ← primary gone
mongo1:27017: UNKNOWN, mongo2:27017: SECONDARY, mongo3:27017: SECONDARY  ← election timer
mongo1:27017: UNKNOWN, mongo2:27017: PRIMARY,   mongo3:27017: SECONDARY  ← new primary!
```

The election typically completes in **10-20 seconds**.

Connect to the new primary and verify the data is intact:

```javascript
// Connect to the new primary (mongo2)
mongosh "mongodb://localhost:27018"
rs.isMaster().primary   // now "mongo2:27017"

// Verify data survived the failover
use demo
db.events.countDocuments()
// Shows all documents including those written before the failover

// Write new data to the new primary
db.events.insertOne({ type: "post_failover_write", timestamp: new Date() })
```

**Bring the old primary back** (it will rejoin as a secondary):

```bash
docker compose start mongo1
```

```javascript
// Watch mongo1 rejoin in the monitor loop
// mongo1:27017: STARTUP → RECOVERING → SECONDARY

// After it's back, check its data includes the post-failover write
mongosh "mongodb://localhost:27017"
db.getMongo().setReadPref("secondary")
use demo
db.events.findOne({ type: "post_failover_write" })
// Present! mongo1 caught up via the oplog.
```

**What you observed**: MongoDB automatically detected the primary failure, elected a new primary without manual intervention, and maintained data integrity. The old primary rejoined as a secondary and caught up automatically via the oplog.

## Exercise 3: Read Preferences with pymongo

**Goal**: Use Python to connect to the replica set and demonstrate read routing.

Run from `demo-app/app/`:

```bash
cd demo-app/app
pip install -r requirements.txt
python replica_demo.py
```

The script will show which node serves each read based on read preference. Look at `demo-app/app/replica_demo.py` for the full source.

Key patterns demonstrated:
```python
from pymongo import MongoClient, ReadPreference

# Replica set connection string -- driver discovers topology automatically
client = MongoClient(
    "mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=rs0"
)

# Default: reads from primary
db_primary = client.get_database("demo")
result = db_primary.products.find_one({})

# Read from secondaries (for analytics/reporting)
db_secondary = client.get_database(
    "demo",
    read_preference=ReadPreference.SECONDARY
)
result = db_secondary.products.find_one({})

# Check which server handled the request
result = db_secondary.command("isMaster")
print(f"Connected to: {result.get('me')}")
print(f"Is primary: {result.get('ismaster')}")
```

## Exercise 4: Write Concerns with pymongo

**Goal**: Measure the latency difference between `w:1` and `w:majority`.

```python
import time
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=rs0")
db = client["demo"]

N = 100

# w:1 -- only primary acknowledges
start = time.time()
for i in range(N):
    db.get_collection("wc_test", write_concern={"w": 1}).insert_one({"i": i, "wc": 1})
t1 = (time.time() - start) * 1000
print(f"w:1 - {N} inserts: {t1:.0f}ms (avg {t1/N:.1f}ms per insert)")

# w:majority -- majority of nodes must acknowledge
start = time.time()
for i in range(N):
    db.get_collection("wc_test", write_concern={"w": "majority"}).insert_one({"i": i, "wc": "majority"})
t2 = (time.time() - start) * 1000
print(f"w:majority - {N} inserts: {t2:.0f}ms (avg {t2/N:.1f}ms per insert)")

print(f"Overhead of majority: +{t2-t1:.0f}ms total (+{(t2-t1)/N:.1f}ms/op)")
```

**Expected results**: `w:majority` will be 5-20ms slower per operation. The trade-off: with `w:1`, a write acknowledged by only the primary could be lost if the primary crashes before replicating. With `w:majority`, the write is on at least 2 of 3 nodes -- it will survive a single-node failure.

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