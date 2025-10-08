# AssetInventoryExecutor Architecture (Post-October 2025)

## Design Shift: Crews → Direct Execution

### OLD Architecture (Pre-October 2025)
- Used CrewAI crews for asset creation
- Multiple agents coordinated asset classification
- Slower, more complex orchestration

### NEW Architecture (Current)
- **Direct execution via AssetService**
- No crews involved in asset_inventory phase
- Faster, deterministic asset creation
- Field mappings applied during creation

## Entry Point

### File
`backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor.py`

### Key Method
```python
async def execute_asset_creation(
    self, flow_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Direct asset creation - NO crews
    
    Args:
        flow_context: Contains execution data (NOT self.state)
            - data_import_id: UUID of data import
            - db_session: Active database session
            - client_account_id, engagement_id: Tenant scoping
    
    Returns:
        {
            "status": "success" | "failed",
            "assets_created": int,
            "assets_failed": int,
            "asset_inventory": {...}  # Backward compatibility
        }
    """
```

## Implementation Flow

### 1. Retrieve Raw Records (by data_import_id)
```python
# Lines 92-107: Validate data_import_id
data_import_id = flow_context.get("data_import_id")
if not data_import_id:
    return {"status": "failed", "error": "data_import_id not found"}

# Lines 217-245: Query raw records
raw_records = await self._get_raw_records(
    db_session, 
    data_import_id,  # NOT master_flow_id!
    client_account_id, 
    engagement_id
)
```

### 2. Retrieve Field Mappings
```python
# Lines 247-268: Get approved field mappings
field_mappings = await self._get_field_mappings(
    db_session,
    data_import_id,  # Same data_import_id
    client_account_id
)
```

### 3. Transform & Create Assets
```python
# Lines 115-156: Apply field mappings
assets_data = self._prepare_assets_from_raw_records(
    raw_records, 
    field_mappings, 
    flow_context
)

# Lines 157-190: Create via AssetService (NO transaction nesting)
for asset_data in assets_data:
    asset = await asset_service.create_asset(
        asset_data, 
        flow_id=master_flow_id
    )
    if asset:
        created_assets.append(asset)
```

## Common Mistakes & Fixes

### Mistake 1: Querying by master_flow_id
```python
# ❌ WRONG (Issue #520-522)
stmt = select(RawImportRecord).where(
    RawImportRecord.master_flow_id == flow_id  # Field doesn't exist!
)

# ✅ CORRECT
stmt = select(RawImportRecord).where(
    RawImportRecord.data_import_id == UUID(data_import_id)
)
```

### Mistake 2: Starting New Transaction
```python
# ❌ WRONG
async with db_session.begin():  # Transaction already active!
    result = await asset_service.create_asset(...)

# ✅ CORRECT
result = await asset_service.create_asset(...)
await db_session.flush()  # Make IDs available
```

### Mistake 3: UUID Type Mismatch
```python
# ❌ WRONG (Pydantic expects string)
flow_context = {
    "data_import_id": uuid_obj  # UUID object
}

# ✅ CORRECT
flow_context = {
    "data_import_id": str(uuid_obj) if uuid_obj else None
}
```

## State vs flow_context Pattern

### Initialization (state required by interface)
```python
# State object required by BasePhaseExecutor.__init__
state = UnifiedDiscoveryFlowState()
state.flow_id = flow_id  # Minimal state

executor = AssetInventoryExecutor(
    state,  # Required but not used by execute_asset_creation
    crew_manager=None, 
    flow_bridge=None
)
```

### Execution (flow_context has actual data)
```python
# flow_context contains REAL execution data
flow_context = {
    "data_import_id": str(data_import_id),  # THE KEY FIELD
    "db_session": db_session,
    "master_flow_id": master_flow_id,
    "client_account_id": client_account_id,
    "engagement_id": engagement_id,
}

# execute_asset_creation uses flow_context (NOT state)
result = await executor.execute_asset_creation(flow_context)
```

## Field Mapping Application

### How It Works
1. Executor retrieves approved field mappings for data_import_id
2. Maps CSV column names to asset table fields
3. Example: `criticality` (CSV) → `business_criticality` (Asset)
4. Creates assets with mapped values

### Result
- Assets have correct `business_criticality` from CSV (High, Critical, Medium, Low)
- NOT default "Medium" values
- Classification logic built into AssetService

## Files Modified (Issues #520-522)
1. `asset_inventory_executor.py:92-107` - Validation
2. `asset_inventory_executor.py:157-190` - Transaction fix
3. `asset_inventory_executor.py:217-245` - Query fix (data_import_id)
4. `phase_executors.py:146-187` - UUID conversion

## Backward Compatibility
Returns `asset_inventory` field for old code:
```python
return {
    "status": "success",
    "assets_created": 5,
    "asset_inventory": {  # For backward compatibility
        "total_assets": 5,
        "classification_complete": True
    }
}
```
