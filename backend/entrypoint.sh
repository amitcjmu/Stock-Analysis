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

# Reset migration history for clean slate
echo "🔄 Resetting migration history for clean deployment..."
python -c "
import os
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def reset_migration_history():
    database_url = os.getenv('DATABASE_URL', '')
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        # Drop and recreate alembic_version table
        await conn.execute(text('DROP TABLE IF EXISTS alembic_version'))
        await conn.execute(text('CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))'))
        print('✅ Migration history reset')
    await engine.dispose()

asyncio.run(reset_migration_history())
"

# Run database migrations
echo "🔄 Running database migrations..."
if python -m alembic upgrade head; then
    echo "✅ Migrations completed successfully!"
else
    echo "❌ Migration failed, but continuing..."
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