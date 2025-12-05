# ADR-039: Architecture Standards Compliance and EOL Lifecycle Integration

**Status**: Draft (Pending Review)
**Date**: 2025-12-05
**Context**: Gap in assessment flow - collecting technology data without surfacing compliance/EOL status
**Deciders**: Engineering Team
**Related**: ADR-037 (Intelligent Gap Detection), ADR-038 (Data Validation), Issue #1242

## Context and Problem Statement

The migration assessment platform collects detailed technical data about customer infrastructure:
- Operating system versions (Windows Server 2012, RHEL 7, AIX 7.1, etc.)
- Technology stacks (Java 8, .NET Framework 4.5, Python 2.7, Node.js 10, etc.)
- Vendor product information (Oracle 11g, SQL Server 2014, etc.)

**However, we have identified critical gaps:**

### Gap 1: Architecture Standards Compliance Not Surfaced
The `validate_technology_compliance()` function in `assessment_standards.py` evaluates technology versions against minimum standards, but:
- Results are computed during ARCHITECTURE_MINIMUMS phase
- Output is NOT persisted to `phase_results` JSONB
- Results are NOT consumed by downstream phases (TECH_DEBT_ANALYSIS, COMPONENT_SIXR_STRATEGIES)
- UI has no visibility into which assets fail compliance checks

### Gap 2: EOL Detection is Hardcoded and Limited
Current EOL detection in `eol_detection.py` has only ~12 hardcoded patterns:
```python
EOL_OS_PATTERNS = {
    "AIX 7.1": "EOL_EXPIRED",
    "AIX 7.2": "EOL_EXPIRED",
    "Windows Server 2008": "EOL_EXPIRED",
    "Windows Server 2012": "EOL_EXPIRED",
    "RHEL 6": "EOL_EXPIRED",
    "RHEL 7": "EOL_SOON",
    "Solaris 10": "EOL_EXPIRED",
}
```

**Problems:**
- No coverage for modern OS versions reaching EOL
- No vendor product lifecycle tracking (Oracle, SAP, etc.)
- No programmatic updates from authoritative sources
- Misses nuanced status (Extended Support vs. Mainstream End)

### Gap 3: Tech Debt Not Connected to Version Compliance
The TECH_DEBT_ANALYSIS phase exists but doesn't consume version compliance results from ARCHITECTURE_MINIMUMS, meaning:
- Tech debt assessment is incomplete
- 6R decisions don't factor in version compliance failures
- Users can't see "this asset uses Java 8 which is below our Java 11+ standard"

## Decision Drivers

1. **Leverage Existing Code**: `validate_technology_compliance()` already exists and works - we just need to persist and consume its output
2. **Keep Decisions Agentic**: Version compliance should be context passed to CrewAI agents, not if/else logic
3. **External Data Integration**: EOL dates change frequently - need authoritative external source
4. **Graceful Degradation**: Must work if external API is unavailable (fallback to current heuristics)
5. **Multi-Tenant Isolation**: All data scoped by client_account_id and engagement_id
6. **Minimal Schema Changes**: Use existing JSONB columns where possible

## Considered Options

### Option 1: Build Custom EOL Database
**Rejected**: Requires constant maintenance, becomes stale, duplicates work others have done.

### Option 2: Add New Database Tables for Compliance Results
**Rejected**: Over-engineering. We have `phase_results` JSONB for exactly this purpose.

### Option 3: Integrate External EOL API + Surface Compliance in phase_results (SELECTED)
**Accepted**: Leverages existing infrastructure, adds authoritative EOL data, keeps system agentic.

## Decision

Implement a three-tier approach:

### Tier 1: Surface Architecture Standards Compliance (Priority: CRITICAL)

Store `validate_technology_compliance()` output in existing `phase_results` JSONB:

```python
# In unified_assessment_flow.py - ARCHITECTURE_MINIMUMS phase
phase_results["architecture_minimums"] = {
    "engagement_standards": engagement_standards,
    "compliance_validation": validate_technology_compliance(
        technology_stack=asset.technology_stack or {},
        engagement_standards=engagement_standards
    ),  # {"compliant": bool, "issues": [], "recommendations": [], "exceptions_needed": []}
    "validated_at": datetime.utcnow().isoformat()
}
```

Consume in COMPONENT_SIXR_STRATEGIES phase:

```python
# Pass compliance context to 6R decision agent
compliance_context = phase_results.get("architecture_minimums", {}).get("compliance_validation", {})
agent_context = {
    "asset_data": asset_data,
    "compliance_issues": compliance_context.get("issues", []),
    "recommendations": compliance_context.get("recommendations", []),
    # Let agent make agentic decisions based on compliance
}
```

