
# E2E Data Flow Analysis: Discovery Overview

**Analysis Date:** 2025-07-13

This document provides a complete, end-to-end data flow analysis for the `Discovery Overview` page, which serves as the central monitoring hub for all discovery workflows.

**Core Architecture:**
*   **Consolidated API:** All flow management (listing, deleting, resuming) is handled through the unified `/api/v1/master-flows/` endpoint.
*   **Service-Driven Frontend:** The frontend uses a dedicated `DashboardService` with built-in caching, request deduplication, and retry logic to manage data fetching efficiently.
*   **Database as Source of Truth:** The dashboard directly reflects the state of flows as recorded in the `crewai_flow_state_extensions` table.

---

## 1. Frontend: Dashboard Orchestration

The Discovery Overview page aggregates data from multiple sources to provide a real-time snapshot of system and agent performance.

### Key Components & Hooks
*   **Page Component:** `src/pages/discovery/EnhancedDiscoveryDashboard/index.tsx`
*   **State Management Hook:** `src/pages/discovery/EnhancedDiscoveryDashboard/hooks/useDashboard.ts`
*   **Data Fetching Service:** `src/pages/discovery/EnhancedDiscoveryDashboard/services/dashboardService.ts`
*   **Flow Management Hooks:** `useIncompleteFlowDetectionV2`, `useFlowDeletion`

### API Call Summary

| # | Method | Endpoint                                  | Trigger                                       | Description                                                                              |
|---|--------|-------------------------------------------|-----------------------------------------------|------------------------------------------------------------------------------------------|
| 1 | `GET`  | `/api/v1/master-flows/active`             | `DashboardService.fetchDashboardData`         | Fetches all active flows, filtered by `flowType=discovery`.                              |
| 2 | `GET`  | `/api/v1/data-import/latest-import`       | `DashboardService.fetchDashboardData` (Parallel) | Fetches the latest data import session as a fallback to identify any orphaned flows.     |
| 3 | `DELETE`| `/api/v1/master-flows/{flowId}`           | `useFlowDeletion` hook                        | Marks a specified discovery flow and all its children as "deleted" in the database.      |
| 4 | `POST` | `/api/v1/flows/{flowId}/resume`           | `useFlowResumptionV2` hook                     | Resumes a paused or incomplete discovery flow.                                           |

---

## 2. Backend: Consolidated Flow Management

The backend provides a single set of endpoints for managing flows across all phases.

### API Endpoint: `GET /api/v1/master-flows/active`

*   **FastAPI Route:** Defined in `backend/app/api/v1/master_flows.py`.
*   **CrewAI Interaction:** None. This is a read-only endpoint that queries the existing state of flows.
*   **ORM Layer:**
    *   **Operation:** Performs a `SELECT` query on the `CrewAIFlowStateExtensions` model.
    *   **Scoping:** The query is filtered by the `client_account_id` from the user's context and, optionally, by the `flowType` query parameter.
    *   **Filtering:** It explicitly excludes flows with a status of `completed`, `failed`, `error`, `deleted`, or `cancelled`.
*   **Database:**
    *   **Table:** `crewai_flow_state_extensions`
    *   **Query:** `SELECT * FROM crewai_flow_state_extensions WHERE client_account_id = ? AND flow_type = 'discovery' AND flow_status NOT IN ('completed', 'failed', ...);`

### API Endpoint: `DELETE /api/v1/master-flows/{flowId}`

*   **FastAPI Route:** Defined in `backend/app/api/v1/master_flows.py`.
*   **Logic:**
    *   The function retrieves the specified master flow.
    *   It updates the `flow_status` of the master flow to `deleted`.
    *   It then finds all **child flows** linked to the master flow and updates their statuses to `child_flows_deleted`.
    *   This is a "soft delete" that preserves the records for auditing but removes them from active view.
*   **Database:**
    *   **Table:** `crewai_flow_state_extensions`
    *   **Query:** `UPDATE crewai_flow_state_extensions SET flow_status = 'deleted' WHERE flow_id = ?;` (and a similar query for child flows).

---

## 3. End-to-End Flow Sequence: Loading the Dashboard

1.  **User Navigates:** The user loads the Discovery Overview page.
2.  **Frontend Hook:** The `useDashboard` hook is initialized, which calls `fetchDashboardData` from the `DashboardService`.
3.  **API Call:** The `DashboardService` triggers a `GET` request to `/api/v1/master-flows/active?flowType=discovery`.
4.  **Backend Route:** FastAPI directs the request to the `get_active_master_flows` function in `master_flows.py`.
5.  **DB Query:** The function queries the `crewai_flow_state_extensions` table for all active discovery flows matching the user's context.
6.  **Backend Response:** The backend serializes the flow records into a JSON array and returns them.
7.  **Frontend State Update:** The response populates the `activeFlows` state in the `useDashboard` hook.
8.  **UI Render:** The `EnhancedDiscoveryDashboardContainer` and its child components render the list of active flows.

---

## 4. Troubleshooting Breakpoints

| Breakpoint        | Diagnostic Check                                                                                                | Platform-Specific Fix                                                                                              |
|-------------------|-----------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| **No Flows Shown**  | Check the browser network tab for errors on `GET /api/v1/master-flows/active`. Verify a valid `flowType` is sent. | Ensure the `useAuth` context is providing the correct `client_account_id` and `engagement_id`.                     |
| **Flow Deletion Fails** | Check console for 403 (Forbidden) or 404 (Not Found) on `DELETE /master-flows/{flowId}`.                         | Verify the `flow_id` is correct and that the user has permission for the associated `client_account_id`.           |
| **Stale Data**      | The `DashboardService` caches data for 30 seconds. Check the `lastUpdated` timestamp on the dashboard.          | Use the "Refresh" button on the UI. This bypasses the cache in the `DashboardService` and forces a fresh API call. |
| **Backend Error**   | `docker exec -it migration_backend bash` and view FastAPI logs. Check for database connection or query errors.    | Validate the query in `get_active_master_flows` is filtering correctly by `client_account_id`.                   |

