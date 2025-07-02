#!/usr/bin/env python3
"""Debug alembic migration issues"""
import os
import sys
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

# Set up paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create alembic config
config = Config("alembic.ini")

# Get database URL
db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@postgres:5432/migration_db')
sync_url = db_url.replace('+asyncpg', '')

print(f"Database URL: {sync_url}")

# Create engine
engine = create_engine(sync_url)

# Check current state
with engine.connect() as conn:
    # Check alembic version
    try:
        result = conn.execute(text("SELECT version_num FROM migration.alembic_version"))
        versions = [row[0] for row in result]
        print(f"\nCurrent alembic versions: {versions}")
    except Exception as e:
        print(f"\nNo alembic_version table or error: {e}")
    
    # Count tables
    result = conn.execute(text("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema = 'migration' AND table_type = 'BASE TABLE'
    """))
    count = result.fetchone()[0]
    print(f"Tables in migration schema: {count}")

# Try to run a specific migration
print("\nAttempting to run migration 000_ensure_migration_schema...")
try:
    command.upgrade(config, "000_ensure_migration_schema")
    print("Migration completed")
except Exception as e:
    print(f"Migration error: {e}")
    import traceback
    traceback.print_exc()

# Check result
with engine.connect() as conn:
    result = conn.execute(text("SELECT version_num FROM migration.alembic_version"))
    versions = [row[0] for row in result]
    print(f"\nAlembic versions after migration: {versions}")