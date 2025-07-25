#!/bin/bash
# restore-db.sh - Restore PostgreSQL database from backup

# Configuration
BACKUP_DIR="./backups"
DB_CONTAINER="migration_postgres"
DB_NAME="migration_db"
DB_USER="postgres"

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "❌ Usage: $0 <backup_file>"
    echo "Available backups:"
    ls -lh "$BACKUP_DIR"/backup_*.sql.gz
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will replace all current data in the database!"
read -p "Are you sure you want to restore from $BACKUP_FILE? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Restore cancelled"
    exit 1
fi

echo "🔄 Starting database restore..."

# Drop and recreate database
docker-compose exec -T postgres psql -U "$DB_USER" <<EOF
DROP DATABASE IF EXISTS ${DB_NAME};
CREATE DATABASE ${DB_NAME};
EOF

# Restore from backup
gunzip -c "$BACKUP_FILE" | docker-compose exec -T postgres psql -U "$DB_USER" "$DB_NAME"

echo "✅ Database restored from: $BACKUP_FILE"
echo "🔄 Running migrations to ensure schema is up to date..."

# Run migrations
docker-compose exec backend alembic upgrade head

echo "✅ Restore completed successfully!"
