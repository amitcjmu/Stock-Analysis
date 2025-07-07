# Platform Cleanup Tasks List

## Overview
This document provides a comprehensive list of all cleanup tasks required to complete the platform modernization. These are minor cleanup items that don't affect core functionality but should be addressed for code quality and consistency.

## Priority 1: Session ID Cleanup (1 week)

### Backend Files with ACTUAL session_id Code Usage
```python
# Data Models
- backend/app/models/data_import_session.py:73 - parent_session_id column definition

# Schema Definitions
- backend/app/schemas/auth_schemas.py:317 - session_id: Optional[str] = None
- backend/app/schemas/data_import_schemas.py:39 - validation_session_id: str (active field)
- backend/app/schemas/data_import_schemas.py:55 - validation_session_id legacy field

# Active Code Usage
- backend/app/api/v1/endpoints/data_import/handlers/import_storage_handler.py:150,182,185,212 - validation_session_id usage
- backend/app/services/discovery_flow_cleanup_service_v2.py:343,348 - import_session_id checks
- backend/app/services/crewai_flows/discovery_flow_cleanup_service.py:412 - Dependency.session_id
- backend/app/services/crewai_flows/handlers/learning_management_handler.py:515 - session_id parameter
- backend/app/services/crewai_flows/handlers/crew_execution_handler.py:339,412,446 - session_id usage
- backend/app/services/crewai_flows/handlers/phase_executors/phase_execution_manager.py:116,128,155 - session_id methods
- backend/app/services/agents/agent_communication_protocol.py:91,107 - ui_session_id
- backend/app/services/agents/intelligent_flow_agent.py:438 - session_id=None
- backend/app/services/flows/discovery_flow.py:149 - session_id in import data
```

### Frontend Files with ACTUAL sessionId Code Usage
```typescript
# Auth Context
- src/contexts/AuthContext/types.ts:69 - switchSession: (sessionId: string) => Promise<void>;
- src/contexts/AuthContext/services/authService.ts:296,298 - switchSession implementation

# Components
- src/components/context/ContextSelector.tsx:149,150,154 - handleStagedSessionChange with sessionId
```

### Actions Required
1. Remove `session_id` column from database models
2. Update all queries to use `flow_id` exclusively
3. Remove session-related schemas and handlers
4. Update frontend to remove session switching logic
5. Run database migration to drop session_id columns

## Priority 2: V3 API Cleanup (1-2 weeks)

### Backend V3 References
```python
# Only found in example/documentation files:
- backend/app/services/flows/example_usage.py:176-181 - V3 API examples (documentation only)
```

### Frontend V3 References
✅ **No V3 API calls found in frontend code** - Frontend already uses V1 APIs

### V2 API Status
```
# V2 API directory exists but is empty:
- backend/app/api/v2/__init__.py - Empty placeholder file
- backend/app/api/v2/ - Directory can be removed
```

### Actions Required
1. Audit all frontend API service files
2. Ensure all use v1 endpoints only
3. Remove any v3 service implementations
4. Update any hardcoded v3 URLs

## Priority 3: Code Pattern Cleanup (1 week)

### Pseudo-Agent References (Still Active)
```python
# API Endpoints using agents
- backend/app/api/v1/endpoints/crew_monitoring.py:117 - imports agent_registry
- backend/app/api/v1/endpoints/flow_processing.py:17 - imports IntelligentFlowAgent
- backend/app/api/v1/endpoints/agents/discovery/handlers/agent_ui_integration.py:17 - imports communication protocol

# Service Files with agent imports
- backend/app/services/agent_registry.py:75 - references DataImportValidationAgent, AttributeMappingAgent
- backend/app/services/crews/data_cleansing_crew.py:41 - imports agent_factory
- backend/app/services/crews/field_mapping_crew.py:42 - imports agent_factory
- backend/app/services/crews/asset_inventory_crew.py:41 - imports agent_factory

# Agent implementations still active
- backend/app/services/agents/*.py - Multiple files importing base_agent, registry
- backend/app/services/agents/data_validation_agent_crewai.py:11 - DataImportValidationAgent class
- backend/app/services/crewai_handlers/agent_coordinator.py:22,40 - imports AgentManager
```

