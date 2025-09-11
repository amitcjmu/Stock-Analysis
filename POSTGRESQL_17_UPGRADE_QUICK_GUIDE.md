# Quick PostgreSQL 17 Upgrade Guide

## Simple 5-Step Process

```bash
# 1. Backup PostgreSQL 16 data (if not already done)
docker-compose -f config/docker/docker-compose.yml exec postgres pg_dumpall -U postgres > backup_pg16.sql

# 2. Stop all containers
docker-compose -f config/docker/docker-compose.yml down

# 3. Remove old PostgreSQL 16 data volume
docker volume rm migration_postgres_data

# 4. Start PostgreSQL 17 (it will auto-create new data directory)
docker-compose -f config/docker/docker-compose.yml up -d postgres
sleep 10  # Wait for initialization

# 5. Restore your backup
docker-compose -f config/docker/docker-compose.yml exec -T postgres psql -U postgres < backup_pg16.sql

# Done! Start all services
docker-compose -f config/docker/docker-compose.yml up -d
```

## Why This Works

- PostgreSQL 17 cannot directly read PostgreSQL 16 data directories
- We use `pg_dumpall` to export data in a portable SQL format
- The SQL backup can be restored to any PostgreSQL version
- This is the standard, safest way to upgrade PostgreSQL major versions

## Verify Success

```bash
# Check PostgreSQL version (should show 17.x)
docker-compose -f config/docker/docker-compose.yml exec postgres psql -U postgres -c "SELECT version();"

# Check all services are running
docker-compose -f config/docker/docker-compose.yml ps
```

## If You Need to Rollback

```bash
# 1. Change docker-compose.yml back to pg16
sed -i 's|pgvector/pgvector:pg17|pgvector/pgvector:pg16|g' config/docker/docker-compose.yml

# 2. Stop containers
docker-compose -f config/docker/docker-compose.yml down

# 3. Remove PostgreSQL 17 volume
docker volume rm migration_postgres_data

# 4. Start PostgreSQL 16
docker-compose -f config/docker/docker-compose.yml up -d postgres

# 5. Restore your pg16 backup
docker-compose -f config/docker/docker-compose.yml exec -T postgres psql -U postgres < backup_pg16.sql

# 6. Start all services
docker-compose -f config/docker/docker-compose.yml up -d
```
