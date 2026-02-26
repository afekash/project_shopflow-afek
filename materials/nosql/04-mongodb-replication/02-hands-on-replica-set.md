# Hands-On: Replica Set

## Setup

All infrastructure is in `demo-app/replica-set/`. Check out the README.md file for instructions on how to start the replica set.

## Python Setup

All exercises use pymongo. Run this cell once before starting:

```python
from pymongo import MongoClient, ReadPreference
from pymongo.write_concern import WriteConcern
import time, datetime, pprint

RS_URI = "mongodb://mongo1:27017,mongo2:27018,mongo3:27019/?replicaSet=rs0"
client = MongoClient(RS_URI)
db = client["demo"]
```

## Understanding the Replica Set Config

Connect to the primary and examine the replica set:

```python
# View the replica set configuration
config = client.admin.command("replSetGetConfig")["config"]
print(f"Replica set: {config['_id']}")
for m in config["members"]:
    print(f"  _id={m['_id']}  host={m['host']}  priority={m['priority']}")
# mongo1 has priority 2, others have priority 1
# Higher priority = more likely to be elected primary
```

```python
# View the current status of all members
status = client.admin.command("replSetGetStatus")
for m in status["members"]:
    print(f"{m['name']:20s}  state={m['stateStr']:10s}  health={m['health']}")
```

### Reading the status output

The `members` array is the most important part:

```
mongo1:27017         state=PRIMARY     health=1.0
mongo2:27018         state=SECONDARY   health=1.0
mongo3:27019         state=SECONDARY   health=1.0
```

**Key fields to watch**: `stateStr` (PRIMARY/SECONDARY/RECOVERING/DOWN), `optime` (how far along the oplog), `syncSourceHost` (who this member replicates from).

Check replication lag — how far secondaries lag behind the primary:

```python
status = client.admin.command("replSetGetStatus")
primary_ts = next(
    m["optime"]["ts"] for m in status["members"] if m["stateStr"] == "PRIMARY"
)
for m in status["members"]:
    if m["stateStr"] == "SECONDARY":
        lag = primary_ts.as_datetime() - m["optime"]["ts"].as_datetime()
        print(f"{m['name']}: {lag.total_seconds():.1f}s behind primary")
```

## Exercise 1: Observe Replication

**Goal**: Write to the primary and read the same data from a secondary.

**Step 1**: Verify which node is the primary:

```python
status = client.admin.command("isMaster")
print(status["primary"])  # should show "mongo1:27017"
```

**Step 2**: Insert a document on the primary:

```python
result = db.events.insert_one({
    "type": "page_view",
    "user": "alice",
    "url": "/products/laptop",
    "timestamp": datetime.datetime.now(datetime.UTC),
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
batch = [{"i": i, "ts": datetime.datetime.now(datetime.UTC)} for i in range(10_000)]
db.events.insert_many(batch)
print("Inserted 10,000 documents")

# Immediately check how far secondaries lag behind
status = client.admin.command("replSetGetStatus")
primary_ts = next(
    m["optime"]["ts"] for m in status["members"] if m["stateStr"] == "PRIMARY"
)
for m in status["members"]:
    if m["stateStr"] == "SECONDARY":
        lag = primary_ts.as_datetime() - m["optime"]["ts"].as_datetime()
        print(f"{m['name']}: {lag.total_seconds():.1f}s behind primary")
```

**What you observed**: Writes on the primary are asynchronously replicated to secondaries. Under light load, replication is near-instant. Under heavy write load, there may be a brief lag.

## Exercise 2: Simulate Failover

**Goal**: Kill the primary and watch a new primary be elected automatically.

**Step 1**: Start a Python status watch loop in a separate cell, then kill the primary:

```python
# Run this in one cell — it will print status every second
# Stop it with the kernel interrupt (■) after you see the new primary elected
for _ in range(60):
    status = client.admin.command("replSetGetStatus")
    summary = ", ".join(f"{m['name']}: {m['stateStr']}" for m in status["members"])
    print(summary)
    time.sleep(1)
```

**Step 2**: Kill the primary in a terminal:

```bash
docker compose stop mongo1
```

