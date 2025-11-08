# Shared Inspector Architecture Design

**Version**: 1.0
**Date**: 2025-11-08
**Status**: Design Phase
**Related Issue**: [#980](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/980)

---

## Executive Summary

This document defines the architecture for a **Shared Inspector System** that enables both **ProgrammaticGapScanner** and **IncrementalGapAnalyzer** to intelligently detect data gaps across multiple layers (columns, enrichments, JSONB, standards). The new system replaces the current 22-attribute hardcoded approach with a flexible, context-aware, multi-layer detection system.

**Key Design Principles**:
1. **Composition over duplication**: Shared inspector interfaces used by both gap scanners
2. **Tenant scoping enforced**: All queries include `client_account_id` and `engagement_id`
3. **Context-aware requirements**: Gap detection adapts to asset type, 6R strategy, compliance scope
4. **Async-first architecture**: All inspectors are `async def` for database compatibility
5. **Feature flag controlled**: Gradual rollout with backward compatibility

---

## 1. Current State Audit

### 1.1 GPT-5 Review Recommendations (ALL ACCEPTED)

**GPT-5 performed a comprehensive review of the solution design in Issue #980. All 8 recommendations have been incorporated into this architecture:**

1. ✅ **Tenant Scoping**: Add `client_account_id` to all queries and inspectors
2. ✅ **Reuse/Compose**: Extract inspectors as shared modules; compose with existing `ProgrammaticGapScanner` and `IncrementalGapAnalyzer`
3. ✅ **Async Consistency**: Make ALL inspectors `async def`, not sync
4. ✅ **Agentic Refinement**: Add optional LLM-based semantic gap detection via `multi_model_service`
5. ✅ **Service Layer Integration**: Use `AssessmentFlowChildService` instead of direct DB access
6. ✅ **Frontend Compatibility**: Provide response shim for gradual rollout
7. ✅ **Standards Templates**: Populate `client_account_id` in template loader
8. ✅ **JSON Safety**: Clamp completeness scores to avoid NaN/Infinity

### 1.2 Existing Gap Detection Locations

| Component | File | Lines | Responsibility |
|-----------|------|-------|---------------|
| Assessment Helpers | `backend/app/api/v1/master_flows/assessment/helpers.py` | 13-66 | Checks 22 hardcoded attributes |
| Critical Attributes | `backend/app/services/collection/critical_attributes.py` | 33-562 | Defines 22 critical attributes with asset-type awareness |
| Programmatic Scanner | `backend/app/services/collection/gap_scanner/scanner.py` | 27-303 | Orchestrates gap scanning with tenant scoping ✅ |
| Incremental Analyzer | `backend/app/services/collection/incremental_gap_analyzer.py` | 58-423 | Recalculates gaps after bulk imports ✅ |

**Key Discovery**: `ProgrammaticGapScanner` already has excellent tenant scoping and uses `CriticalAttributesDefinition` with asset-type awareness. We'll refactor it to use the new inspectors rather than replace it.

### 1.3 Problems with Current Implementation

**Assessment Helpers (`helpers.py:13-66`)**:
```python
def get_missing_critical_attributes(asset: Any) -> List[str]:
    critical_attrs = [
        "asset_name", "technology_stack", ..., "known_vulnerabilities"
    ]  # ❌ Only 22 hardcoded attributes!

    for attr in critical_attrs:
        value = getattr(asset, attr, None)  # ❌ Only checks SQLAlchemy columns!
        if value is None:
            missing.append(attr)
```

**What It Misses**:
- ❌ 7 enrichment tables (AssetResilience, AssetComplianceFlags, etc.)
- ❌ JSONB fields (custom_attributes, technical_details, metadata)
- ❌ CanonicalApplication metadata
- ❌ Architecture standards validation
- ❌ Context-specific requirements (6R, compliance, criticality)

**ProgrammaticGapScanner**: Uses `CriticalAttributesDefinition` with asset-type awareness (✅ good!) but only checks columns.

**IncrementalGapAnalyzer**: Analyzes questionnaire responses but doesn't know what data exists outside questionnaires.

---

## 2. Proposed Architecture

### 2.1 Shared Inspector Interfaces

All gap detection will use **5 specialized inspectors** orchestrated by a central **GapAnalyzer** service:

```
┌───────────────────────────────────────────────────────────────────┐
│                     GapAnalyzer Service                            │
│                  (Orchestrates all inspectors)                     │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Column     │  │ Enrichment   │  │    JSONB     │           │
│  │  Inspector   │  │  Inspector   │  │  Inspector   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐                              │
│  │ Application  │  │  Standards   │                              │
│  │  Inspector   │  │  Inspector   │                              │
│  └──────────────┘  └──────────────┘                              │
│                                                                    │
│                  ┌──────────────────┐                             │
│                  │  Requirements    │                             │
│                  │     Engine       │                             │
│                  │  (Context-Aware) │                             │
│                  └──────────────────┘                             │
└───────────────────────────────────────────────────────────────────┘
```

### 2.2 Inspector Interface

All inspectors implement a common async interface:

```python
from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

class BaseInspector(ABC):
    """Base interface for all gap inspectors (GPT-5 approved)."""

    @abstractmethod
    async def inspect(
        self,
        asset: Asset,
        application: Optional[CanonicalApplication],
        requirements: DataRequirements,
        client_account_id: str,  # ← CRITICAL: Tenant scoping (GPT-5 Rec #1)
        engagement_id: str,      # ← CRITICAL: Tenant scoping (GPT-5 Rec #1)
        db: Optional[AsyncSession] = None,  # Only for standards inspector
    ) -> InspectorReport:
        """
        Inspect asset for gaps in this layer.

        IMPORTANT: This MUST be async def (GPT-5 Rec #3). Never sync.

        Args:
            asset: Asset to inspect
            application: Optional CanonicalApplication (for application inspector)
            requirements: Context-aware requirements from RequirementsEngine
            client_account_id: Tenant client account UUID (GPT-5 Rec #1)
            engagement_id: Engagement UUID (GPT-5 Rec #1)
            db: Async database session (for standards inspector)

        Returns:
            InspectorReport with gaps, completeness score, recommendations
        """
        pass
```

### 2.3 Inspector Responsibilities

| Inspector | Data Layer | Tenant Scoping | DB Required | Performance Target |
|-----------|-----------|----------------|-------------|-------------------|
| **ColumnInspector** | Asset SQLAlchemy columns | N/A (in-memory) | No | <10ms per asset |
| **EnrichmentInspector** | 7 enrichment tables | Eager-loaded relationships | No | <20ms per asset |
| **JSONBInspector** | JSONB fields (custom_attributes, etc.) | N/A (in-memory) | No | <10ms per asset |
| **ApplicationInspector** | CanonicalApplication metadata | N/A (passed in) | No | <10ms per asset |
| **StandardsInspector** | EngagementArchitectureStandard | Query with tenant scoping | **Yes** | <50ms per asset |

---

## 3. Module Structure

```
backend/app/services/gap_detection/
├── __init__.py                             # Public exports
├── schemas.py                              # Pydantic models for reports
├── gap_analyzer.py                         # Main orchestrator service
├── inspectors/
│   ├── __init__.py                         # Inspector exports
│   ├── base.py                             # BaseInspector interface
│   ├── column_inspector.py                 # Checks Asset columns
│   ├── enrichment_inspector.py             # Checks 7 enrichment tables
│   ├── jsonb_inspector.py                  # Traverses JSONB fields
│   ├── application_inspector.py            # Validates CanonicalApplication
│   └── standards_inspector.py              # Validates architecture standards
└── requirements/
    ├── __init__.py                         # Requirements exports
    ├── requirements_engine.py              # Context-aware requirements
    └── matrix.py                           # Requirements matrix definitions
```

---

## 4. Data Flow & Composition

### 4.1 How ProgrammaticGapScanner Will Use Inspectors

**Current (before refactor)**:
```python
# scanner.py:182-200 (simplified)
for asset in assets:
    asset_type = getattr(asset, "asset_type", "other")
    attribute_mapping = CriticalAttributesDefinition.get_attributes_by_asset_type(asset_type)
    asset_gaps = await identify_gaps_for_asset(asset, attribute_mapping, ...)
    all_gaps.extend(asset_gaps)
```

**After refactor**:
```python
from app.services.gap_detection import GapAnalyzer

gap_analyzer = GapAnalyzer()

for asset in assets:
    # Get application if exists
    application = await get_application_for_asset(asset, db)

    # Run comprehensive gap analysis
    gap_report = await gap_analyzer.analyze_asset(
        asset=asset,
        application=application,
        client_account_id=client_uuid,
        engagement_id=engagement_uuid,
        db=db,
    )

    # Convert ComprehensiveGapReport to CollectionDataGap format
    collection_gaps = convert_to_collection_gaps(gap_report)
    all_gaps.extend(collection_gaps)
```

**Benefits**:
- ✅ Replaces hardcoded 22 attributes with multi-layer detection
- ✅ Reuses all inspector logic
- ✅ Maintains backward compatibility (same CollectionDataGap format)

### 4.2 How AssessmentFlowChildService Will Use GapAnalyzer

**New service method**:
```python
# backend/app/services/assessment_flow/assessment_child_flow_service.py

async def get_asset_readiness_with_gaps(
    self,
    assessment_flow_id: str,
    client_account_id: str,
    engagement_id: str,
) -> List[AssetReadinessDetail]:
    """
    Get asset readiness with comprehensive gap analysis.

    Returns:
        List of AssetReadinessDetail with:
        - completeness_score: 0.0-1.0
        - assessment_ready: bool
        - gap_summary: {column_gaps, enrichment_gaps, jsonb_gaps, standards_violations}
        - missing_attributes: categorized missing data
        - blocking_gaps: mandatory items preventing assessment
    """
    gap_analyzer = GapAnalyzer()

    # Load assets for this assessment flow
    assets = await self._get_assets_for_flow(assessment_flow_id)

    readiness_details = []
    for asset in assets:
        application = await self._get_application_for_asset(asset)

        # Run gap analysis
        gap_report = await gap_analyzer.analyze_asset(
            asset=asset,
            application=application,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            db=self.db,
        )

        # Convert to AssetReadinessDetail format
        readiness_details.append(
            self._convert_to_readiness_detail(asset, gap_report)
        )

    return readiness_details
```

---

## 5. Context-Aware Requirements Engine

### 5.1 Requirements Matrix

**Requirement Dimensions**:
1. **Asset Type**: server, database, application, network, storage, container
2. **6R Strategy**: rehost, replatform, refactor, repurchase, retire, retain
3. **Compliance Scope**: PCI-DSS, HIPAA, SOC2, GDPR, ISO27001
4. **Criticality Tier**: tier_1_critical, tier_2_important, tier_3_standard

**Matrix Structure** (`requirements/matrix.py`):
```python
ASSET_TYPE_REQUIREMENTS = {
    "server": {
        "required_columns": ["cpu_cores", "memory_gb", "storage_gb", "operating_system"],
        "required_enrichments": ["resilience"],
        "required_jsonb_keys": {"custom_attributes": ["environment"]},
        "priority_weights": {"columns": 0.5, "enrichments": 0.3, "jsonb": 0.2},
    },
    "application": {
        "required_columns": ["technology_stack", "architecture_pattern"],
        "required_enrichments": ["resilience", "compliance_flags"],
        "required_jsonb_keys": {"technical_details": ["api_endpoints", "dependencies"]},
        "priority_weights": {"columns": 0.3, "enrichments": 0.3, "jsonb": 0.4},
    },
    # ... more asset types
}

SIX_R_STRATEGY_REQUIREMENTS = {
    "rehost": {
        "required_columns": ["cpu_cores", "memory_gb", "storage_gb"],
        "required_enrichments": ["resilience"],
    },
    "refactor": {
        "required_columns": ["technology_stack", "architecture_pattern", "code_quality"],
        "required_enrichments": ["tech_debt", "resilience"],
    },
    # ... more strategies
}

COMPLIANCE_REQUIREMENTS = {
    "PCI-DSS": {
        "required_standards": ["Encryption at Rest", "Network Segmentation"],
        "mandatory_enrichments": ["compliance_flags"],
    },
    # ... more compliance scopes
}
```

### 5.2 Requirements Merging Algorithm

```python
class RequirementsEngine:
    @lru_cache(maxsize=256)
    def get_requirements(
        self,
        asset_type: str,
        six_r_strategy: Optional[str] = None,
        compliance_scopes: Optional[Tuple[str, ...]] = None,
        criticality: Optional[str] = None,
    ) -> DataRequirements:
        """
        Get context-aware requirements for an asset.

        Returns:
            DataRequirements with:
            - required_columns: List[str]
            - required_enrichments: List[str]
            - required_jsonb_keys: Dict[str, List[str]]
            - required_standards: List[str]
            - priority_weights: Dict[str, float]
            - completeness_threshold: float
        """
        # Start with asset type base requirements
        reqs = ASSET_TYPE_REQUIREMENTS.get(asset_type, {})

        # Merge 6R strategy requirements
        if six_r_strategy:
            reqs = self._merge(reqs, SIX_R_STRATEGY_REQUIREMENTS.get(six_r_strategy, {}))

        # Merge compliance requirements
        if compliance_scopes:
            for scope in compliance_scopes:
                reqs = self._merge(reqs, COMPLIANCE_REQUIREMENTS.get(scope, {}))

        # Merge criticality requirements
        if criticality:
            reqs = self._merge(reqs, CRITICALITY_REQUIREMENTS.get(criticality, {}))

        return DataRequirements(**reqs)
```

---

## 6. Pydantic Schemas

All gap reports use Pydantic models for type safety:

```python
# backend/app/services/gap_detection/schemas.py

from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ColumnGapReport(BaseModel):
    """Gap report for Asset columns."""
    missing_attributes: List[str] = Field(default_factory=list)
    empty_attributes: List[str] = Field(default_factory=list)
    null_attributes: List[str] = Field(default_factory=list)
    completeness_score: float = Field(ge=0.0, le=1.0)

class EnrichmentGapReport(BaseModel):
    """Gap report for enrichment tables."""
    missing_tables: List[str] = Field(default_factory=list)
    incomplete_tables: Dict[str, List[str]] = Field(default_factory=dict)
    completeness_score: float = Field(ge=0.0, le=1.0)

class JSONBGapReport(BaseModel):
    """Gap report for JSONB fields."""
    missing_keys: Dict[str, List[str]] = Field(default_factory=dict)
    empty_values: Dict[str, List[str]] = Field(default_factory=dict)
    completeness_score: float = Field(ge=0.0, le=1.0)

class ApplicationGapReport(BaseModel):
    """Gap report for CanonicalApplication."""
    missing_metadata: List[str] = Field(default_factory=list)
    incomplete_tech_stack: List[str] = Field(default_factory=list)
    missing_business_context: List[str] = Field(default_factory=list)
    completeness_score: float = Field(ge=0.0, le=1.0)

class StandardViolation(BaseModel):
    """A single standards violation."""
    standard_name: str
    requirement_type: str  # security, performance, compliance
    violation_details: str
    is_mandatory: bool
    override_available: bool = False

class StandardsGapReport(BaseModel):
    """Gap report for architecture standards."""
    violated_standards: List[StandardViolation] = Field(default_factory=list)
    missing_mandatory_data: List[str] = Field(default_factory=list)
    override_required: bool = False

class MissingDataItem(BaseModel):
    """A single missing data item with priority."""
    attribute_name: str
    data_layer: str  # column, enrichment, jsonb, application, standards
    priority: int  # 1=critical, 2=important, 3=optional
    reason: str
    estimated_effort: str  # low, medium, high

class ComprehensiveGapReport(BaseModel):
    """Complete gap analysis for an asset."""
    asset_id: str
    asset_name: str
    column_gaps: ColumnGapReport
    enrichment_gaps: EnrichmentGapReport
    jsonb_gaps: JSONBGapReport
    application_gaps: ApplicationGapReport
    standards_gaps: StandardsGapReport

    # Aggregated metrics
    overall_completeness_score: float = Field(ge=0.0, le=1.0)
    assessment_ready: bool
    blocking_gaps: List[str] = Field(default_factory=list)

    # Prioritized action items
    priority_missing_data: List[MissingDataItem] = Field(default_factory=list)

    # Metadata
    analysis_timestamp: str
    context_used: Dict[str, Optional[str]] = Field(default_factory=dict)
```

---

## 7. Tenant Scoping Requirements

**CRITICAL**: All database queries MUST include tenant scoping parameters:
- `client_account_id`: Organization isolation
- `engagement_id`: Project/session isolation

**Example (StandardsInspector)**:
```python
async def inspect(
    self,
    asset: Asset,
    application: Optional[CanonicalApplication],
    requirements: DataRequirements,
    client_account_id: str,  # ← REQUIRED
    engagement_id: str,      # ← REQUIRED
    db: AsyncSession,
) -> StandardsGapReport:
    # Query with tenant scoping
    stmt = select(EngagementArchitectureStandard).where(
        EngagementArchitectureStandard.client_account_id == client_account_id,
        EngagementArchitectureStandard.engagement_id == engagement_id,
        EngagementArchitectureStandard.is_mandatory == True,
    )
    result = await db.execute(stmt)
    standards = result.scalars().all()

    # Validate asset against standards
    violations = self._validate_standards(asset, standards)

    return StandardsGapReport(violated_standards=violations, ...)
```

---

## 8. Backward Compatibility Strategy

### 8.1 Preserve Old Endpoints

**Assessment Helpers** (`helpers.py`):
```python
def get_missing_critical_attributes(asset: Any) -> List[str]:
    """
    DEPRECATED: Use GapAnalyzer instead (ADR-035).
    Kept for backward compatibility during rollout.
    """
    # Keep original implementation
    ...

def get_missing_critical_attributes_v1(asset: Any) -> List[str]:
    """Renamed from get_missing_critical_attributes."""
    return get_missing_critical_attributes(asset)

async def get_comprehensive_gap_analysis(
    asset: Asset,
    application: Optional[CanonicalApplication],
    client_account_id: str,
    engagement_id: str,
    db: AsyncSession,
) -> ComprehensiveGapReport:
    """NEW: Use GapAnalyzer for comprehensive gap detection."""
    from app.services.gap_detection import GapAnalyzer

    gap_analyzer = GapAnalyzer()
    return await gap_analyzer.analyze_asset(
        asset=asset,
        application=application,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        db=db,
    )

def get_missing_attributes_compatible(
    gap_report: Optional[ComprehensiveGapReport],
    fallback_asset: Any,
) -> List[str]:
    """
    Feature flag wrapper: Use new or old gap detection.

    If feature flag COMPREHENSIVE_GAP_DETECTION=True:
        Return missing attributes from gap_report
    Else:
        Return v1 hardcoded attributes
    """
    from app.core.feature_flags import is_enabled

    if is_enabled("COMPREHENSIVE_GAP_DETECTION") and gap_report:
        # Extract missing attributes from ComprehensiveGapReport
        missing = []
        missing.extend(gap_report.column_gaps.missing_attributes)
        missing.extend(gap_report.enrichment_gaps.missing_tables)
        missing.extend([
            key for field_keys in gap_report.jsonb_gaps.missing_keys.values()
            for key in field_keys
        ])
        return missing
    else:
        # Fallback to v1
        return get_missing_critical_attributes_v1(fallback_asset)
```

### 8.2 Frontend Compatibility Shim

**ReadinessDashboardWidget.tsx**:
```typescript
// Handle both old and new response formats
const compatMissing = (missing: any): MissingAttributesByCategory => {
  if (missing.infrastructure && missing.enrichments) {
    // New format - already categorized
    return {
      infrastructure: missing.infrastructure ?? [],
      enrichments: missing.enrichments ?? [],
      technical_details: missing.technical_details ?? ([
        ...(missing.application ?? []),
        ...(missing.technical_debt ?? []),
      ]),
      standards_compliance: missing.standards_compliance ?? [],
    };
  } else {
    // Old format - flat list
    // Categorize based on attribute names (legacy logic)
    return categorizeLegacyMissing(missing);
  }
};
```

---

## 9. Performance Requirements

| Operation | Target | Notes |
|-----------|--------|-------|
| ColumnInspector | <10ms per asset | In-memory attribute checks |
| EnrichmentInspector | <20ms per asset | Eager-loaded relationships |
| JSONBInspector | <10ms per asset | JSONB traversal in-memory |
| ApplicationInspector | <10ms per asset | In-memory metadata checks |
| StandardsInspector | <50ms per asset | Database query with caching |
| **Total (all inspectors)** | **<200ms per asset** | Parallel execution with asyncio.gather |

**Optimization Strategies**:
- Use `asyncio.gather()` to run inspectors in parallel
- Cache standards queries per engagement (LRU cache)
- Batch asset processing (50 assets per batch)

---

## 10. Testing Strategy

### 10.1 Unit Tests

**Per Inspector** (`tests/services/gap_detection/test_*_inspector.py`):
- Test with complete data (should show 100% completeness)
- Test with partial data (should identify gaps)
- Test with empty data (should identify all required fields as gaps)
- Test tenant scoping (for standards inspector)

### 10.2 Integration Tests

**GapAnalyzer** (`tests/services/gap_detection/test_gap_analyzer.py`):
- Test orchestration of all inspectors
- Test completeness scoring algorithm
- Test gap prioritization
- Test performance (<200ms per asset)

### 10.3 Regression Tests

**ProgrammaticGapScanner** (`tests/backend/services/collection/test_gap_analysis.py`):
- Ensure all existing tests still pass after refactor
- Verify new gap types detected (enrichments, JSONB)
- Verify performance not degraded

---

## 11. Rollout Plan

### Phase 1: Core Infrastructure (Week 2)
- Day 6: ✅ Architecture design (this document)
- Day 7: Implement ColumnInspector + EnrichmentInspector
- Day 8: Implement JSONBInspector + ApplicationInspector + StandardsInspector
- Day 9: Implement RequirementsEngine
- Day 10: Implement GapAnalyzer orchestrator

### Phase 2: API Integration (Week 3)
- Day 11: AssessmentFlowChildService integration
- Day 12: Frontend ReadinessDashboardWidget update
- Day 13: ProgrammaticGapScanner refactor
- Day 14: IntelligentQuestionnaireGenerator integration
- Day 15: E2E testing

### Phase 3: Optimization (Week 4)
- Day 16: Caching + batch optimization
- Day 17: Optional agentic refinement
- Day 18: Standards template population
- Day 19: Monitoring + Grafana dashboards
- Day 20: Pre-commit + PR + deployment

---

## 12. Success Criteria

**Technical**:
- ✅ All 5 inspectors implemented and passing unit tests (>90% coverage)
- ✅ GapAnalyzer orchestrates inspectors correctly
- ✅ Performance <200ms per asset
- ✅ Tenant scoping enforced in all database queries
- ✅ All existing tests still pass (regression check)

**Business**:
- ✅ False positive elimination (no more "0 missing attributes" when gaps exist)
- ✅ Comprehensive gap reporting (columns + enrichments + JSONB + standards)
- ✅ Backward compatibility maintained during rollout
- ✅ Feature flag controlled for gradual adoption

---

## 13. Next Steps

1. **Review & Approve**: Obtain sign-off from technical lead and architect
2. **Begin Implementation**: Start Day 7 (ColumnInspector + EnrichmentInspector)
3. **Track Progress**: Update todo list and GitHub issue #980
4. **Daily Checkpoints**: Complete acceptance criteria before proceeding

---

**Document Control**:
- **Author**: Claude Code (Orchestration Agent)
- **Reviewers**: Technical Lead, Architect, Product Owner
- **Next Review**: After Week 2 implementation completion
- **Change Log**:
  - 2025-11-08: Initial design (v1.0)
