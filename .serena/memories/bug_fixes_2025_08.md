# Bug Fixes and Solutions - August 2025

## Collection Flow Silent Failures (2025-08-20) - PR #145

### Context: Collection -> Adaptive Forms navigation led to infinite fault loop
**Problem**: Selecting applications triggered 500 errors instead of generating questionnaires
**Root Causes**:
1. Backend expected database `id` but frontend sent `flow_id`
2. Missing support for 'update_applications' action
3. UUID type mismatches in questionnaire queries
4. Import path errors after modularization

**Solutions**:

#### 1. Fixed Parameter Mismatches
```python
# backend/app/api/v1/endpoints/collection_crud_update_commands.py
# Changed from CollectionFlow.id to CollectionFlow.flow_id
result = await db.execute(
    select(CollectionFlow).where(
        CollectionFlow.flow_id == UUID(flow_id),  # Was: CollectionFlow.id == flow_id
        CollectionFlow.engagement_id == context.engagement_id,
    )
)
```

#### 2. Added UUID Validation
```python
# Added proper UUID conversion for questionnaire_id
try:
    questionnaire_uuid = UUID(questionnaire_id)
except (ValueError, TypeError):
    raise HTTPException(status_code=400, detail="Invalid questionnaire ID format")
```

#### 3. Fixed Import Paths After Modularization
```python
# Fixed circular import issues
from app.api.v1.endpoints.collection_utils import log_collection_failure  # Wrong
from app.api.v1.endpoints.collection_validation_utils import log_collection_failure  # Correct
```

#### 4. Updated Schema Support
```python
class CollectionFlowUpdate(BaseModel):
    action: Optional[str] = Field(
        None,
        description="Action to perform: continue, pause, cancel, update_applications"
    )

class CollectionFlowResponse(BaseModel):
    discovery_flow_id: Optional[str] = None  # Added field
```

#### 5. Fixed Enum Usage
```python
# backend/app/services/monitoring/flow_health_monitor.py
CollectionFlow.status.notin_([
    CollectionFlowStatus.COMPLETED.value,  # Use .value for enum
    CollectionFlowStatus.FAILED.value,
    CollectionFlowStatus.CANCELLED.value,
])
```

## Field Mapping Data Corruption Issues (2025-08-18)

### Context: Field mappings showing JSON artifacts instead of CSV column names
**Problem**: Auto-mapped fields displayed "mappings", "skipped_fields", "synthesis_required" instead of actual CSV columns
**Root Cause**: CrewAI agent JSON response metadata was being stored as field names
**Solution**:
1. Filter CrewAI metadata in `extract_records_from_data()` helper
2. Add validation in `create_field_mappings()` to skip JSON artifacts
3. Clean existing corrupted mappings via SQL

```python
# Files modified:
# backend/app/services/data_import/storage_manager/helpers.py
# backend/app/services/data_import/storage_manager/mapping_operations.py

# Cleanup script:
DELETE FROM migration.import_field_mappings
WHERE source_field IN ('mappings', 'skipped_fields', 'synthesis_required', '{}', '[]')
```

### Context: Test data contamination in production tenant
**Problem**: Test field names (Device_ID, Device_Name) appearing instead of production fields (App_ID, App_Name)
**Root Cause**: Multiple imports in same tenant with test and production data mixed
**Solution**: Multi-layer defense against test data:
1. Frontend filtering in useFieldMappings.ts
2. Backend filtering in mapping_service.py
3. Database cleanup script for existing contamination

```python
# Created: backend/scripts/cleanup_test_data_mappings.py
# Usage: python scripts/cleanup_test_data_mappings.py --dry-run
```

## Discovery Flow Display Issues (2025-08-18)

### Context: Discovery Overview showing "No Active Flows" despite data existing
**Problem**: Flows in "initialization" phase not appearing as active
**Root Cause**: Query filtered by status "initializing" but flows use phase "initialization"
**Solution**: Modified flow_status_service.py to check both status AND phase fields

```python
# Added phase-based filtering alongside status filtering
# Changed default time range from 24h to 7d for better visibility
```

## Dependency Conflicts (2025-08-18)

### Context: embedchain vs pypdf version conflict
**Problem**: embedchain==0.1.128 requires pypdf<6.0.0 but pypdf==6.0.0 needed for CVE-2025-3429
**Solution**: Removed unused embedchain dependency entirely

```bash
# backend/requirements.txt - removed embedchain==0.1.128
# Maintained pypdf==6.0.0 for security
```

## Data Import Record Count Issues (2025-08-18)

### Context: Nested JSON structures counted incorrectly
**Problem**: {"data": [records]} counted as 1 record instead of array length
**Solution**: Enhanced data extraction to handle nested structures

```python
# Added _extract_records_from_data() helper
# Handles {"data": [...]} format properly
# Checks for common nested keys: "records", "items", "results", "rows"
```

## Key Insights

### Multi-Tenant Data Isolation
- Tenant isolation works correctly (client_account_id boundaries respected)
- Issues were within-tenant data quality problems, not cross-tenant leaks
- Each discovery flow correctly tied to ONE import (1:1 relationship maintained)

### Import Data Integrity
- Raw CSV data stored correctly in raw_import_records
- Field mappings can become corrupted but original data remains intact
- "Trigger Analysis" can regenerate mappings from clean raw data

### Prevention Strategies
1. Always validate field names before storing mappings
2. Filter AI response metadata at multiple layers
3. Use cleanup scripts for existing data issues
4. Modularize large files to meet line limits (400 lines max)
