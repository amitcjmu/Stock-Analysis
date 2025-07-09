# Backend Session-to-Flow Refactor Plan

**Document Version**: 1.0  
**Date**: July 9, 2025  
**Status**: Critical - Required for Complete Session Cleanup  
**Impact**: High - Affects Authentication, Context Management, and API Responses

## Executive Summary

The platform's session-to-flow migration remains **incomplete in the backend**, despite documentation claiming completion. Critical user-facing functionality (authentication context, admin dashboard) is currently working via frontend compatibility layers, but the backend still uses session-based schemas and APIs.

This document provides a comprehensive technical plan to complete the backend refactoring from session-based to flow-based architecture.

## Current State Analysis

### ✅ **Already Migrated (Working)**
- **Database Models**: Core models (`Asset`, `DiscoveryFlow`) use `flow_id` as primary identifier
- **CrewAI Integration**: Flow-based execution patterns implemented
- **Frontend**: Modern AuthContext uses flow-based patterns with compatibility layer

### ⚠️ **Incomplete/Mixed State**
- **API Responses**: `/context/me` still returns session data instead of flow data
- **Pydantic Schemas**: Session-based schemas still active and in use
- **Authentication Context**: Backend context resolution uses session-based logic

### ❌ **Needs Refactoring (Critical)**
- **Core Schemas**: `UserContext`, `SessionBase` still define session-centric data structures
- **API Endpoints**: Context and admin endpoints return session data
- **Data Import Validation**: Uses session-based tracking instead of flow-based

## Critical Issues Identified

### Issue 1: Authentication Context Mismatch
**Problem**: Frontend expects flow-based context, backend returns session-based context.

**Current Backend Response** (`/api/v1/context/me`):
```json
{
  "user": {...},
  "client": {...},
  "engagement": {...},
  "session": {
    "id": "58467010-6a72-44e8-ba37-cc0238724455",
    "name": "Admin Session - Azure Transformation 2025",
    "engagement_id": "58467010-6a72-44e8-ba37-cc0238724455"
  }
}
```

**Required Flow-Based Response**:
```json
{
  "user": {...},
  "client": {...},
  "engagement": {...},
  "active_flows": [
    {
      "id": "58467010-6a72-44e8-ba37-cc0238724455",
      "name": "Discovery Flow - Azure Transformation 2025",
      "flow_type": "discovery",
      "status": "active",
      "engagement_id": "58467010-6a72-44e8-ba37-cc0238724455"
    }
  ]
}
```

### Issue 2: Schema Definitions Still Session-Centric
**Problem**: Core Pydantic schemas still define session-based data structures.

**Files Requiring Updates**:
- `app/schemas/context.py` - `UserContext` includes `session` field
- `app/schemas/session.py` - Complete session management schemas
- `app/schemas/data_import_schemas.py` - Validation session tracking

## Detailed Refactoring Plan

### Phase 1: Schema Refactoring (Priority: CRITICAL)

#### 1.1 Update Core Context Schema
**File**: `backend/app/schemas/context.py`

**Current**:
```python
class UserContext(BaseModel):
    user: Dict[str, Any]
    client: Optional[ClientBase] = None
    engagement: Optional[EngagementBase] = None
    session: Optional[SessionBase] = None
    available_sessions: List[SessionBase] = Field(default_factory=list)
```

**Refactor To**:
```python
class FlowBase(BaseModel):
    """Flow information."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    flow_type: str  # discovery, assessment, planning, execution, etc.
    status: str     # active, completed, paused, failed
    engagement_id: UUID
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class UserContext(BaseModel):
    user: Dict[str, Any]
    client: Optional[ClientBase] = None
    engagement: Optional[EngagementBase] = None
    active_flows: List[FlowBase] = Field(default_factory=list)
    current_flow: Optional[FlowBase] = None
```

#### 1.2 Replace Session Schema with Flow Schema
**Action**: Replace `backend/app/schemas/session.py` with `backend/app/schemas/flow.py`

**New Flow Schema**:
```python
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum

class FlowType(str, Enum):
    DISCOVERY = "discovery"
    ASSESSMENT = "assessment" 
    PLANNING = "planning"
    EXECUTION = "execution"
    MODERNIZE = "modernize"
    FINOPS = "finops"
    OBSERVABILITY = "observability"
    DECOMMISSION = "decommission"

class FlowStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"
    CANCELLED = "cancelled"

class FlowBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    flow_type: FlowType
    status: FlowStatus = FlowStatus.PENDING
    engagement_id: UUID
    created_by: UUID
    metadata: Optional[Dict[str, Any]] = None

class FlowCreate(BaseModel):
    name: str
    flow_type: FlowType
    engagement_id: UUID
    metadata: Optional[Dict[str, Any]] = None

class FlowUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[FlowStatus] = None
    metadata: Optional[Dict[str, Any]] = None

class Flow(FlowBase):
    created_at: datetime
    updated_at: datetime

class FlowInDB(Flow):
    pass

class FlowList(BaseModel):
    flows: List[Flow]
    total: int
    engagement_id: UUID
```