### Tier 2: External EOL Lifecycle Service (Priority: HIGH)

Create `EOLLifecycleService` that integrates with endoflife.date API:

```python
# backend/app/services/eol_lifecycle/eol_lifecycle_service.py

class EOLLifecycleService:
    """
    Provides EOL status for operating systems and vendor products.
    Uses endoflife.date API with Redis caching and graceful fallback.
    """

    ENDOFLIFE_API_BASE = "https://endoflife.date/api"
    CACHE_TTL_SECONDS = 86400  # 24 hours

    async def get_eol_status(
        self,
        product: str,
        version: str,
        product_type: str = "os"  # "os" | "runtime" | "database" | "framework"
    ) -> EOLStatus:
        """
        Returns EOL status for a product/version combination.

        Returns:
            EOLStatus with:
            - status: "active" | "eol_soon" | "eol_expired" | "unknown"
            - eol_date: Optional[date]
            - support_type: "mainstream" | "extended" | "none"
            - source: "endoflife.date" | "fallback_heuristics"
        """
        # 1. Check Redis cache first
        cached = await self._get_cached(product, version)
        if cached:
            return cached

        # 2. Try endoflife.date API
        try:
            result = await self._fetch_from_api(product, version)
            await self._cache_result(product, version, result)
            return result
        except ExternalAPIError:
            # 3. Fall back to current hardcoded patterns
            return self._fallback_heuristics(product, version, product_type)
```

### Tier 3: Vendor Product Lifecycle Catalog (Priority: MEDIUM)

Extend for vendor-specific products not covered by endoflife.date:

```python
# backend/app/services/eol_lifecycle/vendor_catalog.py

VENDOR_LIFECYCLE_CATALOG = {
    "oracle_database": {
        "11g": {"eol_date": "2020-12-31", "extended_support_end": "2024-12-31"},
        "12c": {"eol_date": "2022-03-31", "extended_support_end": "2025-03-31"},
        "19c": {"eol_date": "2027-04-30", "extended_support_end": "2030-04-30"},
    },
    "sap_netweaver": {
        "7.0": {"eol_date": "2020-12-31"},
        "7.5": {"eol_date": "2030-12-31"},
    },
    # Tenant-overridable via engagement_standards
}
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Assessment Flow Phases                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  ARCHITECTURE_MINIMUMS (ENHANCED)                                           │
│  ├── Load engagement_standards (technology_versions)                        │
│  ├── Call validate_technology_compliance() for each asset                   │
│  ├── Call EOLLifecycleService.get_eol_status() for OS/runtime versions      │
│  └── Store in phase_results["architecture_minimums"]                        │
│                                                                              │
│  TECH_DEBT_ANALYSIS                                                         │
│  ├── Consume phase_results["architecture_minimums"]["compliance_validation"]│
│  ├── Add version compliance failures to tech_debt assessment                │
│  └── Store combined debt analysis in phase_results["tech_debt"]             │
│                                                                              │
│  COMPONENT_SIXR_STRATEGIES                                                  │
│  ├── Consume compliance + EOL context as agent input                        │
│  ├── CrewAI agent makes agentic 6R decision factoring in:                   │
│  │   - Compliance issues → Replatform/Refactor likelihood ↑                 │
│  │   - EOL_EXPIRED → Rehost urgency ↑, Retain risk ↑                        │
│  │   - EOL_SOON → Include in recommendations                                │
│  └── Store 6R decision with compliance_factors in phase_results             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. EOL Lifecycle Service

**Location**: `backend/app/services/eol_lifecycle/`

```
eol_lifecycle/
├── __init__.py
├── eol_lifecycle_service.py    # Main service with API + caching
├── models.py                   # EOLStatus Pydantic models
├── vendor_catalog.py           # Vendor-specific lifecycle data
└── fallback_heuristics.py      # Current eol_detection.py logic moved here
```

### 2. Phase Results Schema Extension

No new tables - extend existing JSONB structure:

```python
# assessment_flow.phase_results schema
{
    "architecture_minimums": {
        "engagement_standards": [...],
        "compliance_validation": {
            "compliant": false,
            "issues": [
                {"field": "java_version", "current": "8", "required": "11+", "severity": "critical"}
            ],
            "recommendations": ["Upgrade Java from 8 to 17 LTS"],
            "exceptions_needed": []
        },
        "eol_assessments": [
            {
                "product": "Windows Server 2012 R2",
                "version": "6.3",
                "status": "eol_expired",
                "eol_date": "2023-10-10",
                "source": "endoflife.date"
            }
        ],
        "validated_at": "2025-12-05T10:30:00Z"
    },
    "tech_debt": {
        "version_compliance_debt": [...],  # From compliance_validation.issues
        "eol_risks": [...],                 # From eol_assessments
        "other_debt": [...]
    },
    "sixr_decisions": {
        "recommendation": "Replatform",
        "confidence": 0.85,
        "compliance_factors": [
            "Java 8 below minimum standard (11+)",
            "Windows Server 2012 R2 EOL expired"
        ]
    }
}
```

### 3. Frontend Compliance Report Component

**Location**: `src/components/assessment/ComplianceReport.tsx`

```typescript
interface ComplianceReportProps {
  assetId: string;
  complianceData: {
    compliant: boolean;
    issues: ComplianceIssue[];
    recommendations: string[];
    eolAssessments: EOLAssessment[];
  };
}

