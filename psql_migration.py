"""Database migration using psql command line tool to bypass Python 3.13/SQLAlchemy compatibility issues"""
import os
import sys
import urllib.parse

def run_psql_migration():
    """Execute database migration using psql command"""
    # Get DATABASE_URL from environment or config
    database_url = os.environ.get('DATABASE_URL', 'postgresql://fetfinder_db_user:yJXZDIUB3VRK7Qf7JxRdyddjiq3ngPEr@dpg-d38m518gjchc73d67m20-a.frankfurt-postgres.render.com/fetfinder_db')
    
    # Handle PostgreSQL URL format for psql
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Parse the database URL to extract components
    parsed_url = urllib.parse.urlparse(database_url)
    
    # Extract components
    username = parsed_url.username
    password = parsed_url.password
    hostname = parsed_url.hostname
    port = parsed_url.port or 5432
    database = parsed_url.path[1:]  # Remove leading slash
    
    # Create environment variable for psql to avoid password prompt
    env_vars = f"PGPASSWORD='{password}' "
    
    # SQL commands to add missing columns and create new tables
    sql_commands = [
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS about_me_video TEXT;",
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS relationship_goals VARCHAR(200);",
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS lifestyle VARCHAR(200);",
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS diet VARCHAR(100);",
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS smoking VARCHAR(50);",
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS drinking VARCHAR(50);",
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS occupation VARCHAR(100);",
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS education VARCHAR(100);",
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS children VARCHAR(50);",
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS pets VARCHAR(50);",
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS coins INTEGER DEFAULT 0;",
        "CREATE TABLE IF NOT EXISTS user_swipe (id SERIAL PRIMARY KEY, swiper_id INTEGER NOT NULL, swipee_id INTEGER NOT NULL, action VARCHAR(10) NOT NULL, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(swiper_id, swipee_id));"
    ]
    
    # Execute each SQL command using psql
    for i, sql_cmd in enumerate(sql_commands, 1):
        print(f"Executing migration step {i}...")
        
        # Construct the psql command
        psql_cmd = f"{env_vars} psql -h {hostname} -p {port} -U {username} -d {database} -c \"{sql_cmd}\""
        
        # Execute the command
        try:
            result = os.system(psql_cmd)
            if result == 0:
                print(f"[SUCCESS] Successfully executed step {i}")
            else:
                print(f"[ERROR] Error executing step {i}")
        except Exception as e:
            print(f"[ERROR] Error executing step {i}: {e}")
    
    print("Database migration completed!")

if __name__ == '__main__':
    run_psql_migration()