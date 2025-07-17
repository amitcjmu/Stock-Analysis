# Phase 1 - Agent B1: Backend API Consolidation

## Context
You are part of a parallel remediation effort to fix critical architectural issues in the AI Modernize Migration Platform. This is Track B (Backend) of Phase 1, focusing on consolidating the fragmented API endpoints into a clean, unified v3 API.

### Required Reading Before Starting
- `docs/planning/PHASE-1-REMEDIATION-PLAN.md` - Overall Phase 1 objectives
- `docs/development/AI_Force_Migration_Platform_Summary_for_Coding_Agents.md` - Platform overview
- Current API analysis: Review existing endpoints in `/api/v1/unified-discovery/`, `/api/v1/discovery/`, and `/api/v2/discovery-flows/`

### Phase 1 Goal
Create a unified, well-documented API that eliminates confusion and duplication. Your v3 API will be the single source of truth for all discovery flow operations.

## Your Specific Tasks

### 1. Create V3 API Structure
**Files to create**:
```
backend/app/api/v3/
├── __init__.py
├── discovery_flow.py       # Main discovery flow endpoints
├── field_mapping.py        # Field mapping operations
├── data_import.py          # Data import operations
├── schemas/
│   ├── __init__.py
│   ├── discovery.py        # Pydantic schemas
│   ├── field_mapping.py
│   └── responses.py
└── middleware/
    ├── __init__.py
    └── deprecation.py      # Add deprecation headers to old APIs
```

### 2. Implement Core Discovery Flow Endpoints
**File**: `backend/app/api/v3/discovery_flow.py`

```python
"""
Unified Discovery Flow API v3
Consolidates all discovery flow operations into a single, coherent API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

router = APIRouter(prefix="/api/v3/discovery-flow", tags=["discovery-v3"])

@router.post("/flows")
async def create_flow():
    """Create a new discovery flow"""
    # Uses flow_id from the start (no session_id)

@router.get("/flows/{flow_id}")
async def get_flow():
    """Get flow details with all sub-resources"""

@router.get("/flows/{flow_id}/status")
async def get_flow_status():
    """Get real-time flow execution status"""

@router.post("/flows/{flow_id}/execute/{phase}")
async def execute_phase():
    """Execute a specific flow phase"""

@router.get("/flows")
async def list_flows():
    """List all flows with filtering and pagination"""

@router.delete("/flows/{flow_id}")
async def delete_flow():
    """Soft delete a flow and its resources"""
```

### 3. Create Comprehensive Schemas
**File**: `backend/app/api/v3/schemas/discovery.py`

```python
from pydantic import BaseModel, Field, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class FlowPhase(str, Enum):
    """Discovery flow phases"""
    FIELD_MAPPING = "field_mapping"
    DATA_CLEANSING = "data_cleansing"
    INVENTORY_BUILDING = "inventory_building"
    APP_SERVER_DEPENDENCIES = "app_server_dependencies"
    APP_APP_DEPENDENCIES = "app_app_dependencies"
    TECHNICAL_DEBT = "technical_debt"

class FlowStatus(str, Enum):
    """Flow execution status"""
    INITIALIZING = "initializing"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class FlowCreate(BaseModel):
    """Request schema for creating a flow"""
    name: str = Field(..., description="Flow name")
    description: Optional[str] = Field(None, description="Flow description")
    client_account_id: UUID4 = Field(..., description="Client account identifier")
    engagement_id: UUID4 = Field(..., description="Engagement identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class FlowResponse(BaseModel):
    """Response schema for flow operations"""
    flow_id: UUID4
    name: str
    status: FlowStatus
    current_phase: Optional[FlowPhase]
    progress_percentage: float = Field(ge=0, le=100)
    created_at: datetime
    updated_at: datetime
    phases_completed: List[FlowPhase]
    metadata: Dict[str, Any]
```

### 4. Implement Deprecation Middleware
**File**: `backend/app/api/v3/middleware/deprecation.py`

