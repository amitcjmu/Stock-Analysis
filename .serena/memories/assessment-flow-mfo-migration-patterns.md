# Assessment Flow MFO Migration - Reusable Patterns

**Session Date**: January 2025  
**Context**: 7-phase migration replacing deprecated 6R Analysis with MFO-integrated Assessment Flow  
**Impact**: 220 files changed, ~25K lines removed, 8 GitHub issues resolved

## Pattern 1: Post-Deletion Import Cleanup Checklist

**Problem**: After deleting `sixr_tools` module in Phase 4, backend failed to start with ImportError in 3 files  
**Root Cause**: Leftover import statements in `__init__.py`, `crew.py`, and `alembic/env.py`

**Solution - Mandatory Checklist After ANY Module Deletion**:

```bash
# 1. Search for direct imports
grep -r "from app.services.deleted_module" backend/

# 2. Check __init__.py files that might re-export
grep -r "from .deleted_module import" backend/app/**/__init__.py

# 3. Check try/except import blocks
grep -r "from.*deleted_module" backend/ | grep -i "try\|except"

# 4. Check Alembic migrations
grep -r "from app.models.DeletedModel" backend/alembic/

# 5. Verify startup BEFORE committing
docker exec -it migration_backend python -m app.main
```

**Usage**: Run this checklist immediately after any `rm -rf` command that deletes a module/package.

---

## Pattern 2: MFO Two-Table Integration Template

**Problem**: Need to integrate new flow type with Master Flow Orchestrator (ADR-006)  
**Solution**: Atomic two-table pattern with master + child flows

**Code Template** (from `mfo_integration.py:76-123`):

```python
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.your_flow import YourFlow

async def create_your_flow_via_mfo(
    client_account_id: UUID,
    engagement_id: UUID,
    user_id: str,
    db: AsyncSession
) -> dict:
    """Create flow through MFO using two-table pattern."""
    flow_id = uuid4()
    
    try:
        async with db.begin():  # Atomic transaction
            # Step 1: Create master flow (lifecycle management)
            master_flow = CrewAIFlowStateExtensions(
                flow_id=flow_id,
                flow_type="your_flow_type",  # e.g., "planning", "discovery"
                flow_status="running",  # High-level lifecycle
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
                flow_configuration={"created_via": "your_api"},
                flow_persistence_data={}
            )
            db.add(master_flow)
            await db.flush()  # Make flow_id available for FK
            
            # Step 2: Create child flow (operational state)
            child_flow = YourFlow(
                flow_id=flow_id,  # Same UUID, not FK
                master_flow_id=master_flow.flow_id,  # FK relationship
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                status="initialized",  # Operational status
                current_phase="phase_1",
                progress=0,
                configuration={},
                runtime_state={}
            )
            db.add(child_flow)
            
            # Step 3: Commit atomic transaction
            await db.commit()
        
        return {
            "flow_id": str(flow_id),
            "status": child_flow.status,  # Use child for UI
            "current_phase": child_flow.current_phase
        }
    
    except Exception as e:
        logger.error(f"Failed to create flow: {e}")
        raise
```

**Key Points**:
- Single `flow_id` UUID shared by both tables
- `master_flow_id` FK enforces relationship integrity
- `async with db.begin()` ensures atomic rollback on error
- Frontend uses **child flow** status for decisions (ADR-012)
- Master flow only for cross-flow coordination

**Usage**: Use this exact pattern for Planning Flow, Data Cleansing Flow, or any new flow type requiring MFO integration.

---

## Pattern 3: Git History Preservation with `git mv`

**Problem**: Need to rename module/directory while preserving git blame and commit history  
**Anti-Pattern**: Copy + delete loses history

**Correct Pattern**:

```bash
# ❌ DON'T: This loses git history
cp -r backend/app/services/old_module/ backend/app/services/new_module/
rm -rf backend/app/services/old_module/
git add backend/app/services/new_module/
git rm -r backend/app/services/old_module/

# ✅ DO: This preserves history
git mv backend/app/services/old_module/ backend/app/services/new_module/

# Then update imports throughout codebase
find backend/ -type f -name "*.py" -exec sed -i '' 's/from app.services.old_module/from app.services.new_module/g' {} +

# Verify no broken imports
grep -r "old_module" backend/
```

**Benefits**:
- `git blame` shows original authors
- `git log --follow` tracks file across rename
- Code review shows rename (not delete + create)

**Usage**: ALWAYS use `git mv` for renames. Used in Phase 6 for `sixr_strategy_crew` → `assessment_strategy_crew`.

---

## Pattern 4: Multi-Agent Parallel Execution Strategy

**Problem**: Need to coordinate multiple CC agents for large migrations  
**Solution**: Partition work by non-overlapping file scopes

