
# Data Flow Analysis Report: Inventory Page

This document provides a complete, end-to-end data flow analysis for the `Inventory` page of the AI Force Migration Platform.

**Analysis Date:** 2024-07-29

**Assumptions:**
*   The analysis focuses on the `Inventory` page.
*   The `GET /flows/{flowId}/status` endpoint is the primary source of data for this page, populating both the asset list and AI insights.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.

---

## 1. Frontend: Components and API Calls

The `Inventory` page displays the consolidated list of discovered assets and provides AI-driven insights about the IT landscape.

### Key Components & Hooks
*   **Page Component:** `src/pages/discovery/Inventory.tsx`
*   **Primary Content Component:** `src/components/discovery/inventory/InventoryContent.tsx`
*   **Insights Component:** `src/components/discovery/inventory/EnhancedInventoryInsights.tsx`
*   **Core Logic:** The page and its children rely on the `useUnifiedDiscoveryFlow` hook to get all necessary data. This hook is the main interface to the backend for this page.

### API Call Mapping Table

| #  | HTTP Call                                     | Triggering Action / Hook (`useQuery`)                  | Payload / Key Parameters      | Expected Response                                                                                                                                                                             |
|----|-------------------------------------------------|--------------------------------------------------------|-------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1  | `GET /master-flows/active?flowType=discovery` | `useDiscoveryFlowList` on page load (via `useInventoryFlowDetection`). | `clientAccountId`, `engagementId` | `MasterFlowResponse[]` (List of active discovery flows to identify the correct `flowId`).                                                                                                  |
| 2  | `GET /flows/{flowId}/status`                  | `useUnifiedDiscoveryFlow` (polls when flow is active). | `flowId`                      | `FlowStatusResponse` object. For this page, the response is expected to be populated with `asset_inventory` (the list of assets) and `agent_insights` (AI-generated analysis). |
| 3  | `POST /flows/{flowId}/execute`                | User triggers the next phase (e.g., "Start Dependency Analysis"). | `flowId`, `phase: 'dependencies'` | Updated flow status, advancing the workflow to the next stage.                                                                                                                                |

---

## 2. Backend, ORM, and Database Trace

The backend process for populating the inventory is driven by a CrewAI flow that runs after data cleansing.

### Trace for `asset_inventory` and `agent_insights` population (via `GET /flows/{flowId}/status`)
1.  **API Router:** The `GET /flows/{flowId}/status` request hits the `flows.py` router.
2.  **Service Layer:** It calls `MasterFlowOrchestrator.get_flow_status()`. The orchestrator fetches the primary flow data from the `master_flows` table.
3.  **CrewAI Interaction (during the `inventory` phase):**
    *   When the flow is in the `inventory` phase, the orchestrator triggers the **Asset Inventory Crew**.
    *   **Agents Involved:**
        *   **Server Classification Expert:** Identifies and categorizes servers (e.g., Windows, Linux, Virtual, Physical).
        *   **Application Discovery Expert:** Identifies applications running on servers.
        *   **Device Classification Expert:** Classifies other network devices.
        *   **Inventory Manager:** Consolidates the findings from all other agents into a unified inventory list. This agent also generates the high-level `agent_insights`.
4.  **ORM Operation:**
    *   The `Inventory Manager` agent is responsible for persisting the final, consolidated data.
    *   **Repository:** `AssetInventoryRepository`, `AgentInsightRepository`.
    *   **Models:** `AssetInventory`, `AgentInsight`.
    *   **Operation:** `BULK INSERT` or `BULK UPDATE` operations on the `asset_inventory` table with the classified and consolidated asset data. Agent insights are saved to the `agent_insights` table.

### Database Tables

| ORM Model         | PostgreSQL Table    | Relevant Columns                                                                                               |
|-------------------|---------------------|----------------------------------------------------------------------------------------------------------------|
| `AssetInventory`  | `asset_inventory`   | `id`, `flow_id`, `asset_name`, `asset_type`, `environment`, `criticality`, `risk_score`, `migration_readiness` |
| `AgentInsight`    | `agent_insights`    | `id`, `flow_id`, `agent_name`, `insight_type`, `title`, `description`, `severity`                              |

---

## 3. End-to-End Flow Sequence: Viewing the Inventory Page

1.  **Frontend (Page Load):** The `Inventory.tsx` page loads. The `useInventoryFlowDetection` hook runs, which in turn calls `useDiscoveryFlowList` to fire `GET /master-flows/active`. It identifies the correct `flowId`.
2.  **Frontend (Hook):** The `useUnifiedDiscoveryFlow` hook, now with a `flowId`, fires its `useQuery` to call `GET /flows/{flowId}/status`.
3.  **Backend (Service):** The `MasterFlowOrchestrator` retrieves the current state of the flow from the `master_flows` table. It also fetches related data requested by the frontend, including all records from `asset_inventory` and `agent_insights` that are linked to the `flow_id`.
4.  **Backend (Response):** The orchestrator bundles the flow status, the asset list, and the agent insights into a single `FlowStatusResponse` JSON object and sends it to the frontend.
5.  **Frontend (Render):**
    *   The `InventoryContent` component receives the `asset_inventory` array from the `flowState` and renders the asset table and overview charts.
    *   The `EnhancedInventoryInsights` component receives the `agent_insights` array and renders the AI-driven analysis.

---

## 4. Troubleshooting Breakpoints

| Stage      | Potential Failure Point                                                                                                     | Diagnostic Checks                                                                                                                                                                                                                                                                                                 |
|------------|-----------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Frontend** | **No Data Displayed:** The inventory table is empty. This is likely because the `asset_inventory` key in the `GET /flows/{flowId}/status` response is empty or missing. | **Browser DevTools (Network Tab):** Inspect the JSON response for `GET /flows/{flowId}/status`. Verify that the `asset_inventory` and `agent_insights` arrays are present and contain data. <br/> **React DevTools:** Check the `flowState` prop being passed to `InventoryContent`. |
| **Backend**  | **Incomplete Inventory:** The inventory list is missing assets. This could mean the **Inventory Manager** agent failed to consolidate data from other agents or that a classification agent failed. | **Docker Logs:** Check `migration_backend` logs for errors during the `inventory` phase of the flow. Look for logs from the `asset_inventory_crew`. <br/> **Agent Observability:** Check the status of the inventory agents. Did they all run successfully?                                                                 |
| **Database** | **Data Integrity Issues:** The `asset_inventory` table contains duplicate assets or assets with inconsistent data (e.g., wrong `asset_type`). This points to flawed logic in the **Inventory Manager** agent. | **Direct DB Query:** Connect to the database and manually inspect the data. `docker exec -it migration_db psql -U user -d migration_db`. <br/> **Query:** `SELECT asset_type, COUNT(*) FROM asset_inventory WHERE flow_id = 'your-flow-id' GROUP BY asset_type;` to check classification distribution. | 