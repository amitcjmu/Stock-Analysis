
# Data Flow Analysis Report: Discovery Overview Page

This document provides a complete, end-to-end data flow analysis for the `Discovery Overview` page of the AI Force Migration Platform.

**Analysis Date:** 2024-07-29

**Assumptions:**
*   The analysis focuses on the `EnhancedDiscoveryDashboard` and its associated components and hooks.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.

---

## 1. Frontend: Components and API Calls

The Discovery Overview page acts as a central hub for monitoring all active discovery flows, system metrics, and agent performance.

### Key Components & Hooks
*   **Page Component:** `src/pages/discovery/EnhancedDiscoveryDashboard/index.tsx`
*   **Core Logic Hooks:**
    *   `useDashboard`: Orchestrates all data fetching for the dashboard.
    *   `useFlowOperations`: Handles flow management actions like deletion and resumption.
*   **Data Fetching Service:** `dashboardService`

### API Call Summary

| # | Method | Endpoint                                        | Trigger                                           | Description                                      |
|---|--------|-------------------------------------------------|---------------------------------------------------|--------------------------------------------------|
| 1 | `GET`  | `/api/v1/discovery/flows/active`                | `dashboardService.fetchDashboardData`             | Fetches all active discovery flows.              |
| 2 | `GET`  | `/api/v1/data-import/latest-import`             | `dashboardService.fetchDashboardData` (fallback)  | Gets the latest import session to find orphan flows. |
| 3 | `GET`  | `/api/v1/discovery/flows/{id}/status`           | `dashboardService.fetchDashboardData` (conditional) | Gets status for a flow found via latest import.  |
| 4 | `GET`  | `/master-flows/active?flowType=discovery`       | `useIncompleteFlowDetectionV2`                    | Fetches active flows to filter for incomplete ones. |
| 5 | `DELETE`| `/master-flows/{flowId}`                        | `useFlowDeletionV2` hook                          | Deletes a specified discovery flow.              |
| 6 | `POST` | `/flows/{flowId}/resume`                        | `useFlowResumptionV2` hook                        | Resumes a paused or incomplete discovery flow.   |

---

## 2. Backend, CrewAI, ORM, and Database Trace

The backend for the overview page is designed for aggregation and monitoring.

### API Endpoint: `GET /api/v1/discovery/flows/active`

*   **FastAPI Route:** Likely located in `backend/app/api/v1/endpoints/discovery_flows.py` in a function decorated with `@router.get("/flows/active")`.
*   **CrewAI Interaction:** Minimal. This endpoint primarily reads the state of existing flows, which are managed by various CrewAI agents in the background. It does not trigger new agent tasks.
*   **ORM Layer:**
    *   **Repository:** `MasterFlowRepository` (or a similar name) using the `ContextAwareRepository` pattern.
    *   **Operation:** Performs a query to fetch all `MasterFlow` records.
    *   **Scoping:** The query is filtered by `client_account_id` and `engagement_id` from the context headers, and `flow_type='discovery'`.
*   **Database:**
    *   **Table:** `master_flows`
    *   **Query:** `SELECT * FROM master_flows WHERE client_account_id = ? AND engagement_id = ? AND flow_type = 'discovery' AND status != 'completed' AND status != 'failed';`

### API Endpoint: `DELETE /master-flows/{flowId}`

*   **FastAPI Route:** Located in `backend/app/api/v1/endpoints/master_flow.py` in a function like `delete_flow`.
*   **CrewAI Interaction:** Triggers a "cleanup" or "teardown" task. This may involve instructing agents to release resources, delete temporary data from their memory, and archive any results. The `OrchestrationAgent` would likely coordinate this.
*   **ORM Layer:**
    *   **Operation:** Deletes the `MasterFlow` record and cascades deletes to related state tables.
    *   **Scoping:** The operation is validated against the `client_account_id` and `engagement_id` before deletion.
*   **Database:**
    *   **Tables:** `master_flows`, `flow_run_state`, `agent_insights`, `asset_inventory`, etc. (via cascading deletes).
    *   **Query:** `DELETE FROM master_flows WHERE id = ? AND client_account_id = ?;`

---

## 3. End-to-End Flow Sequence: Loading the Dashboard

1.  **User Navigates:** User loads the Discovery Overview page.
2.  **Frontend Hook:** `useDashboard` hook is initialized.
3.  **API Call:** `dashboardService.fetchDashboardData` is called, triggering a `GET` request to `/api/v1/discovery/flows/active`.
4.  **Backend Route:** The FastAPI router directs the request to the `get_active_flows` function.
5.  **ORM Query:** The `MasterFlowRepository` queries the `master_flows` table, filtered by the client context and for active discovery flows.
6.  **DB Execution:** PostgreSQL executes the `SELECT` query and returns the matching flow records.
7.  **Backend Response:** FastAPI serializes the ORM models into a JSON array and returns it to the frontend.
8.  **Frontend State Update:** The response populates the `activeFlows` state in the `useDashboard` hook.
9.  **UI Render:** The `EnhancedDiscoveryDashboardContainer` and its child components render, displaying the list of active flows in the `FlowsOverview` component.

---

## 4. Troubleshooting Breakpoints

| Breakpoint        | Diagnostic Check                                                                                                | Platform-Specific Fix                                                                                              |
|-------------------|-----------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| **No Flows Shown**  | Check browser network tab for errors on `/api/v1/discovery/flows/active`. Verify `X-Client-Account-ID` header.    | Ensure the `useAuth` context is providing the correct client/engagement IDs.                                       |
| **Flow Deletion Fails** | Check console for 403 (Forbidden) or 404 (Not Found) on `DELETE /master-flows/{flowId}`.                         | Verify `masterFlowService.deleteFlow` is passing the correct multi-tenant headers.                                 |
| **Stale Data**      | Examine the `lastUpdated` timestamp on the dashboard. Check if `dashboardService` caching is stuck.             | Use the "Refresh" button on the UI to force a call to `fetchDashboardData` and bypass the cache.                   |
| **Backend Error**   | `docker exec -it migration_backend bash` and view FastAPI logs. Check for database connection or query errors.    | Validate the `ContextAwareRepository` is correctly injecting the `client_account_id` into the `WHERE` clause.      |

