
# E2E Data Flow Analysis: Dependency Analysis

**Analysis Date:** 2025-08-12  
**Status:** Enhanced with Persistent Agents and Specialized Dependency Analysis Tools

This document provides a complete, end-to-end data flow analysis for the `Dependency Analysis` page and the backend processes that generate the dependency graph.

**Core Architecture:**
*   **Persistent Agents (ADR-015):** Dependency analysis uses persistent, tenant-scoped agents with specialized tools for comprehensive dependency mapping
*   **Multi-Type Analysis:** Agents analyze network, configuration, data, and service dependencies to build a complete picture
*   **Critical Path Detection:** Identifies bottlenecks, circular dependencies, and critical migration paths
*   **Migration Wave Planning:** Automatically groups assets into migration waves based on dependency analysis
*   **Parallel Execution:** Dependency Analysis and Technical Debt Analysis can be executed in parallel for optimization
*   **State-Driven Visualization:** The frontend dependency graph visualizes the `dependencies` object from the flow state
*   **Memory-Enabled Learning:** Agents remember patterns from previous analyses to improve accuracy over time

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

## 2. Dependency Analysis Tools and Capabilities

The persistent agents have access to specialized tools for comprehensive dependency analysis:

### Available Tools

1. **DependencyAnalysisTool** (`dependency_analyzer`)
   - Analyzes multiple dependency types (network, configuration, data, service)
   - Identifies bottlenecks and critical components
   - Detects circular dependencies
   - Provides migration insights

2. **DependencyGraphBuilderTool** (`dependency_graph_builder`)
   - Builds visual dependency graphs with nodes and edges
   - Calculates confidence scores for dependencies
   - Supports hierarchical and force-directed layouts
   - Prepares visualization-ready data structures

3. **MigrationWavePlannerTool** (`migration_wave_planner`)
   - Plans migration waves based on dependencies
   - Groups interdependent assets
   - Minimizes migration disruption
   - Provides risk assessment per wave

4. **TopologyMappingTool** (`topology_mapping_tool`)
   - Maps application topology and hosting relationships
   - Identifies application tiers
   - Analyzes network topology
   - Builds dependency chains

5. **IntegrationAnalysisTool** (`integration_analysis_tool`)
   - Analyzes integration patterns between applications
   - Maps communication flows
   - Assesses integration complexity
   - Identifies modernization opportunities

### Dependency Types Analyzed

- **Network Dependencies**: IP addresses, ports, network connections
- **Configuration Dependencies**: Connection strings, endpoints, API references
- **Data Dependencies**: Database connections, data flows, shared storage
- **Service Dependencies**: Load balancers, security groups, shared services

## 3. Backend: The Dependency Analysis Crew

The dependency analysis is performed by the `DependencyAnalysisExecutor`, which is triggered when the `MasterFlowOrchestrator` advances the flow to this phase.

### Execution Flow with Persistent Agents

1.  **Phase Invocation:** The `MasterFlowOrchestrator` triggers the `dependency_analysis` phase
2.  **Persistent Agent Retrieval:** The execution engine retrieves persistent agents from `TenantScopedAgentPool`:
    *   **pattern_discovery_agent**: Primary agent for dependency analysis with all dependency tools
    *   **business_value_analyst**: Assesses business impact of dependencies
    *   **risk_assessment_agent**: Identifies dependency-related risks
3.  **Tool-Based Analysis:**
    *   Pattern discovery agent uses `dependency_analyzer` to analyze all dependency types
    *   Uses `dependency_graph_builder` to create visual graph structure
    *   Applies `migration_wave_planner` to group assets for migration
    *   Leverages existing `topology_mapping_tool` and `integration_analysis_tool`
4.  **Memory and Learning:**
    *   Agents remember successful dependency patterns
    *   Learn client-specific integration patterns
    *   Improve accuracy with each analysis
