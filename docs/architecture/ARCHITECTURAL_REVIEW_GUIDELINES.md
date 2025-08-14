# Architectural Review Guidelines for AI Agents

## Purpose
This document provides critical guidelines for AI agents conducting architectural reviews of the AI Force Migration Platform. Following these guidelines will prevent common misunderstandings and ensure accurate assessments aligned with the platform's intentional design decisions.

## Critical Lessons from Past Reviews

### 1. Verify Existence Before Claiming Absence

**Common Mistake:** Claiming components don't exist based on failed searches.

**Correct Approach:**
```python
# Use multiple search strategies
1. mcp__serena__find_symbol with various name patterns
2. mcp__serena__search_for_pattern with regex
3. Glob patterns to find actual files
4. Read imports in related files
```

**Example:** The `TenantScopedAgentPool` exists at:
- `backend/app/services/persistent_agents/tenant_scoped_agent_pool.py`

### 2. Understand Model Types

**Common Mistake:** Confusing Pydantic models with database tables.

**Key Distinctions:**
- **Pydantic Models** (inherits from `BaseModel`): Runtime state objects for validation and serialization
- **SQLAlchemy Models** (inherits from `Base`): Database table definitions
- **Example:** `UnifiedDiscoveryFlowState` is a Pydantic model, NOT a database table

### 3. Respect the Two-Table Architecture

**Common Mistake:** Suggesting to collapse the two-table pattern as "overcomplicated."

**Intentional Design:**
```
Master Table (crewai_flow_state_extensions):
- Orchestration lifecycle (running, paused, completed)
- Generic flow management
- Master flow ID generation

Child Table (discovery_flows):
- Flow-specific operational data
- UI-facing status and progress
- Phase-specific information
```

**Reference:** See `docs/analysis/Notes/000-lessons.md` line 10-13

### 4. Memory System Status

**Common Mistake:** Claiming memory is "disabled globally" when seeing patches.

**Reality:**
- Memory IS enabled (`memory=True` in multiple configurations)
- DeepInfra embedding patch ADAPTS the system, doesn't disable it
- See: `backend/app/services/crewai_memory_patch.py`

### 5. Enterprise Architecture Patterns

**Common Mistake:** Dismissing modular handlers as "over-engineering."

**These Layers Are Required For:**
- **Multi-tenant isolation**: Every request scoped by client/engagement
- **Graceful degradation**: Multiple fallback tiers
- **Atomic transactions**: Database consistency
- **Background processing**: Long-running agent tasks
- **Audit trails**: Enterprise compliance

## Architectural Principles to Respect

### 1. Agent-First Architecture
- ALL intelligence comes from CrewAI agents (ADR-008)
- Persistent agents accumulate knowledge over time (ADR-015)
- No hardcoded business logic - agents make decisions

### 2. Multi-Tenant by Design
- Every data access scoped by `client_account_id` and `engagement_id`
- `ContextAwareRepository` pattern enforces isolation
- Tenant-scoped agent pools maintain separate memory

### 3. Resilience Through Layers
```
API Endpoint
    ↓
Handler (validation, context extraction)
    ↓
Service (business logic, orchestration)
    ↓
Repository (data access, multi-tenant scoping)
    ↓
Database (PostgreSQL with migration schema)
```

### 4. Intentional Fallback Patterns
- Placeholder implementations are FEATURES for resilience
- They prevent total failure when a component is unavailable
- Gradual replacement under feature flags is the correct approach

## How to Conduct Architectural Reviews

### Step 1: Understand Current State
```python
# Read these first:
1. docs/adr/*.md - Architectural Decision Records
2. docs/analysis/Notes/000-lessons.md - Consolidated learnings
3. backend/app/models/*.py - Understand data models
4. backend/app/services/persistent_agents/*.py - Agent architecture
```

### Step 2: Verify Claims
Before stating something doesn't exist or is broken:
1. Search multiple ways (symbol, pattern, glob)
2. Check if it's imported/used elsewhere
3. Understand if a "patch" is adaptation vs disability
4. Read the ADR to understand if it's intentional

### Step 3: Respect Existing Patterns
- Two-table flow architecture is REQUIRED
- Modular handlers provide enterprise features
- Fallbacks ensure graceful degradation
- Memory patches enable DeepInfra compatibility

### Step 4: Propose Enhancements, Not Replacements
Instead of: "Replace entire architecture"
Propose: "Enhance existing patterns with..."

Examples:
- Add convenience methods to existing classes
- Create configuration helpers for better organization
- Implement feature flags for gradual improvements
- Add monitoring/metrics to existing components

## Common Pitfalls to Avoid

### 1. Search Failures
❌ "I searched for X and didn't find it, so it doesn't exist"
✅ "I've tried multiple search strategies; X might not exist or might be named differently"

### 2. Misunderstanding Patches
❌ "There's a monkey patch, so the system is broken"
✅ "The monkey patch adapts CrewAI to use DeepInfra embeddings"

### 3. Oversimplification
❌ "Reduce 7 layers to 3 for simplicity"
✅ "These layers provide specific enterprise features documented in ADRs"

### 4. Ignoring Documentation
❌ "This seems overcomplicated, let's simplify"
✅ "The ADR explains this is required for multi-tenant isolation"

## Recommended Review Process

1. **Start with Documentation**
   - Read relevant ADRs
   - Check docs/analysis/Notes/000-lessons.md
   - Review recent commits for context

2. **Understand Before Judging**
   - Why does this pattern exist?
   - What ADR documents this decision?
   - What problem does it solve?

3. **Verify Thoroughly**
   - Use multiple search methods
   - Check actual file existence
   - Read related implementations

4. **Propose Incrementally**
   - Enhance existing patterns
   - Use feature flags for changes
   - Maintain backward compatibility
   - Preserve fallback mechanisms

## Example: Correct Assessment

### Reviewing Field Mapping Performance

**Good Analysis:**
"The field mapping uses `PersistentFieldMapping` class which leverages `TenantScopedAgentPool` for persistent agents. This reduces execution from 86s to <10s by reusing agents. The implementation exists and works. 

Potential enhancements:
1. Add formal embedder configuration to replace monkey patch
2. Add convenience method `get_agent(context, type)` to pool
3. Implement Redis-backed pool statistics for monitoring"

**Bad Analysis:**
"Persistent agents don't exist, the system is overcomplicated with too many layers, memory is disabled, and we should rebuild everything with 3 simple layers."

## References

Key files for understanding architecture:
- `backend/app/services/persistent_agents/tenant_scoped_agent_pool.py` - Persistent agent implementation
- `backend/app/services/crewai_flows/crews/persistent_field_mapping.py` - Fast field mapping
- `backend/app/models/unified_discovery_flow_state.py` - Pydantic state model
- `backend/app/models/crewai_flow_state_extensions.py` - Master flow table
- `backend/app/models/discovery_flow.py` - Child flow table
- `docs/analysis/Notes/000-lessons.md` - Critical lessons learned
- `docs/adr/015-persistent-multi-tenant-agent-architecture.md` - Agent persistence ADR

## Summary

Before conducting architectural reviews:
1. Thoroughly understand existing patterns
2. Respect documented decisions in ADRs
3. Verify existence through multiple search methods
4. Distinguish between runtime models and database tables
5. Propose enhancements rather than replacements
6. Maintain enterprise requirements (multi-tenancy, resilience, audit)

Remember: What appears as "complexity" often provides critical enterprise features. Always understand the "why" before suggesting changes.