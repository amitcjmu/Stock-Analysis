# Discovery Flow Debugging Patterns - 2025-09-18

## Insight 1: Database Column Existence Verification
**Problem**: Application expects columns that don't exist in database
**Symptoms**: `column assets.discovered_at does not exist`, transaction rollback cascade
**Debug Commands**:
```bash
# Check actual columns in table
docker exec migration_postgres psql -U postgres -d migration_db -c "\d migration.assets" | grep column_name

# Verify migration status
docker exec migration_backend alembic current

# Check column existence
docker exec migration_postgres psql -U postgres -d migration_db -c "SELECT column_name FROM information_schema.columns WHERE table_name='assets';"
```
**Solution**: Create retroactive migration adding missing columns

## Insight 2: Docker Override Files Silent Configuration Changes
**Problem**: PostgreSQL version mismatch despite correct main docker-compose.yml
**Detection Pattern**:
```bash
docker ps | grep postgres  # Shows pg16
cat docker-compose.yml     # Shows pg17
ls -la docker-compose*.yml # Reveals override file!
```
**Root Cause**: `docker-compose.override.yml` automatically loaded, overriding main config
**Fix**: Remove override file or ensure it matches main config

## Insight 3: Transaction Abort Cascade Debugging
**Problem**: `current transaction is aborted, commands ignored until end of transaction block`
**Diagnosis**: Initial SQL error causes all subsequent operations in transaction to fail
**Debug Strategy**:
1. Find first error in logs (usually missing column or FK violation)
2. Fix root cause (not symptoms)
3. Restart backend to clear connection pool
```bash
docker logs migration_backend | grep -A5 "ERROR"  # Find first error
docker restart migration_backend                    # Clear connection pool
```

## Insight 4: Flow Status Field Name Confusion
**Problem**: Different tables use different field names for status
**Mapping**:
- `discovery_flows.status` - Child flow operational status
- `crewai_flow_state_extensions.flow_status` - Master flow lifecycle
- `crewai_flow_state_extensions.flow_persistence_data->>'current_phase'` - Phase from JSON
**Query Pattern**:
```sql
SELECT
  df.status as child_status,
  cfse.flow_status as master_status,
  cfse.flow_persistence_data->>'current_phase' as current_phase
FROM discovery_flows df
JOIN crewai_flow_state_extensions cfse ON df.master_flow_id = cfse.flow_id;
```
