# Comprehensive Solution Approach: Assessment Architecture & Enrichment Pipeline

**Date**: October 15, 2025
**Status**: Awaiting Approval
**Type**: Long-term Architectural Solution
**Dependencies**: ASSET_ENRICHMENT_COMPLETE_ARCHITECTURE.md, COLLECTION_ASSESSMENT_ASSET_TYPE_ANALYSIS.md

---

## Executive Summary

This document provides a **comprehensive, long-term architectural solution** for all identified gaps in the asset enrichment and assessment pipeline. This is NOT a band-aid fix but a proper architectural implementation addressing root causes.

### Vision

Create a fully automated, multi-asset-type enrichment and assessment pipeline where:
- Assets automatically enrich through discovery/collection/bulk import
- Canonical application deduplication happens universally
- Assessment flow seamlessly handles multiple asset types
- Users have full visibility into readiness, blockers, and progress
- AI agents automatically populate enrichment tables

### All Gaps Addressed

| Priority | Gap | Current State | Target State |
|----------|-----|---------------|--------------|
| **P0** | Assessment Applications Endpoint | EXISTS but lacks canonical grouping | Enhance with canonical app resolution + grouping |
| **P0** | Assessment Blockers UI | Invisible (no UI component) | Full readiness dashboard with actionable guidance |
| **P0** | Assessment Data Model | Stores asset_ids as "application_ids" | Proper semantic model: assets + canonical_apps + groups |
| **P1** | Canonical Linkage Bulk Import | Bulk import creates assets but NO dedup | Add canonical dedup + collection_flow_applications link |
| **P1** | Enrichment Auto-Population | Models EXIST, manual entry only | Agent-driven auto-population for 7 enrichment tables |
| **P1** | Collection→Assessment Handoff | Incomplete mapping | Rich metadata transfer with groupings |
| **P2** | Asset-Application Grouping | Flat list | Hierarchical: "App X (3 assets: Server, DB, Network)" |
| **P2** | Gap Remediation Automation | User fills all gaps | AI suggests values from similar assets |
| **P2** | Assessment Progress Tracking | Phase-level only | Attribute-level progress with estimates |

---

## Problem Scenarios (Comprehensive)

### P0 Gaps: Critical Blockers

#### Gap #1: Assessment Applications Endpoint Lacks Canonical Grouping ❌

**Endpoint Exists But Incomplete**: `GET /api/v1/master-flows/{flow_id}/assessment-applications`
- Location: `backend/app/api/v1/master_flows/master_flows_assessment.py:199-331`
- Returns flat list of assets using Discovery-based metadata
- Does NOT group by canonical applications
- Does NOT leverage collection_flow_applications junction table

**Current Failure**:
```
User completes Collection → Transitions to Assessment
   ↓
Frontend calls: GET /api/v1/master-flows/{flow_id}/assessment-applications
   ↓
✅ Endpoint returns data
   ↓
❌ Data is flat asset list, NOT grouped by canonical applications ❌
   ↓
UI displays individual assets instead of application-centric view
   ↓
User sees "3 assets" when it should show "1 application (3 assets)"
```

**Database Shows Data Exists**:
```sql
-- Assessment flow has asset IDs stored
SELECT selected_application_ids FROM assessment_flows
WHERE flow_id = 'ced44ce1-effc-403f-89cc-aeeb05ceba84';
-- Returns: ["c4ed088f-6658-405b-b011-8ce50c065ddf"]  (asset UUID)

-- Asset exists and is mapped to canonical application
SELECT a.asset_name, a.asset_type, cfa.canonical_application_id
FROM assets a
JOIN collection_flow_applications cfa ON a.id = cfa.asset_id
WHERE a.id = 'c4ed088f-6658-405b-b011-8ce50c065ddf';
-- Returns: DevTestVM01, server, 05459507-86cb-41f9-9c2d-2a9f4a50445a
```

**Root Cause**: Existing endpoint doesn't use canonical application resolution and grouping logic

---

#### Gap #2: Assessment Blockers Invisible ❌

**Current Failure**:
```
Asset populated with:
  - assessment_readiness = 'not_ready'
  - assessment_blockers = ["missing_business_owner", "missing_dependencies"]
  - completeness_score = 0.42 (42%)
   ↓
User views Assessment Overview
   ↓
❌ No indication of blockers displayed ❌
   ↓
User confused: "Why can't I start assessment?"
```

**Backend Populates Correctly**:
```python
# backend/app/models/asset/assessment_fields.py:21-40
assessment_readiness = Column(String, default='not_ready')
assessment_blockers = Column(JSON)  # ← Populated with blocker array
completeness_score = Column(Numeric(5, 2))  # ← 0.42
```

**Frontend Missing**:
```typescript
// src/pages/assessment/AssessmentFlowOverview.tsx
// ❌ No component rendering assessment_blockers
// ❌ No widget showing completeness_score
// ❌ No guidance on 22 critical attributes
```

**Root Cause**: Frontend has no UI component to display readiness status and blockers

---

#### Gap #3: Assessment Data Model Semantic Mismatch ❌

**Current Problem**:
```sql
-- Column is named "selected_application_ids"
assessment_flows.selected_application_ids JSONB

-- But actually stores ASSET IDs (servers, databases, network devices)
-- Example:
{"selected_application_ids": ["c4ed088f-6658-405b-b011-8ce50c065ddf"]}
                                ↑
                            This is an ASSET UUID, not application UUID

-- This creates semantic confusion:
-- Frontend: "I need application details"
-- Backend: "I only have asset IDs"
-- Missing: "How do I resolve asset → application?"
```

**Impact**:
- Confusion for developers: "Is this an asset ID or application ID?"
- Inefficient queries: Must resolve at runtime every time
- No grouping: Can't show "Application X has 3 assets"

**Root Cause**: Assessment data model didn't evolve when Collection added multi-asset-type support

---

### P1 Gaps: High-Impact Improvements

#### Gap #4: Canonical Application Linkage Missing in Bulk Import ⚠️

**Current Bulk Import Flow** (Partially Implemented):
```
User uploads CSV with applications
   ↓
POST /api/v1/collection/bulk-import
   ↓
✅ Creates/updates assets directly (backend/app/api/v1/endpoints/collection.py:276-333)
✅ Triggers gap analysis
   ↓
❌ Does NOT call CanonicalApplication.find_or_create_canonical() ❌
❌ Does NOT create collection_flow_applications links ❌
   ↓
Result: Bulk imported apps miss deduplication benefits
```

**Comparison to Discovery Flow** (which works correctly):
```
Discovery agent finds application
   ↓
Calls CanonicalApplication.find_or_create_canonical()
   ↓
SHA-256 hashing + vector similarity matching
   ↓
Creates collection_flow_applications entry
   ↓
Asset linked to canonical application ✅
```

**What Bulk Import Currently Does** ✅:
```python
# backend/app/api/v1/endpoints/collection.py:276-333
@router.post("/bulk-import")
async def bulk_import_collection_data(...):
    # ✅ Parses CSV rows
    # ✅ Creates/updates assets in assets table
    # ✅ Triggers gap analysis
    # ✅ Links to raw_import_records (traceability exists)
```

**What's Missing** ❌:
```python
# After asset creation, should add:
# ❌ Missing: CanonicalApplication.find_or_create_canonical() call
# ❌ Missing: collection_flow_applications entry creation
```

**Impact**:
- Duplicate applications not detected ("SAP ERP" vs "SAP-ERP-Production")
- Can't leverage canonical registry for Assessment
- Breaks application-centric reporting

---

#### Gap #5: Enrichment Tables Not Auto-Populated ⚠️

**Enrichment Models Exist** ✅:
- `AssetComplianceFlag` (backend/app/models/asset_compliance_flag.py) - compliance_scopes, data_classification
- `AssetProductLink` (backend/app/models/asset_product_link.py) - catalog matching
- `AssetLicense` (backend/app/models/asset_license.py) - licensing info
- `AssetVulnerability` (backend/app/models/asset_vulnerability.py) - CVE tracking
- `AssetResilience` (backend/app/models/asset_resilience.py) - HA, DR, backup config
- `AssetDependency` (backend/app/models/asset_dependency.py) - relationship mapping
- `AssetFieldConflict` (backend/app/models/asset_field_conflict.py) - conflict resolution

