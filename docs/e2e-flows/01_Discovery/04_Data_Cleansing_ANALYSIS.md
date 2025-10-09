# Data Cleansing Documentation Analysis
**Analysis Date:** 2025-10-08
**Original Doc Date:** 2025-08-12 (2 months outdated)

## Executive Summary

The existing documentation describes an **idealized, agent-driven enrichment process** that **does NOT match current implementation**. Critical bugs and architectural gaps exist:

1. ❌ **Field mappings are NEVER retrieved from database during cleansing**
2. ❌ **No transformation from approved mappings (Asset_Name → name)**
3. ❌ **Agent receives raw CSV data unchanged, passes it through**
4. ❌ **Asset creation fails because fields have wrong names**

---

## Section-by-Section Analysis

### 1. Frontend Section

#### What Doc Says:
```
- Uses useUnifiedDiscoveryFlow to get raw_data and field_mappings
- Calls /api/v1/unified-discovery/flow/{flowId}/status
- Receives raw_data (11 records) and field_mappings (12 mappings)
```

#### What Code Actually Does:
```typescript
// DataCleansing.tsx uses MULTIPLE hooks, not just one:
- useUnifiedDiscoveryFlow(effectiveFlowId)           // General flow state
- useDataCleansingStats(effectiveFlowId)             // Stats endpoint
- useDataCleansingAnalysis(effectiveFlowId)          // Analysis endpoint
- useTriggerDataCleansingAnalysis()                  // Trigger mutation
- useLatestImport()                                  // Fallback data
```

**Actual API Calls:**
1. `/api/v1/unified-discovery/flows/{flowId}` - Get flow state
2. `/api/v1/data-cleansing/flows/{flowId}/stats` - Get cleansing stats
3. `/api/v1/data-cleansing/flows/{flowId}/analysis` - Get analysis results
4. `/api/v1/data-import/latest-import` - Fallback for raw data

#### Issues:
- ❌ Doc oversimplifies - doesn't mention specialized cleansing hooks
- ❌ Endpoint URLs don't match (uses `/data-cleansing/` not `/unified-discovery/`)
- ⚠️ Multiple data sources create confusion about single source of truth

---

### 2. Backend Trigger Flow Section

#### What Doc Says:
```
1. Endpoint: /api/v1/data-cleansing/flows/{flowId}/data-cleansing/trigger
2. Creates MasterFlowOrchestrator instance
3. Calls orchestrator.execute_phase() with phase_name: "data_cleansing"
4. CrewAI agents analyze data quality
5. Updates discovery_flows and crewai_flow_state_extensions tables
```

#### What Code Actually Does:
```python
# Phase Execution Flow (ACTUAL):
1. POST /api/v1/unified-discovery/flows/{flowId}/execute
   body: {"phase": "data_cleansing", "phase_input": {}}

2. PhaseExecutionManager.execute_phase()
   └─> DataCleansingExecutor.execute(previous_result)
       └─> DataCleansingExecutor.execute_with_crew(crew_input)

3. AgentProcessor.process_with_agent(raw_import_records)
   └─> TenantScopedAgentPool.get_agent("data_cleansing")
       └─> AgentWrapper.process(data)  # Returns data UNCHANGED!

4. DatabaseOperations.update_cleansed_data_sync(cleaned_data)
   └─> Updates raw_import_records.cleansed_data field
```

#### Issues:
- ❌ **Doc says MasterFlowOrchestrator, code uses PhaseExecutionManager + DataCleansingExecutor**
- ❌ **Doc doesn't mention TenantScopedAgentPool (the actual agent system)**
- ❌ **Doc doesn't explain data transformation pipeline**
- ❌ **CRITICAL: No mention of field mapping retrieval/application**

---

### 3. Data Storage Section

#### What Doc Says:
```
Primary Tables:
- discovery_flows: field_mappings JSONB field
- raw_import_records: raw_data JSONB field
- crewai_flow_state_extensions: flow_persistence_data
```

