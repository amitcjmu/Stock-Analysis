
# Data Flow Analysis Report: AttributeMapping Page

This document provides a complete, end-to-end data flow analysis for the `AttributeMapping` page of the AI Force Migration Platform.

**Analysis Date:** 2024-07-29

**Assumptions:**
*   The analysis focuses on the `AttributeMapping` page as the target.
*   The platform operates entirely within a Docker environment (`migration_frontend`, `migration_backend`, `migration_db`).
*   All API calls require authentication and multi-tenant context headers (`X-Client-Account-ID`, `X-Engagement-ID`).

---

## 1. Frontend: Components and API Calls

The `AttributeMapping` page is built with Next.js and TypeScript. Its primary role is to allow users to map uploaded data to the platform's schema, leveraging AI for suggestions. The core logic is encapsulated in a series of React hooks, with API interactions managed by TanStack Query (`useQuery`, `useMutation`).

### Key Components & Hooks
*   **Page Component:** `src/pages/discovery/AttributeMapping/index.tsx`
*   **Primary Logic Hook:** `src/pages/discovery/AttributeMapping/hooks/useAttributeMapping.ts`
*   **Core Business Logic & API Calls:** `src/hooks/discovery/useAttributeMappingLogic.ts`
*   **Flow State Management:** `src/hooks/useUnifiedDiscoveryFlow.ts`
*   **Flow List & Detection:** `src/hooks/discovery/useDiscoveryFlowAutoDetection.ts` & `src/hooks/discovery/useDiscoveryFlowList.ts`
*   **API Service Layer:** `src/services/api/masterFlowService.ts` & `src/services/api/masterFlowService.extensions.ts`

### API Call Mapping Table

| #  | HTTP Call                                                         | Triggering Action / Hook (`useQuery`)                                  | Payload / Key Parameters      | Expected Response                                                               |
|----|-------------------------------------------------------------------|------------------------------------------------------------------------|-------------------------------|---------------------------------------------------------------------------------|
| 1  | `GET /master-flows/active?flowType=discovery`                     | `useDiscoveryFlowList` on page load.                                   | `clientAccountId`, `engagementId` | `MasterFlowResponse[]` (List of active discovery flows)                         |
| 2  | `GET /flows/{flowId}/status`                                      | `useUnifiedDiscoveryFlow` (polls when flow is active).                 | `flowId`                      | `FlowStatusResponse` (Detailed status of a single flow)                         |
| 3  | `GET /api/v1/data-import/flow/{flowId}/import-data`               | `useAttributeMappingLogic` on page load.                               | `flowId`                      | JSON object with import metadata and sample data.                               |
| 4  | `GET /api/v1/data-import/latest-import`                           | `useAttributeMappingLogic` (fallback if flow-specific import fails).   | `clientAccountId`             | JSON object with the latest import data for the client.                         |
| 5  | `GET /api/v1/data-import/field-mapping/imports/{id}/field-mappings` | `useAttributeMappingLogic` after import data is fetched.               | `importId`                    | Array of field mapping objects (source, target, confidence).                    |
| 6  | `GET /api/v1/data-import/imports/{id}`                            | `useAttributeMappingLogic` to supplement mappings with all source fields. | `importId`                    | JSON with raw data details, including all original columns.                     |
| 7  | `GET /api/v1/discovery/critical-attributes-status`                | `useAttributeMappingLogic` after flow is identified.                   | `flowId`                      | JSON with status of critical attributes mapping.                                |
| 8  | `POST /discovery/flow/{flowId}/resume`                            | User clicks "Trigger Analysis" (`handleTriggerFieldMappingCrew`).      | `user_approval: true`         | Confirmation of flow resumption.                                                |
| 9  | `POST /api/v1/data-import/field-mapping/approval/approve-mapping/{id}` | User clicks "Approve" on a mapping (`handleApproveMapping`).           | `mappingId`                   | Success message.                                                                |
| 10 | `GET /data-import/mappings/approval-status/{id}`                  | `checkMappingApprovalStatus` (programmatic check).                     | `dataImportId`                | JSON with approval statistics.                                                  |
| 11 | `POST /flows/{flowId}/execute`                                    | `useUnifiedDiscoveryFlow` (`executeFlowPhase` mutation).               | `flowId`, `phase`, `phaseData` | Updated flow status.                                                            |
| 12 | `POST /flows/`                                                    | `useUnifiedDiscoveryFlow` (`initializeFlow` mutation).                 | `MasterFlowRequest` object    | `MasterFlowResponse` with new flow details.                                     |

