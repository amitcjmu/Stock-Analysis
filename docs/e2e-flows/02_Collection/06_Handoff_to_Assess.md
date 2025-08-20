# Collection Flow: 06 - Handoff to Assess

This document describes the process of handing off the collected and validated data from the Collection flow to the Assessment flow.

**Analysis Date:** 2024-08-01 (Updated)

**Assumptions:**
*   The handoff is a backend-only process, orchestrated by CrewAI as part of the background flow execution.
*   This process runs after the `DATA_VALIDATION` phase is complete and all manual conflicts have been resolved.

---

## 1. Process Overview

The handoff to Assess is the final step of the Collection flow. It marks the successful completion of data gathering and prepares the data for the next stage of the migration journey: assessment and analysis.

---

## 2. Backend, CrewAI, ORM, and Database Trace

The handoff process is fully automated and handled by the backend.

### CrewAI Phase: `FINALIZATION`

*   **Trigger:** This phase is automatically triggered in the background after the `DATA_VALIDATION` phase is complete and there are no outstanding data conflicts.
*   **CrewAI Interaction:**
    *   **Agents:** A `HandoffCoordinator` agent is responsible for this phase.
    *   **Tasks:** The agent performs the following tasks:
        *   **Final Data Packaging:** Gathers all the collected and validated data.
        *   **Status Update:** The `sync_collection_child_flow_state` function is called with a `next_phase` of `None`, which marks the Collection flow as `COMPLETED`.
        *   **Trigger Assessment Flow:** Initiates a new Assessment flow.
*   **ORM Layer:**
    *   **Operation:** Updates the `CollectionFlow` record's status to `COMPLETED`. Creates a new `AssessmentFlow` record (or a similar entity).
    *   **Models:** `app.models.collection_flow.CollectionFlow`, `app.models.assessment.AssessmentFlow` (inferred).
*   **Database:**
    *   **Tables:** `collection_flows`, `assessment_flows` (inferred).
    *   **Query:** `UPDATE collection_flows SET status = 'COMPLETED' WHERE id = ?; INSERT INTO assessment_flows (...) VALUES (...);`

---

## 3. End-to-End Flow Sequence

1.  **Validation Completes:** The `DATA_VALIDATION` phase finishes successfully.
2.  **State is Synced:** The `sync_collection_child_flow_state` function is called, identifying `FINALIZATION` as the `next_phase`.
3.  **Finalization Phase Starts:** The `MasterFlowOrchestrator` starts the `FINALIZATION` phase in the background.
4.  **Agent Prepares Handoff:** The `HandoffCoordinator` agent gathers all the necessary data.
5.  **Collection Flow is Marked as Complete:** The agent's phase completes, and the `sync_collection_child_flow_state` function is called again. With `next_phase` being `None`, it updates the `CollectionFlow` record's status to `COMPLETED`.
6.  **Assessment Flow is Created:** A new Assessment flow is created.
7.  **User is Notified:** The user receives a notification that the Collection flow is complete.

---

## 4. Troubleshooting Breakpoints

| Breakpoint                        | Diagnostic Check                                                                                               | Platform-Specific Fix                                                                                             |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Handoff Fails**                 | Check the backend logs for errors in the `FINALIZATION` phase. The `flow_health_monitor` should also detect if the flow is stuck in this phase. | This could be a data consistency issue or a bug in the `HandoffCoordinator` agent. Ensure that the Assessment flow logic is correctly implemented. |
| **Assessment Flow Not Created**   | Verify in the database that a new record was created in the `assessment_flows` table (or equivalent). If not, the `HandoffCoordinator` agent likely failed. | Debug the `HandoffCoordinator` agent's logic for creating the new Assessment flow. Check for any errors in the agent's tools or its interaction with the MFO. |