**But Auto-Population Missing** ❌:
```sql
SELECT COUNT(*) FROM asset_compliance_flags;    -- Typically 0 rows (manual entry only)
SELECT COUNT(*) FROM asset_product_links;       -- Typically 0 rows (manual entry only)
SELECT COUNT(*) FROM asset_licenses;            -- Typically 0 rows (manual entry only)
SELECT COUNT(*) FROM asset_vulnerabilities;     -- Typically 0 rows (manual entry only)
SELECT COUNT(*) FROM asset_resilience;          -- Typically 0 rows (manual entry only)
```

**Current Manual Process**:
```
User discovers asset
   ↓
Asset created in assets table
   ↓
User must MANUALLY populate enrichment data:
  - Compliance requirements
  - License information
  - Vulnerability scans
  - Resilience configuration
  - Product catalog links
   ↓
❌ Time-consuming and error-prone ❌
```

**Desired Automated Process**:
```
Asset created
   ↓
AI Agent Enrichment Pipeline triggers:
   ├─→ Compliance Agent: Infer compliance_scopes, data_classification
   ├─→ Licensing Agent: Match to vendor_products_catalog, calculate costs
   ├─→ Vulnerability Agent: Query CVE databases, populate vulnerabilities
   ├─→ Resilience Agent: Analyze HA config, calculate resilience_score
   ├─→ Dependency Agent: Auto-discover dependencies, create edges
   └─→ Product Matching Agent: Link to catalog via fuzzy matching
   ↓
Enrichment tables auto-populated ✅
```

**Why This Matters**:
- 6R assessment requires enrichment data (licenses, compliance, vulnerabilities)
- Manual entry doesn't scale beyond 10-20 assets
- AI agents can infer/suggest values with high confidence

---

#### Gap #6: Collection → Assessment Handoff Incomplete ⚠️

**Current Handoff**:
```python
# backend/app/services/flow_commands.py: create_assessment_flow()
assessment_flow = AssessmentFlow(
    selected_application_ids=asset_ids,  # ← Only passes asset IDs
    # ❌ Missing: canonical_application_ids
    # ❌ Missing: application_asset_groups (which assets map to which apps)
    # ❌ Missing: enrichment_status (which enrichment tables populated)
    # ❌ Missing: readiness_summary (how many assets ready vs not)
)
```

**What Assessment Flow Needs**:
```python
assessment_flow = AssessmentFlow(
    # Legacy (kept for compatibility)
    selected_application_ids=asset_ids,

    # NEW: Proper semantic modeling
    selected_asset_ids=asset_ids,
    selected_canonical_application_ids=canonical_app_ids,

    # NEW: Asset-application grouping
    application_asset_groups=[
        {
            "canonical_application_id": "app-1",
            "canonical_application_name": "CRM System",
            "asset_ids": ["server-1", "db-1", "network-device-1"],
            "asset_types": ["server", "database", "network_device"]
        }
    ],

    # NEW: Enrichment status tracking
    enrichment_status={
        "compliance_flags": 2,  # 2 assets have compliance data
        "licenses": 0,          # 0 assets have license data
        "vulnerabilities": 3,   # 3 assets have vulnerability scans
        "resilience": 1,        # 1 asset has HA config
        "dependencies": 4       # 4 dependency relationships mapped
    },

    # NEW: Readiness summary
    readiness_summary={
        "total_assets": 5,
        "ready": 2,
        "not_ready": 3,
        "avg_completeness_score": 0.64
    }
)
```

**Impact**: Assessment flow starts with insufficient context, requiring multiple queries

---

### P2 Gaps: Enhanced User Experience

#### Gap #7: Asset-Application Grouping Not Visible ℹ️

**Current UI Display**:
```
Assessment Overview:
  Selected Applications: 3 applications

  1. ServerA (server)
  2. DatabaseB (database)
  3. NetworkDeviceC (network_device)
```

**Problem**: These 3 assets might all belong to ONE application (e.g., "CRM System")

**Desired UI Display**:
```
Assessment Overview:
  Selected Applications: 1 application (3 assets)

  📦 CRM System
     ├─ ServerA (server) - Production
     ├─ DatabaseB (database) - Production
     └─ NetworkDeviceC (network_device) - Production

     Assessment Readiness: 67% (2/3 assets ready)
     Missing Data: Business Owner, Annual Cost
```

**Root Cause**: Assessment data model doesn't track application_asset_groups

---

#### Gap #8: Gap Remediation Not Automated ℹ️

**Current Gap Collection**:
```
Gap Analysis identifies missing:
  - business_owner
  - annual_operating_cost
  - dependencies
   ↓
Questionnaire generated
   ↓
User must fill EVERY field manually ❌
```

**Desired AI-Assisted Remediation**:
```
Gap Analysis identifies missing:
  - business_owner
  - annual_operating_cost
  - dependencies
   ↓
AI Agent analyzes similar assets:
  - "Similar server (ServerX) has business_owner: 'John Doe' (Finance Dept)"
  - "Typical annual cost for this server class: $12,000"
  - "Detected network dependency to DatabaseB (port 5432)"
   ↓
Questionnaire pre-filled with AI suggestions (confidence scores):
  ✓ business_owner: "John Doe" (85% confidence) [Edit]
  ✓ annual_operating_cost: $12,000 (72% confidence) [Edit]
  ✓ dependencies: ["DatabaseB"] (91% confidence) [Confirm]
   ↓
User reviews and confirms/edits ✅
```

**Benefits**:
- Reduces manual data entry by 60-80%
- Improves data quality through learning
- Accelerates assessment readiness

---

#### Gap #9: Assessment Progress Tracking Limited ℹ️

**Current Progress Display**:
```
Assessment Flow Progress: 33%
Current Phase: Architecture Minimums
```

**Problem**: User doesn't know:
- Which specific attributes are being assessed
- How many attributes completed vs remaining
- Estimated time to completion
- Which assets blocking progress

**Desired Progress Dashboard**:
```
Assessment Flow Progress: 33% Complete
Estimated Time Remaining: 45 minutes

📊 Progress by Category:
  ✅ Infrastructure Attributes: 6/6 complete (100%)
  ⏳ Application Attributes: 4/8 complete (50%) - IN PROGRESS
  ⏳ Business Attributes: 1/4 complete (25%)
  ❌ Technical Debt Attributes: 0/4 complete (0%)

🚧 Current Blockers:
  - 2 assets missing business_owner
  - 3 assets missing dependencies
  - 1 asset missing support_status

📦 Asset Readiness:
  ✅ Ready: 2 assets (40%)
  ⏳ In Progress: 1 asset (20%)
  ❌ Not Ready: 2 assets (40%)
```

**Root Cause**: Assessment flow doesn't track attribute-level granularity

---

## Recommended Solutions (Comprehensive)

