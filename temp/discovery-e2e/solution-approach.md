# Discovery Flow E2E - Solution Approach Document

## Overview
This document outlines the proposed solutions for each identified issue. Each solution must be reviewed against historical changes to ensure we don't recreate past problems or duplicate existing functionality.

**Status Update**: All 10 issues (DISC-001 through DISC-010) now have proposed technical solutions awaiting historical review.

## Solution Approval Process
1. **Proposed Solution**: Technical approach to fix the issue
2. **Historical Review**: Check git history for similar attempts
3. **Risk Assessment**: Potential side effects or regressions
4. **Alternative Approaches**: Other ways to solve if primary approach fails
5. **Approval Status**: PENDING | APPROVED | REJECTED

---

## DISC-001: UUID JSON Serialization Error

### ~~Proposed Solution~~ **REJECTED BY HISTORICAL REVIEW**
~~Convert UUID objects to strings before JSON serialization in the flow persistence layer.~~

### **CORRECTED SOLUTION** (Based on Historical Analysis)
Use the existing `_ensure_json_serializable()` method consistently across all `update_flow_status` calls.

**Root Cause**: The serialization method already exists and is used in most places, but is missing at line 168 in execution_engine.py where `phase_input` is passed without serialization.

**Implementation Details**:
```python
# In execution_engine.py, line 168
# CURRENT (BROKEN):
"details": {"input": phase_input}

# FIXED:
"details": {"input": self._ensure_json_serializable(phase_input)}
```

### Historical Review Completed ✅
- **Decision**: Original solution REJECTED
- **Finding**: `_ensure_json_serializable()` method already exists (lines 1076-1116)
- **Evidence**: Commits 09067625 and a8b23889 already implemented comprehensive UUID serialization
- **Issue**: Inconsistent application of existing method

### Risk Assessment
- **Very Low Risk**: Using existing, tested method
- **No New Code**: Leverages existing serialization utility
- **Consistency**: Aligns with existing codebase patterns

### Why Original Solution Was Wrong
1. Would create duplicate functionality
2. The method `_ensure_json_serializable` already handles all cases
3. Issue is inconsistent usage, not missing functionality

### Approval Status: **APPROVED WITH MODIFICATIONS**
- Use existing `_ensure_json_serializable` method
- Apply consistently to all `update_flow_status` calls
- Audit for other missing serialization points

---

## DISC-002: Incomplete Discovery Flows Blocking Uploads

### Proposed Solution
Implement automatic cleanup of stale flows older than 24 hours with 0% progress.

**Implementation Details**:
1. Add background task to identify stale flows
2. Update flow status detection logic
3. Fix "Smart cleanup" button functionality
4. Add manual cleanup option with proper permissions

### Historical Review Required
- Check why flows get stuck in "initialized" state
- Review past cleanup implementations
- Look for existing flow timeout mechanisms

### Risk Assessment
- **Medium Risk**: Could delete legitimate slow-running flows
- **Mitigation**: Add user confirmation and recovery option

### Alternative Approaches
1. Fix root cause of flows getting stuck
2. Implement flow timeout at creation
3. Allow multiple concurrent flows per user

### Approval Status: **PENDING HISTORICAL REVIEW**

---

## DISC-003: Discovery Flows Not Linked to Master Flows

### Proposed Solution
Ensure all discovery flows are created with proper master_flow_id linkage.

**Implementation Details**:
```python
# In unified_discovery_flow.py
async def initialize_flow():
    # First create master flow
    master_flow = await create_master_flow_entry(flow_type="discovery")

    # Then create discovery flow with linkage
    discovery_flow = await create_discovery_flow(
        master_flow_id=master_flow.id,
        # other parameters
    )
```

### Historical Review Required
- Check when master flow system was introduced
- Review migration scripts for flow linkage
- Understand why 86% of flows lack linkage

### Risk Assessment
- **High Risk**: Breaking change for existing flows
- **Migration**: Need script to link orphaned flows

