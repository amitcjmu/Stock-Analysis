#!/bin/bash

# PostgreSQL 17 to 16 Rollback Script
# This script rolls back from PostgreSQL 17 to PostgreSQL 16

set -e

echo "🔄 PostgreSQL 17 to 16 Rollback Script"
echo "========================================"

# Configuration
COMPOSE_FILE="config/docker/docker-compose.yml"

echo ""
echo "⚠️  WARNING: This script will rollback PostgreSQL 17 to PostgreSQL 16."
echo "⚠️  Make sure you have a backup from PostgreSQL 16."
echo ""
read -p "Do you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo "Rollback cancelled."
    exit 1
fi

echo ""
echo "📋 Available backups:"
ls -lh backups/*pg16*.sql 2>/dev/null || echo "No PostgreSQL 16 backups found in ./backups/"
echo ""
read -p "Enter the backup file path to restore (or 'skip' to start fresh): " BACKUP_FILE

echo ""
echo "🛑 Step 1: Stopping all services..."
docker-compose -f "$COMPOSE_FILE" down

echo ""
echo "🗑️  Step 2: Removing PostgreSQL 17 data volume..."
docker volume rm migration_postgres_data 2>/dev/null || true
echo "✅ PostgreSQL 17 data volume removed"

echo ""
echo "🔄 Step 3: Switching back to PostgreSQL 16..."
sed -i.bak 's|pgvector/pgvector:pg17|pgvector/pgvector:pg16|g' "$COMPOSE_FILE"
echo "✅ docker-compose.yml updated to use PostgreSQL 16"

echo ""
echo "🚀 Step 4: Starting PostgreSQL 16..."
docker-compose -f "$COMPOSE_FILE" up -d postgres

# Wait for PostgreSQL 16 to be ready
echo "⏳ Waiting for PostgreSQL 16 to initialize..."
sleep 10
until docker-compose -f "$COMPOSE_FILE" exec postgres pg_isready -U postgres 2>/dev/null; do
    echo -n "."
    sleep 2
done
echo " Ready!"

if [[ "$BACKUP_FILE" != "skip" ]] && [[ -f "$BACKUP_FILE" ]]; then
    echo ""
    echo "📥 Step 5: Restoring database from backup..."
    docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U postgres < "$BACKUP_FILE"
    echo "✅ Database restored from: $BACKUP_FILE"
else
    echo ""
    echo "⚠️  Step 5: No backup restore - starting with fresh database"
fi

echo ""
echo "🔧 Step 6: Running Alembic migrations..."
docker-compose -f "$COMPOSE_FILE" up -d backend
sleep 5
docker-compose -f "$COMPOSE_FILE" exec backend alembic upgrade head
echo "✅ Migrations completed"

echo ""
echo "🎉 Step 7: Starting all services..."
docker-compose -f "$COMPOSE_FILE" up -d
echo "✅ All services started"

echo ""
echo "==============================================="
echo "✅ Rollback completed successfully!"
echo "==============================================="
echo ""
echo "📝 Current status:"
echo "   - PostgreSQL version: 16"
echo "   - All services are running"
echo ""
echo "🔍 To verify the rollback:"
echo "   docker-compose -f $COMPOSE_FILE exec postgres psql -U postgres -c 'SELECT version();'"
