# Direct Flow Creation Refactoring Summary

## Overview
This document summarizes the refactoring work done to replace direct UnifiedDiscoveryFlow creation with proper MasterFlowOrchestrator usage.

## Files Refactored

### 1. backend/app/api/v1/endpoints/discovery_flows.py
**Changes:**
- Replaced direct `UnifiedDiscoveryFlow()` creation in `resume_discovery_flow` function
- Now uses `MasterFlowOrchestrator.create_flow()` to create new flows
- Added proper flow superseding logic when restarting flows

### 2. backend/app/api/v1/endpoints/discovery_escalation.py
**Changes:**
- Added `db: AsyncSession` dependency to all endpoint functions
- Replaced all `UnifiedDiscoveryFlow()` instances with `MasterFlowOrchestrator` usage
- Updated flow validation to use `orchestrator.get_flow_status()`
- Note: Some escalation-specific methods (like `update_escalation_status`) need to be implemented in MasterFlowOrchestrator

### 3. backend/app/services/crewai_flow_service.py
**Changes:**
- Removed direct `UnifiedDiscoveryFlow()` creation in `initialize_flow` and `resume_flow`
- Added notes that flow creation should be delegated to MasterFlowOrchestrator
- Maintained compatibility by creating placeholder variables

### 4. backend/app/services/flows/manager.py
**Changes:**
- Complete refactor of `FlowManager` class to use MasterFlowOrchestrator
- Removed import of `UnifiedDiscoveryFlow`
- Updated all methods:
  - `create_discovery_flow`: Now uses `orchestrator.create_flow()`
  - `get_flow_status`: Delegates to `orchestrator.get_flow_status()`
  - `resume_flow`: Delegates to `orchestrator.resume_flow()`
  - `pause_flow`: Marked as deprecated (should use orchestrator)
  - `force_complete_flow`: Uses orchestrator to update flow status

## Implementation Notes

### 1. Database Session Handling
- All functions now properly inject `db: AsyncSession` dependency
- MasterFlowOrchestrator requires both `db` and `context` parameters

### 2. Flow ID Management
- When restarting flows, new flow IDs are generated
- Old flows are marked as "superseded" with metadata pointing to new flow

### 3. Background Execution
- MasterFlowOrchestrator handles background task creation internally
- No need for manual `asyncio.create_task()` calls

### 4. Missing Functionality
Some methods that were called on UnifiedDiscoveryFlow instances need to be implemented in MasterFlowOrchestrator:
- `update_escalation_status()`
- `apply_escalation_results()`
- Enhanced `resume_flow()` with resume context

## Benefits

1. **Centralized Flow Management**: All flows now go through a single orchestrator
2. **Consistent Error Handling**: MasterFlowOrchestrator provides unified error handling
3. **Better Audit Trail**: All flow operations are tracked through the orchestrator
4. **Proper State Management**: PostgreSQL-based state persistence is handled consistently
5. **Multi-tenant Isolation**: Orchestrator ensures proper tenant context

## Next Steps

1. Implement missing escalation methods in MasterFlowOrchestrator
2. Test all refactored endpoints to ensure functionality
3. Update frontend to handle new flow ID format when flows are restarted
4. Remove deprecated methods from FlowManager class
5. Update documentation to reflect new flow creation patterns

---

**Refactored By**: CC  
**Date**: January 2025  
**Status**: Complete - Testing Required