#### What's Missing in Doc:
```
CRITICAL TABLE NOT MENTIONED:
- import_field_mappings: Stores APPROVED user mappings
  Columns: source_field, target_field, status, confidence_score
  Example: Asset_Name → name (approved, 1.0 confidence)

THIS IS THE SOURCE OF TRUTH FOR TRANSFORMATIONS!
```

#### Current Reality:
```sql
-- Approved mappings exist in DB:
SELECT source_field, target_field, status
FROM migration.import_field_mappings
WHERE data_import_id = '...' AND status = 'approved';

-- Results (15 mappings):
Asset_Name       → name              (approved)
Asset_Type       → asset_type        (approved)
CPU_Cores        → cpu_cores         (approved)
Operating_System → operating_system  (approved)
...

-- BUT data cleansing NEVER queries this table!
```

#### Issues:
- ❌ **Doc completely omits import_field_mappings table**
- ❌ **No mention of approved mapping workflow**
- ❌ **Doesn't explain relationship between mappings and cleansing**

---

### 4. End-to-End Flow Sequence

#### What Doc Says (Step 4-5):
```
4. Backend (Orchestrator):
   - MasterFlowOrchestrator receives request
   - Executes data_cleansing phase with agent crew

5. Backend (Agent Execution):
   - CrewAI agents analyze data quality
   - Generate quality metrics and recommendations
```

#### What Actually Happens:
```
4. Backend (Executor):
   ✅ PhaseExecutionManager routes to DataCleansingExecutor
   ✅ Retrieves raw_import_records from database
   ❌ Looks for field_mappings in state (ALWAYS EMPTY!)
   ❌ Passes raw CSV data to agent unchanged

5. Backend (Agent):
   ✅ TenantScopedAgentPool returns data_cleansing agent
   ✅ AgentWrapper.process() executes
   ❌ Agent sees: {"Asset_Name": "Server01", "CPU_Cores": "4"}
   ❌ Agent returns: {"Asset_Name": "Server01", "CPU_Cores": "4"}  # UNCHANGED!
   ❌ My normalization hack: {"asset_name": "Server01", "cpu_cores": "4"}

   SHOULD BE (with field mappings):
   ✅ Agent sees: {"Asset_Name": "Server01"}
   ✅ Applies mapping: Asset_Name → name
   ✅ Returns: {"name": "Server01"}  # CORRECT!
```

#### Issues:
- ❌ **Doc describes "quality analysis" but code does data transformation**
- ❌ **No mention of field mapping application logic**
- ❌ **Doesn't explain why cleansing exists (it's to apply mappings!)**

---

## Root Cause Analysis: The Missing Link

### The Fundamental Problem

**Doc's Mental Model:**
```
Data Cleansing = Quality Analysis + Enrichment
```

**Actual Purpose:**
```
Data Cleansing = Apply Approved Field Mappings + Normalize Data
```

### The Broken Flow

#### WRONG (Current):
```
1. User approves: Asset_Name → name
2. Mapping stored in: import_field_mappings table ✅
3. Data cleansing executor runs
4. Executor looks for: self.state.field_mappings ❌ (empty!)
5. Agent receives: {"Asset_Name": "Server01"}
6. Agent returns: {"Asset_Name": "Server01"} (unchanged)
7. My hack normalizes: {"asset_name": "Server01"}
8. Asset creation expects: record.get("name") ❌ (not found!)
9. Result: Asset created as "Asset-1" with type "other"
```

#### CORRECT (What Should Happen):
```
1. User approves: Asset_Name → name
2. Mapping stored in: import_field_mappings table ✅
3. Data cleansing executor runs
4. Executor queries DB: get_field_mappings(data_import_id) ✅
5. Returns: {"Asset_Name": "name", "CPU_Cores": "cpu_cores", ...}
6. Agent/transformer applies mappings:
   Input:  {"Asset_Name": "Server01", "CPU_Cores": "4"}
   Output: {"name": "Server01", "cpu_cores": "4"}
7. Store in: raw_import_records.cleansed_data ✅
8. Asset creation reads: cleansed_data["name"] ✅
9. Result: Asset created as "Server01" with type "server" ✅
```

---

## What's Missing From Documentation