#### 1.3 Update Data Import Schemas
**File**: `backend/app/schemas/data_import_schemas.py`

**Changes**:
```python
# Current
validation_session_id: Optional[str] = None

class ValidationSession(BaseModel):
    session_id: str
    status: str
    created_at: datetime
    
# Refactor To
validation_flow_id: Optional[str] = None

class ValidationFlow(BaseModel):
    flow_id: str
    flow_type: FlowType = FlowType.DISCOVERY
    status: FlowStatus
    created_at: datetime
```

### Phase 2: API Endpoint Updates (Priority: HIGH)

#### 2.1 Update Context Endpoints
**File**: `backend/app/api/v1/endpoints/context/api/user_routes.py`

**Update `/me` endpoint**:
```python
@router.get(
    "/me",
    response_model=UserContext,
    summary="Get current user context",
    description="Get complete context for the current user including client, engagement, and active flows."
)
async def get_user_context(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserContext:
    """Get complete context for the current user"""
    try:
        service = UserService(db)
        return await service.get_user_context_with_flows(current_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user context: {str(e)}"
        )
```

#### 2.2 Replace Session Switch with Flow Management
**Replace**:
```python
@router.post("/session/switch")
async def switch_session(...)
```

**With**:
```python
@router.post("/flow/activate")
async def activate_flow(
    request: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Activate a specific flow for the current user."""
    flow_id = request.get("flow_id")
    
    if not flow_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="flow_id is required"
        )
    
    try:
        service = UserService(db)
        result = await service.activate_user_flow(current_user, flow_id)
        
        return {
            "status": "success",
            "message": "Flow activated successfully",
            "flow_id": flow_id,
            "flow_type": result.get("flow_type"),
            "engagement_id": result.get("engagement_id")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error activating flow: {str(e)}"
        )
```

#### 2.3 Update Admin Session Comparison Endpoints
**Files**: 
- `backend/app/api/v1/admin/session_comparison.py`
- `backend/app/api/v1/admin/session_comparison_modular.py`

**Replace session comparison with flow comparison**:
```python
# Old
@router.get("/sessions/comparison")
async def get_sessions_for_comparison(...)

# New
@router.get("/flows/comparison")
async def get_flows_for_comparison(
    engagement_id: Optional[UUID] = None,
    flow_type: Optional[FlowType] = None,
    status: Optional[FlowStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get flows available for comparison analysis."""
```

### Phase 3: Service Layer Updates (Priority: MEDIUM)

#### 3.1 Update UserService for Flow-Based Context
**File**: `backend/app/api/v1/endpoints/context/services/user_service.py`

**Add new method**:
```python
async def get_user_context_with_flows(self, user: User) -> UserContext:
    """Get complete user context with active flows instead of sessions."""
    try:
        # Get client and engagement (existing logic)
        client, engagement = await self._get_user_client_engagement(user)
        
        # Get active flows for the engagement
        if engagement:
            flows = await self._get_engagement_flows(engagement.id)
            current_flow = await self._get_user_active_flow(user, engagement.id)
        else:
            flows = []
            current_flow = None
        
        return UserContext(
            user={
                "id": str(user.id),
                "email": user.email,
                "role": user.role
            },
            client=client,
            engagement=engagement,
            active_flows=flows,
            current_flow=current_flow
        )
    except Exception as e:
        logger.error(f"Error getting user context with flows: {e}")
        raise

async def _get_engagement_flows(self, engagement_id: UUID) -> List[FlowBase]:
    """Get all active flows for an engagement."""
    # Implementation to query flows for engagement
    pass

async def _get_user_active_flow(self, user: User, engagement_id: UUID) -> Optional[FlowBase]:
    """Get the user's currently active flow."""
    # Implementation to get user's active flow
    pass
```

#### 3.2 Update Context Resolution in Main Application
**File**: `backend/main.py`

**Replace session_id references**:
```python
# Current (lines 455, 481, 506)
context.session_id

# Replace with
context.flow_id
```

### Phase 4: Database and Model Updates (Priority: LOW)

