# Lessons Learned for AI Coding Agents

This document consolidates key learnings from troubleshooting and development sessions on the AI Force Migration Platform. Adhering to these principles will help future AI agents avoid common pitfalls, align with the existing architecture, and contribute effectively.

## TL;DR - Critical Rules (Read First)
*   **Master Flow Orchestrator (MFO) ONLY** - Never call legacy `/api/v1/discovery/*` endpoints
*   **child_flow_service Required** - All flows use this pattern (NOT crew_class which is deprecated)
*   **Tenant Scoping Mandatory** - Every query needs `client_account_id` + `engagement_id`
*   **LLM Usage Tracking** - ALL calls via `multi_model_service.generate_response()` only
*   **UUID PK vs flow_id** - Use `{table}.id` (PK) for FKs/data, `flow_id` only for MFO calls
*   **JSON Serialization Safety** - Handle NaN/Infinity before JSON responses (Python → JS boundary)

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
*   **Child Flow Service Pattern (ADR-025 - October 2025):**
    *   The **child_flow_service pattern** is the REQUIRED execution mechanism for all flows (Discovery, Collection, Assessment).
    *   **NEVER** use `crew_class` - this is deprecated and causes import failures. MFO executes via `child_flow_service` ONLY. Any remaining `crew_class` entries in configs are legacy and must not be used in new code.
    *   Each flow type has a `{Flow}ChildFlowService` (e.g., `DiscoveryChildFlowService`, `CollectionChildFlowService`) that:
        *   Routes phase execution to appropriate handlers (gap analysis, questionnaires, validation, etc.)
        *   Uses persistent agents via `TenantScopedAgentPool` (never instantiates new crews)
        *   Manages auto-progression logic between phases based on results
        *   Maintains tenant scoping through `RequestContext` and `ContextAwareRepository`
    *   **Pattern**: `flow_config.child_flow_service = CollectionChildFlowService` (NOT `crew_class`)
    *   **MFO Integration**: Master Flow Orchestrator calls `child_service.execute_phase(flow_id, phase_name, phase_input)` for all flow operations
    *   **Reference**: `backend/app/services/child_flow_services/`, ADR-025

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
*   **UUID Primary Key vs flow_id Distinction (ADR-025):**
    *   **CRITICAL**: Many tables have BOTH `id` (UUID PK) and `flow_id` (UUID for MFO orchestration).
    *   **Examples**:
        *   `collection_flows.id` = UUID Primary Key → Use for ALL foreign keys, data persistence, background jobs
        *   `collection_flows.flow_id` = UUID → Use ONLY for Master Flow Orchestrator API calls (`execute_phase`, `resume_flow`)
        *   `discovery_flows.id` = UUID Primary Key → Use for data relationships (imports, mappings, gaps)
        *   `discovery_flows.flow_id` = UUID → Use for MFO operations only
    *   **Rule**: When referencing flow data (gaps, questionnaires, analysis, child records), use `{table}.id` (the PK), NOT `flow_id`.
    *   **Verify Schema**: Always check `\d migration.{table_name}` in PostgreSQL before assuming ID types and relationships.
*   **JSON Serialization Safety:**
    *   **CRITICAL**: Python's `float('nan')` and `float('inf')` are NOT valid JSON values and will cause serialization errors at the Python → JavaScript boundary.
    *   **Before returning API responses**: Check for and replace NaN/Infinity with `null` or appropriate sentinel values.
    *   **Pattern**:
        ```python
        import math
        def safe_serialize(value):
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                return None  # or 0, or custom sentinel
            return value
        ```
    *   **Common Source**: AI model confidence scores, statistical calculations, division by zero in analytics.

## 3. Frontend & UI/UX

*   **React Best Practices:**
    *   **Adhere strictly to the Rules of Hooks.** Never call hooks inside conditions, loops, or `try/catch` blocks.
    *   **Variable Definition Order Matters.** Avoid temporal dead zones by defining variables and state before they are referenced in hooks or JSX.
    *   Provide a unique `key` prop when rendering lists. Use a stable identifier from the data (like `flow.flow_id`) and provide a fallback (`flow-${index}`) only as a last resort.
