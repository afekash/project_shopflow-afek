"""
Replica Set Demo
================
Demonstrates application-level patterns when connecting to a MongoDB replica set:
  - Replica set connection string and topology discovery
  - Read preferences: routing reads to secondaries
  - Write concerns: durability trade-offs
  - Failover: how the driver handles primary going down

Prerequisites:
  cd demo-app/replica-set && docker compose up -d && bash init-replica.sh
  pip install -r requirements.txt

Run:
  python replica_demo.py
"""

import time
from pymongo import MongoClient, ReadPreference
from pymongo.errors import ConnectionFailure, NotPrimaryError


REPLICA_SET_URI = (
    "mongodb://localhost:27017,localhost:27018,localhost:27019"
    "/?replicaSet=rs0&serverSelectionTimeoutMS=5000"
)


def print_section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def get_server_info(collection) -> str:
    """Return the host that served the last operation."""
    result = collection.database.command("isMaster")
    return result.get("me", "unknown")


# ─── Demo 1: Basic Connection ────────────────────────────────────────────────

def demo_basic_connection() -> None:
    print_section("1. Connecting to Replica Set")
    
    client = MongoClient(REPLICA_SET_URI)
    db = client["demo"]
    
    # The driver automatically discovers the replica set topology
    server_info = client.server_info()
    print(f"Connected to MongoDB {server_info['version']}")
    
    # Check which node is the current primary
    result = db.command("isMaster")
    print(f"Primary:    {result.get('primary', 'unknown')}")
    print(f"Hosts:      {result.get('hosts', [])}")
    print(f"Me:         {result.get('me', 'unknown')}")
    print(f"Is primary: {result.get('ismaster', False)}")
    
    client.close()


# ─── Demo 2: Read Preferences ───────────────────────────────────────────────

def demo_read_preferences() -> None:
    print_section("2. Read Preferences - Where Do Reads Go?")
    
    client = MongoClient(REPLICA_SET_URI)
    
    # Primary read preference (default) -- always reads from primary
    db_primary = client.get_database("demo", read_preference=ReadPreference.PRIMARY)
    result = db_primary.command("isMaster")
    print(f"READ_PREF=primary        → served by: {result['me']} (is primary: {result['ismaster']})")
    
    # Secondary read preference -- reads from a secondary, never primary
    db_secondary = client.get_database("demo", read_preference=ReadPreference.SECONDARY)
    try:
        result = db_secondary.command("isMaster")
        print(f"READ_PREF=secondary      → served by: {result['me']} (is primary: {result['ismaster']})")
    except Exception as e:
        print(f"READ_PREF=secondary      → Error (no secondaries available): {e}")
    
    # SecondaryPreferred -- prefers secondary, falls back to primary
    db_sec_pref = client.get_database("demo", read_preference=ReadPreference.SECONDARY_PREFERRED)
    result = db_sec_pref.command("isMaster")
    print(f"READ_PREF=sec_preferred  → served by: {result['me']} (is primary: {result['ismaster']})")
    
    # Nearest -- lowest network latency, regardless of type
    db_nearest = client.get_database("demo", read_preference=ReadPreference.NEAREST)
    result = db_nearest.command("isMaster")
    print(f"READ_PREF=nearest        → served by: {result['me']} (is primary: {result['ismaster']})")
    
    print("\nNote: In a local Docker environment all nodes have similar latency.")
    print("In a multi-region deployment, 'nearest' routes to the closest datacenter.")
    
    client.close()


# ─── Demo 3: Write Concerns ──────────────────────────────────────────────────

def demo_write_concerns() -> None:
    print_section("3. Write Concerns - Durability vs Latency")
    
    client = MongoClient(REPLICA_SET_URI)
    db = client["demo"]
    
    N = 50
    
    # w=1: primary acknowledged only
    collection_w1 = db.get_collection("wc_benchmark", write_concern={"w": 1})
    collection_w1.drop()
    
    start = time.perf_counter()
    for i in range(N):
        collection_w1.insert_one({"i": i, "wc": 1, "ts": time.time()})
    elapsed_w1 = (time.perf_counter() - start) * 1000
    
    print(f"w=1 (primary only):  {N} inserts in {elapsed_w1:.0f}ms  ({elapsed_w1/N:.1f}ms/op)")
    
    # w=majority: majority of nodes must acknowledge
    collection_majority = db.get_collection("wc_benchmark", write_concern={"w": "majority"})
    
    start = time.perf_counter()
    for i in range(N):
        collection_majority.insert_one({"i": i, "wc": "majority", "ts": time.time()})
    elapsed_majority = (time.perf_counter() - start) * 1000
    
    print(f"w=majority:          {N} inserts in {elapsed_majority:.0f}ms  ({elapsed_majority/N:.1f}ms/op)")
    print(f"\nOverhead of majority: +{elapsed_majority - elapsed_w1:.0f}ms total (+{(elapsed_majority-elapsed_w1)/N:.1f}ms/op)")
    print("\nTrade-off:")
    print("  w=1:       Fast, but a write acknowledged by only the primary can be lost")
    print("             if the primary crashes before replicating to any secondary.")
    print("  w=majority: Slower, but a write is on >= 2 nodes -- survives any single-node failure.")
    
    # Cleanup
    db["wc_benchmark"].drop()
    client.close()


# ─── Demo 4: Failover Handling ───────────────────────────────────────────────

def demo_failover_simulation() -> None:
    print_section("4. Failover - What the Application Sees")
    
    client = MongoClient(
        REPLICA_SET_URI,
        serverSelectionTimeoutMS=30000,  # wait up to 30s for a new primary
        heartbeatFrequencyMS=500,        # check health every 500ms (faster than default 10s)
    )
    db = client["demo"]
    
    print("Continuously inserting documents. STOP THE PRIMARY CONTAINER now:")
    print("  docker compose stop mongo1")
    print("\nWatch how the driver handles the election...\n")
    
    i = 0
    errors = 0
    
    try:
        while i < 50:
            try:
                result = db.failover_test.insert_one({
                    "i": i,
                    "ts": time.time(),
                    "written_at": time.strftime("%H:%M:%S")
                })
                print(f"[{time.strftime('%H:%M:%S')}] Insert {i:03d}: OK  (_id={result.inserted_id})")
                i += 1
                time.sleep(0.5)
                
            except NotPrimaryError as e:
                errors += 1
                print(f"[{time.strftime('%H:%M:%S')}] NotPrimaryError (election in progress): {e}")
                time.sleep(1)
                
            except ConnectionFailure as e:
                errors += 1
                print(f"[{time.strftime('%H:%M:%S')}] ConnectionFailure: {e}")
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nStopped by user.")
    
    print(f"\nTotal: {i} successful inserts, {errors} errors during failover")
    print(f"Total documents in collection: {db.failover_test.count_documents({})}")
    
    # Cleanup
    db.failover_test.drop()
    client.close()


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("MongoDB Replica Set - Application Patterns Demo")
    print("Replica set URI:", REPLICA_SET_URI)
    
    demo_basic_connection()
    demo_read_preferences()
    demo_write_concerns()
    
    print("\n" + "="*60)
    print("  Run the failover demo separately? It requires manual steps.")
    print("="*60)
    run_failover = input("Run failover demo? (y/n): ").strip().lower()
    if run_failover == "y":
        demo_failover_simulation()
    
    print("\nDone!")
