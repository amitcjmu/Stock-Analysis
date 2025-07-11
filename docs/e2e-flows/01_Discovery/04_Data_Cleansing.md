
# Data Flow Analysis Report: DataCleansing Page

This document provides a complete, end-to-end data flow analysis for the `DataCleansing` page of the AI Force Migration Platform.

**Analysis Date:** 2024-07-29

**Assumptions:**
*   The analysis focuses on the `DataCleansing` page.
*   Endpoint `ANALYZE_QUALITY` in the service layer is assumed to map to the `/discovery/data-cleanup/agent-analyze` API endpoint.
*   Endpoint `APPLY_FIX` is assumed to map to `/discovery/data-cleanup/agent-process/{issueId}`.
*   The platform operates entirely within a Docker environment (`migration_frontend`, `migration_backend`, `migration_db`).
*   All API calls require authentication and multi-tenant context headers (`X-Client-Account-ID`, `X-Engagement-ID`).

---

## 1. Frontend: Components and API Calls

The `DataCleansing` page is responsible for identifying and resolving data quality issues in the imported data, assisted by CrewAI agents.

### Key Components & Hooks
*   **Page Component:** `src/pages/discovery/DataCleansing.tsx`
*   **Core Logic:** The page directly uses several hooks, including:
    *   `useUnifiedDiscoveryFlow`: For managing the overall flow state.
    *   `useDiscoveryFlowAutoDetection`: To identify the active flow.
    *   `useDataCleansingQueries`: For fetching cleansing-specific data and triggering actions.
*   **API Service Layer:** `src/services/dataCleansingService.ts`

### API Call Mapping Table

| #  | HTTP Call                                                    | Triggering Action / Hook (`useQuery`, `useMutation`) | Payload / Key Parameters      | Expected Response                                                               |
|----|--------------------------------------------------------------|-------------------------------------------------------|-------------------------------|---------------------------------------------------------------------------------|
| 1  | `GET /master-flows/active?flowType=discovery`                | `useDiscoveryFlowList` on page load.                  | `clientAccountId`, `engagementId` | `MasterFlowResponse[]` (List of active discovery flows)                         |
| 2  | `GET /flows/{flowId}/status`                                 | `useUnifiedDiscoveryFlow` (polls when flow is active).| `flowId`                      | `FlowStatusResponse` (Detailed status of a single flow)                         |
| 3  | `POST /flows/{flowId}/execute`                               | User clicks "Trigger Cleansing" (`handleTriggerDataCleansingCrew`). | `flowId`, `phase: 'data_cleansing'` | Updated flow status.                                                            |
| 4  | `GET /data-import/latest-import`                             | `useLatestImport` on page load.                       | `clientAccountId`             | JSON object with the latest import data.                                        |
| 5  | `GET /discovery/assets`                                      | `useAssets` query.                                    | `page`, `pageSize`            | Paginated list of assets.                                                       |
| 6  | `POST /discovery/data-cleanup/agent-analyze`                 | `useAgentAnalysis` mutation.                          | `assets: [...]`               | JSON with quality issues and recommendations.                                   |
| 7  | `POST /discovery/data-cleanup/agent-process/{issueId}`       | `useApplyFix` mutation.                               | `issueId`, `fixData`          | Confirmation of fix application.                                                |

---

## 2. Backend, ORM, and Database Trace

The backend flow for Data Cleansing heavily involves CrewAI for analysis.

### Trace for `POST /discovery/data-cleanup/agent-analyze` (Agent Analysis)
1.  **API Router:** The request hits a router like `backend/app/api/v1/endpoints/data_cleanup.py`.
2.  **Service Layer:** The router calls a method like `DataCleanupService.analyze_data_quality()`.
3.  **CrewAI Interaction:**
    *   The service initiates a CrewAI flow.
    *   **Agent Involved:** A specialized **Data Quality Agent** is tasked with analyzing the provided asset data. It identifies inconsistencies, missing values, and outliers, and generates a list of quality issues and actionable recommendations.
4.  **ORM Operation:**
    *   The analysis results are persisted.
    *   **Repository:** `DataQualityIssueRepository`.
    *   **Model:** `DataQualityIssue`.
    *   **Operation:** `INSERT` new quality issues and recommendations into the `data_quality_issues` table.

| ORM Model           | PostgreSQL Table        | Relevant Columns                                                                   |
|---------------------|-------------------------|------------------------------------------------------------------------------------|
| `DataQualityIssue`  | `data_quality_issues`   | `id`, `flow_id`, `asset_id`, `issue_type`, `description`, `recommendation`, `status` |
| `AssetInventory`    | `asset_inventory`       | `id`, `asset_name`, `ip_address`, `data_quality_score`, `is_clean`                 |

---

## 3. End-to-End Flow Sequence: User Triggers Data Cleansing

1.  **Frontend (User Action):** User clicks the "Trigger Data Cleansing" button.
2.  **Frontend (Hook):** The `onClick` event triggers `handleTriggerDataCleansingCrew`, which calls `updatePhase('data_cleansing')` from the `useUnifiedDiscoveryFlow` hook.
3.  **Frontend (API Call):** This executes a mutation that sends a `POST /flows/{flowId}/execute` request with the payload `{ "phase": "data_cleansing" }`.
4.  **Backend (API Router):** The request is routed to the `MasterFlowOrchestrator`.
5.  **Backend (Orchestrator):** The orchestrator transitions the flow to the `data_cleansing` phase and invokes the `DataCleanupService`.
6.  **Backend (CrewAI):** The service starts the **Data Quality Agent** crew, which analyzes the data associated with the flow.
7.  **Database:** As the agent works, it populates the `data_quality_issues` table with its findings. The `asset_inventory` table's `data_quality_score` may be updated.
8.  **Frontend (Polling):** The `useUnifiedDiscoveryFlow` hook periodically polls the `GET /flows/{flowId}/status` endpoint.
9.  **Frontend (UI Update):** As the polling returns updated flow state, the UI reflects the progress, showing the detected quality issues and recommendations.

---

## 4. Troubleshooting Breakpoints

| Stage      | Potential Failure Point                                                                                                     | Diagnostic Checks                                                                                                                                                                                                                         |
|------------|-----------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Frontend** | **Stale Data:** The `useLatestImport` query returns stale data, causing the user to see outdated quality issues.              | **Browser DevTools (Network Tab):** Check the response from `GET /data-import/latest-import`. Verify the `Last-Modified` or `ETag` headers if caching is implemented. <br/> **React DevTools:** Check the `query.dataUpdatedAt` timestamp for the `useLatestImport` query. |
| **Backend**  | **Agent Overload:** The Data Quality Agent takes too long to process a large dataset, leading to a timeout. <br/> **Incorrect Analysis:** The agent misidentifies issues or provides incorrect recommendations. | **Docker Logs:** Monitor `migration_backend` for timeout errors or exceptions from the CrewAI service. <br/> **Agent Observability:** Check agent task durations and memory usage via the platform's observability tools.                   |
| **Database** | **Slow Queries:** Queries on `asset_inventory` or `data_quality_issues` are slow without proper indexing on `flow_id` or `asset_id`. | **Direct DB Query:** Use `EXPLAIN ANALYZE` on slow queries to check the query plan. Example: `docker exec -it migration_db psql -U user -d migration_db -c "EXPLAIN ANALYZE SELECT * FROM data_quality_issues WHERE flow_id = 'your-flow-id';"`. | 