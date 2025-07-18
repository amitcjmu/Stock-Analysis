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

# Bootstrap clean migration state for fresh deployment
echo "🔄 Bootstrapping clean migration state..."
python -c "
import os
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def bootstrap_migration_state():
    database_url = os.getenv('DATABASE_URL', '')
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    engine = create_async_engine(database_url)
    
    async with engine.begin() as conn:
        # Drop all existing tables for clean slate
        await conn.execute(text('DROP SCHEMA IF EXISTS public CASCADE'))
        await conn.execute(text('CREATE SCHEMA public'))
        
        # Drop migration schema if it exists
        await conn.execute(text('DROP SCHEMA IF EXISTS migration CASCADE'))
        await conn.execute(text('CREATE SCHEMA migration'))
        
        print('✅ Clean migration state bootstrapped')
        
    await engine.dispose()

asyncio.run(bootstrap_migration_state())
"

# Run Alembic migrations from clean state
echo "🔄 Running Alembic migrations from clean state..."

# Follow Alembic best practices for squashed migrations
echo "🔄 Running Alembic migrations using best practices..."

# The key insight: Let Alembic handle everything after clean bootstrap
# Our comprehensive migration has down_revision = None, so it should work cleanly
if python -m alembic upgrade head; then
    echo "✅ Alembic migrations completed successfully!"
else
    echo "❌ Alembic migration failed. Attempting recovery..."
    
    # Recovery: Use stamp then upgrade approach
    echo "🔄 Attempting recovery with stamp approach..."
    if python -m alembic stamp base; then
        echo "✅ Stamped to base revision"
        if python -m alembic upgrade head; then
            echo "✅ Upgrade successful after stamp!"
        else
            echo "❌ Upgrade still failed. Using direct schema creation as fallback..."
            
            # Final fallback: Direct schema creation
            python -c "
import os
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def create_schema_directly():
    database_url = os.getenv('DATABASE_URL', '')
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    engine = create_async_engine(database_url)
    
    async with engine.begin() as conn:
        # Create the comprehensive schema using the Base.metadata
        import sys
        sys.path.append('.')
        from app.core.database import Base
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        print('✅ Schema created directly from SQLAlchemy metadata!')
        
    await engine.dispose()

asyncio.run(create_schema_directly())
"
            
            # Let Alembic manage its own version table
            echo "🔄 Letting Alembic manage version state..."
            python -m alembic stamp head
        fi
    else
        echo "❌ Failed to stamp base revision"
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