# Actionable Backend Migration Plan
**Based on Dependency Graph Analysis**

## Executive Summary

🚨 **CRITICAL FINDING**: **ZERO truly orphaned files** detected. Even files marked as "legacy" in the GPT5 inventory are actively imported. The codebase is in a **transitional state** with massive circular dependencies.

### Key Metrics from Dependency Analysis

- **Total files analyzed**: 2,035
- **Crew-related files**: 148
- **Truly orphaned files**: **0** ⚠️
- **Migration candidates**: 28 files with deprecated patterns
- **Coupling issues**:
  - 322 old → new dependencies
  - 112 new → old dependencies
  - 4 mixed pattern files

### Why This Matters

The **absence of orphaned files** confirms our manual review: **archiving based on the GPT5 inventory would break production**. Everything is interconnected through a web of imports.

---

## Phase 1: Immediate Actions (Safe Archival) ✅

### Files Safe to Archive NOW (20 files)

These files are only imported by themselves or deprecated code paths:

#### 1.1 Unmounted Routers (6 files)
```bash
backend/app/api/v1/endpoints/demo.py
backend/app/api/v1/endpoints/data_cleansing.py.bak
backend/app/api/v1/endpoints/flow_processing.py.backup
backend/app/api/v1/discovery/dependency_endpoints.py
backend/app/api/v1/discovery/chat_interface.py
backend/app/api/v1/discovery/app_server_mappings.py
```

**Verification**: None registered in `router_registry.py`

#### 1.2 Example Agents (9 files)
```bash
backend/app/services/agents/validation_workflow_agent_crewai.py
backend/app/services/agents/tier_recommendation_agent_crewai.py
backend/app/services/agents/progress_tracking_agent_crewai.py
backend/app/services/agents/data_validation_agent_crewai.py
backend/app/services/agents/data_cleansing_agent_crewai.py
backend/app/services/agents/critical_attribute_assessor_crewai.py
backend/app/services/agents/credential_validation_agent_crewai.py
backend/app/services/agents/collection_orchestrator_agent_crewai.py
backend/app/services/agents/asset_inventory_agent_crewai.py
```

**Recommendation**: Move to `docs/examples/agent_patterns/` instead of full archival

#### 1.3 Legacy Superseded Code (5 files)
```bash
backend/app/services/crewai_flows/crews/inventory_building_crew_legacy.py
backend/app/services/crewai_flows/crews/manual_collection_crew.py
backend/app/services/crewai_flows/crews/data_synthesis_crew.py
backend/app/services/crewai_flows/crews/field_mapping_crew_fast.py
backend/app/services/crewai_flows/crews/agentic_asset_enrichment_crew.py
```

**Note**: `inventory_building_crew_original/` is still imported - keep for now

---

## Phase 2: Break Circular Dependencies (High Priority) 🔥

### Problem: Tight Coupling Between Old and New Patterns

The dependency graph shows **434 coupling violations**:

#### 2.1 Major Coupling Points

**File**: `app/services/crewai_flows/crews/inventory_building_crew_original/crew.py`
- **Status**: Mixed pattern (has both old Crew() and imports new PhaseExecutors)
- **Imported by**: 160 files
- **Imports**: Phase executors (new pattern)
- **Action**: Refactor to use `TenantScopedAgentPool` pattern

**File**: `app/services/crewai_flows/crews/persistent_field_mapping.py`
- **Status**: Mixed pattern (both old and new)
- **Imported by**: 166 files
- **Uses**: Both `Crew()` instantiation AND `TenantScopedAgentPool`
- **Action**: Remove `Crew()` usage, use only persistent agents

**File**: `app/services/crews/base_crew.py`
- **Imported by**: 398 files
- **Has**: Direct `Crew()` instantiation
- **Action**: Deprecate and create `PersistentBaseCrew` that uses agent pool

**File**: `app/services/crewai_flows/config/crew_factory/factory.py`
- **Imported by**: 209 files
- **Has**: Direct `Crew()` instantiation
- **Action**: Refactor to use `TenantScopedAgentPool` for agent creation

