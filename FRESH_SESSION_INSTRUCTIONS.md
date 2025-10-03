# Fresh Session Instructions - Collection Flow Redesign

## Quick Start Prompt for New Session:

```
I need to completely redesign the collection flow gap analysis. The current implementation is bloated with 3-agent crew structure that never worked.

Please read these 3 documents in order:
1. /COLLECTION_FLOW_REDESIGN_PROMPT.md - Full requirements
2. /BRANCH_CLEANUP_SUMMARY.md - What to delete
3. /FRESH_SESSION_INSTRUCTIONS.md - Step-by-step execution plan

Then execute Phase 1: Cherry-pick valuable commit and delete broken branch.
```

---

## Pre-Flight Checklist:

### ✅ Documents Created:
- [x] `/COLLECTION_FLOW_REDESIGN_PROMPT.md` - Complete requirements and architecture
- [x] `/BRANCH_CLEANUP_SUMMARY.md` - Analysis of commits to delete
- [x] `/FRESH_SESSION_INSTRUCTIONS.md` - This file (step-by-step)

### ✅ Key Findings:
- [x] Current branch: `feature/implement-gap-analysis-detection-20251003`
- [x] Commits on branch: 7 total (all can be deleted EXCEPT one to preserve)
- [x] Asset-based selection commit `99a648d79`: **NOT in main** - MUST cherry-pick before deleting
- [x] Bloated files identified: 4 primary files (~1500 lines to delete)

---

## Phase 1: Preserve Good Code, Delete Broken Branch

### Step 1.1: Create New Branch from Main
```bash
cd /Users/chocka/CursorProjects/migrate-ui-orchestrator/backend
git checkout main
git pull origin main
git checkout -b refactor/lean-collection-gap-analysis
```

### Step 1.2: Cherry-Pick Asset Migration Commit
```bash
# Cherry-pick ONLY the asset-based selection commit
git cherry-pick 99a648d79

# Expected result: Clean cherry-pick with asset migration changes
```

**What this preserves**:
- Frontend: Send `selected_asset_ids` instead of `selected_application_ids`
- Schema: Backward compatible field names
- Collection endpoint: Use `asset_ids` property
- Gap analysis: Support both field names (fallback logic)

### Step 1.3: Delete Old Branch Locally
```bash
git checkout main
git branch -D feature/implement-gap-analysis-detection-20251003
```

### Step 1.4: Delete Remote Branch (if exists)
```bash
# Check if remote branch exists
git ls-remote --heads origin feature/implement-gap-analysis-detection-20251003

# If it exists, delete it
git push origin --delete feature/implement-gap-analysis-detection-20251003
```

### Step 1.5: Return to New Branch
```bash
git checkout refactor/lean-collection-gap-analysis
git status
```

**Expected state**:
- On branch: `refactor/lean-collection-gap-analysis`
- 1 commit ahead of main (asset migration)
- Clean working directory

---

## Phase 2: Delete Bloated Files

### Step 2.1: Delete Primary Bloat (4 files)
```bash
cd /Users/chocka/CursorProjects/migrate-ui-orchestrator/backend

# Delete 3-agent crew implementation
rm app/services/crewai_flows/crews/collection/gap_analysis_crew.py

# Delete wrapper around crew
rm app/services/ai_analysis/gap_analysis_agent.py

# Delete task templates for 3-agent crew
rm app/services/ai_analysis/gap_analysis_tasks.py

# Delete separate questionnaire agent
rm app/services/agents/questionnaire_dynamics_agent_crewai.py
```

### Step 2.2: Review Questionnaire Generator Directory
```bash
# Check what's in this directory
ls -la app/services/ai_analysis/questionnaire_generator/

# Check file sizes to see if worth keeping
du -sh app/services/ai_analysis/questionnaire_generator/*
```

**Decision criteria**:
- If tools are reusable for new implementation: **Keep**
- If tightly coupled to old 3-agent structure: **Delete entire directory**

**Likely action**: Delete entire directory (new implementation will be simpler)

```bash
# If decided to delete:
rm -rf app/services/ai_analysis/questionnaire_generator/
```

### Step 2.3: Review Gap Analysis Constants
```bash
# Check what's in this file
cat app/services/ai_analysis/gap_analysis_constants.py | head -50
```

**Decision criteria**:
- If it contains critical attributes framework: **Keep**
- If it's just error handlers for 3-agent crew: **Delete**

**Likely action**: Keep (critical attributes framework is valuable)