*   **API Interaction & State Management (React Query/TanStack Query):**
    *   **HTTP Polling Strategy:** Use HTTP polling for Vercel/Railway (WebSocket-free). Active: 5s intervals, Waiting: 15s intervals, Stop when complete/failed.
    *   **Field Name Priority:** Always check `master_flow_id` first from backend, then fallback to `flowId` or `flow_id`.
    *   **Demo UUID Pattern:** Use `XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX` for fallback IDs to prevent accidental deletion.
    *   **Implement robust rate-limiting strategies:**
        *   **Debouncing:** For user-triggered actions like authentication (500ms-1s).
        *   **Exponential Backoff:** For handling `429 Too Many Requests` errors (e.g., retry after 2s, 4s, 8s).
        *   **Request Deduplication:** Prevent multiple identical in-flight requests.
        *   **Caching:** Use longer `staleTime` (e.g., 5 minutes) for data that doesn't change frequently, like field mappings.
    *   **Conditionally enable queries** that depend on data from other queries using the `enabled` flag.
*   **Component Design:**
    *   **Reuse components.** The `ThreeColumnFieldMapper` is a proven pattern; use it instead of creating new complex components for similar functionality.
    *   **Filter existing data** on the client-side rather than creating new API endpoints for slightly different views of the same data.
    *   **Display Real Agent Insights:** Parse and display actual agent feedback from agent-ui-bridge instead of hard-coded analysis.
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
    *   **GitHub Actions Optimization:** For free tier, disable heavy workflows and use lightweight alternatives (90% reduction in usage).
    *   **Pre-commit Checks:** Always run pre-commit checks at least once before using `--no-verify`.
    *   Use `per-file-ignores` in `pyproject.toml` to manage legitimate linting exceptions without disabling rules globally.
    *   Automated security scans should generate reports but not necessarily fail the pipeline, allowing for gradual remediation.
    *   **Qodo Bot Reviews:** Qodo Bot reviews ALL branch changes, not just recent commits - review comprehensively.

## 5. Agentic System (CrewAI)

*   **Agent-First Principle:** **All** intelligence and business logic must come from CrewAI agents. Do not implement hardcoded rules, static logic, or pseudo-agents.
*   **Persistent Agents (ADR-015):** Use `TenantScopedAgentPool` for singleton agents per tenant. **NEVER** create new crews for each phase execution - this reduces performance by 94%.
*   **ServiceRegistry Pattern:** Use centralized tool management via ServiceRegistry for better performance. Tools should be pre-loaded at module level to avoid per-call dynamic imports.
*   **22 Critical Attributes for 6R Migration:** The system evaluates 22 critical attributes across 4 categories (Infrastructure-6, Application-8, Business Context-4, Technical Debt-4) for migration readiness.
*   **Agent-UI-Bridge:** Use the `agent-ui-bridge` system as the primary mechanism for agents to communicate with the frontend, request user clarification (via the `AgentClarificationPanel`), and store insights.
*   **Data for Agents:** Agents require operational data from **child flows**, not lifecycle data from master flows, to make accurate decisions.
*   **Dynamic Thresholds:** Agents, not hardcoded values, should determine critical thresholds (e.g., field mapping approval percentages) based on data quality, complexity, and other contextual factors.
*   **CrewAI Memory is DISABLED (ADR-024 - October 2025):**
    *   **RULE:** CrewAI's built-in memory system is **DISABLED** by default. Use `TenantMemoryManager` for all agent learning.
    *   **Why:** ADR-024 replaced CrewAI's ChromaDB-based memory with enterprise `TenantMemoryManager` to eliminate 401/422 errors, provide multi-tenant isolation, and use native PostgreSQL+pgvector.
    *   **Configuration:** `memory=False` in `CrewConfig.DEFAULT_AGENT_CONFIG` and `DEFAULT_CREW_CONFIG` (crew_factory/config.py:100, 147).
    *   **NEVER Override:** Do NOT set `memory=True` in agent/crew creation or enable in `agent_pool_constants.py`.
    *   **Legacy Code:** If you see `memory=True`, change to `memory=False` with comment: `# Per ADR-024: Use TenantMemoryManager`.
    *   **Agent Learning:** Use `TenantMemoryManager.store_learning()` after agent tasks and `retrieve_similar_patterns()` before execution.
    *   **Common Mistakes:** Do NOT re-enable memory patches at startup, use `EmbedderConfig` for CrewAI memory, or propose "fixing" CrewAI memory.
    *   **References:** `/docs/adr/024-tenant-memory-manager-architecture.md`, `/docs/development/TENANT_MEMORY_STRATEGY.md`
