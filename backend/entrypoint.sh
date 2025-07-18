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

# Run database migrations
echo "🔄 Running database migrations..."
if python -m alembic upgrade head; then
    echo "✅ Migrations completed successfully!"
else
    echo "❌ Migration failed, but continuing..."
fi

# Start the application directly
echo "🚀 Starting application..."
exec python start.py