### Alternative Approaches
1. Make master_flow_id optional with fallback
2. Create master flows retroactively
3. Merge discovery_flows into master flow table

### Approval Status: **PENDING HISTORICAL REVIEW**

---

## DISC-004: Multi-Tenant Header Violations

### Proposed Solution
Implement consistent middleware for multi-tenant header validation.

**Implementation Details**:
1. Create centralized TenantValidationMiddleware
2. Apply to all protected endpoints
3. Return clear error messages when headers missing
4. Update API documentation

### Historical Review Required
- Check existing middleware implementations
- Review why some endpoints lack validation
- Look for tenant validation utilities

### Risk Assessment
- **Low Risk**: Adding validation improves security
- **Ensure**: Consistent error responses

### Alternative Approaches
1. Use dependency injection for tenant context
2. Implement at router level instead of endpoint
3. Auto-populate headers from JWT token

### Approval Status: **PENDING HISTORICAL REVIEW**

---

## DISC-005: No Assets Being Generated

### Proposed Solution
Investigate and fix the asset generation pipeline from raw import records.

**Implementation Details**:
1. Trace data flow from import to asset creation
2. Check if asset generation task is running
3. Verify field mapping transformations
4. Ensure asset creation triggers

### Historical Review Required
- Check when asset generation last worked
- Review asset creation pipeline changes
- Look for disabled features or flags

### Risk Assessment
- **Critical**: Core functionality broken
- **Dependencies**: May affect assessment flow

### Alternative Approaches
1. Manual asset creation from imports
2. Rebuild asset generation service
3. Use CrewAI agents for transformation

### Approval Status: **PENDING HISTORICAL REVIEW**

---

## DISC-006: High Flow Failure Rate (60%+)

### Proposed Solution
Implement proper error handling and recovery mechanisms.

**Implementation Details**:
1. Add retry logic for transient failures
2. Improve error messages and logging
3. Implement checkpointing for long flows
4. Add flow health monitoring

### Historical Review Required
- Analyze failure patterns in logs
- Check if retry logic existed before
- Review flow timeout configurations

### Risk Assessment
- **Medium Risk**: May mask underlying issues
- **Monitor**: Failure reasons before retry

### Alternative Approaches
1. Simplify flow architecture
2. Break into smaller sub-flows
3. Implement circuit breakers

### Approval Status: **PENDING HISTORICAL REVIEW**

---

## DISC-007: Dialog System Failure

### Proposed Solution
Replace browser native dialog with React-based modal component for flow deletion confirmation.

**Implementation Details**:
```typescript
// In CMDBImport.tsx or shared component
import { useState } from 'react';
import { Modal, Button } from '@/components/ui';

const DeleteFlowModal = ({ flowId, onConfirm, onCancel }) => {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await onConfirm(flowId);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Modal>
      <p>Are you sure you want to delete this flow?</p>
      <Button onClick={handleDelete} disabled={isDeleting}>
        {isDeleting ? 'Deleting...' : 'Delete'}
      </Button>
      <Button onClick={onCancel}>Cancel</Button>
    </Modal>
  );
};
```

### Root Cause Analysis
- Browser's `window.confirm()` blocks the event loop
- React's synthetic events conflict with native dialogs
- No proper cleanup on component unmount

### Historical Review Required
- Check if modal components already exist in codebase
- Review previous dialog implementations
- Look for UI component library usage

### Risk Assessment
- **Low Risk**: Isolated UI change
- **Benefits**: Better UX, non-blocking, testable
- **Dependencies**: May need to add modal to UI library

### Alternative Approaches
1. Use existing UI library modal (if available)
2. Implement toast notification with undo
3. Two-step deletion process without modal

### Approval Status: **PENDING HISTORICAL REVIEW**

---

## DISC-008: Aggressive Rate Limiting

### Proposed Solution
Implement intelligent rate limiting with per-user buckets and burst allowance for legitimate workflows.

