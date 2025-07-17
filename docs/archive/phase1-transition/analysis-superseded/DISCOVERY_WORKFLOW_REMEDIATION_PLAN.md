# Discovery Workflow Remediation Plan

**Date:** 2025-06-15
**Author:** Cascade AI
**Status:** In Progress (Revised based on deep code audit)

## 1. Objective

This document is the single source of truth for the remediation of the Discovery Workflow in the AI Modernize Migration Platform. It is designed to resolve all critical gaps in state management, session handling, agentic compliance, and multi-tenancy. This revised version reflects the **actual state of the codebase** after a detailed audit and prioritizes fixing a core architectural flaw that prevents state persistence.

---

## 2. Phased Remediation Plan & Task Tracker

### **Phase 0: Core Architectural Refactoring (CRITICAL BLOCKER)**
**Problem:** The `CrewAIFlowService` is a flawed singleton that does not correctly initialize or use the `WorkflowStateService`, preventing all workflow state from being persisted to the database. The frontend is polling for states that are never saved. This must be fixed before any other progress can be made.

- [x] **Refactor `CrewAIFlowService` to a standard injectable class.**
    - [x] Remove the singleton pattern (`__new__`, `_instance`, global instance) from `crewai_flow_service.py`.
- [x] **Implement correct dependency injection for `CrewAIFlowService`.**
    - [x] Create a new dependency provider function (e.g., `get_crewai_flow_service`) in `discovery_flow.py` or a shared dependency file.
    - [x] This provider function must initialize `WorkflowStateService` with a DB session and then inject it into a new `CrewAIFlowService` instance.
- [x] **Update API endpoints to use the new dependency provider.**
    - [x] All endpoint functions in `discovery_flow.py` must get the service via `service: CrewAIFlowService = Depends(get_crewai_flow_service)`.
- [x] **Refactor `CrewAIFlowService` to exclusively use `WorkflowStateService`.**
    - [x] Remove all usage of the old in-memory `self.active_flows` dictionary.
    - [x] All methods for creating, getting, or updating state (e.g., `get_flow_state_by_session`) MUST use `self.state_service` to interact with the database.

### **Phase 1: Persistent, Context-Aware State Foundation**
**Status:** Complete. The core architectural flaw has been resolved, and the state foundation is now correctly integrated.

- [x] Define and implement a persistent `WorkflowState` SQLAlchemy model.
    _(**Verified:** `backend/app/models/workflow_state.py` is correct.)_
- [x] Implement `WorkflowStateService` for CRUD operations.
    _(**Verified:** `backend/app/services/workflow_state_service.py` is correct.)_
- [x] Alembic migration for `workflow_states` table.
    _(**Verified:** Migration script exists.)_
- [x] **Ensure all state ops in `CrewAIFlowService` use the `WorkflowStateService`.**
    _(**Verified:** All state methods now correctly use the persistent service.)_
- [x] **Ensure all state ops require and propagate `client_account_id`, `engagement_id`, `session_id`.**
    _(**Verified:** Service methods and API endpoints correctly pass context.)_

### **Phase 2: Agentic-Only, Unified Workflow Orchestration**
**Status:** Completed. With the state foundation fixed, these tasks are now unblocked.

- [x] Remove/refactor all endpoints not routed through CrewAI agentic flow (see `discovery_phase_backend_audit_report.md`).
    _(**Status:** Major violating files and endpoints have been deleted.)_
- [x] Ensure all feedback, asset, and discovery logic is agent-driven and context-aware.
    _(**Status:** Completed by removing non-agentic endpoints.)_
- [x] Refactor or remove all direct handler/fallback endpoints from production flow.
    _(**Status:** Completed by removing violating files.)_
- [x] Update all API endpoints to require and enforce context (client, engagement, session) via the dependency injection pattern from Phase 0.
    _(**Verified:** The remaining agentic endpoint (`discovery_flow`) uses the correct dependency injection pattern.)_

### **Phase 3: Session Management & API Expansion**
**Status:** In Progress. These tasks are now unblocked.

