# Large Files Modularization Candidates

## Overview
This report identifies files exceeding 300-400 lines of code that are good candidates for modularization during Phase 1 remediation work.

## Python Files (backend/app/)

### Critical Files (1000+ lines) - High Priority
1. **services/crewai_flows/unified_discovery_flow.py** - 1799 lines
   - Main CrewAI Flow implementation
   - Could be split into phase-specific modules
   
2. **api/v1/endpoints/data_import/field_mapping.py** - 1698 lines
   - Complex field mapping logic
   - Mix of handlers, validation, and UI support
   
3. **api/v1/endpoints/context.py** - 1447 lines
   - Context management endpoints
   - Could separate multi-tenant logic
   
4. **api/v1/discovery_handlers/flow_management.py** - 1352 lines
   - Flow management with mixed v1/v3 patterns
   - Good candidate for version-specific splitting

5. **api/v1/endpoints/data_import/agentic_critical_attributes.py** - 1289 lines
   - Agent-based attribute processing
   - Could modularize agent interactions

### Large Files (500-1000 lines) - Medium Priority
- **services/agents/agent_service_layer.py** - 1280 lines
- **services/agent_learning_system.py** - 1264 lines
- **api/v1/unified_discovery_api.py** - 1261 lines
- **api/v1/endpoints/sixr_analysis.py** - 1164 lines
- **services/agents/intelligent_flow_agent.py** - 962 lines
- **api/v1/endpoints/monitoring.py** - 943 lines
- **services/escalation/crew_escalation_manager.py** - 863 lines
- **api/v3/data_import.py** - 859 lines

### Files in Target Range (300-400 lines) - Lower Priority
Total: 62 Python files between 300-400 lines

Key candidates:
- **models/rbac.py** - 397 lines (RBAC model definitions)
- **repositories/asset_repository.py** - 395 lines
- **services/crews/asset_inventory_crew.py** - 393 lines
- **core/flow_state_validator.py** - 365 lines
- **services/crewai_flows/persistence/postgres_store.py** - 353 lines

## TypeScript/React Files (src/)

### Critical Files (1000+ lines) - High Priority
1. **pages/discovery/CMDBImport.tsx** - 1492 lines
   - Main CMDB import page
   - Mix of UI, state management, and API calls
   
2. **pages/discovery/EnhancedDiscoveryDashboard.tsx** - 1132 lines
   - Complex dashboard with multiple features
   - Could split into component modules
   
3. **components/FlowCrewAgentMonitor.tsx** - 1106 lines
   - Agent monitoring UI
   - Mix of monitoring, visualization, and controls

### Large Files (500-1000 lines) - Medium Priority
- **components/sixr/BulkAnalysis.tsx** - 938 lines
- **components/admin/client-management/ClientManagementMain.tsx** - 935 lines
- **components/discovery/application-discovery/ApplicationDiscoveryPanel.tsx** - 907 lines
- **contexts/AuthContext.tsx** - 859 lines (auth logic mixed with UI)
- **components/discovery/inventory/InventoryContent.tsx** - 855 lines
- **hooks/discovery/useDiscoveryFlowV2.ts** - 825 lines (complex hook)
- **components/discovery/attribute-mapping/FieldMappingsTab.tsx** - 770 lines

### Files in Target Range (300-400 lines) - Lower Priority
Total: 37 TypeScript/React files between 300-400 lines

Key candidates:
- **components/ui/ChatInterface.tsx** - 398 lines
- **api/v3/fieldMappingClient.ts** - 397 lines
- **api/v3/discoveryFlowClient.ts** - 389 lines
- **components/discovery/data-cleansing/AgentQualityAnalysis.tsx** - 386 lines
- **components/discovery/attribute-mapping/TrainingProgressTab.tsx** - 382 lines

## Modularization Recommendations

### Phase 1 Priority (During Remediation)
1. **unified_discovery_flow.py** - Split into phase-specific flows
2. **field_mapping.py** - Separate API handlers from business logic
3. **CMDBImport.tsx** - Extract components and hooks
4. **EnhancedDiscoveryDashboard.tsx** - Create widget components

### Common Patterns to Extract
1. **Backend**:
   - Separate API handlers from business logic
   - Extract validation logic into validators
   - Split CrewAI agent interactions
   - Modularize database operations

2. **Frontend**:
   - Extract custom hooks from components
   - Create smaller, focused components
   - Separate API client logic
   - Extract state management logic

### Benefits of Modularization
- Easier testing and maintenance
- Better code reusability
- Clearer separation of concerns
- Reduced complexity during remediation
- Easier API v1 to v3 migration