# Collection Flow Redesign - Lean Single-Agent Architecture

## Context & Problem Statement

The current collection flow gap analysis implementation is severely bloated with redundant code and broken architecture:

### Current Broken Architecture (3-Layer Bloat):
```
User selects assets
  ↓
execution_engine_crew_collection._execute_gap_analysis()
  ↓
gap_analysis_agent.analyze_collection_gaps() (wrapper layer)
  ↓
gap_analysis_crew.create_gap_analysis_crew() (creates 3 agents)
  ↓
[gap_specialist, sixr_impact_assessor, gap_prioritizer] execute sequentially
  ↓
Problem: Agents work with EMPTY/SYNTHETIC data (no real assets loaded)
  ↓
gap_persistence tries to parse fabricated output
  ↓
Result: 0 gaps detected, `'Agent' object has no attribute 'get'` errors
```

### Root Issues:
1. **3-agent crew structure** - gap_specialist, sixr_impact_assessor, gap_prioritizer working sequentially without real data
2. **Duplicate implementations** - gap_analysis_agent.py wraps gap_analysis_crew.py doing the exact same thing
3. **Separate questionnaire phase** - Gap analysis and questionnaire generation should be ONE atomic operation
4. **Synthetic data processing** - Agents analyze gaps without loading actual asset data from database
5. **Legacy code from July 2025** - Never properly tested with real user flow

## Desired Architecture (Lean Single-Agent):

```
User selects assets
  ↓
execution_engine_crew_collection._execute_gap_analysis()
  ↓
TenantScopedAgentPool.get_or_create_agent("gap_analysis_specialist")
  ↓
SINGLE persistent agent executes ONE task:
  1. Load REAL selected assets from database
  2. Compare each asset against 22 critical attributes
  3. Identify missing fields per asset
  4. Generate questionnaire with missing fields
  5. Return structured output: { gaps: [...], questionnaire: {...} }
  ↓
gap_persistence.persist_collection_gaps() - simple, predictable structure
  ↓
Result: Gaps persisted to collection_data_gaps table + questionnaire ready
```

## Files to DELETE (Not Archive):

### Primary Bloat - DELETE These Entirely:
1. **`backend/app/services/crewai_flows/crews/collection/gap_analysis_crew.py`**
   - 354 lines of 3-agent crew boilerplate
   - Created: July 2025, never worked properly

2. **`backend/app/services/ai_analysis/gap_analysis_agent.py`**
   - 330 lines of wrapper around gap_analysis_crew
   - Duplicates functionality

3. **`backend/app/services/ai_analysis/gap_analysis_tasks.py`**
   - Task templates for 3-agent crew
   - No longer needed

4. **`backend/app/services/agents/questionnaire_dynamics_agent_crewai.py`**
   - Separate questionnaire agent
   - Should be integrated with gap analysis

### Secondary Files - Review & Simplify:
5. **`backend/app/services/ai_analysis/questionnaire_generator/`** (entire directory)
   - Check if tools can be reused or should be deleted

6. **`backend/app/services/flow_orchestration/collection_phase_handlers.py`**
   - Lines 84-143: Placeholder questionnaire generation - DELETE
   - Keep only essential handlers

## Files to CREATE:

### New Lean Implementation:
1. **`backend/app/services/collection/gap_analysis_service.py`**
   - Single persistent agent using TenantScopedAgentPool
   - ONE task: analyze gaps + generate questionnaire atomically
   - Loads REAL asset data from database
   - Returns structured output for gap_persistence.py

## Implementation Requirements:

### 1. Use Existing Infrastructure (Don't Reinvent):
- **TenantScopedAgentPool**: `backend/app/services/persistent_agents/tenant_scoped_agent_pool.py`
  - Use: `await TenantScopedAgentPool.get_or_create_agent(client_id, engagement_id, "gap_analysis_specialist")`
  - This is the CORRECT architecture from ADR-015

- **Critical Attributes Framework**: `backend/app/services/crewai_flows/tools/critical_attributes_tool/base.py`
  - Import: `CriticalAttributesDefinition.get_attribute_mapping()`
  - 22 critical attributes already defined

- **Gap Persistence**: `backend/app/services/flow_orchestration/gap_persistence.py`
  - Keep existing `persist_collection_gaps()` function
  - Simplify to expect ONE predictable response format

