# ADR-037 E2E Test Report - CRITICAL BUGS DISCOVERED

## Test Execution Date
2025-11-24 19:30 EST

## Test Status
**BLOCKED - CRITICAL BUGS PREVENT E2E TESTING**

## Executive Summary
The ADR-037 Intelligent Gap Detection and Questionnaire Generation implementation (#1109) is **BLOCKED** from E2E testing due to critical bugs in the `IntelligentGapScanner` data loader module. Testing cannot proceed until these bugs are resolved.

---

## Critical Bugs Discovered

### BUG #1: Schema Mismatch - Invalid WHERE Clause Filtering
**Severity**: CRITICAL (P0)
**File**: `/backend/app/services/collection/gap_analysis/intelligent_gap_scanner/data_loaders.py`
**Lines**: 47-75 (all enrichment table queries)

#### Root Cause
The data loader attempts to filter enrichment tables by `client_account_id` and `engagement_id` columns that **DO NOT EXIST** in these tables.

#### Database Schema Evidence
```sql
-- asset_tech_debt table (NO tenant columns)
\d migration.asset_tech_debt
Columns: id, asset_id, tech_debt_score, modernization_priority, code_quality_score, debt_items, ...
Missing: client_account_id, engagement_id

-- asset_performance_metrics table (NO tenant columns)
\d migration.asset_performance_metrics
Columns: id, asset_id, cpu_utilization_avg, cpu_utilization_peak, ...
Missing: client_account_id, engagement_id

-- asset_cost_optimization table (NO tenant columns)
\d migration.asset_cost_optimization
Columns: id, asset_id, monthly_cost_usd, annual_cost_usd, ...
Missing: client_account_id, engagement_id
```

#### Incorrect Code (Lines 47-51)
```python
# ❌ WRONG - AssetTechDebt has NO client_account_id or engagement_id columns
stmt_tech = select(AssetTechDebt).where(
    AssetTechDebt.asset_id == asset_id,
    AssetTechDebt.client_account_id == self.client_account_id,  # ❌ AttributeError
    AssetTechDebt.engagement_id == self.engagement_id,          # ❌ AttributeError
)
```

#### Error Log Evidence
```
2025-11-25 00:13:47,777 - ERROR - Background generation failed
AttributeError: type object 'AssetTechDebt' has no attribute 'client_account_id'
```

#### Correct Fix
**Option 1: Remove Tenant Filtering (RECOMMENDED)**
```python
# ✅ CORRECT - asset_id uniquely identifies the asset
# Tenant context already validated when Asset was loaded
stmt_tech = select(AssetTechDebt).where(
    AssetTechDebt.asset_id == asset_id
)
```

**Option 2: Join Through Asset Table**
```python
# ✅ ALTERNATIVE - Join through Asset for explicit tenant validation
stmt_tech = (
    select(AssetTechDebt)
    .join(Asset, AssetTechDebt.asset_id == Asset.id)
    .where(
        AssetTechDebt.asset_id == asset_id,
        Asset.client_account_id == self.client_account_id,
        Asset.engagement_id == self.engagement_id,
    )
)
```

**Recommendation**: Use Option 1 (simpler, more efficient) since:
1. `asset_id` is a foreign key to `assets.id` with `ON DELETE CASCADE`
2. The Asset object passed to `scan_gaps()` is already tenant-validated
3. `UNIQUE CONSTRAINT` on `asset_id` ensures one enrichment record per asset
4. Simpler query = better performance

#### Files Affected
- `/backend/app/services/collection/gap_analysis/intelligent_gap_scanner/data_loaders.py` (lines 47-75)
  - `load_enrichment_data()` method (3 queries: tech_debt, performance, cost)

---

### BUG #2: Field Name Mismatch - Invalid Attribute Access
**Severity**: CRITICAL (P0)
**File**: `/backend/app/services/collection/gap_analysis/intelligent_gap_scanner/data_loaders.py`
**Lines**: 54-80

#### Root Cause
The data loader attempts to access fields that **DO NOT EXIST** in the enrichment model classes.

#### Schema vs Code Mismatch

**AssetTechDebt Model** (Lines 54-56)
```python
# ❌ Code tries to access:
enrichment["resilience_tier"] = tech_debt.resilience_tier
enrichment["code_quality_score"] = tech_debt.code_quality_score

# ✅ Actual model fields (from asset_enrichments.py):
# - tech_debt_score (Float)
# - modernization_priority (String: low/medium/high/critical)
# - code_quality_score (Float) ✅ This one exists!
# - debt_items (JSONB)
```

**AssetPerformanceMetrics Model** (Lines 66-68)
```python
# ❌ Code tries to access:
enrichment["avg_response_time_ms"] = performance.avg_response_time_ms  # ❌ Doesn't exist
enrichment["peak_cpu_percent"] = performance.peak_cpu_percent          # ❌ Doesn't exist

# ✅ Actual model fields:
# - cpu_utilization_avg (Float)
# - cpu_utilization_peak (Float)
# - memory_utilization_avg (Float)
# - memory_utilization_peak (Float)
# - disk_iops_avg (Integer)
# - network_throughput_mbps (Float)
```

**AssetCostOptimization Model** (Lines 79-80)
```python
# ❌ Code tries to access:
enrichment["estimated_monthly_cost"] = cost.estimated_monthly_cost              # ❌ Doesn't exist
enrichment["rightsizing_recommendation"] = cost.rightsizing_recommendation      # ❌ Doesn't exist

# ✅ Actual model fields:
# - monthly_cost_usd (Float)
# - annual_cost_usd (Float)
# - optimization_potential_pct (Float)
# - optimization_opportunities (JSONB)
```

#### Correct Fix
```python
# AssetTechDebt - FIXED
if tech_debt:
    enrichment["tech_debt_score"] = tech_debt.tech_debt_score
    enrichment["modernization_priority"] = tech_debt.modernization_priority
    enrichment["code_quality_score"] = tech_debt.code_quality_score
    enrichment["debt_items"] = tech_debt.debt_items

# AssetPerformanceMetrics - FIXED
if performance:
    enrichment["cpu_utilization_avg"] = performance.cpu_utilization_avg
    enrichment["cpu_utilization_peak"] = performance.cpu_utilization_peak
    enrichment["memory_utilization_avg"] = performance.memory_utilization_avg
    enrichment["memory_utilization_peak"] = performance.memory_utilization_peak

# AssetCostOptimization - FIXED
if cost:
    enrichment["monthly_cost_usd"] = cost.monthly_cost_usd
    enrichment["annual_cost_usd"] = cost.annual_cost_usd
    enrichment["optimization_potential_pct"] = cost.optimization_potential_pct
    enrichment["optimization_opportunities"] = cost.optimization_opportunities
```

---

## Impact Analysis

### Functional Impact
- **Questionnaire Generation**: COMPLETELY BROKEN - All collection flows fail at gap analysis phase
- **Intelligent Gap Detection**: NON-FUNCTIONAL - Cannot load enrichment data
- **ADR-037 Implementation**: UNTESTABLE - E2E workflow blocked

### User Impact
- **New Collection Flows**: FAIL with "Background generation failed" error
- **Existing Collection Flows**: Cannot progress past gap analysis phase
- **Error Visibility**: Backend logs show `AttributeError`, frontend shows infinite loading

### Production Readiness
**PR #1109 is NOT PRODUCTION-READY**
- Zero functional testing performed (blocked by bugs)
- Zero performance validation (blocked by bugs)
- Zero cost reduction validation (blocked by bugs)

---

## Test Environment Details

### Docker Services Status
```
migration_backend   - ✅ UP (22 minutes, port 8000)
migration_frontend  - ✅ UP (29 minutes, port 8081)
migration_postgres  - ✅ UP (healthy, port 5433)
migration_redis     - ✅ UP (healthy, port 6379)
```

### Backend Logs Evidence
```
2025-11-25 00:13:47,777 - ERROR - Background generation failed for flow 54294a0f-7c65-4845-974e-bc6612d8565f
Traceback (most recent call last):
  File "/app/app/services/collection/gap_analysis/intelligent_gap_scanner/scanner.py", line 87, in scan_gaps
    enrichment_data = await self.data_loaders.load_enrichment_data(asset.id)
  File "/app/app/services/collection/gap_analysis/intelligent_gap_scanner/data_loaders.py", line 49, in load_enrichment_data
    AssetTechDebt.client_account_id == self.client_account_id,
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: type object 'AssetTechDebt' has no attribute 'client_account_id'
```

### Failed Flow Instance
- **Flow ID**: `54294a0f-7c65-4845-974e-bc6612d8565f`
- **Client**: Demo Corporation (`11111111-1111-1111-1111-111111111111`)
- **Engagement**: `22222222-2222-2222-2222-222222222222`
- **Failure Phase**: Gap Analysis (enrichment data loading)
- **Questionnaire Status**: `failed` (in database)

---

## Root Cause Analysis

### Why These Bugs Exist

1. **Modularization Without Schema Validation**
   - `data_loaders.py` was extracted from main scanner during Issue #1111
   - No database schema validation during modularization
   - Assumed enrichment tables had tenant columns (they don't)

2. **Model-Schema Mismatch**
   - Field names in code don't match SQLAlchemy model definitions
   - No type checking or runtime validation
   - Suggests copy-paste from different schema version

3. **Missing Integration Tests**
   - No tests for `data_loaders.py` module
   - No database integration tests for enrichment queries
   - Unit tests wouldn't catch schema mismatches

### Architectural Context
Enrichment tables (`asset_tech_debt`, `asset_performance_metrics`, `asset_cost_optimization`) follow a **denormalized pattern**:
- **NO direct tenant columns** (no `client_account_id`, `engagement_id`)
- **Tenant isolation via foreign key**: `asset_id → assets.id` (which has tenant columns)
- **Unique constraint**: One enrichment record per asset (`UNIQUE` on `asset_id`)
- **Cascade delete**: `ON DELETE CASCADE` ensures data integrity

This is a **valid architectural pattern** - tenant scoping is inherited through the Asset relationship. The bug is in the data loader assuming direct tenant columns.

---

## Recommended Actions

### Immediate (P0 - Before E2E Testing)
1. **Fix BUG #1**: Remove invalid tenant filtering from enrichment queries
2. **Fix BUG #2**: Correct field names to match actual model definitions
3. **Verify Fix**: Run single collection flow through gap analysis phase
4. **Add Integration Test**: Test `data_loaders.py` against real database schema

### Before Production Merge (P1)
5. **Full E2E Test**: Execute comprehensive ADR-037 test plan (this document)
6. **Performance Validation**: Verify <15 second questionnaire generation target
7. **Cost Validation**: Verify 65% cost reduction vs baseline
8. **Error Handling**: Add try/except for missing enrichment data (graceful degradation)

### Post-Merge (P2)
9. **Schema Validation Tests**: Add SQLAlchemy model reflection tests
10. **Pre-commit Hook**: Add mypy type checking for SQLAlchemy queries
11. **Documentation**: Update ADR-037 with enrichment table architecture

---

## E2E Test Plan (Once Bugs Fixed)

### Phase 1: Collection Flow Creation
- [ ] Navigate to `http://localhost:8081`
- [ ] Login as demo user
- [ ] Create NEW collection flow
- [ ] Select 3 assets (mix of app servers and databases)
- [ ] Capture collection flow ID

### Phase 2: Gap Analysis Execution
- [ ] Execute gap analysis phase
- [ ] Monitor backend logs for intelligent gap scanning
- [ ] Verify gap analysis completes in <5 seconds
- [ ] Verify TRUE gaps identified (20-40% reduction from all fields)
- [ ] Capture screenshot of gap analysis results

### Phase 3: Questionnaire Generation
- [ ] Navigate to Questionnaire phase
- [ ] Monitor backend logs for one-time data awareness map creation
- [ ] Verify NO UUID errors ("Collection flow not found")
- [ ] Verify questionnaires displayed (no infinite loading)
- [ ] Verify questions are migration-focused and contextual
- [ ] Capture screenshot of questionnaire display

### Phase 4: Database Persistence
- [ ] Query `collection_flow_questionnaires` table
- [ ] Verify questionnaires persisted with correct `collection_flow_id`
- [ ] Verify question counts match displayed UI
- [ ] Verify sections correspond to TRUE gaps only

### Phase 5: Performance & Cost Validation
- [ ] Measure questionnaire generation time (target: <15s)
- [ ] Query `llm_usage_logs` for token usage
- [ ] Calculate cost per question (target: $0.006)
- [ ] Compare to ADR-037 performance targets

### Phase 6: Error Analysis
- [ ] Check browser console (no JavaScript errors)
- [ ] Check backend logs (no UUID mismatch errors)
- [ ] Check database (no orphaned questionnaires)

---

## Success Criteria (Post-Fix)

### Functional
- [ ] Collection flow created successfully
- [ ] Gap analysis completes without errors
- [ ] Questionnaires generated and visible in UI
- [ ] Questionnaires persisted to database
- [ ] No backend exceptions or errors

### Performance
- [ ] Gap analysis <5 seconds
- [ ] Questionnaire generation <15 seconds (76% faster than baseline)
- [ ] TRUE gap reduction 20-40% vs all fields

### Cost
- [ ] Token usage tracked in `llm_usage_logs`
- [ ] Cost per question <$0.006 (65% reduction vs $0.017 baseline)

---

## Verdict

**ADR-037 Implementation (#1109): NOT PRODUCTION-READY**

**Blocker Bugs**: 2 critical (P0) bugs prevent any E2E testing
**Code Quality**: Schema validation failure, model-code mismatch
**Testing Status**: UNTESTABLE until bugs fixed
**Recommendation**: **DO NOT MERGE** until bugs resolved and full E2E test passed

---

## Next Steps

1. **python-crewai-fastapi-expert agent**: Fix `data_loaders.py` bugs
2. **qa-playwright-tester agent**: Execute full E2E test plan
3. **Project lead**: Review test results and approve/reject PR #1109

---

## Files Referenced

### Bug Locations
- `/backend/app/services/collection/gap_analysis/intelligent_gap_scanner/data_loaders.py` (lines 47-80)

### Schema Definitions
- `/backend/app/models/asset_enrichments.py` (AssetTechDebt, AssetPerformanceMetrics, AssetCostOptimization)

### Database Tables
- `migration.asset_tech_debt`
- `migration.asset_performance_metrics`
- `migration.asset_cost_optimization`
- `migration.assets` (tenant columns: client_account_id, engagement_id)

### Related PRs
- **PR #1109**: ADR-037 Intelligent Gap Detection Implementation (BLOCKED)
- **Issue #1111**: IntelligentGapScanner Modularization (introduced bugs)

---

**Report Generated**: 2025-11-24 19:45 EST
**Generated By**: qa-playwright-tester (Claude Code QA Agent)
**Report Version**: 1.0
