## Development Best Practices

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
