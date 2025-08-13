# Collection Flow: 06 - Handoff to Assess

This document describes the process of handing off the collected and validated data from the Collection flow to the Assessment flow.

**Analysis Date:** 2024-08-01

**Assumptions:**
*   The handoff is a backend-only process, orchestrated by CrewAI.
*   This process runs after the `DATA_VALIDATION` phase is complete and all manual conflicts have been resolved.

---

## 1. Process Overview

The handoff to Assess is the final step of the Collection flow. It marks the successful completion of data gathering and prepares the data for the next stage of the migration journey: assessment and analysis.

---

## 2. Backend, CrewAI, ORM, and Database Trace

The handoff process is fully automated and handled by the backend.

### CrewAI Phase: `FINALIZATION`

*   **Trigger:** This phase is automatically triggered after the `DATA_VALIDATION` phase is complete and there are no outstanding data conflicts.
*   **CrewAI Interaction:**
    *   **Agents:** A `HandoffCoordinator` agent is responsible for this phase.
    *   **Tasks:** The agent performs the following tasks:
        *   **Final Data Packaging:** Gathers all the collected and validated data for the assets in the flow.
        *   **Status Update:** Marks the Collection flow as `COMPLETED`.
        *   **Trigger Assessment Flow:** Initiates a new Assessment flow, passing the data package as input.
*   **ORM Layer:**
    *   **Operation:** Updates the `CollectionFlow` record's status to `COMPLETED`. Creates a new `AssessmentFlow` record (or a similar entity for the Assessment phase).
    *   **Models:** `app.models.collection_flow.CollectionFlow`, `app.models.assessment.AssessmentFlow` (inferred).
*   **Database:**
    *   **Tables:** `collection_flows`, `assessment_flows` (inferred).
    *   **Query:** `UPDATE collection_flows SET status = 'COMPLETED' WHERE id = ?; INSERT INTO assessment_flows (...) VALUES (...);`

---

## 3. End-to-End Flow Sequence

1.  **Validation Completes:** The `DATA_VALIDATION` phase finishes successfully.
2.  **Finalization Phase Starts:** The `MasterFlowOrchestrator` transitions the flow to the `FINALIZATION` phase.
3.  **Agent Prepares Handoff:** The `HandoffCoordinator` agent gathers all the necessary data.
4.  **Collection Flow is Marked as Complete:** The agent updates the status of the `CollectionFlow` record in the database.
5.  **Assessment Flow is Created:** The agent creates a new Assessment flow, linking it to the completed Collection flow.
6.  **User is Notified:** The user receives a notification that the Collection flow is complete and the Assessment flow is ready.

---

## 4. Troubleshooting Breakpoints

| Breakpoint                        | Diagnostic Check                                                                                               | Platform-Specific Fix                                                                                             |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Handoff Fails**                 | Check the backend logs for errors in the `FINALIZATION` phase of the `UnifiedCollectionFlow`. The error might be related to creating the new Assessment flow or updating the Collection flow's status. | This could be a data consistency issue or a bug in the `HandoffCoordinator` agent. Ensure that the Assessment flow logic is correctly implemented and that there are no database constraints preventing the creation of the new flow. |
| **Assessment Flow Not Created**   | Verify in the database that a new record was created in the `assessment_flows` table (or equivalent). If not, the `HandoffCoordinator` agent likely failed. | Debug the `HandoffCoordinator` agent's logic for creating the new Assessment flow. Check for any errors in the agent's tools or its interaction with the `MasterFlowOrchestrator`. |