---

## 2. Backend: API Routers to CrewAI and ORM

Each frontend API call is routed by FastAPI to a specific service, which may involve CrewAI agents for intelligent processing and the SQLAlchemy ORM for database operations.

### Trace for `POST /api/v1/data-import/field-mapping/approval/approve-mapping/{id}` (Approve Mapping)
1.  **API Router:** The request hits a FastAPI router, likely in a file like `backend/app/api/v1/endpoints/data_import.py`.
2.  **Service Layer:** The router calls a method in a service, for example, `DataImportService.approve_field_mapping()`.
3.  **ORM Operation:** The service method interacts with the database via a repository.
    *   **Repository:** `FieldMappingRepository(db, client_account_id)` is used. It inherits from `ContextAwareRepository`, automatically scoping all queries to the client's account.
    *   **Model:** It updates the `FieldMapping` ORM model.
    *   **Operation:** An `UPDATE` statement is executed.
        ```python
        # Example SQLAlchemy 2.0 async operation
        async with AsyncSessionLocal() as session:
            stmt = (
                update(FieldMapping)
                .where(FieldMapping.id == mapping_id, FieldMapping.client_account_id == client_account_id)
                .values(is_approved=True, approved_by=user_id)
            )
            await session.execute(stmt)
            await session.commit()
        ```

### Trace for `POST /discovery/flow/{flowId}/resume` (Trigger Analysis)
1.  **API Router:** Hits a legacy endpoint, likely in `backend/app/api/v1/endpoints/discovery_flows.py`.
2.  **Service Layer:** Calls the legacy `DiscoveryFlowService`.
3.  **CrewAI Interaction:**
    *   The service kicks off or resumes a CrewAI flow.
    *   **Agent Involved:** The **Pattern Recognition Agent** is tasked with analyzing the source data columns and suggesting mappings to the platform's critical attributes based on learned patterns.
    *   The agent's output (suggested mappings, confidence scores) is then stored.
4.  **ORM Operation:**
    *   **Repository:** Uses `LearningPatternRepository` to fetch existing patterns and `FieldMappingRepository` to store the new AI-suggested mappings.
    *   **Models:** `LearningPattern`, `FieldMapping`.
    *   **Operation:** `SELECT` from `learning_patterns` and `INSERT` into `field_mappings`.

---

## 3. Database: Tables and Queries

All data is stored in a PostgreSQL database, accessed asynchronously via SQLAlchemy.

| ORM Model         | PostgreSQL Table      | Relevant Columns                                                                     | Sample SQL Query (Generated by ORM)                                                                          |
|-------------------|-----------------------|--------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `FieldMapping`    | `field_mappings`      | `id`, `source_field`, `target_field`, `confidence`, `is_approved`, `client_account_id` | `UPDATE field_mappings SET is_approved=%s WHERE id=%s AND client_account_id=%s`                              |
| `LearningPattern` | `learning_patterns`   | `pattern_type`, `source_pattern`, `target_attribute`, `confidence`, `client_account_id`| `SELECT source_pattern, target_attribute FROM learning_patterns WHERE client_account_id=%s`                |
| `MasterFlow`      | `master_flows`        | `id`, `flow_type`, `status`, `current_phase`, `client_account_id`, `engagement_id`     | `SELECT id, status, current_phase FROM master_flows WHERE client_account_id=%s AND flow_type='discovery'` |
| `DataImport`      | `data_imports`        | `id`, `flow_id`, `filename`, `status`, `client_account_id`                            | `SELECT id, filename, status FROM data_imports WHERE flow_id=%s AND client_account_id=%s`                    |

