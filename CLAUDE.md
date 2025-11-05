# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start Commands

### Running the Application (Docker Only)
```bash
# Start all services (frontend on :8081, backend on :8000, DB on :5433)
cd config/docker && docker-compose up -d

# View logs
docker logs migration_backend -f
docker logs migration_frontend -f

# Access containers
docker exec -it migration_backend bash
docker exec -it migration_postgres psql -U postgres -d migration_db
```

### Testing Commands
```bash
# Frontend tests
npm run test:e2e:journey  # Full user journey test
npm run test:admin        # Admin interface tests

# Backend tests (run from backend dir)
cd backend && python -m pytest tests/backend/integration/ -v

# Linting & Type Checking
npm run lint              # Frontend linting
npm run typecheck         # TypeScript checking
cd backend && ruff check . --fix  # Python linting
cd backend && mypy app/   # Python type checking

# Pre-commit (backend)
cd backend && pre-commit run --all-files
```

### Database Commands
```bash
# Run migrations
cd backend && alembic upgrade head

# Create new migration
cd backend && alembic revision --autogenerate -m "Description"

# Check database
docker exec -it migration_postgres psql -U postgres -d migration_db -c "SELECT * FROM migration.discovery_flows;"
```

### Bug Fix Workflow Commands
```bash
# Automated bug fixing with multi-agent orchestration
/fix-bugs execute          # Fix all open bugs (up to 10)
/fix-bugs execute 588      # Fix specific bug
/fix-bugs dry-run          # Analyze bugs without fixing

# Check issues with pending fixes
gh issue list --label fixed-pending-review --state open

# See full workflow documentation
# /docs/guidelines/AUTOMATED_BUG_FIX_WORKFLOW.md
```

## High-Level Architecture

### System Overview
- **Frontend**: Next.js/React with TanStack Query on port 8081 (NOT 3000)
- **Backend**: FastAPI with async SQLAlchemy on port 8000
- **Database**: PostgreSQL 16 with pgvector extension
- **AI**: 17 CrewAI agents (13 active) with DeepInfra/OpenAI integration
- **Deployment**: Railway (WebSocket-free, HTTP polling only)

### Seven-Layer Enterprise Architecture
```
1. API Layer (FastAPI routes) - Request handling and validation
2. Service Layer (business logic) - Orchestration and workflow
3. Repository Layer (data access) - Database abstraction
4. Model Layer (SQLAlchemy/Pydantic) - Data structures
5. Cache Layer (Redis/in-memory) - Performance optimization
6. Queue Layer (async processing) - Background tasks
7. Integration Layer (external services) - Third-party APIs
```
This is NOT over-engineering - it's REQUIRED for enterprise resilience

### Critical Architecture Patterns

#### Master Flow Orchestrator (MFO) Pattern
The MFO is the single source of truth for all workflow operations:
- **Entry Point**: `/api/v1/master-flows/*` endpoints ONLY
- **Two-Table Architecture**:
  - `crewai_flow_state_extensions`: Master flow lifecycle (running/paused/completed)
  - `discovery_flows`: Child flow operational data (phases, UI state)
- **Never** call legacy `/api/v1/discovery/*` endpoints directly

#### State Management Flow
```
User Action → Frontend → MFO API → Master Flow → Child Flow → CrewAI Agent
                                        ↓            ↓
                                   State Table   UI Display
```

#### Multi-Tenant Data Scoping
Every query MUST include:
- `client_account_id`: Organization isolation
- `engagement_id`: Project/session isolation
- All tables use composite scoping for data security

#### LLM Usage Tracking (MANDATORY - October 2025)
**ALL LLM calls MUST use `multi_model_service.generate_response()`** for automatic tracking:

```python
from app.services.multi_model_service import multi_model_service, TaskComplexity

# ✅ CORRECT - Automatic tracking to llm_usage_logs table
response = await multi_model_service.generate_response(
    prompt="Your prompt here",
    task_type="chat",  # or "field_mapping", "analysis", etc.
    complexity=TaskComplexity.SIMPLE  # or AGENTIC for complex tasks
)
```

**Benefits of using `multi_model_service`:**
- ✅ Automatic logging to `llm_usage_logs` table with cost calculation
- ✅ Correct model selection (Gemma 3 for chat, Llama 4 for agentic)
- ✅ Token counting and request/response tracking
- ✅ Multi-tenant context (client_account_id, engagement_id)
- ✅ Performance metrics (response time, success rate)