```python
from fastapi import Request
from fastapi.responses import JSONResponse
import warnings

class DeprecationMiddleware:
    """Add deprecation headers to old API versions"""
    
    DEPRECATED_PATHS = {
        "/api/v1/unified-discovery": "Use /api/v3/discovery-flow",
        "/api/v1/discovery": "Use /api/v3/discovery-flow",
        "/api/v2/discovery-flows": "Use /api/v3/discovery-flow"
    }
    
    async def __call__(self, request: Request, call_next):
        path = request.url.path
        
        for deprecated_path, replacement in self.DEPRECATED_PATHS.items():
            if path.startswith(deprecated_path):
                response = await call_next(request)
                response.headers["X-API-Deprecation-Warning"] = f"This API is deprecated. {replacement}"
                response.headers["X-API-Deprecation-Date"] = "2024-03-01"
                return response
        
        return await call_next(request)
```

### 5. Create OpenAPI Documentation
**File**: `backend/app/api/v3/openapi.py`

```python
def custom_openapi():
    """Enhanced OpenAPI schema with examples and detailed descriptions"""
    # Add request/response examples
    # Include authentication details
    # Document all error responses
    # Add webhook specifications
```

## Success Criteria
- [ ] All v3 endpoints implemented with consistent patterns
- [ ] 100% of endpoints have Pydantic schema validation
- [ ] OpenAPI documentation complete with examples
- [ ] Deprecation warnings on all old endpoints
- [ ] Zero breaking changes (old APIs still work)
- [ ] Response time <200ms for all endpoints
- [ ] Comprehensive error handling with proper HTTP codes

## Interfaces with Other Agents
- **Agent A1** provides flow_id implementation you'll use
- **Agent B2** will create TypeScript client for your API
- **Agent C1** uses your endpoints for state management
- **Agent D1** uses field mapping endpoints

## Implementation Guidelines

### 1. API Design Principles
- RESTful conventions strictly followed
- Consistent naming (plural for collections)
- Proper HTTP verbs and status codes
- Pagination for all list endpoints
- Filtering via query parameters
- Sorting support where applicable

### 2. Error Response Format
```python
class ErrorResponse(BaseModel):
    error: str              # Machine-readable error code
    message: str           # Human-readable message
    details: Optional[Dict] # Additional context
    request_id: str        # For debugging
```

### 3. Pagination Pattern
```python
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
```

### 4. Authentication & Authorization
- Use existing auth middleware
- Ensure tenant isolation via context
- Validate permissions per endpoint

## Commands to Run
```bash
# Generate OpenAPI schema
docker exec -it migration_backend python -m app.api.v3.generate_openapi

# Test new endpoints
docker exec -it migration_backend python -m pytest tests/api/v3/ -v

# Check for breaking changes
docker exec -it migration_backend python -m app.api.v3.compatibility_check

# Performance testing
docker exec -it migration_backend python -m app.api.v3.load_test
```

## Definition of Done
- [ ] All v3 endpoints implemented and tested
- [ ] Pydantic schemas for all requests/responses
- [ ] OpenAPI spec generated and validated
- [ ] Deprecation middleware active on old endpoints
- [ ] All endpoints achieve <200ms response time
- [ ] Error handling comprehensive and consistent
- [ ] PR created with title: "feat: [Phase1-B1] API v3 consolidation"
- [ ] API documentation published
- [ ] Breaking changes documented (should be none)

## Endpoint Mapping (Old → New)
```
/api/v1/unified-discovery/flow/initialize → /api/v3/discovery-flow/flows
/api/v1/discovery/session/{id}/status → /api/v3/discovery-flow/flows/{id}/status
/api/v2/discovery-flows/flows/active → /api/v3/discovery-flow/flows?status=active
/api/v1/data-import/store-import → /api/v3/data-import/imports
```

## Notes
- Maintain backward compatibility throughout
- Use flow_id exclusively (no session_id)
- Follow OpenAPI 3.1 specification
- Consider rate limiting for production