### 2.2 Decoupling Strategy

```python
# Current (deprecated pattern)
from crewai import Crew, Agent, Task

crew = Crew(
    agents=[agent1, agent2],
    tasks=[task1, task2],
    memory=False  # Per ADR-024
)

# Target (persistent pattern)
from app.services.persistent_agents import TenantScopedAgentPool

agent = await TenantScopedAgentPool.get_agent(
    context=request_context,
    agent_type="field_mapping",
    service_registry=service_registry
)

result = await agent.process(input_data)
```

---

## Phase 3: Migration Sequence (Sequential, Non-Disruptive) 🔄

### Week 1: Foundation

**3.1 Create Persistent Agent Wrappers**

For each of the 26 files with direct `Crew()` instantiation, create a persistent agent wrapper:

Example for `field_mapping_crew.py`:
```python
# New file: app/services/persistent_agents/field_mapping_persistent.py

async def get_persistent_field_mapper(
    context: RequestContext,
    service_registry: ServiceRegistry
) -> Agent:
    """Get or create persistent field mapping agent"""
    return await TenantScopedAgentPool.get_agent(
        context=context,
        agent_type="field_mapping",
        service_registry=service_registry
    )
```

**Files to wrap**:
1. `field_mapping_crew.py` → `field_mapping_persistent.py`
2. `dependency_analysis_crew/crew.py` → `dependency_analysis_persistent.py`
3. `technical_debt_crew.py` → `technical_debt_persistent.py`
4. `inventory_building_crew_original/crew.py` → `inventory_building_persistent.py`
5. (Continue for all 26 files)

### Week 2: Update Importers

**3.2 Replace Imports Gradually**

Start with files that have the FEWEST dependencies:

```bash
# Find files with fewest imports
grep -r "from.*field_mapping_crew import" --include="*.py" | wc -l
```

Update imports in batches:
```python
# OLD
from app.services.crewai_flows.crews.field_mapping_crew import create_field_mapping_crew

# NEW
from app.services.persistent_agents.field_mapping_persistent import get_persistent_field_mapper
```

### Week 3: Verify and Test

**3.3 Integration Testing**

For each migrated file:
1. Run unit tests: `pytest tests/unit/test_{file}.py`
2. Run integration tests: `pytest tests/integration/`
3. Check Docker logs for errors: `docker logs migration_backend --tail=100`
4. Verify no performance degradation (persistent agents should be faster)

### Week 4: Cleanup

**3.4 Remove Old Crew Files**

After ALL importers have been migrated:
```bash
# Verify no remaining imports
grep -r "field_mapping_crew" --include="*.py" app/
# If output is empty, safe to remove
mv backend/app/services/crewai_flows/crews/field_mapping_crew.py \
   backend/archive/2025-10/field_mapping_crew.py
```

---

## Phase 4: crew_class Deprecation (Post-Migration) 📝

### Current State

2 files use `crew_class`:
- `app/services/flow_configs/discovery_flow_config.py` (imported by 45 files)
- `app/services/sixr_engine_modular.py` (imported by 29 files)

### Migration Path

**4.1 Update Flow Configs**

```python
# Current in discovery_flow_config.py (line 75)
crew_class=UnifiedDiscoveryFlow,  # OLD: For initialization
child_flow_service=DiscoveryChildFlowService,  # NEW: For execution

# Target (after Phase 3 completion)
# Remove crew_class entirely
child_flow_service=DiscoveryChildFlowService,  # Handles both init and execution
```

**4.2 Update Flow Creation Logic**

In `flow_creation_operations.py:348-381`, replace:
```python
# OLD
if can_instantiate:
    flow_instance = flow_config.crew_class(...)

# NEW
if flow_config.child_flow_service:
    flow_instance = await flow_config.child_flow_service.initialize_flow(...)
```

---

## Phase 5: Monitoring and Rollback Strategy 🛡️

### Success Criteria

For each phase, verify:
1. ✅ All tests pass
2. ✅ No increase in error rates (check `docker logs migration_backend`)
3. ✅ Performance maintained or improved
4. ✅ All imports resolved correctly