### 2. Single Agent Task Structure:
```python
async def analyze_gaps_and_generate_questionnaire(
    client_account_id: str,
    engagement_id: str,
    selected_asset_ids: List[str],
    db_session: AsyncSession
) -> Dict[str, Any]:
    """
    Single atomic operation using ONE persistent agent.

    Returns:
    {
        "gaps": {
            "critical": [
                {
                    "asset_id": "uuid",
                    "field": "technology_stack",
                    "type": "missing_field",
                    "description": "Missing required field",
                    "impact": "high"
                }
            ]
        },
        "questionnaire": {
            "sections": [
                {
                    "section_id": "infrastructure",
                    "questions": [...]
                }
            ]
        },
        "summary": {
            "total_gaps": 15,
            "assets_analyzed": 3
        }
    }
    """
```

### 3. Integration Points to Update:
- **`backend/app/services/flow_orchestration/execution_engine_crew_collection.py`**
  - Line 158: `_execute_gap_analysis()` method
  - Replace 3-agent orchestration with single service call

- **`backend/app/api/v1/endpoints/collection_applications.py`**
  - Line 400: Triggers gap analysis phase
  - No changes needed (already passes selected_asset_ids)

### 4. Database Schema (Keep Existing):
- **`collection_data_gaps` table** - already exists
- **`adaptive_questionnaires` table** - already exists
- Gap persistence uses: `(collection_flow_id, field_name, gap_type, asset_id)` composite key for deduplication

## Branch to DELETE:
- **Branch**: `feature/implement-gap-analysis-detection-20251003`
- **Commits on this branch (all can be discarded)**:
  1. `c0d893276` - Debug logging for broken 3-agent implementation
  2. `e20c812c9` - More debug logging and fallback parsing
  3. `7230d7238` - Asset model AttributeError fix (real fix, but in wrong architecture)
  4. `7de3c81bb` - Questionnaire list format handling
  5. `99a648d79` - Application → Asset migration (good change, but in wrong architecture)
  6. `3da44edb8` - GPT-5 recommendations (batch processing - keep this idea)
  7. `3e7cba6b4` - Agentic gap analysis (wrong - 3-agent bloat)

**Recommendation**: Delete entire branch, start fresh from `main`

## Success Criteria for New Implementation:

### Functional Requirements:
1. ✅ User selects 1-3 assets in collection flow
2. ✅ Gap analysis phase executes in <30 seconds
3. ✅ Gaps persist to `collection_data_gaps` table (verify with SQL query)
4. ✅ Questionnaire generated with specific missing fields
5. ✅ Frontend displays questionnaire to user
6. ✅ No errors in backend logs

### Technical Requirements:
1. ✅ Use TenantScopedAgentPool for persistent agent
2. ✅ ONE agent, ONE task (no crew orchestration)
3. ✅ Load REAL assets from database
4. ✅ Compare against 22 critical attributes
5. ✅ Return structured output (no parsing needed)
6. ✅ Batch processing for >50 assets (GPT-5 recommendation)

### Code Quality:
1. ✅ Total lines: <200 for gap_analysis_service.py
2. ✅ No duplicate implementations
3. ✅ No synthetic/fabricated data
4. ✅ Clear error messages
5. ✅ Comprehensive logging

## Testing Plan:

### 1. Unit Tests (Create):
```python
# tests/backend/unit/services/collection/test_gap_analysis_service.py
async def test_single_agent_gap_analysis():
    # Test with 2 assets missing different fields
    # Verify gaps detected correctly
    # Verify questionnaire generated
```

### 2. Integration Test (Use Playwright):
```
1. Navigate to /collection
2. Start collection flow
3. Select 2 assets (1 server, 1 database)
4. Wait for gap analysis completion
5. Verify gaps in database: SELECT * FROM collection_data_gaps
6. Verify questionnaire displayed in UI
```

### 3. Verification Commands:
```bash
# Check gaps persisted
docker exec -it migration_postgres psql -U postgres -d migration_db -c \
  "SELECT COUNT(*), gap_type FROM migration.collection_data_gaps GROUP BY gap_type;"

# Check questionnaire created
docker exec -it migration_postgres psql -U postgres -d migration_db -c \
  "SELECT id, title, target_gaps FROM migration.adaptive_questionnaires ORDER BY created_at DESC LIMIT 1;"
```

## References:

### Architectural Decision Records:
- **ADR-015**: Persistent Multi-Tenant Agent Architecture
  - Location: `/docs/adr/015-persistent-multi-tenant-agent-architecture.md`
  - Key: Use TenantScopedAgentPool, no per-execution agent creation

