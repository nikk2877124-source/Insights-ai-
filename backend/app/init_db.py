"""
Database initialization script.
Run this to create all tables in the PostgreSQL database.
"""
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.core.database import Base, engine
    from app.models import User, Dataset
    
    def init_db():
        """Create all database tables."""
        try:
            print("🔄 Creating database tables...")
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created successfully!")
            print("\nTables created:")
            print("  • users")
            print("  • datasets")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            raise
    
    if __name__ == "__main__":
        init_db()

except Exception as e:
    print(f"❌ Import Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