### Solution Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNIFIED ENRICHMENT PIPELINE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Discovery Flow              Collection Flow        Bulk Import  │
│       │                           │                      │        │
│       ├─→ Asset Creation ←────────┼──────────────────────┘        │
│       │         │                 │                               │
│       │         ↓                 │                               │
│       │   [CANONICAL DEDUPLICATION SERVICE]                      │
│       │         │                 │                               │
│       │         ├─→ SHA-256 Hash Match                           │
│       │         ├─→ Vector Similarity (384D)                     │
│       │         └─→ Create collection_flow_applications          │
│       │                           │                               │
│       └─────────┬─────────────────┘                               │
│                 ↓                                                 │
│         [AUTOMATED ENRICHMENT PIPELINE]                          │
│                 │                                                 │
│                 ├─→ Compliance Agent → asset_compliance_flags    │
│                 ├─→ Licensing Agent → asset_licenses             │
│                 ├─→ Vulnerability Agent → asset_vulnerabilities  │
│                 ├─→ Resilience Agent → asset_resilience          │
│                 ├─→ Dependency Agent → asset_dependencies        │
│                 ├─→ Product Matcher → asset_product_links        │
│                 └─→ Conflict Resolver → asset_field_conflicts    │
│                                                                   │
│                 ↓                                                 │
│         [ASSESSMENT READINESS CALCULATOR]                        │
│                 │                                                 │
│                 ├─→ 22 Critical Attributes Check                 │
│                 ├─→ Completeness Score (0-1)                     │
│                 ├─→ Assessment Blockers Array                    │
│                 └─→ Update assessment_readiness                  │
│                                                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              ASSESSMENT FLOW (Proper Data Model)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Initialization: POST /master-flows/new/assessment/initialize    │
│       │                                                           │
│       ├─→ Resolve asset_ids → canonical_application_ids          │
│       ├─→ Build application_asset_groups structure               │
│       ├─→ Calculate enrichment_status summary                    │
│       ├─→ Generate readiness_summary                             │
│       │                                                           │
│       └─→ Store in assessment_flows table:                       │
│             - selected_asset_ids                                 │
│             - selected_canonical_application_ids                 │
│             - application_asset_groups                           │
│             - enrichment_status                                  │
│             - readiness_summary                                  │
│                                                                   │
│  Endpoints:                                                       │
│    GET /master-flows/{id}/assessment-applications                │
│        └─→ Returns grouped applications with assets              │
│    GET /master-flows/{id}/assessment-readiness                   │
│        └─→ Returns detailed readiness dashboard data             │
│    GET /master-flows/{id}/assessment-progress                    │
│        └─→ Returns attribute-level progress tracking             │
│                                                                   │
└───────────────────────────────┬─────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                  FRONTEND UI ENHANCEMENTS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Assessment Overview Page:                                        │
│    ├─→ ApplicationGroupsWidget (hierarchical display)           │
│    ├─→ ReadinessDashboard (blockers, completeness, guidance)    │
│    ├─→ ProgressTracker (attribute-level granularity)            │
│    └─→ ActionableGaps (AI suggestions, pre-filled forms)        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Solutions

### Solution 1: Assessment Data Model Refactor (P0)

**Database Migration**: `backend/alembic/versions/093_assessment_data_model_refactor.py`

```sql
-- Add new columns to assessment_flows table
ALTER TABLE migration.assessment_flows
  ADD COLUMN selected_asset_ids JSONB DEFAULT '[]',
  ADD COLUMN selected_canonical_application_ids JSONB DEFAULT '[]',
  ADD COLUMN application_asset_groups JSONB DEFAULT '[]',
  ADD COLUMN enrichment_status JSONB DEFAULT '{}',
  ADD COLUMN readiness_summary JSONB DEFAULT '{}';

-- Add indexes for performance
CREATE INDEX idx_assessment_flows_asset_ids
  ON migration.assessment_flows USING GIN (selected_asset_ids);

CREATE INDEX idx_assessment_flows_canonical_app_ids
  ON migration.assessment_flows USING GIN (selected_canonical_application_ids);

-- Migrate existing data (convert old selected_application_ids to selected_asset_ids)
UPDATE migration.assessment_flows
SET selected_asset_ids = selected_application_ids
WHERE selected_asset_ids = '[]'::jsonb;

-- Mark selected_application_ids as deprecated (keep for backward compatibility)
COMMENT ON COLUMN migration.assessment_flows.selected_application_ids
  IS 'DEPRECATED: Use selected_asset_ids instead. Kept for backward compatibility.';
```

**SQLAlchemy Model Update**: `backend/app/models/assessment_flow.py`

```python
class AssessmentFlow(Base, TimestampMixin):
    __tablename__ = "assessment_flows"

    # ... existing fields ...

    # DEPRECATED: Keep for backward compatibility
    selected_application_ids = Column(
        JSONB,
        default=[],
        comment="DEPRECATED: Use selected_asset_ids instead"
    )

    # NEW: Proper semantic fields
    selected_asset_ids = Column(
        JSONB,
        default=[],
        comment="Array of asset UUIDs selected for assessment"
    )

    selected_canonical_application_ids = Column(
        JSONB,
        default=[],
        comment="Array of canonical application UUIDs (resolved from assets)"
    )

    application_asset_groups = Column(
        JSONB,
        default=[],
        comment="""
        Array of application groups with their assets:
        [
          {
            "canonical_application_id": "uuid",
            "canonical_application_name": "CRM System",
            "asset_ids": ["uuid1", "uuid2"],
            "asset_count": 2,
            "asset_types": ["server", "database"]
          }
        ]
        """
    )

    enrichment_status = Column(
        JSONB,
        default={},
        comment="""
        Summary of enrichment table population:
        {
          "compliance_flags": 2,
          "licenses": 0,
          "vulnerabilities": 3,
          "resilience": 1,
          "dependencies": 4
        }
        """
    )

    readiness_summary = Column(
        JSONB,
        default={},
        comment="""
        Assessment readiness summary:
        {
          "total_assets": 5,
          "ready": 2,
          "not_ready": 3,
          "avg_completeness_score": 0.64
        }
        """
    )
```

**Pydantic Schema Update**: `backend/app/schemas/assessment_flow.py`

```python
class ApplicationAssetGroup(BaseModel):
    canonical_application_id: Optional[UUID]
    canonical_application_name: str
    asset_ids: List[UUID]
    asset_count: int
    asset_types: List[str]
    readiness_summary: Dict[str, Any] = {}

class EnrichmentStatus(BaseModel):
    compliance_flags: int = 0
    licenses: int = 0
    vulnerabilities: int = 0
    resilience: int = 0
    dependencies: int = 0
    product_links: int = 0
    field_conflicts: int = 0

class ReadinessSummary(BaseModel):
    total_assets: int
    ready: int
    not_ready: int
    in_progress: int = 0
    avg_completeness_score: float

class AssessmentFlowCreate(BaseModel):
    # Accept both old and new formats for backward compatibility
    selected_application_ids: Optional[List[UUID]] = []  # Deprecated
    selected_asset_ids: List[UUID]
    selected_canonical_application_ids: Optional[List[UUID]] = []
    application_asset_groups: Optional[List[ApplicationAssetGroup]] = []
    enrichment_status: Optional[EnrichmentStatus] = None
    readiness_summary: Optional[ReadinessSummary] = None
```

---

### Solution 2: Assessment Application Resolver Service (P0)

**New Service**: `backend/app/services/assessment/application_resolver.py`

