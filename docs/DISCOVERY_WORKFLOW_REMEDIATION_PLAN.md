# Discovery Workflow Remediation Plan

**Date:** 2024-07-27
**Author:** AI Assistant
**Status:** In Progress

## 1. Objective

This document outlines a detailed, phased plan to re-architect the AI Force Discovery Workflow. The primary goal is to resolve the critical gaps identified in the `POST_MULTITENANCY_DISCOVERY_GAPS_ANALYSIS.md` report by implementing a **persistent, centralized, and multi-tenancy-aware state management system**.

The successful execution of this plan will result in a reliable, scalable, and observable discovery process that provides a seamless experience for the user.

---

## 2. Remediation Phases & Hourly Breakdown

### **Phase 1: Code Cleanup & Persistent State Foundation (Est. 2 Hours)**

This phase focuses on removing dead code and establishing the database foundation for persistent state.

*   **Hour 1: Archive and Remove Obsolete Code**
    *   **Activity:** Move identified dead code to an `archived` folder for reference.
    *   **Task 1.1:** [✅ COMPLETED] Create an `archived` directory for obsolete code.
    *   **Task 1.2:** [✅ COMPLETED] Delete the obsolete `backend/app/services/crewai_flow_handlers/flow_state_handler.py` file.
    *   **Task 1.3:** [✅ COMPLETED] Remove import and usage of the archived `FlowStateHandler`.

*   **Hour 2: Create Database Model for Persistent State**
    *   **Activity:** Define the database schema for storing workflow state. This directly addresses **Gap 2: No Persistence**.
    *   **Task 2.1:** Create a new file: `backend/app/models/workflow_state.py`.
    *   **Task 2.2:** In this file, define a new SQLAlchemy model named `WorkflowState`. It will include columns for:
        *   `id` (Primary Key)
        *   `session_id` (Indexed, Foreign Key to `data_import_sessions`)
        *   `client_account_id` (Indexed)
        *   `engagement_id` (Indexed)
        *   `workflow_type` (e.g., "discovery")
        *   `current_phase` (e.g., "data_validation", "field_mapping")
        *   `status` (e.g., "running", "completed", "failed")
        *   `state_data` (JSONB or JSON type to store the Pydantic state model)
        *   `created_at`, `updated_at` (Timestamps)
    *   **Task 2.3:** Generate a new Alembic migration script to create the `workflow_states` table in the database.

### **Phase 2: Centralized, Persistent State Management (Est. 3 Hours)**

This phase focuses on building a single, reliable service for all state operations.

*   **Hour 1: Develop the `WorkflowStateService`**
    *   **Activity:** Create a new service to act as the single source of truth for workflow state, addressing **Gap 1: Disconnected State Management**.
    *   **Task 1.1:** Create a new file: `backend/app/services/workflow_state_service.py`.
    *   **Task 1.2:** Implement the `WorkflowStateService` class.
    *   **Task 1.3:** Create core methods that perform CRUD operations on the `WorkflowState` database model:
        *   `create_workflow_state(...)`: Creates a new record in the `workflow_states` table.
        *   `get_workflow_state_by_session_id(...)`: Retrieves a state record.
        *   `update_workflow_state(...)`: Updates fields like `status`, `current_phase`, and the `state_data` JSON blob.

*   **Hour 2: Implement Context-Aware State Operations**
    *   **Activity:** Refactor the new service to enforce multi-tenancy, addressing **Gap 3: Ineffective Context Propagation**.
    *   **Task 2.1:** Modify all data retrieval and update methods in `WorkflowStateService` to require `client_account_id` and `engagement_id` in their signatures.
    *   **Task 2.2:** Ensure all database queries within the service are strictly filtered by these context IDs to guarantee data isolation.
    *   **Task 2.3:** Add methods to retrieve all workflow states for a given `engagement_id` to support UI views.

*   **Hour 3: Integrate State Service into `CrewAIFlowService`**
    *   **Activity:** Replace the old in-memory state management with the new persistent service.
    *   **Task 3.1:** In `backend/app/services/crewai_flow_service.py`, remove the `self.active_flows` dictionary.
    *   **Task 3.2:** Inject the new `WorkflowStateService`.
    *   **Task 3.3:** In the `initiate_data_source_analysis` method, immediately after creating the initial `DiscoveryFlowState` object, call `workflow_state_service.create_workflow_state()` to persist it *before* the background task starts.

### **Phase 3: Refactor Workflow Orchestration (Est. 3 Hours)**

This phase focuses on making the workflow itself resilient and ensuring progress is saved at every step.

*   **Hour 1: Refactor `DiscoveryWorkflowManager`**
    *   **Activity:** Decouple the workflow manager from the transient, in-memory state object.
    *   **Task 1.1:** Inject `WorkflowStateService` into `DiscoveryWorkflowManager`.
    *   **Task 1.2:** Modify the main `run_workflow` loop. Instead of passing the `flow_state` object from one step to the next, the manager will now be responsible for persisting the state after each step.

*   **Hour 2: Implement Step-by-Step State Persistence**
    *   **Activity:** Persist the workflow's progress after every successful step, which will fix **Gap 4: Broken UI Feedback Loop**.
    *   **Task 2.1:** Inside the `_execute_workflow_step` method of the `DiscoveryWorkflowManager`, after a step handler returns successfully, call `workflow_state_service.update_workflow_state()` to save the latest `state_data`, `current_phase`, and `status`.
    *   **Task 2.2:** In case of failure (in the `_handle_workflow_failure` method), use the service to update the state to "failed" and persist the error information.

*   **Hour 3: Adopt Structured State Best Practices**
    *   **Activity:** Improve the structure and reliability of the state object itself, addressing **Gap 5: CrewAI Best Practices**.
    *   **Task 3.1:** Review and enhance the `DiscoveryFlowState` Pydantic model in `app/schemas/flow_schemas.py`. Add explicit fields for all data that needs to be passed between steps.
    *   **Task 3.2:** Ensure this Pydantic model is the definitive structure that gets serialized into the `state_data` JSON column, providing a single, validated source of truth for the workflow's state.

### **Phase 4: API and Testing (Est. 2 Hours)**

This phase ensures the frontend can correctly consume the new persistent state.

*   **Hour 1: Update API Endpoints for Status Polling**
    *   **Activity:** Modify the backend API to serve the persisted, real-time workflow status.
    *   **Task 1.1:** Locate the API endpoint(s) the UI uses to poll for discovery progress.
    *   **Task 1.2:** Rewrite these endpoints to use `WorkflowStateService` to fetch the latest state from the database for the user's current context.
    *   **Task 1.3:** Ensure the API returns the full state object, including `current_phase`, `status`, and `progress_percentage`.

*   **Hour 2: Final Integration Testing**
    *   **Activity:** Run an end-to-end test to validate the entire remediated flow.
    *   **Task 2.1:** Execute the Alembic migration script on a fresh test database.
    *   **Task 2.2:** Manually trigger the discovery workflow by calling the data import API endpoint.
    *   **Task 2.3:** While the workflow is running, use the status API endpoint to poll for progress and verify that the `current_phase` and `status` are updated in the database after each step.
    *   **Task 2.4:** Once complete, verify that the final state is correctly marked as "completed" and that all UI pages dependent on the workflow data are now functional.

---

## 3. Success Criteria

*   The discovery workflow state is successfully persisted in the database.
*   A server restart does not result in the loss of in-progress workflows.
*   The UI can accurately poll and display the real-time progress of a running workflow.
*   All data operations are strictly isolated by client and engagement context.
*   The codebase has a single, clear, and maintainable service for state management. 