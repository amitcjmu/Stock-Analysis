# Collection Flow: 05 - Data Validation

This document describes the Data Validation process, which is a crucial, non-interactive step in the Collection flow.

**Analysis Date:** 2024-08-01 (Updated)

**Assumptions:**
*   Data Validation is primarily a backend process, orchestrated by CrewAI and running in the background.
*   This process runs after data has been collected via adaptive forms, bulk uploads, or data integration.

---

## 1. Process Overview

Data validation is the process of ensuring that the collected data is accurate, complete, and consistent before it is handed off to the Assessment phase. This is a critical step for maintaining data quality and ensuring the reliability of the subsequent analysis.

---

## 2. Backend, CrewAI, ORM, and Database Trace

The entire data validation process is handled by the backend as part of the background flow execution.

### CrewAI Phase: `DATA_VALIDATION`

*   **Trigger:** This phase is automatically triggered in the background after the `AUTOMATED_COLLECTION` or `MANUAL_COLLECTION` phases are complete. The `sync_collection_child_flow_state` function handles the state transition.
*   **CrewAI Interaction:**
    *   **Agents:** A dedicated set of CrewAI agents is responsible for data validation. These may include a `DataQualityAnalyst` and a `SchemaValidationSpecialist`.
    *   **Tasks:** The agents perform a series of tasks, including completeness checks, format validation, consistency checks, and business rule validation.
*   **ORM Layer:**
    *   **Operation:** The agents update the `Asset` records with a `data_quality_score` and may create `DataConflict` records if issues are found that require manual intervention.
    *   **Models:** `app.models.asset.Asset`, `app.models.collection_flow.DataConflict`.
*   **Database:**
    *   **Tables:** `assets`, `data_conflicts`.
    *   **Query:** `UPDATE assets SET data_quality_score = ? WHERE id = ?; INSERT INTO data_conflicts (...) VALUES (...);`

---

## 3. End-to-End Flow Sequence

1.  **Data Collection Completes:** The `AUTOMATED_COLLECTION` or `MANUAL_COLLECTION` phase of the `UnifiedCollectionFlow` finishes.
2.  **State is Synced:** The `sync_collection_child_flow_state` function is called, which updates the child flow's status and identifies `DATA_VALIDATION` as the `next_phase`.
3.  **Validation Phase Starts:** The `MasterFlowOrchestrator` automatically starts the `DATA_VALIDATION` phase in the background.
4.  **Agents Analyze Data:** The data validation agents are tasked with analyzing the collected data.
5.  **Conflicts are Flagged:** If conflicts are found that require manual intervention, the agents create `DataConflict` records and the flow is paused.
6.  **Data is Scored:** Each asset is assigned a `data_quality_score`.
7.  **Flow Pauses or Proceeds:**
    *   If conflicts are found, the flow's status is updated to `AWAITING_INPUT`, and the user is notified.
    *   If no major conflicts are found, the `next_phase` will be `FINALIZATION`, and the flow continues automatically.

---

## 4. Troubleshooting Breakpoints

| Breakpoint                        | Diagnostic Check                                                                                               | Platform-Specific Fix                                                                                             |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Data Quality Score is Low**     | Check the `data_conflicts` table for any unresolved issues. Review the backend logs for the output of the data validation agents. | The validation rules may be too strict, or the source data may be of poor quality. The validation agents or their tools may need to be adjusted. |
| **Flow Gets Stuck**               | The `flow_health_monitor` is designed to detect stuck flows. Check its logs. If the flow is stuck in the `DATA_VALIDATION` phase, it could be an error in an agent. | Debug the specific agent that is failing. It may be an issue with the agent's logic, its tools, or its ability to access the required data. The new fallback phase runner might be invoked if CrewAI is unavailable. |
