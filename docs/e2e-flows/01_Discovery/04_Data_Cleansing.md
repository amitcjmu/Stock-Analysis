# E2E Data Flow Analysis: Data Cleansing

**Analysis Date:** 2025-08-12 (Updated)

This document provides a complete, end-to-end data flow analysis for the `Data Cleansing` phase of the discovery workflow, which has evolved into a sophisticated, agent-driven asset enrichment process.

**Core Architecture:**
*   **Dual-Endpoint System:** The phase can be triggered through two different endpoints:
    *   Direct trigger endpoint: `/api/v1/data-cleansing/flows/{flow_id}/data-cleansing/trigger`
    *   Flow phase execution: `/api/v1/unified-discovery/flow/{flow_id}/execute`
*   **Agentic Enrichment with MasterFlowOrchestrator:** The system uses the `MasterFlowOrchestrator` to execute a sophisticated crew of agents for asset enrichment.
*   **State-Based Results with Database Storage:** Results are stored both in the flow's state object and in dedicated database tables for raw import records and field mappings.

---

## 1. Frontend: Initiating the Phase and Displaying Results

The `DataCleansing` page allows a user to trigger the data cleansing phase and view the results of the backend agentic analysis.

### Key Components & Hooks
*   **Page Component:** `src/pages/discovery/DataCleansing.tsx`
*   **Core Hooks:**
    *   `useDiscoveryFlowAutoDetection`: To identify the active discovery flow with auto-detection capabilities.
    *   `useUnifiedDiscoveryFlow`: To interact with the flow and read its state, including raw_data and field_mappings.
    *   `useLatestImport`: Fallback to fetch latest import data if not available in flow state.

### Data Sources
The component retrieves data from multiple sources in priority order:
1. `flow?.raw_data` - Primary source from discovery flow state
2. `flow?.field_mappings` - Field mapping data from discovery flow
3. `latestImportData?.data` - Fallback from separate API call if flow data is unavailable
4. `flow?.import_metadata?.record_count` - Metadata about imported records

### API Call Summary

| #  | Method | Endpoint                                                        | Trigger                                       | Description                                                                                               |
|----|--------|----------------------------------------------------------------|-----------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| 1  | `POST` | `/api/v1/data-cleansing/flows/{flowId}/data-cleansing/trigger` | User clicks "Trigger Analysis" button        | Primary endpoint to trigger data cleansing analysis with agent execution                                                  |
| 2  | `GET`  | `/api/v1/unified-discovery/flow/{flowId}/status`              | `useUnifiedDiscoveryFlow` hook (polling)     | Gets flow status including raw_data, field_mappings, and summary                                                          |
| 3  | `GET`  | `/api/v1/data-import/latest-import`                           | `useLatestImport` hook (fallback)            | Fallback endpoint to get import data if flow state doesn't contain it                                                     |
| 4  | `POST` | `/api/v1/unified-discovery/flow/{flowId}/execute`             | When completing phase                        | Executes flow phase transition when moving to next phase (inventory)                                                      |

---

## 2. Backend: Data Processing Architecture

### 2.1 Flow Status Service Enhancement
The `flow_status_service.py` now includes comprehensive data loading:
- Loads raw import records from `RawImportRecord` table when `data_import_id` exists
- Parses field mappings from discovery flow (supports string, dict, and list formats)
- Builds summary with record counts and completion status
- Uses `extract_raw_data` from `data_extraction_service.py` for format compatibility

### 2.2 Data Cleansing Trigger Flow

When triggered via `/api/v1/data-cleansing/flows/{flowId}/data-cleansing/trigger`:

1. **Endpoint Handler:** `trigger_data_cleansing_analysis` in `data_cleansing.py`
2. **Orchestrator Invocation:** Creates `MasterFlowOrchestrator` instance
3. **Phase Execution:** Calls `orchestrator.execute_phase()` with:
   - `phase_name`: "data_cleansing"
   - `phase_input`: includes `force_refresh` and `include_agent_analysis` flags
4. **Agent Processing:** The orchestrator triggers CrewAI agents for data quality analysis
5. **Result Storage:** Updates both:
   - `discovery_flows` table with phase status
   - `crewai_flow_state_extensions` with detailed results

### 2.3 Data Storage Structure

#### Primary Tables:
- **`discovery_flows`**: Stores flow metadata, status, and field_mappings
  - `data_import_id`: Links to imported data
  - `field_mappings`: JSONB field containing mapping definitions
  - `current_phase`: Tracks current phase (e.g., "data_cleansing")
  
- **`raw_import_records`**: Stores actual imported data records
  - Linked via `data_import_id`
  - Contains `raw_data` JSONB field with record contents

- **`crewai_flow_state_extensions`**: Stores extended flow state
  - `flow_persistence_data`: Contains agent results and metrics
  - Used for CrewAI state management

---

