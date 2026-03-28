"""
SQLAlchemy ORM models.

Define your database tables here using the SQLAlchemy 2.0 declarative API.
Every class you define here that inherits from Base will become a table
when `Base.metadata.create_all(engine)` is called at startup.

Useful imports are already provided below. Add more as needed.

Documentation:
    https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html
"""
import datetime
from sqlalchemy import Column, Float, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass

class Customer(Base):
    """
    Customer model - maps to 'customers' table.
    Stores basic profile information.
    """
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    
    # Address is stored as JSONB to handle nested address structures from JSON
    address: Mapped[dict] = mapped_column(JSONB, nullable=True)

    # 1:N relationship - one customer can have many orders
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="customer")

class ProductInventory(Base):
    """
    Inventory model - maps to 'inventory' table.
    Manages stock levels and pricing.
    """
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Numeric(10, 2) provides exact precision for money values
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    
    # Constraint to prevent stock from going into negative values
    stock_quantity: Mapped[int] = mapped_column(Integer, CheckConstraint("stock_quantity >= 0"))
    
    # Link to the order items table
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="product")
    category: Mapped[str] = mapped_column(String)

class Order(Base):
    """
    Order model - maps to 'orders' table.
    Stores high-level order metadata.
    """
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(Integer, primary_key=True,autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Timestamp set automatically by the database on creation
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    """
    OrderItem model - maps to 'order_items' table.
    A bridge table connecting specific products to orders.
    """
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.order_id"), nullable=False)
    
    # Points to the 'inventory' table ID
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("inventory.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Bidirectional relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["ProductInventory"] = relationship("ProductInventory", back_populates="order_items")