# Critical PostgreSQL Version Issue - Docker Override Files

## Insight 1: Hidden Docker Compose Override Forcing Wrong PostgreSQL Version
**Problem**: Application failing with "database files incompatible with server" - PostgreSQL 17 data with PG16 container
**Root Cause**: `docker-compose.override.yml` automatically loaded by Docker, forcing `pgvector/pgvector:pg16`
**Detection**:
```bash
# Container shows wrong version despite correct main config
docker ps | grep postgres  # Shows pg16
cat docker-compose.yml      # Shows pg17
ls -la *.yml               # Reveals override file
```
**Fix**:
```bash
# Remove override and force correct version
rm docker-compose.override.yml
docker-compose down -v
docker rmi pgvector/pgvector:pg16
docker-compose up -d --force-recreate
```
**Prevention**: Always check for override files when versions mismatch

## Insight 2: ImportFieldMapping Missing Engagement ID
**Problem**: `type object 'ImportFieldMapping' has no attribute 'engagement_id'`
**Solution**: Add via migration
```python
op.add_column('import_field_mappings',
    Column('engagement_id', UUID,
           ForeignKey('engagements.id', ondelete='CASCADE'),
           nullable=True)
)
op.create_index('ix_import_field_mappings_engagement_id',
                'import_field_mappings', ['engagement_id'])
```
**Impact**: Critical for multi-tenant data isolation

## Insight 3: Transaction Abort Cascade Pattern
**Symptom**: `current transaction is aborted, commands ignored until end of transaction block`
**Cause**: Initial SQL error (missing column) aborts transaction, all subsequent operations fail
**Solution**: Fix root cause (missing columns), restart backend to clear connection pool
```bash
docker exec migration_backend alembic upgrade head
docker restart migration_backend
```
