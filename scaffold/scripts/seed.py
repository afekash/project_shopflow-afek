"""
Seed script — loads data into all databases.

Usage:
    uv run python -m scripts.seed

Prerequisites:
    Run scripts.migrate first to create database structures.

What to implement in seed():
    Phase 1: Load products.json + customers.json into Postgres and MongoDB
    Phase 2: Initialize Redis inventory counters from Postgres product stock
    Phase 3: Build Neo4j co-purchase graph from historical_orders.json

Seed data files are in the seed_data/ directory.
"""

import os
import json
import itertools 
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from pathlib import Path

from dotenv import load_dotenv
from ecommerce_pipeline.postgres_models import Customer, Order, OrderItem, ProductInventory
load_dotenv()

SEED_DIR = Path(__file__).parent.parent / "seed_data"


def seed(engine, mongo_db, redis_client=None, neo4j_driver=None):

    """Load seed data into all databases.

    Add your seeding logic here incrementally as you progress through phases.

    Args:
        engine: SQLAlchemy engine connected to Postgres
        mongo_db: pymongo Database instance
        redis_client: redis.Redis instance or None (Phase 2+)
        neo4j_driver: neo4j.Driver instance or None (Phase 3)

    Tip: Use json.load() to read the files in seed_data/:
        products = json.load(open(SEED_DIR / "products.json"))
        customers = json.load(open(SEED_DIR / "customers.json"))
        historical_orders = json.load(open(SEED_DIR / "historical_orders.json"))
    """


    # Initialize SQLAlchemy session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        
        # 1. Load Customers into Postgres
        #  Phase 1 — load products and customers into Postgres + MongoDB
        print("Seeding Customers...")
        with open(SEED_DIR / "customers.json", 'r', encoding='utf-8') as f:
            for c in json.load(f):
                session.add(Customer(
                    id=c['id'],
                    name=c['name'], 
                    email=c['email'], 
                    address=c['address']
                ))

        # 2. Load Products (Postgres + MongoDB)
        # Products are stored in Postgres (Inventory) and MongoDB (Catalog)
        print("Seeding Products...")
        with open(SEED_DIR / "products.json", 'r', encoding='utf-8') as f:
            for p in json.load(f):
                # Populate Postgres 'inventory' table
                session.add(ProductInventory(
                    id=p['id'], 
                    price=p['price'],
                    category=p.get('category', 'General'),  # <--- תוסיפי את השורה הזו כאן!
                    stock_quantity=p['stock_quantity']
                ))
                
                # Populate MongoDB 'product_catalog' collection
                # Upsert is used to prevent duplicate products
                mongo_db.product_catalog.update_one({"id": p['id']}, {"$set": p}, upsert=True)

        # 3. Load Historical Orders and OrderItems
        # This data is used for testing order history and analytics
        print("Seeding Historical Orders...")
        with open(SEED_DIR / "historical_orders.json", 'r', encoding='utf-8') as f:
            for o in json.load(f):
                # Create the main Order record
                session.add(Order(
                    order_id=o['order_id'], 
                    customer_id=o['customer_id'], 
                    created_at=o['created_at']
                ))
                # Create associated OrderItems
                for p_id in o['product_ids']:
                    session.add(OrderItem(order_id=o['order_id'], product_id=p_id))

        
        # First, persist all records from the JSON files
        session.commit()

        # Synchronize Postgres sequence for order_id.
        # This prevents 'UniqueViolation' errors when creating new orders in tests.
        # It sets the next auto-increment value to MAX(order_id) + 1.
        session.execute(text("SELECT setval('orders_order_id_seq', (SELECT max(order_id) FROM orders));"))
        session.commit()
        
        print("Postgres sequences synchronized successfully!")


        # --- Phase 2: Initialize Redis inventory counters ---redis
        if redis_client:
            print("Seeding Redis inventory counters...")
            # We query Postgres to get the latest authoritative stock levels
            products = session.query(ProductInventory).all()
            for p in products:
                # Key pattern from conventions: inventory:{product_id}
                redis_key = f"inventory:{p.id}"
                redis_client.set(redis_key, p.stock_quantity)
            print(f"Redis inventory synced for {len(products)} products.")


            # --- Phase 3: Build Neo4j co-purchase graph ---
        if neo4j_driver:
            print("Neo4j: Seeding co-purchase graph (BOUGHT_TOGETHER)...")
            
            # Loading products to map names to IDs in the graph
            with open(SEED_DIR / "products.json", 'r', encoding='utf-8') as f:
                product_list = json.load(f)
                product_map = {p['id']: p['name'] for p in product_list}
            
            with open(SEED_DIR / "historical_orders.json", 'r', encoding='utf-8') as f:
                historical_orders = json.load(f)
                
            with neo4j_driver.session() as session:
                for o in historical_orders:
                    # In historical_orders.json, the field is 'product_ids'
                    p_ids = o.get('product_ids', [])
                    
                    if len(p_ids) < 2:
                        continue
                    
                    # Generate all unique pairs from the order
                    for id1, id2 in itertools.combinations(p_ids, 2):
                        # MERGE ensures nodes/edges are created if missing, and updates weight
                        session.run("""
                            MERGE (a:Product {id: $id1})
                            ON CREATE SET a.name = $name1
                            MERGE (b:Product {id: $id2})
                            ON CREATE SET b.name = $name2
                            MERGE (a)-[r:BOUGHT_TOGETHER]-(b)
                            ON CREATE SET r.weight = 1
                            ON MATCH SET r.weight = r.weight + 1
                        """, 
                        id1=int(id1), name1=product_map.get(id1, "Unknown"),
                        id2=int(id2), name2=product_map.get(id2, "Unknown"))
            
            print(f"Neo4j: Graph seeded with BOUGHT_TOGETHER edges.")

    except Exception as e:
        # Rollback in case of any failure to maintain data integrity
        session.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        session.close()
    

      

    


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _pg_url() -> str:
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "ecommerce")
    user = os.environ.get("POSTGRES_USER", "postgres")
    pwd = os.environ.get("POSTGRES_PASSWORD", "postgres")
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"


def _mongo_db():
    from pymongo import MongoClient

    host = os.environ.get("MONGO_HOST", "localhost")
    port = int(os.environ.get("MONGO_PORT", "27017"))
    db = os.environ.get("MONGO_DB", "ecommerce")
    return MongoClient(host, port)[db]


def _redis_client():
    host = os.environ.get("REDIS_HOST")
    if not host:
        return None
    import redis

    port = int(os.environ.get("REDIS_PORT", "6379"))
    return redis.Redis(host=host, port=port, decode_responses=True)


def _neo4j_driver():
    host = os.environ.get("NEO4J_HOST")
    pwd = os.environ.get("NEO4J_PASSWORD")
    if not host or not pwd:
        return None
    from neo4j import GraphDatabase

    port = os.environ.get("NEO4J_BOLT_PORT", "7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    return GraphDatabase.driver(f"bolt://{host}:{port}", auth=(user, pwd))


def main():
    from sqlalchemy import create_engine

    engine = create_engine(_pg_url(), echo=False)
    mongo_db = _mongo_db()
    redis_client = _redis_client()
    neo4j_driver = _neo4j_driver()

    print("Seeding databases...")
    seed(engine, mongo_db, redis_client, neo4j_driver)
    print("Seeding complete.")

    if neo4j_driver:
        neo4j_driver.close()
    engine.dispose()


if __name__ == "__main__":
    main()
