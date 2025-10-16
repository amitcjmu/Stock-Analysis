
# Assessment Flow: MFO-Integrated Data Flow Analysis

**Analysis Date:** October 16, 2025
**Last Updated:** October 16, 2025 (Enhanced for PR #600)
**MFO Integration Status:** Complete
**Status:** ✅ UPDATED FOR OCTOBER 2025 ENHANCEMENTS

## 🏗️ MFO Integration Overview

The Assessment Flow follows the **Master Flow Orchestrator** architecture:

- **Primary Identifier**: `master_flow_id` is used for ALL Assessment flow operations
- **Unified API Pattern**: All flow lifecycle operations use `/api/v1/master-flows/*` endpoints
- **MFO Coordination**: Assessment flows are created, managed, and executed through MFO
- **Internal Implementation**: Assessment-specific data linked via master_flow_id

**October 2025 Enhancements (PR #600):**
- Added **ApplicationGroupsWidget** for canonical application grouping (see `01_Overview.md`)
- Added **ReadinessDashboardWidget** for assessment readiness visualization
- Added **AssessmentApplicationResolver** service for asset-to-application resolution
- Enhanced with 3 new API endpoints: `/assessment-applications`, `/assessment-readiness`, `/assessment-progress`
- Pre-computed data in JSONB fields: `application_asset_groups`, `enrichment_status`, `readiness_summary`
- Full multi-tenant scoping on all queries (client_account_id + engagement_id)

**Key Architectural Changes:**
All Assessment flow operations go through MFO, with `master_flow_id` as the primary identifier. Child flow IDs are internal implementation details only. See `01_Overview.md` for comprehensive details on the new assessment architecture.

**Current Assumptions:**
*   The Assessment Flow is integrated with Master Flow Orchestrator (MFO)
*   All flow operations use `master_flow_id` as the primary identifier
*   The platform operates entirely within a Docker environment
*   All API calls require authentication and multi-tenant context headers

---

## 1. Frontend: Components and API Calls

The Assessment Flow is a multi-step, orchestrated process that guides the user through a detailed application assessment, from defining architectural standards to generating final migration recommendations.

### Key Components & Hooks
*   **Layout Component:** `src/components/assessment/AssessmentFlowLayout.tsx`
*   **Core Logic Hook:** `useAssessmentFlow.ts` - This hook contains a complete, handcrafted API client and state machine for managing the assessment flow.

### API Call Summary (MFO-Aligned)

| # | Method | Endpoint                                                 | Trigger                               | Description                                         |
|---|--------|----------------------------------------------------------|---------------------------------------|-----------------------------------------------------|
| 1 | `POST` | `/api/v1/master-flows`                                  | `initializeFlow` action.              | Creates a new assessment flow via MFO.             |
| 2 | `GET`  | `/api/v1/master-flows/{master_flow_id}/status`          | Polling within the hook.              | Fetches current flow state using master_flow_id.   |
| 3 | `POST` | `/api/v1/master-flows/{master_flow_id}/resume`          | `resumeFlow` action.                  | Resumes flow with user input via MFO.              |
| 4 | `POST` | `/api/v1/master-flows/{master_flow_id}/execute`         | `navigateToPhase` action.             | Executes specific phase via MFO.                   |
| 5 | `PUT`  | `/api/v1/assessment/{master_flow_id}/architecture-standards`    | `updateArchitectureStandards` action. | Saves architecture standards using master_flow_id. |
| 6 | `PUT`  | `/api/v1/assessment/{master_flow_id}/applications/{appId}/components` | `updateApplicationComponents` action. | Updates components using master_flow_id.          |
| 7 | `PUT`  | `/api/v1/assessment/{master_flow_id}/applications/{appId}/sixr-decision` | `updateSixRDecision` action.      | Updates 6R decisions using master_flow_id.        |
| 8 | `POST` | `/api/v1/master-flows/{master_flow_id}/complete`        | `finalizeAssessment` action.          | Finalizes assessment and completes flow via MFO.   |

**Key Changes:**
- Flow lifecycle operations (create, status, resume, execute, complete) now use MFO endpoints
- Assessment-specific operations use `master_flow_id` as the primary identifier
- All operations coordinate through MFO for unified flow management

---

## 2. Backend, CrewAI, ORM, and Database Trace

The backend for the assessment flow is a sophisticated state machine that coordinates multiple CrewAI agents over a series of phases.

### API Endpoint: `POST /api/v1/assessment-flow/initialize`

*   **FastAPI Route:** Located in `backend/app/api/v1/endpoints/assessment_flow.py`.
*   **CrewAI Interaction:**
    *   **Flow Initialization:** Creates a new `AssessmentFlow` record in the database.
    *   **Agent Trigger:** This call likely does not trigger an agent immediately. Instead, it sets up the state for the first phase (`architecture_minimums`).
*   **ORM Layer:**
    *   **Repository:** `AssessmentFlowRepository`.
    *   **Operation:** Creates a new `AssessmentFlow` record.
*   **Database:**
    *   **Table:** `assessment_flows`.
    *   **Query:** `INSERT INTO assessment_flows (...) VALUES (...);`

### API Endpoint: `POST /api/v1/assessment-flow/{id}/navigate`

*   **FastAPI Route:** The `navigate_to_phase` function in `assessment_flow.py`.
*   **CrewAI Interaction:** This is the primary trigger for agent work. When the flow navigates to a new phase (e.g., `tech_debt_analysis`), this endpoint will:
    1.  Update the `current_phase` in the `assessment_flows` table.
    2.  Task the relevant agent (e.g., `TechDebtAnalysisAgent`) to begin its work. The agent will run in the background.
    3.  The frontend will poll the `/status` endpoint to see the results as the agent completes its work.
*   **ORM Layer:**
    *   **Operation:** Updates the `current_phase` of the `AssessmentFlow` record.
*   **Database:**
    *   **Table:** `assessment_flows`
    *   **Query:** `UPDATE assessment_flows SET current_phase = ? WHERE id = ?;`

---

## 3. End-to-End Flow Sequence: Completing a Phase

1.  **User Finishes Task:** The user completes their work on the current phase (e.g., defining architecture standards).
2.  **User Navigates:** The user clicks the button for the next phase (e.g., "Technical Debt Analysis").
3.  **Frontend Action:** The `navigateToPhase` action is called in the `useAssessmentFlow` hook.
4.  **API Call:** A `POST` request is sent to `/api/v1/assessment-flow/{id}/navigate` with the payload `{"phase": "tech_debt_analysis"}`.
5.  **Backend Updates State:** The backend updates the `current_phase` in the database.
6.  **Backend Triggers Agent:** The backend asynchronously starts the `TechDebtAnalysisAgent`, passing it the `flowId`.
7.  **Agent Works:** The agent fetches the application data, analyzes it for technical debt, and saves the results to the `assessment_flow_data` table, linked to the `flowId`.
8.  **Frontend Polls:** The frontend continues to poll the `/status` endpoint. The `progress` value in the response will increase as the agent works.
9.  **UI Updates:** Once the agent is finished, the `/status` endpoint will return a `completed` status for the phase, and the UI will show the results of the analysis.

---

## 4. Troubleshooting Breakpoints

| Breakpoint                        | Diagnostic Check                                                                                           | Platform-Specific Fix                                                                                             |
|-----------------------------------|------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Flow Fails to Initialize**      | Check the network tab for errors on `POST /initialize`. A 400 error might mean the selected application IDs are invalid. | Ensure the application IDs exist and are in the correct format.                                                  |
| **Stuck in "Processing" State**   | If the progress bar never moves, the background agent for that phase likely failed to start or crashed.      | `docker exec` into the `migration_backend` container and check the Celery worker logs for errors related to the specific agent (e.g., `TechDebtAnalysisAgent`). |
| **Data Not Saving (`PUT` calls)** | Check the payload of the `PUT` request in the network tab. The data might not match the Pydantic schema. | Ensure the frontend is sending data in the exact format the backend endpoint expects. Check for type mismatches. |
| **Navigation Fails**              | The `navigateToPhase` endpoint might have logic preventing out-of-order phase execution.                   | Ensure the UI is correctly disabling navigation to phases that are not yet active.                                |


