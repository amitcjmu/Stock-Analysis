
# Data Flow Analysis Report: Wave Planning Page

This document provides a complete, end-to-end data flow analysis for the `Wave Planning` page of the AI Force Migration Platform.

**Analysis Date:** 2024-07-29

**Assumptions:**
*   The analysis is based on the `WavePlanning.tsx` page and its associated hook, `useWavePlanning`.
*   The feature is marked as "Coming Soon," and the analysis is based on the intended API endpoints.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.

---

## 1. Frontend: Components and API Calls

The Wave Planning page is designed to allow users to group applications into migration waves and schedule them over time.

### Key Components & Hooks
*   **Page Component:** `src/pages/assess/WavePlanning.tsx`
*   **Core Logic Hooks:**
    *   `useWavePlanning`: Fetches the wave planning data.
    *   `useUpdateWavePlanning`: Saves changes to the wave plan.

### API Call Summary

| # | Method | Endpoint                   | Trigger                            | Description                         |
|---|--------|----------------------------|------------------------------------|-------------------------------------|
| 1 | `GET`  | `/api/v1/wave-planning`    | `useWavePlanning` hook on load.    | Fetches the current wave plan.      |
| 2 | `PUT`  | `/api/v1/wave-planning`    | `useUpdateWavePlanning` hook (not yet used). | Saves an updated version of the wave plan. |

---

## 2. Backend, CrewAI, ORM, and Database Trace

The backend for wave planning involves a specialized agent that uses the results of the 6R analysis to create an optimal migration schedule.

### API Endpoint: `GET /api/v1/wave-planning`

*   **FastAPI Route:** Located in `backend/app/api/v1/endpoints/wave_planning.py`.
*   **CrewAI Interaction:**
    *   **Initial Analysis (if no plan exists):** If no wave plan exists, this endpoint might trigger the `Wave Planning Coordinator` agent to generate a draft plan. The agent would analyze the `sixr_analyses` results, considering dependencies, business criticality, and migration complexity to group applications into logical waves.
    *   **Read Operation:** If a plan already exists, this is a simple read operation.
*   **ORM Layer:**
    *   **Repository:** `WavePlanRepository`.
    *   **Operation:** Fetches the `WavePlan` for the current engagement.
    *   **Scoping:** Filtered by `client_account_id` and `engagement_id`.
*   **Database:**
    *   **Table:** `wave_plans`
    *   **Query:** `SELECT * FROM wave_plans WHERE engagement_id = ?;`

### API Endpoint: `PUT /api/v1/wave-planning`

*   **FastAPI Route:** An `update_wave_plan` function in `wave_planning.py`.
*   **CrewAI Interaction:** Minimal. This endpoint primarily serves to persist user-defined changes to the wave plan. It might trigger a validation task by the `Wave Planning Coordinator` to ensure the user's changes are logical.
*   **ORM Layer:**
    *   **Operation:** Updates the existing `WavePlan` record.
*   **Database:**
    *   **Table:** `wave_plans`
    *   **Query:** `UPDATE wave_plans SET plan_data = ? WHERE id = ? AND engagement_id = ?;`

---

## 3. End-to-End Flow Sequence: Viewing the Wave Plan

1.  **User Navigates:** The user opens the Wave Planning page.
2.  **Frontend Hook:** The `useWavePlanning` hook is triggered.
3.  **API Call:** A `GET` request is made to `/api/v1/wave-planning`.
4.  **Backend Logic:**
    *   If a plan exists, the backend fetches it from the `wave_plans` table.
    *   If no plan exists, the backend tasks the `Wave Planning Coordinator` agent to generate a draft, saves it, and then returns it.
5.  **DB Execution:** PostgreSQL returns the wave plan data.
6.  **Backend Response:** FastAPI serializes the plan into JSON and returns it.
7.  **UI Render:** The component renders the waves and the summary dashboard.

---

## 4. Troubleshooting Breakpoints

| Breakpoint                 | Diagnostic Check                                                                                           | Platform-Specific Fix                                                                                              |
|----------------------------|------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| **Page Shows No Data**     | Check the network tab for a 404 on `/api/v1/wave-planning`. Check the hook's `enabled` flag.                 | The `useAuth` context must provide a valid client and engagement for the API call to be enabled.                  |
| **Agent Fails to Generate Plan** | If the initial `GET` request hangs or returns a 500 error, the `Wave Planning Coordinator` may have failed. | Check the backend logs for errors within the `Wave Planning Coordinator` agent. It might be missing dependency data from the Discovery phase. |
| **Updates Don't Save**       | If the `PUT` request fails, check the payload being sent.                                                   | The user's changes may have created an invalid state (e.g., circular dependencies). The validation logic in the `update_wave_plan` endpoint should be checked. |

