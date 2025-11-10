# Discovery Flow - Architecture Summary

**Last Updated:** 2025-11-10
**Purpose:** Comprehensive reference guide for understanding the Discovery flow architecture before making code changes

## 🎯 Overview

The Discovery flow is a multi-phase, AI-powered process that imports, analyzes, and inventories IT assets for migration assessment. It uses CrewAI agents orchestrated by the Master Flow Orchestrator (MFO) to process data through five distinct phases with persistent, tenant-scoped intelligence.

**Key Capabilities:**
- Automated CSV/CMDB data import with intelligent field mapping
- AI-driven data validation and quality assessment
- Persistent agent learning across tenant engagements
- Adaptive phase progression with user approval gates
- Multi-tenant isolation with comprehensive audit trails

## 🏗️ Core Architecture (November 2025)

### Master Flow Orchestrator (MFO) Integration (ADR-006)

The Discovery flow is fully integrated with the **Master Flow Orchestrator** architecture, providing centralized flow lifecycle management:

1. **Master Flow Orchestrator (MFO)**
   - **Primary identifier**: `master_flow_id` (from `crewai_flow_state_extensions.flow_id`)
   - ALL flow operations (create, resume, pause, delete) go through MFO
   - **Unified API**: `/api/v1/master-flows/*` endpoints
   - Single source of truth for flow lifecycle management
   - **Location**: `backend/app/services/master_flow_orchestrator/`

2. **Master Flow Table** (`crewai_flow_state_extensions`)
   - Orchestration and coordination hub for ALL flow types
   - Flow status tracking: `running`, `paused`, `completed`, `failed`
   - Stores comprehensive flow state and metadata in JSONB
   - **Primary Key**: `flow_id` (this IS the master_flow_id)
   - Multi-tenant scoping via `client_account_id` and `engagement_id`

3. **Child Flow Service** (`DiscoveryChildFlowService`) - ADR-025
   - **Pattern**: Child flow service replaces legacy crew-based execution
   - **Location**: `backend/app/services/child_flow_services/discovery.py`
   - Routes phase execution to specialized executors
   - Links to master via `master_flow_id` foreign key in `discovery_flows` table
   - Contains phase completion booleans for UI display
   - **NOT exposed to API consumers** - internal state only

4. **Child Flow Table** (`discovery_flows`)
   - Discovery-specific phase tracking (5 phases per ADR-027)
   - Phase booleans: `data_import_completed`, `data_validation_completed`,
     `field_mapping_completed`, `data_cleansing_completed`, `asset_inventory_completed`
   - Stores `current_phase`, `progress_percentage`, and phase state in JSONB
   - Links to data import via `data_import_id` foreign key

⚠️ **CRITICAL**: The `master_flow_id` is the **primary identifier** for all Discovery flow operations. Child flow IDs are internal implementation details and should never be used directly by API consumers or UI components.

### Key Architectural Components

#### 1. **Persistent Multi-Tenant Agent Architecture (ADR-015)**
- **TenantScopedAgentPool**: Manages persistent agents per `(client_account_id, engagement_id)` tuple
- **Location**: `backend/app/services/persistent_agents/tenant_scoped_agent_pool.py`
- **Benefits**: Agents accumulate expertise over time, maintain memory across phases
- **Memory**: Disabled (`memory=False`) per ADR-024; uses TenantMemoryManager instead

#### 2. **Child Flow Service Pattern (ADR-025)**
- **BaseChildFlowService**: Abstract base class for all child flow operations
- **DiscoveryChildFlowService**: Discovery-specific implementation
- **Key Methods**:
  - `get_child_status()`: Returns child flow operational state
  - `get_by_master_flow_id()`: Retrieves child flow by master ID
  - `execute_phase()`: Routes phase execution to handlers

#### 3. **Phase Execution Handlers**
- **Location**: `backend/app/services/flow_orchestration/discovery_phase_handlers.py`
- **Handlers**:
  - `execute_data_validation()`: Data structure and quality validation
  - `execute_data_cleansing()`: AI-driven data enrichment
  - `execute_field_mapping()`: Intelligent field mapping with user approval
  - `execute_asset_inventory()`: Asset categorization and deduplication
  - `execute_dependency_analysis()`: Relationship mapping (deprecated in v3.0.0)

