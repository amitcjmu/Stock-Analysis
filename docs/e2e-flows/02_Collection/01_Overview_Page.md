# Collection Flow: 01 - Overview Page

This document provides a complete, end-to-end data flow analysis for the `Collection Overview` page in the AI Modernize Migration Platform.

**Analysis Date:** 2024-08-01 (Updated)

**Assumptions:**
*   The analysis focuses on the `src/pages/collection/Index.tsx` page and its associated hooks and services.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.

---

## 1. Frontend: Components and API Calls

The Collection Overview page is the central hub for initiating and monitoring all data collection activities. It allows users to choose from different collection methods and view the status of ongoing flows.

### Key Components & Hooks
*   **Page Component:** `src/pages/collection/Index.tsx`
*   **API Client:** `src/services/api/collection-flow.ts` is used for all collection-related API interactions.
*   **Auth Context:** `useAuth` from `src/contexts/AuthContext.ts` is used to manage the current flow and user permissions.
*   **RBAC Utilities:** `canCreateCollectionFlow` and `getRoleName` from `src/utils/rbac.ts` are used to control access to creating collection flows.

### API Call Summary

| # | Method | Endpoint           | Trigger                           | Description                               |
|---|--------|--------------------|-----------------------------------|-------------------------------------------|
| 1 | `POST` | `/collection/flows`| `startCollectionWorkflow` function | Creates a new collection flow.            |

---

## 2. Backend, CrewAI, ORM, and Database Trace

The backend for the Collection Overview page is responsible for creating and initializing new collection flows, which now run as background processes.

### API Endpoint: `POST /flows`

*   **FastAPI Route:** Located in `backend/app/api/v1/endpoints/collection.py`, which delegates to `create_collection_flow` in `.../collection_crud_create_commands.py`.
*   **CrewAI Interaction:**
    *   **Flow Initialization:** This call creates a `CollectionFlow` record (the "child" flow).
    *   **Master Flow Orchestrator (MFO):** It then calls `create_mfo_flow` to create a new "master" flow in the MFO framework. The `master_flow_id` is saved on the `CollectionFlow` record.
    *   **Background Execution:** After creation, the `initialize_mfo_flow_execution` function is called, which starts the flow as a background task. This function has an idempotency check to prevent duplicate starts.
*   **ORM Layer:**
    *   **Operation:** Creates a new `CollectionFlow` record and then updates it with the `master_flow_id`.
    *   **Model:** `app.models.collection_flow.CollectionFlow`
*   **Database:**
    *   **Table:** `collection_flows`
    *   **Query:** `INSERT INTO collection_flows (...) VALUES (...); UPDATE collection_flows SET master_flow_id = ? WHERE id = ?;`

---

## 3. End-to-End Flow Sequence: Starting a Collection Flow

1.  **User Selects Method:** The user clicks on one of the collection workflow options (e.g., "Adaptive Data Collection").
2.  **User Starts Workflow:** The user clicks the "Start Workflow" button, which triggers the `startCollectionWorkflow` function in `src/pages/collection/Index.tsx`.
3.  **Permission Check:** The function first checks if the user has the required permissions using the `canCreateCollectionFlow` utility.
4.  **API Call:** A `POST` request is sent to the `/api/v1/collection/flows` endpoint. The request body contains the `automation_tier` and `collection_config`.
5.  **Backend Creates Flow:** The `create_collection_flow` function in the backend:
    *   Creates a `CollectionFlow` record with a status of `INITIALIZED`.
    *   Creates a corresponding master flow using the `MasterFlowOrchestrator`.
    *   Saves the `master_flow_id` on the `CollectionFlow` record.
    *   **Crucially, it then kicks off the flow as a background task via `initialize_mfo_flow_execution`.**
6.  **Frontend Navigates:** The frontend receives the response containing the new child flow's ID (`flow_id`) and navigates the user to the corresponding page (e.g., `/collection/adaptive-forms?flowId=...`). The flow is now running in the background.

---

## 4. Troubleshooting Breakpoints

| Breakpoint                        | Diagnostic Check                                                                                               | Platform-Specific Fix                                                                                             |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Workflow Doesn't Start**        | Check the browser's developer console for errors on the `POST /collection/flows` call. A 409 Conflict error indicates that an active flow already exists. | Ensure no other collection flows are running for the current engagement. The new logic prevents multiple active flows more robustly. |
| **Flow is Stuck in 'Initialized'** | The new `is_flow_stuck_in_initialization` utility and the `flow_health_monitor` service are designed to detect this. Check the backend logs for warnings about stale flows being canceled or recovered. | The background task may have failed to start. `docker exec` into the `migration_backend` container and examine the logs for errors related to `initialize_mfo_flow_execution` or the Celery workers. |
| **Master Flow ID is Missing**     | If the `master_flow_id` on the `collection_flows` table is NULL, the call to `create_mfo_flow` failed. The API response to the frontend will include a `warning` in this case. | This indicates a problem with the `MasterFlowOrchestrator` service itself. Check the backend logs for errors during the MFO `create_flow` call. |