Watch the loop output:
```
mongo1:27017: PRIMARY,  mongo2:27018: SECONDARY, mongo3:27019: SECONDARY
mongo1:27017: UNKNOWN,  mongo2:27018: SECONDARY, mongo3:27019: SECONDARY  ← primary gone
mongo1:27017: UNKNOWN,  mongo2:27018: PRIMARY,   mongo3:27019: SECONDARY  ← new primary!
```

The election typically completes in **10-20 seconds**.

**Step 3**: Verify data survived and write to the new primary:

```python
# pymongo auto-discovers the new primary — no reconnect needed
print("Primary now:", client.primary)

count = db.events.count_documents({})
print(f"All {count} documents survived the failover")

# Write to the new primary
db.events.insert_one({"type": "post_failover_write", "timestamp": datetime.datetime.now(datetime.UTC)})
print("Post-failover write succeeded")
```

**Bring the old primary back** (it will rejoin as a secondary):

```bash
docker compose start mongo1
```

Wait ~15 seconds for mongo1 to sync, then verify it caught up:

```python
time.sleep(15)

# Connect directly to the old primary (now a secondary) to confirm it caught up
old_primary = MongoClient("mongodb://mongo1:27017", directConnection=True)
old_primary_db = old_primary.get_database(
    "demo", read_preference=ReadPreference.SECONDARY_PREFERRED
)
doc = old_primary_db.events.find_one({"type": "post_failover_write"})
print("Post-failover write visible on rejoined node:", doc is not None)
# True — mongo1 caught up via the oplog
```

**What you observed**: MongoDB automatically detected the primary failure, elected a new primary without manual intervention, and maintained data integrity. The old primary rejoined as a secondary and caught up automatically via the oplog.

## Exercise 3: Read Preferences

**Goal**: Demonstrate read routing across replica set members.

```python
def served_by(cursor):
    """Return '(host:port, isPrimary=True/False)' for the node that ran this cursor."""
    addr = cursor.address           # (host, port) of the node PyMongo chose
    host_port = f"{addr[0]}:{addr[1]}"
    is_primary = addr == client.primary   # client.primary is already known from RS topology
    return host_port, is_primary

# Default: reads go to the primary (always fresh data)
db_primary = client.get_database("demo", read_preference=ReadPreference.PRIMARY)
c = db_primary.events.find({}).limit(1); list(c)
node, primary = served_by(c)
print(f"Primary read          — served by: {node}  (isPrimary: {primary})")

# Offload reads to secondaries (slightly stale, but offloads the primary)
db_secondary = client.get_database("demo", read_preference=ReadPreference.SECONDARY)
c = db_secondary.events.find({}).limit(1); list(c)
node, primary = served_by(c)
print(f"Secondary read        — served by: {node}  (isPrimary: {primary})")

# Prefer secondary, fall back to primary if no secondary is available
db_sec_pref = client.get_database("demo", read_preference=ReadPreference.SECONDARY_PREFERRED)
c = db_sec_pref.events.find({}).limit(1); list(c)
node, primary = served_by(c)
print(f"Secondary-preferred   — served by: {node}  (isPrimary: {primary})")
```

**What to observe**: `isPrimary: False` for the secondary reads — and a different host than the primary read. Secondary reads route to a different host, demonstrating actual load distribution.

> **Why not just call `db.command("isMaster")`?** `isMaster` is a server-selection/topology command — PyMongo always routes it to the primary regardless of read preference. `cursor.address` is the right tool: it records which node PyMongo actually dispatched the find to. Comparing it against `client.primary` (which the driver already tracks) tells us whether it's the primary or a secondary — no extra connection needed.

## Exercise 4: Write Concerns

**Goal**: Measure the latency difference between `w=1` and `w="majority"`.