#### 4. **CrewAI Agent Activation**
Agents are retrieved from TenantScopedAgentPool and execute with specialized tools:
- **Data Validation Agent**: `data_validator`, `data_structure_analyzer`, `field_suggestion_generator`
- **Field Mapping Agent**: `mapping_confidence_calculator`, `critical_attributes_assessor`
- **Data Cleansing Agent**: `data_enrichment_tool`, `quality_enhancement_tool`
- **Asset Inventory Agent**: `asset_categorization_tool`, `deduplication_engine`

## 📊 Flow Phases (Discovery v3.0.0 - ADR-027)

Discovery v3.0.0 has **5 active phases** (dependency_analysis and tech_debt moved to Assessment Flow):

### 1. **Data Import**
- Uploads and validates data files (CSV/CMDB)
- Creates atomic transaction for all records
- Triggers flow creation through MFO
- **Agent**: Data Validation Agent
- **Tools**: `data_validator`, `data_structure_analyzer`
- **Endpoints**: `POST /api/v1/data-import/store-import`
- [Details →](./02_Data_Import.md)

### 2. **Data Validation**
- AI-powered structure and completeness validation
- Field type inference and pattern detection
- Quality score calculation
- **Agent**: Data Validation Agent
- **Tools**: `data_quality_assessor`, `field_suggestion_generator`
- **Phase Added**: ADR-027 (October 2025)

### 3. **Field Mapping** (Requires User Approval)
- AI suggests field mappings with confidence scores
- 22 critical attributes assessment for 6R readiness
- Pauses for user approval with intelligent MCQ questions
- **Agent**: Field Mapping Agent
- **Tools**: `critical_attributes_assessor`, `migration_readiness_scorer`
- **Endpoints**: `GET /api/v1/unified-discovery/flows/{flow_id}/field-mappings`
- [Details →](./03_Attribute_Mapping.md)

### 4. **Data Cleansing**
- Enriches data with AI intelligence
- Standardizes and validates records
- Persists cleansed data for asset creation
- **Agent**: Data Cleansing Agent
- **Tools**: `data_enrichment_tool`, `standardization_tool`
- **Critical Fix**: November 2025 - Fixed phase progression bug where clicking "Continue" didn't update `current_phase` in database
- [Details →](./04_Data_Cleansing.md)

### 5. **Asset Inventory**
- Categorizes and deduplicates assets
- Multi-domain classification (app, infra, network)
- Creates records in `assets` table
- **Agent**: Asset Inventory Agent
- **Tools**: `asset_categorization_tool`, `deduplication_engine`
- [Details →](./05_Inventory.md)

### 6. **Dependency Analysis** (DEPRECATED - Moved to Assessment Flow)
- **Status**: Removed from Discovery v3.0.0 per ADR-027
- **Now Part Of**: Assessment Flow
- Phase boolean kept in model for backward compatibility

### 7. **Technical Debt Assessment** (DEPRECATED - Moved to Assessment Flow)
- **Status**: Removed from Discovery v3.0.0 per ADR-027
- **Now Part Of**: Assessment Flow
- Phase boolean kept in model for backward compatibility

## 🔄 Data Flow Sequence (MFO-Aligned)

```
1. User uploads CSV → POST /api/v1/data-import/store-import
2. Backend creates flow through MasterFlowOrchestrator (atomic transaction):
   - MFO.create_flow() → returns master_flow_id
   - DataImport record (references master_flow_id)
   - RawImportRecords (JSONB storage)
   - ImportFieldMappings (AI suggestions)
   - Master flow state (crewai_flow_state_extensions)
   - Child flow record (discovery_flows) via DiscoveryChildFlowService
3. MFO initiates DiscoveryChildFlowService with master_flow_id
4. DiscoveryChildFlowService routes phases to specialized handlers
5. TenantScopedAgentPool provides persistent agents for each phase
6. ALL phase updates go through MFO using master_flow_id
7. UI polls MFO endpoints with master_flow_id for updates
```

## 🚨 Recent Architectural Changes (2024-2025)

