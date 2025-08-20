# Collection Flow: 04 - Data Integration

This document provides a complete, end-to-end data flow analysis for the `Data Integration` page in the Collection phase of the AI Modernize Migration Platform.

**Analysis Date:** 2024-08-01 (Updated)

**Assumptions:**
*   The analysis focuses on the `src/pages/collection/DataIntegration.tsx` page.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.
*   The frontend is currently using mock data, so the API calls described here are inferred based on the UI and the updated application patterns.

---

## 1. Frontend: Components and API Calls

The Data Integration page is designed to resolve conflicts that arise when data is collected from multiple sources. It is the primary interface for manual intervention when the automated validation process detects issues.

### Key Components & Hooks
*   **Page Component:** `src/pages/collection/DataIntegration.tsx`
*   **UI Components:**
    *   `DataIntegrationView`: Displays an overview of the integrated data.
    *   `ConflictResolver`: The main component for viewing and resolving data conflicts.
    *   `ValidationDisplay`: Shows data validation results.
    *   `ProgressTracker`: Tracks the progress of the data integration process.

### Inferred API Call Summary

| # | Method | Endpoint                              | Trigger                           | Description                               |
|---|--------|---------------------------------------|-----------------------------------|-------------------------------------------|
| 1 | `GET`  | `/collection/flows/{flow_id}/conflicts` | Page load                         | Fetches a list of data conflicts for the flow. |
| 2 | `POST` | `/collection/flows/{flow_id}/continue`| `handleConflictResolve` function    | Submits a resolution for a data conflict and continues the flow. |
| 3 | `POST` | `/collection/flows/{flow_id}/continue`| `handleProceedToDiscovery` function | Marks the current phase as complete and continues the flow. |

---

## 2. Backend, CrewAI, ORM, and Database Trace

The backend for the Data Integration page is responsible for identifying data conflicts, storing user-provided resolutions, and resuming the background flow.

### CrewAI Phase: `DATA_VALIDATION` (Conflict Identification)

*   **Trigger:** This phase runs in the background. If it identifies conflicts that require manual intervention, it pauses the flow.
*   **CrewAI Interaction:** `DataQualityAnalyst` agents analyze the data and create `DataConflict` records for any issues they can't resolve automatically.
*   **ORM Layer:**
    *   **Operation:** Creates `DataConflict` records.
    *   **Model:** `app.models.collection_flow.DataConflict` (inferred).
*   **Database:**
    *   **Table:** `data_conflicts` (inferred).
    *   **Query:** `INSERT INTO data_conflicts (...) VALUES (...);`

### API Endpoint: `POST /flows/{flow_id}/continue`

*   **FastAPI Route:** `continue_flow` function in `.../collection_crud_execution.py`.
*   **CrewAI Interaction:**
    *   **Resume Flow:** This call resumes the `MasterFlow` using the `resume_mfo_flow` utility. The conflict resolution is passed in the `resume_context`.
    *   **Next Phase:** The `DATA_VALIDATION` agents process the resolution, update the asset data, and re-validate. If all conflicts are resolved, the flow transitions to the `FINALIZATION` phase.
*   **ORM Layer:**
    *   **Operation:** The CrewAI agents will update the `DataConflict` record to mark it as resolved and update the corresponding `Asset` record.
*   **Database:**
    *   **Tables:** `data_conflicts`, `assets`.
    *   **Query:** `UPDATE data_conflicts SET status = 'resolved', ... WHERE id = ?; UPDATE assets SET ... WHERE id = ?;`

---

## 3. End-to-End Flow Sequence: Resolving Data Conflicts

1.  **Flow Pauses:** The background `DATA_VALIDATION` phase identifies a conflict and pauses the flow, setting its status to something like `AWAITING_INPUT`.
2.  **User Navigates to Page:** The user is notified and navigates to the `Data Integration` page.
3.  **Page Load:** The page fetches the list of data conflicts from the `/collection/flows/{flow_id}/conflicts` endpoint.
4.  **User Resolves Conflict:** The user interacts with the `ConflictResolver` to choose the correct value, triggering `handleConflictResolve`.
5.  **API Call:** A `POST` request is sent to `/collection/flows/{flow_id}/continue` with the resolution in the request body.
6.  **Backend Resumes Flow:** The backend resumes the background CrewAI flow. The agents process the resolution and the flow continues.
7.  **UI Updates:** The UI removes the resolved conflict from the list.
8.  **User Proceeds:** Once all conflicts are resolved, the user clicks "Proceed to Discovery Phase", which calls the `/collection/flows/{flow_id}/continue` endpoint again to signal that the manual intervention step is complete.

---

## 4. Troubleshooting Breakpoints

| Breakpoint                        | Diagnostic Check                                                                                               | Platform-Specific Fix                                                                                             |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Conflicts Don't Load**          | Check the network tab for errors on the `GET .../conflicts` call. The flow might not be in a state that requires manual intervention. | Verify the status of the collection flow. Ensure the `DATA_VALIDATION` phase has run and correctly identified conflicts. Check the `data_conflicts` table. |
| **Conflict Resolution Fails**     | Check the console for errors on the `POST .../continue` call. A 400 error might indicate an invalid resolution, while a 500 error suggests a problem with resuming the flow. | Ensure the resolution being sent is in the correct format. Check the backend logs to see why the `resume_mfo_flow` call failed. The `flow_health_monitor` may provide additional details. |
| **Flow Doesn't Continue**         | If the flow doesn't proceed after resolving all conflicts, the backend might not be correctly transitioning to the next phase (`FINALIZATION`). | Check the backend logs for the output of the `sync_collection_child_flow_state` function. This function is responsible for updating the flow's status based on the `next_phase` returned by the MFO. |
