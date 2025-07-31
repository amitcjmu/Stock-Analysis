# Lessons Learned for AI Coding Agents

This document consolidates key learnings from troubleshooting and development sessions on the AI Force Migration Platform. Adhering to these principles will help future AI agents avoid common pitfalls, align with the existing architecture, and contribute effectively.

## 1. Architecture & Design Patterns

*   **Master Flow Orchestrator (MFO) is the Single Source of Truth:**
    *   **ALWAYS** use the `MasterFlowOrchestrator` via `/api/v1/flows` for all workflow operations.
    *   **NEVER** call legacy discovery endpoints (`/api/v1/discovery/...`) as this bypasses the MFO and corrupts state.
*   **Two-Table Flow Architecture is Required:**
    *   **Master Flows** (`crewai_flow_state_extensions`): For orchestration and lifecycle management (running, paused, completed).
    - **Child Flows** (`discovery_flows`): For UI-facing operational status and phase-specific data (e.g., `current_phase`, `field_mapping_status`). The UI and agents rely on child flow data for decision-making.
    *   The MFO only creates the master flow record; child flow records must be created **explicitly** within the same atomic transaction.
*   **Data Flow Chaining:** Retrieving data often requires a chained approach. For instance, getting field mappings is a two-step process: `Flow ID` -> `Import ID` -> `Field Mappings`. Do not assume data is available from a single endpoint.
*   **Separation of Concerns:**
    *   The frontend is for **displaying** agent decisions, not for making them.
    *   Business logic (e.g., approval thresholds) should be handled by **CrewAI agents**, not hardcoded in the backend or frontend.
*   **Atomic Transactions for Critical Operations:** Any operation involving multiple state changes (e.g., creating a master flow and its corresponding child flow) **must** be wrapped in an atomic transaction to ensure data integrity. Use `db.flush()` to make objects available for foreign key relationships within the transaction before the final commit.
*   **Background Task Separation:** Long-running operations, such as CrewAI agent executions, should be run in the background and separated from synchronous database transactions to prevent locking and timeouts.

## 2. Backend & Database

*   **Database Schema:**
    *   All application tables reside in the `migration` schema, not the `public` schema. All queries must explicitly reference the `migration` schema.
    *   **ALWAYS** use `CHECK` constraints instead of native PostgreSQL `ENUM` types for better flexibility.
*   **SQLAlchemy Best Practices:**
    *   **Use `== True` for boolean comparisons, not `is True`.** The `is` operator does not work reliably with SQLAlchemy's boolean handling.
    *   Use native `UUID` types in database queries; do not convert them to strings for comparisons.
    *   Use `AsyncAdaptedQueuePool` for the async engine, not `QueuePool`.
*   **Foreign Keys:** Foreign key relationships **must** reference the target table's primary key (typically an integer `id` column), not other unique identifiers like `flow_id`.
*   **Alembic Migrations:**
    *   Make all migration scripts **idempotent** by checking for the existence of tables, columns, or constraints before attempting to create them.
    *   For new deployments, a single comprehensive "initial schema" migration is preferred over many small, fragmented ones.
*   **UUID Handling:**
    *   When passing data to Pydantic models for serialization, explicitly convert `UUID` objects to strings.
    *   Use a consistent, recognizable pattern for demo/fallback UUIDs (e.g., `XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX`) to prevent accidental deletion of real data.

## 3. Frontend & UI/UX

*   **React Best Practices:**
    *   **Adhere strictly to the Rules of Hooks.** Never call hooks inside conditions, loops, or `try/catch` blocks.
    *   **Variable Definition Order Matters.** Avoid temporal dead zones by defining variables and state before they are referenced in hooks or JSX.
    *   Provide a unique `key` prop when rendering lists. Use a stable identifier from the data (like `flow.flow_id`) and provide a fallback (`flow-${index}`) only as a last resort.
*   **API Interaction & State Management (React Query/TanStack Query):**
    *   **Implement robust rate-limiting strategies:**
        *   **Debouncing:** For user-triggered actions like authentication (500ms-1s).
        *   **Exponential Backoff:** For handling `429 Too Many Requests` errors (e.g., retry after 2s, 4s, 8s).
        *   **Request Deduplication:** Prevent multiple identical in-flight requests.
        *   **Caching:** Use longer `staleTime` (e.g., 5 minutes) for data that doesn't change frequently, like field mappings.
    *   **Conditionally enable queries** that depend on data from other queries using the `enabled` flag.