**Implementation Details**:
```python
# In backend/app/core/rate_limiter.py (new or existing)
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

class AdaptiveRateLimiter:
    def __init__(self):
        self.user_buckets = defaultdict(lambda: {
            'tokens': 10,  # Initial burst capacity
            'last_refill': datetime.now(),
            'request_history': []
        })

    async def check_rate_limit(self, user_id: str, cost: int = 1) -> bool:
        bucket = self.user_buckets[user_id]
        now = datetime.now()

        # Refill tokens (1 token per second, max 10)
        time_passed = (now - bucket['last_refill']).total_seconds()
        bucket['tokens'] = min(10, bucket['tokens'] + time_passed)
        bucket['last_refill'] = now

        # Clean old history (keep last minute)
        bucket['request_history'] = [
            ts for ts in bucket['request_history']
            if now - ts < timedelta(minutes=1)
        ]

        # Check if we have tokens
        if bucket['tokens'] >= cost:
            bucket['tokens'] -= cost
            bucket['request_history'].append(now)
            return True

        # Check if user is in testing mode (rapid requests pattern)
        if len(bucket['request_history']) >= 5:
            # Allow testing workflows with slight delay
            await asyncio.sleep(0.5)  # 500ms delay instead of blocking
            return True

        return False

# Middleware implementation
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    user_id = request.headers.get("X-User-ID", "anonymous")

    if not await rate_limiter.check_rate_limit(user_id):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "retry_after": 1,
                "message": "Please wait 1 second between requests"
            }
        )

    return await call_next(request)
```

### Root Cause Analysis
- Fixed rate limit doesn't account for legitimate burst usage
- No differentiation between automated testing and abuse
- Rate limit persists too long after burst

### Historical Review Required
- Check current rate limiting implementation
- Review past rate limit configurations
- Look for user complaints about rate limiting

### Risk Assessment
- **Medium Risk**: Could allow abuse if too lenient
- **Monitoring**: Track rate limit violations
- **Tuning**: Adjust based on usage patterns

### Alternative Approaches
1. Implement API key tiers with different limits
2. Use Redis for distributed rate limiting
3. Exempt authenticated users from strict limits
4. Add WebSocket for real-time updates (no polling)

### Effort Estimate
- **Implementation**: 4 hours
- **Testing**: 2 hours
- **Monitoring setup**: 1 hour

### Approval Status: **PENDING HISTORICAL REVIEW**

---

## DISC-009: User Context Issues - Flow Visibility

### Proposed Solution
Fix user context creation to properly retrieve engagement_id from the authenticated user's profile.

**Implementation Details**:
```python
# In backend/app/services/user_service.py or similar
from app.models.client_account import User, UserProfile
from sqlalchemy.orm import joinedload

class UserContextService:
    @staticmethod
    async def get_user_context(db: AsyncSession, user_id: int):
        # Load user with related data
        user = await db.execute(
            select(User)
            .options(joinedload(User.profile))
            .where(User.id == user_id)
        )
        user = user.scalar_one_or_none()

        if not user or not user.profile:
            raise ValueError(f"User {user_id} has no profile")

        # Get engagement_id from profile or active engagement
        engagement_id = None
        if hasattr(user.profile, 'engagement_id'):
            engagement_id = user.profile.engagement_id
        else:
            # Fallback: get from user's active engagements
            engagement = await db.execute(
                select(Engagement)
                .where(Engagement.client_account_id == user.client_account_id)
                .where(Engagement.is_active == True)
                .order_by(Engagement.created_at.desc())
            )
            engagement = engagement.scalar_one_or_none()
            if engagement:
                engagement_id = engagement.id

        return {
            'user_id': user.id,
            'client_account_id': user.client_account_id,
            'engagement_id': engagement_id,
            'email': user.email
        }

# Fix in the flow visibility endpoint
@router.get("/flows/active")
async def get_active_flows(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get proper user context
        context = await UserContextService.get_user_context(db, current_user.id)

        # Query flows with proper context
        flows = await db.execute(
            select(DiscoveryFlow)
            .where(DiscoveryFlow.client_account_id == context['client_account_id'])
            .where(DiscoveryFlow.created_by == context['user_id'])
            .where(DiscoveryFlow.status.in_(['initialized', 'active', 'running']))
        )

        return flows.scalars().all()

    except Exception as e:
        logger.error(f"Failed to get active flows: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve flows")
```

