# Database Consolidation Deployment Guide

## Overview

This guide covers the deployment process for the database consolidation changes. The deployment involves schema changes, data migrations, and application updates.

## Pre-Deployment Checklist

### 1. Team Communication
- [ ] Notify development team of deployment schedule
- [ ] Schedule maintenance window (recommended: 2-4 hours)
- [ ] Prepare rollback communication plan

### 2. Backup Verification
- [ ] Verify automated backups are current
- [ ] Create manual backup before deployment
- [ ] Test backup restoration process (on staging)
- [ ] Document backup file locations

### 3. Environment Preparation
- [ ] Ensure staging environment matches production
- [ ] Verify database connection strings
- [ ] Check disk space for backups
- [ ] Confirm all team members have necessary access

### 4. Code Preparation
- [ ] All Day 1-5 changes merged to main branch
- [ ] Database migration files reviewed and tested
- [ ] Deployment scripts tested on staging
- [ ] Rollback scripts tested on staging

## Deployment Process

### Stage 1: Staging Deployment

1. **Run deployment on staging environment**
   ```bash
   cd backend/scripts
   ./deploy_db_consolidation.py --database-url $STAGING_DB_URL --dry-run
   ```

2. **Review dry run output**
   - Verify all steps would complete
   - Check for any warnings or issues

3. **Execute staging deployment**
   ```bash
   ./deploy_db_consolidation.py --database-url $STAGING_DB_URL
   ```

4. **Run validation tests**
   ```bash
   docker exec staging_backend python -m pytest tests/integration/test_db_consolidation_v3.py -v
   ```

5. **Perform manual testing**
   - Create new discovery flow
   - Upload test data
   - Verify field mappings work
   - Check multi-tenant isolation

### Stage 2: Production Deployment

1. **Final preparation**
   ```bash
   # Create fresh backup
   pg_dump $PROD_DB_URL -f backup_production_$(date +%Y%m%d_%H%M%S).sql
   
   # Verify backup
   ls -lh backup_production_*.sql
   ```

2. **Start deployment**
   ```bash
   # Dry run first
   ./deploy_db_consolidation.py --database-url $PROD_DB_URL --dry-run
   
   # Execute deployment
   ./deploy_db_consolidation.py --database-url $PROD_DB_URL
   ```

3. **Monitor deployment**
   - Watch deployment logs
   - Monitor application logs
   - Check database connections
   - Monitor error rates

4. **Post-deployment validation**
   - Run integration tests
   - Verify critical workflows
   - Check performance metrics
   - Monitor for errors

## Rollback Process

### When to Rollback

Rollback should be initiated if:
- Critical functionality is broken
- Data integrity issues are detected
- Performance degradation exceeds 50%
- Multiple users report blocking issues

### Rollback Steps

1. **Assess the situation**
   ```bash
   # Check current state
   docker logs migration_backend --tail 100
   ```

2. **Execute rollback**
   ```bash
   # Using backup file (recommended)
   ./rollback_db_consolidation.py \
     --database-url $PROD_DB_URL \
     --backup-file backup_pre_consolidation_20250101_120000.sql
   
   # Or using Alembic rollback
   ./rollback_db_consolidation.py --database-url $PROD_DB_URL
   ```

3. **Verify rollback**
   - Test critical functionality
   - Check database schema
   - Verify data integrity

## Post-Deployment Tasks

### Immediate (First Hour)
- [ ] Monitor error logs
- [ ] Check application performance
- [ ] Verify all services are running
- [ ] Test critical user workflows

### Short Term (First Day)
- [ ] Review performance metrics
- [ ] Check for any data inconsistencies
- [ ] Monitor user feedback channels
- [ ] Update documentation

### Long Term (First Week)
- [ ] Analyze performance improvements
- [ ] Document any issues encountered
- [ ] Plan for optimization if needed
- [ ] Remove deprecated code (after stability confirmed)

## Troubleshooting

### Common Issues

1. **Migration fails with "column already exists"**
   - The migration may have partially applied
   - Check current schema state
   - May need to manually adjust migration

2. **Application can't connect after migration**
   - Verify connection strings
   - Check for connection pool exhaustion
   - Restart application services

3. **Performance degradation**
   - Check for missing indexes
   - Analyze query plans
   - May need to run VACUUM ANALYZE

4. **Data appears missing**
   - Check multi-tenant context headers
   - Verify client_account_id values
   - Check for data in wrong tables

### Emergency Contacts

- Database Administrator: [Contact Info]
- DevOps Lead: [Contact Info]
- Platform Team Lead: [Contact Info]

## Monitoring

### Key Metrics to Watch

1. **Database Performance**
   - Query execution time
   - Connection pool usage
   - Lock contention
   - Disk I/O

2. **Application Performance**
   - API response times
   - Error rates
   - Memory usage
   - CPU utilization

3. **Business Metrics**
   - Discovery flow creation rate
   - Data import success rate
   - User activity levels

### Alerting Thresholds

- Error rate > 5% - WARNING
- Error rate > 10% - CRITICAL
- API response time > 2s (p95) - WARNING
- API response time > 5s (p95) - CRITICAL
- Database connections > 80% - WARNING
- Database connections > 95% - CRITICAL

## Success Criteria

The deployment is considered successful when:
- [ ] All integration tests pass
- [ ] No critical errors in logs
- [ ] Performance metrics are stable or improved
- [ ] Users can complete all workflows
- [ ] No data integrity issues reported

## Appendix

### Script Options

**deploy_db_consolidation.py**
- `--database-url`: Database connection string
- `--dry-run`: Show what would be done without executing
- `--skip-backup`: Skip backup step (not recommended)
- `--skip-tests`: Skip post-deployment tests

**rollback_db_consolidation.py**
- `--database-url`: Database connection string
- `--backup-file`: Path to backup file to restore
- `--dry-run`: Show what would be done without executing
- `--force`: Skip confirmation prompt

### Railway-Specific Deployment

For Railway deployment:

1. **Update environment variables**
   ```bash
   railway variables set ENABLE_DB_CONSOLIDATION=true
   ```

2. **Trigger deployment**
   ```bash
   railway up
   ```

3. **Monitor logs**
   ```bash
   railway logs -f
   ```

### Database Migration Commands

```bash
# Check current migration status
alembic current

# Generate new migration
alembic revision --autogenerate -m "Database consolidation"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

---

Last Updated: January 2025