```python
N = 100

# w=1 — only the primary acknowledges before returning
coll_w1 = db.get_collection("wc_test", write_concern=WriteConcern(w=1))
t0 = time.time()
for i in range(N):
    coll_w1.insert_one({"i": i, "wc": 1})
t1 = (time.time() - t0) * 1000
print(f"w=1        — {N} inserts: {t1:.0f} ms  (avg {t1/N:.1f} ms/op)")

# w="majority" — waits for 2 of 3 nodes to confirm
coll_maj = db.get_collection("wc_test", write_concern=WriteConcern(w="majority"))
t2 = time.time()
for i in range(N):
    coll_maj.insert_one({"i": i, "wc": "majority"})
t3 = (time.time() - t2) * 1000
print(f"w=majority — {N} inserts: {t3:.0f} ms  (avg {t3/N:.1f} ms/op)")

print(f"Overhead per op: +{(t3-t1)/N:.1f} ms")
```

**Expected results**: `w="majority"` will be slower per operation. The trade-off: with `w=1`, a write acknowledged by only the primary could be lost if the primary crashes before replicating. With `w="majority"`, the write is on at least 2 of 3 nodes — it will survive a single-node failure.

## Exercise 5: Inspect the Oplog

**Goal**: See exactly what the oplog looks like during writes — including how MongoDB rewrites update operators into idempotent absolute-value entries.

**Step 1**: Perform a controlled sequence of writes so the oplog entries are predictable:

```python
import datetime

db.oplog_demo.drop()   # start clean

# INSERT — op: 'i'
db.oplog_demo.insert_one({"item": "widget", "qty": 10})

# UPDATE with $inc — MongoDB rewrites this in the oplog
db.oplog_demo.update_one({"item": "widget"}, {"$inc": {"qty": 5}})

# DELETE — op: 'd'
db.oplog_demo.delete_one({"item": "widget"})
```

**Step 2**: Read the oplog entries that correspond to those three writes:

```python
oplog = client.local["oplog.rs"]

# Grab the 3 most recent entries on demo.oplog_demo (newest first, then reverse for readability)
recent = list(
    oplog.find({"ns": "demo.oplog_demo"})
         .sort("$natural", -1)
         .limit(3)
)
recent.reverse()   # show in write order: insert → update → delete

for entry in recent:
    pprint.pprint({k: entry[k] for k in ("op", "ns", "o", "o2") if k in entry})
    print()
```

**Entry 1 — Insert (`op: 'i'`)**

`o` holds the full document that was inserted. `o2` holds the document's `_id`. Both are recorded so a secondary can insert the exact document and verify identity without re-reading anything.

**Entry 2 — Update (`op: 'u'`)**

`o2` is the filter — the `_id` that identifies which document to update. `o` is the diff to apply: `{$v: 2, diff: {u: {qty: 15}}}`. Notice `qty` is `15`, not `{$inc: {qty: 5}}`. MongoDB rewrites the operator into its **absolute computed result** before writing to the oplog. This makes the entry **idempotent** — a secondary can replay it any number of times and always arrive at the same state. If the oplog stored `$inc: 5` instead, each replay would add another 5.

**Entry 3 — Delete (`op: 'd'`)**

`o` contains only the `_id` of the deleted document. That is all a secondary needs to replay the deletion — no other fields are required.

Check the oplog window — how far back in time the oplog covers:

```python
oplog = client.local["oplog.rs"]
first = oplog.find_one(sort=[("$natural", 1)])
last  = oplog.find_one(sort=[("$natural", -1)])
window = last["ts"].as_datetime() - first["ts"].as_datetime()
print(f"Oplog window: {window}")
```

If a secondary is down longer than the oplog window, it cannot re-sync automatically — it must be re-initialized from scratch. This is why oplog size matters for operational resilience.

## Cleanup

```bash
cd demo-app/replica-set
docker compose down -v    # -v removes the data volumes
```

## Key Takeaways

- Replica sets provide automatic failover — no manual intervention needed
- Election completes in ~10-30 seconds; applications should handle brief errors during this window
- The oplog is the replication mechanism — understanding it helps debug lag and resync scenarios
- Write concern (`w:majority`) adds latency but guarantees durability across node failures
- Read preference enables secondary reads for analytics — but reads may be slightly stale
- The old primary automatically rejoins as a secondary and catches up via the oplog

---

**Next:** [Sharding Architecture →](../05-mongodb-sharding/01-sharding-architecture.md)

---

[← Back: Replica Set Architecture](01-replica-set-architecture.md) | [Course Home](../README.md)
