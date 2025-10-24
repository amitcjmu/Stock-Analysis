# RepositoryFactory Usage Guide

## Overview

The `RepositoryFactory` centralizes repository initialization across 42+ files in the codebase. It eliminates duplicate initialization code and ensures consistent multi-tenant context handling.

## Current State Analysis

**Files with repository instantiation**: 42 files in `app/services/`

**Average code duplication per file**: 4-6 lines per repository (init + context passing)

**Estimated LOC savings**: 150-250 lines across the codebase

## Usage Pattern

### Before (Old Pattern)
```python
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
from app.repositories.asset_repository import AssetRepository

# Duplicate initialization code (4-6 lines per repo)
self.master_flow_repo = CrewAIFlowStateExtensionsRepository(
    db=db,
    client_account_id=str(context.client_account_id),
    engagement_id=str(context.engagement_id),
)

self.flow_repo = DiscoveryFlowRepository(
    db=db,
    client_account_id=str(context.client_account_id),
    engagement_id=str(context.engagement_id),
)

self.asset_repo = AssetRepository(
    db=db,
    client_account_id=str(context.client_account_id),
    engagement_id=str(context.engagement_id),
)
```

### After (With RepositoryFactory)
```python
from app.services.repository_factory import RepositoryFactory

# Single factory initialization (1 line)
factory = RepositoryFactory(db, context)

# Get repositories as needed (1 line each)
self.master_flow_repo = factory.get_crewai_flow_repo()
self.flow_repo = factory.get_discovery_flow_repo()
self.asset_repo = factory.get_asset_repo()
```

**LOC Reduction**: From 18 lines → 4 lines (78% reduction)

## Top 10 Example Files for Migration

### 1. `/app/services/discovery_flow_service/core/flow_manager.py`

**Current pattern** (lines 45-56):
```python
# Initialize repositories with multi-tenant context
self.master_flow_repo = CrewAIFlowStateExtensionsRepository(
    db=db,
    client_account_id=str(context.client_account_id),
    engagement_id=str(context.engagement_id),
)

self.flow_repo = DiscoveryFlowRepository(
    db=db,
    client_account_id=str(context.client_account_id),
    engagement_id=str(context.engagement_id),
)
```

**With factory**:
```python
factory = RepositoryFactory(db, context)
self.master_flow_repo = factory.get_crewai_flow_repo()
self.flow_repo = factory.get_discovery_flow_repo()
```

**Savings**: 12 lines → 3 lines (75% reduction)

---

### 2. `/app/services/discovery_flow_service/managers/asset_manager.py`

**Current pattern**:
```python
self.flow_repo = DiscoveryFlowRepository(
    db=db,
    client_account_id=str(context.client_account_id),
    engagement_id=str(context.engagement_id),
)
```

**With factory**:
```python
factory = RepositoryFactory(db, context)
self.flow_repo = factory.get_discovery_flow_repo()
```

**Savings**: 5 lines → 2 lines (60% reduction)

---

### 3. `/app/services/child_flow_services/discovery.py`

**Current pattern** (line ~50):
```python
self.repository = DiscoveryFlowRepository(
    db=self.db,
    client_account_id=context.client_account_id,
    engagement_id=context.engagement_id,
)
```

**With factory**:
```python
factory = RepositoryFactory(self.db, context)
self.repository = factory.get_discovery_flow_repo()
```

**Savings**: 5 lines → 2 lines (60% reduction)

---

### 4. `/app/services/crewai_flows/flow_progress_tracker.py`

**Current pattern** (multiple instances):
```python
async with AsyncSessionLocal() as db:
    repo = CrewAIFlowStateExtensionsRepository(
        db=db,
        client_account_id=self.context.client_account_id,
        engagement_id=self.context.engagement_id,
    )
```

**With factory**:
```python
async with AsyncSessionLocal() as db:
    factory = RepositoryFactory(db, self.context)
    repo = factory.get_crewai_flow_repo()
```

**Savings**: Appears 3 times in file = 15 lines → 6 lines (60% reduction)

---

### 5. `/app/services/crewai_flows/flow_state_manager/status_commands.py`

**Current pattern** (appears 3 times):
```python
child_repo = DiscoveryFlowRepository(
    self.db,
    self.context.client_account_id,
    self.context.engagement_id,
)
```

**With factory**:
```python
factory = RepositoryFactory(self.db, self.context)
child_repo = factory.get_discovery_flow_repo()
```

**Savings**: 3 instances = 12 lines → 6 lines (50% reduction)

---

### 6. `/app/services/assessment_flow_service/core/assessment_manager.py`

