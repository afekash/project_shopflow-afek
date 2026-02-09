"""Generic file readers for CSV and JSON formats."""

import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar, Generic, Callable, Any

T = TypeVar('T')


class FileReader(Generic[T], ABC):
    """Abstract base class for file readers.
    
    Generic over T - the type of records this reader produces.
    """
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        
        if not self.filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
    
    @abstractmethod
    def read(self) -> list[T]:
        """Read file and return list of records of type T."""
        pass


class CsvReader(FileReader[T]):
    """Read CSV file and convert rows to type T.
    
    Requires a factory function that converts dict to T.
    """
    
    def __init__(self, filepath: str, factory: Callable[[dict[str, Any]], T]):
        """Initialize CSV reader.
        
        Args:
            filepath: Path to CSV file
            factory: Function that converts a dict (CSV row) to type T
        """
        super().__init__(filepath)
        self.factory = factory
    
    def read(self) -> list[T]:
        """Read CSV file and convert each row to type T."""
        records: list[T] = []
        
        with open(self.filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
                try:
                    # Convert CSV row (dict) to type T
                    record = self.factory(row)
                    records.append(record)
                except (ValueError, KeyError) as e:
                    print(f"Warning: Skipping invalid row {row_num}: {e}")
                    continue
        
        return records


class JsonReader(FileReader[T]):
    """Read JSON file and convert objects to type T.
    
    Requires a factory function that converts dict to T.
    """
    
    def __init__(self, filepath: str, factory: Callable[[dict[str, Any]], T]):
        """Initialize JSON reader.
        
        Args:
            filepath: Path to JSON file
            factory: Function that converts a dict (JSON object) to type T
        """
        super().__init__(filepath)
        self.factory = factory
    
    def read(self) -> list[T]:
        """Read JSON file and convert each object to type T."""
        records: list[T] = []
        
        with open(self.filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Ensure data is a list
        if not isinstance(data, list):
            data = [data]
        
        for idx, item in enumerate(data):
            try:
                record = self.factory(item)
                records.append(record)
            except (ValueError, KeyError) as e:
                print(f"Warning: Skipping invalid item {idx}: {e}")
                continue
        
        return records


# Factory functions for creating model instances from dicts
def customer_from_dict(data: dict[str, Any]) -> "Customer":
    """Convert dict to Customer instance."""
    from file_etl.models import Customer
    return Customer(
        id=int(data["id"]),
        name=str(data["name"]),
        email=str(data["email"]),
    )


def order_from_dict(data: dict[str, Any]) -> "Order":
    """Convert dict to Order instance."""
    from file_etl.models import Order
    return Order(
        id=int(data["id"]),
        customer_id=int(data["customer_id"]),
        amount=float(data["amount"]),
        status=str(data["status"]),
    )
