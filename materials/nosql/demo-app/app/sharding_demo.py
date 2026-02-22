"""
Sharding Demo
=============
Demonstrates application-level interaction with a MongoDB sharded cluster:
  - Connect to mongos (not to shards directly)
  - Inserts routed transparently by the driver + mongos
  - Targeted queries (shard key included) vs scatter-gather (no shard key)
  - Verifying which shard stores which documents

Prerequisites:
  cd demo-app/sharded-cluster && docker compose up -d && bash init-sharding.sh
  pip install -r requirements.txt

Run:
  python sharding_demo.py
"""

import time
from datetime import datetime
from pymongo import MongoClient


# Connect to mongos -- the single entry point for the sharded cluster
# The application does NOT know about individual shards
MONGOS_URI = "mongodb://localhost:27017"


def print_section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


# ─── Demo 1: Transparent Connection ─────────────────────────────────────────

def demo_connection() -> None:
    print_section("1. Connecting Through mongos")
    
    client = MongoClient(MONGOS_URI)
    db = client["demo"]
    
    # The application sees a normal MongoDB connection
    # It has no idea it's talking to a sharded cluster
    server_info = client.server_info()
    print(f"Connected to MongoDB {server_info['version']}")
    
    # But we can ask mongos about the cluster
    result = db.command("isMaster")
    print(f"Server role: {result.get('msg', 'unknown')}")  # "isdbgrid" for mongos
    print(f"Connected to: {result.get('me', 'unknown')}")
    
    # Sharding status
    admin_db = client["admin"]
    sh_status = admin_db.command("listShards")
    print(f"\nShards in cluster ({len(sh_status['shards'])}):")
    for shard in sh_status["shards"]:
        print(f"  {shard['_id']}: {shard['host']}")
    
    client.close()


# ─── Demo 2: Insert Routes to Correct Shard ──────────────────────────────────

def demo_insert_routing() -> None:
    print_section("2. Insert Routing - mongos Decides the Shard")
    
    client = MongoClient(MONGOS_URI)
    db = client["demo"]
    
    # Insert documents with different user_ids
    # mongos will hash the user_id and route each to the appropriate shard
    users = ["user_0001", "user_0250", "user_0500", "user_0750", "user_1000"]
    
    print("Inserting events for different users...")
    print("(mongos routes each insert to the correct shard based on hashed user_id)\n")
    
    for user_id in users:
        doc = {
            "user_id": user_id,
            "event_type": "demo_insert",
            "payload": f"test data for {user_id}",
            "inserted_at": datetime.now()
        }
        result = db.events_hashed.insert_one(doc)
        print(f"  Inserted: user_id={user_id}  _id={result.inserted_id}")
    
    print("\nAll inserts succeeded. The application doesn't know which shard was used.")
    print("mongos determined the destination based on hash(user_id).")
    
    client.close()


# ─── Demo 3: Targeted Query (Shard Key Present) ──────────────────────────────

def demo_targeted_query() -> None:
    print_section("3. Targeted Query - Shard Key in Filter")
    
    client = MongoClient(MONGOS_URI)
    db = client["demo"]
    
    target_user = "user_0001"
    
    print(f"Query: db.events_hashed.find({{user_id: '{target_user}'}})")
    print(f"shard key = user_id (hashed) → mongos can route to exactly one shard\n")
    
    # Run the query
    start = time.perf_counter()
    results = list(db.events_hashed.find({"user_id": target_user}))
    elapsed = (time.perf_counter() - start) * 1000
    
    print(f"Found {len(results)} documents in {elapsed:.1f}ms")
    
    # Get explain plan to see routing
    explain = db.events_hashed.find({"user_id": target_user}).explain("executionStats")
    winning_plan = explain["queryPlanner"]["winningPlan"]
    
    stage = winning_plan.get("stage", "unknown")
    print(f"\nexplain() stage: {stage}")
    
    if stage == "SINGLE_SHARD":
        shard_name = winning_plan["shards"][0]["shardName"]
        print(f"Routed to:       {shard_name}  ← only ONE shard contacted")
    elif "shards" in winning_plan:
        shards = [s["shardName"] for s in winning_plan["shards"]]
        print(f"Contacted shards: {shards}")
    
    exec_stats = explain.get("executionStats", {})
    print(f"nReturned:        {exec_stats.get('nReturned', 'n/a')}")
    print(f"totalDocsExamined:{exec_stats.get('totalDocsExamined', 'n/a')}")
    print(f"executionTimeMs:  {exec_stats.get('executionTimeMillis', 'n/a')}")
    
    client.close()


# ─── Demo 4: Scatter-Gather Query (No Shard Key) ─────────────────────────────

