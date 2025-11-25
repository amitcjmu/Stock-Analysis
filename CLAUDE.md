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

#### ⚠️ CRITICAL: MFO Flow ID Pattern (READ THIS FIRST!)

**This is a RECURRING BUG pattern** - read before implementing ANY flow endpoints!

The MFO uses a **two-table pattern** with **TWO DIFFERENT UUIDs** per flow:
- **Master Flow ID**: Internal MFO routing (`crewai_flow_state_extensions.flow_id`)
- **Child Flow ID**: User-facing identifier (`assessment_flows.id`, `discovery_flows.id`, etc.)

**THE GOLDEN RULES**:
1. **URL paths receive CHILD flow IDs** (user-facing: `/execute/{flow_id}`)
2. **MFO methods expect MASTER flow IDs** (`orchestrator.execute_phase(master_id, ...)`)
3. **ALWAYS resolve master_flow_id from child table BEFORE calling MFO**
4. **Include child flow_id in phase_input** for persistence

**CORRECT PATTERN** (copy this verbatim):
```python
@router.post("/execute/{flow_id}")  # ← Child ID from URL
async def execute_something(flow_id: str, db: AsyncSession, context: RequestContext):
    # Step 1: Query child flow table using child ID
    stmt = select(AssessmentFlow).where(
        AssessmentFlow.id == UUID(flow_id),  # ← Child ID
        AssessmentFlow.client_account_id == context.client_account_id,
        AssessmentFlow.engagement_id == context.engagement_id,
    )
    result = await db.execute(stmt)
    child_flow = result.scalar_one_or_none()

    if not child_flow or not child_flow.master_flow_id:
        raise HTTPException(status_code=404, detail="Flow not found")

    # Step 2: Extract master flow ID
    master_flow_id = child_flow.master_flow_id  # ← FK to master flow

    # Step 3: Call MFO with MASTER ID, pass CHILD ID in phase_input
    orchestrator = MasterFlowOrchestrator(db, context)
    result = await orchestrator.execute_phase(
        str(master_flow_id),  # ← MASTER flow ID (MFO routing)
        "phase_name",
        {"flow_id": flow_id}  # ← CHILD flow ID (persistence)
    )

    return {"success": True, "flow_id": flow_id}  # Return child ID
```

**Reference**: See Serena memory `mfo_two_table_flow_id_pattern_critical` for full details.

**Example Files**:
- `backend/app/api/v1/endpoints/assessment_flow/mfo_integration/create.py`
- `backend/app/api/v1/endpoints/collection_flow/lifecycle.py`

**Common Mistakes**:
- ❌ Passing child ID to `MFO.execute_phase()` → "Flow not found" errors
- ❌ Querying `AssessmentFlow.flow_id` → AttributeError (use `.id`)
- ❌ Missing `flow_id` in `phase_input` → Phase results won't persist

#### Flow Execution Pattern Selection (CRITICAL - ADR-025)

**Two execution patterns exist** - choose based on flow characteristics:

**Child Service Pattern** (Collection, Discovery, Decommission):
- ✅ Use when: Multi-phase data collection, questionnaire generation, auto-progression
- ✅ Provides: Centralized phase routing, state abstraction, auto-progression logic
- ✅ Files: `backend/app/services/child_flow_services/{flow}_child_flow_service.py`

**Direct Flow Pattern** (Assessment):
- ✅ Use when: Analysis workflows, linear phases, simpler state management
- ✅ Provides: Direct CrewAI integration, simpler architecture
- ✅ Files: `backend/app/services/crewai_flows/unified_{flow}_flow.py`

**Decision Criteria**:
```
Does flow collect data via questionnaires?
├─ Yes → Does it have auto-progression logic?
│         ├─ Yes → Use Child Service Pattern
│         └─ No → Consider Child Service Pattern
└─ No → Is it analyzing existing data?
          ├─ Yes → Use Direct Flow Pattern (like Assessment)
          └─ No → Evaluate complexity
```

**IMPORTANT**: ADR-025 applies to Collection Flow only. Assessment Flow correctly uses Direct Flow Pattern.

**See**: `docs/adr/025-collection-flow-child-service-migration.md` section "When to Use Child Service Pattern"

