import os
from app import app, create_tables, export_data

# Create database tables when the module is imported
try:
    with app.app_context():
        create_tables()
        print("Database tables created successfully!")
except Exception as e:
    print(f"Error creating database tables: {e}")
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
    # For local development
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)