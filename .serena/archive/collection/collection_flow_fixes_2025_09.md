# Collection Flow Fixes - September 2025

## Issue 1: Asset Model Missing is_deleted Attribute
**Problem**: Code filtering assets using `Asset.is_deleted == False` but field doesn't exist
**Error**: `type object 'Asset' has no attribute 'is_deleted'`
**Solution**: Use existing status field instead
**Code**:
```python
# Before - WRONG
.where(Asset.is_deleted == False)

# After - CORRECT
.where(Asset.status != 'decommissioned')
```
**File**: `backend/app/services/collection/asset_selection_bootstrap.py:154`
**Usage**: When filtering assets, always check actual model fields first

## Issue 2: CollectionGapAnalysis Schema Mismatch
**Problem**: Model has columns that don't exist in database
**Error**: `column collection_gap_analysis.analysis_type does not exist`
**Solution**: Comment out non-existent columns
**Code**:
```python
# These columns don't exist in DB - comment out
# analysis_type = Column(String(100), nullable=False, default="automated")
# analysis_version = Column(String(50), nullable=True)
# analysis_config = Column(JSONB, nullable=False, default=dict)
```
**File**: `backend/app/models/collection_flow/gap_analysis_model.py:79-82`
**Usage**: Always verify database schema matches model definitions

## Issue 3: Raw Data Type Mismatch
**Problem**: Code expects dict but gets string, causing `'str' object has no attribute 'items'`
**Solution**: Add defensive type checking
**Code**:
```python
# Ensure raw_data is a dict, not string
raw_data = getattr(asset, "raw_data", {}) or {}
if not isinstance(raw_data, dict):
    raw_data = {}

# Same for field_mappings
field_mappings = getattr(asset, "field_mappings_used", {}) or {}
if not isinstance(field_mappings, dict):
    field_mappings = {}
```
**File**: `backend/app/api/v1/endpoints/collection_crud_questionnaires/utils.py:159-167`
**Usage**: Always validate data types when processing external/stored data

## Issue 4: Selected Assets Type Confusion
**Problem**: Code treating list of dicts as Asset objects
**Solution**: Use data as-is without transformation
**Code**:
```python
# Before - WRONG (selected_assets is list of dicts, not Asset objects)
"assets": [
    {
        "id": str(asset.id),
        "name": asset.name,
        # ... trying to access attributes on dict
    }
    for asset in selected_assets
]

# After - CORRECT
"assets": selected_assets,  # Already formatted as list of dicts
```
**File**: `backend/app/api/v1/endpoints/collection_crud_questionnaires/agents.py:167`
**Usage**: Check return types of functions before processing

## Issue 5: Error Logging Silent Failures
**Problem**: Exceptions swallowed without logging, making debugging impossible
**Solution**: Add comprehensive error logging with stack traces
**Code**:
```python
except Exception as e:
    # Log with full stack trace for debugging
    logger.error(f"Failed for flow {flow_id}: {e}", exc_info=True)
    logger.error(f"Exception type: {type(e).__name__}")
    logger.error(f"Exception details: {str(e)}")

    # Store error in database for visibility
    error_msg = f"{type(e).__name__}: {str(e)}"
    await _update_questionnaire_status(
        questionnaire_id, "failed", error_message=error_msg, db=db
    )
```
**Files**:
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/commands.py:207-216`
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/agents.py:199-207`
**Usage**: Always log errors with exc_info=True for debugging

## Key Debugging Commands
```bash
# Check questionnaire failures in database
docker exec migration_postgres psql -U postgres -d migration_db -c \
  "SELECT id, description FROM migration.adaptive_questionnaires WHERE completion_status = 'failed';"

# Monitor backend logs for errors
docker logs migration_backend --tail 100 2>&1 | grep -E "ERROR|Failed|Exception"

# Restart backend after fixes
docker-compose restart backend
```

## Root Cause Analysis Pattern
1. Frontend shows instant timeout → Check browser console errors
2. No backend errors visible → Add better error logging first
3. Database shows failed records → Check description field for errors
4. Error says "X has no attribute Y" → Verify model matches actual schema
5. Type errors ('str' has no attribute) → Add defensive type checking

## Critical Lesson
**Never use fallback mechanisms when debugging** - they mask real problems. Disable all fallbacks to see actual errors, fix root causes, then re-enable safety mechanisms.
