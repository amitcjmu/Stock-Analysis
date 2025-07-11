
# Data Flow Analysis Report: Data Import Page

This document provides a complete, end-to-end data flow analysis for the `Data Import` page of the AI Force Migration Platform.

**Analysis Date:** 2024-07-29

**Assumptions:**
*   The analysis focuses on the `CMDBImport` page.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.

---

## 1. Frontend: Components and API Calls

The Data Import page is the entry point for starting a discovery flow. It allows users to upload a data file (e.g., a CMDB export), which triggers a new analysis workflow.

### Key Components & Hooks
*   **Page Component:** `src/pages/discovery/CMDBImport/index.tsx`
*   **Core Logic Hooks:**
    *   `useCMDBImport`: Orchestrates the entire data import process.
    *   `useFileUpload`: Handles the file parsing and the initial API call to the backend.
    *   `useUnifiedDiscoveryFlow`: Manages the state of the newly created flow.

### API Call Summary

| # | Method | Endpoint                          | Trigger                                 | Description                                                                 |
|---|--------|-----------------------------------|-----------------------------------------|-----------------------------------------------------------------------------|
| 1 | `POST` | `/data-import/store-import`       | `useFileUpload` hook after file upload. | Sends parsed file data to the backend to store it and initiate a new flow. |
| 2 | `GET`  | `/api/v1/flows/{flowId}/status`   | `useCMDBImport` hook (polling).         | Periodically fetches the status of the newly created and processing flow.   |

---

## 2. Backend, CrewAI, ORM, and Database Trace

The backend for data import is responsible for initiating a complex, multi-agent workflow.

### API Endpoint: `POST /data-import/store-import`

*   **FastAPI Route:** Likely located in `backend/app/api/v1/endpoints/data_import.py` in a function decorated with `@router.post("/store-import")`.
*   **CrewAI Interaction:** This is a critical trigger point.
    *   **Flow Initialization:** This endpoint call instantiates a new `MasterFlow` for the "discovery" type.
    *   **Agent Trigger:** It kicks off the `MasterFlowOrchestrator`, which starts the first phase: `data_import_validation`.
    *   **Initial Agents:** The `Data Import Validation Crew` (composed of agents like a `SecurityAgent`, `PrivacyAgent`, and `FormatValidationAgent`) is immediately tasked with analyzing the uploaded data.
*   **ORM Layer:**
    *   **Repository:** `MasterFlowRepository`, `DataImportSessionRepository`.
    *   **Operation:**
        1.  Creates a new `DataImportSession` record to log the upload event.
        2.  Creates a new `MasterFlow` record with `flow_type='discovery'` and an initial `status='initializing'`.
    *   **Scoping:** All records are created with the `client_account_id` and `engagement_id` from the context.
*   **Database:**
    *   **Tables:** `data_import_sessions`, `master_flows`.
    *   **Query:**
        *   `INSERT INTO data_import_sessions (...) VALUES (...);`
        *   `INSERT INTO master_flows (..., client_account_id, engagement_id, flow_type, status) VALUES (..., ?, ?, 'discovery', 'initializing');`

### API Endpoint: `GET /api/v1/flows/{flowId}/status`

*   This endpoint was detailed in the `Discovery Overview` report. For the Data Import page, it serves to provide real-time feedback on the agents' validation progress.

---

## 3. End-to-End Flow Sequence: Uploading a File

1.  **User Uploads File:** A user drags and drops a CSV file into the `CMDBUploadSection`.
2.  **Frontend Hook:** The `useFileUpload` hook's `handleFileUpload` function is triggered.
3.  **File Parsing:** The hook parses the CSV data into a JSON object in the browser.
4.  **API Call:** The hook calls `storeImportData`, which sends a `POST` request to `/data-import/store-import` with the parsed data.
5.  **Backend Flow Creation:** The backend receives the data, creates records in the `data_import_sessions` and `master_flows` tables, and returns the new `flow_id`.
6.  **Backend Agent Activation:** The `MasterFlowOrchestrator` starts the `data_import_validation` phase, activating the relevant CrewAI agents.
7.  **Frontend State Update:** The `useCMDBImport` hook receives the `flow_id` and sets it as the `activeFlowId`.
8.  **Polling Begins:** The `useCMDBImport` hook starts polling the `GET /api/v1/flows/{flowId}/status` endpoint every few seconds.
9.  **UI Render:** The `CMDBDataTable` and `SimplifiedFlowStatus` components render, showing the real-time progress of the validation agents as reported by the status endpoint.

---

## 4. Troubleshooting Breakpoints

| Breakpoint              | Diagnostic Check                                                                                               | Platform-Specific Fix                                                                                              |
|-------------------------|----------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| **Upload Fails**        | Check browser network tab for errors on `POST /data-import/store-import`. A 403 error indicates a context issue. | Ensure `useAuth` is providing a valid client and engagement. For admins, verify demo context is being applied correctly. |
| **Flow Doesn't Start**  | Check the response from `/store-import`. If `flow_id` is null, the backend failed to create the flow.          | `docker exec -it migration_backend bash` and check logs for errors in the `MasterFlowOrchestrator` or `DataImportValidationCrew`. |
| **Status Not Updating** | Verify the `useEffect` polling logic in `useCMDBImport` is firing. Check network tab for calls to `/status`.   | Ensure the `activeFlowId` is being set correctly after the initial `store-import` call returns.                    |
| **Agent Validation Error**| Examine the `agent_insights` object within the response from the `/status` endpoint for error messages.         | Review the logic in the specific validation agent (e.g., `SecurityAgent`) to understand why it failed the data.      |