### November 2025: Phase Progression Fix (Issue #980)
- **Problem**: Clicking "Continue" navigated UI but didn't update `current_phase` in database
- **Root Cause**: `continue_flow_processing` endpoint returned next phase but didn't persist it
- **Solution**: Added phase update logic using `FlowPhaseManagementCommands`
- **Location**: `backend/app/api/v1/endpoints/flow_processing.py:256-290`
- **Serena Memory**: `discovery_flow_phase_progression_fix_implementation_2025_11`

### October 2025: Child Flow Service Migration (ADR-025)
- **Change**: Replaced crew-based execution with ChildFlowService pattern
- **Benefit**: Single execution path through MFO, eliminates duplicate code
- **Pattern**: `crew_class` parameter removed entirely from FlowConfig
- **Location**: `backend/app/services/child_flow_services/discovery.py`

### October 2025: TenantMemoryManager (ADR-024)
- **Change**: Disabled CrewAI built-in memory (`memory=False`)
- **Reason**: DeepInfra/OpenAI embedding conflicts causing 401 errors
- **Replacement**: Enterprise TenantMemoryManager with PostgreSQL + pgvector
- **Benefits**: Multi-tenant isolation, data classification, audit trails
- **Location**: `backend/app/services/crewai_flows/memory/tenant_memory_manager.py`

### August 2025: Field Mapping Fixes
- **Fixed**: Attribute mapping showing 0 fields by updating to MFO endpoints
- **Fixed**: Frontend/backend field naming (snake_case: `target_field`, `confidence_score`)
- **Fixed**: Flow detection to include `waiting_for_approval` status
- **Result**: All 9 fields from CSV imports now display correctly

### August 2025: Persistent Agents (ADR-015)
- **Implemented**: TenantScopedAgentPool for all phases
- **Benefit**: 60-80% reduction in agent initialization overhead
- **Pattern**: Agents persist per `(client_account_id, engagement_id)` tuple
- **Location**: `backend/app/services/persistent_agents/tenant_scoped_agent_pool.py`

## 💾 Database Schema

### Essential Tables
- `data_imports` - File upload metadata, links to master_flow_id
- `raw_import_records` - Uploaded data in JSONB format
- `import_field_mappings` - AI field mapping suggestions
- `crewai_flow_state_extensions` - Master flow orchestration (all flow types)
- `discovery_flows` - Discovery-specific tracking (MUST EXIST per ADR-012)
- `assets` - Final inventory from asset_inventory phase
- `llm_usage_logs` - LLM tracking per ADR-026 (October 2025)

### Foreign Key Relationships (MFO-Aligned)
```
# Primary relationships through master_flow_id
data_imports.master_flow_id → crewai_flow_state_extensions.flow_id
discovery_flows.master_flow_id → crewai_flow_state_extensions.flow_id
discovery_flows.data_import_id → data_imports.id
assets.discovery_flow_id → discovery_flows.id (UUID PK, NOT flow_id)

# Key Point: crewai_flow_state_extensions.flow_id IS the master_flow_id
# All external references use this as the primary identifier
```

## 🛠️ Critical Code Patterns

### ✅ Correct Patterns

```python
# MFO Flow Creation (Primary Pattern)
master_flow_id = await mfo.create_flow(
    flow_type="discovery",
    configuration=config,
    atomic=True  # MUST be true for imports
)

# Always use master_flow_id for operations
await mfo.execute_phase(master_flow_id, phase_input)
await mfo.get_flow_status(master_flow_id)
await mfo.pause_flow(master_flow_id)

# UUID Serialization (prevents JSON errors)
configuration = convert_uuids_to_str({...})

# Child Flow Service (ADR-025 Pattern)
from app.services.child_flow_services import DiscoveryChildFlowService

child_service = DiscoveryChildFlowService(db, context)
result = await child_service.execute_phase(
    flow_id=master_flow_id,  # NOT child flow ID!
    phase_name="field_mapping",
    phase_input={"selected_assets": asset_ids}
)

# Persistent Agent Usage
from app.services.persistent_agents import TenantScopedAgentPool

agent = await TenantScopedAgentPool.get_agent(
    context=context,
    agent_type="field_mapper",
    service_registry=service_registry
)

# TenantMemoryManager (ADR-024)
from app.services.crewai_flows.memory.tenant_memory_manager import (
    TenantMemoryManager, LearningScope
)

memory_manager = TenantMemoryManager(
    crewai_service=crewai_service,
    database_session=db
)
await memory_manager.store_learning(
    client_account_id=context.client_account_id,
    engagement_id=context.engagement_id,
    scope=LearningScope.ENGAGEMENT,
    pattern_type="field_mapping",
    pattern_data={...}
)

# LLM Tracking (Mandatory - ADR-026)
from app.services.multi_model_service import multi_model_service, TaskComplexity

response = await multi_model_service.generate_response(
    prompt="Your prompt",
    task_type="field_mapping",
    complexity=TaskComplexity.SIMPLE  # Automatic tracking to llm_usage_logs
)
```

