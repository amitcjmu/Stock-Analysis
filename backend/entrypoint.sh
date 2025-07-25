#!/bin/bash
# Railway Entrypoint Script - Ensures migrations run before starting the app

set -e

echo "🚀 Railway Entrypoint Starting..."
echo "📅 Date: $(date)"
echo "📁 Working Directory: $(pwd)"
echo "🗄️ DATABASE_URL configured: $(echo "$DATABASE_URL" | cut -c1-50)..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if python -c "
import os
import psycopg
from urllib.parse import urlparse

db_url = os.getenv('DATABASE_URL', '')
if 'postgresql+asyncpg://' in db_url:
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')

try:
    conn = psycopg.connect(db_url)
    conn.close()
    exit(0)
except Exception as e:
    print(f'Connection failed: {e}')
    exit(1)
" 2>&1; then
        echo "✅ Database is ready!"
        break
    fi

    echo "   Attempt $attempt/$max_attempts: Database not ready yet..."
    sleep 2
    attempt=$((attempt + 1))
done

# Fix migration state issues intelligently instead of destructive cleanup
echo "🔧 Checking and fixing migration state..."

# First, run the SQL script to ensure alembic_version table exists with proper schema
echo "🔧 Running fix_alembic_version.sql to ensure migration schema exists..."
python -c "
import os
import psycopg
from pathlib import Path

db_url = os.getenv('DATABASE_URL', '')
if 'postgresql+asyncpg://' in db_url:
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')

try:
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Read and execute the SQL script
            sql_file = Path('scripts/fix_alembic_version.sql')
            if sql_file.exists():
                sql_content = sql_file.read_text()
                cur.execute(sql_content)
                conn.commit()
                print('✅ Successfully ran fix_alembic_version.sql')
            else:
                print('⚠️  fix_alembic_version.sql not found')
except Exception as e:
    print(f'⚠️  Error running fix_alembic_version.sql: {e}')
"

if python scripts/fix_migration_state.py; then
    echo "✅ Migration state validated/fixed successfully"
else
    echo "❌ Migration state fix failed, continuing with standard migration process..."
fi

# Run Alembic migrations with intelligent error handling
echo "🔄 Running Alembic migrations..."

if python -m alembic upgrade head; then
    echo "✅ Alembic migrations completed successfully!"
else
    echo "❌ Alembic migration failed. Running fix script again..."

    # Try fix script one more time in case of race conditions
    if python scripts/fix_migration_state.py; then
        echo "✅ Migration state re-fixed, trying upgrade again..."
        if python -m alembic upgrade head; then
            echo "✅ Alembic migrations completed after fix!"
        else
            echo "❌ Migration still failed, but continuing with app startup..."
        fi
    else
        echo "❌ Migration fix failed, but continuing with app startup..."
    fi
fi

# Initialize database with default users and data
echo "🔄 Initializing database with default users and data..."
if python -m app.core.database_initialization; then
    echo "✅ Database initialization completed successfully!"
else
    echo "❌ Database initialization failed, but continuing..."
fi

# Start the application directly
echo "🚀 Starting application..."
exec python start.py