*   **Component Design:**
    *   **Reuse components.** The `ThreeColumnFieldMapper` is a proven pattern; use it instead of creating new complex components for similar functionality.
    *   **Filter existing data** on the client-side rather than creating new API endpoints for slightly different views of the same data.
*   **User Experience:**
    *   **Never delete user data without explicit confirmation.** Replace all automatic cleanup logic with user-initiated approval dialogs.
    *   Default to a working view. If one tab might be empty, make a functional tab the default.
    *   Treat AI-suggested data (e.g., 'suggested' field mappings) as valid and actionable in the UI until a user explicitly rejects it.

## 4. DevOps & Deployment

*   **Docker-First Development:** The entire platform runs in Docker. **NEVER** run services (Next.js, Python, PostgreSQL) locally. All development, testing, and debugging must happen inside the containers using `docker exec`.
*   **Railway Deployment:**
    *   Railway uses `requirements-docker.txt`, not `requirements.txt`.
    *   It provides a single `DATABASE_URL` environment variable. Alembic and other tools must be configured to prioritize this over individual `POSTGRES_*` variables.
    *   Container entrypoint scripts (`entrypoint.sh`) should use `#!/bin/bash` for compatibility and avoid shell-specific syntax.
*   **Environment Configuration:**
    *   Use environment variables for all secrets and configurations.
    *   The backend is configured to ignore `.env` files when a `RAILWAY_ENVIRONMENT` variable is present to prevent local settings from overriding production ones.
*   **CI/CD:**
    *   Use `per-file-ignores` in `pyproject.toml` to manage legitimate linting exceptions without disabling rules globally.
    *   Automated security scans should generate reports but not necessarily fail the pipeline, allowing for gradual remediation.

## 5. Agentic System (CrewAI)

*   **Agent-First Principle:** **All** intelligence and business logic must come from CrewAI agents. Do not implement hardcoded rules, static logic, or pseudo-agents.
*   **Use Existing Patterns:** The platform has an established 7-agent specialist model. Enhance these existing agents and crews rather than creating new ones.
*   **Agent-UI-Bridge:** Use the `agent-ui-bridge` system as the primary mechanism for agents to communicate with the frontend, request user clarification (via the `AgentClarificationPanel`), and store insights.
*   **Data for Agents:** Agents require operational data from **child flows**, not lifecycle data from master flows, to make accurate decisions.
*   **Dynamic Thresholds:** Agents, not hardcoded values, should determine critical thresholds (e.g., field mapping approval percentages) based on data quality, complexity, and other contextual factors.

## 6. Security

*   **Authentication:**
    *   **NEVER** implement an authentication bypass, even for demo modes. All users must be validated against a proper password hash.
    *   Use `bcrypt` for password hashing, not insecure algorithms like SHA256.
*   **Credentials:**
    *   **NEVER** hardcode credentials in any file (`.py`, `.yml`, `.env`). Use environment variables exclusively.
    *   **NEVER** expose credentials or sensitive user information in API responses.
*   **Multi-Tenancy:**
    *   This is an enterprise platform. **ALL** data access **MUST** be scoped by `client_account_id` and `engagement_id`.
    *   Use the `ContextAwareRepository` pattern for all database repositories.
    *   Every tenant-scoped API call must include `X-Client-Account-ID` and `X-Engagement-ID` headers. Use the `getAuthHeaders()` utility on the frontend.
*   **CORS:** Do not use wildcard origins. Explicitly list all allowed domains.

## 7. Debugging & Troubleshooting

*   **Check the Database First:** Many UI issues that appear as "missing data" are rooted in the backend failing to retrieve data due to incorrect multi-tenant headers, faulty foreign key relationships, or transaction timing issues.
*   **Trace the Data Flow:** Verify each step in a data chain (e.g., Flow -> Import -> Mappings). Use browser developer tools to inspect API calls and responses.
*   **API Response Mismatches:** A common source of bugs is a mismatch between the field names the backend sends (e.g., `master_flow_id`) and what the frontend expects (e.g., `flowId`). Always verify the API contract.
*   **Look for Insights in Multiple Places:** Agent insights can be stored in `flow_persistence_data`, `agent_collaboration_log`, or the `agent-ui-bridge` files. If one source is empty, check the others.
*   **Use the Provided Scripts:** The repository contains numerous validation and cleanup scripts (e.g., `cleanup_orphaned_flows_simple.py`). Use them to diagnose and fix data integrity issues.
