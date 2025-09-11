# PostgreSQL 17 Security Upgrade Guide

## Overview
This document outlines the upgrade from PostgreSQL 16/15 to PostgreSQL 17 to address critical security vulnerabilities.

## Security Vulnerabilities Addressed

### CVE-2025-8715 (High - CVSS 8.8)
- **Issue**: Improper neutralization of newlines in pg_dump allows restore-time code injection and SQL injection
- **Impact**: Allows malicious actors to execute arbitrary code during database restore operations

### CVE-2025-8714 (High - CVSS 8.8)
- **Issue**: Untrusted data inclusion in pg_dump allows malicious superuser to inject code during restore
- **Impact**: Compromised database backups could execute malicious code when restored

### CVE-2025-8713 (Low - CVSS 3.1)
- **Issue**: PostgreSQL optimizer statistics leak sampled data bypassing ACLs and row security policies
- **Impact**: Potential data exposure through optimizer statistics

## Compatibility Verification

### ✅ Verified Compatible Dependencies
- **SQLAlchemy**: Full PostgreSQL 17 support confirmed
- **psycopg 3.2.9**: Compatible with PostgreSQL 17
- **psycopg-binary 3.2.9**: Compatible with PostgreSQL 17
- **asyncpg 0.30.0**: Full PostgreSQL 17 support
- **pgvector 0.4.1**: Fully compatible (consider upgrading to 0.8.0 for enhanced features)
- **Alembic 1.16.3**: Works via SQLAlchemy

## Migration Steps

### 1. Pre-Upgrade Checklist
- [ ] Backup all databases using pg_dump
- [ ] Test backups in a staging environment
- [ ] Review application logs for any PostgreSQL-specific warnings
- [ ] Document current PostgreSQL configuration settings

### 2. Docker Configuration Updates
All Docker Compose files have been updated:
- `docker-compose.prod.yml`: postgres:16-alpine → postgres:17-alpine
- `docker-compose.secure.yml`: postgres:16-bookworm → postgres:17-bookworm
- `docker-compose.staging.yml`: postgres:16-alpine → postgres:17-alpine
- `docker-compose.observability.yml`: postgres:15-alpine → postgres:17-alpine

### 3. Database Migration Process

#### ⚠️ IMPORTANT: Data Directory Incompatibility
PostgreSQL 17 cannot directly use a PostgreSQL 16 data directory. You must perform a proper data migration.

#### Automated Migration (Recommended):
```bash
# Navigate to project root directory
cd /path/to/migrate-ui-orchestrator

# Run the automated migration script
./scripts/migrate-postgres-17.sh

# This script will:
# 1. Backup your PostgreSQL 16 data
# 2. Remove the old data directory
# 3. Initialize a new PostgreSQL 17 data directory
# 4. Restore your data to PostgreSQL 17
# 5. Run Alembic migrations
# 6. Start all services
```

