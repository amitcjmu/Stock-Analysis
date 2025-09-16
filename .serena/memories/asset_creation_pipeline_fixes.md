# Asset Creation Pipeline Fixes - Discovery Flow

## Issue 1: Missing data_import_id in Asset Inventory Phase
**Problem**: Asset inventory phase received 0 records despite successful data cleansing (13 records, 89% quality)
**Root Cause**: `data_import_id` not passed from data_cleansing to asset_inventory phase in `phase_input`

**Solution**: Modified flow_state_helpers.py to retrieve data_import_id from discovery flow record
**Code**:
```python
# In load_flow_state_for_phase() - lines 53-71
if phase_name == "asset_inventory":
    from sqlalchemy import select
    from app.models.discovery_flow import DiscoveryFlow

    discovery_result = await db.execute(
        select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
    )
    discovery_flow = discovery_result.scalar_one_or_none()

    if discovery_flow:
        data_import_id = discovery_flow.data_import_id
        master_flow_id = discovery_flow.master_flow_id
        logger.info(f"📦 Found data_import_id={data_import_id} for asset_inventory phase")

# In prepare_phase_input() - lines 119-125
if data_import_id:
    phase_input["data_import_id"] = data_import_id
if master_flow_id:
    phase_input["master_flow_id"] = master_flow_id
```

**Files Modified**:
- `/backend/app/services/discovery/flow_state_helpers.py`

## Issue 2: UUID Validation Errors - 'ADMIN' as client_account_id
**Problem**: SQL queries failed with "invalid UUID 'ADMIN': length must be between 32..36 characters"
**Root Cause**: RequestContext was receiving 'ADMIN' as client_account_id instead of valid UUID

**Symptoms in Logs**:
```
RequestContext(client=ADMIN, engagement=demo, user=None, flow=None)
app.middleware.tenant_context - WARNING - Invalid client_account_id in header: ADMIN
```

**Solution**: System now properly uses UUID values (11111111-1111-1111-1111-111111111111)
**Status**: Auto-resolved in current deployment - no code changes needed

## Key Log Patterns for Debugging Asset Creation

**Success Indicators**:
- `📦 Found data_import_id=X for asset_inventory phase`
- `📦 Passing X records to asset_inventory phase` (X > 0)
- Asset count increases from baseline (47)

**Failure Indicators**:
- `📦 Passing 0 records to asset_inventory phase`
- `No data_import_id provided`
- UUID validation errors in SQL queries

## Testing Commands
```bash
# Monitor asset creation logs
docker logs migration_backend -f | grep -E "📦|asset"

# Check database for asset count
docker exec -it migration_postgres_dev psql -U postgres -d migration_db \
  -c "SELECT COUNT(*) FROM migration.assets WHERE client_account_id='11111111-1111-1111-1111-111111111111';"
```

**Usage**: Apply when asset inventory phase receives 0 records despite successful data cleansing
