#!/bin/bash

# AI Modernize Migration Platform - Database Restore Script
# Restore database from backup created by backup_database.sh

set -e

# Configuration
CONTAINER_NAME="migration_postgres"
DB_NAME="migration_db"
DB_USER="postgres"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 AI Modernize Migration Platform - Database Restore${NC}"
echo -e "${BLUE}=================================================${NC}"

# Check if backup file is provided
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Error: No backup file specified${NC}"
    echo -e "${YELLOW}Usage: $0 <backup_file.tar.gz>${NC}"
    echo -e "${YELLOW}Example: $0 ./backups/migration_db_backup_20250127_143022.tar.gz${NC}"
    echo ""
    echo -e "${BLUE}Available backups:${NC}"
    if [ -d "./backups" ]; then
        ls -la ./backups/migration_db_backup_*.tar.gz 2>/dev/null || echo -e "${YELLOW}No backup files found${NC}"
    else
        echo -e "${YELLOW}No backups directory found${NC}"
    fi
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Error: Backup file '$BACKUP_FILE' not found${NC}"
    exit 1
fi

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}❌ Error: Container '$CONTAINER_NAME' is not running${NC}"
    echo -e "${YELLOW}💡 Start the container with: docker-compose up -d${NC}"
    exit 1
fi

echo -e "${GREEN}📁 Backup file: $BACKUP_FILE${NC}"
echo -e "${GREEN}📏 Backup size: $(du -h "$BACKUP_FILE" | cut -f1)${NC}"

# Create temporary directory for extraction
TEMP_DIR=$(mktemp -d)
echo -e "${BLUE}📦 Extracting backup to temporary directory...${NC}"

# Extract backup
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to extract backup file${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Find the SQL backup file
SQL_BACKUP=$(find "$TEMP_DIR" -name "migration_db_backup_*.sql" | head -1)
if [ -z "$SQL_BACKUP" ]; then
    echo -e "${RED}❌ No SQL backup file found in archive${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo -e "${GREEN}✅ Backup extracted successfully${NC}"

# Show metadata if available
METADATA_FILE=$(find "$TEMP_DIR" -name "backup_metadata_*.json" | head -1)
if [ -f "$METADATA_FILE" ]; then
    echo -e "\n${BLUE}📋 Backup Metadata${NC}"
    echo -e "${BLUE}=================${NC}"
    if command -v jq &> /dev/null; then
        jq . "$METADATA_FILE"
    else
        cat "$METADATA_FILE"
    fi
fi

# Confirmation prompt
echo -e "\n${YELLOW}⚠️  WARNING: This will completely replace the current database!${NC}"
echo -e "${YELLOW}All existing data will be lost.${NC}"
echo -e "\n${BLUE}Current database information:${NC}"
CURRENT_SIZE=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" | xargs)
CURRENT_TABLES=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
echo -e "${GREEN}Current size: $CURRENT_SIZE${NC}"
echo -e "${GREEN}Current tables: $CURRENT_TABLES${NC}"

echo -e "\n${YELLOW}Do you want to continue? (yes/no)${NC}"
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}❌ Restore cancelled${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo -e "\n${BLUE}🚀 Starting database restore...${NC}"

# 1. Create a pre-restore backup
echo -e "${YELLOW}Creating pre-restore backup...${NC}"
PRE_RESTORE_BACKUP="./backups/pre_restore_backup_$(date +"%Y%m%d_%H%M%S").sql"
mkdir -p "./backups"
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" > "$PRE_RESTORE_BACKUP"
echo -e "${GREEN}✅ Pre-restore backup created: $PRE_RESTORE_BACKUP${NC}"

# 2. Drop existing database connections
echo -e "${YELLOW}Terminating existing database connections...${NC}"
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();"

# 3. Drop and recreate database
echo -e "${YELLOW}Dropping and recreating database...${NC}"
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;"

# 4. Restore from backup
echo -e "${YELLOW}Restoring database from backup...${NC}"
docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" < "$SQL_BACKUP"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database restored successfully${NC}"
else
    echo -e "${RED}❌ Failed to restore database${NC}"
    echo -e "${YELLOW}💡 You can restore the pre-restore backup: $PRE_RESTORE_BACKUP${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# 5. Verify restore
echo -e "\n${BLUE}🔍 Verifying restore...${NC}"
RESTORED_SIZE=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" | xargs)
RESTORED_TABLES=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)

echo -e "${GREEN}✅ Restore verification complete${NC}"
echo -e "${GREEN}Restored size: $RESTORED_SIZE${NC}"
echo -e "${GREEN}Restored tables: $RESTORED_TABLES${NC}"

# 6. Test database connectivity
echo -e "${YELLOW}Testing database connectivity...${NC}"
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 'Database connection successful' as status;" > /dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database connectivity test passed${NC}"
else
    echo -e "${RED}❌ Database connectivity test failed${NC}"
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo -e "\n${BLUE}📋 Restore Summary${NC}"
echo -e "${BLUE}=================${NC}"
echo -e "${GREEN}✅ Database restore completed successfully${NC}"
echo -e "${GREEN}📁 Restored from: $BACKUP_FILE${NC}"
echo -e "${GREEN}📏 Restored size: $RESTORED_SIZE${NC}"
echo -e "${GREEN}🗂️  Restored tables: $RESTORED_TABLES${NC}"
echo -e "${GREEN}🛡️  Pre-restore backup: $PRE_RESTORE_BACKUP${NC}"

echo -e "\n${GREEN}🎉 Database restore completed successfully!${NC}"
echo -e "${BLUE}💡 You may need to restart your application containers${NC}"
echo -e "${BLUE}💡 Run: docker-compose restart backend frontend${NC}"
