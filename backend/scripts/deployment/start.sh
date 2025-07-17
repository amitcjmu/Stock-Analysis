#!/bin/bash
set -e

# AI Modernize Migration Platform - Railway Startup Script
# This script handles environment variable expansion for Railway deployment

echo "🚀 Starting AI Modernize Migration Platform API..."
echo "Environment: ${ENVIRONMENT:-production}"
echo "Port: ${PORT:-8000}"
echo "Debug: ${DEBUG:-false}"
echo "Database URL: ${DATABASE_URL:0:50}..." # Show first 50 chars for debugging

# Function to wait for database
wait_for_database() {
    echo "⏳ Waiting for database to be ready..."
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python -c "
import asyncio
import asyncpg
import os
import sys

async def check():
    try:
        # Get DATABASE_URL and convert from SQLAlchemy format to asyncpg format
        db_url = os.getenv('DATABASE_URL', '')
        
        # Handle different URL formats
        if 'postgresql+asyncpg://' in db_url:
            # Convert SQLAlchemy URL to asyncpg format
            asyncpg_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
        else:
            asyncpg_url = db_url
            
        conn = await asyncpg.connect(asyncpg_url)
        await conn.execute('SELECT 1')
        await conn.close()
        sys.exit(0)
    except Exception as e:
        print(f'Database not ready: {e}')
        sys.exit(1)

asyncio.run(check())
" 2>&1 | tail -n 1; then
            echo "✅ Database is ready!"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts: Database not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ Database did not become ready within timeout"
    exit 1
}

# Function to run database setup
run_database_setup() {
    echo "🔧 Running database setup..."
    
    # Run the consolidated railway setup script
    if python railway_setup.py; then
        echo "✅ Database setup completed successfully!"
        return 0
    else
        echo "❌ Railway setup failed! Check logs above for details."
        return 1
    fi
}

# Main setup process
echo "🏁 Starting Railway deployment setup..."

# Step 1: Wait for database
wait_for_database

# Step 2: Run database setup
if run_database_setup; then
    echo "🎉 Database setup completed successfully!"
else
    echo "💥 Database setup failed!"
    exit 1
fi


# Use Railway's PORT environment variable or default to 8000
PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT 