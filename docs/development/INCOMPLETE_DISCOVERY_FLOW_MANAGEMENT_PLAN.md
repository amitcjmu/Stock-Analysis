# Incomplete Discovery Flow Management Implementation Plan

## 🎯 **Executive Summary**

This document outlines the implementation plan for proper incomplete discovery flow management in the AI Force Migration Platform. The goal is to ensure users can only initiate new discovery flows when no incomplete flows exist for their client/engagement context, and provide proper management tools for completing or discarding existing incomplete flows.

## 📊 **Current Implementation Analysis**

### ✅ **What's Already Implemented**

#### **Backend Validation Logic**
- **File**: `backend/app/api/v1/endpoints/data_import/handlers/import_storage_handler.py`
- **Function**: `_validate_no_incomplete_discovery_flow()`
- **Status**: ✅ **IMPLEMENTED**
- **Functionality**:
  - Validates no incomplete discovery flows exist before allowing new data imports
  - Returns 409 conflict error with detailed information about existing flows
  - Provides recommendations for user action
  - Includes session_id, current_phase, progress_percentage, and next_steps

#### **Frontend Conflict Handling**
- **File**: `src/pages/discovery/CMDBImport.tsx`
- **Status**: ✅ **PARTIALLY IMPLEMENTED**
- **Functionality**:
  - Catches 409 conflict errors during data import
  - Shows toast notifications about incomplete flows
  - Offers navigation to existing flow via window.confirm dialog
  - Basic error handling and user guidance

#### **Workflow State Management**
- **File**: `backend/app/models/workflow_state.py`
- **Status**: ✅ **IMPLEMENTED**
- **Functionality**:
  - Complete WorkflowState model with multi-tenant isolation
  - UnifiedFlowStateRepository with CRUD operations
  - `delete_flow_state()` method for flow deletion
  - Multi-tenant filtering for all operations

#### **Flow Status Tracking**
- **Files**: Multiple discovery flow status endpoints
- **Status**: ✅ **IMPLEMENTED**
- **Functionality**:
  - Flow status polling and monitoring
  - Real-time progress tracking
  - Phase completion tracking
  - Agent insights and error logging

### ❌ **What's Missing**

#### **1. Frontend: Incomplete Flow Detection & UI Blocking**
- **Status**: ❌ **NOT IMPLEMENTED**
- **Required**: 
  - Pre-upload validation to check for incomplete flows
  - Disable upload buttons when incomplete flows exist
  - Show incomplete flow warning banner
  - Redirect users to flow management interface

#### **2. Frontend: Incomplete Flow Management Interface**
- **Status**: ❌ **NOT IMPLEMENTED**
- **Required**:
  - List of incomplete flows for current context
  - Flow details view (phase, progress, last activity)
  - Continue flow functionality
  - Discard/Delete flow functionality
  - Bulk flow management

#### **3. Backend: Flow Deletion with Data Cleanup**
- **Status**: ❌ **PARTIALLY IMPLEMENTED**
- **Required**:
  - Complete flow deletion API endpoint
  - Cascade deletion of associated data (assets, mappings, etc.)
  - Data integrity validation before deletion
  - Audit logging for deletion operations

#### **4. Backend: Enhanced Flow Management APIs**
- **Status**: ❌ **NOT IMPLEMENTED**
- **Required**:
  - List incomplete flows for context
  - Get detailed flow information
  - Resume/continue flow functionality
  - Batch flow operations

#### **5. Frontend: Enhanced Discovery Dashboard Integration**
- **Status**: ❌ **PARTIALLY IMPLEMENTED**
- **Required**:
  - Show incomplete flows prominently
  - Quick actions for flow management
  - Flow status indicators
  - Navigation to appropriate flow phases

## 🏗️ **Implementation Plan**

### **Phase 1: Backend API Enhancements**

#### **Task 1.1: Enhanced Flow Management API Endpoints**
**File**: `backend/app/api/v1/endpoints/discovery_flow_management.py` (NEW)

```python
@router.get("/flows/incomplete")
async def get_incomplete_flows(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get all incomplete discovery flows for current client/engagement context"""

@router.get("/flows/{session_id}/details")
async def get_flow_details(
    session_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed information about a specific flow"""

@router.post("/flows/{session_id}/resume")
async def resume_flow(
    session_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Resume an incomplete discovery flow"""

@router.delete("/flows/{session_id}")
async def delete_flow(
    session_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Delete an incomplete discovery flow and all associated data"""

@router.post("/flows/batch-delete")
async def batch_delete_flows(
    request: BatchDeleteRequest,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Delete multiple flows in batch operation"""
```

#### **Task 1.2: Data Cleanup Service**
**File**: `backend/app/services/flow_cleanup_service.py` (NEW)

```python
class FlowCleanupService:
    """Service for safely deleting discovery flows and associated data"""
    
    async def delete_flow_with_cleanup(self, session_id: str, context: RequestContext) -> Dict[str, Any]:
        """Delete flow and cascade to all associated data"""
        # 1. Delete WorkflowState
        # 2. Delete DataImportSession 
        # 3. Delete ImportFieldMapping records
        # 4. Delete created Asset records
        # 5. Delete AssetDependency records
        # 6. Clean up file storage
        # 7. Audit log the deletion
        
    async def validate_deletion_safety(self, session_id: str) -> Dict[str, Any]:
        """Validate that flow can be safely deleted"""
        
    async def get_deletion_impact(self, session_id: str) -> Dict[str, Any]:
        """Get information about what will be deleted"""
```

## 🎯 **Next Steps**

1. **Review and approve this implementation plan**
2. **Set up development environment for flow management features**
3. **Begin Sprint 1 implementation with backend foundation**
4. **Establish testing protocols for flow management scenarios**
5. **Create monitoring and alerting for flow management operations**

This comprehensive plan ensures that the incomplete discovery flow management feature will be robust, user-friendly, and maintainable while preserving data integrity and providing excellent user experience.
