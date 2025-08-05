
# E2E Data Flow Analysis: Technical Debt

**Analysis Date:** 2025-07-13

This document provides a complete, end-to-end data flow analysis for the `Technical Debt Analysis` page and the backend processes that generate its data.

**Core Architecture:**
*   **Parallel Execution:** This phase is executed **in parallel** with the Dependency Analysis phase to optimize performance. The `MasterFlowOrchestrator` triggers both via the `CrewCoordinator` after the Asset Inventory phase is complete.
*   **State-Driven UI:** The frontend is a direct reflection of the flow's state. All technical debt data is read from the `technical_debt` key within the flow's main state object.
*   **Orchestrated Agent Execution:** A dedicated `TechDebtExecutor` manages the execution of a specialized CrewAI crew to perform the analysis.
*   **Fail-Fast Execution:** The backend is designed to fail fast. If the primary CrewAI agents fail, the process halts. There is no fallback to a non-AI or rule-based classification system.

---

## 1. Frontend: Displaying Technical Debt Insights

The `TechDebtAnalysis` page displays the results of the backend analysis, including outdated software, security vulnerabilities, and modernization recommendations.

### Key Components & Hooks
*   **Page Component:** `src/pages/discovery/TechDebtAnalysis.tsx`
*   **Core Data Hook:** `useUnifiedDiscoveryFlow` is the single source of truth for all data displayed on this page.

### API Call Summary

| #  | Method | Endpoint                                | Trigger                                       | Description                                                                                       |
|----|--------|-----------------------------------------|-----------------------------------------------|---------------------------------------------------------------------------------------------------|
| 1  | `GET`  | (WebSocket or Polling)                  | `useUnifiedDiscoveryFlow` hook.               | Listens for updates to the flow's state object to receive the technical debt analysis data once it's available. |
| 2  | `POST` | `/api/v1/master-flows/{flowId}/resume`  | User clicks a button to finalize the discovery. | Signals the `MasterFlowOrchestrator` that the user has reviewed the findings and the flow can be completed. |

---

## 2. Backend: The Technical Debt Crew

The technical debt analysis is performed by the `TechDebtExecutor`, which is triggered automatically by the `MasterFlowOrchestrator`.

### Execution Flow

1.  **Parallel Invocation:** After the `inventory` phase, the `MasterFlowOrchestrator` calls the `CrewCoordinator`, which starts both the `DependencyAnalysisExecutor` and the `TechDebtExecutor` to run in parallel.
2.  **CrewAI Execution:**
    *   The `TechDebtExecutor` takes the `asset_inventory` and `dependencies` as its primary inputs.
    *   It creates and runs the `tech_debt` crew. This crew is composed of multiple agents:
        *   **Version Scanner Agent:** Checks software and OS versions against a knowledge base of end-of-life dates.
        *   **Vulnerability Agent:** Queries public (e.g., CVE) and internal databases for known vulnerabilities.
        *   **Modernization Advisor Agent:** Analyzes the findings and suggests modernization strategies and recommendations.
3.  **State Persistence:**
    *   The `_store_results` method takes the final analysis from the crew.
    *   It saves this entire object to the `technical_debt` key within the main `state` object of the flow.

### Database Interaction

*   **Table:** `crewai_flow_state_extensions`
*   **Operation:** The executor performs an `UPDATE` on the `state` JSONB column for the active `flow_id`. The `technical_debt` key within the JSON object is populated with the complete analysis, including debt scores, risks, and recommendations. No separate `tech_debt` table is used.

---

## 3. End-to-End Flow Sequence: Viewing Technical Debt

1.  **Backend Parallel Execution:** After the inventory is built, the orchestrator automatically starts the `TechDebtExecutor` in parallel with the dependency analysis. The results are saved to the flow's `state` in the database as they complete.
2.  **Frontend Page Load:** A user navigates to the `TechDebtAnalysis` page.
3.  **Frontend Data Fetch:** The `useUnifiedDiscoveryFlow` hook retrieves the latest state for the active `flowId`.
4.  **Frontend Render:**
    *   The page's components access `flowState.technical_debt`.
    *   They render the lists of vulnerabilities, outdated components, and modernization recommendations directly from the flow's state object.

---

## 4. Troubleshooting Breakpoints

| Stage      | Potential Failure Point                                                                                                               | Diagnostic Checks                                                                                                                                                                                                                                                                                                    |
|------------|---------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Frontend** | **No Tech Debt Data Shown:** The page loads, but all sections are empty. This means the `technical_debt` key in the flow's state object is missing or empty. | **React DevTools:** Inspect the `flowState` object from the `useUnifiedDiscoveryFlow` hook. Does the `technical_debt` key exist? Does it contain the analysis data?                                                                                                                            |
| **Backend**  | **Inaccurate Analysis:** The tech debt assessment is missing items or contains incorrect information. This points to a failure in one of the analysis agents. | **Docker Logs:** Check `migration_backend` logs for errors from the `TechDebtExecutor`. The agents might be failing to connect to external vulnerability databases or internal knowledge bases.                                                                                                |
| **Database** | **State Not Updating:** The technical debt analysis is generated by the crew but is not correctly saved to the flow's state in the database. | **Direct DB Query:** Connect to the database and inspect the `state` column for your `flow_id`: `SELECT state -> 'technical_debt' FROM crewai_flow_state_extensions WHERE flow_id = 'your-flow-id';`. Verify that the JSON data is present and contains the expected analysis structure. |