### 1. Field Mapping Application Logic
**Needs to document:**
- How approved mappings are retrieved from `import_field_mappings` table
- Transformation logic: `cleansed[mapping[source]] = raw[source]`
- Storage of transformed data in `raw_import_records.cleansed_data`

### 2. Agent vs Direct Transformation
**Needs to clarify:**
- When does agent enrich vs. direct transformation?
- Current reality: Agent is a pass-through (bug)
- Should be: Agent enriches AFTER mappings applied

### 3. Data Flow Sequence
**Needs complete flow:**
```
Attribute Mapping Phase:
  ↓ User approves mappings
  ↓ Stored in import_field_mappings

Data Cleansing Phase:
  ↓ Retrieve approved mappings
  ↓ Apply transformations (source → target)
  ↓ Store cleansed_data

Asset Inventory Phase:
  ↓ Read cleansed_data
  ↓ Create assets with correct field names
```

### 4. Database Schema Relationships
**Needs ERD showing:**
```
data_imports
    ↓ (1:N)
import_field_mappings (source_field → target_field)
    ↓ (used by)
data_cleansing phase
    ↓ (produces)
raw_import_records.cleansed_data
    ↓ (consumed by)
asset_inventory phase
```

---

## Required Documentation Changes

### HIGH PRIORITY (Critical Bugs)

1. **Section 2.2 - Add Field Mapping Retrieval:**
   ```markdown
   ### 2.2 Data Cleansing Execution Flow

   1. **Retrieve Approved Mappings:**
      - Query `import_field_mappings` table
      - Filter by `data_import_id` and `status = 'approved'`
      - Build mapping dictionary: `{source_field: target_field}`

   2. **Apply Field Transformations:**
      - For each raw record:
        - For each field in record:
          - If field in mappings: use target_field name
          - Else: keep original field name
      - Result: `cleansed_data` with correct field names

   3. **Store Cleansed Data:**
      - Update `raw_import_records.cleansed_data` JSON field
      - Enables asset inventory phase to find expected fields
   ```

2. **Section 3 - Correct E2E Flow:**
   ```markdown
   ## 3. Complete Data Flow: Mapping → Cleansing → Assets

   ### Prerequisite: Field Mapping Phase
   - User reviews AI-suggested mappings
   - Approves mappings (e.g., Asset_Name → name)
   - Stored in `import_field_mappings` table with status='approved'

   ### Data Cleansing Phase (CURRENT BUG):
   ❌ WRONG: Executor reads self.state.field_mappings (empty)
   ✅ FIX: Executor must query import_field_mappings table

   ### Asset Inventory Phase:
   - Reads raw_import_records.cleansed_data
   - Expects fields: name, asset_type, cpu_cores (snake_case)
   - Creates assets successfully when cleansing applied mappings
   ```

3. **Section 4 - Add Missing Table:**
   ```markdown
   ### Primary Tables (COMPLETE LIST):

   - **import_field_mappings**: Source of truth for transformations
     - source_field: CSV column name (e.g., "Asset_Name")
     - target_field: Database field name (e.g., "name")
     - status: 'approved' | 'rejected' | 'suggested'
     - Used by data cleansing to transform field names

   - **raw_import_records**: Raw and cleansed data storage
     - raw_data: Original CSV data (PascalCase fields)
     - cleansed_data: Transformed data (snake_case, mapped fields)
     - cleansed_data is NULL until cleansing phase completes
   ```

### MEDIUM PRIORITY (Clarifications)

4. **Clarify Agent Role:**
   - Current: Agent is pass-through (returns data unchanged)
   - Should: Agent enriches AFTER field mapping applied
   - Or: Remove agent, use direct transformation service

5. **Update API Endpoints Table:**
   - Add: `GET /api/v1/data-cleansing/flows/{flowId}/stats`
   - Add: `GET /api/v1/data-cleansing/flows/{flowId}/analysis`
   - Clarify: Which endpoint triggers phase execution?

6. **Fix Orchestrator References:**
   - Replace "MasterFlowOrchestrator" with "PhaseExecutionManager"
   - Add "DataCleansingExecutor" component
   - Add "TenantScopedAgentPool" agent system

