# Data Cleansing Documentation Analysis - CORRECTED
**Analysis Date:** 2025-10-08
**Original Doc Date:** 2025-08-12 (2 months outdated)

## Executive Summary - ARCHITECTURE CLARIFICATION

After reviewing ADR-022, Serena memories, and actual code:

**CORRECT Architecture (Per ADR-022 - Sept 2025):**
```
MasterFlowOrchestrator (entry point)
    ↓
FlowExecutionEngine (delegates to phase executors)
    ↓
PhaseExecutionManager (routes to specific executor)
    ↓
DataCleansingExecutor (data cleansing logic)
    ↓
TenantScopedAgentPool (persistent agent system)
    ↓
Single Agent (NOT crew) with process() method
```

**OLD Architecture (Removed - ADR-022):**
```
❌ Multi-agent CrewAI crews (infinite loops, hallucinations)
❌ Agent coordination (analysis paralysis)
❌ Crew-based execution patterns
```

### Critical Bugs Remain:

1. ❌ **Field mappings NEVER retrieved from import_field_mappings table**
2. ❌ **No transformation from approved mappings (Asset_Name → name)**
3. ❌ **Agent returns data unchanged (pass-through bug)**
4. ❌ **Asset creation fails due to wrong field names**

---

## CORRECT Data Cleansing Flow (New Architecture)

### Frontend → Backend Flow

**Frontend Trigger:**
```typescript
// DataCleansing.tsx
useTriggerDataCleansingAnalysis() mutation
    ↓
POST /api/v1/data-cleansing/flows/{flowId}/data-cleansing/trigger
```

**Backend Execution Chain:**
```python
1. API Endpoint: trigger_data_cleansing_analysis()
   File: backend/app/api/v1/endpoints/data_cleansing/triggers.py:26-203

2. MasterFlowOrchestrator.execute_phase()
   File: backend/app/services/master_flow_orchestrator/core.py:240
   Delegates to → FlowExecutionEngine

3. FlowExecutionEngine.execute()
   File: backend/app/services/flow_orchestration/execution_engine.py
   Routes to → PhaseExecutionManager

4. PhaseExecutionManager.execute_phase(phase_name="data_cleansing")
   File: backend/app/services/crewai_flows/handlers/phase_executors/phase_execution_manager.py:95-97
   Calls → DataCleansingExecutor.execute()

5. DataCleansingExecutor.execute_with_crew()
   File: backend/app/services/crewai_flows/handlers/phase_executors/data_cleansing/executor.py:31-134

6. AgentProcessor.process_with_agent()
   File: backend/app/services/crewai_flows/handlers/phase_executors/data_cleansing/agent_processor.py:21-47

7. TenantScopedAgentPool.get_agent(agent_type="data_cleansing")
   File: backend/app/services/persistent_agents/tenant_scoped_agent_pool.py
   Returns → Single persistent agent (NOT crew)

8. AgentWrapper.process(data)
   File: backend/app/services/persistent_agents/config/agent_wrapper.py:119-172
   ❌ BUG: Returns data unchanged!

9. DatabaseOperations.update_cleansed_data_sync()
   File: backend/app/services/crewai_flows/handlers/phase_executors/data_cleansing/database_operations.py:83-126
   Stores in → raw_import_records.cleansed_data
```

### Alternate Flow (Unified Discovery)

**Also used:**
```
POST /api/v1/unified-discovery/flows/{flowId}/execute
body: {"phase": "data_cleansing", "phase_input": {...}}

→ Same execution chain (MFO → Engine → Manager → Executor)
```

---

## What Documentation Says vs Reality

### Section 1: Frontend

#### Doc Claims:
```markdown
Uses useUnifiedDiscoveryFlow to get raw_data and field_mappings
Calls /api/v1/unified-discovery/flow/{flowId}/status
```

#### Reality:
```typescript
// DataCleansing.tsx ACTUALLY uses:
✅ useUnifiedDiscoveryFlow(flowId)              // Flow state
✅ useDataCleansingStats(flowId)                // Stats endpoint
✅ useDataCleansingAnalysis(flowId)             // Analysis results
✅ useTriggerDataCleansingAnalysis()            // Trigger mutation
✅ usePhaseAwareFlowResolver(flowId, 'data_cleansing')  // Flow resolution

// Multiple API endpoints:
✅ GET /api/v1/unified-discovery/flows/{flowId}
✅ GET /api/v1/data-cleansing/flows/{flowId}/stats
✅ GET /api/v1/data-cleansing/flows/{flowId}/analysis
✅ POST /api/v1/data-cleansing/flows/{flowId}/data-cleansing/trigger
```

**Status:** ❌ Doc oversimplified, missing specialized hooks

---

### Section 2: Backend Architecture

#### Doc Claims:
```markdown
MasterFlowOrchestrator receives request
Executes data_cleansing phase with agent crew
CrewAI agents analyze data quality
```

