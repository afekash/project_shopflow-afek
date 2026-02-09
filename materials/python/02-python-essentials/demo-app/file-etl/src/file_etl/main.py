"""Main ETL pipeline orchestration."""

from file_etl.models import Customer, Order
from file_etl.readers import CsvReader, JsonReader, customer_from_dict, order_from_dict
from file_etl.loader import SqlServerLoader


def main() -> None:
    """Run the ETL pipeline."""
    
    print("=" * 60)
    print("File ETL Demo Application")
    print("=" * 60)
    
    # SQL Server connection string
    # Modify this based on your SQL Server setup
    connection_string = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=demo_etl;"
        "Trusted_Connection=yes;"
    )
    
    try:
        # Step 1: Extract - Read customers from CSV
        print("\n[1/4] Extracting customers from CSV...")
        customer_reader = CsvReader[Customer](
            filepath="data/customers.csv",
            factory=customer_from_dict
        )
        customers = customer_reader.read()
        print(f"  ✓ Read {len(customers)} customers")
        
        # Step 2: Extract - Read orders from JSON
        print("\n[2/4] Extracting orders from JSON...")
        order_reader = JsonReader[Order](
            filepath="data/orders.json",
            factory=order_from_dict
        )
        orders = order_reader.read()
        print(f"  ✓ Read {len(orders)} orders")
        
        # Step 3: Load - Insert customers into database
        print("\n[3/4] Loading customers into database...")
        customer_loader = SqlServerLoader[Customer](connection_string)
        customer_loader.load(customers, "customers")
        
        # Step 4: Load - Insert orders into database
        print("\n[4/4] Loading orders into database...")
        order_loader = SqlServerLoader[Order](connection_string)
        order_loader.load(orders, "orders")
        
        print("\n" + "=" * 60)
        print("ETL Pipeline Completed Successfully!")
        print("=" * 60)
        
        # Summary statistics
        print("\nSummary:")
        print(f"  • Customers processed: {len(customers)}")
        print(f"  • Orders processed: {len(orders)}")
        
        # Show sample data
        if customers:
            print(f"\nSample customer: {customers[0]}")
        if orders:
            print(f"Sample order: {orders[0]}")
    
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you're running from the project root directory:")
        print("  cd file-etl")
        print("  uv run python -m file_etl.main")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPossible issues:")
        print("  • SQL Server not running")
        print("  • Database 'demo_etl' not created")
        print("  • Tables not created (see README.md for SQL setup)")
        print("  • ODBC driver not installed")
        raise


if __name__ == "__main__":
    main()
