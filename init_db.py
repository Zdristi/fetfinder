import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, create_tables, import_data
from migrate_db import check_and_add_columns

if __name__ == '__main__':
    print("Starting database initialization...")
    try:
        create_tables()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        import traceback
        traceback.print_exc()
    
    # Run migrations to update existing tables with new columns
try:
    check_and_add_columns()
    print("Database migrations completed successfully!")
except Exception as e:
    print(f"Error running Python-based database migrations: {e}")
    print("Attempting psql-based migration...")
    try:
        from psql_migration import run_psql_migration
        run_psql_migration()
        print("Psql-based database migrations completed successfully!")
    except Exception as e2:
        print(f"Error running psql-based database migrations: {e2}")
        import traceback
        traceback.print_exc()
    
    # Try to import data from backup if it exists
try:
    import_data()
    print("Data imported from backup successfully!")
except Exception as e:
    print(f"No backup data to import or import failed: {e}")


if __name__ == '__main__':
    print("For manual migration, run: python init_db.py")