# E2E Data Flow Analysis: Data Import

**Analysis Date:** 2025-08-12  
**Status:** Updated with Persistent Agent Implementation

This document provides a complete, end-to-end data flow analysis for the `Data Import` process, which initiates a `Discovery` workflow with persistent agents as per ADR-015.

**Core Architecture:**
- **Persistent Agents (ADR-015):** All data processing uses persistent, tenant-scoped agents that maintain memory and context
- **Agent Tools:** Agents have specific tools for data validation, analysis, and database operations
- **Modular Services:** The backend uses a modular service architecture with atomic transactions
- **Asynchronous Execution:** Agentic workflow executes asynchronously after initial API success
- **Phase-based Execution:** PhaseController manages step-by-step flow with pause/resume capabilities

---

## 1. Frontend: Initiating the Import

The Data Import page allows users to upload a data file (e.g., a CMDB export), which triggers the discovery workflow with persistent agents.

### Key Components & Hooks
- **Page Component:** `src/pages/discovery/CMDBImport/index.tsx`
- **File Upload Logic:** `src/pages/discovery/CMDBImport/hooks/useFileUpload.ts`
- **Flow State Management:** `src/hooks/useUnifiedDiscoveryFlow.ts`

### API Call Summary

| # | Method | Endpoint | Trigger | Description |
|---|--------|----------|---------|-------------|
| 1 | `POST` | `/api/v1/data-import/store-import` | `useFileUpload` hook after file upload | Sends parsed file data to backend for storage and flow triggering |
| 2 | `GET` | (WebSocket or Polling) | `useUnifiedDiscoveryFlow` hook | Monitors real-time status updates on flow progress |

---

## 2. Backend: Persistent Agent Architecture

The backend uses persistent agents (per ADR-015) that maintain memory and context across the entire discovery flow.

### API Endpoint: `POST /api/v1/data-import/store-import`

- **FastAPI Route:** `backend/app/api/v1/endpoints/data_import/handlers/import_storage_handler.py`
- **Orchestration Service:** `backend/app/services/data_import/import_storage_handler.py`

### Service-Layer Execution Flow

1. **Validation (`ImportValidator`):**
   - Validates request context (client_account_id, engagement_id)
   - Checks for existing incomplete flows
   - Validates data structure

2. **Atomic Transaction (`ImportTransactionManager`):**
   - All database operations in single transaction

3. **Data Persistence (`ImportStorageManager`):**
   - Creates record in `data_imports` table
   - Stores rows as JSON in `raw_import_records` table
   - Creates initial field mapping suggestions
   - Updates status to `processing`

4. **Flow Creation (`FlowTriggerService`):**
   - Calls MasterFlowOrchestrator in atomic mode
   - Creates master flow in `crewai_flow_state_extensions`
   - Creates discovery flow in `discovery_flows` table
   - Links all records with master_flow_id

5. **Persistent Agent Initialization:**
   - `TenantScopedAgentPool` creates/retrieves agents for tenant
   - Agents maintain memory across all phases
   - Tools are loaded based on agent type

6. **Asynchronous Execution:**
   - BackgroundExecutionService starts phased workflow
   - Persistent agents process data with their tools
   - State persisted between phases

### Persistent Agent Implementation

#### Agent Pool Architecture
```python
# backend/app/services/persistent_agents/tenant_scoped_agent_pool.py
class TenantScopedAgentPool:
    # Agents are singletons per (client_id, engagement_id) tuple
    _agent_pools: Dict[Tuple[str, str], Dict[str, Agent]] = {}
    
    # Each agent gets appropriate tools
    def _get_agent_tools(agent_type, memory_manager):
        - data_analyst: validation + creation + intelligence tools
        - field_mapper: mapping confidence tools
        - quality_assessor: enrichment tools
        - pattern_discovery_agent: creation + intelligence tools
```

#### Data Validation Tools

Persistent agents now have specialized tools for data import/validation:

1. **DataValidationTool** (`data_validator`)
   - Validates data structure and completeness
   - Checks field consistency
   - Identifies required fields
   - Reports errors and warnings

2. **DataStructureAnalyzerTool** (`data_structure_analyzer`)
   - Analyzes field types and patterns
   - Detects asset type indicators
   - Calculates data quality scores
   - Samples values for pattern detection

3. **FieldSuggestionTool** (`field_suggestion_generator`)
   - Generates intelligent field mapping suggestions
   - Uses pattern matching for common fields
   - Provides confidence scores for mappings
   - Handles custom field inference

4. **DataQualityAssessmentTool** (`data_quality_assessor`)
   - Assesses overall data quality
   - Identifies data issues
   - Provides cleansing recommendations
   - Calculates quality scores

### Database Schema

- **`data_imports`:** Central record for file upload with metadata and status
  - Links to master flow via `master_flow_id`
