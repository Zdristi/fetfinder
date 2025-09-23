import os
from app import app, create_tables, export_data

if __name__ == "__main__":
    # Create database tables
    create_tables()
    
    # Export data to JSON backup (for migration purposes)
    try:
        export_data()
        print("Data exported to data_backup.json")
    except Exception as e:
        print(f"Could not export data: {e}")
    
    # For local development
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)