#### Reality (Per ADR-022):
```
✅ MasterFlowOrchestrator exists (entry point)
✅ Delegates to FlowExecutionEngine
✅ Engine routes to PhaseExecutionManager
✅ Manager calls DataCleansingExecutor
✅ Executor uses TenantScopedAgentPool
✅ SINGLE AGENT (NOT crew) - per ADR-022
❌ NO multi-agent crews (removed Sept 2025)
❌ Agent does NOT analyze quality (bug - should transform data)
```

**Key Files:**
- `master_flow_orchestrator/core.py` - Entry orchestrator
- `flow_orchestration/execution_engine.py` - Execution delegation
- `phase_executors/phase_execution_manager.py` - Phase routing
- `phase_executors/data_cleansing/executor.py` - Cleansing logic
- `persistent_agents/tenant_scoped_agent_pool.py` - Agent management

**Status:** ❌ Doc partially correct but outdated on agent architecture

---

### Section 3: The CRITICAL Missing Piece

#### What Doc Doesn't Mention:

**Field Mapping Application - COMPLETELY ABSENT!**

```sql
-- These 15 approved mappings exist in database:
SELECT source_field, target_field, status
FROM migration.import_field_mappings
WHERE data_import_id = '...' AND status = 'approved';

Asset_Name       → name              ✅ Approved
CPU_Cores        → cpu_cores         ✅ Approved
Operating_System → operating_system  ✅ Approved
...15 total mappings...
```

**But data cleansing NEVER queries this table!**

```python
# DataCleansingExecutor._prepare_crew_input() - Line 176-182
def _prepare_crew_input(self) -> Dict[str, Any]:
    return {
        "raw_data": self.state.raw_data,
        "field_mappings": getattr(self.state, "field_mappings", {}),  # ❌ ALWAYS EMPTY!
        "cleansing_type": "comprehensive_data_cleansing",
    }
```

**SHOULD BE:**
```python
# CORRECT implementation:
async def _prepare_crew_input(self) -> Dict[str, Any]:
    # Import from asset_inventory_executor (already exists!)
    from ..asset_inventory_executor.queries import get_field_mappings

    # Retrieve approved mappings from database
    field_mappings = await get_field_mappings(
        db=self.db_session,
        data_import_id=self.state.data_import_id,
        client_account_id=self.state.client_account_id
    )
    # Returns: {"Asset_Name": "name", "CPU_Cores": "cpu_cores", ...}

    return {
        "raw_data": self.state.raw_data,
        "field_mappings": field_mappings,  # ✅ ACTUAL MAPPINGS!
        "cleansing_type": "apply_field_mappings_and_cleanse",
    }
```

---

## Correct Data Transformation Flow

### What SHOULD Happen:

```
1. Attribute Mapping Phase (Prerequisite)
   ├─ User reviews AI-suggested mappings
   ├─ Approves: Asset_Name → name
   ├─ Approves: CPU_Cores → cpu_cores
   └─ Stored in: import_field_mappings table ✅

2. Data Cleansing Phase (BROKEN - Missing Steps)
   ├─ ❌ MISSING: Query import_field_mappings table
   ├─ ❌ MISSING: Apply transformations
   ├─ Agent receives: {"Asset_Name": "Server01", "CPU_Cores": "4"}
   ├─ Agent returns: {"Asset_Name": "Server01", "CPU_Cores": "4"}  # unchanged!
   ├─ My hack normalizes: {"asset_name": "Server01", "cpu_cores": "4"}
   └─ Stores in: raw_import_records.cleansed_data (WRONG DATA!)

3. Asset Inventory Phase (FAILS)
   ├─ Reads: cleansed_data
   ├─ Expects: record.get("name")  # From approved mapping
   ├─ Gets: record.get("asset_name")  # From my normalization
   ├─ Falls back: f"Asset-{row_number}"
   └─ Result: ❌ "Asset-1", "Asset-2" with type "other"
```

### What SHOULD Happen (Corrected):

```
1. Attribute Mapping Phase
   [Same - already working ✅]

2. Data Cleansing Phase (FIXED)
   ├─ ✅ Query import_field_mappings table
   │   Returns: {"Asset_Name": "name", "CPU_Cores": "cpu_cores"}
   │
   ├─ ✅ Apply field transformations:
   │   Input:  {"Asset_Name": "Server01", "CPU_Cores": "4"}
   │   Mapping: Asset_Name → name, CPU_Cores → cpu_cores
   │   Output: {"name": "Server01", "cpu_cores": "4"}
   │
   ├─ ✅ Agent enriches transformed data (optional)
   └─ ✅ Store in: raw_import_records.cleansed_data
       Value: {"name": "Server01", "cpu_cores": "4", ...}

3. Asset Inventory Phase (WORKS!)
   ├─ ✅ Reads: cleansed_data
   ├─ ✅ Finds: record.get("name") = "Server01"
   ├─ ✅ Finds: record.get("cpu_cores") = "4"
   └─ ✅ Creates asset: "Server01" type "server" ✅
```