### Step 2.4: Commit Deletions
```bash
git add -A
git commit -m "refactor: Delete bloated 3-agent gap analysis implementation

DELETED FILES:
- gap_analysis_crew.py (354 lines) - 3-agent crew boilerplate
- gap_analysis_agent.py (330 lines) - wrapper around crew
- gap_analysis_tasks.py (245 lines) - task templates
- questionnaire_dynamics_agent_crewai.py (150+ lines) - separate questionnaire agent
- questionnaire_generator/ (entire directory - tightly coupled to old structure)

REASON:
These files implement a fundamentally broken architecture:
- 3 agents (gap_specialist, sixr_impact_assessor, gap_prioritizer) running sequentially
- Agents work with synthetic/fabricated data instead of real database assets
- Separate questionnaire generation phase (should be atomic with gap analysis)
- Never successfully detected or persisted gaps

REPLACEMENT:
Will implement lean single-agent service using TenantScopedAgentPool (ADR-015)
in next commit.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Expected outcome**:
- ~1500 lines deleted across 4-5 files
- Clean slate for new implementation

---

## Phase 3: Create Lean Single-Agent Service

### Step 3.1: Create New Service File
```bash
# Create collection services directory if it doesn't exist
mkdir -p app/services/collection

# Create the new lean service
touch app/services/collection/gap_analysis_service.py
```

### Step 3.2: Implement Single-Agent Service
```python
# File: app/services/collection/gap_analysis_service.py
"""
Lean Gap Analysis Service - Single Persistent Agent
Uses TenantScopedAgentPool (ADR-015) for gap detection and questionnaire generation.
"""

import logging
from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID

logger = logging.getLogger(__name__)


