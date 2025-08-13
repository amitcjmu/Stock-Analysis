# Collection Flow: 05 - Data Validation

This document describes the Data Validation process, which is a crucial, non-interactive step in the Collection flow.

**Analysis Date:** 2024-08-01

**Assumptions:**
*   Data Validation is primarily a backend process, orchestrated by CrewAI.
*   This process runs after data has been collected via adaptive forms, bulk uploads, or data integration.

---

## 1. Process Overview

Data validation is the process of ensuring that the collected data is accurate, complete, and consistent before it is handed off to the Assessment phase. This is a critical step for maintaining data quality and ensuring the reliability of the subsequent analysis.

---

## 2. Backend, CrewAI, ORM, and Database Trace

The entire data validation process is handled by the backend, with no direct user interaction.

### CrewAI Phase: `DATA_VALIDATION`

*   **Trigger:** This phase is automatically triggered after the `AUTOMATED_COLLECTION` or `MANUAL_COLLECTION` phases are complete.
*   **CrewAI Interaction:**
    *   **Agents:** A dedicated set of CrewAI agents is responsible for data validation. These may include a `DataQualityAnalyst` and a `SchemaValidationSpecialist`.
    *   **Tasks:** The agents perform a series of tasks, including:
        *   **Completeness Checks:** Verifying that all required fields are populated.
        *   **Format Validation:** Ensuring that data is in the correct format (e.g., dates, numbers).
        *   **Consistency Checks:** Cross-referencing data to ensure internal consistency.
        *   **Business Rule Validation:** Checking the data against predefined business rules.
*   **ORM Layer:**
    *   **Operation:** The agents update the `Asset` records with a `data_quality_score` and may create `DataConflict` records if issues are found that require manual intervention.
    *   **Models:** `app.models.asset.Asset`, `app.models.collection_flow.DataConflict`.
*   **Database:**
    *   **Tables:** `assets`, `data_conflicts`.
    *   **Query:** `UPDATE assets SET data_quality_score = ? WHERE id = ?; INSERT INTO data_conflicts (...) VALUES (...);`

---

## 3. End-to-End Flow Sequence

1.  **Data Collection Completes:** The `AUTOMATED_COLLECTION` or `MANUAL_COLLECTION` phase of the `UnifiedCollectionFlow` finishes.
2.  **Validation Phase Starts:** The `MasterFlowOrchestrator` automatically transitions the flow to the `DATA_VALIDATION` phase.
3.  **Agents Analyze Data:** The data validation agents are tasked with analyzing the collected data for the assets in the current flow.
4.  **Conflicts are Flagged:** If the agents find any conflicts that they cannot resolve automatically, they create `DataConflict` records in the database.
5.  **Data is Scored:** Each asset is assigned a `data_quality_score` based on the validation results.
6.  **Flow Pauses or Proceeds:**
    *   If conflicts requiring manual resolution are found, the flow pauses, and the user is directed to the `Data Integration` page.
    *   If no major conflicts are found, the flow automatically proceeds to the `FINALIZATION` phase.

---

## 4. Troubleshooting Breakpoints

| Breakpoint                        | Diagnostic Check                                                                                               | Platform-Specific Fix                                                                                             |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Data Quality Score is Low**     | Check the `data_conflicts` table for any unresolved issues. Review the logs for the `migration_backend` container to see the output of the data validation agents. | The validation rules may be too strict, or the source data may be of poor quality. The validation agents or their tools may need to be adjusted to better handle the data. |
| **Flow Fails to Proceed**         | If the flow gets stuck in the `DATA_VALIDATION` phase, it could indicate an error in one of the validation agents. Check the backend logs for agent-related errors. | Debug the specific agent that is failing. It may be an issue with the agent's logic, its tools, or its ability to access the required data. |