- **`raw_import_records`:** Contains actual data from uploaded file
  - Stores data as JSONB in `raw_data` column
  - Links to flow via `master_flow_id`
- **`import_field_mappings`:** Stores AI-suggested and user-confirmed mappings
  - Uses intelligent mapping helpers
  - Links to flow via `master_flow_id`
- **`crewai_flow_state_extensions`:** Master flow table
  - Primary flow record with unique `flow_id`
- **`discovery_flows`:** Discovery-specific tracking
  - Links to master via `master_flow_id`
  - Contains phase completion flags

---

## 3. Persistent Agent Execution Flow

### Phase 1: Data Import Validation

When data is imported, the persistent `data_analyst` agent:

1. **Receives raw data** from `raw_import_records`
2. **Uses validation tools** to:
   - Validate structure with `data_validator`
   - Analyze patterns with `data_structure_analyzer`
   - Assess quality with `data_quality_assessor`
3. **Stores insights** in agent memory for future phases
4. **Updates flow state** with validation results

### Phase 2: Field Mapping Suggestions

The persistent `field_mapper` agent:

1. **Uses previous validation insights** from memory
2. **Applies field suggestion tool** to generate mappings
3. **Leverages historical patterns** from past flows
4. **Creates mapping suggestions** with confidence scores

### Key Implementation Code

```python
# Data validation phase execution
def _execute_discovery_data_import_validation(agent_pool, phase_input):
    data_analyst = agent_pool.get("data_analyst")
    
    # Agent has these tools available:
    # - data_validator
    # - data_structure_analyzer
    # - field_suggestion_generator
    # - data_quality_assessor
    
    # Agent processes data using tools
    validation_results = agent.validate_with_tools(raw_data)
    
    return {
        "phase": "data_import_validation",
        "agent": "data_analyst",
        "status": "executed_with_persistent_agent_and_tools",
        "validation_results": validation_results
    }
```

---

## 4. End-to-End Flow Sequence

1. **User Uploads File:** CSV/Excel file uploaded via UI
2. **Frontend Parsing:** File parsed to JSON in browser
3. **API Call:** POST to `/api/v1/data-import/store-import`
4. **Backend Processing:**
   - Atomic transaction creates all records
   - Flow created via MasterFlowOrchestrator
   - Persistent agents initialized for tenant
5. **Agent Validation:**
   - Data analyst validates with specialized tools
   - Results stored in agent memory
   - Flow state updated
6. **Field Mapping:**
   - Field mapper suggests mappings
   - Uses validation insights from memory
   - Pauses for user approval
7. **Continuation:** After approval, flow continues through remaining phases

---

## 5. Troubleshooting & Diagnostics

| Issue | Diagnostic Check | Solution |
|-------|-----------------|----------|
| **No Agent Tools** | Check `_get_agent_tools()` in TenantScopedAgentPool | Ensure tool imports are correct |
| **Validation Fails** | Check if data_analyst has validation tools | Verify `create_data_validation_tools()` called |
| **Memory Not Persisting** | Check agent pool singleton pattern | Ensure same tenant key used |
| **Tools Not Working** | Check CREWAI_TOOLS_AVAILABLE flag | Install crewai package |
| **Agent Not Found** | Check tenant pool initialization | Call `initialize_tenant_pool()` |
| **Flow Stuck** | Check phase execution result | Ensure proper status returned |

---

## 6. Recent Enhancements (2025-08-12)

### Persistent Agent Tools
- Created `data_validation_tool.py` with 4 specialized tools
- Updated agent pool to provide tools based on agent type
- Enhanced execution engine for tool-based processing

### Architecture Improvements
- Agents maintain memory across entire flow
- Tools enable direct database operations
- No delegation to stateless executors
- Follows ADR-015 requirements

### Data Import Specific Changes
- Data analyst gets validation tools
- Field mapper gets suggestion tools
- Quality assessor gets enrichment tools
- All agents have deduplication capabilities

---

## 7. Technical Patterns

### UUID Serialization
```python
configuration = convert_uuids_to_str({
    "import_id": data_import_id,
    # ...
})
```

### Persistent Agent Retrieval
```python
agent_pool = await TenantScopedAgentPool.initialize_tenant_pool(
    client_id, engagement_id
)
data_analyst = agent_pool.get("data_analyst")
```

### Tool Execution Pattern
```python
# Agent uses tools internally
result = await agent.execute_with_tools(
    task="validate_data",
    input_data=raw_data,
    available_tools=["data_validator", "data_structure_analyzer"]
)
```

---

## 8. Next Steps

1. **Enhance Field Mapping Phase** with more intelligent tools
2. **Add Memory Persistence** for cross-flow learning
3. **Implement Tool Metrics** to track tool usage
4. **Create Tool Feedback Loop** for continuous improvement
5. **Add Custom Tool Creation** based on tenant needs