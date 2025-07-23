#!/usr/bin/env python3
"""Test minimal alembic functionality"""

from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config

# Clean up first
db_url = 'postgresql://postgres:postgres@postgres:5432/migration_db'
engine = create_engine(db_url)

print("Cleaning up...")
with engine.connect() as conn:
    conn.execute(text("DROP SCHEMA IF EXISTS migration CASCADE"))
    conn.execute(text("CREATE SCHEMA migration"))
    conn.execute(text("SET search_path TO migration, public"))
    conn.commit()

print("Setting up alembic config...")
# Create alembic config
config = Config("alembic.ini")

# Override the URL to ensure we're using the right one
config.set_main_option("sqlalchemy.url", db_url)

print(f"Database URL: {config.get_main_option('sqlalchemy.url')}")

# Try to get current version
print("\nChecking current alembic version...")
try:
    command.current(config)
except Exception as e:
    print(f"Error getting current version: {e}")

# Try to run just the first migration
print("\nAttempting to run first migration...")
try:
    command.upgrade(config, "000_ensure_migration_schema")
    print("Migration completed")
except Exception as e:
    print(f"Migration error: {e}")
    import traceback
    traceback.print_exc()

# Check what happened
print("\nChecking results...")
with engine.connect() as conn:
    # Check schemas
    result = conn.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'migration'"))
    if result.fetchone():
        print("✓ Migration schema exists")
    
    # Check tables
    result = conn.execute(text("""
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE schemaname = 'migration'
        ORDER BY tablename
    """))
    
    tables = list(result)
    print(f"\nTables in migration schema: {len(tables)}")
    for schema, table in tables:
        print(f"  - {schema}.{table}")
    
    # Check alembic_version
    try:
        result = conn.execute(text("SELECT * FROM migration.alembic_version"))
        versions = list(result)
        print(f"\nAlembic versions: {versions}")
    except Exception as e:
        print(f"\nNo alembic_version table or error: {e}")