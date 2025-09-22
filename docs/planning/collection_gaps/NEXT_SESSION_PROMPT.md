# Next Session Prompt: Asset-Agnostic Collection Implementation

## Context for New Session

I need you to orchestrate the complete implementation of the Asset-Agnostic Collection remedial plan using our CC agents. This will complete the current branch's changes and create a new PR for the feature.

## Key Documents to Read First

1. **Implementation Plan**: `/docs/planning/collection_gaps/ASSET_AGNOSTIC_IMPLEMENTATION_PLAN_FINAL.md`
2. **Phase 2 Plan**: `/docs/planning/collection_gaps/PHASE2_IMPLEMENTATION_PLAN.md`
3. **Session Memories**:
   - `collection_gaps_phase2_implementation`
   - `agent_orchestration_patterns`
   - `database_architecture_decisions`

## Critical Learnings from Previous Session

### ✅ What EXISTS (Don't Recreate):
1. **Asset model** exists at `app/models/asset/models.py`
2. **Completeness endpoints** exist at `/flows/{flow_id}/completeness`
3. **8 modular gap analysis tools** exist (better than monolithic)
4. **JSON fields** exist: `assets.custom_attributes` and `assets.technical_details`
5. **Import tables** exist: `raw_import_records` and `ImportFieldMapping`

### ⚠️ Critical Fixes Required:
1. **Asset import path**: Use `from app.models.asset import Asset` (NOT `from app.models.assets`)
2. **Tenant IDs are UUIDs**: NOT integers in any new tables
3. **Router registration**: ALL collection_gaps routers must be registered
4. **Mock data replacement**: DataIntegration.tsx lines 50-152 must be replaced
5. **Transaction patterns**: Use `commit=True` not nested transactions

### 🚫 What NOT to Do:
- Don't create GapAnalysisTool (use existing 8 modular tools)
- Don't create completeness endpoints (already exist)
- Don't use integer tenant IDs (must be UUIDs)
- Don't deploy full EAV immediately (use JSON fields first)
- Don't skip pre-commit validation

## Implementation Sprint (16 Hours)

### Phase 1: Backend Foundation (Hours 1-6)
Use **python-crewai-fastapi-expert** agent to:
1. Create conflicts table migration with UUID tenant IDs
2. Add three asset endpoints (start/conflicts/resolve)
3. Register ALL collection_gaps routers in router_imports.py and router_registry.py
4. Build ConflictDetectionService using existing JSON fields
5. Add feature flag enforcement

### Phase 2: Frontend Changes (Hours 7-10)
Use **nextjs-ui-architect** agent to:
1. Remove application gates with ScopeSelectionDialog
2. Replace mock data (lines 50-152) with real API calls
3. Create Collection Gaps dashboard mounting existing components

### Phase 3: Testing & Validation (Hours 11-14)
Use **qa-playwright-tester** agent to:
1. Test all new endpoints work
2. Verify real conflicts display (not mock data)
3. Test asset-agnostic collection flow
4. Ensure browser cleanup (no orphaned tabs)

### Phase 4: Compliance & Commit (Hours 15-16)
Use **devsecops-linting-engineer** agent to:
1. Run pre-commit checks
2. Fix any linting issues
3. Create comprehensive commit message
4. Push to branch for PR

## Agent Orchestration Pattern

```
For each phase:
1. python-crewai-fastapi-expert → Implement
2. qa-playwright-tester → Validate
3. python-crewai-fastapi-expert → Fix issues
4. Continue until phase complete
Final: devsecops-linting-engineer → Commit
```

## Success Criteria

### Must Have (Week 1):
- [ ] Users can start collection for ANY asset type (not just applications)
- [ ] Real conflicts shown from multiple data sources (no mock data)
- [ ] Conflicts can be resolved through UI
- [ ] All routers properly registered and reachable
- [ ] Feature flags enforced on new endpoints

### Nice to Have (If Time):
- [ ] Auto-resolution for high-confidence conflicts
- [ ] Bulk conflict resolution UI
- [ ] Progress metrics dashboard

## Critical Reminders

1. **ALWAYS** verify router registration - endpoints won't work without it
2. **ALWAYS** use UUID for tenant IDs - verified in governance.py
3. **ALWAYS** test with qa-playwright-tester before committing
4. **NEVER** use --no-verify for commits
5. **NEVER** leave mock data in production UI

## Branch and PR Information

- Current branch: `feat/collection-gaps-phase2-asset-agnostic`
- PR title: "feat: Enable asset-agnostic data collection with conflict detection"
- PR description should reference:
  - Removal of application-first requirement
  - Real conflict detection implementation
  - Support for any asset type (server, database, device, application)
  - JSON-first approach before EAV

## Starting Commands

```bash
# Ensure on correct branch
git checkout -b feat/collection-gaps-phase2-asset-agnostic

# Start Docker if not running
cd config/docker && docker-compose up -d

# Verify backend is healthy
docker logs migration_backend -f
```


---

**Begin by reading the three memory documents and the FINAL implementation plan, then start Phase 1 with the python-crewai-fastapi-expert agent.**