### ❌ Incorrect Patterns

```python
# DON'T use child flow IDs for operations
discovery_flow_id = get_discovery_flow_id()  # WRONG!
await some_operation(discovery_flow_id)      # WRONG!

# DON'T bypass MFO for flow operations
await direct_database_update(flow_id)        # WRONG!

# DON'T reference child flow IDs in APIs/UI
return {"discovery_flow_id": child_id}       # WRONG!

# Always use master_flow_id instead
return {"master_flow_id": master_flow_id}    # CORRECT!

# DON'T create crews per execution (ADR-015 violation)
crew = Crew(agents=[...], tasks=[...])       # WRONG!

# DON'T use crew_class in FlowConfig (ADR-025 violation)
FlowConfig(flow_type="discovery", crew_class=DiscoveryCrew)  # WRONG!

# DON'T use direct LLM calls (ADR-026 violation)
response = litellm.completion(model="...", messages=[...])  # WRONG!
```

## 📋 Implementation Checklist

Before modifying Discovery flow code:

- [ ] **CRITICAL**: Use master_flow_id for ALL external operations
- [ ] Route all flow operations through MasterFlowOrchestrator
- [ ] Never expose child flow IDs to API consumers or UI
- [ ] Use `/api/v1/master-flows/*` endpoints for flow operations
- [ ] Use DiscoveryChildFlowService for phase execution (not crew_class)
- [ ] Retrieve agents from TenantScopedAgentPool (not per-call creation)
- [ ] Use TenantMemoryManager for agent learning (not CrewAI memory)
- [ ] Use multi_model_service for all LLM calls (automatic tracking)
- [ ] Ensure child flow records exist for internal tracking
- [ ] Use atomic transactions for data import through MFO
- [ ] Handle UUID serialization for JSON storage
- [ ] Test full flow lifecycle using only master_flow_id
- [ ] Verify UI uses master_flow_id for all flow references

## 🔗 Quick References

| Topic | Details | Key File |
|-------|---------|----------|
| Flow Overview | [01_Overview.md](./01_Overview.md) | `src/pages/discovery/EnhancedDiscoveryDashboard` |
| Data Import | [02_Data_Import.md](./02_Data_Import.md) | `backend/app/services/data_import/flow_trigger_service.py` |
| Field Mapping | [03_Attribute_Mapping.md](./03_Attribute_Mapping.md) | `src/pages/discovery/AttributeMapping` |
| Data Cleansing | [04_Data_Cleansing.md](./04_Data_Cleansing.md) | `backend/app/services/flow_orchestration/discovery_phase_handlers.py` |
| Asset Inventory | [05_Inventory.md](./05_Inventory.md) | `backend/app/services/persistent_agents/tenant_scoped_agent_pool.py` |
| MFO Architecture | [ADR-006](../../adr/006-master-flow-orchestrator.md) | `backend/app/services/master_flow_orchestrator/` |
| Persistent Agents | [ADR-015](../../adr/015-persistent-multi-tenant-agent-architecture.md) | `backend/app/services/persistent_agents/` |
| Child Flow Services | [ADR-025](../../adr/025-child-flow-service-pattern.md) | `backend/app/services/child_flow_services/` |
| TenantMemoryManager | [ADR-024](../../adr/024-tenant-memory-manager-architecture.md) | `backend/app/services/crewai_flows/memory/tenant_memory_manager.py` |

