
# E2E Data Flow Analysis: Data Import

**Analysis Date:** 2025-07-13

This document provides a complete, end-to-end data flow analysis for the `Data Import` process, which initiates a `Discovery` workflow.

**Core Architecture:**
*   **Modular Services:** The backend uses a modular service architecture. The API endpoint is a thin wrapper that delegates to an orchestration service.
*   **Atomic Transactions:** All initial database records (import metadata, raw data, flow creation) are created within a single, atomic database transaction to ensure data integrity.
*   **Asynchronous Execution:** The agentic workflow is executed asynchronously in the background after the initial API request has successfully completed.

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
    *   This service calls the `MasterFlowOrchestrator`.
    *   The orchestrator creates a new flow record (`flow_type='discovery'`) in the `crewai_flow_state_extensions` table.
    *   The `data_import_id` is passed to the new flow, linking the uploaded data to the workflow.

5.  **Final Status Update**: The status in the `data_imports` record is updated to `discovery_initiated`.

6.  **Transaction Commit**: The database transaction is committed, making all created records visible.

7.  **Asynchronous Kickoff (`BackgroundExecutionService`)**:
    *   *After* the API request has returned a success response to the user, this service starts the asynchronous execution of the CrewAI agents for the newly created flow.

### Database Schema

*   **`data_imports`**: The central record for the file upload. Contains metadata and status.
*   **`raw_import_records`**: Contains the actual data from the uploaded file, one row per record.
*   **`import_field_mappings`**: Stores suggested and confirmed field mappings.
*   **`crewai_flow_state_extensions`**: The master table for all flows, including discovery flows. All other records are linked back to the `flow_id` created here.

---

## 3. End-to-End Flow Sequence: A Complete Trace

1.  **User Uploads File:** A user uploads a CSV file.
2.  **Frontend Parsing:** The `useFileUpload` hook parses the CSV data into a JSON object in the browser.
3.  **API Call:** The hook sends a `POST` request to `/api/v1/data-import/store-import`.
4.  **Backend Orchestration:** The `ImportStorageHandler` executes its full sequence (validation, storage, flow creation) within a single atomic transaction.
5.  **Successful Response:** The backend returns a `200 OK` response to the frontend, including the new `flow_id`.
6.  **Async Execution:** Simultaneously, the `BackgroundExecutionService` begins the agentic workflow on the backend.
7.  **Frontend State Update:** The frontend receives the `flow_id` and begins monitoring it for status updates.
8.  **Real-Time UI:** The UI components update in real-time to show the progress of the agents as they process the data.

---

## 4. Troubleshooting Breakpoints

| Breakpoint                        | Diagnostic Check                                                                                                    | Platform-Specific Fix                                                                                                    |
|-----------------------------------|---------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| **Upload Fails (409 Conflict)**   | A `409` error on `/store-import` means an incomplete discovery flow already exists for this client/engagement.      | Use the UI to either continue or delete the existing flow before starting a new one.                                     |
| **Flow Doesn't Start**            | Check the API response from `/store-import`. If `flow_id` is null, the backend failed during the transaction.       | `docker exec -it migration_backend bash` and check logs for errors in the `FlowTriggerService` or `MasterFlowOrchestrator`. |
| **Status Not Updating**           | Verify that the frontend is receiving WebSocket messages or that its polling requests are succeeding.                 | Check the browser's network tab. Ensure the `activeFlowId` is set correctly in the frontend state.                         |
| **Data Not Appearing in UI**       | The `raw_import_records` for the `data_import_id` might be missing or incorrect.                                    | Query the `raw_import_records` table in the database to inspect the JSON data for the corresponding `data_import_id`.      |
| **Agent Processing Error**        | Check the `state` and `result` columns in the `crewai_task_execution` table for the relevant `flow_id`.               | Examine the error messages to identify which agent failed and why. Debug the agent's logic in the `crewai_flows` service. |