5.  **State Persistence:**
    *   Results saved to `dependencies` key in flow state
    *   Includes graph structure, analysis results, and migration waves

### Database Interaction

*   **Table:** `crewai_flow_state_extensions`
*   **Operation:** The executor performs an `UPDATE` on the `state` JSONB column for the active `flow_id`. The `dependencies` key within the JSON object is populated with the complete dependency graph, including nodes and edges. No separate `dependencies` table is used.

### Critical Path and Bottleneck Detection

The dependency analysis identifies:

- **Bottlenecks**: Assets with high connectivity that could block migration
- **Circular Dependencies**: Components that depend on each other (must migrate together)
- **Critical Paths**: Longest dependency chains that require careful sequencing
- **Independent Components**: Assets with no dependencies (can migrate first)

### Migration Wave Planning

Based on dependency analysis, assets are grouped into waves:

1. **Wave 1 - Independent Components**: No dependencies, low risk, parallel migration
2. **Wave 2 - Low Dependency Components**: Few dependencies, medium risk
3. **Wave 3 - Critical Dependencies**: Bottlenecks and high-connectivity assets
4. **Wave 4 - Circular Dependency Groups**: Must migrate as atomic units

---

## 4. End-to-End Flow Sequence: Generating and Viewing the Graph

1.  **Frontend (User Action):** After the inventory is built, user clicks "Analyze Dependencies"
2.  **Frontend (API Call):** POST to `/api/v1/master-flows/{flowId}/resume` to start `dependency_analysis` phase
3.  **Backend (Agent Execution):** 
    - Persistent agents retrieved from TenantScopedAgentPool
    - Pattern discovery agent analyzes dependencies using specialized tools
    - Business and risk agents assess impact and risks
    - Dependency graph built with confidence scores
    - Migration waves planned automatically
4.  **Backend (Memory Update):** Agents update their memory with discovered patterns
5.  **Backend (State Persistence):** Dependency graph and analysis saved to flow state
6.  **Frontend (UI Update):** Receives updated state via WebSocket/polling
7.  **Frontend (Visualization):** Renders interactive dependency graph with:
    - Nodes colored by asset type and criticality
    - Edges showing dependency types and confidence
    - Bottlenecks and critical paths highlighted
    - Migration wave groupings displayed

---

## 5. Agent Tool Distribution for Dependency Analysis

| Agent | Dependency Tools | Purpose |
|-------|-----------------|---------||
| **pattern_discovery_agent** | All 3 dependency tools + topology/integration tools | Primary dependency analysis |
| **business_value_analyst** | Dependency tools for impact assessment | Business impact of dependencies |
| **risk_assessment_agent** | Dependency tools for risk analysis | Dependency-related risk assessment |

## 6. Troubleshooting Breakpoints

| Stage      | Potential Failure Point                                                                                                | Diagnostic Checks                                                                                                                                                                                                                                                                                           |
|------------|------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Frontend** | **Graph is Empty:** The page loads, but no dependency graph is shown. This means the `dependencies` key in the flow's state object is missing or empty. | **React DevTools:** Inspect the `flowState` object from the `useUnifiedDiscoveryFlow` hook. Does the `dependencies` key exist? Does it contain nodes and edges for the graph?                                                                                                       |
| **Backend**  | **Incorrect Graph:** The graph shows missing or incorrect connections. This suggests a failure or logical error in one of the analysis agents. | **Docker Logs:** Check `migration_backend` logs for errors from the `DependencyAnalysisExecutor` or any of its constituent agents. The logs may indicate issues with accessing data sources (like network logs).                                                                  |
| **Database** | **State Not Updating:** The dependency graph is generated by the crew but is not correctly saved to the flow's state in the database. | **Direct DB Query:** Connect to the database and inspect the `state` column for your `flow_id`: `SELECT state -> 'dependencies' FROM crewai_flow_state_extensions WHERE flow_id = 'your-flow-id';`. Verify that the JSON data is present and contains the expected graph structure. | 