#### Master Flow Orchestrator (MFO) Pattern
The MFO is the single source of truth for all workflow operations:
- **Entry Point**: `/api/v1/master-flows/*` endpoints ONLY
- **Two-Table Architecture** (see critical pattern above):
  - `crewai_flow_state_extensions`: Master flow lifecycle (running/paused/completed)
  - `assessment_flows` / `discovery_flows` / `collection_flows`: Child flow operational data
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

#### LLM Usage Tracking (Updated November 2025)
**When writing code that calls LLMs** (CrewAI agents, direct completions, embeddings):
- Use `multi_model_service.generate_response()` for new code - provides automatic cost tracking, tenant context, and correct model selection (Gemma 3 for chat, Llama 4 for agentic)
- Legacy `litellm.completion()` calls are auto-tracked via global callback - no changes needed
- All usage logged to `migration.llm_usage_logs` with costs viewable at `/finops/llm-costs`

**See Observability section below** for full patterns, code examples, and pre-commit enforcement rules.

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

### Assessment Flow Architecture

**Purpose**: Cloud readiness assessment and 6R migration recommendation

**Endpoints**: `/api/v1/assessment-flow/*` (MFO-integrated per ADR-006)

**Execution Pattern**: Direct Flow (NOT Child Service) - Assessment analyzes existing data with linear phases; see ADR-025 for pattern selection criteria.

**Flow Progression**: Create → Architecture Standards → Tech Debt → Dependency Analysis → 6R Decisions → Accept → Export

**Key Files**:
- Backend: `backend/app/api/v1/endpoints/assessment_flow/`
- CrewAI Flow: `backend/app/services/crewai_flows/unified_assessment_flow.py`

**Deprecated**: `/api/v1/6r/*` endpoints (HTTP 410 Gone - use Assessment Flow instead)

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

#### Example - Issue #795 Lesson
**Reported**: "Asset 2 shows only 3 sections instead of 7 - BUG!"
**Reality**: Serena memory documented gap-based generation; Asset 2 had better data → fewer gaps → fewer questions. **NOT A BUG** - intelligent adaptive behavior.
**Wrong action**: "Fixing" it to always show 7 sections would break intelligent filtering.

#### Red Flags suggesting "Not a Bug"
- "Fewer items displayed" in adaptive/intelligent systems
- "Different behavior per asset" in personalized systems
- "Questions vary by data quality" in gap-based collection

**When in doubt: CHECK SERENA MEMORIES → REPRODUCE WITH PLAYWRIGHT → PRESENT ANALYSIS**

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

### CRITICAL: JSON Sanitization Pattern (ADR-029)

**When to use**: Any code parsing JSON from LLM responses (CrewAI task outputs, direct completions, agent tool results).

