
# E2E Data Flow Analysis: Data Import

**Analysis Date:** 2025-07-30
**Status:** Updated to reflect current implementation

This document provides a complete, end-to-end data flow analysis for the `Data Import` process, which initiates a `Discovery` workflow.

**Core Architecture:**
*   **Modular Services:** The backend uses a modular service architecture. The API endpoint is a thin wrapper that delegates to an orchestration service.
*   **Atomic Transactions:** All initial database records (import metadata, raw data, flow creation) are created within a single, atomic database transaction to ensure data integrity.
*   **Asynchronous Execution:** The agentic workflow is executed asynchronously in the background after the initial API request has successfully completed.
*   **Phase-based Execution:** Uses a PhaseController to manage step-by-step flow execution with pause/resume capabilities for user approvals.
*   **Master Flow Orchestrator:** All flows are created through the MasterFlowOrchestrator which manages flow lifecycle and state.

---

## 1. Frontend: Initiating the Import

The Data Import page allows users to upload a data file (e.g., a CMDB export), which triggers the entire discovery analysis workflow.

### Key Components & Hooks
*   **Page Component:** `src/pages/discovery/CMDBImport/index.tsx`
*   **File Upload Logic:** `src/pages/discovery/CMDBImport/hooks/useFileUpload.ts`
*   **Flow State Management:** `src/hooks/useUnifiedDiscoveryFlow.ts`

### API Call Summary

| # | Method | Endpoint                          | Trigger                                 | Description                                                                                               |
|---|--------|-----------------------------------|-----------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| 1 | `POST` | `/api/v1/data-import/store-import`| `useFileUpload` hook after file upload. | Sends the entire parsed file data to the backend to be stored and to trigger the Unified Discovery Flow.          |
| 2 | `GET`  | (WebSocket or Polling)            | `useUnifiedDiscoveryFlow` hook.         | After the flow is created, the frontend listens for real-time status updates on the flow's progress. |

---

## 2. Backend: Modular Service Orchestration

The backend is architected as a set of modular, single-responsibility services that are orchestrated by a central handler.

### API Endpoint: `POST /api/v1/data-import/store-import`

*   **FastAPI Route:** Defined in `backend/app/api/v1/endpoints/data_import/handlers/import_storage_handler.py`.
*   **Orchestration Service:** The endpoint immediately delegates to the `handle_import` method in `backend/app/services/data_import/import_storage_handler.py`.

### Service-Layer Execution Flow

The `ImportStorageHandler` service executes the following sequence:

1.  **Validation (`ImportValidator`)**:
    *   Validates the request context (`client_account_id`, `engagement_id`).
    *   Checks for any existing, incomplete discovery flows for the current context to prevent conflicts.
    *   Validates the data itself (e.g., checks for valid CSV headers).

2.  **Atomic Transaction (`ImportTransactionManager`)**: All subsequent database operations are wrapped in a single transaction.

3.  **Data Persistence (`ImportStorageManager`)**:
    *   A new record is created in the `data_imports` table to track the upload.
    *   All rows from the uploaded file are stored as JSON in the `raw_import_records` table.
    *   Initial suggestions are created in the `import_field_mappings` table.
    *   The status in the `data_imports` table is updated to `processing`.

4.  **Flow Creation (`FlowTriggerService`)**:
    *   This service calls the `MasterFlowOrchestrator` in atomic mode to prevent early commits.
    *   The orchestrator creates a new flow record (`flow_type='discovery'`) in the `crewai_flow_state_extensions` table.
    *   The service then creates a corresponding record in the `discovery_flows` table, following the MFO two-table design pattern.
    *   The `data_import_id` is passed as part of the initial_state along with raw_data from the file.
    *   Both master and child flow records use the same flow_id for consistency.
    *   UUID serialization is handled by converting all UUIDs to strings before JSON storage.

5.  **Final Status Update**: The status in the `data_imports` record is updated to `discovery_initiated`.

6.  **Transaction Commit**: The database transaction is committed, making all created records visible.

7.  **Asynchronous Kickoff (`BackgroundExecutionService`)**:
    *   *After* the API request has returned a success response to the user, this service starts the asynchronous execution of the CrewAI agents for the newly created flow.
    *   Creates a UnifiedDiscoveryFlow instance with the master_flow_id parameter.
    *   Uses PhaseController to execute phases sequentially rather than automatic @listen chains.
    *   Monitors phase results to determine when user input is required (e.g., field mapping approval).
    *   Updates flow status through CrewAIFlowStateExtensionsRepository.

### Database Schema

*   **`data_imports`**: The central record for the file upload. Contains metadata and status.
    *   Has `master_flow_id` column linking to CrewAI flow
*   **`raw_import_records`**: Contains the actual data from the uploaded file, one row per record.
    *   Stores data as JSONB in `raw_data` column
    *   Has `master_flow_id` column for flow association
*   **`import_field_mappings`**: Stores suggested and confirmed field mappings.
    *   Uses intelligent mapping helpers for field suggestions
    *   Has `master_flow_id` column for flow association
*   **`crewai_flow_state_extensions`**: The master table for all flows, including discovery flows.
    *   Primary flow record with `flow_id` as unique identifier
    *   All other records reference this via foreign keys
*   **`discovery_flows`**: Discovery-specific flow tracking table (part of MFO two-table design)
    *   Links to master flow via `master_flow_id`
    *   Contains discovery-specific fields like `data_import_id` and phase completion flags
    *   Required for proper UI operation and API endpoints

---

## 3. End-to-End Flow Sequence: A Complete Trace