```python
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset, CanonicalApplication, CollectionFlowApplication
from app.schemas.assessment_flow import ApplicationAssetGroup

class AssessmentApplicationResolver:
    """
    Service for resolving assets to canonical applications in Assessment flow.
    Provides rich application-centric view with asset groupings.
    """

    def __init__(self, db: AsyncSession, client_account_id: UUID, engagement_id: UUID):
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def resolve_assets_to_applications(
        self,
        asset_ids: List[UUID],
        collection_flow_id: Optional[UUID] = None
    ) -> List[ApplicationAssetGroup]:
        """
        Resolve asset IDs to canonical applications with grouping.

        Args:
            asset_ids: List of asset UUIDs from assessment flow
            collection_flow_id: Optional collection flow for scoping

        Returns:
            List of ApplicationAssetGroup objects with:
            - canonical_application_id
            - canonical_application_name
            - asset_ids (all assets belonging to this app)
            - asset_types (distinct types: server, database, etc.)
            - readiness_summary (how many assets ready)
        """
        # Query to join assets → collection_flow_applications → canonical_applications
        query = (
            select(
                Asset.id.label("asset_id"),
                Asset.asset_name,
                Asset.asset_type,
                Asset.environment,
                Asset.assessment_readiness,
                Asset.assessment_readiness_score,
                CollectionFlowApplication.canonical_application_id,
                CollectionFlowApplication.deduplication_method,
                CollectionFlowApplication.match_confidence,
                CanonicalApplication.canonical_name,
                CanonicalApplication.application_type,
                CanonicalApplication.technology_stack
            )
            .select_from(Asset)
            .outerjoin(
                CollectionFlowApplication,
                Asset.id == CollectionFlowApplication.asset_id
            )
            .outerjoin(
                CanonicalApplication,
                CollectionFlowApplication.canonical_application_id == CanonicalApplication.id
            )
            .where(
                Asset.id.in_(asset_ids),
                Asset.client_account_id == self.client_account_id,
                Asset.engagement_id == self.engagement_id
            )
        )

        if collection_flow_id:
            query = query.where(CollectionFlowApplication.collection_flow_id == collection_flow_id)

        result = await self.db.execute(query)
        rows = result.all()

        # Group assets by canonical application
        app_groups: Dict[str, Dict[str, Any]] = {}

        for row in rows:
            # Use canonical_application_id as key, fallback to asset_id for unmapped
            app_key = str(row.canonical_application_id) if row.canonical_application_id else f"unmapped-{row.asset_id}"

            if app_key not in app_groups:
                app_groups[app_key] = {
                    "canonical_application_id": row.canonical_application_id,
                    "canonical_application_name": row.canonical_name or row.asset_name or "Unknown",
                    "application_type": row.application_type,
                    "technology_stack": row.technology_stack or [],
                    "assets": [],
                    "asset_types": set(),
                    "readiness": {"ready": 0, "not_ready": 0, "in_progress": 0}
                }

            # Add asset to group
            app_groups[app_key]["assets"].append({
                "asset_id": row.asset_id,
                "asset_name": row.asset_name,
                "asset_type": row.asset_type,
                "environment": row.environment,
                "assessment_readiness": row.assessment_readiness,
                "assessment_readiness_score": float(row.assessment_readiness_score or 0),
                "deduplication_method": row.deduplication_method,
                "match_confidence": float(row.match_confidence or 0)
            })

            # Track asset type
            app_groups[app_key]["asset_types"].add(row.asset_type)

            # Track readiness
            if row.assessment_readiness == "ready":
                app_groups[app_key]["readiness"]["ready"] += 1
            elif row.assessment_readiness == "in_progress":
                app_groups[app_key]["readiness"]["in_progress"] += 1
            else:
                app_groups[app_key]["readiness"]["not_ready"] += 1

        # Convert to ApplicationAssetGroup objects
        groups = []
        for app_key, group_data in app_groups.items():
            groups.append(ApplicationAssetGroup(
                canonical_application_id=group_data["canonical_application_id"],
                canonical_application_name=group_data["canonical_application_name"],
                asset_ids=[a["asset_id"] for a in group_data["assets"]],
                asset_count=len(group_data["assets"]),
                asset_types=list(group_data["asset_types"]),
                readiness_summary=group_data["readiness"]
            ))

        return groups

    async def calculate_enrichment_status(self, asset_ids: List[UUID]) -> Dict[str, int]:
        """
        Calculate how many assets have data in each enrichment table.

        Returns:
            {
                "compliance_flags": 2,
                "licenses": 0,
                "vulnerabilities": 3,
                ...
            }
        """
        from app.models import (
            AssetComplianceFlag, AssetLicense, AssetVulnerability,
            AssetResilience, AssetDependency, AssetProductLink, AssetFieldConflict
        )

        enrichment_counts = {}

        # Count assets in each enrichment table
        for table_name, model in [
            ("compliance_flags", AssetComplianceFlag),
            ("licenses", AssetLicense),
            ("vulnerabilities", AssetVulnerability),
            ("resilience", AssetResilience),
            ("dependencies", AssetDependency),
            ("product_links", AssetProductLink),
            ("field_conflicts", AssetFieldConflict)
        ]:
            query = select(model.asset_id.distinct()).where(
                model.asset_id.in_(asset_ids),
                model.client_account_id == self.client_account_id,
                model.engagement_id == self.engagement_id
            )
            result = await self.db.execute(query)
            enrichment_counts[table_name] = len(result.all())

        return enrichment_counts

    async def calculate_readiness_summary(self, asset_ids: List[UUID]) -> Dict[str, Any]:
        """
        Calculate assessment readiness summary for selected assets.

        Returns:
            {
                "total_assets": 5,
                "ready": 2,
                "not_ready": 3,
                "in_progress": 0,
                "avg_completeness_score": 0.64
            }
        """
        query = select(
            Asset.assessment_readiness,
            Asset.assessment_readiness_score
        ).where(
            Asset.id.in_(asset_ids),
            Asset.client_account_id == self.client_account_id,
            Asset.engagement_id == self.engagement_id
        )

        result = await self.db.execute(query)
        rows = result.all()

        readiness_counts = {"ready": 0, "not_ready": 0, "in_progress": 0}
        scores = []

        for row in rows:
            readiness_counts[row.assessment_readiness or "not_ready"] += 1
            if row.assessment_readiness_score is not None:
                scores.append(float(row.assessment_readiness_score))

        avg_score = sum(scores) / len(scores) if scores else 0.0

        return {
            "total_assets": len(rows),
            "ready": readiness_counts["ready"],
            "not_ready": readiness_counts["not_ready"],
            "in_progress": readiness_counts["in_progress"],
            "avg_completeness_score": round(avg_score, 2)
        }
```

---

### Solution 3: Enhance Assessment Applications Endpoint (P0)

**Existing Endpoint to Enhance**: `backend/app/api/v1/master_flows/master_flows_assessment.py:199-331`

Current endpoint `GET /{flow_id}/assessment-applications` exists but needs enhancement:

**Current Implementation Issues**:
- Returns flat asset list using Discovery-based metadata
- Uses `DiscoveryFlowIntegration` instead of canonical applications
- No grouping by canonical_application_id
- Checks for unmapped `CollectionFlowApplication` records but doesn't use them for grouping

**Enhanced Implementation**:

```python
# Update existing endpoint in backend/app/api/v1/master_flows/master_flows_assessment.py

@router.get("/{flow_id}/assessment-applications", response_model=AssessmentApplicationsListResponse)
async def get_assessment_applications_via_master(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
):
    """
    Get applications selected for assessment with canonical grouping.

    ENHANCED: Now uses AssessmentApplicationResolver to:
    - Resolve asset IDs to canonical applications
    - Group multiple assets under same application
    - Provide readiness summary per application
    - Handle unmapped assets gracefully

    Returns:
        - applications: List of canonical applications with their assets (GROUPED)
        - total_applications: Count of unique canonical applications
        - total_assets: Count of total assets
        - unmapped_assets: Count of assets without canonical mapping
    """
    # Get assessment flow
    query = select(AssessmentFlow).where(
        AssessmentFlow.flow_id == flow_id,
        AssessmentFlow.client_account_id == context.client_account_id,
        AssessmentFlow.engagement_id == context.engagement_id
    )
    result = await db.execute(query)
    assessment_flow = result.scalar_one_or_none()

    if not assessment_flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment flow not found: {flow_id}"
        )

    # Use new fields if available, fallback to legacy
    asset_ids = assessment_flow.selected_asset_ids or assessment_flow.selected_application_ids or []

    if not asset_ids:
        return AssessmentApplicationsListResponse(
            applications=[],
            total_applications=0,
            total_assets=0,
            unmapped_assets=0
        )

    # Resolve assets to applications
    resolver = AssessmentApplicationResolver(db, context.client_account_id, context.engagement_id)

    # Get application groups from cached data if available
    if assessment_flow.application_asset_groups:
        # Use pre-computed groups from initialization
        application_groups = assessment_flow.application_asset_groups
    else:
        # Compute on-the-fly (fallback for legacy flows)
        application_groups = await resolver.resolve_assets_to_applications(asset_ids)

    # Convert to response objects
    applications = []
    unmapped_count = 0

    for group in application_groups:
        if not group.canonical_application_id:
            unmapped_count += group.asset_count

        applications.append(AssessmentApplicationResponse(
            canonical_application_id=group.canonical_application_id,
            canonical_application_name=group.canonical_application_name,
            application_type=group.get("application_type"),
            technology_stack=group.get("technology_stack", []),
            asset_count=group.asset_count,
            assets=[
                AssessmentApplicationAsset(**asset)
                for asset in group.get("assets", [])
            ],
            business_criticality=None,  # TODO: Calculate from assets
            complexity_score=None,      # TODO: Calculate
            readiness_score=group.readiness_summary.get("ready", 0) / group.asset_count if group.asset_count > 0 else 0,
            discovery_completed_at=None
        ))

    return AssessmentApplicationsListResponse(
        applications=applications,
        total_applications=len(applications),
        total_assets=len(asset_ids),
        unmapped_assets=unmapped_count
    )

@router.get("/{flow_id}/assessment-readiness")
async def get_assessment_readiness(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
):
    """
    Get detailed assessment readiness information.

    Returns:
        - Per-application readiness status
        - Missing critical attributes
        - Assessment blockers
        - Completeness scores
        - Actionable guidance
    """
    # ... implementation similar to assessment-applications ...
    # Plus: Fetch assessment_blockers from assets
    # Plus: Calculate missing critical attributes
    # Plus: Return actionable remediation steps

@router.get("/{flow_id}/assessment-progress")
async def get_assessment_progress(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
):
    """
    Get attribute-level assessment progress tracking.

    Returns:
        - Progress by category (Infrastructure, Application, Business, Technical Debt)
        - Completed vs remaining attributes
        - Current blockers
        - Estimated time remaining
    """
    # ... implementation ...
    # Returns granular progress data for frontend dashboard
```