// Display in Assessment Details panel:
// - Red badge: "3 Compliance Issues"
// - Yellow badge: "2 EOL Warnings"
// - Expandable list of issues with recommendations
```

## Implementation Steps

### Phase 1: Core Compliance (Week 1)
1. **[Backend]** Modify ARCHITECTURE_MINIMUMS phase to persist `validate_technology_compliance()` output
2. **[Backend]** Modify TECH_DEBT_ANALYSIS phase to consume compliance validation
3. **[Backend]** Modify COMPONENT_SIXR_STRATEGIES to pass compliance context to 6R agent

### Phase 2: EOL Service (Week 2)
4. **[Backend]** Create EOLLifecycleService with endoflife.date integration
5. **[Backend]** Add Redis caching layer with 24h TTL
6. **[Backend]** Move current eol_detection.py patterns to fallback_heuristics.py

### Phase 3: Vendor Catalog (Week 3)
7. **[Backend]** Create vendor_catalog.py with Oracle, SAP, etc.
8. **[Backend]** Add tenant-override capability via engagement_standards

### Phase 4: Frontend (Week 4)
9. **[Frontend]** Create ComplianceReport component
10. **[Frontend]** Add EOL Risk section to Assessment Details
11. **[Frontend]** Add compliance filters to asset list

### Phase 5: Testing & Polish
12. **[Testing]** Unit tests for EOLLifecycleService
13. **[Testing]** Integration tests for phase data flow
14. **[E2E]** Playwright tests for compliance UI

## Files to Modify

### Backend
| File | Change |
|------|--------|
| `backend/app/services/crewai_flows/unified_assessment_flow.py` | Persist compliance to phase_results, consume in later phases |
| `backend/app/core/seed_data/assessment_standards.py` | Ensure validate_technology_compliance() returns consistent schema |
| `backend/app/services/eol_lifecycle/` | NEW: EOL lifecycle service directory |
| `backend/app/api/v1/endpoints/collection_crud_questionnaires/eol_detection.py` | Move patterns to fallback, call new service |

### Frontend
| File | Change |
|------|--------|
| `src/components/assessment/ComplianceReport.tsx` | NEW: Compliance display component |
| `src/components/assessment/AssessmentDetails.tsx` | Add ComplianceReport section |
| `src/types/assessment.ts` | Add compliance-related types |

## Consequences

### Positive
- Customers see clear "compliance vs. non-compliant" status per asset
- 6R recommendations factor in version compliance and EOL status
- EOL data automatically refreshed from authoritative source
- Graceful degradation if external API unavailable
- No new database tables - uses existing phase_results JSONB

### Negative
- Adds external API dependency (mitigated by caching + fallback)
- Redis required for caching (already in infrastructure)
- Vendor catalog requires manual maintenance for products not in endoflife.date

### Neutral
- Existing assessment flows continue working unchanged until migration
- Can roll out per-engagement via feature flag if needed

## Success Metrics

1. **Compliance Visibility**: 100% of assessed assets show compliance status in UI
2. **EOL Coverage**: >80% of OS/runtime versions have EOL status from API
3. **6R Impact**: 6R recommendations include compliance_factors for non-compliant assets
4. **Fallback Reliability**: System degrades gracefully when API unavailable

## References

- `backend/app/core/seed_data/assessment_standards.py:validate_technology_compliance()`
- `backend/app/core/seed_data/standards/technology_versions.py`
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/eol_detection.py`
- `backend/app/services/crewai_flows/unified_assessment_flow.py`
- External: https://endoflife.date/api
- ADR-037: Intelligent Gap Detection and Questionnaire Generation
- ADR-038: Intelligent Data Validation and Profiling
