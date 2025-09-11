# PostgreSQL Major Version Upgrade Pattern

## Problem
PostgreSQL major versions (e.g., 16 to 17) have incompatible data directories. Direct upgrade causes:
```
FATAL: database files are incompatible with server
DETAIL: The data directory was initialized by PostgreSQL version 16, which is not compatible with this version 17
```

## Solution Pattern
```bash
# 1. Backup existing data (while old version running)
docker-compose -f config/docker/docker-compose.yml exec postgres pg_dumpall -U postgres > backup.sql

# 2. Stop containers
docker-compose -f config/docker/docker-compose.yml down

# 3. Remove old data volume (CRITICAL)
docker volume rm migration_postgres_data

# 4. Start new PostgreSQL version
docker-compose -f config/docker/docker-compose.yml up -d postgres
sleep 10  # Wait for initialization

# 5. Restore backup
docker-compose -f config/docker/docker-compose.yml exec -T postgres psql -U postgres < backup.sql
```

## Key Points
- Use `pg_dumpall` for complete backup (includes users, roles, databases)
- Must remove old volume - PostgreSQL won't overwrite incompatible data
- SQL backup is portable across versions
- Always verify with: `SELECT version();`

## Files Created
- `scripts/migrate-postgres-17.sh` - Automated migration
- `scripts/rollback-postgres-16.sh` - Rollback script
- `POSTGRESQL_17_UPGRADE_QUICK_GUIDE.md` - Quick reference