---

### Solution 4: Canonical Deduplication in Bulk Import (P1)

**Update Bulk Import Endpoint**: `backend/app/api/v1/endpoints/collection.py:276-321`

```python
@router.post("/bulk-import")
async def bulk_import_collection_data(
    file: UploadFile,
    collection_flow_id: UUID,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
):
    """
    Process bulk CSV import for Collection flow.

    Enhanced to include canonical application deduplication.
    """
    # ... existing CSV parsing ...

    created_assets = []
    canonical_mappings = []

    for row in csv_rows:
        # 1. Create/update asset (existing logic)
        asset = await asset_service.create_or_update_asset(row_data)
        created_assets.append(asset)

        # 2. NEW: Canonical application deduplication
        if asset.application_name:
            # Use existing deduplication service
            canonical_app = await CanonicalApplication.find_or_create_canonical(
                db=db,
                application_name=asset.application_name,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                additional_context={
                    "technology_stack": asset.technology_stack,
                    "business_criticality": asset.business_criticality
                }
            )

            # 3. NEW: Create collection_flow_applications link
            cfa = CollectionFlowApplication(
                collection_flow_id=collection_flow_id,
                asset_id=asset.id,
                canonical_application_id=canonical_app.id,
                application_name=asset.application_name,
                deduplication_method="bulk_import_auto",
                match_confidence=canonical_app.confidence_score,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id
            )
            db.add(cfa)
            canonical_mappings.append(cfa)

    await db.commit()

    # 4. NEW: Trigger enrichment pipeline for all created assets
    await enrichment_pipeline.trigger_auto_enrichment(asset_ids=[a.id for a in created_assets])

    return {
        "success": True,
        "created_assets": len(created_assets),
        "canonical_mappings": len(canonical_mappings)
    }
```

---

### Solution 5: Automated Enrichment Pipeline (P1)

**New Service**: `backend/app/services/enrichment/auto_enrichment_pipeline.py`

```python
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.enrichment.agents import (
    ComplianceEnrichmentAgent,
    LicensingEnrichmentAgent,
    VulnerabilityEnrichmentAgent,
    ResilienceEnrichmentAgent,
    DependencyEnrichmentAgent,
    ProductMatchingAgent
)

class AutoEnrichmentPipeline:
    """
    Automated enrichment pipeline that triggers AI agents to populate
    enrichment tables for newly discovered/imported assets.
    """

    def __init__(self, db: AsyncSession, client_account_id: UUID, engagement_id: UUID):
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

        # Initialize enrichment agents
        self.agents = {
            "compliance": ComplianceEnrichmentAgent(db),
            "licensing": LicensingEnrichmentAgent(db),
            "vulnerability": VulnerabilityEnrichmentAgent(db),
            "resilience": ResilienceEnrichmentAgent(db),
            "dependency": DependencyEnrichmentAgent(db),
            "product_matching": ProductMatchingAgent(db)
        }

    async def trigger_auto_enrichment(self, asset_ids: List[UUID]):
        """
        Trigger enrichment agents for the given assets.

        This runs in the background (async task queue recommended for production).
        """
        for asset_id in asset_ids:
            # Run agents concurrently
            await asyncio.gather(
                self.agents["compliance"].enrich_asset(asset_id),
                self.agents["licensing"].enrich_asset(asset_id),
                self.agents["vulnerability"].enrich_asset(asset_id),
                self.agents["resilience"].enrich_asset(asset_id),
                self.agents["dependency"].enrich_asset(asset_id),
                self.agents["product_matching"].enrich_asset(asset_id)
            )

        # After enrichment, recalculate assessment readiness
        await self._recalculate_readiness(asset_ids)

    async def _recalculate_readiness(self, asset_ids: List[UUID]):
        """
        Recalculate assessment_readiness after enrichment completes.
        """
        from app.services.asset_service import AssetService

        asset_service = AssetService(self.db, self.client_account_id, self.engagement_id)

        for asset_id in asset_ids:
            await asset_service.calculate_assessment_readiness(asset_id)
```

**Example Enrichment Agent**: `backend/app/services/enrichment/agents/compliance_agent.py`

```python
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset, AssetComplianceFlag
from app.services.multi_model_service import multi_model_service, TaskComplexity

class ComplianceEnrichmentAgent:
    """
    AI agent that infers compliance requirements based on asset metadata.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def enrich_asset(self, asset_id: UUID):
        """
        Infer compliance_scopes, data_classification, residency for an asset.
        """
        # Get asset
        result = await self.db.execute(
            select(Asset).where(Asset.id == asset_id)
        )
        asset = result.scalar_one_or_none()

        if not asset:
            return

        # Build AI prompt for compliance inference
        prompt = f"""
Analyze the following asset and infer compliance requirements:

Asset Name: {asset.asset_name}
Asset Type: {asset.asset_type}
Technology Stack: {asset.technology_stack}
Business Criticality: {asset.business_criticality}
Data Sensitivity: {asset.data_sensitivity or 'Unknown'}
Location: {asset.location or 'Unknown'}

Based on this information, determine:
1. compliance_scopes: Which compliance frameworks apply? (e.g., GDPR, HIPAA, PCI-DSS, SOX)
2. data_classification: PUBLIC, INTERNAL, CONFIDENTIAL, or RESTRICTED
3. residency_requirements: Data residency constraints (e.g., "EU", "US", "None")

Respond in JSON format:
{{
  "compliance_scopes": ["framework1", "framework2"],
  "data_classification": "CONFIDENTIAL",
  "residency_requirements": "EU",
  "confidence_score": 0.85,
  "reasoning": "Brief explanation"
}}
"""

        # Call LLM (tracked automatically)
        response = await multi_model_service.generate_response(
            prompt=prompt,
            task_type="compliance_analysis",
            complexity=TaskComplexity.SIMPLE,
            context={
                "feature": "enrichment_pipeline",
                "agent": "compliance"
            }
        )

        # Parse response
        import json
        result = json.loads(response)

        # Create AssetComplianceFlag entry
        compliance_flag = AssetComplianceFlag(
            asset_id=asset.id,
            compliance_scopes=result["compliance_scopes"],
            data_classification=result["data_classification"],
            residency_requirements=result["residency_requirements"],
            confidence_score=result["confidence_score"],
            reasoning=result["reasoning"],
            client_account_id=asset.client_account_id,
            engagement_id=asset.engagement_id
        )

        self.db.add(compliance_flag)
        await self.db.commit()
```

**ADR Compliance Notes**:

Per architectural decision records, the enrichment agents MUST follow these patterns:

1. **Persistent Agent Architecture (ADR-015)**:
   - Enrichment agents should use `TenantScopedAgentPool` for persistence
   - Agents maintained as singletons per `(client_account_id, engagement_id)` tuple
   - Avoid creating new agent instances per enrichment task

```python
# Enhanced implementation using persistent agents
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool

class AutoEnrichmentPipeline:
    def __init__(self, db: AsyncSession, client_account_id: UUID, engagement_id: UUID):
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.agent_pool = TenantScopedAgentPool()

    async def trigger_auto_enrichment(self, asset_ids: List[UUID]):
        # Get or create persistent enrichment agents
        compliance_agent = await self.agent_pool.get_or_create_agent(
            client_id=str(self.client_account_id),
            engagement_id=str(self.engagement_id),
            agent_type="compliance_enrichment"
        )

        # ... similar for other agents ...
```

2. **TenantMemoryManager Integration (ADR-024)**:
   - Enrichment agents should store learned patterns using `TenantMemoryManager`
   - Retrieve similar enrichment patterns before processing new assets
   - CrewAI memory is DISABLED (`memory=False`) - use TenantMemoryManager instead