**NEVER use direct LLM calls** - they bypass tracking:
- ❌ `litellm.completion()` - Use `multi_model_service` instead
- ❌ `openai.chat.completions.create()` - Use `multi_model_service` instead
- ❌ `LLM().call()` - Use `multi_model_service` instead

**Legacy Code Exception:** If you find direct calls in existing code, wrap with tracker:
```python
from app.services.llm_usage_tracker import llm_tracker

async with llm_tracker.track_llm_call(
    provider="deepinfra",
    model=model_name,
    feature_context="crew_execution"
) as usage_log:
    response = litellm.completion(model=model, messages=messages)
    usage_log.input_tokens = response.usage.prompt_tokens
    usage_log.output_tokens = response.usage.completion_tokens
```

**Viewing LLM Costs:** Navigate to `/finops/llm-costs` in the frontend to see:
- Real-time usage by model (e.g., "Deepinfra: gemma-3-4b-it")
- Token consumption and cost breakdown
- Usage trends and optimization recommendations

**Database Tables:**
- `migration.llm_usage_logs` - Individual LLM API calls
- `migration.llm_model_pricing` - Cost per 1K tokens by model
- `migration.llm_usage_summary` - Aggregated usage statistics

**Automatic Tracking via LiteLLM Callback:**
- All LLM calls (including CrewAI) automatically tracked via LiteLLM callback
- Installed at app startup in `app/app_setup/lifecycle.py:116`
- Logs to `llm_usage_logs` even for legacy code using direct LiteLLM calls
- Tracks: Llama 4 (CrewAI), Gemma 3 (OpenAI), and all LLM providers

**Reference:**
- `app/services/multi_model_service.py:169-577` - Multi-model service
- `app/services/litellm_tracking_callback.py` - LiteLLM callback for CrewAI tracking
- `app/app_setup/lifecycle.py:113-120` - Callback installation at startup

#### TenantMemoryManager - Enterprise Agent Memory (October 2025)
**CrewAI built-in memory is DISABLED** (ADR-024). All agent learning uses TenantMemoryManager:

```python
from app.services.crewai_flows.memory.tenant_memory_manager import (
    TenantMemoryManager,
    LearningScope
)

# Store agent learnings after task completion
memory_manager = TenantMemoryManager(
    crewai_service=crewai_service,
    database_session=db
)

await memory_manager.store_learning(
    client_account_id=client_account_id,
    engagement_id=engagement_id,
    scope=LearningScope.ENGAGEMENT,  # or CLIENT, GLOBAL
    pattern_type="field_mapping",
    pattern_data={
        "source_field": "cust_name",
        "target_field": "customer_name",
        "confidence": 0.95
    }
)
```

**Why TenantMemoryManager over CrewAI Memory:**
- ✅ Multi-tenant isolation (engagement/client/global scopes)
- ✅ PostgreSQL + pgvector (native to our stack, no external ChromaDB)
- ✅ Enterprise features: data classification, audit trails, encryption
- ✅ DeepInfra compatibility without monkey patches
- ❌ CrewAI memory causes 401 errors (DeepInfra key → OpenAI endpoint)

**IMPORTANT:** When creating crews, **ALWAYS** set `memory=False`:
```python
from app.services.crewai_flows.config.crew_factory import create_crew

crew = create_crew(
    agents=[agent],
    tasks=[task],
    memory=False,  # ✅ REQUIRED - Use TenantMemoryManager instead
    verbose=False
)
```

**Reference:**
- ADR-024 - TenantMemoryManager architecture (supersedes ADR-019)
- `/docs/development/TENANT_MEMORY_STRATEGY.md` - Implementation strategy
- `app/services/crewai_flows/memory/tenant_memory_manager.py` - Implementation

### CrewAI Agent Architecture

#### Agent Types & Responsibilities
- **Discovery Agents** (4): Data analysis, CMDB, dependencies
- **Assessment Agents** (2): Migration strategy, risk assessment
- **Planning Agents** (1): Wave planning coordination
- **Learning Agents** (3): Pattern recognition, context management
- **Observability Agents** (3): Health monitoring, performance

#### Agent Communication Pattern
```
TenantScopedAgentPool → Agent Instance → Tools → Database
                          ↓
                    Agent UI Bridge → Frontend Display
```

