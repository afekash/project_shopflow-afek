"""
DBAccess — the data access layer.

This is one of the files you implement. The web API is already wired up;
every route calls one method on this class. Your job is to replace each
`raise NotImplementedError(...)` with a real implementation.

Work through the phases in order. Read the corresponding lesson file before
starting each phase.

You also implement scripts/migrate.py and scripts/seed.py alongside this file.
"""

from __future__ import annotations

import json
import logging
from ecommerce_pipeline.models.responses import OrderSnapshotResponse
from ecommerce_pipeline.models.responses import ProductResponse
from itertools import combinations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import neo4j
    import redis as redis_lib
    from pymongo.database import Database as MongoDatabase
    from sqlalchemy.orm import sessionmaker

    from ecommerce_pipeline.models.requests import OrderItemRequest
    from ecommerce_pipeline.models.responses import (
        CategoryRevenueResponse,
        OrderCustomerEmbed,
        OrderItemResponse,
        OrderResponse,
        OrderSnapshotResponse,
        ProductResponse,
        RecommendationResponse,
    )

logger = logging.getLogger(__name__)


class DBAccess:
    def __init__(
        self,
        pg_session_factory: sessionmaker,
        mongo_db: MongoDatabase,
        redis_client: redis_lib.Redis | None = None,
        neo4j_driver: neo4j.Driver | None = None,
    ) -> None:
        self._pg_session_factory = pg_session_factory
        self._mongo_db = mongo_db
        self._redis = redis_client
        self._neo4j = neo4j_driver

    # ── Phase 1 ───────────────────────────────────────────────────────────────

    def create_order(self, customer_id: int, items: list[OrderItemRequest]) -> OrderResponse:
        
        """Place an order atomically.

        See OrderItemRequest in models/requests.py for the input shape.
        See OrderResponse in models/responses.py for the return shape.

        Raises ValueError if any product has insufficient stock. When that
        happens, no data is modified in any database.

        After the order is persisted transactionally, a denormalized snapshot
        is saved for read access, and downstream counters and graph edges are
        updated (best-effort, does not roll back the order on failure).
        """
        """Place an order atomically across Postgres and MongoDB."""
        """
        Place an order atomically across Postgres and MongoDB.
        Uses a transaction to ensure stock is updated and the order is saved.
        """
        from sqlalchemy.orm import Session
        from ecommerce_pipeline.postgres_models import Order, OrderItem, ProductInventory, Customer
        from ecommerce_pipeline.models.responses import OrderCustomerEmbed, OrderItemResponse, OrderResponse
        from datetime import datetime

        # 1. Start a SQLAlchemy session from the factory
        with self._pg_session_factory() as session:
            try:
                # 2. Fetch customer details for the MongoDB snapshot
                customer = session.query(Customer).filter(Customer.id == customer_id).first()
                if not customer:
                    raise ValueError(f"Customer {customer_id} not found")

                total_amount = 0.0
                snapshot_items = []
                order_items_to_save = []

                # 3. Process items: Check stock and calculate totals
                for item_req in items:
                    # 'with_for_update' locks the row to prevent concurrent stock issues
                    product = session.query(ProductInventory).filter(
                        ProductInventory.id == item_req.product_id
                    ).with_for_update().first()
                    
                    if not product:
                        raise ValueError(f"Product {item_req.product_id} not found")
                    
                    if product.stock_quantity < item_req.quantity:
                        raise ValueError("Insufficient stock")

                    # Update stock levels in Postgres
                    product.stock_quantity -= item_req.quantity
                    
                    # Convert Numeric/Decimal to float for calculations and response
                    price_at_order = float(product.price)
                    item_total = price_at_order * item_req.quantity
                    total_amount += item_total

                    # Prepare OrderItem for Postgres
                    order_items_to_save.append(OrderItem(
                        product_id=product.id,
                        quantity=item_req.quantity
                    ))

                    # Prepare Item for MongoDB snapshot
                    # (Note: Using a placeholder for name if not in Inventory table)
                    snapshot_items.append(OrderItemResponse(
                        product_id=product.id,
                        product_name="Product Details", 
                        quantity=item_req.quantity,
                        unit_price=price_at_order
                    ))

                # 4. Create the main Order in Postgres
                # We do NOT pass order_id, Postgres generates it via autoincrement
                new_order = Order(
                    customer_id=customer_id,
                    total_amount=total_amount
                )
                session.add(new_order)
                
                # Flush tells Postgres to execute the INSERT and return the new ID
                session.flush() 

                # Link items to the newly generated order_id
                for oi in order_items_to_save:
                    oi.order_id = new_order.order_id
                    session.add(oi)

                # 5. Save denormalized snapshot to MongoDB
                # This happens before the commit to keep everything in sync
                current_time = datetime.now().isoformat()
                self.save_order_snapshot(
                    order_id=new_order.order_id,
                    customer=OrderCustomerEmbed(
                        id=customer.id, 
                        name=customer.name, 
                        email=customer.email
                    ),
                    items=snapshot_items,
                    total_amount=total_amount,
                    status="completed",
                    created_at=current_time
                )

                # 6. Final Commit - If we get here, both databases are updated
                session.commit()

                return OrderResponse(
                    order_id=new_order.order_id,
                    customer_id=customer_id,
                    total_amount=total_amount,
                    status="completed",
                    created_at=current_time,
                    items=snapshot_items
                )

            except Exception as e:
                # If anything fails (Postgres OR MongoDB), undo all Postgres changes
                session.rollback()
                logger.error(f"Order creation failed: {e}")
                raise e

    def get_product(self, product_id: int) -> ProductResponse | None:

        """Fetch a product by its integer ID.

        See ProductResponse in models/responses.py for the return shape.
        Returns None if not found.
        """
        """Fetch a product by its integer ID.

        See ProductResponse in models/responses.py for the return shape.
        Returns None if not found.
        """
       # Search in product_catalog for consistency with the tests
        product_data = self._mongo_db.product_catalog.find_one({"id": int(product_id)})

        if not product_data:
            return None
            
        product_data.pop("_id", None)
        return ProductResponse(**product_data)
        
        """
        raise NotImplementedError("Phase 1: implement get_product")
        """

    def search_products(
        self,
        category: str | None = None,
        q: str | None = None,
    ) -> list[ProductResponse]:
        """Search the product catalog with optional filters.

        category: exact match on the category field
        q: case-insensitive substring match on the product name
        Both filters are ANDed together. Returns all products if both are None.
        """

        """Search the product catalog with optional filters."""
        
       # Build the MongoDB query dictionary
        query = {}
        if category:
            query["category"] = category
        if q:
            # Case-insensitive substring match on the product name
            query["name"] = {"$regex": q, "$options": "i"}

        # Use 'product_catalog' as confirmed by the DEBUG logs
        cursor = self._mongo_db.product_catalog.find(query)
        
        results = []
        for p in cursor:
            # Remove MongoDB's internal _id to prevent validation errors
            p.pop("_id", None)
            # Map dictionary to ProductResponse object
            results.append(ProductResponse(**p))
            
        return results
        """
        raise NotImplementedError("Phase 1: implement search_products")
        """

    def save_order_snapshot(
        self,
        order_id: int,
        customer: OrderCustomerEmbed,
        items: list[OrderItemResponse],
        total_amount: float,
        status: str,
        created_at: str,
    ) -> str:
        """Save a denormalized order snapshot for fast read access.

        See OrderCustomerEmbed and OrderItemResponse in models/responses.py
        for the input shapes.

        Embeds all customer and product details as they existed at the time
        of the order, so the snapshot remains accurate even if prices or
        names change later.

        Returns a string identifier for the saved document.

        Called internally by create_order after the transactional write
        commits. Not called directly by routes.
        """

        # Prepare the document dictionary from input models
        # Use .model_dump() to convert Pydantic models to dicts
        snapshot_doc = {
            "order_id": order_id,
            "customer": customer.model_dump(),
            "items": [item.model_dump() for item in items],
            "total_amount": total_amount,
            "status": status,
            "created_at": created_at
        }

        # Update or Insert (upsert) the snapshot into 'order_snapshots' collection
        self._mongo_db.order_snapshots.update_one(
            {"order_id": order_id},
            {"$set": snapshot_doc},
            upsert=True
        )

        # Return the order_id as a string as required by the test
        return str(order_id)
        """
        raise NotImplementedError("Phase 1: implement save_order_snapshot")
        """

    def get_order(self, order_id: int) -> OrderSnapshotResponse | None:
        """Fetch a single order snapshot by order_id.

        See OrderSnapshotResponse in models/responses.py for the return shape.
        Returns None if not found.
        """

        # 1. Search for the snapshot in the 'order_snapshots' collection
        # Search specifically by the integer order_id
        data = self._mongo_db.order_snapshots.find_one({"order_id": order_id})
        
        # 2. Return None if the order is not found
        if not data:
            return None
            
        # 3. Remove the MongoDB internal ID field
        data.pop("_id", None)
        
        # 4. Convert the dictionary back to the OrderSnapshotResponse model
        # The API/Test expects an object, not a raw dictionary
        return OrderSnapshotResponse(**data)
        """
        raise NotImplementedError("Phase 1: implement get_order")
        """

    def get_order_history(self, customer_id: int) -> list[OrderSnapshotResponse]:
        """Fetch all order snapshots for a customer, sorted by created_at descending.

        Returns an empty list if the customer has no orders.
        """
        # 1. Search for snapshots where the nested customer.id matches
        # We use dot notation "customer.id" to reach the nested field in MongoDB
        cursor = self._mongo_db.order_snapshots.find({"customer.id": customer_id})
        
        # 2. Convert cursor to a list of dictionaries
        results = list(cursor)
        
        # 3. Sort by 'created_at' in descending order (newest first)
        # We use the string date for sorting
        results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        history = []
        for r in results:
            # 4. Clean up the internal MongoDB ID
            r.pop("_id", None)
            # 5. Convert each dictionary to an OrderSnapshotResponse object
            history.append(OrderSnapshotResponse(**r))
            
        return history
        """
        raise NotImplementedError("Phase 1: implement get_order_history")
        """

    def revenue_by_category(self) -> list[CategoryRevenueResponse]:
        """Compute total revenue per product category, sorted by total_revenue descending.

        See CategoryRevenueResponse in models/responses.py for the return shape.
        """
        """
        Compute total revenue per product category based on Postgres data.
        Returns a list of CategoryRevenueResponse sorted by total_revenue descending.
        """
        from sqlalchemy import func
        from sqlalchemy.orm import Session
        from ecommerce_pipeline.postgres_models import OrderItem, ProductInventory
        from ecommerce_pipeline.models.responses import CategoryRevenueResponse

        # 1. Start a session to query Postgres via the session factory
        with self._pg_session_factory() as session:
            
            # 2. Build the aggregation query using a JOIN
            # We multiply quantity by price, group by category, and sum the results
            query = (
                session.query(
                    ProductInventory.category.label("category"),
                    func.sum(OrderItem.quantity * ProductInventory.price).label("total_revenue")
                )
                .join(OrderItem, ProductInventory.id == OrderItem.product_id)
                .group_by(ProductInventory.category)
                .order_by(func.sum(OrderItem.quantity * ProductInventory.price).desc())
            )

            results = query.all()

            # 3. Convert raw database rows into our Pydantic response models
            # We use float() to ensure compatibility with the CategoryRevenueResponse schema
            category_report = [
                CategoryRevenueResponse(
                    category=row.category, 
                    total_revenue=float(row.total_revenue)
                )
                for row in results
            ]
            
            return category_report


        """
        raise NotImplementedError("Phase 1: implement revenue_by_category")
        """


    # ── Phase 2 ───────────────────────────────────────────────────────────────
    #
    # In this phase you also need to:
    #   - Update create_order to DECR Redis inventory counters after the
    #     Postgres transaction succeeds.
    #   - Optionally, add a fast pre-check: before starting the Postgres
    #     transaction, check the Redis counter. If it shows insufficient
    #     stock, fail fast without hitting Postgres.
    #   - Update scripts/seed.py to initialize inventory counters in Redis.
    #   - Add cache-aside logic to get_product (check Redis first, populate
    #     on miss with a 300-second TTL).

    def invalidate_product_cache(self, product_id: int) -> None:
        """Remove a product's cached entry.

        Call this after updating a product's data so the next read fetches
        fresh data from the primary store. No-op if no entry exists.
        """
        raise NotImplementedError("Phase 2: implement invalidate_product_cache")

    def record_product_view(self, customer_id: int, product_id: int) -> None:
        """Record that a customer viewed a product.

        Maintains a bounded, ordered list of the customer's most recently
        viewed products (most recent first, capped at 10 entries).
        """
        raise NotImplementedError("Phase 2: implement record_product_view")

    def get_recently_viewed(self, customer_id: int) -> list[int]:
        """Return up to 10 recently viewed product IDs for a customer.

        Returns IDs as integers, most recently viewed first.
        Returns an empty list if no views have been recorded.
        """
        raise NotImplementedError("Phase 2: implement get_recently_viewed")

    # ── Phase 3 ───────────────────────────────────────────────────────────────
    #
    # In this phase you also need to:
    #   - Update create_order to MERGE co-purchase edges in Neo4j for every
    #     pair of products in the order, incrementing the edge weight.
    #   - Update scripts/migrate.py to create Neo4j constraints.
    #   - Update scripts/seed.py to build the co-purchase graph from
    #     seed_data/historical_orders.json.

    def get_recommendations(self, product_id: int, limit: int = 5) -> list[RecommendationResponse]:
        """Return product recommendations based on co-purchase patterns.

        See RecommendationResponse in models/responses.py for the return shape.
        Sorted by score descending. Returns an empty list if no co-purchase relationships exist.
        """
        raise NotImplementedError("Phase 3: implement get_recommendations")
