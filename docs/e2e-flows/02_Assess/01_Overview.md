
# Data Flow Analysis Report: Assess Overview Page

This document provides a complete, end-to-end data flow analysis for the `Assess Overview` page of the AI Force Migration Platform.

**Analysis Date:** 2024-07-29

**Assumptions:**
*   The analysis is based on the `AssessmentFlowOverview.tsx` component.
*   **Crucially, this component currently uses mock data.** The analysis is based on the intended API endpoints inferred from commented-out code.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.

---

## 1. Frontend: Components and API Calls

The Assess Overview page serves as the dashboard for managing and monitoring all application assessment flows.

### Key Components & Hooks
*   **Page Component:** `src/pages/assessment/AssessmentFlowOverview.tsx`
*   **Core Logic:** The page uses `useQuery` from TanStack Query to fetch its data.

### Intended API Call Summary

| # | Method | Endpoint                  | Trigger             | Description                                   |
|---|--------|---------------------------|---------------------|-----------------------------------------------|
| 1 | `GET`  | `/assessment-flow/list`   | `useQuery` on load. | Fetches a list of all assessment flows.       |
| 2 | `GET`  | `/assessment-flow/metrics`| `useQuery` on load. | Fetches aggregate metrics for the assessments. |

---

## 2. Backend, CrewAI, ORM, and Database Trace

The backend for the Assess Overview page would aggregate data from assessment-specific flows.

### API Endpoint: `GET /assessment-flow/list` (Inferred)

*   **FastAPI Route:** Would likely be located in `backend/app/api/v1/endpoints/assessment_flow.py` in a function like `@router.get("/list")`.
*   **CrewAI Interaction:** Minimal. This endpoint reads the state of existing assessment flows. It does not trigger new agent tasks.
*   **ORM Layer:**
    *   **Repository:** `MasterFlowRepository`.
    *   **Operation:** Performs a query to fetch `MasterFlow` records where the `flow_type` is 'assessment'.
    *   **Scoping:** The query is filtered by `client_account_id` and `engagement_id`.
*   **Database:**
    *   **Table:** `master_flows`
    *   **Query:** `SELECT * FROM master_flows WHERE client_account_id = ? AND engagement_id = ? AND flow_type = 'assessment';`

---

## 3. End-to-End Flow Sequence: Loading the Assess Dashboard (Intended)

1.  **User Navigates:** User loads the Assess Overview page.
2.  **Frontend Hook:** The `useQuery` hooks for `assessment-flows` and `assessment-flow-metrics` are triggered.
3.  **API Call:** A `GET` request is made to `/assessment-flow/list`.
4.  **Backend Route:** The FastAPI router directs the request to the `get_assessment_flows` function.
5.  **ORM Query:** The `MasterFlowRepository` queries the `master_flows` table, filtering for assessment flows.
6.  **DB Execution:** PostgreSQL executes the `SELECT` query.
7.  **Backend Response:** FastAPI returns the list of assessment flows as a JSON array.
8.  **UI Render:** The component renders the list of flows in the main table.

---

## 4. Troubleshooting Breakpoints

| Breakpoint              | Diagnostic Check                                                                                      | Platform-Specific Fix                                                                                              |
|-------------------------|-------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| **Page Shows No Data**  | The page is currently mocked. The first step is to implement the real API call.                       | Uncomment the `apiCall` in `useQuery` and ensure the `/assessment-flow/list` endpoint exists and is functional.     |
| **API Call Fails (404)**| If the implemented API call returns a 404, the backend route has not been created yet.                  | Create the corresponding route in `backend/app/api/v1/endpoints/assessment_flow.py`.                                |
| **Incorrect Data**      | If data is shown but is wrong, check the `WHERE` clause of the `MasterFlowRepository` query.              | Ensure the query is correctly filtering for `flow_type = 'assessment'` and by the correct `client_account_id`.     |
| **Backend Error (500)** | `docker exec -it migration_backend bash` and view FastAPI logs for database or serialization errors.      | The `MasterFlow` ORM model may have a mismatch with the `master_flows` table schema. Check model and table definitions. |


