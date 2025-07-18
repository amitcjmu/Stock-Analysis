#!/bin/sh
# Railway Entrypoint Script - Ensures migrations run before starting the app

set -e

echo "🚀 Railway Entrypoint Starting..."
echo "📅 Date: $(date)"
echo "📁 Working Directory: $(pwd)"
echo "🗄️ DATABASE_URL: ${DATABASE_URL:0:50}..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if python -c "
import os
import psycopg2
from urllib.parse import urlparse

db_url = os.getenv('DATABASE_URL', '')
if 'postgresql+asyncpg://' in db_url:
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')

try:
    conn = psycopg2.connect(db_url)
    conn.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
        echo "✅ Database is ready!"
        break
    fi
    
    echo "   Attempt $attempt/$max_attempts: Database not ready yet..."
    sleep 2
    attempt=$((attempt + 1))
done

# Run migration fix first
echo "🔄 Running Railway migration fix..."
if python railway_migration_fix.py; then
    echo "✅ Migration fix completed successfully!"
else
    echo "❌ Migration fix failed, trying standard migrations..."
    
    # Fallback to standard migrations
    echo "🔄 Running standard database migrations..."
    if python -m alembic upgrade head; then
        echo "✅ Standard migrations completed successfully!"
    else
        echo "❌ Standard migration also failed, but continuing..."
    fi
fi

# Start the application directly
echo "🚀 Starting application..."
exec python start.py