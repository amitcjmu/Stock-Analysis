# Crews Superseded by Persistent Agent Wrappers

**Archive Date**: 2025-10-11
**Reason**: Superseded by persistent agent wrappers (Phase B1 + B2)
**Phase**: B3 - Archive Old Crew Implementations

---

## Archived Crews

These 5 crew implementations were superseded by persistent agent wrappers created in Phase B1 and migrated in Phase B2.

### 1. field_mapping_crew.py
- **Superseded By**: `app/services/persistent_agents/field_mapping_persistent.py`
- **Reason**: Direct crew instantiation pattern replaced with TenantScopedAgentPool singleton
- **Active Imports**: 2 fallback imports remain (unified_flow_crew_manager.py, field_mapping_persistent.py)
- **Usage**: Graceful fallback if persistent wrapper unavailable

### 2. persistent_field_mapping.py
- **Superseded By**: `app/services/persistent_agents/field_mapping_persistent.py`
- **Reason**: Old persistent pattern replaced with newer TenantScopedAgentPool-based implementation
- **Active Imports**: 0
- **Note**: This was an interim persistent implementation before ADR-015 and ADR-024

### 3. data_import_validation_crew.py
- **Superseded By**: `app/services/persistent_agents/data_import_validation_persistent.py`
- **Reason**: Direct crew instantiation replaced with persistent agent pattern
- **Active Imports**: 0
- **Migration**: All importers updated in Phase B2

### 4. dependency_analysis_crew/ (directory)
- **Superseded By**: `app/services/persistent_agents/dependency_analysis_persistent.py`
- **Reason**: Multi-file crew implementation replaced with single persistent wrapper
- **Active Imports**: 0
- **Features**: App-to-app and app-to-server dependency analysis now via convenience functions

### 5. tech_debt_analysis_crew/ (directory)
- **Superseded By**: `app/services/persistent_agents/technical_debt_persistent.py`
- **Reason**: Multi-file crew implementation replaced with single persistent wrapper
- **Active Imports**: 0
- **Features**: Security, performance, and maintainability analysis now via convenience functions

---

## Why These Were Archived

### ADR-015: Persistent Multi-Tenant Agent Architecture
- Old pattern: Direct `Crew()` instantiation per request (memory leaks, no tenant isolation)
- New pattern: Singleton agent per (tenant, agent_type) via TenantScopedAgentPool
- Benefits: Memory efficiency, tenant isolation, lazy initialization

### ADR-024: TenantMemoryManager Architecture
- Old pattern: CrewAI built-in memory (caused 401 errors with DeepInfra)
- New pattern: `memory=False` + TenantMemoryManager for agent learning
- Benefits: Multi-tenant memory isolation, PostgreSQL + pgvector native, no external ChromaDB

### Phase B1 + B2 Migration
- **Phase B1**: Created 4 persistent agent wrappers (990 lines)
- **Phase B2**: Migrated 6 production files to use wrappers
- **E2E Tests**: All critical journeys passing (field mapping, tech debt, collection)
- **Result**: 0 active imports to old crews (except 2 graceful fallbacks)

---

## Verification

**Import Analysis** (Phase B3):
```bash
# Field mapping crew - 2 fallback imports (safe)
grep -r "from.*field_mapping_crew import" app/ | grep -v archive
# Result: 2 imports (fallback in unified_flow_crew_manager, field_mapping_persistent)

# Technical debt crew - 0 imports
grep -r "from.*tech_debt_analysis_crew import" app/ | grep -v archive
# Result: 0 imports

# Dependency analysis crew - 0 imports
grep -r "from.*dependency_analysis_crew import" app/ | grep -v archive
# Result: 0 imports

# Data import validation crew - 0 imports
grep -r "from.*data_import_validation_crew import" app/ | grep -v archive
# Result: 0 imports

# Old persistent field mapping - 0 imports
grep -r "from.*persistent_field_mapping import" app/ | grep -v archive | grep -v fallback
# Result: 0 imports
```

**E2E Test Results** (from Phase B2):
- ✅ Discovery Flow - Field Mapping: PASS (13/13 mappings, 100% accuracy)
- ✅ 6R Analysis - Technical Debt: PASS
- ✅ Collection Flow: PASS
- ✅ Zero JavaScript errors, zero backend errors

---

## Restoration Instructions

### If Restoration Is Needed (Emergency Rollback)

1. **Copy files back to original location**:
   ```bash
   cd backend
   git mv archive/2025-10/crews_superseded_by_persistent_wrappers/field_mapping_crew.py app/services/crewai_flows/crews/
   git mv archive/2025-10/crews_superseded_by_persistent_wrappers/persistent_field_mapping.py app/services/crewai_flows/crews/
   git mv archive/2025-10/crews_superseded_by_persistent_wrappers/data_import_validation_crew.py app/services/crewai_flows/crews/
   git mv archive/2025-10/crews_superseded_by_persistent_wrappers/dependency_analysis_crew app/services/crewai_flows/crews/
   git mv archive/2025-10/crews_superseded_by_persistent_wrappers/tech_debt_analysis_crew app/services/crewai_flows/crews/
   ```

2. **Verify imports work**:
   ```bash
   python -c "from app.services.crewai_flows.crews.field_mapping_crew import create_field_mapping_crew; print('✅ Restoration successful')"
   ```

3. **Run tests**:
   ```bash
   pytest tests/unit/test_crew_factory.py -v
   ```

### Why Restoration Should NOT Be Needed

1. **Graceful Fallbacks**: Persistent wrappers have 3-tier fallback (NEW → OLD → Standard)
2. **Tested**: All E2E tests passed before archival
3. **Zero Active Imports**: Only 2 fallback imports remain (by design)
4. **ADR Compliance**: New architecture is the standard per ADR-015 and ADR-024

---

## Related Documentation

- **Phase B1 Report**: `docs/analysis/backend_cleanup/PHASE_B1_COMPLETE.md`
- **Phase B2 Report**: PR #563 - Backend cleanup migration
- **ADR-015**: Persistent Multi-Tenant Agent Architecture
- **ADR-024**: TenantMemoryManager Architecture
- **Persistent Wrappers**: `backend/app/services/persistent_agents/*_persistent.py`

---

**Archive Status**: ✅ SAFE - All crews superseded by tested persistent agent wrappers
**Rollback Risk**: LOW - Graceful fallbacks in place, zero breaking changes
**Next Phase**: B4 - Update remaining tests to use persistent wrappers