- [ ] **(IN PROGRESS)** Verify session creation on import is saving correctly via the refactored `CrewAIFlowService`.
- [ ] Add/expand endpoints for:
    - [ ] Session switching
    - [ ] Session merging
    - [ ] Setting default session
- [ ] Document session management logic for future maintainers.

### **Phase 4: Integration Tests & Validation**
**Status:** Minimal coverage. Blocked by Phase 0.

- [ ] **(BLOCKED)** Write integration tests for the refactored `CrewAIFlowService`.
    - [ ] Test end-to-end flow: initiate → poll status → retrieve results (verifying DB persistence).
- [ ] Write integration tests for:
    - [ ] Session creation, switching, merging.
    - [ ] Multi-tenant isolation (verifying no data leakage between contexts).
- [ ] Validate that only agentic endpoints are used by UI and tests.
- [ ] Document test coverage and any gaps.

### **Phase 5: Frontend Refactor & UX**
**Status:** Remarkably well-aligned with the intended (but broken) backend. No major frontend refactor is needed, just a stable backend to communicate with.

- [x] Update Discovery/CMDB Import page to initiate a workflow and get a session ID.
    _(**Verified:** `useCMDBImport.ts` correctly creates a `sessionId` and passes it to the backend.)_
- [x] Use session ID for all status polling.
    _(**Verified:** `useFileAnalysisStatus` hook polls the correct endpoint using the `sessionId`.)_
- [x] Render multi-stage agentic progress UI.
    _(**Verified:** `FileAnalysis.tsx` is capable of rendering progress based on polling data.)_
- [ ] **(BLOCKED)** Add UI for session management (merge, switch, set default) after backend APIs are created.
- [ ] **(BLOCKED)** Verify end-to-end UX works once the backend is fixed.
- [ ] **(BLOCKED)** Refactor existing Session UI (`/pages/session`, `SessionContext.tsx`, `sessionService.ts`) to use the new backend APIs and dependency-injected services once they are available.
- [ ] **(BLOCKED)** Ensure session switching and management UX works correctly after the backend is fixed.

### **Phase 6: Recent Progress & Next Steps**

#### **Completed (2025-06-15)**
- [x] Aligned frontend API endpoints with backend services
- [x] Implemented real-time status polling in the UI
- [x] Added proper error handling and retry logic for API calls
- [x] Updated status display to show current analysis phase
- [x] Enhanced type safety for API responses

#### **Current Focus**
- [ ] Resolve TypeScript errors in TechDebtAnalysis component
- [ ] Add proper error boundaries and loading states
- [ ] Implement session management UI
- [ ] Add comprehensive test coverage

#### **Known Issues**
1. TypeScript errors in TechDebtAnalysis related to context properties
2. Missing module declarations for papaparse
3. Need to verify end-to-end flow with backend services

#### **Next Steps**
1. Fix remaining TypeScript errors
2. Add proper error boundaries and loading states
3. Implement session management UI
4. Write integration tests for the complete workflow
5. Document the implementation details and API contracts

*   **Hour 2: Final Integration Testing**
    *   **Activity:** Run an end-to-end test to validate the entire remediated flow.
    *   **Task 2.1:** Execute the Alembic migration script on a fresh test database.
    *   **Task 2.2:** Manually trigger the discovery workflow by calling the data import API endpoint.
    *   **Task 2.3:** While the workflow is running, use the status API endpoint to poll for progress and verify that the `current_phase` and `status` are updated in the database after each step.
    *   **Task 2.4:** Once complete, verify that the final state is correctly marked as "completed" and that all UI pages dependent on the workflow data are now functional.

---

## 3. Success Criteria

*   **The `CrewAIFlowService` is a standard dependency-injected service, not a global singleton.**
*   **The discovery workflow state is successfully persisted in the `workflow_states` database table on initiation.**
*   A server restart does not result in the loss of in-progress workflows.
*   **The frontend can successfully poll the `/agent/crew/analysis/status` endpoint and retrieve the workflow state from the database.**
*   All data operations are strictly isolated by client and engagement context through the service layer.
*   The codebase has a single, clear, and maintainable pattern for service dependency injection. 