def demo_scatter_gather() -> None:
    print_section("4. Scatter-Gather - No Shard Key in Filter")
    
    client = MongoClient(MONGOS_URI)
    db = client["demo"]
    
    print("Query: db.events_hashed.find({event_type: 'purchase'})")
    print("No shard key in filter → mongos must query ALL shards and merge results\n")
    
    # Run the query
    start = time.perf_counter()
    count = db.events_hashed.count_documents({"event_type": "purchase"})
    elapsed = (time.perf_counter() - start) * 1000
    
    print(f"Found {count} documents in {elapsed:.1f}ms")
    
    # Get explain plan
    explain = db.events_hashed.find({"event_type": "purchase"}).explain("executionStats")
    winning_plan = explain["queryPlanner"]["winningPlan"]
    
    stage = winning_plan.get("stage", "unknown")
    print(f"\nexplain() stage: {stage}")
    
    if "shards" in winning_plan:
        shards = [s["shardName"] for s in winning_plan["shards"]]
        print(f"Contacted shards: {shards}  ← ALL shards queried")
    
    exec_stats = explain.get("executionStats", {})
    print(f"nReturned:        {exec_stats.get('nReturned', 'n/a')}")
    print(f"totalDocsExamined:{exec_stats.get('totalDocsExamined', 'n/a')}")
    print(f"executionTimeMs:  {exec_stats.get('executionTimeMillis', 'n/a')}")
    
    print("\nCompare with the targeted query:")
    print("  Targeted:      contacted 1 shard, examined ~50 docs")
    print("  Scatter-gather: contacted ALL shards, examined ~50,000 docs")
    print("  This is why shard key selection matters for performance!")
    
    client.close()


# ─── Demo 5: Performance Comparison ─────────────────────────────────────────

def demo_performance_comparison() -> None:
    print_section("5. Performance Comparison: Targeted vs Scatter-Gather")
    
    client = MongoClient(MONGOS_URI)
    db = client["demo"]
    
    RUNS = 10
    
    # Targeted queries: different user_ids
    targeted_times = []
    for i in range(RUNS):
        user_id = f"user_{str(i * 100 + 1).zfill(4)}"
        start = time.perf_counter()
        list(db.events_hashed.find({"user_id": user_id}))
        targeted_times.append((time.perf_counter() - start) * 1000)
    
    # Scatter-gather queries: filter by event_type
    scatter_times = []
    event_types = ["page_view", "click", "purchase", "search"]
    for i in range(RUNS):
        event_type = event_types[i % 4]
        start = time.perf_counter()
        list(db.events_hashed.find({"event_type": event_type}).limit(100))
        scatter_times.append((time.perf_counter() - start) * 1000)
    
    avg_targeted = sum(targeted_times) / len(targeted_times)
    avg_scatter = sum(scatter_times) / len(scatter_times)
    
    print(f"Targeted queries  (shard key):    avg {avg_targeted:.1f}ms  (min {min(targeted_times):.1f}ms)")
    print(f"Scatter-gather    (no shard key): avg {avg_scatter:.1f}ms  (min {min(scatter_times):.1f}ms)")
    print(f"\nScatter-gather overhead: {avg_scatter/avg_targeted:.1f}x slower")
    print("(This ratio grows with more shards and more data)")
    
    client.close()


# ─── Demo 6: Cluster Stats from Application ──────────────────────────────────

def demo_cluster_stats() -> None:
    print_section("6. Cluster Visibility from Application Code")
    
    client = MongoClient(MONGOS_URI)
    db = client["demo"]
    
    # Get shard distribution
    result = db.command("collStats", "events_hashed")
    
    print("events_hashed collection stats (via mongos):")
    print(f"  Total documents: {result.get('count', 0):,}")
    print(f"  Total size:      {result.get('size', 0) / 1024 / 1024:.1f}MB")
    print(f"  Avg object size: {result.get('avgObjSize', 0):.0f} bytes")
    
    if "shards" in result:
        print(f"\n  Distribution across shards:")
        for shard_name, stats in result["shards"].items():
            pct = stats["count"] / result["count"] * 100
            print(f"    {shard_name}: {stats['count']:,} docs ({pct:.1f}%)")
    
    client.close()


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("MongoDB Sharded Cluster - Application Patterns Demo")
    print(f"mongos URI: {MONGOS_URI}")
    
    demo_connection()
    demo_insert_routing()
    demo_targeted_query()
    demo_scatter_gather()
    demo_performance_comparison()
    demo_cluster_stats()
    
    print("\nDone!")
    print("\nKey takeaways:")
    print("  1. Application connects to mongos -- shards are invisible")
    print("  2. Inserts are automatically routed to the correct shard")
    print("  3. Queries with the shard key: SINGLE_SHARD (fast)")
    print("  4. Queries without the shard key: SHARD_MERGE (all shards contacted)")
    print("  5. Design your shard key around your most frequent query patterns")
