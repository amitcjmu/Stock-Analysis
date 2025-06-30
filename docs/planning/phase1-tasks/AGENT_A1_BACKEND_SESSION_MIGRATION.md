# Phase 1 - Agent A1: Backend Session-to-Flow Migration

## Context
You are part of a parallel remediation effort to fix critical architectural issues in the AI Force Migration Platform. This is Track A (Backend) of Phase 1, focusing on migrating from session_id to flow_id as the primary identifier throughout the system.

### Required Reading Before Starting
- `docs/planning/PHASE-1-REMEDIATION-PLAN.md` - Overall Phase 1 objectives
- `docs/development/AI_Force_Migration_Platform_Summary_for_Coding_Agents.md` - Platform overview
- `docs/troubleshooting/discovery-flow-sync-issues.md` - Current session/flow issues

### Phase 1 Goal
Complete foundation cleanup to enable proper CrewAI integration and remove technical debt. Your work on session-to-flow migration is **critical** as it blocks Phase 2.

## Your Specific Tasks

### 1. Create Database Migration Script
**File to create**: `backend/migrations/add_flow_id_migration.py`

```python
"""
Migration to replace session_id with flow_id as primary identifier.
This migration must:
1. Add flow_id columns where missing
2. Populate flow_id from existing session data
3. Update foreign key relationships
4. Create indexes for performance
5. Be reversible for safety
"""
```

Tables requiring migration:
- `data_imports` - Add flow_id column, populate from existing flows
- `raw_import_records` - Update to reference flow_id
- `import_field_mappings` - Add flow_id for direct reference
- Any other tables using session_id

### 2. Update All Python Models
**Files to modify**: `backend/app/models/*.py`

Update all SQLAlchemy models to:
- Use `flow_id` as the primary reference instead of `session_id`
- Maintain backward compatibility during transition
- Update relationships and foreign keys

Key models to update:
- `DataImport`
- `RawImportRecord`
- `ImportFieldMapping`
- `UnifiedDiscoveryFlowState`

### 3. Create Backward Compatibility Layer
**File to create**: `backend/app/services/migration/session_to_flow.py`

```python
class SessionFlowCompatibilityService:
    """
    Provides backward compatibility during migration.
    - Maps old session_id calls to flow_id
    - Handles dual-key lookups during transition
    - Logs deprecation warnings
    - Provides migration utilities
    """
```

### 4. Write Comprehensive Tests
**File to create**: `backend/tests/test_session_flow_migration.py`

Test cases must cover:
- Migration script correctness
- Data integrity preservation
- Backward compatibility
- Performance impact
- Rollback scenarios

## Success Criteria
- [ ] All session_id columns migrated to flow_id
- [ ] Zero data loss during migration
- [ ] Backward compatibility maintained
- [ ] All tests passing (100% coverage for migration code)
- [ ] Migration is reversible
- [ ] Performance benchmarks met (<100ms overhead)

## Interfaces with Other Agents
- **Agent A2** will update frontend to use your flow_id changes
- **Agent B1** will use flow_id in new v3 API endpoints
- **Agent C1** will use flow_id for state management
- Coordinate on shared types in `backend/app/schemas/base.py`

## Implementation Guidelines
1. Start with the migration script - this is the foundation
2. Test on a copy of production data before proceeding
3. Use feature flags for gradual rollout: `ENABLE_FLOW_ID_PRIMARY`
4. Maintain audit log of all migrations for debugging
5. Document any breaking changes in `BREAKING_CHANGES.md`

## Commands to Run
```bash
# Create migration
docker exec -it migration_backend alembic revision -m "migrate_session_to_flow_id"

# Test migration
docker exec -it migration_backend python -m pytest tests/test_session_flow_migration.py -v

# Run migration
docker exec -it migration_backend alembic upgrade head

# Rollback if needed
docker exec -it migration_backend alembic downgrade -1
```

## Definition of Done
- [ ] Migration script created and tested
- [ ] All models updated with flow_id
- [ ] Compatibility layer implemented
- [ ] Tests achieving 100% coverage
- [ ] PR created with title: "feat: [Phase1-A1] Backend session to flow migration"
- [ ] Code reviewed by at least one other agent
- [ ] Documentation updated

## Notes
- Session IDs in the format: `disc_session_*`
- Flow IDs in the format: UUID v4
- Some tables may have both during transition
- Coordinate with Agent A2 for frontend changes