*   **LLM Usage Tracking (Mandatory - October 2025):**
    *   **ALL LLM calls MUST use `multi_model_service.generate_response()`** for automatic tracking to `llm_usage_logs` table with cost calculation.
    *   **NEVER use direct LLM calls** - they bypass cost tracking and budget visibility:
        *   ❌ `litellm.completion()` - Use `multi_model_service` instead
        *   ❌ `openai.chat.completions.create()` - Use `multi_model_service` instead
        *   ❌ `LLM().call()` - Use `multi_model_service` instead
    *   **Legacy Code**: If you find direct LLM calls in existing code, wrap with `llm_tracker.track_llm_call()` context manager or migrate to `multi_model_service` immediately.
    *   **Automatic Tracking**: LiteLLM callback installed at app startup (`app/app_setup/lifecycle.py:116`) automatically tracks all CrewAI calls (Llama 4, etc.) without code changes.
    *   **View Costs**: Navigate to `/finops/llm-costs` in frontend to see real-time usage by model (e.g., "Deepinfra: gemma-3-4b-it"), token consumption, and cost breakdown.
    *   **Database Tables**: `llm_usage_logs` (individual calls), `llm_model_pricing` (costs per 1K tokens), `llm_usage_summary` (aggregated stats).
    *   **Pattern**:
        ```python
        from app.services.multi_model_service import multi_model_service, TaskComplexity

        response = await multi_model_service.generate_response(
            prompt="Your prompt here",
            task_type="chat",  # or "field_mapping", "analysis", etc.
            complexity=TaskComplexity.SIMPLE  # or AGENTIC for complex tasks
        )
        ```
    *   **Reference**: `app/services/multi_model_service.py:169-577`, `app/services/litellm_tracking_callback.py`

## 6. Security

*   **Authentication:**
    *   **NEVER** implement an authentication bypass, even for demo modes. All users must be validated against a proper password hash.
    *   Use `bcrypt` for password hashing, not insecure algorithms like SHA256.
*   **Credentials:**
    *   **NEVER** hardcode credentials in any file (`.py`, `.yml`, `.env`). Use environment variables exclusively.
    *   **NEVER** expose credentials or sensitive user information in API responses.
    *   **NEVER** log API keys or sensitive data. Remove sensitive data from error logs (e.g., client_account_id, API keys).
*   **SQL Injection Prevention:**
    *   **NEVER** use f-strings in `sa.text()` calls - use `.bindparams()` for dynamic SQL parameters.
    *   Even migration files can contain SQL injection vulnerabilities - review all SQL carefully.
*   **Multi-Tenancy:**
    *   This is an enterprise platform. **ALL** data access **MUST** be scoped by `client_account_id` and `engagement_id`.
    *   Use the `ContextAwareRepository` pattern for all database repositories.
    *   Every tenant-scoped API call must include `X-Client-Account-ID` and `X-Engagement-ID` headers. Use the `getAuthHeaders()` utility on the frontend.
*   **CORS:** Do not use wildcard origins. Explicitly list all allowed domains.
*   **Dependency Management:** Regularly audit and remove unused vulnerable dependencies. Prefer actively maintained packages (e.g., PyJWT over python-jose).

## 7. Debugging & Troubleshooting

