"""
Database migration script.

Drops and recreates all database structures, then runs your migration logic.

Usage:
    uv run python -m scripts.migrate

What to implement in migrate():
    Phase 1: Create Postgres tables (Base.metadata.create_all) + MongoDB indexes
    Phase 2: No structural migration needed for Redis
    Phase 3: Neo4j uniqueness constraints
"""

import os

from dotenv import load_dotenv

load_dotenv()


def migrate(engine, mongo_db, redis_client=None, neo4j_driver=None):
    
    """
    Create all database tables, indexes, and constraints.
    This function handles the structural setup for Postgres, MongoDB, and Neo4j.
    """
    
    # 1. PostgreSQL: Create relational tables
    from ecommerce_pipeline.postgres_models import Base
    print("PostgreSQL: Creating tables based on SQLAlchemy models...")
    # Base.metadata.create_all uses the models defined in postgres_models.py
    Base.metadata.create_all(bind=engine)
    
    # 2. MongoDB: Create indexes for optimized document retrieval
    print("MongoDB: Creating indexes for products and order snapshots...")
    
    # Ensure unique constraint on product ID for fast lookups
    mongo_db.products.create_index("id", unique=True)
    
    # Create a compound text index to enable full-text search on name and description
    mongo_db.products.create_index([("name", "text"), ("description", "text")])
    
    # Index by category for faster filtering
    mongo_db.products.create_index("category")
    
    # Ensure each order snapshot has a unique order_id
    mongo_db.order_snapshots.create_index("order_id", unique=True)

    # 3. Neo4j: Create graph constraints (Phase 3)
    if neo4j_driver:
        print("Neo4j: Creating uniqueness constraints for the Product graph...")
        with neo4j_driver.session() as session:
            # Phase 3: Ensure each Product node has a unique ID to prevent duplicates in the graph
            session.run("""
                CREATE CONSTRAINT product_id IF NOT EXISTS 
                FOR (p:Product) REQUIRE p.id IS UNIQUE
            """)
    
    print("Migration logic implemented and executed successfully!")


    """Create all database tables, indexes, and constraints.

    This function is called after reset_all() has wiped everything.
    Add your creation logic here incrementally as you progress through phases.

    Args:
        engine: SQLAlchemy engine connected to Postgres
        mongo_db: pymongo Database instance
        redis_client: redis.Redis instance or None (Phase 2+)
        neo4j_driver: neo4j.Driver instance or None (Phase 3)
    
    pass  #  Phase 1 — create Postgres tables and MongoDB indexes
    """


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
    """
    test of DEBUG show me 
    print("\n" + "="*50)
    print(f"DEBUG: מחפש קובץ .env בכתובת: {os.getcwd()}")
    print(f"DEBUG: האם קובץ .env קיים? {os.path.exists('.env')}")
    print(f"DEBUG: שם ה-DB שהמחשב קורא: '{os.environ.get('POSTGRES_DB')}'")
    print(f"DEBUG: ה-URL המלא שנוצר: {_pg_url()}")
    print("="*50 + "\n")
    """


    from sqlalchemy import create_engine

    from ecommerce_pipeline.reset import reset_all

    engine = create_engine(_pg_url(), echo=False)
    mongo_db = _mongo_db()
    redis_client = _redis_client()
    neo4j_driver = _neo4j_driver()

    print("Resetting all databases...")
    reset_all(engine, mongo_db, redis_client, neo4j_driver)

    print("Running migration...")
    migrate(engine, mongo_db, redis_client, neo4j_driver)

    print("Migration complete.")

    if neo4j_driver:
        neo4j_driver.close()
    engine.dispose()


if __name__ == "__main__":
    main()
