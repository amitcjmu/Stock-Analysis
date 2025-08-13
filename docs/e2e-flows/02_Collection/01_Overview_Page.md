# Collection Flow: 01 - Overview Page

This document provides a complete, end-to-end data flow analysis for the `Collection Overview` page in the AI Modernize Migration Platform.

**Analysis Date:** 2024-08-01

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

The backend for the Collection Overview page is responsible for creating and initializing new collection flows.

### API Endpoint: `POST /flows`

*   **FastAPI Route:** Located in `backend/app/api/v1/endpoints/collection.py`, the `create_collection_flow` function.
*   **CrewAI Interaction:**
    *   **Flow Initialization:** This call creates a new `CollectionFlow` record in the database.
    *   **Master Flow Orchestrator:** It then uses the `MasterFlowOrchestrator` to create a new master flow with `flow_type='collection'`.
    *   **Agent Trigger:** The `MasterFlowOrchestrator` starts the `initialization` phase of the collection flow, which in turn can trigger the appropriate CrewAI agents.
*   **ORM Layer:**
    *   **Operation:** Creates a new `CollectionFlow` record.
    *   **Model:** `app.models.collection_flow.CollectionFlow`
*   **Database:**
    *   **Table:** `collection_flows`
    *   **Query:** `INSERT INTO collection_flows (...) VALUES (...);`

---

## 3. End-to-End Flow Sequence: Starting a Collection Flow

1.  **User Selects Method:** The user clicks on one of the collection workflow options (e.g., "Adaptive Data Collection").
2.  **User Starts Workflow:** The user clicks the "Start Workflow" button, which triggers the `startCollectionWorkflow` function in `src/pages/collection/Index.tsx`.
3.  **Permission Check:** The `startCollectionWorkflow` function first checks if the user has the required permissions using the `canCreateCollectionFlow` utility.
4.  **API Call:** A `POST` request is sent to the `/api/v1/collection/flows` endpoint. The request body contains the `automation_tier` and `collection_config` based on the selected workflow.
5.  **Backend Creates Flow:** The `create_collection_flow` function in the backend:
    *   Checks for an existing active flow for the same engagement.
    *   Creates a new `CollectionFlow` record in the database with a status of `INITIALIZED`.
    *   Initializes a new master flow using the `MasterFlowOrchestrator`.
    *   Executes the `initialization` phase of the flow.
6.  **Frontend Navigates:** The frontend receives the response containing the new flow's ID and navigates the user to the corresponding page for that workflow (e.g., `/collection/adaptive-forms?flowId=...`).

---

## 4. Troubleshooting Breakpoints

| Breakpoint                        | Diagnostic Check                                                                                               | Platform-Specific Fix                                                                                             |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Workflow Doesn't Start**        | Check the browser's developer console for errors on the `POST /collection/flows` call. A 403 error indicates a permissions issue. A 400 error may indicate that an active flow already exists. | Ensure the user has the 'analyst' role or higher. If a flow is already active, it must be completed or canceled before starting a new one. |
| **Redirect Fails After Start**    | Verify that the `flowResponse.id` is correctly received in the frontend and that the navigation path is correct. Check for any JavaScript errors in the console after the API call succeeds. | The issue might be in the `setCurrentFlow` function or the `setTimeout` navigation logic. Debug the state updates and the `navigate` call in `src/pages/collection/Index.tsx`. |
| **Flow is Stuck in 'Initialized'** | The backend has a check for flows stuck in the `INITIALIZED` state for more than 5 minutes. If a flow is stuck, it will be automatically canceled. Check the backend logs for warnings about stale flows. | This could indicate an issue with the `MasterFlowOrchestrator` or the `initialization` phase of the CrewAI flow. `docker exec` into the `migration_backend` container and examine the logs for errors. |