#### CrewAI Memory Configuration (CRITICAL - ADR-024)

**RULE**: CrewAI memory is **DISABLED** by default. Use `TenantMemoryManager` for all agent learning.

**Why Memory is Disabled**:
- ADR-024 (October 2025) replaced CrewAI's ChromaDB-based memory with enterprise `TenantMemoryManager`
- Eliminates 401/422 errors from DeepInfra/OpenAI embedding conflicts
- Provides multi-tenant isolation (client_account_id, engagement_id scoping)
- Uses native PostgreSQL + pgvector (already in stack)
- Better performance and enterprise data classification

**Configuration Defaults**:
```python
# From crew_factory/config.py (lines 100, 147)
CrewConfig.DEFAULT_AGENT_CONFIG["memory"] = False
CrewConfig.DEFAULT_CREW_CONFIG["memory"] = False
```

**NEVER Override These Defaults**:
- ❌ **DO NOT** set `memory=True` in agent or crew creation
- ❌ **DO NOT** enable memory in `agent_pool_constants.py`
- ❌ **DO NOT** apply memory patches at startup (violates ADR-024)

**If You See `memory=True` in Code**:
1. This is legacy code from pre-October 2025
2. Change to `memory=False` with comment: `# Per ADR-024: Use TenantMemoryManager`
3. If agent needs learning, integrate `TenantMemoryManager.store_learning()`

**Using TenantMemoryManager for Agent Learning**:
```python
from app.services.crewai_flows.memory.tenant_memory_manager import (
    TenantMemoryManager,
    LearningScope
)

# After agent completes task
memory_manager = TenantMemoryManager(
    crewai_service=crewai_service,
    database_session=db
)

await memory_manager.store_learning(
    client_account_id=client_account_id,
    engagement_id=engagement_id,
    scope=LearningScope.ENGAGEMENT,
    pattern_type="field_mapping",
    pattern_data={
        "source_field": "cust_name",
        "target_field": "customer_name",
        "confidence": 0.95
    }
)

# Before agent execution - retrieve patterns
patterns = await memory_manager.retrieve_similar_patterns(
    client_account_id=client_account_id,
    engagement_id=engagement_id,
    scope=LearningScope.ENGAGEMENT,
    pattern_type="field_mapping",
    query_context={"source_field": "customer"}
)
```

**Common Mistakes to Avoid**:
1. ❌ Re-enabling memory patches at startup (violates explicit configuration principle)
2. ❌ Using `EmbedderConfig` to configure CrewAI memory (superseded by TenantMemoryManager)
3. ❌ Setting `memory_enabled: True` in agent pool constants
4. ❌ Proposing to "fix" CrewAI memory instead of using TenantMemoryManager

**If You See Memory Errors in Production**:
- **Root Cause**: Legacy `memory=True` settings not yet migrated
- **Fix**: Change to `memory=False` + integrate TenantMemoryManager
- **Do NOT**: Re-enable global memory patches or embedder configuration

**References**:
- `/docs/adr/024-tenant-memory-manager-architecture.md` - Full architectural decision
- `/docs/development/TENANT_MEMORY_STRATEGY.md` - Implementation strategy
- `backend/app/services/crewai_flows/memory/tenant_memory_manager/` - Implementation

### Assessment Flow Architecture

**Purpose**: Cloud readiness assessment and 6R migration recommendation

**Endpoints**: `/api/v1/assessment-flow/*` (MFO-integrated per ADR-006)

**Flow Progression**:
1. Create assessment flow → Master flow in `crewai_flow_state_extensions`
2. Child flow in `assessment_flows` tracks operational state
3. Phases: Architecture Standards → Tech Debt → 6R Decisions
4. Accept recommendations → Update `Asset.six_r_strategy`
5. Export results → PDF/Excel/JSON

**Two-Table Pattern** (ADR-012):
- **Master Table**: `crewai_flow_state_extensions` (lifecycle: running/paused/completed)
- **Child Table**: `assessment_flows` (operational: phases, UI state, selected applications)

**Key Files**:
- Backend: `backend/app/api/v1/endpoints/assessment_flow/`
- Frontend: `src/lib/api/assessmentFlow.ts`
- MFO Integration: `backend/app/api/v1/endpoints/assessment_flow/mfo_integration.py`

**Deprecated**: `/api/v1/6r/*` endpoints (HTTP 410 Gone - use Assessment Flow instead)

