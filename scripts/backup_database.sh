#!/bin/bash

# AI Force Migration Platform - Database Backup Script
# Run this before any schema updates or major changes

set -e

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
CONTAINER_NAME="migration_postgres"
DB_NAME="migration_db"
DB_USER="postgres"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗄️  AI Force Migration Platform - Database Backup${NC}"
echo -e "${BLUE}=================================================${NC}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}❌ Error: Container '$CONTAINER_NAME' is not running${NC}"
    echo -e "${YELLOW}💡 Start the container with: docker-compose up -d${NC}"
    exit 1
fi

echo -e "${BLUE}📊 Gathering database information...${NC}"

# Get database size and table count
DB_SIZE=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" | xargs)
TABLE_COUNT=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)

echo -e "${GREEN}Database Size: $DB_SIZE${NC}"
echo -e "${GREEN}Table Count: $TABLE_COUNT${NC}"

# Create backup filename
BACKUP_FILE="$BACKUP_DIR/migration_db_backup_$TIMESTAMP.sql"
SCHEMA_FILE="$BACKUP_DIR/migration_db_schema_$TIMESTAMP.sql"
DATA_FILE="$BACKUP_DIR/migration_db_data_$TIMESTAMP.sql"

echo -e "\n${BLUE}🚀 Creating backups...${NC}"

# 1. Full database backup
echo -e "${YELLOW}Creating full database backup...${NC}"
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" --verbose > "$BACKUP_FILE"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Full backup created: $BACKUP_FILE${NC}"
else
    echo -e "${RED}❌ Failed to create full backup${NC}"
    exit 1
fi

# 2. Schema-only backup
echo -e "${YELLOW}Creating schema-only backup...${NC}"
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" --schema-only --verbose > "$SCHEMA_FILE"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Schema backup created: $SCHEMA_FILE${NC}"
else
    echo -e "${RED}❌ Failed to create schema backup${NC}"
fi

# 3. Data-only backup
echo -e "${YELLOW}Creating data-only backup...${NC}"
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" --data-only --verbose > "$DATA_FILE"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Data backup created: $DATA_FILE${NC}"
else
    echo -e "${RED}❌ Failed to create data backup${NC}"
fi

# 4. Create backup metadata
METADATA_FILE="$BACKUP_DIR/backup_metadata_$TIMESTAMP.json"
cat > "$METADATA_FILE" << EOF
{
  "timestamp": "$TIMESTAMP",
  "database_name": "$DB_NAME",
  "database_size": "$DB_SIZE",
  "table_count": $TABLE_COUNT,
  "container_name": "$CONTAINER_NAME",
  "backup_files": {
    "full_backup": "$BACKUP_FILE",
    "schema_backup": "$SCHEMA_FILE",
    "data_backup": "$DATA_FILE"
  },
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "git_branch": "$(git branch --show-current 2>/dev/null || echo 'unknown')"
}
EOF

echo -e "${GREEN}✅ Backup metadata created: $METADATA_FILE${NC}"

# 5. Compress backups
echo -e "\n${YELLOW}📦 Compressing backups...${NC}"
tar -czf "$BACKUP_DIR/migration_db_backup_$TIMESTAMP.tar.gz" -C "$BACKUP_DIR" \
    "migration_db_backup_$TIMESTAMP.sql" \
    "migration_db_schema_$TIMESTAMP.sql" \
    "migration_db_data_$TIMESTAMP.sql" \
    "backup_metadata_$TIMESTAMP.json"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Compressed backup created: migration_db_backup_$TIMESTAMP.tar.gz${NC}"
    
    # Remove individual files to save space
    rm "$BACKUP_FILE" "$SCHEMA_FILE" "$DATA_FILE" "$METADATA_FILE"
    echo -e "${GREEN}✅ Cleaned up individual backup files${NC}"
else
    echo -e "${RED}❌ Failed to compress backup${NC}"
fi

# 6. Show backup summary
BACKUP_SIZE=$(du -h "$BACKUP_DIR/migration_db_backup_$TIMESTAMP.tar.gz" | cut -f1)
echo -e "\n${BLUE}📋 Backup Summary${NC}"
echo -e "${BLUE}=================${NC}"
echo -e "${GREEN}✅ Backup completed successfully${NC}"
echo -e "${GREEN}📁 Backup file: migration_db_backup_$TIMESTAMP.tar.gz${NC}"
echo -e "${GREEN}📏 Backup size: $BACKUP_SIZE${NC}"
echo -e "${GREEN}📊 Database size: $DB_SIZE${NC}"
echo -e "${GREEN}🗂️  Tables backed up: $TABLE_COUNT${NC}"

# 7. Cleanup old backups (keep last 10)
echo -e "\n${YELLOW}🧹 Cleaning up old backups (keeping last 10)...${NC}"
cd "$BACKUP_DIR"
ls -t migration_db_backup_*.tar.gz | tail -n +11 | xargs -r rm
REMAINING_BACKUPS=$(ls migration_db_backup_*.tar.gz 2>/dev/null | wc -l)
echo -e "${GREEN}✅ Cleanup complete. $REMAINING_BACKUPS backup(s) remaining${NC}"

echo -e "\n${GREEN}🎉 Database backup completed successfully!${NC}"
echo -e "${BLUE}💡 To restore: ./scripts/restore_database.sh migration_db_backup_$TIMESTAMP.tar.gz${NC}" 