```python
# After successful enrichment
from app.services.crewai_flows.memory.tenant_memory_manager import (
    TenantMemoryManager, LearningScope
)

memory_manager = TenantMemoryManager(crewai_service=crewai_service, database_session=db)

await memory_manager.store_learning(
    client_account_id=self.client_account_id,
    engagement_id=self.engagement_id,
    scope=LearningScope.ENGAGEMENT,
    pattern_type="compliance_enrichment",
    pattern_data={
        "asset_type": asset.asset_type,
        "inferred_compliance": result["compliance_scopes"],
        "confidence": result["confidence_score"],
        "reasoning": result["reasoning"]
    }
)

# Before enrichment - retrieve similar patterns
patterns = await memory_manager.retrieve_similar_patterns(
    client_account_id=self.client_account_id,
    engagement_id=self.engagement_id,
    scope=LearningScope.ENGAGEMENT,
    pattern_type="compliance_enrichment",
    query_context={"asset_type": asset.asset_type}
)
```

3. **LLM Usage Tracking (Mandatory)**:
   - ALL LLM calls use `multi_model_service.generate_response()` for automatic tracking
   - Tracked to `llm_usage_logs` table with cost calculation
   - Already implemented in example above ✓

4. **Master Flow Orchestrator (ADR-006)**:
   - Enrichment pipeline should register with Master Flow if run as standalone flow
   - For background enrichment (triggered by asset creation), no registration needed
   - Use `/api/v1/master-flows/*` endpoints for any user-facing enrichment operations

---

### Solution 6: Enhanced Collection → Assessment Handoff (P1)

**Update Assessment Initialization**: `backend/app/services/flow_commands.py: create_assessment_flow()`

```python
async def create_assessment_flow(
    db: AsyncSession,
    collection_flow_id: UUID,
    context: RequestContext
) -> AssessmentFlow:
    """
    Create Assessment flow from completed Collection flow.

    Enhanced to include:
    - Canonical application resolution
    - Asset grouping by application
    - Enrichment status summary
    - Readiness summary
    """
    # Get collection flow
    collection_flow = await get_collection_flow(db, collection_flow_id, context)

    # Get selected asset IDs from collection
    asset_ids = await get_collection_selected_assets(db, collection_flow_id)

    # Initialize resolver
    resolver = AssessmentApplicationResolver(db, context.client_account_id, context.engagement_id)

    # Resolve assets to applications (with grouping)
    application_groups = await resolver.resolve_assets_to_applications(
        asset_ids=asset_ids,
        collection_flow_id=collection_flow_id
    )

    # Calculate enrichment status
    enrichment_status = await resolver.calculate_enrichment_status(asset_ids)

    # Calculate readiness summary
    readiness_summary = await resolver.calculate_readiness_summary(asset_ids)

    # Extract canonical application IDs
    canonical_app_ids = [
        group.canonical_application_id
        for group in application_groups
        if group.canonical_application_id
    ]

    # Create Assessment flow with rich metadata
    assessment_flow = AssessmentFlow(
        # Legacy field (backward compatibility)
        selected_application_ids=asset_ids,

        # NEW: Proper semantic fields
        selected_asset_ids=asset_ids,
        selected_canonical_application_ids=canonical_app_ids,
        application_asset_groups=[group.dict() for group in application_groups],
        enrichment_status=enrichment_status,
        readiness_summary=readiness_summary,

        # Standard fields
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id,
        flow_metadata={
            "source_collection": {
                "collection_flow_id": str(collection_flow_id),
                "transitioned_from": datetime.utcnow().isoformat()
            }
        }
    )

    db.add(assessment_flow)
    await db.commit()
    await db.refresh(assessment_flow)

    return assessment_flow
```

---

### Solution 7: Frontend UI Enhancements (P0 + P2)

#### Component 1: Application Groups Widget

**File**: `src/components/assessment/ApplicationGroupsWidget.tsx`

```typescript
import React from 'react';
import { ChevronDown, ChevronRight, Server, Database, Network, Check, AlertCircle } from 'lucide-react';

interface ApplicationGroup {
  canonical_application_id: string | null;
  canonical_application_name: string;
  asset_count: number;
  asset_types: string[];
  assets: Array<{
    asset_id: string;
    asset_name: string;
    asset_type: string;
    environment: string;
    assessment_readiness: 'ready' | 'not_ready' | 'in_progress';
  }>;
  readiness_summary: {
    ready: number;
    not_ready: number;
    in_progress: number;
  };
}

interface ApplicationGroupsWidgetProps {
  groups: ApplicationGroup[];
}

export const ApplicationGroupsWidget: React.FC<ApplicationGroupsWidgetProps> = ({ groups }) => {
  const [expandedGroups, setExpandedGroups] = React.useState<Set<string>>(new Set());

  const toggleGroup = (groupId: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      if (next.has(groupId)) {
        next.delete(groupId);
      } else {
        next.add(groupId);
      }
      return next;
    });
  };

  const getAssetIcon = (assetType: string) => {
    switch (assetType) {
      case 'server': return <Server className="h-4 w-4" />;
      case 'database': return <Database className="h-4 w-4" />;
      case 'network_device': return <Network className="h-4 w-4" />;
      default: return <Server className="h-4 w-4" />;
    }
  };

  const getReadinessIcon = (readiness: string) => {
    switch (readiness) {
      case 'ready': return <Check className="h-4 w-4 text-green-500" />;
      case 'not_ready': return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'in_progress': return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default: return null;
    }
  };

  const calculateReadinessPercent = (summary: ApplicationGroup['readiness_summary']) => {
    const total = summary.ready + summary.not_ready + summary.in_progress;
    return total > 0 ? Math.round((summary.ready / total) * 100) : 0;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          Selected Applications ({groups.length} {groups.length === 1 ? 'application' : 'applications'})
        </h3>
        <div className="text-sm text-gray-500">
          Total Assets: {groups.reduce((sum, g) => sum + g.asset_count, 0)}
        </div>
      </div>

      {groups.map((group) => {
        const groupId = group.canonical_application_id || `unmapped-${group.canonical_application_name}`;
        const isExpanded = expandedGroups.has(groupId);
        const readinessPercent = calculateReadinessPercent(group.readiness_summary);

        return (
          <div key={groupId} className="border rounded-lg p-4 bg-white shadow-sm">
            {/* Application Header */}
            <div
              className="flex items-center justify-between cursor-pointer"
              onClick={() => toggleGroup(groupId)}
            >
              <div className="flex items-center gap-3 flex-1">
                {isExpanded ? (
                  <ChevronDown className="h-5 w-5 text-gray-400" />
                ) : (
                  <ChevronRight className="h-5 w-5 text-gray-400" />
                )}

                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-gray-900">
                      {group.canonical_application_name}
                    </h4>
                    {!group.canonical_application_id && (
                      <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                        Unmapped
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                    <span>{group.asset_count} asset{group.asset_count !== 1 ? 's' : ''}</span>
                    <span>•</span>
                    <span>{group.asset_types.join(', ')}</span>
                  </div>
                </div>

                {/* Readiness Summary */}
                <div className="text-right">
                  <div className="text-sm font-semibold text-gray-900">
                    {readinessPercent}% Ready
                  </div>
                  <div className="text-xs text-gray-500">
                    {group.readiness_summary.ready}/{group.asset_count} assets
                  </div>
                </div>
              </div>
            </div>

            {/* Expanded Asset List */}
            {isExpanded && (
              <div className="mt-4 pl-8 space-y-2 border-t pt-4">
                {group.assets.map((asset) => (
                  <div
                    key={asset.asset_id}
                    className="flex items-center justify-between p-2 rounded hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-3">
                      {getAssetIcon(asset.asset_type)}
                      <div>
                        <div className="font-medium text-sm">{asset.asset_name}</div>
                        <div className="text-xs text-gray-500">
                          {asset.asset_type} • {asset.environment}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {getReadinessIcon(asset.assessment_readiness)}
                      <span className="text-xs capitalize">
                        {asset.assessment_readiness.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
```

#### Component 2: Readiness Dashboard Widget

**File**: `src/components/assessment/ReadinessDashboardWidget.tsx`

