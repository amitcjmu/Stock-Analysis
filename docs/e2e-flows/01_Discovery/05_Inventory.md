
# E2E Data Flow Analysis: Asset Inventory

**Analysis Date:** 2025-07-13

This document provides a complete, end-to-end data flow analysis for the `Asset Inventory` page and the backend processes that populate it.

**Core Architecture:**
*   **State-Driven UI:** The frontend is a direct reflection of the flow's state. The entire asset inventory is read from the `asset_inventory` key within the flow's main state object. There are no separate API calls to fetch assets.
*   **Orchestrated Agent Execution:** The inventory is built by a specialized CrewAI crew, which is executed as a distinct phase (`inventory`) within the `MasterFlowOrchestrator`.
*   **Resilient Fallback:** The backend includes a non-AI fallback mechanism that performs a simple, rule-based asset classification if the primary CrewAI agents fail, ensuring the flow can continue.

---

## 1. Frontend: Displaying the Inventory

The `Inventory` page displays the results of the `inventory` phase, which is orchestrated by the backend. The frontend's role is to render the data provided in the flow's state.

### Key Components & Hooks
*   **Page Component:** `src/pages/discovery/Inventory.tsx`
*   **Content Component:** `src/components/discovery/inventory/InventoryContent.tsx`
*   **Core Data Hook:** `useUnifiedDiscoveryFlow` is the single source of truth for all data displayed on this page.

### API Call Summary

| #  | HTTP Call                                     | Triggering Action / Hook                 | Key Parameters       | Description                                                                    |
|----|-------------------------------------------------|------------------------------------------|----------------------|--------------------------------------------------------------------------------|
| 1  | `GET /api/v1/master-flows/active`               | `useInventoryFlowDetection` on page load.| `flowType=discovery` | Fetches the list of active discovery flows to identify the correct `flowId`.   |
| 2  | `GET` (WebSocket or Polling)                    | `useUnifiedDiscoveryFlow` hook.          | `flowId`             | Listens for updates to the flow's state object from the backend.               |
| 3  | `POST /api/v1/master-flows/{flowId}/resume`     | User triggers the next phase.            | `phase: 'dependencies'`| Signals the orchestrator to advance the flow to the next phase (Dependency Analysis). |

---

## 2. Backend: The Asset Inventory Crew

The inventory is built by the `AssetInventoryExecutor`, which is triggered when the `MasterFlowOrchestrator` reaches the `inventory` phase.

### Execution Flow

1.  **Executor Invocation:** The `MasterFlowOrchestrator` calls the `AssetInventoryExecutor`.
2.  **CrewAI Execution:**
    *   The executor takes the `cleaned_data` from the previous phase's output.
    *   It creates and runs the `inventory` crew. This crew is composed of multiple specialized agents:
        *   **Server Classification Expert:** Identifies and categorizes various server types.
        *   **Application Discovery Expert:** Identifies software and applications.
        *   **Device Classification Expert:** Handles other network devices.
        *   **Inventory Manager:** Consolidates the findings from all agents into a single, unified asset list.
3.  **Fallback Execution:** If the `inventory` crew fails for any reason (e.g., LLM timeout), the `execute_fallback` method is triggered. This method performs a simple, rule-based classification based on keywords in the data, ensuring a basic inventory is always produced.
4.  **State Persistence:**
    *   The `_store_results` method takes the final asset list (either from the crew or the fallback).
    *   It saves this entire list as a JSON object to the `asset_inventory` key within the main `state` object of the flow.

### Database Interaction

*   **Table:** `crewai_flow_state_extensions`
*   **Operation:** The executor performs an `UPDATE` on the `state` JSONB column for the active `flow_id`. The `asset_inventory` key within the JSON object is populated with the complete list of discovered assets. No separate `asset_inventory` or `agent_insights` tables are used for this process.

---

## 3. End-to-End Flow Sequence: Viewing the Inventory

1.  **Backend Execution:** The `MasterFlowOrchestrator` completes the `data_cleansing` phase and proceeds to the `inventory` phase, executing the `AssetInventoryExecutor`. The resulting asset list is saved to the flow's state in the database.
2.  **Frontend Page Load:** A user navigates to the `Inventory` page. The `useInventoryFlowDetection` hook identifies the correct `flowId`.
3.  **Frontend Data Fetch:** The `useUnifiedDiscoveryFlow` hook retrieves the latest state for that `flowId`.
4.  **Frontend Render:**
    *   The `InventoryContent` component accesses `flowState.asset_inventory`.
    *   It renders the list of assets found in the state object into the UI, displaying the tables and charts. The page is a direct visual representation of the data stored in the flow's state.

---

## 4. Troubleshooting Breakpoints

| Stage      | Potential Failure Point                                                                                                                                  | Diagnostic Checks                                                                                                                                                                                                                                                                        |
|------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Frontend** | **Inventory is Empty or Stale:** The page loads, but the asset table is empty. This means the `asset_inventory` key in the flow's state object is missing or empty. | **React DevTools:** Inspect the `flowState` object from the `useUnifiedDiscoveryFlow` hook. Does the `asset_inventory` key exist? Does it contain an array of assets?                                                                                                       |
| **Backend**  | **Incomplete Inventory:** The inventory is missing assets or has incorrect classifications. This suggests an issue with one of the agents in the `inventory` crew. | **Docker Logs:** Check `migration_backend` logs for errors from the `AssetInventoryExecutor`. Look for the "using fallback" warning to see if the main crew failed.                                                                                                    |
| **Database** | **State Not Updating:** The `asset_inventory` data is not being correctly saved to the flow's state in the database.                                          | **Direct DB Query:** Connect to the database and inspect the `state` column for your `flow_id`: `SELECT state -> 'asset_inventory' FROM crewai_flow_state_extensions WHERE flow_id = 'your-flow-id';`. Verify that the JSON data is present and structured correctly. | 