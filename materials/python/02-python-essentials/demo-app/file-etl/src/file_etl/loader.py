"""Generic SQL Server loader."""

from typing import TypeVar, Generic
import pyodbc
from dataclasses import fields, is_dataclass

T = TypeVar('T')


class SqlServerLoader(Generic[T]):
    """Generic loader for inserting records into SQL Server.
    
    Works with any dataclass that has a to_dict() method.
    """
    
    def __init__(self, connection_string: str):
        """Initialize loader with SQL Server connection.
        
        Args:
            connection_string: ODBC connection string
        """
        self.connection_string = connection_string
    
    def load(self, records: list[T], table: str) -> int:
        """Load records into SQL Server table.
        
        Args:
            records: List of records to insert (must have to_dict() method)
            table: Name of the target table
            
        Returns:
            Number of records successfully inserted
        """
        if not records:
            print(f"No records to load into {table}")
            return 0
        
        # Connect to database
        conn = pyodbc.connect(self.connection_string)
        cursor = conn.cursor()
        
        inserted_count = 0
        
        try:
            for record in records:
                try:
                    # Convert record to dict
                    if hasattr(record, 'to_dict'):
                        data = record.to_dict()
                    elif is_dataclass(record):
                        # Fallback: extract fields from dataclass
                        data = {field.name: getattr(record, field.name) for field in fields(record)}
                    else:
                        raise ValueError(f"Record type {type(record)} must have to_dict() method or be a dataclass")
                    
                    # Build INSERT statement
                    columns = ', '.join(data.keys())
                    placeholders = ', '.join(['?' for _ in data])
                    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                    
                    # Execute insert
                    cursor.execute(sql, list(data.values()))
                    inserted_count += 1
                    
                except pyodbc.Error as e:
                    print(f"Warning: Failed to insert record: {e}")
                    continue
            
            # Commit transaction
            conn.commit()
            print(f"Successfully inserted {inserted_count} records into {table}")
            
        finally:
            cursor.close()
            conn.close()
        
        return inserted_count
    
    def load_batch(self, records: list[T], table: str, batch_size: int = 1000) -> int:
        """Load records in batches for better performance.
        
        Args:
            records: List of records to insert
            table: Name of the target table
            batch_size: Number of records per batch
            
        Returns:
            Total number of records successfully inserted
        """
        if not records:
            return 0
        
        total_inserted = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            inserted = self.load(batch, table)
            total_inserted += inserted
        
        return total_inserted