#### 4.1 Verify Flow-Based Models
**Ensure these models are properly using flow patterns**:
- ✅ `app/models/asset.py` - Already uses `flow_id`
- ✅ `app/models/discovery_flow.py` - Already flow-based
- ⚠️ Verify no remaining session_id foreign keys

#### 4.2 Create Missing Flow Management Tables
**If needed, create proper flow management tables**:
```sql
-- User's active flows tracking
CREATE TABLE user_active_flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    flow_id UUID NOT NULL,
    engagement_id UUID NOT NULL REFERENCES engagements(id),
    activated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_current BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, flow_id)
);

-- Flow metadata and status
CREATE TABLE flow_metadata (
    flow_id UUID PRIMARY KEY,
    flow_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    engagement_id UUID NOT NULL REFERENCES engagements(id),
    created_by UUID NOT NULL REFERENCES users(id),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Phase 5: Remove Session References (Priority: CLEANUP)

#### 5.1 Remove or Archive Session-Related Files
**Files to remove/archive**:
- `backend/app/schemas/session.py` → Archive after flow.py is implemented
- Session-related admin endpoints → Replace with flow equivalents

#### 5.2 Update Import Statements
**Find and replace session imports**:
```bash
# Search for session imports
grep -r "from.*session import" backend/app/
grep -r "import.*session" backend/app/

# Replace with flow imports
# from app.schemas.session import SessionBase
# becomes
# from app.schemas.flow import FlowBase
```

## Implementation Timeline

### Week 1: Critical Path (Authentication Fix)
- [ ] **Day 1-2**: Update `UserContext` schema to include `active_flows`
- [ ] **Day 3-4**: Update `/context/me` endpoint to return flow-based data
- [ ] **Day 5**: Test authentication flow with flow-based context

### Week 2: API Modernization  
- [ ] **Day 1-2**: Create complete `flow.py` schema
- [ ] **Day 3-4**: Update all context API endpoints
- [ ] **Day 5**: Update admin flow comparison endpoints

### Week 3: Service Layer & Testing
- [ ] **Day 1-3**: Update UserService for flow-based operations
- [ ] **Day 4-5**: Comprehensive testing of flow-based APIs

### Week 4: Cleanup & Documentation
- [ ] **Day 1-2**: Remove session references from main.py
- [ ] **Day 3-4**: Archive old session-related files
- [ ] **Day 5**: Update API documentation

## Migration Strategy

### Backward Compatibility Approach
To ensure zero downtime during migration:

1. **Dual Response Format** (Temporary):
   ```python
   # During migration, include both formats
   class UserContextMigration(BaseModel):
       user: Dict[str, Any]
       client: Optional[ClientBase] = None
       engagement: Optional[EngagementBase] = None
       # Legacy support
       session: Optional[SessionBase] = None
       available_sessions: List[SessionBase] = Field(default_factory=list)
       # New flow-based
       active_flows: List[FlowBase] = Field(default_factory=list)
       current_flow: Optional[FlowBase] = None
   ```

2. **Frontend Compatibility**: Keep frontend compatibility layer during backend migration

3. **Gradual Rollout**: Update endpoints one by one, test thoroughly

## Success Criteria

### ✅ **Phase 1 Complete When**:
- `/api/v1/context/me` returns flow-based data
- Frontend authentication works without compatibility layer
- Admin dashboard shows real data without CORS errors

### ✅ **Full Migration Complete When**:
- Zero references to "session" in active backend code (excluding database sessions)
- All API endpoints return flow-based data structures
- All schemas use flow-based patterns
- Frontend can remove session-to-flow compatibility layer

## Risk Assessment

### High Risk Items
- **Authentication Breakage**: Changing `/context/me` could break user login
- **Frontend Dependencies**: Multiple frontend components expect session data
- **Database Consistency**: Flow-based data must maintain referential integrity

### Mitigation Strategies
- **Feature Flags**: Use environment variables to toggle flow-based responses
- **Gradual Migration**: Implement dual-format responses during transition
- **Comprehensive Testing**: Test authentication flows thoroughly in development

## Post-Migration Benefits

1. **Consistency**: Frontend and backend use same data models
2. **Performance**: Eliminate frontend compatibility layer overhead
3. **Maintainability**: Single source of truth for flow-based patterns
4. **Scalability**: Flow-based architecture supports multiple concurrent flows
5. **Type Safety**: Proper TypeScript/Python type checking for flow objects

---

**Next Actions**: Begin with Phase 1 schema updates to resolve immediate authentication context mismatch issues.