1.  **User Uploads File:** A user uploads a CSV file.
2.  **Frontend Parsing:** The `useFileUpload` hook parses the CSV data into a JSON object in the browser.
3.  **API Call:** The hook sends a `POST` request to `/api/v1/data-import/store-import`.
4.  **Backend Orchestration:** The `ImportStorageHandler` executes its full sequence within a single atomic transaction:
    *   Validates request context and data
    *   Creates DataImport record
    *   Stores raw records in database
    *   Creates field mappings with intelligent suggestions
    *   Triggers flow creation through MasterFlowOrchestrator
    *   Creates discovery flow child record via DiscoveryFlowService
    *   Links all records with master_flow_id
5.  **Successful Response:** The backend returns a `200 OK` response to the frontend, including the new `flow_id`.
6.  **Async Execution:** The `BackgroundExecutionService` begins the phased workflow execution:
    *   Creates UnifiedDiscoveryFlow instance
    *   Initializes PhaseController for controlled execution
    *   Executes initialization phase first
    *   Continues through phases until user input required
7.  **Frontend State Update:** The frontend receives the `flow_id` and begins monitoring it for status updates.
8.  **Real-Time UI:** The UI components update in real-time to show the progress of the agents as they process the data.
9.  **Phase Execution:** Flow proceeds through phases:
    *   Initialization → Data Validation → Field Mapping Suggestions → **[Pause for User Approval]**
    *   After approval: Data Cleansing → Asset Inventory → Parallel Analysis → Completion

---

## 4. Troubleshooting Breakpoints

| Breakpoint                        | Diagnostic Check                                                                                                    | Platform-Specific Fix                                                                                                    |
|-----------------------------------|---------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| **Upload Fails (409 Conflict)**   | A `409` error on `/store-import` means an incomplete discovery flow already exists for this client/engagement.      | Use the UI to either continue or delete the existing flow before starting a new one.                                     |
| **Flow Doesn't Start**            | Check the API response from `/store-import`. If `flow_id` is null, the backend failed during the transaction.       | Check logs for UUID serialization errors or atomic transaction failures in `FlowTriggerService`.                         |
| **Discovery Flow Not Found**      | API calls fail with "Discovery flow not found" despite master flow existing.                                        | Ensure `DiscoveryFlowService.create_discovery_flow` is called after master flow creation. Check both tables have records.|
| **Flow Stuck on "Processing"**    | Flow initialization may be returning wrong status. Check phase_controller.py initialization logic.                  | Ensure `initialize_discovery` result status is properly checked (dict with status field, not string comparison).         |
| **Status Not Updating**           | Verify that the frontend is receiving WebSocket messages or that its polling requests are succeeding.               | Check Redis cache availability and flow registration. Ensure agent-ui-bridge WebSocket connection is active.             |
| **Data Not Appearing in UI**      | Check if raw data is loaded from database in UnifiedDiscoveryFlow initialization.                                  | Query `raw_import_records` table. Check `load_raw_data_from_database` in data_utilities.py is executing.               |
| **Phase Execution Fails**         | Check PhaseController execution and phase result handling.                                                         | Review phase_controller.py phase methods. Ensure proper error handling and state persistence between phases.            |
| **UUID Serialization Error**      | "Object of type UUID is not JSON serializable" errors in flow creation.                                           | Ensure `convert_uuids_to_str` is applied to configuration and initial_state before passing to MasterFlowOrchestrator.   |
| **Field Mapping Pause Not Working** | Flow doesn't pause at field mapping approval phase.                                                              | Check if PhaseExecutionResult.requires_user_input is set correctly in phase_controller field mapping methods.          |
| **Agent Processing Error**        | Check the `state` and `result` columns in the `crewai_task_execution` table for the relevant `flow_id`.               | Examine the error messages to identify which agent failed and why. Debug the agent's logic in the `crewai_flows` service. |

---

## 5. Technical Implementation Details

### Phase Controller Architecture
The Discovery flow uses a PhaseController (`phase_controller.py`) that manages sequential phase execution:
- Replaces automatic @listen chains with explicit phase control
- Allows proper pause/resume for user input
- Prevents rate limiting from concurrent phase execution
- Each phase returns a PhaseExecutionResult with status and next phase

### Key Phase Transitions
1. **Initialization**: Loads raw data, sets up flow state
2. **Data Validation**: Validates imported data structure
3. **Field Mapping Suggestions**: AI generates mapping suggestions
4. **Field Mapping Approval**: **PAUSES** for user approval
5. **Data Cleansing**: Cleans data based on approved mappings
6. **Asset Inventory**: Creates discovery assets
7. **Parallel Analysis**: Runs dependency and tech debt analysis
8. **Finalization**: Completes flow and prepares results

### State Management
- Flow state persisted in `crewai_flow_state_extensions` table
- Phase-specific data stored in `phase_data` JSONB column
- Flow state includes `current_phase`, `status`, and phase results
- Redis cache used for quick state access and flow deduplication

### Error Handling
- Each phase has try-catch with specific error handling
- Failed phases update flow status to 'failed' with error details
- Error notifications sent via agent-ui-bridge
- Retry logic handled by MasterFlowOrchestrator

### Important Code Patterns
```python
# UUID Serialization (prevents JSON errors)
configuration = convert_uuids_to_str({
    "import_id": data_import_id,
    # ...
})

# Atomic Flow Creation
flow_result = await orchestrator.create_flow(
    flow_type="discovery",
    atomic=True,  # Prevents early commit
)

# Child Flow Creation (MFO Two-Table Pattern)
if flow_result and flow_result[0]:
    discovery_service = DiscoveryFlowService(db, context)
    await discovery_service.create_discovery_flow(
        flow_id=str(flow_result[0]),
        master_flow_id=str(flow_result[0]),
        data_import_id=data_import_id,
        # ...
    )

# Phase Result Checking
is_successful = isinstance(result, dict) and result.get("status") in [
    "initialized",
    "initialization_completed",
]
```