```typescript
import React from 'react';
import { AlertCircle, CheckCircle, Clock, TrendingUp } from 'lucide-react';

interface AssetReadiness {
  asset_id: string;
  asset_name: string;
  assessment_readiness: 'ready' | 'not_ready' | 'in_progress';
  completeness_score: number;
  assessment_blockers: string[];
  missing_critical_attributes: string[];
}

interface ReadinessDashboardProps {
  assets: AssetReadiness[];
}

const CRITICAL_ATTRIBUTES_DESCRIPTIONS = {
  application_name: 'Application Name - Primary identifier for the application',
  technology_stack: 'Technology Stack - Programming languages and frameworks used',
  operating_system: 'Operating System - OS running on the asset',
  cpu_cores: 'CPU Cores - Number of processor cores',
  memory_gb: 'Memory (GB) - RAM capacity',
  storage_gb: 'Storage (GB) - Disk capacity',
  business_criticality: 'Business Criticality - Impact on business operations',
  application_type: 'Application Type - Category (web, mobile, backend, etc.)',
  architecture_pattern: 'Architecture Pattern - Microservices, monolith, etc.',
  dependencies: 'Dependencies - Integrations with other systems',
  user_base: 'User Base - Number and type of users',
  data_sensitivity: 'Data Sensitivity - Level of data protection required',
  compliance_requirements: 'Compliance Requirements - Regulatory frameworks (GDPR, HIPAA)',
  sla_requirements: 'SLA Requirements - Uptime and performance guarantees',
  business_owner: 'Business Owner - Person responsible for business decisions',
  annual_operating_cost: 'Annual Operating Cost - Yearly cost to operate',
  business_value: 'Business Value - Revenue or strategic importance',
  strategic_importance: 'Strategic Importance - Priority in business strategy',
  code_quality_score: 'Code Quality Score - Technical debt assessment',
  last_update_date: 'Last Update Date - When application was last updated',
  support_status: 'Support Status - Vendor support availability',
  known_vulnerabilities: 'Known Vulnerabilities - Security issues identified'
};

export const ReadinessDashboardWidget: React.FC<ReadinessDashboardProps> = ({ assets }) => {
  const readyCount = assets.filter(a => a.assessment_readiness === 'ready').length;
  const notReadyCount = assets.filter(a => a.assessment_readiness === 'not_ready').length;
  const inProgressCount = assets.filter(a => a.assessment_readiness === 'in_progress').length;

  const avgCompleteness = assets.length > 0
    ? Math.round(assets.reduce((sum, a) => sum + a.completeness_score, 0) / assets.length * 100)
    : 0;

  // Group assets by readiness status
  const notReadyAssets = assets.filter(a => a.assessment_readiness === 'not_ready');

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Ready for Assessment</p>
              <p className="text-2xl font-bold text-green-600">{readyCount}</p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Not Ready</p>
              <p className="text-2xl font-bold text-red-600">{notReadyCount}</p>
            </div>
            <AlertCircle className="h-8 w-8 text-red-500" />
          </div>
        </div>

        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">In Progress</p>
              <p className="text-2xl font-bold text-yellow-600">{inProgressCount}</p>
            </div>
            <Clock className="h-8 w-8 text-yellow-500" />
          </div>
        </div>

        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Avg Completeness</p>
              <p className="text-2xl font-bold text-blue-600">{avgCompleteness}%</p>
            </div>
            <TrendingUp className="h-8 w-8 text-blue-500" />
          </div>
        </div>
      </div>

      {/* Blockers Details */}
      {notReadyAssets.length > 0 && (
        <div className="bg-white border rounded-lg p-6">
          <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-red-500" />
            Assessment Blockers
          </h4>

          <div className="space-y-4">
            {notReadyAssets.map((asset) => (
              <div key={asset.asset_id} className="border rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h5 className="font-semibold">{asset.asset_name}</h5>
                    <div className="text-sm text-gray-500 mt-1">
                      Completeness: {Math.round(asset.completeness_score * 100)}%
                    </div>
                  </div>

                  <div className="px-3 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                    Not Ready
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                  <div
                    className="bg-red-500 h-2 rounded-full"
                    style={{ width: `${asset.completeness_score * 100}%` }}
                  />
                </div>

                {/* Missing Attributes */}
                {asset.missing_critical_attributes.length > 0 && (
                  <div className="mb-3">
                    <p className="text-sm font-semibold text-gray-700 mb-2">
                      Missing Critical Attributes ({asset.missing_critical_attributes.length}):
                    </p>
                    <ul className="space-y-1">
                      {asset.missing_critical_attributes.slice(0, 5).map((attr) => (
                        <li key={attr} className="text-sm flex items-start gap-2">
                          <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                          <div>
                            <span className="font-medium">{attr.replace(/_/g, ' ')}</span>
                            {CRITICAL_ATTRIBUTES_DESCRIPTIONS[attr] && (
                              <span className="text-gray-500 ml-1">
                                - {CRITICAL_ATTRIBUTES_DESCRIPTIONS[attr]}
                              </span>
                            )}
                          </div>
                        </li>
                      ))}
                      {asset.missing_critical_attributes.length > 5 && (
                        <li className="text-sm text-gray-500">
                          ... and {asset.missing_critical_attributes.length - 5} more
                        </li>
                      )}
                    </ul>
                  </div>
                )}

                {/* Blockers */}
                {asset.assessment_blockers.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-gray-700 mb-2">
                      Assessment Blockers:
                    </p>
                    <ul className="space-y-1">
                      {asset.assessment_blockers.map((blocker) => (
                        <li key={blocker} className="text-sm flex items-start gap-2">
                          <span className="text-red-500">•</span>
                          <span>{blocker.replace(/_/g, ' ')}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Action Button */}
                <button
                  className="mt-4 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
                  onClick={() => {
                    // Navigate to Collection flow to fill gaps
                    window.location.href = `/collection?asset_id=${asset.asset_id}`;
                  }}
                >
                  Collect Missing Data
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Ready Assets Summary */}
      {readyCount > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <h4 className="font-semibold text-green-900">
              {readyCount} {readyCount === 1 ? 'Asset' : 'Assets'} Ready for Assessment
            </h4>
          </div>
          <p className="text-sm text-green-700">
            These assets have sufficient data to proceed with 6R assessment. You can start the assessment process.
          </p>
        </div>
      )}
    </div>
  );
};
```

#### Integration into Assessment Overview Page

**File**: `src/pages/assessment/AssessmentFlowOverview.tsx`

```typescript
import { ApplicationGroupsWidget } from '@/components/assessment/ApplicationGroupsWidget';
import { ReadinessDashboardWidget } from '@/components/assessment/ReadinessDashboardWidget';
import { useAssessmentApplications, useAssessmentReadiness } from '@/hooks/useAssessmentData';

export const AssessmentFlowOverview: React.FC<{ flowId: string }> = ({ flowId }) => {
  // Fetch applications with asset groupings
  const { data: applicationsData, isLoading: appsLoading } = useAssessmentApplications(flowId);

  // Fetch readiness data
  const { data: readinessData, isLoading: readinessLoading } = useAssessmentReadiness(flowId);

  if (appsLoading || readinessLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-8 p-6">
      <div>
        <h1 className="text-2xl font-bold">Assessment Overview</h1>
        <p className="text-gray-500 mt-1">
          Review selected applications and assessment readiness
        </p>
      </div>

      {/* Application Groups Widget */}
      <ApplicationGroupsWidget groups={applicationsData.applications} />

      {/* Readiness Dashboard */}
      <ReadinessDashboardWidget
        assets={applicationsData.applications.flatMap(app => app.assets)}
      />

      {/* Existing assessment configuration, 6R analysis, etc. */}
      {/* ... */}
    </div>
  );
};
```

---

## Implementation Plan & Tracker

### Phase 1: Database & Data Model (Week 1)

**Days 1-2: Database Migration**
- [ ] Create migration `093_assessment_data_model_refactor.py`
- [ ] Add new columns to `assessment_flows` table
- [ ] Migrate existing data (selected_application_ids → selected_asset_ids)
- [ ] Add indexes for performance
- [ ] Test migration on staging database

**Days 3-4: SQLAlchemy & Pydantic Models**
- [ ] Update `AssessmentFlow` SQLAlchemy model
- [ ] Create Pydantic schemas: `ApplicationAssetGroup`, `EnrichmentStatus`, `ReadinessSummary`
- [ ] Update existing schemas to include new fields
- [ ] Write unit tests for model validation