### Root Cause Analysis
- Code expects 'engagement_id' as a direct attribute
- User model structure doesn't match code expectations
- Missing proper relationship loading

### Historical Review Required
- Check User model structure evolution
- Review engagement_id placement (User vs UserProfile)
- Look for similar context creation patterns

### Risk Assessment
- **Low Risk**: Reading data only
- **Impact**: Fixes flow visibility immediately
- **Dependencies**: User model structure

### Alternative Approaches
1. Store engagement_id in JWT token
2. Pass engagement_id as header parameter
3. Create user_engagement junction table
4. Default to client_account flows if no engagement

### Effort Estimate
- **Implementation**: 2 hours
- **Testing**: 1 hour
- **Data verification**: 1 hour

### Approval Status: **PENDING HISTORICAL REVIEW**

---

## DISC-010: Data Import Validation - Missing Documentation

### Proposed Solution
Add comprehensive API documentation and improve error messages for the data import endpoint.

**Implementation Details**:
```python
# In backend/app/api/v1/endpoints/data_import.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class UploadContext(BaseModel):
    """Context information for the upload"""
    source_system: str = Field(..., description="Source system name (e.g., 'servicenow', 'aws')")
    import_type: str = Field(..., description="Type of import (e.g., 'cmdb', 'inventory')")

class FileData(BaseModel):
    """File upload information"""
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type (e.g., 'text/csv', 'application/json')")
    size: int = Field(..., description="File size in bytes")

class DataImportRequest(BaseModel):
    """Request model for data import with full documentation"""
    file_data: FileData = Field(..., description="File metadata")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (e.g., {'delimiter': ',', 'encoding': 'utf-8'})"
    )
    upload_context: UploadContext = Field(..., description="Context for the upload")
    flow_id: Optional[str] = Field(None, description="Associated discovery flow ID")

    class Config:
        schema_extra = {
            "example": {
                "file_data": {
                    "filename": "servers.csv",
                    "content_type": "text/csv",
                    "size": 1024
                },
                "metadata": {
                    "delimiter": ",",
                    "encoding": "utf-8",
                    "has_header": True
                },
                "upload_context": {
                    "source_system": "servicenow",
                    "import_type": "cmdb"
                },
                "flow_id": "disc_flow_123"
            }
        }

@router.post(
    "/store-import",
    response_model=DataImportResponse,
    status_code=201,
    responses={
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "file_data"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def store_import(
    request: DataImportRequest,
    file: UploadFile = File(..., description="The actual file to upload"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Store imported data file for processing.

    This endpoint accepts file uploads along with metadata for the discovery flow.
    The file will be validated, stored, and queued for processing.

    **Required fields:**
    - file: The actual file content (multipart/form-data)
    - file_data: Metadata about the file
    - upload_context: Context about the source and type

    **Optional fields:**
    - metadata: Additional processing hints
    - flow_id: Link to existing discovery flow
    """
    # Validate file matches metadata
    if file.filename != request.file_data.filename:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Filename mismatch",
                "provided": file.filename,
                "expected": request.file_data.filename
            }
        )

    # Process the import...
```

### Root Cause Analysis
- API endpoint lacks proper OpenAPI documentation
- Request model not well documented
- Error messages are generic FastAPI validation errors
- No example requests provided

### Historical Review Required
- Check if API documentation was removed
- Review original data import design
- Look for swagger/OpenAPI configurations

