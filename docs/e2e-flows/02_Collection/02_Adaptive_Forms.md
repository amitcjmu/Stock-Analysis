# Collection Flow: 02 - Adaptive Forms

This document provides a complete, end-to-end data flow analysis for the `Adaptive Forms` page in the Collection phase of the AI Modernize Migration Platform.

**Analysis Date:** 2024-08-01

**Assumptions:**
*   The analysis focuses on the `src/pages/collection/AdaptiveForms.tsx` page and its core hook, `useAdaptiveFormFlow`.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.

---

## 1. Frontend: Components and API Calls

The Adaptive Forms page provides a dynamic, questionnaire-based approach to data collection. It is designed to intelligently ask for the information that is most needed to complete the asset inventory.

### Key Components & Hooks
*   **Page Component:** `src/pages/collection/AdaptiveForms.tsx`
*   **Core Logic Hook:** `useAdaptiveFormFlow` from `src/hooks/collection/useAdaptiveFormFlow.ts` encapsulates all the logic for managing the adaptive form flow.
*   **API Client:** `collectionFlowApi` from `src/services/api/collection-flow.ts` is used for all API interactions.
*   **UI Components:**
    *   `CollectionPageLayout`: Provides the basic layout for the page.
    *   `AdaptiveFormContainer`: Renders the dynamic form based on the data received from the backend.
    *   `CollectionUploadBlocker`: A UI component that blocks the user from proceeding if there are other incomplete collection flows.

### API Call Summary

| # | Method | Endpoint                                      | Trigger                                   | Description                                      |
|---|--------|-----------------------------------------------|-------------------------------------------|--------------------------------------------------|
| 1 | `GET`  | `/collection/flows/incomplete`                | `useIncompleteCollectionFlows` hook       | Fetches a list of incomplete flows to check for blockers. |
| 2 | `POST` | `/collection/flows`                           | `initializeFlow` in `useAdaptiveFormFlow` | Creates a new collection flow if one doesn't exist. |
| 3 | `GET`  | `/collection/flows/{flow_id}`                 | `initializeFlow` in `useAdaptiveFormFlow` | Fetches the details of an existing flow.         |
| 4 | `GET`  | `/collection/flows/status`                    | `initializeFlow` in `useAdaptiveFormFlow` | Gets the status of the current collection flow.  |
| 5 | `GET`  | `/collection/flows/{flow_id}/questionnaires`  | `initializeFlow` in `useAdaptiveFormFlow` | Fetches the adaptive questionnaires for the flow.|
| 6 | `POST` | `/collection/flows/{flow_id}/questionnaires/{questionnaire_id}/submit` | `handleSubmit` in `useAdaptiveFormFlow` | Submits the user's answers to the questionnaire. |
| 7 | `DELETE`| `/collection/flows/{flow_id}`                 | `handleDeleteFlow` in `AdaptiveForms.tsx` | Deletes a collection flow.                       |

---

## 2. Backend, CrewAI, ORM, and Database Trace

The backend for the Adaptive Forms page is responsible for generating the questionnaires, processing the responses, and managing the overall state of the collection flow.

### API Endpoint: `GET /flows/{flow_id}/questionnaires`

*   **FastAPI Route:** Located in `backend/app/api/v1/endpoints/collection.py`, the `get_adaptive_questionnaires` function.
*   **CrewAI Interaction:** This endpoint doesn't directly trigger a CrewAI flow. Instead, it retrieves the results of a previously run flow. The `QUESTIONNAIRE_GENERATION` phase of the `UnifiedCollectionFlow` is responsible for creating the `AdaptiveQuestionnaire` records.
*   **ORM Layer:**
    *   **Operation:** Fetches `AdaptiveQuestionnaire` records associated with the given `flow_id`.
    *   **Model:** `app.models.collection_flow.AdaptiveQuestionnaire`
*   **Database:**
    *   **Table:** `adaptive_questionnaires`
    *   **Query:** `SELECT * FROM adaptive_questionnaires WHERE collection_flow_id = ?;`

### API Endpoint: `POST /flows/{flow_id}/questionnaires/{questionnaire_id}/submit`

*   **FastAPI Route:** `submit_questionnaire_response` function in `collection.py`.
*   **CrewAI Interaction:**
    *   **Resume Flow:** This call resumes the `MasterFlow` using the `MasterFlowOrchestrator`. The submitted responses are passed as part of the `resume_context`.
    *   **Next Phase:** This typically triggers the `DATA_VALIDATION` phase of the `UnifiedCollectionFlow`, where CrewAI agents will process and validate the submitted data.
*   **ORM Layer:**
    *   **Operation:** Updates the `responses_collected`, `completion_status`, and `completed_at` fields of the `AdaptiveQuestionnaire` record.
*   **Database:**
    *   **Table:** `adaptive_questionnaires`
    *   **Query:** `UPDATE adaptive_questionnaires SET responses_collected = ?, ... WHERE id = ?;`

---

## 3. End-to-End Flow Sequence: Filling Out an Adaptive Form

1.  **Page Load:** The `AdaptiveForms.tsx` component mounts and calls the `useAdaptiveFormFlow` hook.
2.  **Blocker Check:** The `useIncompleteCollectionFlows` hook is called to check for any other active flows that might block the current one.
3.  **Flow Initialization:** If there are no blockers, the `initializeFlow` function is called.
4.  **Get/Create Flow:** `initializeFlow` either gets the details of an existing flow (if a `flowId` is present in the URL) or creates a new one by calling `POST /collection/flows`.
5.  **Fetch Questionnaires:** The frontend polls the `GET /collection/flows/{flow_id}/questionnaires` endpoint until the CrewAI agents have generated the questionnaires.
6.  **Render Form:** Once the questionnaires are fetched, the `AdaptiveFormContainer` component renders the dynamic form.
7.  **User Submits Form:** The user fills out the form and clicks "Submit," which triggers the `handleSubmit` function.
8.  **API Call:** A `POST` request is sent to `/collection/flows/{flow_id}/questionnaires/{questionnaire_id}/submit`.
9.  **Backend Processes Responses:** The backend updates the questionnaire record in the database and resumes the CrewAI flow, which then proceeds to the data validation phase.

---

## 4. Troubleshooting Breakpoints

| Breakpoint                        | Diagnostic Check                                                                                               | Platform-Specific Fix                                                                                             |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Page is Stuck Loading**         | Check the network tab for polling requests to `/questionnaires`. If these requests are failing or returning empty, it means the CrewAI agents have not yet generated the form. | Check the logs for the `migration_backend` container. Look for errors in the `UnifiedCollectionFlow` or the `QUESTIONNAIRE_GENERATION` phase. |
| **Form Submission Fails**         | Look for errors in the console on the `POST .../submit` call. A 400 error might indicate invalid data, while a 500 error suggests a problem with the backend processing. | Verify that the data being submitted matches the expected format. For backend errors, check the logs for the `migration_backend` container to see why the flow failed to resume. |
| **"Multiple active flows" error** | This error indicates that the database contains more than one non-completed collection flow for the current engagement. | Use the "Manage Flows" button to navigate to the flow management page and delete any unnecessary or stuck flows. If the issue persists, there may be a bug in the flow cleanup logic. |
