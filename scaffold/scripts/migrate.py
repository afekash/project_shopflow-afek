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
    
    """Create all database tables, indexes, and constraints."""
    """יישום הלוגיקה ליצירת המבנים במסדי הנתונים"""
    
    # 1. יצירת הטבלאות ב-PostgreSQL
    # אנחנו מייבאים את ה-Base כאן כדי לוודא שכל המודלים שכתבנו נרשמו בו
    from ecommerce_pipeline.postgres_models import Base
    print("PostgreSQL: Creating tables based on postgres_models.py...")
    Base.metadata.create_all(bind=engine)
    
    # 2. יצירת אינדקסים ב-MongoDB (חשוב מאוד לטסטים של Phase 1)
    print("MongoDB: Creating indexes for products and snapshots...")
    
    # מוודא שחיפוש מוצר לפי ID יהיה מהיר וייחודי
    mongo_db.products.create_index("id", unique=True)
    
    # אינדקס טקסטואלי - כדי שנוכל לחפש מילים בתוך השם והתיאור של המוצר
    mongo_db.products.create_index([("name", "text"), ("description", "text")])
    

    # אינדקס לקטגוריה
    mongo_db.products.create_index("category")
    
    # אינדקסים להזמנות (Snapshots)
    mongo_db.order_snapshots.create_index("order_id", unique=True)

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