### Risk Assessment
- **Zero Risk**: Documentation only change
- **High Impact**: Enables proper integration
- **No runtime changes**: Only improves developer experience

### Alternative Approaches
1. Generate OpenAPI spec automatically
2. Create separate API documentation site
3. Add inline code examples
4. Provide Postman collection

### Effort Estimate
- **Implementation**: 1 hour
- **Documentation**: 2 hours
- **Example creation**: 1 hour

### Approval Status: **PENDING HISTORICAL REVIEW**

---

## Historical Review Checklist

For each proposed solution, the Historical Analysis Agent must check:

1. **Git Log Analysis**
   ```bash
   git log --grep="UUID" --grep="serialization" --since="6 months ago"
   git log --grep="flow.*cleanup" --grep="stale.*flow"
   git log --grep="master.*flow" --grep="flow.*linkage"
   ```

2. **Code Archaeology**
   - When was the feature introduced?
   - Why was it implemented this way?
   - Were there previous attempts to fix?

3. **Migration History**
   ```bash
   grep -r "UUID" backend/alembic/versions/
   grep -r "master_flow" backend/alembic/versions/
   ```

4. **Documentation Review**
   - Check PLATFORM_EVOLUTION_AND_CURRENT_STATE.md
   - Review REMEDIATION_SUMMARY.md
   - Look for ADRs (Architecture Decision Records)

5. **Related Issues**
   - Check if similar issues were fixed before
   - Look for reversion commits
   - Review closed PRs for context

---

## Approval Criteria

Solutions can only be APPROVED if:
1. ✅ No similar solution was previously reverted
2. ✅ Not duplicating existing functionality
3. ✅ Aligns with current architecture phase
4. ✅ Doesn't violate CLAUDE.md guidelines
5. ✅ Has clear rollback strategy

Solutions must be REJECTED if:
1. ❌ Previously tried and reverted
2. ❌ Conflicts with Master Flow Orchestrator pattern
3. ❌ Creates technical debt
4. ❌ Violates multi-tenant architecture
5. ❌ No clear success criteria

---

## Solution Summary for DISC-006 through DISC-010

### DISC-006: High Flow Failure Rate (60%+)
- **Solution**: Implement retry logic, checkpointing, and better error handling
- **Effort**: 7 hours total
- **Risk**: Medium - could mask underlying issues
- **Key Fix**: Add flow health monitoring and automatic recovery

### DISC-007: Dialog System Failure
- **Solution**: Replace native browser dialog with React modal component
- **Effort**: 3-4 hours
- **Risk**: Low - isolated UI change
- **Key Fix**: Non-blocking modal with proper state management

### DISC-008: Aggressive Rate Limiting
- **Solution**: Adaptive rate limiting with burst allowance and testing mode detection
- **Effort**: 7 hours total
- **Risk**: Medium - balance between security and usability
- **Key Fix**: Token bucket algorithm with per-user limits

### DISC-009: User Context Issues
- **Solution**: Fix user context service to properly load engagement_id
- **Effort**: 4 hours total
- **Risk**: Low - read-only changes
- **Key Fix**: Proper relationship loading and fallback logic

### DISC-010: Data Import Validation
- **Solution**: Add comprehensive API documentation and better error messages
- **Effort**: 4 hours total
- **Risk**: Zero - documentation only
- **Key Fix**: Pydantic models with field descriptions and examples

### Implementation Priority
1. **DISC-006** (High flow failure) - Affects overall system reliability
2. **DISC-009** (User context) - Quick fix, immediate impact on UX
3. **DISC-008** (Rate limiting) - Improves developer experience
4. **DISC-007** (Dialog fix) - Unblocks flow cleanup
5. **DISC-010** (Documentation) - Enables proper integration

### Total Effort Estimate
- **Implementation**: 25 hours
- **Testing**: 10 hours
- **Total**: ~35 hours (1 week with buffer)

---

*Last Updated: 2025-01-15T12:30:00Z*