- **ADR-024**: TenantMemoryManager (CrewAI memory disabled)
  - Location: `/docs/adr/024-tenant-memory-manager-architecture.md`
  - Key: Set `memory=False` in agent creation

### Existing Working Examples:
- **Discovery Flow**: Uses persistent agents correctly
  - File: `backend/app/services/flow_orchestration/execution_engine_crew_discovery.py`
  - Pattern to follow for gap analysis

### Critical Attributes Framework:
- **Location**: `backend/app/services/crewai_flows/tools/critical_attributes_tool/base.py`
- **22 Attributes**:
  - Infrastructure: hostname, environment, os_type, cpu_cores, memory_gb, storage_gb
  - Application: app_name, technology_stack, criticality, dependencies
  - Operational: owner, cost_center, backup_strategy, monitoring_status
  - Dependencies: app_dependencies, database_dependencies, integration_points
  - Performance: network_throughput_mbps, iops_requirements
  - Compliance: data_classification, compliance_requirements

## Step-by-Step Implementation (Fresh Session):

### Phase 1: Cleanup (Delete Old Code)
1. Delete branch `feature/implement-gap-analysis-detection-20251003`
2. Checkout main: `git checkout main && git pull origin main`
3. Create new branch: `git checkout -b refactor/lean-collection-gap-analysis`
4. Delete bloated files:
   ```bash
   rm backend/app/services/crewai_flows/crews/collection/gap_analysis_crew.py
   rm backend/app/services/ai_analysis/gap_analysis_agent.py
   rm backend/app/services/ai_analysis/gap_analysis_tasks.py
   rm backend/app/services/agents/questionnaire_dynamics_agent_crewai.py
   ```
5. Commit: `git commit -m "refactor: Delete bloated 3-agent gap analysis implementation"`

### Phase 2: Create Lean Service
1. Create new service: `backend/app/services/collection/gap_analysis_service.py`
2. Implement single persistent agent approach
3. Test with 2 assets manually
4. Commit: `git commit -m "feat: Implement lean single-agent gap analysis service"`

### Phase 3: Integration
1. Update `execution_engine_crew_collection.py` to use new service
2. Simplify `gap_persistence.py` to expect single format
3. Test end-to-end with Playwright
4. Commit: `git commit -m "feat: Integrate lean gap analysis into collection flow"`

### Phase 4: Verification
1. Run Playwright test: 3 assets selected → gaps detected → questionnaire shown
2. Verify database: `SELECT COUNT(*) FROM migration.collection_data_gaps`
3. Verify no errors in logs
4. Create PR with before/after comparison

## Questions to Address in Fresh Session:

1. **Should we keep gap_analysis_constants.py?**
   - Check if it has reusable constants
   - If it's just error handlers, delete it

2. **What about questionnaire_generator/ directory?**
   - Check if tools can be reused
   - Likely entire directory is bloat - delete

3. **Asset-based selection code from this branch?**
   - Commit `99a648d79` has good changes for asset vs application
   - Cherry-pick this commit into new branch before deleting old one

## Expected Outcome:

### Code Deletion:
- **Before**: ~1500 lines across 7 files
- **After**: ~200 lines in 1 file

### Performance:
- **Before**: 75+ seconds, 0 gaps detected, errors
- **After**: <30 seconds, gaps detected, questionnaire ready

### Maintainability:
- **Before**: 3 duplicate implementations, hard to debug
- **After**: 1 clear implementation, easy to test

---

## Prompt for Fresh Session:

**Title**: Refactor Collection Flow Gap Analysis - Delete Bloated 3-Agent Code, Implement Lean Single-Agent Architecture

**Initial Message**:
```
I need to completely redesign the collection flow gap analysis implementation. The current code is severely bloated with:
- 3-agent crew structure (gap_specialist, sixr_impact_assessor, gap_prioritizer)
- Duplicate implementations (gap_analysis_agent.py wraps gap_analysis_crew.py)
- Agents working with synthetic data instead of real database assets
- Separate questionnaire generation phase (should be atomic with gap analysis)

Current branch `feature/implement-gap-analysis-detection-20251003` has 7 commits of debug logging and workarounds for broken architecture. We need to:

1. DELETE this entire branch
2. DELETE all bloated files (gap_analysis_crew.py, gap_analysis_agent.py, etc.)
3. CREATE a lean single-agent implementation using TenantScopedAgentPool
4. Verify gaps persist to database and questionnaire generates correctly

Please read the detailed requirements in `/COLLECTION_FLOW_REDESIGN_PROMPT.md` and let's start with Phase 1: Cleanup.
```