#### Manual Migration Steps:
```bash
# Navigate to project root directory
cd /path/to/migrate-ui-orchestrator

# 1. First, ensure PostgreSQL 16 is running to backup data
# Temporarily revert docker-compose.yml to use pg16 if already changed
sed -i.bak 's|pgvector/pgvector:pg17|pgvector/pgvector:pg16|g' config/docker/docker-compose.yml

# 2. Start PostgreSQL 16 and backup ALL data
docker-compose -f config/docker/docker-compose.yml up -d postgres
sleep 5
docker-compose -f config/docker/docker-compose.yml exec postgres pg_dumpall -U postgres > backup_pg16_$(date +%Y%m%d_%H%M%S).sql

# 3. Stop all containers
docker-compose -f config/docker/docker-compose.yml down

# 4. Remove the PostgreSQL 16 data volume (CRITICAL STEP)
docker volume rm migration_postgres_data

# 5. Restore docker-compose.yml to use PostgreSQL 17
mv config/docker/docker-compose.yml.bak config/docker/docker-compose.yml
# Or manually ensure it uses: pgvector/pgvector:pg17

# 6. Pull new PostgreSQL 17 image
docker pull pgvector/pgvector:pg17

# 7. Start PostgreSQL 17 (will create new data directory)
docker-compose -f config/docker/docker-compose.yml up -d postgres

# 8. Wait for PostgreSQL 17 to initialize (important!)
sleep 10
docker-compose -f config/docker/docker-compose.yml exec postgres pg_isready -U postgres

# 9. Restore data to PostgreSQL 17
docker-compose -f config/docker/docker-compose.yml exec -T postgres psql -U postgres < backup_pg16_*.sql

# 10. Start backend and run migrations
docker-compose -f config/docker/docker-compose.yml up -d backend
sleep 5
docker-compose -f config/docker/docker-compose.yml exec backend alembic upgrade head

# 11. Start all services
docker-compose -f config/docker/docker-compose.yml up -d

# 12. Verify PostgreSQL version
docker-compose -f config/docker/docker-compose.yml exec postgres psql -U postgres -c "SELECT version();"
```

#### For Production/Staging Environments:
```bash
# Use the appropriate compose file for your environment
# Production:
docker-compose -f config/docker/docker-compose.prod.yml [commands]

# Staging:
docker-compose -f config/docker/docker-compose.staging.yml [commands]

# Secure environment:
docker-compose -f config/docker/docker-compose.secure.yml [commands]
```

#### For Cloud Deployments (Railway/AWS):
- Railway will automatically use the new PostgreSQL version on next deployment
- AWS RDS users should upgrade to PostgreSQL 17.4 or later

### 4. Post-Upgrade Validation
- [ ] Verify all Alembic migrations succeed
- [ ] Test pgvector functionality (vector similarity searches)
- [ ] Confirm application can connect and query successfully
- [ ] Run integration tests
- [ ] Monitor performance metrics for any anomalies

## Optional Enhancements

### Upgrade pgvector to 0.8.0
```sql
-- After PostgreSQL 17 upgrade
ALTER EXTENSION pgvector UPDATE TO '0.8.0';
```

Benefits:
- Enhanced filtering performance
- Iterative scanning features
- Better query planner integration

### PostgreSQL 17 Performance Features
- Improved parallel query execution
- Better JSON/JSONB performance
- Enhanced partitioning capabilities
- Reduced memory usage for vacuum operations

## Rollback Plan

If issues occur:
```bash
# 1. Stop the application
docker-compose -f config/docker/docker-compose.yml down

# 2. Restore PostgreSQL 16 image in docker-compose.yml
# Edit config/docker/docker-compose.yml:
# Change: image: pgvector/pgvector:pg17
# To:     image: pgvector/pgvector:pg16

# 3. Start PostgreSQL 16
docker-compose -f config/docker/docker-compose.yml up -d postgres

# 4. Restore database from backup
docker-compose -f config/docker/docker-compose.yml exec -T postgres psql -U postgres -d migration_db < backup_YYYYMMDD_HHMMSS.sql

# 5. Restart application
docker-compose -f config/docker/docker-compose.yml up -d
```

## Support Timeline
- PostgreSQL 17: Supported until November 2029
- PostgreSQL 16: Supported until November 2028
- PostgreSQL 15: Supported until November 2027

## References
- [PostgreSQL 17 Release Notes](https://www.postgresql.org/docs/17/release-17.html)
- [pgvector PostgreSQL 17 Support](https://github.com/pgvector/pgvector)
- [CVE-2025-8715 Details](https://nvd.nist.gov/vuln/detail/CVE-2025-8715)
- [CVE-2025-8714 Details](https://nvd.nist.gov/vuln/detail/CVE-2025-8714)
- [CVE-2025-8713 Details](https://nvd.nist.gov/vuln/detail/CVE-2025-8713)