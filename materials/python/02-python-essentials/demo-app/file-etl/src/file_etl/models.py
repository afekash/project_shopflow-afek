"""Data models for the ETL application."""

from dataclasses import dataclass


@dataclass
class Customer:
    """Customer entity with validation in __post_init__."""
    
    id: int
    name: str
    email: str
    
    def __post_init__(self) -> None:
        """Validate customer data after initialization."""
        if self.id <= 0:
            raise ValueError(f"Customer ID must be positive, got {self.id}")
        
        if not self.name or not self.name.strip():
            raise ValueError("Customer name cannot be empty")
        
        if "@" not in self.email:
            raise ValueError(f"Invalid email format: {self.email}")
    
    def to_dict(self) -> dict[str, str | int]:
        """Convert to dictionary for database insertion."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
        }


@dataclass
class Order:
    """Order entity with validation."""
    
    id: int
    customer_id: int
    amount: float
    status: str
    
    def __post_init__(self) -> None:
        """Validate order data after initialization."""
        if self.id <= 0:
            raise ValueError(f"Order ID must be positive, got {self.id}")
        
        if self.customer_id <= 0:
            raise ValueError(f"Customer ID must be positive, got {self.customer_id}")
        
        if self.amount < 0:
            raise ValueError(f"Order amount cannot be negative, got {self.amount}")
        
        valid_statuses = {"pending", "completed", "cancelled"}
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {valid_statuses}")
    
    def to_dict(self) -> dict[str, str | int | float]:
        """Convert to dictionary for database insertion."""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "status": self.status,
        }
