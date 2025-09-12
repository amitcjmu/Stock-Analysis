# Collection to Assessment Transition Fixes - January 2025

## Critical Issues Fixed

### 1. TenantScopedAgentPool Initialization Pattern
**Problem**: `'dict' object has no attribute 'get_or_create_agent'`
**Root Cause**: Using return value (None) instead of class reference

**Fix Pattern**:
```python
# WRONG - initialize_tenant_pool returns None
await TenantScopedAgentPool.initialize_tenant_pool(
    client_id=str(self.client_account_id),
    engagement_id=str(self.engagement_id),
)
self._modular_executor.agent_pool = None  # BUG!

# CORRECT - Use the class itself
await TenantScopedAgentPool.initialize_tenant_pool(
    client_id=str(self.client_account_id),
    engagement_id=str(self.engagement_id),
)
self._modular_executor.agent_pool = TenantScopedAgentPool  # Use class reference
```

### 2. AssessmentFlowRepository Model Initialization
**Problem**: `'str' object has no attribute '__name__'`
**Location**: `backend/app/repositories/assessment_flow_repository/base_repository.py:69`

**Fix**:
```python
# Missing model_class parameter
super().__init__(db, AssessmentFlow, client_account_id, engagement_id)
```

### 3. Database Schema Alignment - Idempotent Migration Pattern
**File**: `backend/alembic/versions/062_add_description_to_assessment_flows.py`

**Pattern for Idempotent Migrations**:
```python
def column_exists(table_name: str, column_name: str, schema: str = 'migration') -> bool:
    """Check if column exists in table."""
    bind = op.get_bind()
    try:
        stmt = sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = :schema
                  AND table_name = :table_name
                  AND column_name = :column_name
            )
        """)
        result = bind.execute(stmt, {
            "schema": schema,
            "table_name": table_name,
            "column_name": column_name
        }).scalar()
        return bool(result)
    except Exception:
        return False

def upgrade():
    # Check before adding each column
    if not column_exists('assessment_flows', 'column_name'):
        op.add_column(...)
```

### 4. Assessment Flow Creation Field Mapping
**Location**: `backend/app/repositories/assessment_flow_repository/commands/flow_commands.py`

**Required Fields**:
```python
flow_record = AssessmentFlow(
    client_account_id=self.client_account_id,
    engagement_id=engagement_id,
    flow_name=f"Assessment Flow - {len(selected_application_ids)} Applications",
    configuration={
        "selected_application_ids": selected_application_ids,
    },
    selected_application_ids=selected_application_ids,  # Separate JSONB column
    status=AssessmentFlowStatus.INITIALIZED.value,
    current_phase=AssessmentPhase.INITIALIZATION.value,
    progress=0.0,
    phase_progress={},
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
)
```

### 5. Missing Columns Added
Assessment flows table required these columns:
- `description` (Text, nullable)
- `flow_name` (String(255), NOT NULL)
- `phase_progress` (JSONB, default '{}')
- `configuration` (JSONB, default '{}')
- `runtime_state` (JSONB, default '{}')
- `flow_metadata` (JSONB, default '{}')
- `last_error` (Text, nullable)
- `error_count` (Integer, default 0)
- `started_at` (Timestamp with timezone)
- `completed_at` (Timestamp with timezone)
- `selected_application_ids` (JSONB, NOT NULL)

## Collection Flow Validation Requirements

### Critical Validation Points:
1. **Application Selection**: MUST have at least one application with valid asset ID
2. **Gap Analysis**: Must populate collection_gaps table
3. **Field Mappings**: Must complete field_mapping process
4. **Readiness Thresholds**:
   - Completeness >= 70%
   - Data quality >= 65%
   - No critical gaps unresolved

### Tables to Verify:
- `collection_flows` - Main flow record
- `collection_flow_applications` - Application linkage
- `collection_flow_gaps` - Gap identification
- `collection_flow_field_mappings` - Mapping results
- `assets` - Linked asset records

## Testing Commands

```bash
# Run migration
docker exec migration_backend alembic upgrade head

# Verify columns
docker exec migration_postgres psql -U postgres -d migration_db -c "\d migration.assessment_flows"

# Test transition
curl -X POST "http://localhost:8081/api/v1/collection/flows/{flow_id}/transition-to-assessment"
```

## Key Files Modified
- `/backend/app/services/field_mapping_executor/agent_executor.py`
- `/backend/app/services/crewai_flows/handlers/phase_executors/field_mapping_executor.py`
- `/backend/app/repositories/assessment_flow_repository/base_repository.py`
- `/backend/app/repositories/assessment_flow_repository/commands/flow_commands.py`
- `/backend/app/services/collection_transition_service.py`
- `/backend/alembic/versions/062_add_description_to_assessment_flows.py`
- `/src/components/collection/progress/FlowDetailsCard.tsx`
