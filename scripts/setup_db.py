"""
Database initialization script for AdaptiveCare.
"""
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Initialize database with schema."""
    print("\n🗄️  Initializing AdaptiveCare Database...")
    print("="*60)
    
    try:
        from backend.db.connection import init_db, get_db
        from backend.core.config import Config
        
        # Initialize database
        db_url = getattr(Config, 'DATABASE_URL', 'sqlite:///./adaptivecare.db')
        print(f"📍 Database URL: {db_url}")
        
        engine = init_db(db_url)
        print("✅ Database schema created successfully!")
        
        # Test connection
        db = get_db()
        print("✅ Database connection verified!")
        db.close()
        
        # Show database info
        if db_url.startswith('sqlite'):
            db_file = db_url.replace('sqlite:///', '')
            db_path = Path(db_file).resolve()
            print(f"\n📊 SQLite Database: {db_path}")
            if db_path.exists():
                size = db_path.stat().st_size
                print(f"   Size: {size:,} bytes")
        
        print("\n✅ Database ready!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Database initialization failed!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