**Migration Context**:
- 6R Analysis implementation was removed (Oct 2025) to eliminate duplicate code paths
- Assessment Flow is the single source of truth for 6R recommendations
- Strategy crew integrated with Assessment Flow via MFO architecture

## Subagent Instructions and Requirements

### AUTOMATIC ENFORCEMENT FOR ALL SUBAGENTS (Including Autonomous)

#### Two-Layer Enforcement System:

1. **Manual Invocations (User-Initiated)**:
   When YOU explicitly invoke a subagent, you must include the instruction text below.

2. **Autonomous Invocations (Claude/Opus-Initiated)**:
   When Claude autonomously orchestrates subagents, the system automatically:
   - Reads configuration from `/.claude/agent_config.json`
   - Prepends mandatory instructions to ALL agent prompts
   - Appends summary requirements
   - Enforces banned pattern checks
   - Logs compliance in `/.claude/agent_audit.log`

#### Configuration Files That Enable This:
- `/.claude/agent_config.json` - Defines what gets auto-injected
- `/.claude/settings.local.json` - Enables auto-injection globally
- `/.claude/agent_instructions.md` - Full requirements and templates
- `/.claude/AGENT_DEFAULTS.md` - System documentation

#### For Multi-Agent Orchestration:
The system automatically:
- Passes instructions down the agent chain
- Aggregates summaries from child agents
- Maintains context through the hierarchy
- Limits recursion depth to prevent loops

### MANDATORY FOR ALL CLAUDE CODE SUBAGENTS
When invoking ANY subagent (qa-playwright-tester, python-crewai-fastapi-expert, sre-precommit-enforcer, etc.), ensure they:

1. **Read Required Documentation First**:
   - `/docs/analysis/Notes/000-lessons.md` - Core architectural lessons
   - `/docs/analysis/Notes/coding-agent-guide.md` - Implementation patterns
   - `/.claude/agent_instructions.md` - Detailed subagent requirements

2. **Provide Comprehensive Summary**:
   - Not just "Done" but a detailed summary of work performed
   - Include files modified, patterns applied, and verification steps
   - Follow the summary template in `/.claude/agent_instructions.md`

3. **Include This in Every Manual Subagent Prompt**:
   ```
   IMPORTANT: First read these files:
   1. /docs/analysis/Notes/coding-agent-guide.md
   2. /.claude/agent_instructions.md

   After completing your task, provide a detailed summary following the template in agent_instructions.md, not just "Done".
   Include: what was requested, what was accomplished, technical details, and verification steps.
   ```

## Development Best Practices

### CRITICAL: Bug Investigation Workflow (MUST READ - Prevents False Fixes)

**⚠️ MANDATORY PROCESS FOR ALL BUG INVESTIGATIONS - LEARNED FROM ISSUE #795**

Before assuming something is a bug and implementing a fix, **ALWAYS** follow this sequence:

#### 1. Check Serena Memories FIRST
```bash
# Search for relevant architectural context
mcp__serena__list_memories  # List all available memories
mcp__serena__read_memory <memory_name>  # Read relevant memories
```

**Why**: Many "bugs" are actually **working as designed**. Serena memories document:
- Architectural intent and design decisions
- Intelligent behavior patterns (e.g., adaptive questionnaires, gap-based filtering)
- Why certain code appears to do "less" but is actually doing "more intelligently"

#### 2. Understand Architectural Intent
Ask yourself:
- **Is this behavior intentional?** (e.g., fewer questions = better data quality, not a bug)
- **What problem does this design solve?** (e.g., intelligent gap-based question generation)
- **Does showing "less" actually mean "smarter"?** (e.g., adaptive forms showing only data gaps)

#### 3. Reproduce with Playwright FIRST
**NEVER** ask users for manual testing - use qa-playwright-tester agent:
```typescript
Task tool with subagent_type: "qa-playwright-tester"
// Reproduce the exact scenario
// Capture screenshots, console logs, network traces
// Verify actual vs expected behavior
```

#### 4. Analyze Backend Logic
Check the backend code that generates the data:
- Gap analysis services
- Intelligent filtering logic
- Agent-based decision making
- Database queries with proper scoping

#### 5. Present Analysis BEFORE Implementing
**MANDATORY**: Before writing ANY fix:
1. Document what you found (root cause analysis)
2. Explain whether it's a bug or working as designed
3. If it's a bug, propose the fix approach
4. **Wait for user approval** before implementing

