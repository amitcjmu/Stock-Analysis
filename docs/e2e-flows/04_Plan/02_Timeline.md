
# Data Flow Analysis Report: Timeline Page

This document provides a complete, end-to-end data flow analysis for the `Timeline` page of the AI Modernize Migration Platform.

**Analysis Date:** 2024-07-29

**Assumptions:**
*   The analysis is based on the `Timeline.tsx` page and its associated hook, `useTimeline`.
*   The feature is likely under development, as the hook contains fallback logic for a 404 response.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.

---

## 1. Frontend: Components and API Calls

The Timeline page is designed to provide a detailed, Gantt-like view of the migration plan, including phases, milestones, dependencies, and risks.

### Key Components & Hooks
*   **Page Component:** `src/pages/plan/Timeline.tsx`
*   **Core Logic Hook:** `useTimeline`: Fetches the timeline data.

### API Call Summary

| # | Method | Endpoint                | Trigger                   | Description                  |
|---|--------|-------------------------|---------------------------|------------------------------|
| 1 | `GET`  | `/api/v1/plan/timeline` | `useTimeline` hook on load. | Fetches the timeline data.   |

---

## 2. Backend, CrewAI, ORM, and Database Trace

The backend for the timeline would be responsible for generating a detailed project plan based on the high-level wave plan.

### API Endpoint: `GET /api/v1/plan/timeline`

*   **FastAPI Route:** Located in `backend/app/api/v1/endpoints/plan.py`.
*   **CrewAI Interaction:**
    *   **Initial Generation:** If no timeline exists, this call would trigger a `ProjectSchedulerAgent`. This agent would take the `wave_plan` as input and break it down into a detailed schedule with phases, milestones, and dependencies. It would also perform a critical path analysis and risk assessment.
    *   **Read Operation:** If a timeline has been generated, this is a simple read.
*   **ORM Layer:**
    *   **Repository:** `TimelineRepository`.
    *   **Operation:** Fetches the `Timeline` for the current engagement.
*   **Database:**
    *   **Table:** `project_timelines`.
    *   **Query:** `SELECT * FROM project_timelines WHERE engagement_id = ?;`

---

## 3. End-to-End Flow Sequence: Viewing the Timeline

1.  **User Navigates:** The user opens the Timeline page.
2.  **Frontend Hook:** The `useTimeline` hook is triggered.
3.  **API Call:** A `GET` request is made to `/api/v1/plan/timeline`.
4.  **Backend Logic:** The backend fetches the timeline data, potentially generating it with the `ProjectSchedulerAgent` if it doesn't exist.
5.  **DB Execution:** PostgreSQL returns the timeline data.
6.  **Backend Response:** FastAPI serializes the data into JSON and returns it.
7.  **UI Render:** The component renders the detailed timeline view.

---

## 4. Troubleshooting Breakpoints

| Breakpoint               | Diagnostic Check                                                                        | Platform-Specific Fix                                                                                      |
|--------------------------|-----------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| **Page Shows No Data**   | Check the network tab for a 404 on `/api/v1/plan/timeline`. The feature may not be implemented yet. | Implement the `/api/v1/plan/timeline` endpoint on the backend. Ensure it is connected to the `TimelineRepository`. |
| **Timeline is Empty**    | If the API returns an empty object, it means no `WavePlan` has been created for this engagement. | Go back to the "Wave Planning" page and ensure a plan has been generated and saved first, as the timeline depends on it. |
| **Critical Path is Wrong** | The `ProjectSchedulerAgent`'s critical path analysis logic may be flawed.              | Debug the agent's algorithm for identifying dependencies and calculating the critical path.                 |