**Day 5: Assessment Application Resolver Service**
- [ ] Implement `AssessmentApplicationResolver` class
- [ ] Method: `resolve_assets_to_applications()`
- [ ] Method: `calculate_enrichment_status()`
- [ ] Method: `calculate_readiness_summary()`
- [ ] Write unit tests for resolver logic

---

### Phase 2: Backend Services & Endpoints (Week 2)

**Days 6-7: Assessment Endpoints Enhancement**
- [ ] Enhance existing `/master-flows/{flow_id}/assessment-applications` endpoint (master_flows_assessment.py:199-331)
- [ ] Replace Discovery-based metadata with AssessmentApplicationResolver
- [ ] Add canonical application grouping logic
- [ ] Create `/master-flows/{flow_id}/assessment-readiness` endpoint (NEW)
- [ ] Create `/master-flows/{flow_id}/assessment-progress` endpoint (NEW)
- [ ] Update response schemas for enhanced data structures
- [ ] Write endpoint unit tests

**Days 8-9: Enhanced Assessment Initialization**
- [ ] Update `create_assessment_flow()` in flow_commands.py
- [ ] Add canonical application resolution
- [ ] Build application_asset_groups structure
- [ ] Calculate enrichment_status and readiness_summary
- [ ] Write integration tests for handoff

**Day 10: Canonical Deduplication in Bulk Import**
- [ ] Update `/collection/bulk-import` endpoint
- [ ] Add canonical deduplication step
- [ ] Create `collection_flow_applications` entries
- [ ] Write tests for bulk import with deduplication

---

### Phase 3: Automated Enrichment Pipeline (Week 3)

**Days 11-12: Enrichment Pipeline Framework**
- [ ] Create `AutoEnrichmentPipeline` class
- [ ] Define enrichment agent interface
- [ ] Implement agent orchestration logic
- [ ] Add async task queue integration (Celery or similar)
- [ ] Write pipeline tests

**Days 13-15: Enrichment Agents Implementation**
- [ ] Implement `ComplianceEnrichmentAgent`
- [ ] Implement `LicensingEnrichmentAgent`
- [ ] Implement `VulnerabilityEnrichmentAgent`
- [ ] Implement `ResilienceEnrichmentAgent`
- [ ] Implement `DependencyEnrichmentAgent`
- [ ] Implement `ProductMatchingAgent`
- [ ] Write tests for each agent

**Day 16: Integration & Testing**
- [ ] Integrate enrichment pipeline into asset creation flow
- [ ] Test with sample assets (servers, databases, applications)
- [ ] Verify enrichment tables populated correctly
- [ ] Performance testing (50+ assets)

---

### Phase 4: Frontend UI Implementation (Week 4)

**Days 17-18: Application Groups Widget**
- [ ] Create `ApplicationGroupsWidget.tsx` component
- [ ] Implement hierarchical display (collapsible groups)
- [ ] Add readiness indicators per group
- [ ] Write component unit tests
- [ ] Style and responsive design

**Days 19-20: Readiness Dashboard Widget**
- [ ] Create `ReadinessDashboardWidget.tsx` component
- [ ] Implement summary cards (ready, not ready, in progress)
- [ ] Display missing critical attributes
- [ ] Show assessment blockers with guidance
- [ ] Add "Collect Missing Data" action button
- [ ] Write component tests

**Day 21: Frontend Service Layer**
- [ ] Update `masterFlowService.ts`
- [ ] Add `getAssessmentApplications()` method
- [ ] Add `getAssessmentReadiness()` method
- [ ] Add `getAssessmentProgress()` method
- [ ] Implement proper error handling

**Day 22: Integration into Assessment Overview**
- [ ] Update `AssessmentFlowOverview.tsx` page
- [ ] Integrate `ApplicationGroupsWidget`
- [ ] Integrate `ReadinessDashboardWidget`
- [ ] Add loading states and error boundaries
- [ ] Test with real Assessment flows

---

### Phase 5: Testing & Validation (Week 5)

**Days 23-24: Integration Testing**
- [ ] End-to-end test: Discovery → Collection → Assessment
- [ ] End-to-end test: Bulk Import → Enrichment → Assessment
- [ ] Test multi-asset-type scenarios (servers + databases + network devices)
- [ ] Test canonical deduplication across flows
- [ ] Test enrichment pipeline with 100+ assets

**Day 25: UI/UX Testing**
- [ ] Manual testing of all UI components
- [ ] Test responsive design (mobile, tablet, desktop)
- [ ] Accessibility testing (WCAG compliance)
- [ ] User acceptance testing with sample data

**Day 26: Performance & Load Testing**
- [ ] Load test with 500+ assets
- [ ] Query performance optimization
- [ ] Frontend rendering performance
- [ ] Identify and fix bottlenecks

**Day 27: Bug Fixes & Polish**
- [ ] Fix issues from testing phase
- [ ] Code review and refactoring
- [ ] Documentation updates
- [ ] Prepare deployment checklist

---

### Phase 6: Deployment & Monitoring (Week 6)

**Day 28: Staging Deployment**
- [ ] Deploy database migration to staging
- [ ] Deploy backend changes to staging
- [ ] Deploy frontend changes to staging
- [ ] Smoke test all endpoints

**Day 29: Production Deployment**
- [ ] Database migration to production
- [ ] Backend deployment (zero-downtime)
- [ ] Frontend deployment
- [ ] Verify all endpoints working

**Day 30: Monitoring & Support**
- [ ] Set up monitoring dashboards
- [ ] Configure alerts for errors
- [ ] Monitor LLM usage for enrichment agents
- [ ] Gather user feedback
- [ ] Document lessons learned

---

## Success Metrics

### Functional Metrics
- [ ] 100% of Assessment flows display selected applications correctly
- [ ] 100% of assets show assessment readiness status
- [ ] 90%+ of bulk imported applications deduplicated via canonical registry
- [ ] 70%+ of assets have enrichment data auto-populated within 24 hours
- [ ] 0 critical bugs in production for 7 days

### Performance Metrics
- [ ] `/assessment-applications` endpoint responds < 500ms (95th percentile)
- [ ] Enrichment pipeline processes 100 assets < 10 minutes
- [ ] UI loads Assessment Overview < 2 seconds

### User Experience Metrics
- [ ] Users can identify missing data in < 30 seconds
- [ ] 80%+ reduction in support tickets for "Why can't I assess?"
- [ ] 60%+ faster gap remediation with AI suggestions

---

## Risk Management

### Technical Risks

1. **Query Performance Degradation**
   - Risk: Complex joins slow down with 1000+ assets
   - Mitigation: Add database indexes, implement pagination, cache responses
   - Fallback: Pre-compute application groups at Assessment creation

2. **LLM API Rate Limits**
   - Risk: Enrichment agents hit API rate limits
   - Mitigation: Implement rate limiting, queue management, retry logic
   - Fallback: Process enrichment in batches (10 assets/minute)

3. **Data Migration Failures**
   - Risk: Existing assessment flows fail after migration
   - Mitigation: Thorough testing on staging, backward compatibility
   - Fallback: Rollback plan with data backup

### Business Risks

4. **User Confusion from UI Changes**
   - Risk: Users struggle with new hierarchical display
   - Mitigation: User training materials, tooltips, gradual rollout
   - Fallback: Feature flag to toggle between old/new UI

5. **Enrichment Accuracy Concerns**
   - Risk: AI agents populate incorrect data
   - Mitigation: Confidence scores, human review workflow, feedback loop
   - Fallback: Manual enrichment option always available

---

## Approval Checklist

Before proceeding with implementation:

- [ ] Solution addresses ALL identified gaps (P0, P1, P2)
- [ ] Proper data model with semantic correctness
- [ ] Automated enrichment pipeline reduces manual burden
- [ ] Comprehensive UI visibility into readiness and blockers
- [ ] Clear implementation plan with realistic timeline (6 weeks)
- [ ] Success metrics and risk mitigations defined
- [ ] Backward compatibility maintained
- [ ] Testing strategy covers unit, integration, E2E
- [ ] Deployment plan with rollback strategy

---

**Document Status**: Ready for Review
**Timeline**: 6 weeks (30 working days)
**Team Requirements**: 2 backend engineers, 1 frontend engineer, 1 QA engineer
**Next Step**: Await user approval to proceed with Phase 1 implementation