#### Example: Issue #795 (Adaptive Forms)
**Reported**: "Asset 2 shows only 3 sections instead of 7 - BUG!"

**Investigation Revealed**:
- ✅ Serena memory: "questions should be generated based on gaps"
- ✅ Asset 2 has better data quality → fewer gaps → fewer questions
- ✅ Playwright testing: System working correctly
- ✅ Backend: Gap analysis correctly identifying missing fields only
- ❌ **NOT A BUG** - Intelligent adaptive behavior

**What Went Wrong**:
- Assumed fewer sections = bug without checking intent
- Implemented "fix" that broke intelligent filtering
- Made system ask unnecessary questions for complete data

**Correct Action**: Close as "Working as Designed"

#### Red Flags That Suggest "Not a Bug"
- 🚩 "Fewer items displayed" in an **adaptive/intelligent** system
- 🚩 "Different behavior per asset/user" in a **personalized** system
- 🚩 "Empty sections hidden" in a **smart UI** that shows only relevant content
- 🚩 "Questions vary by data quality" in a **gap-based** collection system

**When in doubt: CHECK SERENA MEMORIES FIRST, REPRODUCE WITH PLAYWRIGHT, PRESENT ANALYSIS**

### CRITICAL: API Request Body vs Query Parameters (MUST READ - Prevents 422 Errors)

**⚠️ THIS IS THE #1 RECURRING BUG - FIXED MULTIPLE TIMES**

#### The Rule
- **POST/PUT/DELETE**: ALWAYS use request body, NEVER query parameters
- **GET**: Use query parameters
- **See**: `/docs/guidelines/API_REQUEST_PATTERNS.md` for full details

#### Quick Reference
```typescript
// ❌ WRONG - Causes 422 errors
await apiCall(`/api/endpoint?param=value`, { method: 'POST' })

// ✅ CORRECT
await apiCall(`/api/endpoint`, {
  method: 'POST',
  body: JSON.stringify({ param: 'value' })
})
```

**Backend uses FastAPI with Pydantic models that ONLY accept request bodies for POST/PUT/DELETE**

### CRITICAL: API Field Naming Convention (MUST READ - Prevents Recurring Bugs)

#### The Problem
The #1 recurring bug in this codebase WAS confusion between snake_case and camelCase field names. This has been resolved.

#### The Rule - NEVER BREAK THIS (Updated Aug 2025)
1. **Backend (Python/FastAPI)**: ALWAYS returns `snake_case` fields (e.g., `flow_id`, `client_account_id`)
2. **Frontend (TypeScript/React)**: SHOULD use `snake_case` fields to match backend for all NEW code
   - **IMPORTANT**: Legacy code may still use `camelCase`. When touching those areas, refactor to `snake_case` in the same PR
   - **MIGRATION IN PROGRESS**: Some components may have mixed usage during transition
3. **Raw API Calls**: Will receive `snake_case` and should use it directly - NO TRANSFORMATION NEEDED
4. **Type Definitions**: Frontend interfaces should use `snake_case` ONLY for new/updated types to match backend

#### Migration Notes and Warnings
- **Legacy Utilities**: `api-field-transformer.ts` is now a NO-OP but retained for backward compatibility
- **Incremental Migration**: When updating a component, convert ALL its field references to snake_case
- **Type Safety**: Use explicit null/undefined checks instead of truthy checks for numeric fields (e.g., confidence_score)
- **DO NOT**: Mix camelCase and snake_case in the same component or type definition
- **DO**: Complete field name migration within the scope of your PR when touching a file

#### For AI Agents - MANDATORY CHECKS
Before writing ANY code that handles API responses:
1. Always use `snake_case` for all field names (e.g., `flow_id`, NOT `flowId`)
2. Do NOT transform field names - use them exactly as received from the API
3. NEVER create interfaces with camelCase field names
4. If you see camelCase fields in existing code, they should be updated to snake_case

### Git History and Code Modification Guidelines
- When solving an issue, always thoroughly review the project's Git history to understand past changes related to the code you intend to impact
- Ensure you comprehensively understand existing codebase support for the area you're modifying
- Validate that your proposed approach remains consistent with past implementation patterns
- Prioritize modifying existing code over adding new code to prevent unnecessary code sprawl
- Before introducing new implementations, carefully assess if existing code can be refactored or extended to meet the current requirements
- Never bypass pre-commit checks with --no-verify unless you have gone through the pre-commit checks at least once and fixed all the issues mentioned by the checks

