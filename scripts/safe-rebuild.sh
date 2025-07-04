#!/bin/bash
# safe-rebuild.sh - Safely rebuild Docker containers without losing data

echo "🔄 Safe Docker rebuild starting..."
echo "📊 This will preserve your database data"

# Create backup first (optional but recommended)
read -p "Do you want to create a backup first? (recommended) (y/n): " backup_choice
if [ "$backup_choice" = "y" ]; then
    ./scripts/backup-db.sh
fi

# Stop containers (but keep volumes)
echo "🛑 Stopping containers..."
docker-compose down  # NO -v flag!

# Rebuild containers
echo "🔨 Building containers..."
docker-compose build --no-cache

# Start containers
echo "🚀 Starting containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check database connection
echo "🔍 Checking database connection..."
docker-compose exec backend python -c "
from app.core.database import db_manager
import asyncio
asyncio.run(db_manager.health_check())
print('✅ Database connection successful')
"

echo "✅ Safe rebuild completed!"
echo "📊 Your data has been preserved"

# Show running containers
echo "🐳 Running containers:"
docker-compose ps