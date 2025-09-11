#!/bin/bash

# PostgreSQL 16 to 17 Migration Script
# This script handles the data migration from PostgreSQL 16 to PostgreSQL 17

set -e

echo "🔄 PostgreSQL 16 to 17 Migration Script"
echo "========================================"

# Configuration
COMPOSE_FILE="config/docker/docker-compose.yml"
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/migration_db_pg16_${TIMESTAMP}.sql"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo ""
echo "⚠️  WARNING: This script will migrate your PostgreSQL 16 data to PostgreSQL 17."
echo "⚠️  The existing data directory will be backed up and recreated."
echo ""
read -p "Do you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo "Migration cancelled."
    exit 1
fi

echo ""
echo "📦 Step 1: Starting PostgreSQL 16 for backup..."
# Temporarily revert to PostgreSQL 16 to backup data
sed -i.bak 's|pgvector/pgvector:pg17|pgvector/pgvector:pg16|g' "$COMPOSE_FILE"

# Start PostgreSQL 16
docker-compose -f "$COMPOSE_FILE" up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL 16 to be ready..."
sleep 5
until docker-compose -f "$COMPOSE_FILE" exec postgres pg_isready -U postgres 2>/dev/null; do
    echo -n "."
    sleep 2
done
echo " Ready!"

echo ""
echo "💾 Step 2: Backing up database..."
docker-compose -f "$COMPOSE_FILE" exec postgres pg_dumpall -U postgres > "$BACKUP_FILE"
echo "✅ Backup saved to: $BACKUP_FILE"

# Get the size of the backup
BACKUP_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
echo "   Backup size: $BACKUP_SIZE"

echo ""
echo "🛑 Step 3: Stopping PostgreSQL 16..."
docker-compose -f "$COMPOSE_FILE" down

echo ""
echo "🗑️  Step 4: Removing old PostgreSQL 16 data volume..."
docker volume rm migration_postgres_data 2>/dev/null || true
echo "✅ Old data volume removed"

echo ""
echo "🔄 Step 5: Switching to PostgreSQL 17..."
# Restore the PostgreSQL 17 configuration
mv "${COMPOSE_FILE}.bak" "$COMPOSE_FILE"

echo ""
echo "🚀 Step 6: Starting PostgreSQL 17..."
docker-compose -f "$COMPOSE_FILE" up -d postgres

# Wait for PostgreSQL 17 to be ready
echo "⏳ Waiting for PostgreSQL 17 to initialize..."
sleep 10
until docker-compose -f "$COMPOSE_FILE" exec postgres pg_isready -U postgres 2>/dev/null; do
    echo -n "."
    sleep 2
done
echo " Ready!"

echo ""
echo "📥 Step 7: Restoring database to PostgreSQL 17..."
docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U postgres < "$BACKUP_FILE"
echo "✅ Database restored successfully"

echo ""
echo "🔧 Step 8: Running Alembic migrations..."
docker-compose -f "$COMPOSE_FILE" up -d backend
sleep 5
docker-compose -f "$COMPOSE_FILE" exec backend alembic upgrade head
echo "✅ Migrations completed"

echo ""
echo "🎉 Step 9: Starting all services..."
docker-compose -f "$COMPOSE_FILE" up -d
echo "✅ All services started"

echo ""
echo "==============================================="
echo "✅ Migration completed successfully!"
echo "==============================================="
echo ""
echo "📝 Important information:"
echo "   - Backup saved at: $BACKUP_FILE"
echo "   - PostgreSQL version: 17"
echo "   - All services are running"
echo ""
echo "🔍 To verify the migration:"
echo "   docker-compose -f $COMPOSE_FILE exec postgres psql -U postgres -c 'SELECT version();'"
echo ""
echo "⚠️  If you need to rollback:"
echo "   1. Run: ./scripts/rollback-postgres-16.sh"
echo "   2. Or manually restore from: $BACKUP_FILE"
