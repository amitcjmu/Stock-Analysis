# Bug #676 Fix: Invalid flow ID returns 405 Method Not Allowed instead of 404 Not Found

## Issue Summary
When querying for a non-existent flow ID via GET request, the API returned 405 Method Not Allowed instead of the expected 404 Not Found.

**Affected Endpoint**: `GET /api/v1/master-flows/{flow_id}`

## Root Cause Analysis
The master flows CRUD router (`backend/app/api/v1/master_flows/master_flows_crud.py`) did NOT have a GET endpoint for `/{flow_id}`. The router only had:
- `GET /{master_flow_id}/assets` - Get assets for a flow
- `GET /{master_flow_id}/discovery-flow` - Get discovery flow by master flow ID
- `DELETE /{flow_id}` - Soft delete a flow

When a client requested `GET /api/v1/master-flows/{flow_id}`, FastAPI couldn't find a matching GET handler, so it returned **405 Method Not Allowed** (since only DELETE was registered for that path pattern).

## Solution Implemented

### 1. Added Response Schema (`master_flows_schemas.py`)
Created `MasterFlowResponse` Pydantic model to properly serialize master flow data:

```python
class MasterFlowResponse(BaseModel):
    """Master flow detail response model (Bug #676 fix)"""

    flow_id: str
    flow_type: str
    flow_name: Optional[str] = None
    flow_status: str
    client_account_id: str
    engagement_id: str
    user_id: str
    flow_configuration: Dict[str, Any]
    current_phase: Optional[str] = None
    progress_percentage: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    execution_metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
```

### 2. Added GET Endpoint (`master_flows_crud.py`)
Implemented `get_master_flow_by_id` endpoint with:
- **Tenant scoping**: Uses `CrewAIFlowStateExtensionsRepository` with tenant context
- **UUID validation**: Returns 400 for invalid UUID format
- **Proper 404 handling**: Returns 404 when flow not found (instead of 405)
- **Authentication**: Requires authenticated user via `get_current_user` dependency
- **Error handling**: Comprehensive exception handling with proper HTTP status codes

```python
@router.get("/{flow_id}", response_model=MasterFlowResponse)
async def get_master_flow_by_id(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
    current_user: User = Depends(get_current_user),
) -> MasterFlowResponse:
    """
    Get master flow by ID (Bug #676 fix).

    Returns 404 if flow not found, instead of 405 Method Not Allowed.
    """
    # Implementation details...
```

## Expected Behavior After Fix

### Test Case 1: No Authentication Headers
**Request**: `GET /api/v1/master-flows/00000000-0000-0000-0000-000000000000`

**Response**:
- Status: **400 Bad Request** (missing tenant context headers)
- Body: `{"error": "Context extraction failed", "path": "..."}`

✅ **Pass**: No longer returns 405 Method Not Allowed

### Test Case 2: With Tenant Headers, No Auth Token
**Request**:
```bash
GET /api/v1/master-flows/00000000-0000-0000-0000-000000000000
Headers:
  X-Client-Account-ID: 00000000-0000-0000-0000-000000000001
  X-Engagement-ID: 00000000-0000-0000-0000-000000000001
```

**Response**:
- Status: **401 Unauthorized**
- Body: `{"detail": "Not authenticated"}`

✅ **Pass**: Endpoint exists, requires authentication

### Test Case 3: With Valid Auth, Invalid Flow ID
**Request**:
```bash
GET /api/v1/master-flows/00000000-0000-0000-0000-000000000000
Headers:
  X-Client-Account-ID: <valid-client-id>
  X-Engagement-ID: <valid-engagement-id>
  Authorization: Bearer <valid-token>
```

**Response**:
- Status: **404 Not Found**
- Body: `{"detail": "Master flow 00000000-0000-0000-0000-000000000000 not found"}`

✅ **Expected**: Returns 404 for non-existent flows

### Test Case 4: With Valid Auth and Valid Flow ID
**Response**:
- Status: **200 OK**
- Body: `MasterFlowResponse` JSON object

## Files Modified
1. `/backend/app/api/v1/master_flows_schemas.py` - Added `MasterFlowResponse` schema
2. `/backend/app/api/v1/master_flows/master_flows_crud.py` - Added GET `/{flow_id}` endpoint

## Architecture Compliance
✅ **Multi-tenant scoping**: Uses `client_account_id` and `engagement_id` in all queries
✅ **Repository pattern**: Uses `CrewAIFlowStateExtensionsRepository` for data access
✅ **Service layer separation**: Clean separation of concerns
✅ **Authentication**: Requires authenticated user
✅ **Error handling**: Proper HTTP status codes (400/401/404/500)
✅ **snake_case naming**: All fields use snake_case per project standards

## Verification
Verified via:
1. ✅ OpenAPI schema inspection (`/openapi.json`) - Endpoint registered
2. ✅ Docker backend restart - Changes loaded successfully
3. ✅ HTTP tests - Proper status codes (400/401 instead of 405)
4. ✅ Python syntax check - No compilation errors

## Related Issues
- Bug #676: Invalid flow ID returns 405 Method Not Allowed instead of 404 Not Found

## Date
October 22, 2025
