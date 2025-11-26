# GapAnalyzer vs IntelligentGapScanner Architecture

## Overview

The codebase has TWO separate gap analysis systems that serve DIFFERENT purposes. Understanding this prevents confusion when debugging readiness issues.

## GapAnalyzer (Assessment Readiness)

**Location**: `backend/app/services/gap_detection/gap_analyzer/`
**Purpose**: Determines "Is this asset ready for assessment?" (binary verdict)
**Used By**: `AssetReadinessService.analyze_asset_readiness()`, "Refresh Readiness" button

### 5 Inspectors (run in parallel via asyncio.gather):
1. **ColumnInspector** - Asset model direct columns
2. **EnrichmentInspector** - 7 enrichment tables (resilience, compliance_flags, vulnerabilities, tech_debt, dependencies, performance_metrics, cost_optimization)
3. **JSONBInspector** - `custom_attributes` and `technical_details` JSONB fields
4. **ApplicationInspector** - Canonical application metadata
5. **StandardsInspector** - Compliance standards (HIPAA, PCI-DSS, SOC2)

### Output
- `ComprehensiveGapReport` with overall_completeness, is_ready_for_assessment, critical_gaps, etc.
- Returns lists of field names (strings) for missing attributes

## IntelligentGapScanner (Questionnaire Generation)

**Location**: `backend/app/services/collection/gap_analysis/intelligent_gap_scanner/`
**Purpose**: Determines "What questions to show user?" by finding TRUE gaps (data not in ANY source)
**Used By**: Questionnaire generation during Collection Flow

### 6 Data Sources (checked sequentially per field):
1. **Standard columns** - `assets.{field}` direct attributes
2. **Custom attributes** - `custom_attributes` JSONB + `technical_details` JSONB
3. **Enrichment tables** - tech_debt, performance, cost tables
4. **Environment field** - Dedicated `assets.environment` check
5. **Canonical applications** - Via `CollectionFlowApplication` junction table
6. **Related assets** - Via `asset_dependencies` table

### Output
- `List[IntelligentGap]` with field_id, section, is_true_gap, confidence_score, data_found sources
- Returns structured `IntelligentGap` objects with source tracking

## Key Differences

| Feature | GapAnalyzer | IntelligentGapScanner |
|---------|-------------|----------------------|
| Purpose | Assessment readiness (binary) | Questionnaire generation (TRUE gaps only) |
| Related Assets | Only via dependencies inspector | ✅ Dedicated check |
| Environment Field | Not explicit | ✅ Dedicated check |
| Standards Compliance | ✅ StandardsInspector | ❌ Not checked |
| Confidence Scoring | Not tracked | ✅ Per-source confidence (0.70-1.0) |
| Data Source Tracking | Not tracked | ✅ Records which sources had data |

## The Mismatch Problem

GapAnalyzer might report "not ready" for an asset that IntelligentGapScanner found "no TRUE gaps" for:

**Example**: Asset has `environment` in `canonical_applications` table
- IntelligentGapScanner: ✅ Found data in source 5 → No gap for environment
- GapAnalyzer: ❌ ColumnInspector doesn't see it in `assets.environment` → Gap!

## Solution Pattern (November 2025)

In `readiness_gaps.py` (the "Refresh Readiness" endpoint), we check questionnaire completion BEFORE running GapAnalyzer:

```python
# Pre-fetch questionnaire completion status
assets_ready_by_questionnaire: set[UUID] = set()
for q in questionnaires:
    if q.completion_status == "completed":
        assets_ready_by_questionnaire.add(q.asset_id)
    elif q.completion_status == "failed":
        description = q.description or ""
        if "No questionnaires could be generated" in description:
            # IntelligentGapScanner found no TRUE gaps
            assets_ready_by_questionnaire.add(q.asset_id)

# In asset loop:
if asset.id in assets_ready_by_questionnaire:
    is_ready = True  # Override GapAnalyzer - trust IntelligentGapScanner
else:
    # Run GapAnalyzer for assets without questionnaire history
    readiness_result = await readiness_service.analyze_asset_readiness(...)
```

## When to Use Which

- **GapAnalyzer**: Initial readiness assessment, bulk asset filtering
- **IntelligentGapScanner**: Questionnaire generation (prevents false positive gaps)
- **Combined**: "Refresh Readiness" button uses questionnaire completion as override

## Future Consideration

These systems could potentially be unified:
- Add related assets check to GapAnalyzer's inspectors
- Add source tracking to GapAnalyzer
- Use IntelligentGapScanner's 6-source approach as the single source of truth

However, they serve different purposes (binary readiness vs questionnaire generation), so complete unification may not be desirable.

## Related Files
- `backend/app/services/gap_detection/gap_analyzer/orchestration.py` - GapAnalyzer main logic
- `backend/app/services/collection/gap_analysis/intelligent_gap_scanner/scanner.py` - IntelligentGapScanner
- `backend/app/api/v1/canonical_applications/router/readiness_gaps.py` - Refresh Readiness endpoint
- `backend/app/services/assessment/asset_readiness_service.py` - AssetReadinessService wrapper
