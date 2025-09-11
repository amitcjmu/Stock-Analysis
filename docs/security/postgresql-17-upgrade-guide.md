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

#### For Docker Deployments:
```bash
# 1. Stop the application
docker-compose down

# 2. Backup existing data
docker-compose run --rm postgres pg_dump -h postgres -U $DB_USER -d $DB_NAME > backup_$(date +%Y%m%d).sql

# 3. Pull new PostgreSQL 17 image
docker pull postgres:17-alpine

# 4. Start with new PostgreSQL version
docker-compose up -d postgres

# 5. Run migrations
docker-compose run --rm backend alembic upgrade head

# 6. Verify application functionality
docker-compose up -d
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
1. Stop the application
2. Restore PostgreSQL 16 Docker image in compose files
3. Restore database from backup
4. Start application with PostgreSQL 16

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