"""
Verification script to check if tables were created in PostgreSQL.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.core.database import engine
    from sqlalchemy import inspect, text
    
    # Create inspector to check existing tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("📊 Tables in PostgreSQL database:")
    print("=" * 50)
    
    if tables:
        for table in tables:
            print(f"\n✅ Table: {table}")
            columns = inspector.get_columns(table)
            print("   Columns:")
            for col in columns:
                col_type = col['type']
                nullable = "nullable" if col['nullable'] else "NOT NULL"
                print(f"     • {col['name']}: {col_type} ({nullable})")
    else:
        print("❌ No tables found in database!")
        
    # Try to create tables if they don't exist
    if 'users' not in tables or 'datasets' not in tables:
        print("\n🔄 Creating missing tables...")
        from app.core.database import Base
        from app.models import User, Dataset
        
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")
        
        # Verify again
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\n✅ Total tables now: {len(tables)}")
        for table in tables:
            print(f"  • {table}")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
