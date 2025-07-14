
# Data Flow Analysis Report: Assessment Flow Page

This document provides a complete, end-to-end data flow analysis for the active `Assessment Flow` pages of the AI Force Migration Platform.

**Analysis Date:** 2024-07-29

**Assumptions:**
*   The analysis is based on the `AssessmentFlowLayout.tsx` component and its core hook, `useAssessmentFlow`.
*   This is a mature feature with a full suite of API interactions.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.

---

## 1. Frontend: Components and API Calls

The Assessment Flow is a multi-step, orchestrated process that guides the user through a detailed application assessment, from defining architectural standards to generating final migration recommendations.

### Key Components & Hooks
*   **Layout Component:** `src/components/assessment/AssessmentFlowLayout.tsx`
*   **Core Logic Hook:** `useAssessmentFlow.ts` - This hook contains a complete, handcrafted API client and state machine for managing the assessment flow.

### API Call Summary

| # | Method | Endpoint                                                 | Trigger                               | Description                                         |
|---|--------|----------------------------------------------------------|---------------------------------------|-----------------------------------------------------|
| 1 | `POST` | `/api/v1/assessment-flow/initialize`                     | `initializeFlow` action.              | Starts a new assessment flow.                       |
| 2 | `GET`  | `/api/v1/assessment-flow/{id}/status`                    | Polling within the hook.              | Fetches the current state of the flow.              |
| 3 | `POST` | `/api/v1/assessment-flow/{id}/resume`                    | `resumeFlow` action.                  | Sends user input to a paused flow.                  |
| 4 | `POST` | `/api/v1/assessment-flow/{id}/navigate`                  | `navigateToPhase` action.             | Moves the flow to a specific phase.                 |
| 5 | `PUT`  | `/api/v1/assessment-flow/{id}/architecture-standards`    | `updateArchitectureStandards` action. | Saves changes to architecture standards.            |
| 6 | `PUT`  | `/api/v1/assessment-flow/{id}/applications/{appId}/components` | `updateApplicationComponents` action. | Saves changes to an application's components.       |
| 7 | `PUT`  | `/api/v1/assessment-flow/{id}/applications/{appId}/sixr-decision` | `updateSixRDecision` action.      | Saves changes to a 6R decision.                     |
| 8 | `POST` | `/api/v1/assessment-flow/{id}/finalize`                  | `finalizeAssessment` action.          | Finalizes the assessment and marks it as complete.  |

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


