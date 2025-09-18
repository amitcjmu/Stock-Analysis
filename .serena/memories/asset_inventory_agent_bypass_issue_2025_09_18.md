# Asset Inventory Agent Bypass Issue - 2025-09-18

## Insight 1: Agent System Being Bypassed by Direct Handlers
**Problem**: Asset Inventory Agent with 12 intelligent tools never executes, simple fallback classification used instead
**Root Cause**: Competing execution paths - direct handler registered that bypasses agent system
**Evidence**:
```python
# WRONG PATH (Currently Used):
discovery_handlers.py:295
"asset_inventory": {
    "handler": AssetInventoryExecutor.execute_asset_creation,  # Bypasses agent!
}

# CORRECT PATH (Should Use):
execution_engine_crew_discovery.execute_phase()
  → TenantScopedAgentPool.get_agent("asset_inventory")
  → Agent uses 12 tools for intelligent classification
```
**Solution**: Remove direct handler or redirect to agent-based execution
**Impact**: Assets misclassified as "device" instead of proper types (Server, Database, Application)

## Insight 2: Asset Visibility Filter Using Wrong Field
**Problem**: "Current Flow Only" toggle shows no assets despite assets existing
**Root Cause**: Backend filters only by `discovery_flow_id` but frontend sends `master_flow_id`
```python
# File: asset_list_handler.py:88
# BROKEN:
base_query = base_query.where(
    Asset.discovery_flow_id == flow_id.strip()
)

# FIXED:
from sqlalchemy import or_
base_query = base_query.where(
    or_(
        Asset.discovery_flow_id == flow_id.strip(),
        Asset.master_flow_id == flow_id.strip(),
        Asset.flow_id == flow_id.strip()
    )
)
```
**Usage**: When filtering assets by flow, check all flow ID fields

## Insight 3: Nested Cleansed Data Structure Issue
**Problem**: Classification can't access data buried in multiple cleansed_data layers
**Structure**: `{"cleansed_data": {"cleansed_data": {"hostname": "server01", "os": "linux"}}}`
**Solution**: Flatten nested structures recursively
```python
def _flatten_cleansed_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    result = {}
    for key, value in data.items():
        if key == "cleansed_data" and isinstance(value, dict):
            result.update(self._flatten_cleansed_data(value))
        else:
            result[key] = value
    return result
```

## Insight 4: Schema Consolidation Incomplete Implementation
**Problem**: Discovery flow stuck due to partial column renaming
**Files Missed**: Several critical runtime files still had legacy column names
- `asset_creation_bridge_service.py:360` - `inventory_completed`
- `data_helpers.py:138` - `attribute_mapping_completed`
- `asset_handler.py:182,308` - `dependencies_completed`, `tech_debt_completed`
**Lesson**: When renaming columns, use comprehensive search across all file types including scripts and tests