### Development Environment Configuration
- Use /opt/homebrew/bin/gh for all Git CLI tools and /opt/homebrew/bin/python3.11@ for all Python executions in the app
- Never attempt to run npm run dev locally as ALL app related testing needs to be done on docker instances locally. The app runs on localhost:8081 NOT on port 3000

## Architectural Review Guidelines for AI Agents

### Critical: Before Claiming Something Doesn't Exist
1. Use multiple search approaches (find_symbol, search_for_pattern, Glob patterns)
2. Check actual file paths with ls/Glob commands
3. Read the imports in related files to find actual usage
4. Example: TenantScopedAgentPool EXISTS at backend/app/services/persistent_agents/tenant_scoped_agent_pool.py

### Understanding State Management Architecture
1. **Pydantic models (BaseModel)** = runtime state objects for validation/serialization
2. **SQLAlchemy models (Base)** = database table definitions
3. **Two-table pattern is INTENTIONAL** - Master (crewai_flow_state_extensions) + Child (discovery_flows)
4. See docs/analysis/Notes/000-lessons.md for architectural decisions

### Evaluating Existing Patterns - DO NOT DISMISS AS "OVER-ENGINEERING"
1. **Read ADRs first** before suggesting any architectural changes
2. **Modular handlers provide enterprise resilience** - they are features, not complexity
3. **Fallback patterns are intentional** for graceful degradation
4. **Memory patches are adaptations** (e.g., DeepInfra embeddings), not failures
5. **7+ layer architecture is REQUIRED** for multi-tenant isolation, atomic transactions, and audit trails

### Making Architectural Recommendations
1. **Enhance existing implementations** rather than proposing replacements
2. **Respect multi-tenant isolation** - all data scoped by client_account_id and engagement_id
3. **Preserve atomic transaction boundaries** for data integrity
4. **Keep graceful degradation paths** - placeholders are resilience features
5. **Use feature flags** for gradual improvements rather than wholesale replacements

### Common Mistakes to Avoid
- ❌ "Persistent agents don't exist" - They DO exist and are actively used
- ❌ "Memory is disabled globally" - Memory is ENABLED with DeepInfra patch
- ❌ "Too many state tables" - UnifiedDiscoveryFlowState is a Pydantic model, not a table
- ❌ "Reduce layers for simplicity" - Enterprise systems REQUIRE these layers
- ❌ "Remove placeholder implementations" - They provide critical fallback resilience

