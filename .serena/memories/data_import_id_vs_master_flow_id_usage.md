# Critical: data_import_id vs master_flow_id Usage

## The Confusion
Both `data_import_id` and `master_flow_id` exist in discovery_flows table, but they link to DIFFERENT entities.

## Table-by-Table Field Usage

### raw_import_records
- **Primary Key**: `data_import_id` (UUID)
- **Foreign Key**: Links to `data_imports.id`
- **DOES NOT HAVE**: `master_flow_id` field
- ❌ **WRONG**: `WHERE master_flow_id = flow_id` → Returns 0 rows
- ✅ **CORRECT**: `WHERE data_import_id = data_import_id`

### discovery_flows
- **Has BOTH fields**:
  - `data_import_id`: Links to the data import that created raw records
  - `master_flow_id`: Links to crewai_flow_state_extensions (orchestrator)

### import_field_mappings
- **Primary Key**: Uses `data_import_id`
- **Purpose**: Maps fields for a specific data import
- ✅ **Query by**: `data_import_id`

## Query Pattern Examples

### ❌ WRONG (Issue #520-522)
```python
# This returns 0 rows because raw_import_records doesn't have master_flow_id
stmt = select(RawImportRecord).where(
    RawImportRecord.master_flow_id == master_flow_id  # WRONG FIELD!
)
```

### ✅ CORRECT (Fixed)
```python
# First get data_import_id from discovery_flows
data_import_id = flow_context.get("data_import_id")

# Then query raw records by data_import_id
stmt = select(RawImportRecord).where(
    RawImportRecord.data_import_id == UUID(data_import_id),
    RawImportRecord.client_account_id == UUID(client_account_id),
    RawImportRecord.engagement_id == UUID(engagement_id),
)
```

## When to Use Which

### Use data_import_id when:
- Fetching `raw_import_records` (they don't have master_flow_id)
- Fetching `import_field_mappings` (linked to data import)
- Tracking which CSV/data source created records

### Use master_flow_id when:
- Querying `crewai_flow_state_extensions` (orchestrator state)
- Querying `discovery_flows` (flow metadata)
- Tracking overall flow lifecycle

## Recent Fix Location
- File: `asset_inventory_executor.py`
- Method: `_get_raw_records()` lines 217-245
- Changed from: `master_flow_id` to `data_import_id`
