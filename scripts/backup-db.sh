#!/bin/bash
# backup-db.sh - Backup PostgreSQL database

# Configuration
BACKUP_DIR="./backups"
DB_CONTAINER="migration_postgres"
DB_NAME="migration_db"
DB_USER="postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "🔄 Starting database backup..."

# Method 1: SQL dump (recommended for portability)
docker-compose exec -T postgres pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/backup_${TIMESTAMP}.sql.gz"

# Method 2: Full data directory backup (faster for large databases)
# docker run --rm -v migrate-ui-orchestrator_postgres_data:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine \
#   tar czf "/backup/postgres_data_${TIMESTAMP}.tar.gz" -C /data .

echo "✅ Backup completed: $BACKUP_DIR/backup_${TIMESTAMP}.sql.gz"

# Keep only last 7 backups
echo "🧹 Cleaning old backups..."
ls -t "$BACKUP_DIR"/backup_*.sql.gz | tail -n +8 | xargs -r rm

echo "📊 Current backups:"
ls -lh "$BACKUP_DIR"/backup_*.sql.gz