*   **Check the Database First:** Many UI issues that appear as "missing data" are rooted in the backend failing to retrieve data due to incorrect multi-tenant headers, faulty foreign key relationships, or transaction timing issues.
*   **Trace the Data Flow:** Verify each step in a data chain (e.g., Flow -> Import -> Mappings). Use browser developer tools to inspect API calls and responses.
*   **API Response Mismatches:** A common source of bugs is a mismatch between the field names the backend sends (e.g., `master_flow_id`) and what the frontend expects (e.g., `flowId`). Always verify the API contract.
*   **Event Loop Handling:** Detect running event loops and handle appropriately - never use `asyncio.run()` inside running loops.
*   **Transaction Management:** Use `await db.flush()` after creating master flow records before dependent foreign key operations.
*   **Flow Status vs Data Availability:** A flow can be marked "completed" but still lack accessible data - verify actual data availability.
*   **Look for Insights in Multiple Places:** Agent insights can be stored in `flow_persistence_data`, `agent_collaboration_log`, or the `agent-ui-bridge` files. If one source is empty, check the others.
*   **Use the Provided Scripts:** The repository contains numerous validation and cleanup scripts (e.g., `cleanup_orphaned_flows_simple.py`). Use them to diagnose and fix data integrity issues.
*   **Performance Monitoring:** Reduce polling frequency (60s for status) and increase cache times (5-10 min) to reduce backend load.

## 8. User Preferences & Development Guidelines

*   **Testing Environment:** Use Docker containers on localhost:8081 (NOT port 3000). Test with demo@demo-corp.com credentials.
*   **Git Tools:** Use `/opt/homebrew/bin/gh` for Git CLI and `/opt/homebrew/bin/python3.11` for Python executions.
*   **Code Philosophy:** 
    *   Prioritize root cause fixes over band-aid solutions.
    *   Modify existing code over adding new code to prevent sprawl.
    *   Review ALL changes in a branch for PRs, not just recent commits.
*   **Development Practices:**
    *   Never bypass pre-commit checks without running them at least once.
    *   Test issues locally before updating GitHub.
    *   Document architectural decisions in ADRs (docs/adr/*.md).
*   **Architecture Respect:**
    *   The 7+ layer architecture is REQUIRED for enterprise multi-tenant systems - not over-engineering.
    *   Placeholder implementations provide critical fallback resilience - don't remove them.
    *   Feature flags are preferred over wholesale replacements.

## 9. Data Loss Prevention (October 2025 Incident)

*   **Multi-Layered Safety for Destructive Operations:**
    *   Following Oct 7, 2025 data loss incident (37 assets, all discovery flows wiped), ALL destructive operations (cleanup scripts, bulk deletes, data migrations) MUST implement 5-layer protection:
        1. **Environment Checks**: Block production/staging automatically (`if env in ["production", "staging"]: sys.exit(1)`), require explicit "yes" confirmation for non-local environments
        2. **User Confirmation**: Require typing exact phrases ("DELETE MY DATA", "I understand the risks") - NO simple yes/no prompts
        3. **Dry-Run Mode**: Default to showing counts only (`--dry-run` flag), require explicit flag for actual execution
        4. **Automatic Backup**: Use `pg_dump` via `asyncio.create_subprocess_exec()` to create timestamped backup BEFORE any deletion
        5. **Detailed Logging**: Show record counts before/after, log all operations with emojis (✅/⚠️) for visibility
    *   **Naming Convention**: Dangerous scripts MUST use `.DANGEROUS_` prefix and `.disabled` extension (e.g., `.DANGEROUS_clean_all_demo_data.py.disabled`)
    *   **Reference Implementation**: `backend/scripts/SAFE_cleanup_demo_data.py`
    *   **Never Skip Backups**: Even in development - data recovery is expensive
*   **Data Loss Investigation Methodology:**
    *   **PostgreSQL Forensics**: Use `pg_stat_user_tables` to find deletion counts even after data is gone:
        ```sql
        SELECT relname, n_tup_del as deletes, n_live_tup as live_rows
        FROM pg_stat_user_tables WHERE schemaname = 'migration'
        ORDER BY n_tup_del DESC;
        ```
    *   **Log Analysis**: Check PostgreSQL logs for DELETE command timestamps: `docker logs migration_postgres 2>&1 | grep -i "delete from"`
    *   **Git History**: Find when cleanup scripts were created: `git log --all --oneline -- backend/scripts/clean*.py`
    *   **Automation Verification**: Check if script runs automatically in entrypoint.sh, docker-compose, or CI/CD workflows
    *   **Recovery Options**: (1) Recent pg_dump backup, (2) Re-import from source CSV/Excel files, (3) PostgreSQL WAL point-in-time recovery, (4) Reconstruct from backend logs (last resort)
    *   **Reference**: `docs/troubleshooting/DATA_LOSS_TRIAGE_REPORT.md`
