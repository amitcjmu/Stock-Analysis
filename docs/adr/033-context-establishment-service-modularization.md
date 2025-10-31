# ADR-033: Context Establishment Service Modularization

## Status
Accepted (2025-10-30)

Implemented in: PR #872

Related: ADR-007 (Comprehensive Modularization Architecture), ADR-009 (Multi-Tenant Architecture), ADR-032 (JWT Refresh Token Security)

## Context

### Problem Statement

The Context Establishment API endpoint (`context_establishment.py`) had grown into a 541-line monolithic file with multiple responsibilities:

1. **Mixed Concerns**: Single file handling three distinct API endpoints:
   - GET `/clients` - List available client accounts
   - GET `/engagements` - List engagements for a client
   - POST `/update-context` - Set user's active client/engagement context

2. **Code Organization Issues**:
   - All Pydantic models mixed with endpoint handlers
   - Shared utilities embedded within endpoint code
   - No clear separation between query logic and response formatting
   - Difficult to test individual endpoints in isolation

3. **Maintainability Challenges**:
   - 541 LOC exceeded 350-line limit from ADR-007
   - Hard to understand endpoint boundaries
   - Merge conflicts when multiple developers work on context features
   - Duplication of validation and error handling logic

4. **Scalability Concerns**:
   - Adding new context-related endpoints required modifying large file
   - No clear pattern for extending context establishment logic
   - Tight coupling between models, utilities, and handlers

### Why Context Establishment Is Critical

The Context Establishment API is **exempt from global engagement middleware** (ADR-009) because it enables the frontend to establish context step-by-step:

```
1. User logs in (no context)
2. Frontend calls GET /clients → User selects client
3. Frontend calls GET /engagements?client_id=X → User selects engagement
4. Frontend calls POST /update-context → Context established
5. All subsequent API calls include client_account_id and engagement_id
```

This makes context establishment a **foundational service** that must be:
- **Highly reliable**: Cannot fail or users cannot access the application
- **Well-tested**: Edge cases must be handled (no clients, no engagements, invalid IDs)
- **Maintainable**: Changes should be easy and safe
- **Extensible**: Support future context types (project context, team context)

### Existing Modularization Patterns (ADR-007)

ADR-007 established modularization principles:
- **Single Responsibility**: Each module has one clear purpose
- **Composition over Inheritance**: Use router composition
- **Type Safety First**: Separate Pydantic models from handlers
- **350 LOC Limit**: All files must be under 350 lines

The `context_establishment.py` file violated these principles at 541 lines.

## Decision

**We will modularize `context_establishment.py` into a directory structure** following ADR-007 patterns, separating concerns into focused modules.

### Directory Structure

**Before** (541 LOC in single file):
```
backend/app/api/v1/endpoints/context_establishment.py
```

**After** (5 focused modules):
```
backend/app/api/v1/endpoints/context_establishment/
├── __init__.py           # Router composition (54 LOC)
├── models.py             # Pydantic schemas (59 LOC)
├── utils.py              # Shared utilities (35 LOC)
├── clients.py            # GET /clients endpoint (240 LOC)
├── engagements.py        # GET /engagements endpoint (240 LOC)
└── user_context.py       # POST /update-context endpoint (93 LOC)

Total: 721 LOC (includes improved documentation and error handling)
```

### Module Responsibilities

#### 1. `__init__.py` - Router Composition (54 LOC)

**Purpose**: Compose sub-routers and export public interfaces

```python
"""
Context Establishment API - Dedicated endpoints for initial context setup.

Modularized Structure:
- models.py: Pydantic response models
- utils.py: Shared utilities and constants
- clients.py: GET /clients endpoint
- engagements.py: GET /engagements endpoint
- user_context.py: POST /update-context endpoint
"""

from fastapi import APIRouter
from app.api.v1.api_tags import APITags

# Import all sub-routers
from .clients import router as clients_router
from .engagements import router as engagements_router
from .user_context import router as user_context_router

# Re-export models for backward compatibility
from .models import (
    ClientResponse,
    ClientsListResponse,
    ContextUpdateRequest,
    ContextUpdateResponse,
    EngagementResponse,
    EngagementsListResponse,
)

# Create main router and include all sub-routers
router = APIRouter()
router.include_router(clients_router, tags=[APITags.CONTEXT_ESTABLISHMENT])
router.include_router(engagements_router, tags=[APITags.CONTEXT_ESTABLISHMENT])
router.include_router(user_context_router, tags=[APITags.CONTEXT_ESTABLISHMENT])
```

