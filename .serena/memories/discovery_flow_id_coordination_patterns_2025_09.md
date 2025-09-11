# Discovery Flow ID Coordination Patterns - September 2025

## Critical Understanding: Three Types of IDs

### 1. master_flow_id (Primary for APIs)
- Stored in: crewai_flow_state_extensions.flow_id
- Used by: MasterFlowOrchestrator, all API endpoints
- Frontend should ALWAYS use this for API calls
- Example: cf038071-1462-4d69-b332-0b5b88a43053

### 2. discovery_flow_id (Internal)
- Stored in: discovery_flows.id
- Links to master via: discovery_flows.master_flow_id
- NEVER expose to frontend or APIs
- Internal implementation detail only

### 3. data_import_id (Data Reference)
- Stored in: data_imports.id
- Referenced by: discovery_flows.data_import_id
- Used to find raw_import_records
- Example: af3c2979-3fa7-4f40-83dd-ee7cd89a9b94

## Common ID Confusion Issues

### Issue 1: Frontend sends flow_id, backend needs data_import_id
**Solution**: Backend should accept flow_id and lookup data_import_id
```python
# Lookup chain
flow_id → discovery_flows.master_flow_id → discovery_flows.data_import_id
```

### Issue 2: Multiple imports create confusing IDs
**Pattern**: Latest import might be "direct_raw_data" type instead of "cmdb"
**Solution**: When flow_id provided, use it to find specific import, don't just get latest

### Issue 3: Flow and Import IDs sometimes match (but shouldn't be assumed)
**Wrong**: Using flow_id as data_import_id directly
**Right**: Always lookup via discovery_flows table

## Correct API Pattern
```python
# Accept flow_id from frontend
flow_id: Optional[str] = Query(None)

# Find associated data import
if flow_id:
    # Find discovery flow
    discovery = await db.execute(
        select(DiscoveryFlow).where(
            DiscoveryFlow.master_flow_id == flow_id
        )
    )
    discovery_flow = discovery.scalar_one_or_none()

    # Get data_import_id
    if discovery_flow and discovery_flow.data_import_id:
        data_import = await db.execute(
            select(DataImport).where(
                DataImport.id == discovery_flow.data_import_id
            )
        )
```

## Database Relationships
```sql
-- Master flow is source of truth
crewai_flow_state_extensions.flow_id (master_flow_id)
    ↓
-- Discovery flow links to master
discovery_flows.master_flow_id → crewai_flow_state_extensions.flow_id
    ↓
-- Discovery flow has data import
discovery_flows.data_import_id → data_imports.id
    ↓
-- Data import has raw records
raw_import_records.data_import_id → data_imports.id
```

## Key Principle
Frontend knows master_flow_id, backend needs data_import_id. The discovery_flows table is the bridge between them. Never assume IDs match - always lookup through proper relationships.
