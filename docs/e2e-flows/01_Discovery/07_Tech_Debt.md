
# Data Flow Analysis Report: Tech Debt Analysis Page

This document provides a complete, end-to-end data flow analysis for the `TechDebtAnalysis` page of the AI Force Migration Platform.

**Analysis Date:** 2024-07-29

**Assumptions:**
*   The analysis focuses on the `TechDebtAnalysis` page.
*   The `GET /flows/{flowId}/status` endpoint is the primary source of data for this page.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.

---

## 1. Frontend: Components and API Calls

The Tech Debt Analysis page is responsible for displaying insights about outdated software, security vulnerabilities, and end-of-life components discovered in the client's IT landscape.

### Key Components & Hooks
*   **Page Component:** `src/pages/discovery/TechDebtAnalysis.tsx`
*   **Core Logic Hooks:**
    *   `useTechDebtFlowDetection`: Identifies the active discovery flow.
    *   `useUnifiedDiscoveryFlow`: Manages the state of the active flow and triggers phase executions.

### API Call Summary

| # | Method | Endpoint                  | Trigger                            | Description                                        |
|---|--------|---------------------------|------------------------------------|----------------------------------------------------|
| 1 | `POST` | `/flows/{flowId}/execute` | `handleExecuteTechDebtAnalysis` function | Initiates the backend tech debt analysis by the agents. |

*Note: Data is not fetched via a dedicated API call but is delivered as part of the response from the `GET /flows/{flowId}/status` endpoint, which is polled by the `useUnifiedDiscoveryFlow` hook.*

---

## 2. Backend, CrewAI, ORM, and Database Trace

The backend for tech debt analysis involves a specialized crew of agents analyzing the existing asset inventory.

### API Endpoint: `POST /flows/{flowId}/execute` (Phase: `tech_debt`)

*   **FastAPI Route:** The request is handled by the generic `execute_flow_phase` function in `backend/app/api/v1/endpoints/master_flow.py`.
*   **CrewAI Interaction:**
    *   **Orchestrator:** The `MasterFlowOrchestrator` receives the request and identifies that the `tech_debt` phase needs to be executed.
    *   **Agent Trigger:** It activates the `Tech Debt Analysis Crew`.
    *   **Specialized Agents:** This crew is composed of agents like a `VersionScannerAgent` (checks software versions against a knowledge base), a `VulnerabilityAgent` (queries CVE databases), and a `ModernizationAdvisorAgent` (suggests replacements).
    *   **Process:** The agents iterate through the `asset_inventory` data, enrich it with tech debt information, and store the results.
*   **ORM Layer:**
    *   **Repository:** `AssetInventoryRepository`, `TechDebtRepository`.
    *   **Operation:**
        1.  **Read:** The agents read from the `asset_inventory` table to get the list of components to analyze.
        2.  **Write/Update:** The agents write their findings to the `tech_debt_analysis` table and update the `asset_inventory` with risk scores.
    *   **Scoping:** All database operations are scoped to the `client_account_id` and `engagement_id` associated with the `flowId`.
*   **Database:**
    *   **Tables Read:** `asset_inventory`
    *   **Tables Written:** `tech_debt_analysis`, `agent_insights`. The `asset_inventory` table is also updated.
    *   **Query Example (Read):** `SELECT * FROM asset_inventory WHERE flow_id = ?;`
    *   **Query Example (Write):** `INSERT INTO tech_debt_analysis (asset_id, flow_id, debt_details) VALUES (?, ?, ?);`

---

## 3. End-to-End Flow Sequence: Analyzing Tech Debt

1.  **User Navigation:** A user navigates to the Tech Debt Analysis page for an active flow.
2.  **Frontend Hook:** The `useUnifiedDiscoveryFlow` hook is already polling the `GET /flows/{flowId}/status` endpoint. The UI displays any existing tech debt data from the `flowState`.
3.  **User Action:** The user clicks the "Start Analysis" button.
4.  **API Call:** The `handleExecuteTechDebtAnalysis` function is called, triggering a `POST` request to `/flows/{flowId}/execute` with the payload `{ "phase": "tech_debt" }`.
5.  **Backend Orchestration:** The `MasterFlowOrchestrator` receives the request and tasks the `Tech Debt Analysis Crew`.
6.  **Agent Analysis:** The agents begin their work, querying external vulnerability databases and internal knowledge bases. As they find issues, they write results to the `tech_debt_analysis` and `agent_insights` tables.
7.  **Status Polling:** The frontend continues polling the `/status` endpoint.
8.  **Data Update:** The backend route for `/status` now reads from the `tech_debt_analysis` table and includes the new findings in its response.
9.  **UI Render:** The new tech debt items appear on the page in real-time as the `flowState` is updated by the polling hook.

---

## 4. Troubleshooting Breakpoints

| Breakpoint               | Diagnostic Check                                                                                                    | Platform-Specific Fix                                                                                              |
|--------------------------|---------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| **Analysis Won't Start** | Check network tab for errors on `POST /flows/{flowId}/execute`. A 400 error might mean the phase is already complete. | Verify the `isPhaseComplete` logic in the UI is correctly disabling the "Start Analysis" button.                   |
| **No Data Appears**      | After starting analysis, check the response from `GET /flows/{flowId}/status`. See if the `tech_debt` key is populated. | `docker exec -it migration_backend bash` and check logs for errors in the `Tech Debt Analysis Crew`. The agents may be failing to connect to external CVE databases. |
| **Data is Incorrect**    | Examine the `agent_insights` for the `Tech Debt Analysis Crew` to see the confidence scores and raw data used.          | The agents' knowledge bases (`knowledge_bases/version_info.yaml`, etc.) may be out of date. Update them with the latest information. |
| **Performance Issues**   | If the analysis is slow, check the logs for the `Tech Debt Analysis Crew` to see if a specific agent is bottlenecked. | Optimize the database queries in the `TechDebtRepository`. Ensure the `asset_inventory` table is properly indexed for the agents' queries. |