### Required Reading Before Reviews
- docs/adr/*.md - All Architectural Decision Records
- docs/analysis/Notes/000-lessons.md - Critical lessons learned
- docs/guidelines/ARCHITECTURAL_REVIEW_GUIDELINES.md - Detailed review guidelines

## Key Architectural Decision Records (ADRs)

### ADR-006: Master Flow Orchestrator
- Single source of truth for ALL workflow operations
- All flows MUST register with `crewai_flow_state_extensions` table
- Centralizes flow management, state persistence, and multi-tenancy
- "Rip and replace" strategy over phased migration

### ADR-010: Docker-First Development Mandate
- ALL development MUST occur within Docker containers
- NO local services (Python, Node.js, PostgreSQL) on dev machines
- Use `docker exec` for all command execution
- Docker Compose for multi-service orchestration

### ADR-012: Flow Status Management Separation
- **Master Flow**: High-level lifecycle (`running`, `paused`, `completed`)
- **Child Flow**: Operational decisions (phases, validations, UI state)
- Frontend and agents MUST use child flow status for decisions
- Master flow only for cross-flow coordination

### ADR-015: Persistent Multi-Tenant Agent Architecture
- TenantScopedAgentPool manages agent lifecycle per tenant
- Agents maintain memory with DeepInfra embeddings patch
- Singleton pattern with lazy initialization per tenant

### ADR-019: CrewAI DeepInfra Embeddings Monkey Patch
- Memory IS enabled via DeepInfra patch
- Located at `backend/app/core/memory/crewai_deepinfra_patch.py`
- Applied at startup to enable agent memory persistence

## Critical: API Endpoint Synchronization (Post-Aug 2025 Incident)

### MANDATORY: Backend-Frontend Changes MUST Be Done Together
When modifying API endpoints, **ALWAYS**:
1. Search frontend for endpoint usage: `grep -r "/api/path" src/`
2. Update BOTH backend router AND frontend services in same commit
3. Test with Docker + check browser console for 404s

### Current Endpoint Patterns (Don't Assume - Verify in router_registry.py)
- MFO: `/api/v1/master-flows/*` (NOT `/flows/*`)
- Flow Processing: `/api/v1/flow-processing/*`
- Discovery: `/api/v1/unified-discovery/*`
- Collection: `/api/v1/collection/*`
- Assessment: `/api/v1/assessment-flow/*` (NOT `/6r/*` - deprecated)

### Files That MUST Be Updated Together
- Backend: `router_registry.py`, `router_imports.py`, endpoint files
- Frontend: `masterFlowService.ts`, `discoveryService.ts`, `collectionService.ts`, `assessmentFlowApi.ts`

### Never Do This
- ❌ Change backend without frontend
- ❌ Use fallbacks to hide broken endpoints
- ❌ Skip browser console check for 404s

## Database Best Practices

### Schema & Migrations
- All tables in `migration` schema, NOT `public`
- Use CHECK constraints, not PostgreSQL ENUMs
- Make migrations idempotent with existence checks
- Foreign keys reference primary keys only (id column)

### CRITICAL: Alembic Migration Conventions

**ALL migrations MUST:**
1. Use 3-digit prefix: `092_description.py` (NOT `228e0eae6242_description.py`)
2. Be idempotent: Use `IF EXISTS`/`IF NOT EXISTS` in PostgreSQL DO blocks
3. Chain properly: `down_revision = "091_previous_migration"`
4. Use `migration.` schema prefix for all table references

Find next number: `ls -1 backend/alembic/versions/ | grep "^[0-9]" | tail -1`
Reference: `backend/alembic/versions/092_add_supported_versions_requirement_details.py`

### SQLAlchemy Patterns
```python
# Correct boolean comparison
.filter(DiscoveryFlow.is_active == True)  # NOT is True

# UUID handling
flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id

# Async session pattern
async with AsyncSession(engine) as session:
    async with session.begin():
        # Atomic transaction
```

### Common Queries
```sql
-- Check flow state
SELECT flow_id, current_phase, status
FROM migration.discovery_flows
WHERE flow_id = 'uuid-here';

-- Master flow status
SELECT flow_id, status, current_phase
FROM migration.crewai_flow_state_extensions
WHERE client_account_id = 1 AND engagement_id = 1;
```

## Frontend Patterns

### React Query Configuration
```typescript
// Polling strategy for Railway (no WebSockets)
{
  refetchInterval: status === 'running' ? 5000 : 15000,
  enabled: !!flowId && flowId !== 'XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX'
}
```

### Field Name Handling
```typescript
// Always use snake_case from API
const flowId = data.master_flow_id || data.flow_id; // Fallback pattern
```

### Component Reuse
- Use `ThreeColumnFieldMapper` for mapping interfaces
- Filter client-side rather than creating new endpoints
- Display real agent insights from agent-ui-bridge

## Modularization Patterns

### When Modularizing Large Files (>400 lines)
```
original_file.py → original_file/
                    ├── __init__.py (preserve public API)
                    ├── base.py (base classes)
                    ├── commands.py (write operations)
                    ├── queries.py (read operations)
                    └── utils.py (helper functions)
```

### Preserve Backward Compatibility
```python
# In __init__.py - maintain all public imports
from .base import BaseClass
from .commands import create_flow, update_flow
from .queries import get_flow, list_flows

__all__ = ['BaseClass', 'create_flow', 'update_flow', 'get_flow', 'list_flows']
```

### Import Strategy
- Use absolute imports within packages
- Avoid circular dependencies
- Group imports: stdlib → third-party → local

## Code Review Checklist

Before submitting PRs:
- [ ] Run pre-commit checks at least once
- [ ] Test in Docker environment (localhost:8081)
- [ ] Check browser console for API errors
- [ ] Verify snake_case field naming
- [ ] Update both backend and frontend for API changes
- [ ] Check existing code before adding new implementations
- [ ] Ensure multi-tenant scoping in all queries
- [ ] Preserve atomic transaction boundaries

Never start with adding new code to fix any issue however critical it may be. Always check existing code or Git history for such functionality and see if it can be adjusted to meet our needs, and only if none such exists then you'll create new code.