### Direct Flow Creation (Bypassing Orchestrator)
```python
# API Endpoints with direct flow creation
- backend/app/api/v1/endpoints/discovery_flows.py:1286 - UnifiedDiscoveryFlow() direct
- backend/app/api/v1/endpoints/discovery_escalation.py:49,118,200,246,300 - Multiple direct UnifiedDiscoveryFlow()

# Service files with direct flow creation
- backend/app/services/crewai_flow_service.py:131,480 - UnifiedDiscoveryFlow() direct creation
- backend/app/services/flows/manager.py:90 - UnifiedDiscoveryFlow(db, context)

# Note: backend/app/services/crewai_flows/unified_discovery_flow/base_flow.py:55 is the class definition (OK)
```

### V2 API Redundancy
```python
# V2 Discovery Flow API (redundant with v1)
- backend/app/api/v2/* - entire v2 directory if exists
- References to discovery_flow_v2
```

### Actions Required
1. Remove all imports from archived modules
2. Ensure all flow creation goes through MasterFlowOrchestrator
3. Remove V2 API if it exists
4. Update any direct flow instantiation

## Priority 4: Frontend Route Cleanup (3-4 days)

### Route Inconsistencies
```typescript
# Inconsistent route patterns
- /discovery/cmdb-import vs /cmdb-import
- /discovery/flow/* vs /discovery-flow/*
- flow_id vs flowId parameter naming
- Trailing slashes inconsistency
```

### Actions Required
1. Standardize all discovery routes under /discovery/*
2. Use consistent parameter naming (flow_id)
3. Remove trailing slashes
4. Update React Router configurations

## Priority 5: Documentation Updates (2-3 days)

### API Documentation
- Update OpenAPI/Swagger specs to remove v3 endpoints
- Document v1-only API structure
- Add examples of proper flow creation

### Developer Guides
- Update flow creation examples to use orchestrator
- Remove references to session-based flows
- Document proper multi-tenant patterns

### Architecture Docs
- Update all diagrams to reflect current state
- Remove references to pseudo-agents
- Document PostgreSQL-only persistence

## Verification Results Summary

### Session ID Usage: ACTIVE (14 backend files, 3 frontend files)
- Mostly in validation/import flows where `validation_session_id` is actively used
- Some legacy fields in schemas marked as optional
- Active usage in crew execution and phase management

### V3 API Usage: MINIMAL (1 documentation file only)
- Only found in example_usage.py as documentation
- No active V3 API code in backend or frontend

### V2 API: EMPTY DIRECTORY
- backend/app/api/v2/ exists but only contains empty __init__.py
- Can be safely removed

### Pseudo-Agent Usage: EXTENSIVE (15+ files)
- Agent patterns are still actively used throughout the codebase
- Not actually "pseudo" - these appear to be real CrewAI agent implementations
- May need architectural review rather than simple cleanup

### Direct Flow Creation: MODERATE (5 files)
- Several API endpoints create flows directly instead of using orchestrator
- discovery_escalation.py has the most instances (5 occurrences)
- These should be refactored to use MasterFlowOrchestrator

### Frontend Verification
```bash
# Check for sessionId references
grep -r "sessionId" src/

# Check for v3 API calls
grep -r "api/v3" src/

# Check for inconsistent routes
grep -r "discovery" src/config/
```

### Database Verification
```sql
-- Check for session_id columns
SELECT table_name, column_name 
FROM information_schema.columns 
WHERE column_name = 'session_id';

-- Check for session-related tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_name LIKE '%session%';
```

## Timeline Summary

| Priority | Task | Duration | Impact |
|----------|------|----------|--------|
| 1 | Session ID Cleanup | 1 week | Medium - DB schema change |
| 2 | V3 API Frontend Cleanup | 1-2 weeks | Low - Frontend only |
| 3 | Code Pattern Cleanup | 1 week | Low - Code quality |
| 4 | Route Consistency | 3-4 days | Low - UX improvement |
| 5 | Documentation | 2-3 days | Low - Developer experience |

**Total Duration**: 3-4 weeks for complete cleanup

## Notes

1. **Core Functionality**: The platform is fully functional without these cleanups
2. **Production Ready**: These are code quality improvements, not blockers
3. **Incremental**: Each cleanup can be done independently
4. **Low Risk**: Most changes are removing dead code, not modifying active logic

---

**Created**: January 2025  
**Status**: Ready for execution  
**Priority**: Nice-to-have (not blocking production)