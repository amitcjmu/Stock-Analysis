# Issue #999: Assets Table Update with 6R Recommendations

## Overview

This document describes the implementation of automatic asset table updates with 6R migration strategies after the assessment flow recommendation phase completes.

## Problem Statement

**Before**: Assessment flow generated per-application 6R recommendations (rehost, replatform, refactor, etc.) but stored them only in the `phase_results` JSON field of `assessment_flows` table. The `assets` table remained unchanged with `six_r_strategy = NULL` and `confidence_score = NULL`.

**After**: When the recommendation generation phase completes, the system automatically updates all assets matching each application's canonical name with:
- `six_r_strategy`: Enum value (rehost, replatform, refactor, rearchitect, replace, retire)
- `confidence_score`: Float 0.0-1.0 indicating recommendation confidence
- `assessment_flow_id`: UUID tracking which assessment produced the recommendation

## Architecture

### Components Modified

1. **AssetRepository** (`backend/app/repositories/asset_repository.py`)
   - Added `update_six_r_strategy_from_assessment()` method
   - Handles bulk updates by application name with tenant scoping
   - Validates 6R strategy enum values
   - Clamps confidence scores to 0.0-1.0 range

2. **RecommendationExecutor** (`backend/app/services/flow_orchestration/execution_engine_crew_assessment/`)
   - `recommendation_executor.py`: Calls asset update after agent completes
   - `recommendation_executor_asset_update.py`: New mixin with update logic
   - `base.py`: Integrates AssetUpdateMixin into execution engine

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Recommendation Agent Executes                                 │
│    - Analyzes all selected applications                          │
│    - Generates per-application 6R strategies                     │
│    - Returns JSON: {applications: [{...}, {...}], summary: {...}}│
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Results Validated (parallel task #999-iteration-4)            │
│    - Checks for required fields (application_name, six_r_strategy)│
│    - Counts applications with recommendations                    │
│    - Logs validation warnings                                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Asset Update Triggered (THIS IMPLEMENTATION)                 │
│    - Calls _update_assets_with_recommendations()                │
│    - Passes: parsed_result, assessment_flow_id, master_flow     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. AssetRepository Updates                                      │
│    FOR EACH application in results:                             │
│      - Extract: application_name, six_r_strategy, confidence    │
│      - Validate enum value                                      │
│      - UPDATE migration.assets WHERE application_name = ?       │
│        SET six_r_strategy, confidence_score, assessment_flow_id │
│      - Log success/failure                                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Results Returned                                             │
│    - assets_updated: true/false                                 │
│    - assets_updated_count: 42                                   │
│    - Stored in phase_results for audit trail                   │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. AssetRepository Method

**File**: `backend/app/repositories/asset_repository.py`

**Method**: `update_six_r_strategy_from_assessment()`

**Key Features**:
- **Tenant Scoping**: All queries include `client_account_id` and `engagement_id`
- **Bulk Update**: Updates ALL assets matching application_name in one query
- **Enum Validation**: Validates 6R strategy against valid enum values
- **Confidence Clamping**: Ensures confidence scores are 0.0-1.0
- **Detailed Logging**: Logs every update with [ISSUE-999] prefix

**SQL Generated**:
```sql
UPDATE migration.assets
SET six_r_strategy = 'rehost',
    confidence_score = 0.85,
    assessment_flow_id = '09cfb82e-...'
WHERE application_name = 'SAP ERP'
  AND client_account_id = 'uuid-...'
  AND engagement_id = 'uuid-...';
```

### 2. Asset Update Mixin

**File**: `backend/app/services/flow_orchestration/execution_engine_crew_assessment/recommendation_executor_asset_update.py`

**Class**: `AssetUpdateMixin`

**Method**: `_update_assets_with_recommendations()`

**Key Features**:
- **Database Session Access**: Uses `self.crew_utils.db` from execution engine
- **Graceful Partial Failures**: Continues processing even if one app fails
- **Transaction Management**: Commits on success, rollback on critical error
- **Comprehensive Logging**: Tracks each application update with success/error details

**Error Handling**:
- `ValueError`: Invalid 6R strategy enum - log and skip application
- `Exception`: Unexpected error - log with traceback, continue processing
- Critical error: Rollback transaction, return partial count

### 3. Integration Points

**File**: `backend/app/services/flow_orchestration/execution_engine_crew_assessment/recommendation_executor.py`

**Integration**:
```python
# After agent execution and validation
assets_updated_count = await self._update_assets_with_recommendations(
    parsed_result=parsed_result,
    assessment_flow_id=assessment_flow_id,
    master_flow=master_flow,
)

# Include in phase results
return {
    "phase": "recommendation_generation",
    "status": "completed",
    "results": {...},
    "assets_updated": assets_updated_count > 0,
    "assets_updated_count": assets_updated_count,
}
```

## Multi-Tenant Security

### Tenant Scoping
Every database query includes both:
- `client_account_id`: Organization isolation
- `engagement_id`: Project/session isolation

### Row-Level Security
PostgreSQL RLS policies on `assets` table enforce:
```sql
POLICY "rls_assets_tenant_isolation"
  TO application_role
  USING ((client_account_id = current_setting('app.client_id'::text, true)::uuid))
```

### Repository Pattern
The `AssetRepository` is initialized with tenant context:
```python
asset_repo = AssetRepository(
    db=db,
    client_account_id=str(master_flow.client_account_id),
    engagement_id=str(master_flow.engagement_id),
)
```

All queries inherit this scoping via `_apply_context_filter()` method.

## Testing & Verification

### Verification Query

Run the verification SQL script:
```bash
docker exec migration_postgres psql -U postgres -d migration_db \
  -f /app/scripts/verify_issue_999.sql
```

**Expected Output**:
1. **Check 1**: Assets with 6R strategies populated
2. **Check 2**: Distribution across 6R categories
3. **Check 3**: Recent updates with timestamps
4. **Check 4**: Per-application breakdown
5. **Check 5**: Assessment flows → asset counts

### Manual Test Flow

1. **Start assessment flow**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/assessment-flow/create \
     -H "X-Client-Account-ID: ${CLIENT_ID}" \
     -H "X-Engagement-ID: ${ENGAGEMENT_ID}" \
     -d '{"selected_application_ids": [...]}'
   ```

2. **Resume to recommendation phase**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/assessment-flow/${FLOW_ID}/resume \
     -H "X-Client-Account-ID: ${CLIENT_ID}" \
     -d '{"phase": "recommendation_generation"}'
   ```

3. **Check logs for [ISSUE-999] markers**:
   ```bash
   docker logs migration_backend -f | grep "\[ISSUE-999\]"
   ```

4. **Query assets table**:
   ```sql
   SELECT application_name, six_r_strategy, confidence_score
   FROM migration.assets
   WHERE assessment_flow_id = '${FLOW_ID}'
   ORDER BY updated_at DESC;
   ```

### Logging Output

Successful execution shows:
```
[ISSUE-999] 📝 Processing 3 application recommendations for asset updates
[ISSUE-999] ✅ Updated 5 asset(s) for application 'SAP ERP' with 6R strategy: rehost (confidence: 85.00%)
[ISSUE-999] ✅ Updated 2 asset(s) for application 'CRM System' with 6R strategy: replatform (confidence: 78.50%)
[ISSUE-999] ✅ Updated 1 asset(s) for application 'Legacy Billing' with 6R strategy: retire (confidence: 95.00%)
[ISSUE-999] ✅ Asset update complete: 8 assets updated across 3 applications
```

## Error Scenarios & Handling

### 1. Invalid 6R Strategy
**Scenario**: Agent returns invalid strategy "modernize"

**Handling**:
```python
# ValueError raised by repository
# Logged as error, continue to next application
logger.error("[ISSUE-999] ❌ Invalid 6R strategy for application 'App1': ...")
```

### 2. No Assets Match Application Name
**Scenario**: Canonical name doesn't match any assets

**Handling**:
```python
# Zero rows updated
# Logged as warning
logger.warning("[ISSUE-999] ⚠️ No assets found for application 'App2' ...")
```

### 3. Database Connection Lost
**Scenario**: Connection error during update

**Handling**:
```python
# Exception caught
# Transaction rolled back
# Partial count returned
logger.error("[ISSUE-999] ❌ Critical error during asset updates: ...")
await db.rollback()
return total_updated  # Return count of successful updates
```

### 4. Agent Returns No Recommendations
**Scenario**: Empty applications array

**Handling**:
```python
# Early return with warning
logger.warning("[ISSUE-999] ⚠️ No applications found in recommendation results")
return 0
```

## Database Schema

### Assets Table Columns (Relevant)

```sql
CREATE TABLE migration.assets (
    id UUID PRIMARY KEY,
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    application_name VARCHAR(255),  -- Canonical application name
    six_r_strategy VARCHAR(50),     -- Updated by this implementation
    confidence_score FLOAT,          -- Updated by this implementation
    assessment_flow_id UUID,         -- Updated by this implementation
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Valid 6R Strategies

Per `SixRStrategy` enum in `backend/app/models/asset/enums.py`:
- `rehost`: Lift-and-shift with minimal changes
- `replatform`: Reconfigure as PaaS
- `refactor`: Modify code for cloud deployment
- `rearchitect`: Microservices/cloud-native transformation
- `replace`: Replace with COTS/SaaS OR rewrite custom apps
- `retire`: Decommission/sunset assets

## Future Enhancements

1. **Bulk Update Optimization**: Consider batching updates if asset counts exceed threshold
2. **Audit Trail**: Store update history in separate table for compliance
3. **Rollback Support**: Add undo functionality if recommendations change
4. **Conflict Resolution**: Handle scenarios where multiple assessment flows update same assets
5. **Asset Status Update**: Automatically transition `migration_status` to "assessed"

## References

- **GitHub Issue**: #999
- **Parallel Work**: Iteration 4 (per-application 6R generation by python-crewai-fastapi-expert)
- **Related ADRs**: ADR-012 (Flow Status Separation), ADR-024 (TenantMemoryManager)
- **Repository Pattern**: `/docs/analysis/Notes/coding-agent-guide.md`
- **Multi-Tenant Guide**: `CLAUDE.md` - Multi-Tenant Data Scoping section