## ⚡ API Endpoints (November 2025)

### Master Flow Operations
- `GET /api/v1/master-flows/active` - List active flows (all types)
- `GET /api/v1/master-flows/{flow_id}` - Get master flow status
- `POST /api/v1/master-flows/create` - Create new flow (any type)
- `POST /api/v1/master-flows/{flow_id}/pause` - Pause flow execution
- `POST /api/v1/master-flows/{flow_id}/resume` - Resume paused flow
- `DELETE /api/v1/master-flows/{flow_id}` - Soft delete flow

### Unified Discovery Operations
- `GET /api/v1/unified-discovery/flows/active` - List active discovery flows
- `GET /api/v1/unified-discovery/flows/{flow_id}/field-mappings` - Get field mappings
- `POST /api/v1/unified-discovery/flows/{flow_id}/approve-mappings` - Approve mappings
- `GET /api/v1/unified-discovery/flows/{flow_id}/assets` - Get discovered assets
- `GET /api/v1/unified-discovery/flows/{flow_id}/status` - Get detailed flow status

### Data Import Operations
- `POST /api/v1/data-import/store-import` - Upload and create flow (atomic)
- `GET /api/v1/data-import/latest-import` - Get latest import for tenant
- `GET /api/v1/data-import/critical-attributes-status` - Get field mapping status

### Flow Processing Operations
- `POST /api/v1/flow-processing/continue` - Continue to next phase
- `POST /api/v1/flow-processing/execute-phase` - Execute specific phase

### Legacy Endpoints (DEPRECATED)
- ❌ `/api/v1/discovery/*` - Use unified-discovery instead
- ❌ `/api/v1/6r/*` - Moved to Assessment Flow

## 🐛 Emergency Fixes

### If Discovery Flow is Stuck:
1. Check `crewai_flow_state_extensions` for flow status
   ```sql
   SELECT flow_id, flow_status, current_phase, flow_persistence_data
   FROM migration.crewai_flow_state_extensions
   WHERE flow_id = 'your-flow-id';
   ```
2. Verify `discovery_flows` record exists (if not, that's the problem)
   ```sql
   SELECT id, flow_id, master_flow_id, current_phase, status
   FROM migration.discovery_flows
   WHERE master_flow_id = 'your-flow-id';
   ```
3. Check agent pool health
   ```bash
   docker exec migration_backend python -c "from app.services.persistent_agents import TenantScopedAgentPool; print(TenantScopedAgentPool.get_pool_health())"
   ```
4. Review backend logs for phase execution errors
   ```bash
   docker logs migration_backend --tail 100 | grep -i "discovery\|phase\|agent"
   ```

### If Field Mapping Fails:
1. Verify discovery flow lookup has correct `data_import_id`
2. Check `import_field_mappings` table for suggestions
   ```sql
   SELECT id, source_field, target_field, confidence_score, status
   FROM migration.import_field_mappings
   WHERE data_import_id = (
     SELECT data_import_id FROM migration.discovery_flows WHERE master_flow_id = 'your-flow-id'
   );
   ```
3. Ensure field mapper agent exists in TenantScopedAgentPool
4. Check critical attributes definition import

### If Phase Progression Stuck:
1. Verify `current_phase` matches UI display
2. Check phase completion booleans in `discovery_flows`
3. Confirm `continue_flow_processing` endpoint is updating database
4. Review November 2025 fix in `flow_processing.py:256-290`

---

**Remember**: The Discovery flow is the foundation for migration assessment. Breaking it prevents users from analyzing their infrastructure. Always test the complete flow after changes using the Docker environment on port 8081.

**Testing Checklist**:
- [ ] Upload CSV creates both master and child flow records
- [ ] Field mapping suggestions appear with confidence scores
- [ ] Clicking "Continue" updates `current_phase` in database
- [ ] Assets are created in `assets` table after inventory phase
- [ ] Agent insights display in UI via agent-ui-bridge
- [ ] LLM usage tracked in `llm_usage_logs` table
- [ ] Multi-tenant isolation verified (no cross-tenant data leaks)