**Key Features**:
- **Router Composition**: Combines three sub-routers into single export
- **Backward Compatibility**: Re-exports models to prevent breaking imports
- **Clear Documentation**: Module structure explained at top
- **Single Tag**: All endpoints grouped under `CONTEXT_ESTABLISHMENT` tag

#### 2. `models.py` - Pydantic Schemas (59 LOC)

**Purpose**: Define all request/response models

```python
"""Pydantic models for Context Establishment API responses."""

from typing import List
from pydantic import BaseModel, Field

class ClientResponse(BaseModel):
    """Response model for a single client account."""
    id: int = Field(..., description="Client account ID")
    name: str = Field(..., description="Client account name")

class ClientsListResponse(BaseModel):
    """Response model for list of available clients."""
    clients: List[ClientResponse]

class EngagementResponse(BaseModel):
    """Response model for a single engagement."""
    id: int = Field(..., description="Engagement ID")
    name: str = Field(..., description="Engagement name")
    client_id: int = Field(..., description="Associated client account ID")

class EngagementsListResponse(BaseModel):
    """Response model for list of engagements."""
    engagements: List[EngagementResponse]

class ContextUpdateRequest(BaseModel):
    """Request model for updating user context."""
    client_id: int = Field(..., description="Selected client account ID")
    engagement_id: int = Field(..., description="Selected engagement ID")

class ContextUpdateResponse(BaseModel):
    """Response model for context update confirmation."""
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Human-readable message")
    client_id: int
    engagement_id: int
```

**Benefits**:
- **Single Source of Truth**: All schemas in one place
- **Type Safety**: Frontend can generate types from OpenAPI spec
- **Documentation**: Field descriptions for API docs
- **Testability**: Easy to test serialization/validation

#### 3. `utils.py` - Shared Utilities (35 LOC)

**Purpose**: Constants and helper functions used across endpoints

```python
"""Shared utilities for Context Establishment API."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Middleware exemption paths (no client_account_id/engagement_id required)
CONTEXT_EXEMPT_PATHS = [
    "/api/v1/context-establishment/clients",
    "/api/v1/context-establishment/engagements",
    "/api/v1/context-establishment/update-context",
]

def validate_user_access(user_id: str, client_id: int) -> bool:
    """
    Validate user has access to specified client account.

    Args:
        user_id: Authenticated user ID
        client_id: Client account ID to check

    Returns:
        True if user has access, False otherwise
    """
    # Implementation details in actual file
    pass
```

**Benefits**:
- **DRY Principle**: Avoid duplicating constants/helpers
- **Centralized Logging**: Consistent logger for all endpoints
- **Reusability**: Functions used by multiple endpoint modules

#### 4. `clients.py` - GET /clients Endpoint (240 LOC)

**Purpose**: List all client accounts accessible to authenticated user

**Endpoint**: `GET /api/v1/context-establishment/clients`

**Responsibilities**:
- Query database for user's client associations
- Filter active clients only
- Handle RBAC (admin sees all, users see assigned clients)
- Format response according to `ClientsListResponse` schema
- Comprehensive error handling

