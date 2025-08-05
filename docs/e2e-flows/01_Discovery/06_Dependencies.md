
# E2E Data Flow Analysis: Dependency Analysis

**Analysis Date:** 2025-07-13

This document provides a complete, end-to-end data flow analysis for the `Dependency Analysis` page and the backend processes that generate the dependency graph.

**Core Architecture:**
*   **Parallel Execution:** The Dependency Analysis and Technical Debt Analysis phases are executed **in parallel** by the `CrewCoordinator` to optimize performance. The results are stored in the flow's state as they become available.
*   **State-Driven Visualization:** The frontend dependency graph is a direct visualization of the `dependencies` object stored within the flow's main state. The frontend does not fetch dependency data separately.
*   **Orchestrated Agent Execution:** A dedicated `DependencyAnalysisExecutor` manages the execution of a specialized CrewAI crew to perform the analysis.
*   **Fail-Fast Execution:** The backend is designed to fail fast. If the primary CrewAI agents fail, the process halts. There is no fallback to a non-AI or rule-based classification system.

---

## 1. Frontend: Visualizing the Dependency Graph

The `Dependencies` page is responsible for rendering a graph of the application and server dependencies discovered by the backend agents.

### Key Components & Hooks
*   **Page Component:** `src/pages/discovery/Dependencies.tsx`
*   **Core Hooks:**
    *   `useDependenciesFlowDetection`: To identify the active discovery flow from the URL or system state.
    *   `useUnifiedDiscoveryFlow`: The single source of truth for all data, including the dependency graph read from `flowState.dependencies`.

### API Call Summary

| #  | Method | Endpoint                                | Trigger                                       | Description                                                                                       |
|----|--------|-----------------------------------------|-----------------------------------------------|---------------------------------------------------------------------------------------------------|
| 1  | `POST` | `/api/v1/master-flows/{flowId}/resume`  | User clicks "Analyze Dependencies".           | Signals the `MasterFlowOrchestrator` to begin the `dependency_analysis` phase.                    |
| 2  | `GET`  | (WebSocket or Polling)                  | `useUnifiedDiscoveryFlow` hook.               | Listens for updates to the flow's state object to receive the dependency graph data when it's ready.|

---

## 2. Backend: The Dependency Analysis Crew

The dependency analysis is performed by the `DependencyAnalysisExecutor`, which is triggered when the `MasterFlowOrchestrator` advances the flow to this phase.

### Execution Flow

1.  **Executor Invocation:** The `MasterFlowOrchestrator` calls the `DependencyAnalysisExecutor`.
2.  **CrewAI Execution:**
    *   The executor takes the `asset_inventory` generated in the previous phase as its primary input.
    *   It creates and runs the `dependencies` crew. This crew is composed of multiple agents working together:
        *   **Network Log Analyst:** Scans network traffic data.
        *   **Configuration File Parser:** Finds connection strings and endpoints in configuration files.
        *   **Process Communication Analyst:** Identifies inter-process communication on servers.
        *   **Dependency Synthesis Expert:** Consolidates all findings into a unified dependency graph.
3.  **State Persistence:**
    *   The `_store_results` method in the executor takes the final dependency graph object from the crew.
    *   It saves this entire object to the `dependencies` key within the main `state` object of the flow.

### Database Interaction

*   **Table:** `crewai_flow_state_extensions`
*   **Operation:** The executor performs an `UPDATE` on the `state` JSONB column for the active `flow_id`. The `dependencies` key within the JSON object is populated with the complete dependency graph, including nodes and edges. No separate `dependencies` table is used.

---

## 3. End-to-End Flow Sequence: Generating and Viewing the Graph

1.  **Frontend (User Action):** After the inventory is built, the user clicks the "Analyze Dependencies" button.
2.  **Frontend (API Call):** The `useUnifiedDiscoveryFlow` hook sends a `POST` request to `/api/v1/master-flows/{flowId}/resume`, instructing the orchestrator to start the `dependency_analysis` phase.
3.  **Backend (Parallel Execution):** The `MasterFlowOrchestrator` invokes the `CrewCoordinator`, which runs the **Dependency Analysis** and **Technical Debt** crews in parallel.
4.  **Backend (Database Update):** As the `DependencyAnalysisExecutor` finishes, it saves the resulting dependency graph into the flow's `state` object in the database.
5.  **Frontend (UI Update):** The `useUnifiedDiscoveryFlow` hook on the frontend receives the updated flow state via its WebSocket or polling mechanism.
6.  **Frontend (Render):** The `DependencyGraph` component accesses `flowState.dependencies`, and if the data is present, it renders the visual graph of the application and server relationships.

---

## 4. Troubleshooting Breakpoints

| Stage      | Potential Failure Point                                                                                                | Diagnostic Checks                                                                                                                                                                                                                                                                                           |
|------------|------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Frontend** | **Graph is Empty:** The page loads, but no dependency graph is shown. This means the `dependencies` key in the flow's state object is missing or empty. | **React DevTools:** Inspect the `flowState` object from the `useUnifiedDiscoveryFlow` hook. Does the `dependencies` key exist? Does it contain nodes and edges for the graph?                                                                                                       |
| **Backend**  | **Incorrect Graph:** The graph shows missing or incorrect connections. This suggests a failure or logical error in one of the analysis agents. | **Docker Logs:** Check `migration_backend` logs for errors from the `DependencyAnalysisExecutor` or any of its constituent agents. The logs may indicate issues with accessing data sources (like network logs).                                                                  |
| **Database** | **State Not Updating:** The dependency graph is generated by the crew but is not correctly saved to the flow's state in the database. | **Direct DB Query:** Connect to the database and inspect the `state` column for your `flow_id`: `SELECT state -> 'dependencies' FROM crewai_flow_state_extensions WHERE flow_id = 'your-flow-id';`. Verify that the JSON data is present and contains the expected graph structure. | 