---

## 4. End-to-End Flow Sequence: User Approves a Mapping

1.  **Frontend (User Action):** User clicks the "Approve" button for a suggested mapping in the `AttributeMapping` UI.
2.  **Frontend (Hook):** The `onClick` event triggers the `handleApproveMapping` function inside the `useAttributeMappingLogic` hook.
3.  **Frontend (API Call):** The hook executes `apiCall` to `POST /api/v1/data-import/field-mapping/approval/approve-mapping/{mappingId}`. `X-Client-Account-ID` and `X-Engagement-ID` headers are attached.
4.  **Backend (API Router):** The FastAPI router receives the request and passes it to the `DataImportService`.
5.  **Backend (Service & ORM):** The service uses the `FieldMappingRepository` (which is context-aware) to update the `is_approved` flag for the corresponding record in the database.
6.  **Database:** The `field_mappings` table is updated for the given `mappingId` where the `client_account_id` matches the one from the header.
7.  **Backend (Response):** The API returns a `200 OK` success response.
8.  **Frontend (UI Update):** The `useQuery` managing field mappings is invalidated (`refetchFieldMappings`). It re-fetches the data, and the UI updates to show the mapping as "Approved".

---

## 5. Troubleshooting Breakpoints

| Stage      | Potential Failure Point                                                                                                                                                                                                                                                                   | Diagnostic Checks                                                                                                                                                                                                                                                                                                                                                                |
|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Frontend** | **Incorrect Flow Detected:** The `useDiscoveryFlowAutoDetection` hook picks the wrong flow, leading to a 404 or incorrect data being shown. <br/> **Legacy API Called:** `handleTriggerFieldMappingCrew` calls the deprecated `/discovery/flow/...` endpoint, causing state desync with `MasterFlowOrchestrator`. | **Browser DevTools (Network Tab):** Check API calls. Verify the `flowId` in requests like `GET /flows/{flowId}/status`. Look for 404s. <br/> **React DevTools:** Inspect the state of `useAttributeMappingLogic` and `useUnifiedDiscoveryFlow` to see the `effectiveFlowId`. <br/> **Console Logs:** The hooks are instrumented with detailed logs; check the console for "Flow Detection Debug". |
| **Backend**  | **Missing Context Headers:** Request fails with a 401/403 because `X-Client-Account-ID` or `X-Engagement-ID` is missing. <br/> **CrewAI Agent Failure:** The Pattern Recognition Agent fails or returns low-confidence results.                                                              | **Docker Logs:** Check the `migration_backend` container logs for FastAPI errors: `docker logs -f migration_backend`. <br/> **Agent Health:** Use the observability endpoints (e.g., `/api/v1/observability/agents/status`) to check CrewAI agent health.                                                                                                                             |
| **ORM**      | **Async Session Conflict:** A background task uses a session incorrectly, leading to `DetachedInstanceError` or other session-related exceptions. <br/> **Multi-Tenant Scope Failure:** `ContextAwareRepository` is not used, and data from another client is accessed or modified.                                   | **Enable SQLAlchemy Logging:** Set `logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)` in the backend config to see all generated SQL queries in the logs. <br/> **Code Review:** Ensure all repository methods use `self.query_with_context()` and are instantiated with a `client_account_id`.                                                                     |
| **Database** | **Constraint Violation:** A `FOREIGN KEY` constraint fails (e.g., trying to add a mapping for a non-existent `data_import_id`). <br/> **Deadlock:** Concurrent transactions on the same rows cause a deadlock.                                                                                    | **Direct DB Query:** Connect to the database container and run queries directly to verify data integrity: `docker exec -it migration_db psql -U user -d migration_db`. <br/> **Example:** `SELECT * FROM field_mappings WHERE client_account_id = 'your-client-id';`                                                                                                               | 