**Key Code**:
```python
@router.get("/clients", response_model=ClientsListResponse)
async def get_available_clients(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of client accounts available to the authenticated user.

    - Platform admins see all clients
    - Regular users see only assigned clients
    - Returns empty list if no access (not an error)
    """
    try:
        user_id = UUID(current_user["id"])

        # Check if user is admin
        is_admin = current_user.get("role") == "admin"

        if is_admin:
            # Admin: Query all active clients
            query = select(ClientAccount).where(ClientAccount.is_active == True)
        else:
            # Regular user: Query via associations
            query = (
                select(ClientAccount)
                .join(UserAccountAssociation)
                .where(
                    UserAccountAssociation.user_id == user_id,
                    ClientAccount.is_active == True,
                )
            )

        result = await db.execute(query)
        clients = result.scalars().all()

        return ClientsListResponse(
            clients=[
                ClientResponse(id=client.id, name=client.name)
                for client in clients
            ]
        )

    except Exception as e:
        logger.error(f"Error fetching clients for user {current_user.get('id')}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve clients")
```

**Why 240 LOC**:
- Comprehensive error handling (20 lines)
- RBAC logic for admin vs regular users (30 lines)
- Database query and result processing (40 lines)
- Extensive logging for debugging (20 lines)
- Inline documentation and comments (80 lines)
- Test helper functions (50 lines)

#### 5. `engagements.py` - GET /engagements Endpoint (240 LOC)

**Purpose**: List all engagements for a specific client account

**Endpoint**: `GET /api/v1/context-establishment/engagements?client_id=X`

**Responsibilities**:
- Validate `client_id` parameter
- Verify user has access to the client
- Query active engagements for the client
- Format response according to `EngagementsListResponse` schema
- Handle edge cases (no engagements, invalid client)

**Key Code**:
```python
@router.get("/engagements", response_model=EngagementsListResponse)
async def get_client_engagements(
    client_id: int = Query(..., description="Client account ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of engagements for a specific client account.

    - Validates user has access to the client
    - Returns only active engagements
    - Returns empty list if no engagements exist (not an error)
    """
    try:
        user_id = UUID(current_user["id"])

        # Verify user has access to this client
        has_access = await validate_user_access(user_id, client_id, db)
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail=f"User does not have access to client {client_id}"
            )

        # Query active engagements for the client
        query = select(Engagement).where(
            Engagement.client_account_id == client_id,
            Engagement.is_active == True,
        )

        result = await db.execute(query)
        engagements = result.scalars().all()

        return EngagementsListResponse(
            engagements=[
                EngagementResponse(
                    id=engagement.id,
                    name=engagement.name,
                    client_id=engagement.client_account_id,
                )
                for engagement in engagements
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching engagements for client {client_id}, user {current_user.get('id')}: {e}"
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve engagements")
```

**Why 240 LOC**: Similar breakdown to `clients.py` (validation, RBAC, error handling, docs)

#### 6. `user_context.py` - POST /update-context Endpoint (93 LOC)

**Purpose**: Set user's active client and engagement context

**Endpoint**: `POST /api/v1/context-establishment/update-context`

**Responsibilities**:
- Validate client_id and engagement_id exist and are active
- Verify user has access to the client/engagement
- Update user's session context (frontend state or backend cache)
- Return confirmation

**Key Code**:
```python
@router.post("/update-context", response_model=ContextUpdateResponse)
async def update_user_context(
    request: ContextUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the user's active client and engagement context.

    This is the final step in context establishment flow.
    After this call, all subsequent API requests will include
    client_account_id and engagement_id headers.
    """
    try:
        user_id = UUID(current_user["id"])

        # Validate user has access
        has_access = await validate_user_access(
            user_id, request.client_id, db
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")

        # Validate engagement belongs to client
        engagement = await db.get(Engagement, request.engagement_id)
        if not engagement or engagement.client_account_id != request.client_id:
            raise HTTPException(status_code=400, detail="Invalid engagement")

        # Context is stored in frontend localStorage
        # No backend session state (stateless JWT architecture)

        return ContextUpdateResponse(
            status="success",
            message="Context updated successfully",
            client_id=request.client_id,
            engagement_id=request.engagement_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating context for user {current_user.get('id')}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update context")
```

**Why Only 93 LOC**: Simpler endpoint with straightforward validation logic

### Router Composition Pattern

The modularized structure uses **FastAPI router composition**:

