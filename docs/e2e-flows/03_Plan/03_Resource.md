
# Data Flow Analysis Report: Resource Page

This document provides a complete, end-to-end data flow analysis for the `Resource` page of the AI Modernize Migration Platform.

**Analysis Date:** 2024-07-29

**Assumptions:**
*   The analysis is based on the `Resource.tsx` page and its associated hook, `useResource`.
*   The feature is likely under development, as the hook contains fallback logic for a 404 response.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.

---

## 1. Frontend: Components and API Calls

The Resource page is designed to provide a comprehensive view of team allocation, skill sets, and resource utilization for the migration project.

### Key Components & Hooks
*   **Page Component:** `src/pages/plan/Resource.tsx`
*   **Core Logic Hook:** `useResource`: Fetches the resource data.

### API Call Summary

| # | Method | Endpoint                 | Trigger                  | Description                   |
|---|--------|--------------------------|--------------------------|-------------------------------|
| 1 | `GET`  | `/api/v1/plan/resources` | `useResource` hook on load. | Fetches the resource data.    |

---

## 2. Backend, CrewAI, ORM, and Database Trace

The backend for resource planning would involve an agent that analyzes the project timeline and required skills to generate a resource plan.

### API Endpoint: `GET /api/v1/plan/resources`

*   **FastAPI Route:** Located in `backend/app/api/v1/endpoints/plan.py`.
*   **CrewAI Interaction:**
    *   **Initial Generation:** If no resource plan exists, this call would trigger a `ResourceAllocationAgent`. This agent would analyze the `project_timeline` to understand the skills and effort required for each phase. It would then match these requirements against the available resources (teams and their skills) to generate an optimal allocation plan and identify any resource gaps.
    *   **Read Operation:** If a plan has been generated, this is a simple read.
*   **ORM Layer:**
    *   **Repository:** `ResourcePlanRepository`.
    *   **Operation:** Fetches the `ResourcePlan` for the current engagement.
*   **Database:**
    *   **Table:** `resource_plans`.
    *   **Query:** `SELECT * FROM resource_plans WHERE engagement_id = ?;`

---

## 3. End-to-End Flow Sequence: Viewing the Resource Plan

1.  **User Navigates:** The user opens the Resource page.
2.  **Frontend Hook:** The `useResource` hook is triggered.
3.  **API Call:** A `GET` request is made to `/api/v1/plan/resources`.
4.  **Backend Logic:** The backend fetches the resource plan, potentially generating it with the `ResourceAllocationAgent` if it doesn't exist.
5.  **DB Execution:** PostgreSQL returns the resource plan data.
6.  **Backend Response:** FastAPI serializes the data into JSON and returns it.
7.  **UI Render:** The component renders the team allocation table and utilization metrics.

---

## 4. Troubleshooting Breakpoints

| Breakpoint                | Diagnostic Check                                                                                      | Platform-Specific Fix                                                                                      |
|---------------------------|-------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| **Page Shows No Data**    | Check the network tab for a 404 on `/api/v1/plan/resources`. The feature may not be implemented yet.      | Implement the `/api/v1/plan/resources` endpoint on the backend and connect it to the `ResourcePlanRepository`. |
| **Resource Plan is Empty**| If the API returns an empty object, it means no `project_timeline` has been created for this engagement. | Go back to the "Timeline" page and ensure a timeline has been generated and saved first.                    |
| **Utilization is Incorrect** | The `ResourceAllocationAgent`'s logic for calculating utilization may be flawed.                      | Debug the agent's algorithm for assigning tasks and calculating team member allocation percentages.           |


