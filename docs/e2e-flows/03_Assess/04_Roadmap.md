
# Data Flow Analysis Report: Roadmap Page

**Analysis Date:** October 16, 2025
**Status:** ⚠️ PARTIALLY UPDATED (Core architecture unchanged since 2024-07-29)

**Note:** This page's implementation remains largely unchanged from the previous version. The major updates in PR #600 focused on the **Assessment Overview page** (see `01_Overview.md` for comprehensive details on the new ApplicationGroupsWidget, ReadinessDashboardWidget, and AssessmentApplicationResolver service).

The Roadmap page continues to function as previously documented, with the following key reminders:
- All database tables reside in `migration` schema (not `public`)
- All field names use snake_case (per CLAUDE.md requirements)
- Multi-tenant scoping required on all database queries (client_account_id + engagement_id)
- All API endpoints follow Master Flow Orchestrator (MFO) pattern

---

## Original Documentation (2024-07-29)

This document provides a complete, end-to-end data flow analysis for the `Roadmap` page of the AI Modernize Migration Platform.

**Assumptions:**
*   The analysis is based on the `Roadmap.tsx` page and its associated hook, `useRoadmap`.
*   The feature is marked as "Coming Soon," and the analysis is based on the intended API endpoints.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.

---

## 1. Frontend: Components and API Calls

The Roadmap page is designed to provide a high-level, timeline-based view of the entire migration project, broken down by waves and phases.

### Key Components & Hooks
*   **Page Component:** `src/pages/assess/Roadmap.tsx`
*   **Core Logic Hooks:**
    *   `useRoadmap`: Fetches the roadmap data.
    *   `useUpdateRoadmap`: Saves changes to the roadmap.

### API Call Summary

| # | Method | Endpoint          | Trigger                       | Description                    |
|---|--------|-------------------|-------------------------------|--------------------------------|
| 1 | `GET`  | `/assess/roadmap` | `useRoadmap` hook on load.    | Fetches the current roadmap.   |
| 2 | `PUT`  | `/assess/roadmap` | `useUpdateRoadmap` hook (not yet used). | Saves an updated version of the roadmap. |

---

## 2. Backend, CrewAI, ORM, and Database Trace

The backend for the roadmap would aggregate data from the wave planning phase to generate a visual timeline.

### API Endpoint: `GET /assess/roadmap`

*   **FastAPI Route:** Located in `backend/app/api/v1/endpoints/assessment.py` (or a dedicated `roadmap.py`).
*   **CrewAI Interaction:**
    *   **Initial Generation:** If no roadmap exists, this call would trigger an agent (likely the `Wave Planning Coordinator` or a new `RoadmapVisualizationAgent`) to process the data from the `wave_plans` table and structure it into a timeline format.
    *   **Read Operation:** If a roadmap has been generated, this is a simple read.
*   **ORM Layer:**
    *   **Repository:** `RoadmapRepository` (or it could read directly from `WavePlanRepository`).
    *   **Operation:** Fetches the `Roadmap` for the current engagement.
    *   **Scoping:** Filtered by `client_account_id` and `engagement_id`.
*   **Database:**
    *   **Table:** `roadmaps` (or it could be generated on-the-fly from `wave_plans`).
    *   **Query:** `SELECT * FROM roadmaps WHERE engagement_id = ?;`

---

## 3. End-to-End Flow Sequence: Viewing the Roadmap

1.  **User Navigates:** The user opens the Roadmap page.
2.  **Frontend Hook:** The `useRoadmap` hook is triggered.
3.  **API Call:** A `GET` request is made to `/assess/roadmap`.
4.  **Backend Logic:** The backend fetches the roadmap data, potentially generating it with an agent if it doesn't exist.
5.  **DB Execution:** PostgreSQL returns the roadmap data.
6.  **Backend Response:** FastAPI serializes the data into JSON and returns it.
7.  **UI Render:** The component renders the timeline view of the migration waves and phases.

---

## 4. Troubleshooting Breakpoints

| Breakpoint               | Diagnostic Check                                                                        | Platform-Specific Fix                                                                                      |
|--------------------------|-----------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| **Page Shows No Data**   | Check the network tab for a 404 on `/assess/roadmap`. The feature may not be implemented yet. | Implement the `/assess/roadmap` endpoint on the backend. Ensure it is connected to the `RoadmapRepository`. |
| **Roadmap is Empty**     | If the API returns an empty object, it means no `WavePlan` has been created for this engagement. | Go back to the "Wave Planning" page and ensure a plan has been generated and saved first.                |
| **Timeline is Incorrect**| Check the agent logic for the `RoadmapVisualizationAgent`.                              | The agent's logic for converting wave plan dates into a visual timeline may have a bug. Debug the agent's transformation logic. |