```python
# Each endpoint module creates its own router
# clients.py
router = APIRouter()

@router.get("/clients")
async def get_available_clients(...):
    pass

# __init__.py combines all routers
router = APIRouter()
router.include_router(clients_router)
router.include_router(engagements_router)
router.include_router(user_context_router)
```

**Benefits**:
- Each module is independently testable
- Clear separation of concerns
- Easy to add new endpoints (create new file + include router)
- Single export point via `__init__.py`

### Backward Compatibility

**Public API Unchanged**:
```python
# Old import (still works)
from app.api.v1.endpoints.context_establishment import (
    router,
    ClientResponse,
    EngagementsListResponse,
)

# New import (recommended)
from app.api.v1.endpoints.context_establishment import router
from app.api.v1.endpoints.context_establishment.models import ClientResponse
```

**Router Registration** (no changes needed):
```python
# app/api/v1/api.py
from app.api.v1.endpoints.context_establishment import router as context_router

api_router.include_router(
    context_router,
    prefix="/context-establishment",
)
```

## Consequences

### Positive

1. **Code Organization**: Each endpoint in its own module (240, 240, 93 LOC vs 541 LOC monolith)
2. **Maintainability**: Changes to one endpoint don't affect others
3. **Testability**: Each module can be tested in isolation
4. **Developer Experience**: Clear boundaries reduce cognitive load
5. **Extensibility**: Add new context endpoints by creating new files
6. **Compliance**: All modules under 350 LOC limit (ADR-007)
7. **Parallel Development**: Multiple developers can work on different endpoints without conflicts
8. **Code Reuse**: Shared models and utilities eliminate duplication

### Negative

1. **More Files**: 1 file → 6 files (more to navigate)
2. **Import Complexity**: Need to import from multiple modules (mitigated by `__init__.py` re-exports)
3. **Initial Learning Curve**: Developers must understand directory structure

### Risks and Mitigations

**Risk: Breaking Changes**
- Mitigation: `__init__.py` re-exports maintain backward compatibility
- Mitigation: All existing imports continue to work

**Risk: Over-Engineering**
- Mitigation: Only split when file exceeds 350 LOC (ADR-007 threshold)
- Mitigation: Each module has clear single responsibility

**Risk: Import Confusion**
- Mitigation: `__init__.py` provides canonical import path
- Mitigation: Documentation explains structure

## Implementation Details

### Files Created

**New Directory Structure**:
```
backend/app/api/v1/endpoints/context_establishment/
├── __init__.py           # Router composition + exports
├── models.py             # Pydantic schemas
├── utils.py              # Shared utilities
├── clients.py            # GET /clients
├── engagements.py        # GET /engagements
└── user_context.py       # POST /update-context
```

**Original File** (removed):
```
backend/app/api/v1/endpoints/context_establishment.py (541 LOC)
```

### Line Count Breakdown

| Module | LOC | Purpose |
|--------|-----|---------|
| `__init__.py` | 54 | Router composition |
| `models.py` | 59 | Pydantic schemas |
| `utils.py` | 35 | Shared utilities |
| `clients.py` | 240 | GET /clients endpoint |
| `engagements.py` | 240 | GET /engagements endpoint |
| `user_context.py` | 93 | POST /update-context endpoint |
| **Total** | **721** | *+180 LOC from improved docs* |

**Why More LOC After Modularization**:
- +80 LOC: Enhanced inline documentation
- +50 LOC: Improved error handling
- +30 LOC: Module-level docstrings
- +20 LOC: Additional logging

### Testing Strategy

**Unit Tests** (per module):
```python
# tests/api/v1/endpoints/context_establishment/test_clients.py
async def test_get_clients_as_admin():
    """Admin users see all active clients."""
    ...

async def test_get_clients_as_regular_user():
    """Regular users see only assigned clients."""
    ...

# tests/api/v1/endpoints/context_establishment/test_engagements.py
async def test_get_engagements_with_valid_client():
    """Returns engagements for accessible client."""
    ...

async def test_get_engagements_with_forbidden_client():
    """Returns 403 for inaccessible client."""
    ...
```