### Rollback Plan

If any phase fails:
```bash
# 1. Git revert the changes
git revert <commit-hash>

# 2. Rebuild Docker containers
docker-compose -f config/docker/docker-compose.yml build --no-cache backend

# 3. Restart services
docker-compose -f config/docker/docker-compose.yml up -d

# 4. Check logs
docker logs migration_backend --tail=100
```

### Monitoring Commands

```bash
# Check for import errors
docker logs migration_backend 2>&1 | grep "ImportError\|ModuleNotFoundError"

# Check for crew instantiation errors
docker logs migration_backend 2>&1 | grep "Crew\(\)" -A 5

# Verify persistent agent usage
docker logs migration_backend 2>&1 | grep "TenantScopedAgentPool"

# Performance metrics
docker logs migration_backend 2>&1 | grep "performance\|timing\|duration"
```

---

## Dependency Visualization

### View the Dependency Graph

The Mermaid diagram is available at:
```
docs/analysis/backend_cleanup/dependency_graphs/dependency_graph_crews.mmd
```

To visualize:
1. Copy content from `.mmd` file
2. Paste into https://mermaid.live
3. Or use VS Code extension: "Mermaid Preview"

### Coupling Analysis

Full reports available at:
- `dependency_graphs/coupling_analysis.md` - Circular dependency details
- `dependency_graphs/migration_candidates.md` - Files needing updates
- `dependency_graphs/analysis_data.json` - Programmatic access

---

## Risk Assessment

### High Risk (Do NOT Archive)

❌ **Never archive**:
- `persistent_field_mapping.py` - Primary production implementation (166 importers)
- `dependency_analysis_crew/` - Active phase executor (172 importers)
- `technical_debt_crew.py` - 6R strategy requirement (165 importers)
- `base_crew.py` - Foundation class (398 importers)
- `crew_factory/factory.py` - Core agent creation (209 importers)

### Medium Risk (Migrate First)

⚠️ **Migrate before considering archival**:
- `inventory_building_crew_original/` - 160 importers, mixed patterns
- `optimized_field_mapping_crew/` - May be superseded but has imports
- `asset_intelligence_crew.py` - Used by confidence manager

### Low Risk (Safe to Archive)

✅ **After verification**:
- Files in Phase 1 list (20 files)
- Files with only self-referential imports
- Files explicitly commented as deprecated in codebase

---

## Timeline Estimate

| Phase | Duration | Effort | Risk |
|-------|----------|--------|------|
| Phase 1: Safe Archival | 1 day | Low | Low |
| Phase 2: Break Coupling | 2 weeks | High | Medium |
| Phase 3: Sequential Migration | 4 weeks | High | Medium |
| Phase 4: crew_class Removal | 1 week | Medium | Low |
| Phase 5: Monitoring | Ongoing | Low | Low |

**Total**: ~7-8 weeks for complete migration

---

## Success Metrics

- [ ] 0 files with direct `Crew()` instantiation
- [ ] 0 circular dependencies between old/new patterns
- [ ] All crew operations use `TenantScopedAgentPool`
- [ ] `crew_class` removed from all flow configs
- [ ] 20+ files successfully archived
- [ ] No performance degradation
- [ ] All tests passing

---

## Conclusion

The dependency analysis reveals that **safe archival is limited to 20 files** (not 84 as GPT5 suggested). The remaining files require a **structured migration** to break circular dependencies before any archival can occur.

**Key Takeaway**: Don't archive first, migrate first. The absence of orphaned files means everything is connected, and we must carefully untangle dependencies to avoid breaking production.

**Next Steps**:
1. Archive the 20 safe files (Phase 1)
2. Start Week 1 of Phase 2 (create persistent agent wrappers)
3. Monitor coupling metrics after each migration
4. Update this plan based on learnings

---

**Report Generated**: 2025-10-10
**Methodology**: AST parsing, import graph analysis, pattern detection
**Tools**: Python dependency analyzer, Serena MCP, ADR review