**Successful Parallel Execution** (from Phase 1):

```markdown
**Agent 1 - python-crewai-fastapi-expert**:
Scope: backend/app/api/v1/endpoints/sixr_analysis.py, backend/app/core/feature_flags.py

**Agent 2 - nextjs-ui-architect**:
Scope: src/lib/api/sixr.ts

**Agent 3 - docs-curator**:
Scope: docs/planning/SIXR_ANALYSIS_CURRENT_STATE.md
```

**Critical Rules**:
1. **No file overlap** between agents
2. **Independent domains** (backend vs frontend vs docs)
3. **Explicit scope** in agent prompts
4. **Retry logic** for API limit errors (user confirmed temporary)

**Agent Prompt Template**:

```
IMPORTANT: Your scope is LIMITED to these files:
- backend/app/api/v1/endpoints/your_feature/
- backend/app/models/your_model.py

DO NOT modify any files outside this scope.
After completion, provide summary of files modified.
```

**Usage**: When orchestrating 3+ agents in parallel, assign explicit file scopes to prevent conflicts and enable rollback per agent.

---

## Pattern 5: Database Migration Best Practices

**Problem**: Need to drop deprecated tables while preserving data  
**Solution**: Archive-then-drop pattern with no downgrade

**Template** (from `111_remove_sixr_analysis_tables.py`):

```python
"""Remove deprecated SixR Analysis tables

Revision ID: 111_remove_sixr_analysis_tables
Revises: 110_previous_migration
Create Date: 2025-01-29
"""

def upgrade():
    # Step 1: Archive data BEFORE dropping
    op.execute("""
        CREATE TABLE IF NOT EXISTS migration.sixr_analyses_archive AS
        SELECT * FROM migration.sixr_analyses;
        
        CREATE TABLE IF NOT EXISTS migration.sixr_iterations_archive AS
        SELECT * FROM migration.sixr_iterations;
    """)
    
    # Step 2: Drop tables in dependency order
    op.execute("DROP TABLE IF EXISTS migration.sixr_iterations CASCADE;")
    op.execute("DROP TABLE IF EXISTS migration.sixr_recommendations CASCADE;")
    op.execute("DROP TABLE IF EXISTS migration.sixr_analyses CASCADE;")

def downgrade():
    raise NotImplementedError(
        "No downgrade path - use Assessment Flow. "
        "Archived data available in *_archive tables."
    )
```

**Key Points**:
- Archive BEFORE dropping
- Use IF NOT EXISTS for idempotency
- CASCADE to handle foreign keys
- Explicit NotImplementedError in downgrade
- 3-digit migration naming: `111_description.py`

**Usage**: Use for any table deprecation. Provides rollback via archive tables without complex downgrade logic.

---

## Pattern 6: Backend-Frontend API Synchronization

**Problem**: Backend endpoint changes cause 404s in frontend  
**Solution**: Update both in same commit with verification checklist

**Checklist**:

```bash
# 1. Backend changes
vim backend/app/api/v1/endpoints/your_feature/endpoint.py
vim backend/app/api/v1/router_registry.py

# 2. Search frontend for usage BEFORE changing
grep -r "/api/v1/old-path" src/

# 3. Update frontend services
vim src/lib/api/yourFeatureApi.ts

# 4. Verify in browser console
# Start docker, check Network tab for 404s
docker-compose up -d
# Open http://localhost:8081, check console

# 5. Commit together
git add backend/app/api/ src/lib/api/
git commit -m "feat: Update API endpoint (backend + frontend)"
```

**Critical**: NEVER change backend endpoint without updating frontend in same commit. This prevents the August 2025 404 incident.

**Usage**: Mandatory for ANY API endpoint modification (path, method, or request/response schema).

---

## Anti-Patterns Avoided

1. ❌ **Skipping import cleanup** after deletions → Backend startup failure
2. ❌ **Copy + delete** instead of `git mv` → Lost commit history
3. ❌ **Overlapping agent scopes** → File conflicts, merge issues
4. ❌ **Backend changes without frontend** → 404 errors in production
5. ❌ **Direct model imports in Alembic** → Circular dependency errors

**Reference Issues**: #840 (broken imports), August 2025 404 incident (endpoint sync)

---

## Success Metrics from This Migration

- **Files Changed**: 220 files
- **Code Reduction**: ~25,000 lines removed
- **Zero Downtime**: Deprecation warnings + feature flags
- **Test Coverage**: 3 new integration tests passing
- **Pre-commit**: All checks passing (Black, Flake8, MyPy, Bandit)
- **Documentation**: 1,200+ lines of comprehensive guides

**Key Takeaway**: Large migrations succeed with atomic transactions, parallel agents, and comprehensive verification at each phase.