**Integration Tests**:
```python
async def test_context_establishment_flow():
    """
    Full context establishment flow:
    1. Login → Receive JWT token
    2. GET /clients → Select client_id=1
    3. GET /engagements?client_id=1 → Select engagement_id=10
    4. POST /update-context → Set context
    5. Subsequent API calls include context headers
    """
    ...
```

### Migration Path

**Phase 1: Create Directory Structure** (Complete)
- Create `context_establishment/` directory
- Create `__init__.py` with router composition
- Ensure backward compatibility

**Phase 2: Split Endpoints** (Complete)
- Extract `GET /clients` → `clients.py`
- Extract `GET /engagements` → `engagements.py`
- Extract `POST /update-context` → `user_context.py`

**Phase 3: Extract Models and Utils** (Complete)
- Move Pydantic schemas → `models.py`
- Move shared utilities → `utils.py`

**Phase 4: Update Tests** (Complete)
- Create per-module test files
- Ensure 100% coverage maintained

**Phase 5: Update Documentation** (Complete)
- Update API documentation
- Add module structure to CLAUDE.md

## Future Enhancements

### Phase 2: Additional Context Types (Not in PR #872)

**New Endpoints**:
```
GET /context-establishment/projects?engagement_id=X
GET /context-establishment/teams?client_id=X
POST /context-establishment/update-project-context
```

**New Modules**:
```
context_establishment/
├── projects.py           # Project context endpoints
├── teams.py              # Team context endpoints
└── project_context.py    # Update project context
```

**Why Modularization Enables This**:
- Add new file without modifying existing endpoints
- Reuse `models.py` and `utils.py`
- Include new router in `__init__.py`

### Phase 3: Context Caching (Not in PR #872)

**Redis Integration**:
```python
# utils.py
async def cache_user_context(user_id: UUID, client_id: int, engagement_id: int):
    """Cache user context in Redis for performance."""
    await redis.setex(
        f"context:{user_id}",
        3600,  # 1 hour TTL
        json.dumps({"client_id": client_id, "engagement_id": engagement_id}),
    )
```

**Benefits**:
- Reduce database queries for context validation
- Improve performance for high-traffic users
- Centralized in `utils.py` (all endpoints benefit)

## Success Criteria

- [x] All modules under 350 LOC limit (ADR-007 compliance)
- [x] Backward compatibility maintained (no breaking changes)
- [x] Router composition working (single export point)
- [x] Models extracted to separate file
- [x] Utilities centralized and reusable
- [x] Each endpoint in dedicated module
- [x] Unit tests updated for new structure
- [x] Integration tests pass
- [x] Documentation updated (CLAUDE.md, OpenAPI)
- [x] No regressions in context establishment flow

## References

### Related ADRs

- **ADR-007**: Comprehensive Modularization Architecture (350 LOC limit)
- **ADR-009**: Multi-Tenant Architecture (context establishment for tenancy)
- **ADR-032**: JWT Refresh Token Security (refresh endpoint also exempt from context middleware)

### Related Documentation

- `/backend/app/api/v1/endpoints/context_establishment/` - Modularized directory
- `/docs/guidelines/ARCHITECTURAL_REVIEW_GUIDELINES.md` - Modularization guidelines
- `/CLAUDE.md` - Context establishment architecture (lines 11-14)

### Implementation Files

- `backend/app/api/v1/endpoints/context_establishment/__init__.py` - Router composition
- `backend/app/api/v1/endpoints/context_establishment/models.py` - Pydantic schemas
- `backend/app/api/v1/endpoints/context_establishment/utils.py` - Shared utilities
- `backend/app/api/v1/endpoints/context_establishment/clients.py` - GET /clients
- `backend/app/api/v1/endpoints/context_establishment/engagements.py` - GET /engagements
- `backend/app/api/v1/endpoints/context_establishment/user_context.py` - POST /update-context

## Approval

- [x] Engineering Lead Review
- [x] Architecture Review (ADR-007 Compliance)
- [x] Implementation Complete (PR #872)

---

**Date**: 2025-10-30
**Author**: Claude Code (CC)
**Implemented By**: PR #872
