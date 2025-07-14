
# Data Flow Analysis Report: Treatment Page

This document provides a complete, end-to-end data flow analysis for the `Treatment` page in the Assess phase of the AI Force Migration Platform.

**Analysis Date:** 2024-07-29

**Assumptions:**
*   The analysis focuses on the `Treatment.tsx` page and its associated hooks.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.

---

## 1. Frontend: Components and API Calls

The Treatment page is the interactive core of the 6R analysis process, allowing users to select applications, fine-tune AI parameters, answer qualifying questions, and manage analysis jobs.

### Key Components & Hooks
*   **Page Component:** `src/pages/assess/Treatment.tsx`
*   **Core Logic Hooks:**
    *   `useApplications`: Fetches the initial list of discovered applications.
    *   `useSixRAnalysis`: Manages the interactive, single-analysis workflow.
    *   `useAnalysisQueue`: Manages batch processing of multiple analyses.
*   **API Client:** `SixRApiClient` is used for most interactions.

### API Call Summary

| # | Method | Endpoint                              | Trigger                               | Description                                      |
|---|--------|---------------------------------------|---------------------------------------|--------------------------------------------------|
| 1 | `GET`  | `/discovery/applications`             | `useApplications` hook on load.       | Fetches the list of all discovered applications. |
| 2 | `GET`  | `/sixr/analyses/`                     | `useApplications` hook on load.       | Fetches existing analyses to check status.       |
| 3 | `POST` | `/sixr/analyze`                       | `useSixRAnalysis` hook (`createAnalysis`) | Creates a new 6R analysis job.                   |
| 4 | `GET`  | `/sixr/{id}`                          | `useSixRAnalysis` hook (`loadAnalysis`)   | Fetches the status of a specific analysis.       |
| 5 | `PUT`  | `/sixr/{id}/parameters`               | `useSixRAnalysis` hook (`updateParameters`) | Updates the parameters for an analysis.          |
| 6 | `POST` | `/sixr/{id}/questions/submit`         | `useSixRAnalysis` hook (`submitAllQuestions`) | Submits user answers to clarifying questions.    |
| 7 | `POST` | `/sixr/{id}/iterate`                  | `useSixRAnalysis` hook (`iterateAnalysis`) | Re-runs the analysis with new parameters.        |
| 8 | `POST` | `/sixr/{id}/recommendation/accept`    | `useSixRAnalysis` hook (`acceptRecommendation`) | Accepts the AI's final recommendation.           |
| 9 | `GET`  | `/api/v1/analysis/queues`             | `useAnalysisQueue` hook on load.      | Fetches the list of all batch analysis jobs.     |
| 10| `POST` | `/api/v1/analysis/queues`             | `useAnalysisQueue` hook (`createQueue`)   | Creates a new batch analysis job.                |

---

## 2. Backend, CrewAI, ORM, and Database Trace

The backend for the Treatment page is a complex system involving multiple CrewAI agents and detailed state management.

### API Endpoint: `POST /sixr/analyze`

*   **FastAPI Route:** Likely located in `backend/app/api/v1/endpoints/sixr.py`.
*   **CrewAI Interaction:**
    *   **Flow Initialization:** This call creates a new `MasterFlow` record with `flow_type='assessment'` and a sub-type of `sixr_analysis`.
    *   **Agent Trigger:** It activates the `6R Analysis Crew`.
    *   **Specialized Agents:** This crew includes the `MigrationStrategyExpert`, `RiskAssessmentSpecialist`, `CostAnalysisAgent`, and potentially others. They are tasked with analyzing the application based on the provided parameters.
*   **ORM Layer:**
    *   **Operation:** Creates a new `MasterFlow` record and an `SixRAnalysis` record.
*   **Database:**
    *   **Tables:** `master_flows`, `sixr_analyses`.
    *   **Query:** `INSERT INTO sixr_analyses (...) VALUES (...);`

### API Endpoint: `PUT /sixr/{id}/parameters`

*   **FastAPI Route:** `update_parameters` function in `sixr.py`.
*   **CrewAI Interaction:** This call updates the parameters for an in-progress analysis and triggers a re-evaluation by the `6R Analysis Crew`. The agents will re-run their analysis with the new weighting.
*   **ORM Layer:**
    *   **Operation:** Updates the `parameters` JSONB column in the `sixr_analyses` table.
*   **Database:**
    *   **Table:** `sixr_analyses`
    *   **Query:** `UPDATE sixr_analyses SET parameters = ? WHERE id = ?;`

---

## 3. End-to-End Flow Sequence: Performing a 6R Analysis

1.  **User Selects Apps:** The user selects one or more applications from the list loaded via `GET /discovery/applications`.
2.  **User Starts Analysis:** The user clicks "Start Analysis," which triggers the `createAnalysis` function in the `useSixRAnalysis` hook.
3.  **API Call:** A `POST` request is sent to `/sixr/analyze`.
4.  **Backend Creates Job:** The backend creates a new `sixr_analyses` record and tasks the `6R Analysis Crew`.
5.  **Agent Analysis:** The agents begin processing. The `MigrationStrategyExpert` might ask clarifying questions.
6.  **Frontend Polls:** The frontend (`useSixRAnalysis`) polls `GET /sixr/{id}` for status. When the agent needs input, the `status` changes to `requires_input`.
7.  **User Answers Questions:** The UI displays the questions. The user answers them, triggering a `POST` to `/sixr/{id}/questions/submit`.
8.  **Agents Continue:** The agents use the answers to complete their analysis and generate a recommendation.
9.  **Frontend Displays Recommendation:** The status becomes `completed`, and the recommendation is shown.
10. **User Accepts:** The user accepts the recommendation, calling `POST /sixr/{id}/recommendation/accept`.
11. **Backend Finalizes:** The backend updates the status of the `sixr_analyses` record to `finalized`.

---

## 4. Troubleshooting Breakpoints

| Breakpoint                        | Diagnostic Check                                                                                               | Platform-Specific Fix                                                                                             |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Applications Don't Load**       | Check network tab for errors on `GET /discovery/applications`. A 404 means the Discovery phase is not complete. | Ensure a discovery flow has been successfully run first. The treatment page depends on its output.              |
| **Analysis Doesn't Start**        | Check console for errors on `POST /sixr/analyze`. A 400 error may indicate invalid application IDs.            | Verify that the application IDs being sent are integers, as expected by the 6R backend.                          |
| **Recommendation Seems Wrong**    | Review the `iteration_history` in the `useSixRAnalysis` state to see the parameters and answers that led to the result. | Use the "Iterate" feature to adjust the parameters and guide the AI agents toward a better recommendation.     |
| **Batch Jobs (`useAnalysisQueue`) Stuck** | Check the logs for the `migration_backend` container. Look for errors in the Celery workers that process the queue. | The queue processing logic might have a bug. `docker exec` into the container and debug the worker scripts. |


