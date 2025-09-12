# Discovery Flow Data Display Issues - September 2025

## Problem Pattern
Frontend shows "No Data Imported Yet" despite data existing in database. This affects:
1. Imported Data tab in Attribute Mapping page
2. Critical Attributes tab showing "No Critical Attributes found"
3. Assets not appearing in Inventory after data cleansing

## Root Causes Identified
1. **ID Type Mismatch**: Frontend uses flow_id but backend needs data_import_id
2. **Discovery Flow Linkage**: Discovery flow has both IDs but API endpoints inconsistent
3. **Data Structure Issues**: ImportStorageHandler.get_import_data() returning wrong structure

## Database Verification Queries
```sql
-- Check if raw data exists
SELECT COUNT(*) FROM migration.raw_import_records WHERE data_import_id = ?;

-- Find correct import ID from flow
SELECT id, flow_id, data_import_id FROM migration.discovery_flows WHERE flow_id = ?;

-- Verify data import record
SELECT id, import_type, master_flow_id FROM migration.data_imports WHERE id = ?;
```

## Solution Pattern

### Backend Fixes Required
1. **Add flow_id parameter support to endpoints**:
```python
@router.get("/critical-attributes-status")
async def get_critical_attributes_status(
    request: Request,
    flow_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    # If flow_id provided, lookup associated data_import
    if flow_id:
        # Try finding via discovery flow
        discovery_query = select(DiscoveryFlow).where(
            (DiscoveryFlow.flow_id == flow_id) |
            (DiscoveryFlow.master_flow_id == flow_id)
        )
        discovery_result = await db.execute(discovery_query)
        discovery_flow = discovery_result.scalar_one_or_none()

        if discovery_flow and discovery_flow.data_import_id:
            # Use the data_import_id to find the import
            import_query = select(DataImport).where(
                DataImport.id == discovery_flow.data_import_id
            )
```

2. **Fix data extraction in ImportStorageHandler**:
```python
# WRONG - Returns entire dict as data
return {
    "success": True,
    "data": import_data,  # This is wrong!
    "import_metadata": import_data.get("metadata")
}

# CORRECT - Extract data array
return {
    "success": True,
    "data": import_data.get("data", []),  # Extract the array
    "import_metadata": import_data.get("import_metadata")
}
```

### Frontend Investigation Needed
- Check components in `/src/pages/discovery/AttributeMapping/`
- Verify API calls use correct endpoint and parameters
- Ensure snake_case field names are used (not camelCase)

## Files That Need Modification
- `backend/app/api/v1/endpoints/data_import/critical_attributes.py` - Add flow_id parameter
- `backend/app/services/data_import/import_storage_handler.py` - Fix data extraction
- Frontend components displaying imported data - Need investigation

## Testing Evidence
- Database has 10 raw_import_records with data_import_id = af3c2979-3fa7-4f40-83dd-ee7cd89a9b94
- Discovery flow cf038071-1462-4d69-b332-0b5b88a43053 correctly links to this data_import_id
- Field mappings work (proving data exists) but UI can't display it

## Key Architecture Pattern
The system uses a two-table pattern that MUST be understood:
- **Master Flow Table** (crewai_flow_state_extensions): Uses flow_id as primary key
- **Child Flow Table** (discovery_flows): Links to master via master_flow_id, has data_import_id
- **Data Import Table** (data_imports): Referenced by discovery_flows.data_import_id

This is NOT over-engineering but required for multi-tenant isolation and atomic transactions.
