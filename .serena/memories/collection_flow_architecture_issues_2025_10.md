# Collection Flow Architecture Issues - October 2025

## Critical Issue #1: Asset Type Hardcoded to "application"

**Problem**: All assets (databases, servers, network devices) receive application-specific questions because `asset_type` is hardcoded at `generation.py:254`.

**Root Cause**:
```python
# File: backend/app/services/ai_analysis/questionnaire_generator/tools/generation.py:254
"asset_type": "application",  # ← HARDCODED DEFAULT
```

**Impact**:
- Database assets get questions about "programming frameworks" instead of "replication config"
- Server assets get application questions instead of CPU/RAM/storage questions
- 100% mismatch between asset type and question type

**Solution**: Add `_get_asset_type()` method (2-3 hours)

```python
async def _get_asset_type(self, asset_id: str) -> str:
    """Retrieve asset type from business_context table."""
    try:
        from app.models.business_context import BusinessContext
        from sqlalchemy import select

        result = await self.db.execute(
            select(BusinessContext.asset_type)
            .where(BusinessContext.asset_id == asset_id)
            .where(BusinessContext.client_account_id == self.client_account_id)
            .where(BusinessContext.engagement_id == self.engagement_id)
        )
        return result.scalar_one_or_none() or "application"
    except Exception as e:
        self.logger.error(f"Error fetching asset type: {e}")
        return "application"
```

Replace line 254:
```python
"asset_type": await self._get_asset_type(gap.get("asset_id")) if gap.get("asset_id") else "application",
```

**Benefit**: Activates existing `DatabaseQuestionsGenerator`, `ServerQuestionsGenerator`, `ApplicationQuestionsGenerator` that are already in codebase but never reached.

**Verification**: `backend/app/services/ai_analysis/questionnaire_generator/tools/question_generators.py` contains asset-specific generators (lines 9-235) that work correctly - they're just never used.

---

## Critical Issue #2: Enrichment Runs AFTER Gap Analysis

**Problem**: AutoEnrichmentPipeline runs in assessment flow (AFTER collection completes), so gap analysis doesn't see enriched data.

**Current Flow** (Broken):
```
Upload CSV (CPU, RAM, OS) → Gap Analysis → Marks CPU/RAM/OS as "gaps"
→ Questions generated → User manually enters data THAT WAS IN THE CSV
→ LATER: Enrichment runs (too late)
```

**Evidence**:
- Enrichment trigger: `backend/app/repositories/assessment_flow_repository/commands/flow_commands/creation.py:274-303`
- Collection phases: `backend/app/services/flow_configs/collection_flow_config.py:72-80`
  - Current: `asset_selection → gap_analysis → questionnaire_generation`
  - Missing: enrichment phase before gap_analysis

**Solution**: Move AutoEnrichmentPipeline to collection flow BEFORE gap_analysis

1. Create `backend/app/services/flow_configs/collection_phases/auto_enrichment_phase.py`
2. Update collection flow phases:
```python
phases = [
    get_asset_selection_phase(),
    get_auto_enrichment_phase(),      # ← ADD THIS
    get_gap_analysis_phase(),
    get_questionnaire_generation_phase(),
    ...
]
```
3. Update gap analysis to check 7 enrichment tables:
   - `asset_compliance_flags`
   - `asset_licenses`
   - `asset_vulnerabilities`
   - `asset_resilience`
   - `asset_dependencies`
   - `asset_product_links`
   - `asset_field_conflicts`

**Impact**: 50-80% fewer questions (data from CSV not re-asked)

---

## Architecture Insight: Questionnaire Generation is Deterministic

**Correction**: Questionnaire generation does NOT use LLMs (contrary to initial analysis).

**Evidence** (Per GPT5 verification):
- File: `backend/app/services/ai_analysis/questionnaire_generator/tools/generation.py:154-176`
- Builds sections from `data_gaps` deterministically
- No `multi_model_service` calls in questionnaire path
- **Note**: Enrichment agents DO use LLMs (`vulnerability_agent.py:101`)

**Implication**:
- Caching benefit is TIME and UX, NOT LLM cost reduction
- Still valuable: 90% time reduction for 100 identical assets
- Deduplication reduces repetitive UX across similar assets

---

## Assessment → Collection Feedback Loop: NOT IMPLEMENTED

**Verified Missing**:
- Tables: `assessment_data_requirements`, `re_collection_requests` do NOT exist
- Endpoints: `/assessment/{id}/trigger-re-collection` does NOT exist
- No mechanism for assessment to request missing data from collection

**Design Intent Found**:
- `assessment_flow_config.py:96` shows `"prerequisite_flows": ["discovery"]`
- Assessment phases would discover incomplete data, but can't send it back

**Implementation Needed**: Net-new tables, endpoints, and UI flow (32 hours estimated)

---

## Key Files Reference

### Question Generation:
- `backend/app/services/ai_analysis/questionnaire_generator/tools/generation.py` (main tool)
- `backend/app/services/ai_analysis/questionnaire_generator/tools/question_generators.py` (asset-specific)

### Flow Configuration:
- `backend/app/services/flow_configs/collection_flow_config.py` (phases)
- `backend/app/services/flow_configs/collection_phases/gap_analysis_phase.py` (gap detection)

### Enrichment:
- `backend/app/services/enrichment/auto_enrichment_pipeline.py` (main pipeline)
- `backend/app/repositories/assessment_flow_repository/commands/flow_commands/creation.py:274-303` (trigger)

### Data Import:
- `backend/app/api/v1/endpoints/data_import.py` (upload endpoint)
- `backend/app/services/data_import/import_storage_handler.py` (orchestrator)

---

## Implementation Priority

1. **Day 1** (2-3 hours): Fix asset type routing (quick win)
2. **Days 2-3** (16 hours): Fix enrichment timing
3. **Days 3-4** (16 hours): Implement questionnaire caching
4. **Day 5** (8 hours): Add batch deduplication

**Combined Result**: 70-90% reduction in user manual data entry

---

## Testing Commands

```bash
# After Phase 1 fix
docker exec -it migration_backend bash
cd backend && python -m pytest tests/backend/integration/test_questionnaire_generation.py -v -k "test_asset_type_routing"

# Verify in DB
docker exec -it migration_postgres psql -U postgres -d migration_db -c \
  "SELECT asset_id, asset_type FROM migration.business_context LIMIT 10;"
```

**Log Verification**:
```bash
docker logs migration_backend -f | grep "Using.*QuestionsGenerator"
# Should see: "Using DatabaseQuestionsGenerator" for databases
# NOT: "Using ApplicationQuestionsGenerator" for all assets
```
