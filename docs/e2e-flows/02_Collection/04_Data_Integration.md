# Collection Flow: 04 - Data Integration

This document provides a complete, end-to-end data flow analysis for the `Data Integration` page in the Collection phase of the AI Modernize Migration Platform.

**Analysis Date:** 2024-08-01

**Assumptions:**
*   The analysis focuses on the `src/pages/collection/DataIntegration.tsx` page.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.
*   The frontend is currently using mock data, so the API calls described here are inferred based on the UI and application patterns.

---

## 1. Frontend: Components and API Calls

The Data Integration page is designed to resolve conflicts that arise when data is collected from multiple sources (e.g., automated scans, manual forms, bulk uploads).

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
| 2 | `POST` | `/collection/flows/{flow_id}/resolve` | `handleConflictResolve` function    | Submits a resolution for a data conflict. |
| 3 | `POST` | `/collection/flows/{flow_id}/handoff` | `handleProceedToDiscovery` function | Marks the collection flow as complete and hands off to the Discovery phase. |

---

## 2. Backend, CrewAI, ORM, and Database Trace

The backend for the Data Integration page is responsible for identifying data conflicts, storing user-provided resolutions, and finalizing the collected data.

### API Endpoint: `GET /flows/{flow_id}/conflicts` (Inferred)

*   **FastAPI Route:** A new route, likely in `backend/app/api/v1/endpoints/collection.py`.
*   **CrewAI Interaction:** This endpoint would retrieve the results of the `AUTOMATED_COLLECTION` and `MANUAL_COLLECTION` phases of the `UnifiedCollectionFlow`. The `DATA_VALIDATION` phase would be responsible for identifying and storing these conflicts.
*   **ORM Layer:**
    *   **Operation:** Fetches `DataConflict` records associated with the flow.
    *   **Model:** A new model, e.g., `app.models.collection_flow.DataConflict`.
*   **Database:**
    *   **Table:** A new table, e.g., `data_conflicts`.
    *   **Query:** `SELECT * FROM data_conflicts WHERE collection_flow_id = ?;`

### API Endpoint: `POST /flows/{flow_id}/resolve` (Inferred)

*   **FastAPI Route:** A new route, likely in `collection.py`.
*   **CrewAI Interaction:** This call would provide the resolution to the `DATA_VALIDATION` phase of the `UnifiedCollectionFlow`. The CrewAI agents would then update the asset data with the chosen value and re-validate the data.
*   **ORM Layer:**
    *   **Operation:** Updates the `DataConflict` record to mark it as resolved and stores the chosen resolution. It would also update the corresponding `Asset` record.
*   **Database:**
    *   **Tables:** `data_conflicts`, `assets`.
    *   **Query:** `UPDATE data_conflicts SET status = 'resolved', ... WHERE id = ?; UPDATE assets SET ... WHERE id = ?;`

---

## 3. End-to-End Flow Sequence: Resolving Data Conflicts

1.  **Page Load:** The `DataIntegration.tsx` component mounts and fetches the list of data conflicts from the (inferred) `/collection/flows/{flow_id}/conflicts` endpoint.
2.  **User Resolves Conflict:** The user interacts with the `ConflictResolver` component to choose the correct value for a conflicting attribute. This triggers the `handleConflictResolve` function.
3.  **API Call:** A `POST` request is sent to the (inferred) `/collection/flows/{flow_id}/resolve` endpoint with the chosen resolution.
4.  **Backend Updates Data:** The backend updates the `DataConflict` and `Asset` records in the database.
5.  **UI Updates:** The UI removes the resolved conflict from the list.
6.  **User Proceeds:** Once all conflicts are resolved, the user clicks "Proceed to Discovery Phase", which triggers the `handleProceedToDiscovery` function and calls the (inferred) `/collection/flows/{flow_id}/handoff` endpoint.

---

## 4. Troubleshooting Breakpoints

| Breakpoint                        | Diagnostic Check                                                                                               | Platform-Specific Fix                                                                                             |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Conflicts Don't Load**          | Since the data is mocked, this is not currently an issue. In a real implementation, check the network tab for errors on the `GET .../conflicts` call. | Verify that the `DATA_VALIDATION` phase of the `UnifiedCollectionFlow` has run and that there are actual conflicts in the database for the given flow. |
| **Conflict Resolution Fails**     | Check the console for errors on the `POST .../resolve` call. A 400 error might indicate an invalid resolution, while a 500 error suggests a backend processing issue. | Ensure the resolution being sent is in the correct format. Check the backend logs to see why the data update or flow resumption failed. |
| **Unable to Proceed**             | The "Proceed" button is disabled until all conflicts are resolved. If the button remains disabled after resolving all conflicts, there may be a state management issue in the frontend. | Debug the `resolvedConflicts` and `conflicts` state arrays in `DataIntegration.tsx` to ensure they are being updated correctly. |