### LOW PRIORITY (Nice-to-Have)

7. **Add Architecture Diagram:**
   - Show: Frontend → API → Executor → Agent → Database
   - Include: Field mapping retrieval step
   - Highlight: Data transformation pipeline

8. **Add Troubleshooting for Field Mapping Bug:**
   ```markdown
   ### Common Issue: Assets Created with Wrong Names

   **Symptom:** Assets show "Asset-1", "Asset-2" instead of real names

   **Root Cause:** Data cleansing not applying approved field mappings

   **Diagnosis:**
   1. Check approved mappings exist:
      SELECT * FROM import_field_mappings
      WHERE data_import_id = '...' AND status = 'approved';

   2. Check cleansed_data has transformed fields:
      SELECT cleansed_data FROM raw_import_records
      WHERE data_import_id = '...';

   3. If cleansed_data has PascalCase fields → Bug confirmed

   **Fix:** Ensure DataCleansingExecutor retrieves and applies mappings
   ```

---

## Implementation Checklist for Fixes

Before updating documentation, these code bugs must be fixed:

- [ ] **DataCleansingExecutor must retrieve field mappings:**
  - Import `get_field_mappings` from asset_inventory_executor/queries.py
  - Call in `execute_with_crew()` before agent processing
  - Pass mappings to agent/transformer

- [ ] **Apply field mapping transformations:**
  - Create `apply_field_mappings()` function in data_cleansing_utils.py
  - Transform: `{source_field: value}` → `{target_field: value}`
  - Store in `cleansed_data` with correct field names

- [ ] **Remove my snake_case normalization hack:**
  - Delete `normalize_field_name()` from data_cleansing_utils.py
  - Delete normalization in agent_processor.py and base.py
  - Rely on approved mappings instead

- [ ] **Verify asset creation works:**
  - Test with flow that has approved mappings
  - Confirm assets created with correct names/types
  - Validate cleansed_data contains expected fields

---

## Recommended Documentation Structure (New)

```markdown
# E2E Data Flow: Data Cleansing Phase

## Overview
Data cleansing applies user-approved field mappings to transform raw CSV data into
standardized database fields, enabling accurate asset creation.

## Prerequisites
- Attribute Mapping phase completed
- User has reviewed and approved field mappings
- Mappings stored in `import_field_mappings` table

## Architecture Components

### Frontend
- DataCleansing.tsx page
- useDataCleansingStats hook
- useDataCleansingAnalysis hook
- useTriggerDataCleansingAnalysis hook

### Backend
- PhaseExecutionManager (routes to executor)
- DataCleansingExecutor (orchestrates phase)
- TenantScopedAgentPool (provides agents)
- get_field_mappings() (retrieves approved mappings)
- apply_field_mappings() (transforms data)

### Database Tables
- import_field_mappings (source → target mappings)
- raw_import_records (raw_data + cleansed_data)
- discovery_flows (phase tracking)

## Data Transformation Pipeline

1. **Retrieve Approved Mappings**
2. **Load Raw Import Records**
3. **Apply Field Transformations**
4. **Store Cleansed Data**
5. **Update Phase Status**

## API Endpoints
[Complete list with actual endpoints used]

## Troubleshooting
[Include field mapping bug diagnosis]
```

---

## Summary of Changes Needed

| Section | Change Type | Priority | Description |
|---------|------------|----------|-------------|
| 2.2 Backend Processing | **ADD** | HIGH | Field mapping retrieval and application logic |
| 3 E2E Flow | **REWRITE** | HIGH | Correct sequence including mapping application |
| 4 Database Tables | **ADD** | HIGH | Document import_field_mappings table |
| 1 Frontend | **UPDATE** | MEDIUM | Add specialized cleansing hooks |
| 2 Backend | **FIX** | MEDIUM | Replace MasterFlowOrchestrator with actual components |
| 6 Troubleshooting | **ADD** | MEDIUM | Field mapping bug diagnosis |
| All | **VERIFY** | HIGH | Re-test all flows after code fixes applied |

**DO NOT update documentation until code bugs are fixed!**