**Why needed**: LLMs return malformed JSON - markdown wrappers (` ```json `), trailing commas, single quotes, NaN/Infinity values, truncation at 16KB.

**Pattern**: Use `safe_parse_llm_json()` instead of `json.loads()`:
```python
from app.utils.llm_json_parser import safe_parse_llm_json

# ❌ WRONG - Will fail on LLM output
data = json.loads(llm_response)

# ✅ CORRECT - Handles all LLM quirks
data = safe_parse_llm_json(llm_response)
```

**Never**: Call `json.loads()` directly on raw LLM output without sanitization.

### CRITICAL: API Field Naming Convention (MUST READ - Prevents Recurring Bugs)

#### Current Status (November 2025)
- **Migration Status**: ~80% complete, ongoing incremental migration
- **Rule**: ALL new code MUST use snake_case exclusively
- **Legacy Code**: May contain camelCase - refactor when touched

#### The Rules - NEVER BREAK THESE
1. **Backend (Python/FastAPI)**: ALWAYS uses `snake_case` fields
   - Examples: `flow_id`, `client_account_id`, `master_flow_id`
   - NO exceptions - backend is 100% snake_case

2. **Frontend (TypeScript/React)**:
   - **New Code**: MUST use `snake_case` to match backend exactly
   - **Legacy Code**: May have `camelCase` - refactor to `snake_case` when modifying
   - **No Transformation**: Use API fields exactly as received

3. **Type Definitions**:
   ```typescript
   // ✅ CORRECT - New interfaces use snake_case
   interface FlowData {
     flow_id: string;
     master_flow_id: string;
     client_account_id: number;
   }

   // ❌ WRONG - Never create new camelCase interfaces
   interface FlowData {
     flowId: string;  // NO!
     masterFlowId: string;  // NO!
   }
   ```

#### Migration Guidelines
- **When Touching Legacy Code**: Convert ALL fields in that component to snake_case
- **api-field-transformer.ts**: Now a NO-OP, retained for compatibility
- **Type Safety**: Use explicit checks for numeric fields: `if (confidence_score !== undefined)`
- **PR Scope**: Complete migration for any file you modify

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

### CRITICAL: Observability Enforcement (MANDATORY - November 2025)

**When to apply**: All code that calls LLMs or executes CrewAI tasks MUST be instrumented.

#### LLM Call Tracking (Automatic)
- **New code**: Use `multi_model_service.generate_response()` with tenant context
- **Legacy code**: Auto-tracked via global LiteLLM callback (no changes needed)
- **Tables**: `migration.llm_usage_logs`, `migration.llm_model_pricing`

#### Agent Task Tracking (Manual - Required for CrewAI)
**MANDATORY** - wrap all `task.execute_async()` calls with `CallbackHandlerIntegration`:
1. Create handler with tenant context (flow_id, client_account_id, engagement_id, flow_type, phase)
2. Call `callback_handler.setup_callbacks()`
3. Register task start BEFORE execution via `_step_callback()`
4. Execute task
5. Mark completion via `_task_completion_callback()`

**Full code pattern**: `/docs/guidelines/OBSERVABILITY_PATTERNS.md`
**Reference impl**: `backend/app/services/crewai_flows/unified_assessment_flow.py`

#### Pre-Commit Enforcement
- **CRITICAL** (blocks): `task.execute_async()` without `CallbackHandler` in scope
- **ERROR** (blocks): Direct `litellm.completion()` calls without tracking
- **WARNING**: `crew.kickoff()` without `callbacks` parameter

#### Viewing Data
- **Grafana**: `http://localhost:9999` - LLM costs, agent activity, flow metrics
- **Frontend**: `/finops/llm-costs` - Cost breakdown by model/provider

**Exemptions**: Test code, migration scripts, utility scripts (unless calling LLMs)

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
- ❌ "Memory is enabled with patches" - Memory is DISABLED per ADR-024, use TenantMemoryManager
- ❌ "Too many state tables" - UnifiedDiscoveryFlowState is a Pydantic model, not a table
- ❌ "Reduce layers for simplicity" - Enterprise systems REQUIRE these layers
- ❌ "Remove placeholder implementations" - They provide critical fallback resilience

### Required Reading Before Reviews
- docs/adr/*.md - All Architectural Decision Records
- docs/analysis/Notes/000-lessons.md - Critical lessons learned
- docs/guidelines/ARCHITECTURAL_REVIEW_GUIDELINES.md - Detailed review guidelines

## Key ADRs (Read Before Architectural Changes)

| ADR | When to Reference | Key Rule |
|-----|-------------------|----------|
| **006** | Implementing ANY flow endpoint | All flows use MFO; register with `crewai_flow_state_extensions` |
| **010** | Setting up dev environment | Docker-only development, no local services |
| **012** | Working with flow status | Master=lifecycle (running/paused), Child=operational decisions |
| **015** | Creating/modifying agents | Use TenantScopedAgentPool, singleton per tenant |
| **024** | Any CrewAI memory questions | `memory=False` ALWAYS; use TenantMemoryManager for learning |
| **025** | Adding new flow type | Collection/Discovery=Child Service, Assessment=Direct Flow |
| **029** | Parsing LLM JSON responses | Use `safe_parse_llm_json()`, never raw `json.loads()` |
| **030** | Questionnaire generation issues | Fewer questions = better data quality (adaptive, not bug) |
| **035** | Large LLM responses failing | Chunk per-asset/per-section to avoid 16KB truncation |
| **036** | Asset ↔ canonical app mapping | Use junction table; handles race conditions |

**Other ADRs**: 027 (Flow Type Config), 028 (Phase State), 031 (Observability), 032 (JWT Security), 033 (Context Service), 034 (Questionnaire Dedup)

**Full documentation**: `docs/adr/*.md`

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
