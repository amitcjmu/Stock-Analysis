#!/usr/bin/env python3
"""Test running migration code directly"""

from sqlalchemy import create_engine, text

# Database URL
db_url = "postgresql://postgres:postgres@postgres:5432/migration_db"
engine = create_engine(db_url, echo=True)  # Enable SQL echo

print("Testing direct migration execution...")
print(f"Database URL: {db_url}")

# Test connection and execute in transaction
with engine.begin() as conn:
    try:
        # Create schema
        print("\nCreating migration schema...")
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS migration"))

        # Set search path
        print("Setting search path...")
        conn.execute(text("SET search_path TO migration, public"))

        # Create alembic_version table
        print("\nCreating alembic_version table...")
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """
            )
        )

        # Create a simple table
        print("\nCreating test_table...")
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100)
            )
        """
            )
        )

        # Insert alembic version
        print("\nInserting alembic version...")
        conn.execute(
            text(
                """
            INSERT INTO alembic_version (version_num) 
            VALUES ('test_version')
            ON CONFLICT DO NOTHING
        """
            )
        )

        print("\nAll operations completed successfully!")

    except Exception as e:
        print(f"\nError during transaction: {e}")
        raise

# Verify
print("\nVerifying tables...")
with engine.connect() as conn:
    result = conn.execute(
        text(
            """
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE schemaname = 'migration'
        ORDER BY tablename
    """
        )
    )

    tables = list(result)
    print(f"\nTables in migration schema: {len(tables)}")
    for schema, table in tables:
        print(f"  - {schema}.{table}")

    # Check alembic_version content
    result = conn.execute(text("SELECT * FROM migration.alembic_version"))
    versions = list(result)
    print(f"\nAlembic versions: {versions}")