---

## Documentation Updates Required

### HIGH PRIORITY (Must Fix Code First!)

1. **Add Field Mapping Retrieval Logic**
   ```python
   # In DataCleansingExecutor
   - Import get_field_mappings from asset_inventory_executor
   - Call in _prepare_crew_input() to retrieve from DB
   - Pass actual mappings to agent/transformer
   ```

2. **Add Field Transformation Logic**
   ```python
   # In AgentProcessor or new transformer service
   def apply_field_mappings(raw_data, field_mappings):
       transformed = {}
       for source_field, value in raw_data.items():
           target_field = field_mappings.get(source_field, source_field)
           transformed[target_field] = value
       return transformed
   ```

3. **Remove My Normalization Hack**
   ```python
   # Delete from data_cleansing_utils.py:
   - normalize_field_name()
   - normalize_record_fields()

   # Delete from agent_processor.py and base.py:
   - All normalization calls
   ```

### MEDIUM PRIORITY (Doc Updates After Code Fix)

4. **Update Section 1: Frontend**
   - Add all specialized hooks
   - List actual API endpoints used
   - Remove oversimplification

5. **Update Section 2: Backend Architecture**
   - Correct: MFO → Engine → Manager → Executor → AgentPool
   - Clarify: Single agent (NOT crew) per ADR-022
   - Add: Field mapping retrieval step
   - Add: Data transformation pipeline

6. **Add Section: Field Mapping Integration**
   ```markdown
   ## Field Mapping Application (NEW)

   ### Prerequisites
   - Attribute Mapping phase completed
   - User approved field mappings
   - Mappings in import_field_mappings table

   ### Data Cleansing Process
   1. Query approved mappings from database
   2. Apply transformations (source → target)
   3. Store transformed data in cleansed_data
   4. Enable asset inventory to find expected fields
   ```

7. **Update Section 3: Database Tables**
   - **ADD**: import_field_mappings table (critical!)
   - Explain: Source of truth for transformations
   - Show: Relationship to cleansing phase

---

## Summary of Changes Needed

### Code Fixes (MUST DO FIRST):

| Component | File | Change | Priority |
|-----------|------|--------|----------|
| DataCleansingExecutor | data_cleansing/executor.py | Add field mapping query | HIGH |
| AgentProcessor | data_cleansing/agent_processor.py | Add field transformation | HIGH |
| Data Utils | data_cleansing_utils.py | Remove normalization hack | HIGH |
| Base Cleansing | data_cleansing/base.py | Remove normalization hack | HIGH |

### Documentation Fixes (AFTER CODE):

| Section | Issue | Change | Priority |
|---------|-------|--------|----------|
| Frontend | Oversimplified | Add all hooks and endpoints | MEDIUM |
| Backend | Wrong architecture | Correct MFO delegation chain | HIGH |
| Backend | Missing step | Add field mapping retrieval | HIGH |
| Database | Missing table | Document import_field_mappings | HIGH |
| Flow | Wrong sequence | Show correct transformation flow | HIGH |

---

## Key Architectural Points (For Doc)

### MasterFlowOrchestrator Role (Correct Understanding):
```
MFO is the ENTRY POINT but NOT the executor
- Receives phase execution requests
- Validates flow state
- Delegates to FlowExecutionEngine
- Handles errors and retries
- Manages flow lifecycle

MFO does NOT directly execute phases!
```

### Phase Execution Delegation:
```
MasterFlowOrchestrator
    ↓ (delegates via)
FlowExecutionEngine
    ↓ (routes via)
PhaseExecutionManager
    ↓ (calls specific)
{Phase}Executor (e.g., DataCleansingExecutor)
    ↓ (uses)
TenantScopedAgentPool
    ↓ (returns)
Single Persistent Agent
```

### Agent Architecture (Per ADR-022):
```
✅ Single persistent agent per phase
✅ TenantScopedAgentPool management
✅ AgentWrapper.process() interface
❌ NO multi-agent crews
❌ NO agent coordination
❌ NO crew-based patterns
```

### Data Flow Purpose:
```
NOT: "Quality analysis and enrichment" (doc's claim)
IS:  "Apply approved field mappings for asset creation"

Cleansing = Transformation using user-approved mappings
```

---

## Validation Checklist

Before updating documentation:

- [ ] Code: DataCleansingExecutor retrieves field mappings from DB
- [ ] Code: Transformation applied (source → target field names)
- [ ] Code: Removed normalization hacks
- [ ] Test: Assets created with correct names and types
- [ ] Test: cleansed_data has transformed fields
- [ ] Verify: All 15 approved mappings are applied
- [ ] Docs: Updated with correct architecture
- [ ] Docs: Field mapping integration documented
- [ ] Docs: import_field_mappings table included

**STATUS: Do NOT update documentation until code bugs are fixed!**