## 3. End-to-End Flow Sequence: Current Implementation

1. **Frontend (Data Loading):** 
   - `DataCleansing.tsx` loads with `useUnifiedDiscoveryFlow` hook
   - Calls `/api/v1/unified-discovery/flow/{flowId}/status` to get flow data
   - Receives `raw_data` (11 records) and `field_mappings` (12 mappings)

2. **Frontend (User Action):** 
   - User clicks "Trigger Analysis" button
   - Calls `handleTriggerDataCleansingCrew` function

3. **Frontend (API Call):** 
   - Sends POST to `/api/v1/data-cleansing/flows/{flowId}/data-cleansing/trigger`
   - Includes `force_refresh: true` and `include_agent_analysis: true`

4. **Backend (Orchestrator):** 
   - `MasterFlowOrchestrator` receives request
   - Executes `data_cleansing` phase with agent crew

5. **Backend (Agent Execution):** 
   - CrewAI agents analyze data quality
   - Generate quality metrics and recommendations

6. **Backend (Database Update):** 
   - Updates flow status in `discovery_flows`
   - Stores results in `crewai_flow_state_extensions`

7. **Frontend (Polling):** 
   - `useUnifiedDiscoveryFlow` polls for updates
   - Receives updated flow state with analysis results

8. **Frontend (UI Update):** 
   - Displays quality metrics, issues found, and recommendations
   - Shows completion status and enables navigation to next phase

---

## 4. Key Differences from Previous Documentation

| Aspect | Previous Documentation | Current Implementation |
|--------|----------------------|------------------------|
| **Trigger Endpoint** | `/api/v1/master-flows/{flowId}/resume` | `/api/v1/data-cleansing/flows/{flowId}/data-cleansing/trigger` |
| **Data Storage** | Only in flow state JSON | Both in dedicated tables (`raw_import_records`) and flow state |
| **Field Mappings** | Not explicitly mentioned | Stored in `discovery_flows.field_mappings` JSONB field |
| **Data Loading** | Single source | Multiple sources with fallbacks (flow state, latest import API) |
| **Flow Detection** | Manual flow ID | Auto-detection with `useDiscoveryFlowAutoDetection` |
| **Error Handling** | Fail-fast only | Includes refresh attempts and fallback data sources |

---

## 5. Troubleshooting Breakpoints

| Stage      | Potential Failure Point | Diagnostic Checks |
|------------|------------------------|-------------------|
| **Frontend** | **"0 records" displayed:** Flow status endpoint not returning `raw_data` and `field_mappings` | **Network Tab:** Check response from `/api/v1/unified-discovery/flow/{flowId}/status`. Should contain `raw_data` array and `field_mappings` object. |
| **Frontend** | **Trigger button disabled:** Missing flow ID or previous phase incomplete | **React DevTools:** Check `effectiveFlowId` and `flow?.phase_completion` in component state |
| **Backend** | **No data in response:** `flow_status_service.py` not loading data | **Docker Logs:** Look for "✅ Loaded X raw records" and "✅ Loaded Y field mappings" messages |
| **Backend** | **Agent execution fails:** MasterFlowOrchestrator error | **Docker Logs:** Check `migration_backend` for errors from `MasterFlowOrchestrator.execute_phase` |
| **Database** | **Missing raw data:** No records in `raw_import_records` | **Direct Query:** `SELECT COUNT(*) FROM migration.raw_import_records WHERE data_import_id = 'your-import-id';` |
| **Database** | **Missing field mappings:** Not stored in discovery flow | **Direct Query:** `SELECT field_mappings FROM migration.discovery_flows WHERE flow_id = 'your-flow-id';` |

---

## 6. Recent Fixes Applied

### Issue: Data Cleansing page showing "0 records"
**Root Cause:** During the modularization of `unified_discovery.py` (commit 0a0b06b8a), the data extraction logic was moved to separate services but the `flow_status_service.py` wasn't updated to include `raw_data` and `field_mappings` in the response.

**Solution Applied:**
1. Updated `flow_status_service.py` to:
   - Import `extract_raw_data` from `data_extraction_service.py`
   - Load raw import records from database when `data_import_id` exists
   - Parse and format field mappings from discovery flow
   - Build comprehensive summary object
   - Return all data in the status response

**Verification:**
- Backend now returns 11 raw data records and 12 field mappings
- Data Cleansing page correctly displays record counts and enables analysis

---

## 7. Configuration Notes

### Required Environment Variables
- Database connection must be properly configured for flow state persistence
- Redis must be available for caching and session management

### Feature Flags
- No specific feature flags required for data cleansing functionality
- Agent analysis is always enabled (no fallback mode)

### Dependencies
- CrewAI agents must be properly initialized with memory support
- MasterFlowOrchestrator requires proper context (client_id, engagement_id)
- Data extraction service must be available for format conversion