**Current pattern**:
```python
self.assessment_repo = AssessmentFlowRepository(
    db, str(context.client_account_id), str(context.engagement_id)
)
self.asset_repo = AssetRepository(db, str(context.client_account_id))
```

**With factory**:
```python
factory = RepositoryFactory(db, context)
self.assessment_repo = factory.get_assessment_flow_repo()
self.asset_repo = factory.get_asset_repo()
```

**Savings**: 6 lines → 3 lines (50% reduction)

---

### 7. `/app/services/asset_service/base.py`

**Current pattern**:
```python
self.repository = AssetRepository(
    db, client_account_id=client_account_id, engagement_id=engagement_id
)
```

**With factory**:
```python
context = RequestContext(client_account_id=client_account_id, engagement_id=engagement_id)
factory = RepositoryFactory(db, context)
self.repository = factory.get_asset_repo()
```

**Note**: Requires creating RequestContext, but improves consistency

---

### 8. `/app/services/crewai_flows/unified_discovery_flow/state_management.py`

**Current pattern**:
```python
repo = DiscoveryFlowRepository(
    db,
    client_account_id=client_account_id,
    engagement_id=engagement_id,
)
```

**With factory**:
```python
context = RequestContext(client_account_id=client_account_id, engagement_id=engagement_id)
factory = RepositoryFactory(db, context)
repo = factory.get_discovery_flow_repo()
```

**Savings**: More consistent context handling

---

### 9. `/app/services/crewai_flows/handlers/phase_executors/dependency_analysis_executor.py`

**Current pattern**:
```python
asset_repo = AssetRepository(db, client_account_id, engagement_id)
```

**With factory**:
```python
context = RequestContext(client_account_id=client_account_id, engagement_id=engagement_id)
factory = RepositoryFactory(db, context)
asset_repo = factory.get_asset_repo()
```

---

### 10. `/app/services/field_mapper_modular.py`

**Current pattern**:
```python
from app.repositories.asset_repository import AssetRepository
asset_repo = AssetRepository(db, client_account_id, engagement_id)
asset = await asset_repo.get_by_id(asset_id)
```

**With factory**:
```python
from app.services.repository_factory import RepositoryFactory
from app.core.context import RequestContext

context = RequestContext(client_account_id=client_account_id, engagement_id=engagement_id)
factory = RepositoryFactory(db, context)
asset_repo = factory.get_asset_repo()
asset = await asset_repo.get_by_id(asset_id)
```

---

## Migration Strategy

### Phase 1: High-Impact Files (Immediate)
Migrate the top 10 files listed above. These provide:
- Maximum LOC reduction (100+ lines)
- Most duplicated patterns
- Central service files

### Phase 2: Service Layer (Next Sprint)
Migrate all remaining files in:
- `app/services/discovery_flow_service/`
- `app/services/assessment_flow_service/`
- `app/services/child_flow_services/`

### Phase 3: Supporting Services (Future)
Migrate remaining files in:
- `app/services/crewai_flows/`
- `app/services/asset_service/`

## Benefits Summary

### Code Quality
- **Consistency**: Single pattern for all repository initialization
- **Maintainability**: Change init signature in one place
- **Readability**: Less boilerplate, clearer intent

### Multi-Tenant Safety
- **Guaranteed context**: Factory ensures context is always passed
- **Type safety**: Factory handles string/int conversions
- **None handling**: Explicit None handling for optional fields

### Developer Experience
- **Less typing**: 75% reduction in initialization code
- **Fewer imports**: One factory import vs. multiple repo imports
- **IDE support**: Better autocomplete and type hints

### Estimated Impact
- **42 files** to potentially migrate
- **150-250 LOC** reduction across codebase
- **Zero logic changes**: Pure refactoring, preserves behavior

## Testing

Comprehensive unit tests are provided in:
- `backend/tests/backend/unit/test_repository_factory.py`

Tests cover:
- ✅ All repository types
- ✅ Context value conversion (string/int)
- ✅ None value handling
- ✅ Multiple repos from same factory
- ✅ Edge cases (empty strings, all None)

## Implementation Notes

### DO:
- ✅ Use factory for new code immediately
- ✅ Migrate files incrementally (no big bang)
- ✅ Test each migration individually
- ✅ Keep backward compatibility during migration

### DON'T:
- ❌ Mix factory and direct instantiation in same file
- ❌ Skip testing after migration
- ❌ Change repository logic during migration
- ❌ Rush migration - this is pure refactoring

## Questions?

For questions or issues:
1. Check unit tests for usage examples
2. Review this guide's top 10 examples
3. See `app/services/repository_factory.py` docstrings