class GapAnalysisService:
    """
    Lean gap analysis using single persistent agent.

    Replaces bloated 3-agent crew (gap_specialist, sixr_impact_assessor, gap_prioritizer)
    with direct asset comparison and single-task questionnaire generation.
    """

    def __init__(self, client_account_id: str, engagement_id: str):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def analyze_and_generate_questionnaire(
        self,
        selected_asset_ids: List[str],
        db: AsyncSession,
        automation_tier: str = "tier_2",
    ) -> Dict[str, Any]:
        """
        Single atomic operation: Load assets, detect gaps, generate questionnaire.

        Args:
            selected_asset_ids: UUIDs of assets selected for gap analysis
            db: Database session
            automation_tier: Automation tier for agent configuration

        Returns:
            {
                "gaps": {
                    "critical": [...],
                    "high": [...],
                    "medium": [...],
                    "low": [...]
                },
                "questionnaire": {
                    "sections": [...]
                },
                "summary": {
                    "total_gaps": int,
                    "assets_analyzed": int
                }
            }
        """
        try:
            # 1. Load REAL assets from database
            from app.models.asset import Asset

            asset_uuids = [
                UUID(aid) if isinstance(aid, str) else aid
                for aid in selected_asset_ids
            ]

            stmt = select(Asset).where(
                and_(
                    Asset.id.in_(asset_uuids),
                    Asset.client_account_id == str(self.client_account_id),
                    Asset.engagement_id == str(self.engagement_id),
                )
            )
            result = await db.execute(stmt)
            assets = result.scalars().all()

            if not assets:
                logger.warning("No assets found for gap analysis")
                return self._empty_result()

            logger.info(f"📦 Loaded {len(assets)} real assets for gap analysis")

            # 2. Get single persistent agent
            from app.services.persistent_agents.tenant_scoped_agent_pool import (
                TenantScopedAgentPool,
            )

            agent = await TenantScopedAgentPool.get_or_create_agent(
                client_id=self.client_account_id,
                engagement_id=self.engagement_id,
                agent_type="gap_analysis_specialist",
            )

            # 3. Create single task: analyze + generate questionnaire
            from crewai import Task

            task = Task(
                description=self._build_task_description(assets),
                agent=agent,
                expected_output="JSON with gaps and questionnaire structure",
            )

            # 4. Execute task
            logger.info("🤖 Executing single-agent gap analysis task")
            task_output = await task.execute_async()

            # 5. Parse result
            result_dict = self._parse_task_output(task_output)

            return result_dict

        except Exception as e:
            logger.error(f"Gap analysis failed: {e}", exc_info=True)
            return self._error_result(str(e))

    def _build_task_description(self, assets: List[Any]) -> str:
        """Build task description with REAL asset data."""
        # Import critical attributes
        from app.services.crewai_flows.tools.critical_attributes_tool.base import (
            CriticalAttributesDefinition,
        )

        attribute_mapping = CriticalAttributesDefinition.get_attribute_mapping()

        # Build asset summary
        asset_summary = []
        for asset in assets[:5]:  # Show first 5
            asset_summary.append({
                "id": str(asset.id),
                "name": asset.name,
                "type": asset.asset_type,
            })

        return f'''
Analyze REAL assets and generate questionnaire for missing critical attributes.

ASSETS TO ANALYZE ({len(assets)} total):
{asset_summary}

CRITICAL ATTRIBUTES FRAMEWORK (22 attributes):
{attribute_mapping}

YOUR TASK:
1. For each asset, compare against 22 critical attributes
2. Identify missing/null fields
3. Classify gaps by priority (critical/high/medium/low)
4. Generate questionnaire sections for missing fields

RETURN JSON:
{{
    "gaps": {{
        "critical": [
            {{
                "asset_id": "uuid",
                "field": "technology_stack",
                "type": "missing_field",
                "description": "Missing required field",
                "impact": "high"
            }}
        ]
    }},
    "questionnaire": {{
        "sections": [
            {{
                "section_id": "infrastructure",
                "title": "Infrastructure Details",
                "questions": [...]
            }}
        ]
    }},
    "summary": {{
        "total_gaps": 15,
        "assets_analyzed": {len(assets)}
    }}
}}
'''

    def _parse_task_output(self, task_output: Any) -> Dict[str, Any]:
        """Parse task output with proper error handling."""
        import json

        raw_output = task_output.raw if hasattr(task_output, "raw") else str(task_output)

        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            logger.warning("Task output not valid JSON, wrapping")
            return {"raw_output": raw_output, "gaps": {}, "questionnaire": {}}

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result when no assets found."""
        return {
            "gaps": {},
            "questionnaire": {},
            "summary": {"total_gaps": 0, "assets_analyzed": 0},
        }

    def _error_result(self, error: str) -> Dict[str, Any]:
        """Return error result."""
        return {
            "status": "error",
            "error": error,
            "gaps": {},
            "questionnaire": {},
        }
```

### Step 3.3: Commit New Service
```bash
git add app/services/collection/gap_analysis_service.py
git commit -m "feat: Implement lean single-agent gap analysis service

NEW FILE:
- gap_analysis_service.py (~200 lines) - Single persistent agent implementation

ARCHITECTURE:
- Uses TenantScopedAgentPool.get_or_create_agent() per ADR-015
- Loads REAL assets from database (not synthetic data)
- Single task: analyze gaps + generate questionnaire atomically
- Predictable JSON output (no multiple formats to parse)

BENEFITS:
- 87% code reduction (~1500 lines → ~200 lines)
- Works with real data from database
- Atomic operation (no separate questionnaire phase)
- Simple to test and debug
- Follows ADR-015 persistent agent pattern

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Phase 4: Integration

### Step 4.1: Update Execution Engine
```bash
# Edit: app/services/flow_orchestration/execution_engine_crew_collection.py
# Line 158: _execute_gap_analysis() method
```

**Changes needed**:
```python
# BEFORE (lines 158-442): 3-agent orchestration
async def _execute_gap_analysis(...):
    # Loads gap_analysis_agent.analyze_collection_gaps()
    # Which wraps gap_analysis_crew (3 agents)
    ...

# AFTER: Single service call
async def _execute_gap_analysis(
    self, agent_pool: Any, phase_input: Dict[str, Any]
) -> Dict[str, Any]:
    from app.services.collection.gap_analysis_service import GapAnalysisService
    from app.core.database import AsyncSessionLocal

    selected_asset_ids = phase_input.get("selected_asset_ids", [])

    async with AsyncSessionLocal() as db:
        service = GapAnalysisService(
            client_account_id=phase_input["client_account_id"],
            engagement_id=phase_input["engagement_id"],
        )

        result = await service.analyze_and_generate_questionnaire(
            selected_asset_ids=selected_asset_ids,
            db=db,
            automation_tier=phase_input.get("automation_tier", "tier_2"),
        )

        # Persist gaps
        from app.services.flow_orchestration.gap_persistence import persist_collection_gaps

        gaps_count, summary = await persist_collection_gaps(
            db=db,
            flow_id=phase_input["flow_id"],
            gap_results=result,
            client_account_id=phase_input["client_account_id"],
            engagement_id=phase_input["engagement_id"],
        )

        return {
            "phase": "gap_analysis",
            "status": "completed",
            "gaps_detected": gaps_count,
            "gap_analysis_summary": summary,
        }
```

### Step 4.2: Simplify Gap Persistence
```bash
# Edit: app/services/flow_orchestration/gap_persistence.py
# Remove lines 100-159: Fallback parsing for multiple formats
```

**Simplification**:
```python
# BEFORE: Complex fallback parsing
task_results = gap_results.get("task_results", {})
if not task_results:
    # Try alternative structures...
    if "gaps" in gap_results:
        task_results = {"task_0": {"gaps": gap_results["gaps"]}}
    elif "missing_critical_fields" in gap_results:
        # Convert...
    ...

# AFTER: Simple direct access
gaps_by_priority = gap_results.get("gaps", {})
# That's it - predictable structure
```

### Step 4.3: Commit Integration
```bash
git add app/services/flow_orchestration/execution_engine_crew_collection.py
git add app/services/flow_orchestration/gap_persistence.py
git commit -m "feat: Integrate lean gap analysis service into collection flow

UPDATED FILES:
- execution_engine_crew_collection.py: Replace 3-agent orchestration with single service call
- gap_persistence.py: Remove complex fallback parsing (no longer needed)

CHANGES:
- _execute_gap_analysis() now calls GapAnalysisService directly
- No more gap_analysis_agent wrapper
- No more gap_analysis_crew creation
- Simplified gap_persistence to expect single predictable format

RESULT:
- Cleaner code flow
- Easier to debug
- Predictable data structures

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Phase 5: Testing & Verification

### Step 5.1: Run Playwright Test
```bash
# Use qa-playwright-tester agent
Task: Test collection flow gap analysis end-to-end

Steps:
1. Navigate to /collection
2. Start new collection flow
3. Select 2-3 assets (different types: server, database, application)
4. Proceed to gap analysis phase
5. Wait for completion (<30 seconds expected)
6. Verify gaps detected message
7. Verify questionnaire displayed
8. Take screenshot
```

### Step 5.2: Verify Database
```bash
# Check gaps persisted
docker exec -it migration_postgres psql -U postgres -d migration_db -c "
SELECT
    COUNT(*) as total_gaps,
    gap_type,
    gap_category,
    priority
FROM migration.collection_data_gaps
GROUP BY gap_type, gap_category, priority
ORDER BY priority DESC;
"

# Expected: Multiple rows with gap counts

# Check questionnaire created
docker exec -it migration_postgres psql -U postgres -d migration_db -c "
SELECT
    id,
    title,
    array_length(target_gaps, 1) as gaps_count,
    completion_status
FROM migration.adaptive_questionnaires
ORDER BY created_at DESC
LIMIT 1;
"

# Expected: 1 row with new questionnaire
```

### Step 5.3: Check Backend Logs
```bash
docker logs migration_backend --tail 100 | grep -E "gap_analysis|GapAnalysisService"

# Expected logs:
# "📦 Loaded X real assets for gap analysis"
# "🤖 Executing single-agent gap analysis task"
# "💾 Persisted X new gaps"
# NO errors about 'Agent' object has no attribute 'get'
```

---

## Success Criteria Checklist:

### ✅ Code Quality:
- [ ] Old branch deleted (feature/implement-gap-analysis-detection-20251003)
- [ ] Asset migration commit preserved (cherry-picked to new branch)
- [ ] ~1500 lines deleted (4-5 bloated files)
- [ ] ~200 lines added (lean service)
- [ ] Net reduction: ~1300 lines

### ✅ Functionality:
- [ ] Gaps detected and persisted to database
- [ ] Questionnaire generated with specific missing fields
- [ ] No 'Agent' object errors in logs
- [ ] Execution time <30 seconds for 2-3 assets
- [ ] Frontend displays questionnaire correctly

### ✅ Architecture:
- [ ] Uses TenantScopedAgentPool (ADR-015 compliance)
- [ ] Single persistent agent (no crew orchestration)
- [ ] Loads real assets from database
- [ ] Atomic gap analysis + questionnaire generation
- [ ] Predictable JSON output structure

---

## Rollback Plan (If Needed):

If new implementation has issues:

```bash
# Restore old branch
git checkout feature/implement-gap-analysis-detection-20251003

# Or revert commits on new branch
git checkout refactor/lean-collection-gap-analysis
git log --oneline
git revert <commit-hash>
```

**BUT**: Don't rollback prematurely! The old code NEVER worked. Debugging new lean code will be MUCH faster than fixing broken 3-agent structure.

---

## Estimated Timeline:

- **Phase 1** (Cherry-pick & delete): 10 minutes
- **Phase 2** (Delete files): 5 minutes
- **Phase 3** (Create service): 30-45 minutes
- **Phase 4** (Integration): 30 minutes
- **Phase 5** (Testing): 20-30 minutes

**Total**: 2-3 hours (vs 10+ hours debugging broken architecture)

---

## Final Notes:

1. **Don't overthink it** - The new service is intentionally simple
2. **Test incrementally** - Commit after each phase
3. **Trust the architecture** - TenantScopedAgentPool IS the right pattern
4. **Focus on data** - Load REAL assets, compare REAL fields
5. **Keep it lean** - Resist urge to add back complexity

**Remember**: We're replacing 1500 lines of broken code with 200 lines of working code. If it seems too simple, that's because the old code was over-engineered!

🚀 **Ready to start fresh!**
