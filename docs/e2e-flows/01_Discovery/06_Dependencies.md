
# Data Flow Analysis Report: Dependencies Page

This document provides a complete, end-to-end data flow analysis for the `Dependencies` page of the AI Force Migration Platform.

**Analysis Date:** 2024-07-29

**Assumptions:**
*   The analysis focuses on the `Dependencies` page.
*   The `GET /flows/{flowId}/status` endpoint is the primary source of data for this page.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.

---

## 1. Frontend: Components and API Calls

The `Dependencies` page is responsible for visualizing application and server dependencies, powered by a backend CrewAI analysis.

### Key Components & Hooks
*   **Page Component:** `src/pages/discovery/Dependencies.tsx`
*   **Core Logic:** The page relies on two main hooks:
    *   `useDependenciesFlowDetection`: To identify the active discovery flow.
    *   `useDependencyLogic`: To encapsulate the page's logic, which in turn uses `useUnifiedDiscoveryFlow` for all backend communication.

### API Call Mapping Table

| #  | HTTP Call                                     | Triggering Action / Hook (`useQuery`)                  | Payload / Key Parameters                     | Expected Response                                                                                                                                                                          |
|----|-------------------------------------------------|--------------------------------------------------------|----------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1  | `GET /master-flows/active?flowType=discovery` | `useDiscoveryFlowList` on page load (via `useDependenciesFlowDetection`). | `clientAccountId`, `engagementId`            | `MasterFlowResponse[]` (List of active discovery flows to identify the correct `flowId`).                                                                                                  |
| 2  | `GET /flows/{flowId}/status`                  | `useUnifiedDiscoveryFlow` (polls when flow is active). | `flowId`                                     | `FlowStatusResponse` object. For this page, the response is expected to be populated with a `dependency_analysis` object containing graph data, mappings, and complexity scores. |
| 3  | `POST /flows/{flowId}/execute`                | User clicks "Analyze Dependencies" (`analyzeDependencies`).  | `flowId`, `phase: 'dependency_analysis'`     | Updated flow status, advancing the workflow to the dependency analysis phase.                                                                                                              |

---

## 2. Backend, ORM, and Database Trace

The backend process is triggered when the user initiates the dependency analysis phase.

### Trace for `dependency_analysis` population (via `GET /flows/{flowId}/status`)
1.  **API Router & Service Layer:** The `POST /flows/{flowId}/execute` call is handled by the `MasterFlowOrchestrator`, which transitions the flow to the `dependency_analysis` phase.
2.  **CrewAI Interaction:**
    *   The orchestrator invokes the **Dependency Analysis Crew**.
    *   **Agents Involved:**
        *   **Network Log Analyst:** Scans network traffic logs and firewall rules.
        *   **Configuration File Parser:** Parses configuration files (e.g., `.xml`, `.properties`) to find connection strings and endpoints.
        *   **Process Communication Analyst:** Analyzes running processes on servers to identify inter-process communication.
        *   **Dependency Synthesis Expert:** Consolidates all findings into a coherent dependency graph, mapping relationships between applications and servers.
3.  **ORM Operation:**
    *   The `Dependency Synthesis Expert` persists the discovered relationships.
    *   **Repository:** `DependencyRepository`.
    *   **Model:** `Dependency`.
    *   **Operation:** `BULK INSERT` into the `dependencies` table. Each row represents a link between a source and a target asset.

### Database Tables

| ORM Model     | PostgreSQL Table | Relevant Columns                                                                     |
|---------------|------------------|--------------------------------------------------------------------------------------|
| `Dependency`  | `dependencies`   | `id`, `flow_id`, `source_asset_id`, `target_asset_id`, `port`, `protocol`, `direction` |

---

## 3. End-to-End Flow Sequence: User Triggers Dependency Analysis

1.  **Frontend (User Action):** The user clicks the "Analyze Dependencies" button on the `Dependencies` page.
2.  **Frontend (Hook):** The `onClick` event triggers the `analyzeDependencies` function in the `useDependencyLogic` hook.
3.  **Frontend (API Call):** The hook calls `updatePhase('dependency_analysis')`, which sends a `POST /flows/{flowId}/execute` request with the payload `{ "phase": "dependency_analysis" }`.
4.  **Backend (Orchestrator):** The `MasterFlowOrchestrator` receives the request, updates the flow's state, and starts the **Dependency Analysis Crew**.
5.  **Backend (CrewAI & Database):** The agents in the crew analyze the available data and populate the `dependencies` table with their findings.
6.  **Frontend (Polling & UI Update):** The `useUnifiedDiscoveryFlow` hook, which is continuously polling `GET /flows/{flowId}/status`, eventually receives a response containing the populated `dependency_analysis` object. The `DependencyGraph` and other components on the page then render the new data.

---

## 4. Troubleshooting Breakpoints

| Stage      | Potential Failure Point                                                                                                     | Diagnostic Checks                                                                                                                                                                                                                                                                                                  |
|------------|-----------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Frontend** | **Graph Not Rendering:** The dependency graph is empty or incorrect. This is likely because the `dependency_analysis` key in the `GET /flows/{flowId}/status` response is empty. | **Browser DevTools (Network Tab):** Inspect the JSON response for `GET /flows/{flowId}/status`. Verify that the `dependency_analysis` object is present and contains the expected mapping arrays (`app_server_mapping`, etc.). <br/> **React DevTools:** Check the `dependencyData` prop being passed to `DependencyGraph`. |
| **Backend**  | **Inaccurate Mappings:** The dependency graph shows incorrect or missing connections. This points to a failure in one of the analysis agents (e.g., the Network Log Analyst couldn't access logs). | **Docker Logs:** Check `migration_backend` for errors during the `dependency_analysis` phase. Look for logs related to file parsing or network access failures. <br/> **Agent Observability:** Check the status of the dependency agents. Did they all complete? Did they report any errors?                                    |
| **Database** | **Performance Issues:** With thousands of assets, querying the `dependencies` table to build the graph becomes slow. | **Direct DB Query:** Ensure the `dependencies` table is properly indexed on `flow_id`, `source_asset_id`, and `target_asset_id`. Use `EXPLAIN ANALYZE` on the graph-building queries to verify index usage. `docker exec -it migration_db psql -U user -d migration_db`.                                                  | 