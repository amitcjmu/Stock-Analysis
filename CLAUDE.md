## Subagent Instructions and Requirements

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

3. **Include This in Every Subagent Prompt**:
   ```
   IMPORTANT: First read these files:
   1. /docs/analysis/Notes/coding-agent-guide.md
   2. /.claude/agent_instructions.md

   After completing your task, provide a detailed summary following the template in agent_instructions.md, not just "Done".
   Include: what was requested, what was accomplished, technical details, and verification steps.
   ```

## Development Best Practices

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
- Never by pass pre-commit checks with --no-verify unless you have gone through the pre-commit checks at least once and fixed all the issues mentioned by the checks

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

### Files That MUST Be Updated Together
- Backend: `router_registry.py`, `router_imports.py`, endpoint files
- Frontend: `masterFlowService.ts`, `discoveryService.ts`, `collectionService.ts`

### Never Do This
- ❌ Change backend without frontend
- ❌ Use fallbacks to hide broken endpoints
- ❌ Skip browser console check for 404s

- Never start with adding new code to fix any issue however critical it may be. Always check existing code or Git history for such functionality and see if it can be adjusted to meet our needs, and only if none such exists then you'll create new code
