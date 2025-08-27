# Questionnaire Persistence Endpoint - Issues Fixed

## Summary
Fixed critical issues preventing the Save Progress button from working for questionnaire persistence. The frontend should now be able to successfully call the backend API.

## Issues Identified & Fixed

### 1. Missing Request Schema
**Problem**: No Pydantic schema existed for the questionnaire submission request body.
**Fix**: Created `QuestionnaireSubmissionRequest` schema in `/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/schemas/collection_flow.py`

```python
class QuestionnaireSubmissionRequest(BaseModel):
    """Schema for submitting questionnaire responses"""

    responses: Dict[str, Any] = Field(
        ..., description="Form responses with field_id -> value mapping"
    )
    form_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Form metadata including application_id, completion_percentage, etc."
    )
    validation_results: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Validation results including isValid flag and field-level errors"
    )
```

### 2. Endpoint Parameter Mismatch
**Problem**: The endpoint signature in `collection.py` only accepted `responses: Dict[str, Any]` but the implementation expected a nested structure with `responses`, `form_metadata`, and `validation_results`.

**Fix**: Updated endpoint signature in `/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/api/v1/endpoints/collection.py`:

```python
@router.post("/flows/{flow_id}/questionnaires/{questionnaire_id}/responses")
async def submit_questionnaire_response(
    flow_id: str,
    questionnaire_id: str,
    request_data: QuestionnaireSubmissionRequest,  # Updated to use proper schema
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
```

### 3. Database Query Bug
**Problem**: In `collection_crud_update_commands.py`, the flow lookup query was using:
```python
.where(CollectionFlow.id == flow_id)
```
But it should use:
```python
.where(CollectionFlow.flow_id == flow_id)
```

**Fix**: Corrected the query in `/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/api/v1/endpoints/collection_crud_update_commands.py`:

```python
flow_result = await db.execute(
    select(CollectionFlow)
    .where(CollectionFlow.flow_id == flow_id)  # Fixed: Use flow_id not id
    .where(CollectionFlow.engagement_id == context.engagement_id)
)
```

### 4. Model Field Name Mismatch
**Problem**: Code was referencing `flow.progress` but the model field is named `progress_percentage`.

**Fix**: Updated all references to use the correct field name:
```python
flow.progress_percentage = form_metadata.get("completion_percentage", flow.progress_percentage)
```

### 5. Non-existent Field Reference
**Problem**: Code was trying to set `flow.updated_by = current_user.id` but this field doesn't exist in the model.

**Fix**: Removed the non-existent field assignment.

### 6. Missing Comprehensive Logging
**Problem**: No logging to track when the endpoint is called or help debug issues.

**Fix**: Added comprehensive logging throughout the submission process:

```python
logger.info(
    f"Processing questionnaire submission - Flow ID: {flow_id}, "
    f"Questionnaire ID: {questionnaire_id}, User ID: {current_user.id}, "
    f"Engagement ID: {context.engagement_id}"
)
logger.info(f"Processing {len(form_responses)} form responses")
logger.info(f"Committing {len(response_records)} response records to database")
```

### 7. Legacy Endpoint Compatibility
**Problem**: The legacy `/submit` endpoint wasn't updated to work with the new request format.

**Fix**: Updated the legacy endpoint to convert old format to new format:

```python
@router.post("/flows/{flow_id}/questionnaires/{questionnaire_id}/submit")
async def submit_questionnaire_response_legacy(
    # ... parameters ...
) -> Dict[str, Any]:
    """Legacy endpoint - converts old format to new format for backward compatibility"""
    request_data = QuestionnaireSubmissionRequest(
        responses=responses,
        form_metadata={},
        validation_results={}
    )
```

## Files Modified

### Backend Files
1. `/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/schemas/collection_flow.py`
   - Added `QuestionnaireSubmissionRequest` schema

2. `/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/api/v1/endpoints/collection.py`
   - Updated import to include new schema
   - Fixed endpoint signatures for both new and legacy endpoints
   - Added comprehensive logging

3. `/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/api/v1/endpoints/collection_crud_update_commands.py`
   - Fixed database query bug (flow_id vs id)
   - Fixed model field references (progress_percentage)
   - Added comprehensive logging
   - Updated function signature to accept new request format
   - Removed non-existent field assignment

## Endpoint Registration Verification

✅ **Confirmed**: The endpoint is properly registered in router_registry.py:
```python
if COLLECTION_AVAILABLE:
    api_router.include_router(collection_router, prefix="/collection")
```

✅ **Confirmed**: The endpoint is accessible at:
- New format: `POST /api/v1/collection/flows/{flow_id}/questionnaires/{questionnaire_id}/responses`
- Legacy format: `POST /api/v1/collection/flows/{flow_id}/questionnaires/{questionnaire_id}/submit`

## Expected Request Format

The frontend should send requests to the new endpoint with this structure:

```json
{
  "responses": {
    "field_id_1": "value_1",
    "field_id_2": "value_2",
    "application_name": "My App",
    "platform": "AWS"
  },
  "form_metadata": {
    "application_id": "uuid-here",
    "form_id": "application_details",
    "completion_percentage": 75,
    "submitted_at": "2025-01-27T12:00:00Z",
    "confidence_score": 0.85
  },
  "validation_results": {
    "isValid": true,
    "errors": {},
    "warnings": {
      "field_name": "Warning message"
    }
  }
}
```

## Testing Results

✅ **Endpoint Registration**: Confirmed the endpoint is properly registered and accessible
✅ **Request Format**: Confirmed the endpoint accepts the expected JSON structure
✅ **Router Integration**: Confirmed the router is properly integrated with FastAPI
✅ **Authentication Protection**: Confirmed the endpoint is properly protected by authentication

## Next Steps

1. **Frontend Integration**: The frontend should now be able to successfully call the backend API
2. **Authentication**: Ensure the frontend is sending proper authentication headers
3. **Flow ID Validation**: Ensure the frontend is using valid flow IDs that exist in the database
4. **Error Handling**: The frontend should handle various HTTP response codes appropriately:
   - 200: Success
   - 401/403: Authentication/Authorization issues
   - 404: Flow or questionnaire not found
   - 422: Validation errors
   - 500: Server errors

## Monitoring

The comprehensive logging will help track:
- When submissions are received
- Number of responses processed
- Database commit operations
- Flow progress updates
- Any errors that occur

Check Docker logs with:
```bash
docker logs migrate-ui-orchestrator-backend-1 --tail 50 | grep -E "(questionnaire|submission)"
```
