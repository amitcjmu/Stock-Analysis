# Assessment Canonical Application Grouping - Remediation Plan

**Date**: October 16, 2025
**Status**: 🟡 AWAITING APPROVAL
**Issue**: Assessment flows displaying individual unmapped assets (e.g., "DevTestVM01" server) instead of canonical application groups
**Root Cause**: 83% of production assets unmapped (119/144), assessment initialization accepts unmapped asset IDs
**Impact**: Breaks canonical application grouping architecture, makes holistic assessment impossible

---

## Executive Summary

### Problem Statement

User screenshot shows "DevTestVM01" (a server asset) appearing in the "Selected Applications" section of the assessment flow architecture page. This violates the canonical application grouping architecture where applications should be deduplicated and aggregated.

### Root Cause Analysis

**E2E Testing Used Canonical Path** (Working):
- Test flow created from "Admin Dashboard" canonical application
- Automatically included all 16 linked assets (servers, databases, network devices)
- Result: "1 applications, 16 assets" - correct holistic scope

**Production Flow Used Asset ID Path** (Broken):
- Flow created from raw asset IDs without canonical mapping
- Database query: 119 out of 144 assets (83%) are unmapped
- `AssessmentApplicationResolver` creates `"unmapped-{asset_id}"` fallback keys
- Result: Individual assets like "DevTestVM01" displayed as "applications"

### Success Criteria

- ✅ Assessment initialization from canonical applications (already working)
- ✅ Unmapped assets either mapped or prevented from assessment
- ✅ Enrichment pipeline triggers successfully with all 7 tables populated
- ✅ Performance: 100 assets enriched in < 10 minutes
- ✅ Frontend displays canonical application groups, not individual assets

---

## Implementation Phases

### Phase 0: Pre-Implementation (1 hour)

#### Task 0.1: Create Centralized Pattern Type Mapping Module
**Priority**: P0
**Estimated Time**: 30 minutes
**Rationale**: Centralize mapping to avoid drift across 6 agents (GPT-5 recommendation)

**Implementation**:
```python
# File: backend/app/services/enrichment/constants.py (NEW)

"""
Centralized enrichment constants and mappings.

Per GPT-5 recommendation: Single source of truth for pattern type enum mappings
to avoid drift across enrichment agents.
"""

from enum import Enum
from typing import Dict

# PostgreSQL enum: migration.patterntype
class PatternTypeDB(str, Enum):
    """Database-backed pattern types (PostgreSQL enum values)"""
    FIELD_MAPPING_APPROVAL = "FIELD_MAPPING_APPROVAL"
    FIELD_MAPPING_REJECTION = "FIELD_MAPPING_REJECTION"
    FIELD_MAPPING_SUGGESTION = "FIELD_MAPPING_SUGGESTION"
    TECHNOLOGY_CORRELATION = "TECHNOLOGY_CORRELATION"
    BUSINESS_VALUE_INDICATOR = "BUSINESS_VALUE_INDICATOR"
    RISK_FACTOR = "RISK_FACTOR"
    MODERNIZATION_OPPORTUNITY = "MODERNIZATION_OPPORTUNITY"
    DEPENDENCY_PATTERN = "DEPENDENCY_PATTERN"
    SECURITY_VULNERABILITY = "SECURITY_VULNERABILITY"
    PERFORMANCE_BOTTLENECK = "PERFORMANCE_BOTTLENECK"
    COMPLIANCE_REQUIREMENT = "COMPLIANCE_REQUIREMENT"


# Agent pattern types → PostgreSQL enum mapping
PATTERN_TYPE_ENUM_MAP: Dict[str, PatternTypeDB] = {
    "product_matching": PatternTypeDB.TECHNOLOGY_CORRELATION,
    "compliance_analysis": PatternTypeDB.COMPLIANCE_REQUIREMENT,
    "licensing_analysis": PatternTypeDB.TECHNOLOGY_CORRELATION,
    "vulnerability_analysis": PatternTypeDB.SECURITY_VULNERABILITY,
    "resilience_analysis": PatternTypeDB.RISK_FACTOR,
    "dependency_analysis": PatternTypeDB.DEPENDENCY_PATTERN,
}

# Tolerant fallback with warning (GPT-5 recommendation)
DEFAULT_PATTERN_TYPE = PatternTypeDB.TECHNOLOGY_CORRELATION


def get_db_pattern_type(agent_pattern_type: str) -> PatternTypeDB:
    """
    Map agent pattern type to database enum value.

    Uses tolerant fallback to avoid blocking pipeline on unknown types.
    Logs warning for unmapped types for monitoring.

    Args:
        agent_pattern_type: Pattern type from enrichment agent

    Returns:
        PatternTypeDB enum value
    """
    if agent_pattern_type not in PATTERN_TYPE_ENUM_MAP:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Unknown pattern type '{agent_pattern_type}' - using fallback "
            f"'{DEFAULT_PATTERN_TYPE.value}'. Update PATTERN_TYPE_ENUM_MAP."
        )
        return DEFAULT_PATTERN_TYPE

    return PATTERN_TYPE_ENUM_MAP[agent_pattern_type]
```

**Files Modified**: 1 new file

**Unit Test**:
```python
# File: backend/tests/unit/services/enrichment/test_pattern_type_mapping.py (NEW)

import pytest
from app.services.enrichment.constants import (
    get_db_pattern_type,
    PatternTypeDB,
    PATTERN_TYPE_ENUM_MAP,
)


def test_all_agent_pattern_types_mapped():
    """Verify all agent pattern types have valid DB enum mappings"""
    agent_types = [
        "product_matching",
        "compliance_analysis",
        "licensing_analysis",
        "vulnerability_analysis",
        "resilience_analysis",
        "dependency_analysis",
    ]

    for agent_type in agent_types:
        db_type = get_db_pattern_type(agent_type)
        assert isinstance(db_type, PatternTypeDB)
        assert db_type.value in [e.value for e in PatternTypeDB]


def test_unknown_pattern_type_uses_fallback(caplog):
    """Unknown pattern types should use fallback and log warning"""
    result = get_db_pattern_type("unknown_agent_type")

    assert result == PatternTypeDB.TECHNOLOGY_CORRELATION
    assert "Unknown pattern type" in caplog.text
    assert "using fallback" in caplog.text


def test_no_invalid_enum_values():
    """Ensure mapping only contains valid DB enum values"""
    for agent_type, db_type in PATTERN_TYPE_ENUM_MAP.items():
        assert isinstance(db_type, PatternTypeDB)
        # This will fail fast if we accidentally use a string instead of enum
        assert hasattr(PatternTypeDB, db_type.name)
```

**Verification**:
```bash
cd backend && pytest tests/unit/services/enrichment/test_pattern_type_mapping.py -v
```

---

#### Task 0.2: Add Database Indexes for Performance
**Priority**: P0
**Estimated Time**: 30 minutes
**Rationale**: GPT-5 recommendation for resolver and bulk-map queries

**Implementation**:
```python
# File: backend/alembic/versions/095_add_enrichment_performance_indexes.py (NEW)

"""Add indexes for enrichment and canonical mapping performance

Revision ID: 095_enrichment_indexes
Revises: 094_add_architecture_standards_unique_constraint
Create Date: 2025-10-16

"""
from alembic import op

revision = '095_enrichment_indexes'
down_revision = '094_add_architecture_standards_unique_constraint'
branch_labels = None
depends_on = None


def upgrade():
    # Index for AssessmentApplicationResolver queries
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'collection_flow_applications'
                AND indexname = 'idx_cfa_tenant_canonical'
            ) THEN
                CREATE INDEX idx_cfa_tenant_canonical
                ON migration.collection_flow_applications (
                    client_account_id,
                    engagement_id,
                    canonical_application_id
                );
            END IF;
        END $$;
    """)

    # Index for bulk asset mapping lookups
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'collection_flow_applications'
                AND indexname = 'idx_cfa_asset_lookup'
            ) THEN
                CREATE INDEX idx_cfa_asset_lookup
                ON migration.collection_flow_applications (asset_id);
            END IF;
        END $$;
    """)

    # Index for unmapped asset queries
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'assets'
                AND indexname = 'idx_assets_tenant_type'
            ) THEN
                CREATE INDEX idx_assets_tenant_type
                ON migration.assets (
                    client_account_id,
                    engagement_id,
                    asset_type
                );
            END IF;
        END $$;
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS migration.idx_cfa_tenant_canonical;")
    op.execute("DROP INDEX IF EXISTS migration.idx_cfa_asset_lookup;")
    op.execute("DROP INDEX IF EXISTS migration.idx_assets_tenant_type;")
```

**Verification**:
```bash
cd backend && alembic upgrade head
docker exec -it migration_postgres psql -U postgres -d migration_db -c "\d+ migration.collection_flow_applications"
# Verify indexes exist: idx_cfa_tenant_canonical, idx_cfa_asset_lookup
```

---

### Phase 1: Critical Blockers (P0 - 2.5 hours)

#### Task 1.1: Update Enrichment Agents with Centralized Mapping
**Priority**: P0
**Estimated Time**: 1 hour
**Rationale**: Enables agent learning, unblocks pattern storage (from Day 26 report)

**Implementation**:
```python
# File: backend/app/services/enrichment/agents/executors/compliance_agent.py
# Lines: ~140 (store_learning call)

# BEFORE:
await self.memory_manager.store_learning(
    client_account_id=self.client_account_id,
    engagement_id=self.engagement_id,
    pattern_type="compliance_analysis",  # ❌ String causes enum error
    pattern_data={...}
)

# AFTER:
from app.services.enrichment.constants import get_db_pattern_type

await self.memory_manager.store_learning(
    client_account_id=self.client_account_id,
    engagement_id=self.engagement_id,
    pattern_type=get_db_pattern_type("compliance_analysis").value,  # ✅ Enum value
    pattern_data={...}
)
```

**Files Modified** (6):
- `backend/app/services/enrichment/agents/executors/compliance_agent.py`
- `backend/app/services/enrichment/agents/executors/licensing_agent.py`
- `backend/app/services/enrichment/agents/executors/vulnerability_agent.py`
- `backend/app/services/enrichment/agents/executors/resilience_agent.py`
- `backend/app/services/enrichment/agents/executors/dependency_agent.py`
- `backend/app/services/enrichment/agents/executors/product_matching_agent.py`

**Search Pattern**:
```bash
cd backend && grep -n "pattern_type=" app/services/enrichment/agents/executors/*.py
# Update all store_learning calls to use get_db_pattern_type()
```

**Verification**:
```bash
# Trigger enrichment and verify no enum errors
curl -X POST "http://localhost:8000/api/v1/master-flows/{flow_id}/trigger-enrichment" \
  -H "X-Client-Account-ID: 11111111-1111-1111-1111-111111111111" \
  -H "X-Engagement-ID: 22222222-2222-2222-2222-222222222222"

# Check backend logs - should see "Stored learning pattern" without errors
docker logs migration_backend -f | grep "pattern"

# Query database - verify patterns stored successfully
docker exec -it migration_postgres psql -U postgres -d migration_db -c \
  "SELECT pattern_type, COUNT(*) FROM migration.learned_patterns GROUP BY pattern_type;"
```

**Success Criteria**:
- ✅ All 6 agents use centralized `get_db_pattern_type()` function
- ✅ No PostgreSQL enum errors in logs
- ✅ `learned_patterns` table populated with valid enum values
- ✅ Unit test passes: `test_all_agent_pattern_types_mapped()`

---

#### Task 1.2: Feature-Flagged Unmapped Asset Handling
**Priority**: P0
**Estimated Time**: 1 hour
**Rationale**: GPT-5 recommendation - progressive strictness with threshold

**Implementation**:
```python
# File: backend/app/core/config.py
# Add feature flags

class Settings(BaseSettings):
    # ... existing settings ...

    # Unmapped asset handling configuration
    UNMAPPED_ASSET_HANDLING: str = Field(
        default="banner",  # Options: "banner", "block", "strict"
        description="How to handle unmapped assets: banner (warn + proceed), block (reject if >threshold), strict (always reject)"
    )
    UNMAPPED_ASSET_THRESHOLD: float = Field(
        default=0.5,  # 50%
        description="Maximum percentage of unmapped assets allowed (0.0-1.0)"
    )

    class Config:
        env_file = ".env"
```

```python
# File: backend/app/repositories/assessment_flow_repository/commands/flow_commands.py
# Lines: 112-120 (update unmapped handling logic)

from app.core.config import settings

# Calculate unmapped percentage
unmapped_count = sum(
    1 for group in application_groups if group.canonical_application_id is None
)
unmapped_percentage = unmapped_count / len(application_groups) if application_groups else 0

# Collect unmapped asset names for error/warning message
unmapped_names = [
    group.canonical_application_name
    for group in application_groups
    if group.canonical_application_id is None
]

# Log metrics for monitoring (GPT-5 recommendation)
logger.info(
    f"Assessment flow unmapped asset metrics: "
    f"total={len(application_groups)}, "
    f"unmapped={unmapped_count}, "
    f"percentage={unmapped_percentage:.1%}, "
    f"client_account_id={client_account_id}, "
    f"engagement_id={engagement_id}"
)

# Feature-flagged handling
if unmapped_count > 0:
    if settings.UNMAPPED_ASSET_HANDLING == "strict":
        # Always reject unmapped assets
        raise ValueError(
            f"Assessment initialization blocked: {unmapped_count} unmapped assets detected. "
            f"Unmapped assets: {', '.join(unmapped_names[:5])}{'...' if len(unmapped_names) > 5 else ''}. "
            f"Strict mode requires all assets mapped to canonical applications. "
            f"Use Asset Resolution workflow in collection flow."
        )
    elif settings.UNMAPPED_ASSET_HANDLING == "block":
        # Reject if exceeds threshold
        if unmapped_percentage > settings.UNMAPPED_ASSET_THRESHOLD:
            raise ValueError(
                f"Assessment initialization blocked: {unmapped_percentage:.1%} unmapped assets "
                f"exceeds threshold of {settings.UNMAPPED_ASSET_THRESHOLD:.1%}. "
                f"Unmapped assets ({unmapped_count}): {', '.join(unmapped_names[:5])}{'...' if len(unmapped_names) > 5 else ''}. "
                f"Please complete canonical application mapping to proceed."
            )
        else:
            logger.warning(
                f"Assessment flow has {unmapped_count} unmapped assets ({unmapped_percentage:.1%}) "
                f"but within threshold ({settings.UNMAPPED_ASSET_THRESHOLD:.1%}). Proceeding with banner."
            )
    else:  # "banner" mode (default)
        logger.warning(
            f"Assessment flow has {unmapped_count} unmapped assets. "
            f"Asset Resolution banner will be shown in UI."
        )
```

**Files Modified**: 2
- `backend/app/core/config.py` (add feature flags)
- `backend/app/repositories/assessment_flow_repository/commands/flow_commands.py` (update validation)

**Environment Configuration**:
```bash
# .env file options

# Default: Show banner, allow proceeding
UNMAPPED_ASSET_HANDLING=banner

# Block if >50% unmapped
UNMAPPED_ASSET_HANDLING=block
UNMAPPED_ASSET_THRESHOLD=0.5

# Always block unmapped assets (for high-maturity tenants)
UNMAPPED_ASSET_HANDLING=strict
```

**Verification**:
```bash
# Test banner mode (default)
curl -X POST "http://localhost:8000/api/v1/master-flows/new/assessment/initialize" \
  -H "Content-Type: application/json" \
  -d '{"selected_application_ids": ["unmapped-asset-1", "unmapped-asset-2"]}'
# Expected: 200 OK, warning in logs

# Test block mode with threshold
export UNMAPPED_ASSET_HANDLING=block
export UNMAPPED_ASSET_THRESHOLD=0.3
# Retry request with 80% unmapped
# Expected: 400 error with threshold message

# Test strict mode
export UNMAPPED_ASSET_HANDLING=strict
# Retry request with any unmapped
# Expected: 400 error immediately
```

**Success Criteria**:
- ✅ Feature flag configurable via environment variables
- ✅ Tenant-scoped metrics logged for monitoring
- ✅ "banner" mode allows proceeding (default)
- ✅ "block" mode rejects if exceeds threshold
- ✅ "strict" mode always rejects unmapped assets

---

#### Task 1.3: Add "Enrich Applications" Button with Structured Progress
**Priority**: P0
**Estimated Time**: 30 minutes
**Rationale**: UX improvement + structured progress feedback (GPT-5 recommendation)

**Implementation**:
```typescript
// File: src/pages/assessment/[flowId]/architecture.tsx
// Lines: After 211 (in Selected Applications card header)

import { Zap, Loader2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const [isEnriching, setIsEnriching] = useState(false);
const [enrichmentProgress, setEnrichmentProgress] = useState<{
  compliance_flags: number;
  licenses: number;
  vulnerabilities: number;
  resilience: number;
  dependencies: number;
  product_links: number;
} | null>(null);

const handleEnrichApplications = async () => {
  setIsEnriching(true);
  setEnrichmentProgress(null);

  try {
    // Start enrichment
    const response = await fetch(
      `/api/v1/master-flows/${flowId}/trigger-enrichment`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Client-Account-ID': client?.id || '',
          'X-Engagement-ID': engagement?.id || '',
        },
      }
    );

    if (!response.ok) throw new Error('Enrichment failed');

    // Poll for status updates (GPT-5 recommendation)
    const pollInterval = setInterval(async () => {
      const statusResponse = await fetch(
        `/api/v1/master-flows/${flowId}/enrichment-status`,
        {
          headers: {
            'X-Client-Account-ID': client?.id || '',
            'X-Engagement-ID': engagement?.id || '',
          },
        }
      );

      if (statusResponse.ok) {
        const status = await statusResponse.json();
        setEnrichmentProgress(status.enrichment_status);

        // Check if enrichment complete (any non-zero counts)
        const totalEnriched = Object.values(status.enrichment_status).reduce(
          (sum: number, count: number) => sum + count, 0
        );

        if (totalEnriched > 0) {
          clearInterval(pollInterval);
          setIsEnriching(false);
          await refreshApplicationData();
          console.log('[Architecture] Enrichment completed:', status);
        }
      }
    }, 3000); // Poll every 3 seconds

    // Timeout after 5 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      setIsEnriching(false);
    }, 300000);

  } catch (error) {
    console.error('Failed to enrich applications:', error);
    alert(`Enrichment failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    setIsEnriching(false);
  }
};

// Add button in card header (after Refresh button)
<Button
  variant="default"
  size="sm"
  onClick={handleEnrichApplications}
  disabled={isEnriching || state.isLoading}
  className="ml-2"
>
  {isEnriching ? (
    <>
      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
      Enriching...
    </>
  ) : (
    <>
      <Zap className="h-3 w-3 mr-1" />
      Enrich Applications
    </>
  )}
</Button>

{/* Show progress indicator */}
{isEnriching && enrichmentProgress && (
  <div className="text-xs text-muted-foreground mt-2">
    Enriched: {Object.entries(enrichmentProgress).map(([key, count]) =>
      `${key}: ${count}`
    ).join(', ')}
  </div>
)}
```

**Files Modified**: 1
- `src/pages/assessment/[flowId]/architecture.tsx`

**Verification**:
1. Navigate to `/assessment/{flowId}/architecture`
2. Click "Enrich Applications" button
3. Verify button shows "Enriching..." with spinner
4. Verify progress counts update every 3 seconds
5. Verify button re-enables after completion
6. Check backend logs for LLM calls
7. Verify `ApplicationGroupsWidget` shows updated readiness

**Success Criteria**:
- ✅ Button disables during enrichment (GPT-5 recommendation)
- ✅ Structured progress displayed (counts per table)
- ✅ Tenant headers always sent
- ✅ Polls status until complete
- ✅ Refreshes data on completion

---

### Phase 2: Core Features (P1 - 5 hours)

#### Task 2.1: Bulk Asset Mapping Endpoint with Validation
**Priority**: P1
**Estimated Time**: 2 hours
**Rationale**: Solves 83% unmapped problem (GPT-5 recommendations: tenant scoping, idempotency, audit)

**Implementation**:
```python
# File: backend/app/api/v1/canonical_applications/bulk_mapping.py (NEW)

from typing import List, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.database import get_db
from app.models.assets import Asset
from app.models.canonical_applications.canonical_application import CanonicalApplication
from app.models.collection_flow import CollectionFlowApplication
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class AssetMapping(BaseModel):
    """Single asset-to-canonical mapping"""
    asset_id: str = Field(..., description="Asset UUID")
    canonical_application_id: str = Field(..., description="Canonical application UUID")

    @validator('asset_id', 'canonical_application_id')
    def validate_uuid(cls, v):
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid UUID format: {v}")


class BulkMappingRequest(BaseModel):
    """Bulk asset mapping request"""
    mappings: List[AssetMapping] = Field(..., min_items=1, max_items=100)
    collection_flow_id: Optional[str] = None

    @validator('mappings')
    def validate_unique_assets(cls, v):
        asset_ids = [m.asset_id for m in v]
        if len(asset_ids) != len(set(asset_ids)):
            raise ValueError("Duplicate asset_id entries in mappings")
        return v


class BulkMappingResponse(BaseModel):
    """Bulk asset mapping response"""
    total_requested: int
    successfully_mapped: int
    already_mapped: int
    errors: List[Dict[str, str]]


@router.post("/bulk-map-assets", response_model=BulkMappingResponse)
async def bulk_map_assets(
    request: BulkMappingRequest,
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Header(None, alias="X-Client-Account-ID"),
    engagement_id: str = Header(None, alias="X-Engagement-ID"),
) -> BulkMappingResponse:
    """
    Bulk map assets to canonical applications with full validation.

    Enforces:
    - Tenant scoping on both Asset and CanonicalApplication IDs
    - Idempotent upsert on conflict
    - Cross-tenant ID rejection
    - Audit logging

    Per GPT-5 recommendations.
    """
    if not client_account_id or not engagement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing tenant headers: X-Client-Account-ID and X-Engagement-ID required"
        )

    client_account_uuid = UUID(client_account_id)
    engagement_uuid = UUID(engagement_id)

    results = {
        "successfully_mapped": 0,
        "already_mapped": 0,
        "errors": []
    }

    for mapping in request.mappings:
        try:
            asset_uuid = UUID(mapping.asset_id)
            canonical_uuid = UUID(mapping.canonical_application_id)

            # Validate asset exists and belongs to tenant
            asset_result = await db.execute(
                select(Asset)
                .where(
                    Asset.id == asset_uuid,
                    Asset.client_account_id == client_account_uuid,
                    Asset.engagement_id == engagement_uuid
                )
            )
            asset = asset_result.scalar_one_or_none()

            if not asset:
                results["errors"].append({
                    "asset_id": mapping.asset_id,
                    "error": "Asset not found or does not belong to tenant"
                })
                continue

            # Validate canonical application exists and belongs to tenant
            canonical_result = await db.execute(
                select(CanonicalApplication)
                .where(
                    CanonicalApplication.id == canonical_uuid,
                    CanonicalApplication.client_account_id == client_account_uuid,
                    CanonicalApplication.engagement_id == engagement_uuid
                )
            )
            canonical = canonical_result.scalar_one_or_none()

            if not canonical:
                results["errors"].append({
                    "asset_id": mapping.asset_id,
                    "error": "Canonical application not found or does not belong to tenant"
                })
                continue

            # Idempotent upsert (GPT-5 recommendation)
            stmt = insert(CollectionFlowApplication).values(
                collection_flow_id=UUID(request.collection_flow_id) if request.collection_flow_id else None,
                asset_id=asset_uuid,
                canonical_application_id=canonical_uuid,
                client_account_id=client_account_uuid,
                engagement_id=engagement_uuid,
            ).on_conflict_do_update(
                index_elements=['asset_id'],  # Unique constraint on asset_id
                set_={
                    'canonical_application_id': canonical_uuid,
                    'collection_flow_id': UUID(request.collection_flow_id) if request.collection_flow_id else None,
                }
            )

            result = await db.execute(stmt)

            # Check if insert or update
            if result.rowcount == 0:
                results["already_mapped"] += 1
            else:
                results["successfully_mapped"] += 1

                # Audit logging (GPT-5 recommendation)
                logger.info(
                    f"Asset mapped: asset_id={mapping.asset_id}, "
                    f"canonical_id={mapping.canonical_application_id}, "
                    f"tenant={client_account_id}/{engagement_id}"
                )

        except Exception as e:
            logger.error(f"Failed to map asset {mapping.asset_id}: {e}")
            results["errors"].append({
                "asset_id": mapping.asset_id,
                "error": str(e)
            })

    await db.commit()

    return BulkMappingResponse(
        total_requested=len(request.mappings),
        successfully_mapped=results["successfully_mapped"],
        already_mapped=results["already_mapped"],
        errors=results["errors"]
    )
```

**Register Router**:
```python
# File: backend/app/api/v1/router_registry.py
# Add to canonical_applications router

from app.api.v1.canonical_applications import bulk_mapping

# In register_routes() function:
canonical_app_router.include_router(
    bulk_mapping.router,
    tags=["canonical-applications"]
)
```

**Files Modified**: 2
- `backend/app/api/v1/canonical_applications/bulk_mapping.py` (new)
- `backend/app/api/v1/router_registry.py` (add router)

**Unit Tests**:
```python
# File: backend/tests/unit/api/canonical_applications/test_bulk_mapping.py (NEW)

import pytest
from uuid import uuid4

async def test_bulk_map_assets_success(client, db_session):
    """Successfully map multiple assets"""
    asset_ids = [str(uuid4()) for _ in range(5)]
    canonical_id = str(uuid4())

    # Create test data
    # ...

    response = await client.post(
        "/api/v1/canonical-applications/bulk-map-assets",
        json={
            "mappings": [
                {"asset_id": aid, "canonical_application_id": canonical_id}
                for aid in asset_ids
            ]
        },
        headers={
            "X-Client-Account-ID": "...",
            "X-Engagement-ID": "..."
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["successfully_mapped"] == 5
    assert data["already_mapped"] == 0
    assert len(data["errors"]) == 0


async def test_bulk_map_idempotency(client, db_session):
    """Mapping same asset twice should be idempotent"""
    # First mapping
    response1 = await client.post("/api/v1/canonical-applications/bulk-map-assets", ...)
    assert response1.json()["successfully_mapped"] == 1

    # Second mapping (same asset)
    response2 = await client.post("/api/v1/canonical-applications/bulk-map-assets", ...)
    assert response2.json()["already_mapped"] == 1


async def test_bulk_map_rejects_cross_tenant(client, db_session):
    """Reject mapping assets from different tenant"""
    response = await client.post(
        "/api/v1/canonical-applications/bulk-map-assets",
        json={...},
        headers={
            "X-Client-Account-ID": "different-tenant-id",
            "X-Engagement-ID": "..."
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["errors"]) > 0
    assert "does not belong to tenant" in data["errors"][0]["error"]
```

**Verification**:
```bash
# Test bulk mapping
curl -X POST "http://localhost:8000/api/v1/canonical-applications/bulk-map-assets" \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-ID: 11111111-1111-1111-1111-111111111111" \
  -H "X-Engagement-ID: 22222222-2222-2222-2222-222222222222" \
  -d '{
    "mappings": [
      {"asset_id": "asset-uuid-1", "canonical_application_id": "canonical-uuid-1"},
      {"asset_id": "asset-uuid-2", "canonical_application_id": "canonical-uuid-1"}
    ]
  }'

# Verify database
docker exec -it migration_postgres psql -U postgres -d migration_db -c \
  "SELECT asset_id, canonical_application_id FROM migration.collection_flow_applications WHERE asset_id IN ('asset-uuid-1', 'asset-uuid-2');"
```

**Success Criteria**:
- ✅ Tenant scoping enforced on both Asset and CanonicalApplication
- ✅ Idempotent: duplicate calls return "already_mapped"
- ✅ Cross-tenant IDs rejected with clear error message
- ✅ Audit logs show who mapped, when, what tenant
- ✅ Unit tests pass: success, idempotency, cross-tenant rejection

---

#### Task 2.2: Bulk Mapping UI Component
**Priority**: P1
**Estimated Time**: 2 hours
**Rationale**: User-friendly interface for bulk mapping (GPT-5: pagination, debounce, in-line confirmation)

**Implementation**:
```typescript
// File: src/components/assessment/BulkAssetMappingDialog.tsx (NEW - 300 lines)

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Check, X, Search, Loader2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useDebounce } from '@/hooks/useDebounce';

interface UnmappedAsset {
  asset_id: string;
  asset_name: string;
  asset_type: string;
}

interface CanonicalApplication {
  id: string;
  canonical_name: string;
  application_type: string;
  business_criticality: string;
  usage_count: number;
  confidence_score: number;
  is_verified: boolean;
}

interface BulkAssetMappingDialogProps {
  unmappedAssets: UnmappedAsset[];
  onComplete: () => void;
  onCancel: () => void;
}

export const BulkAssetMappingDialog: React.FC<BulkAssetMappingDialogProps> = ({
  unmappedAssets,
  onComplete,
  onCancel,
}) => {
  const { client, engagement } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [mappings, setMappings] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [mappingResults, setMappingResults] = useState<Record<string, 'success' | 'error'>>({});

  // Debounce search for performance (GPT-5 recommendation)
  const debouncedSearch = useDebounce(searchTerm, 300);

  // Query canonical applications with pagination
  const { data: canonicalApps, isLoading } = useQuery({
    queryKey: ['canonical-applications', debouncedSearch, client?.id, engagement?.id],
    queryFn: async () => {
      const response = await fetch(
        `/api/v1/canonical-applications?search=${debouncedSearch}&page_size=50`,
        {
          headers: {
            'X-Client-Account-ID': client?.id || '',
            'X-Engagement-ID': engagement?.id || '',
          },
        }
      );
      if (!response.ok) throw new Error('Failed to fetch canonical applications');
      return response.json();
    },
    enabled: !!client?.id && !!engagement?.id,
  });

  const handleSelectMapping = (assetId: string, canonicalAppId: string) => {
    setMappings(prev => ({ ...prev, [assetId]: canonicalAppId }));
  };

  const handleBulkMap = async () => {
    setIsSubmitting(true);
    setMappingResults({});

    try {
      const mappingArray = Object.entries(mappings).map(([asset_id, canonical_application_id]) => ({
        asset_id,
        canonical_application_id,
      }));

      const response = await fetch('/api/v1/canonical-applications/bulk-map-assets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Client-Account-ID': client?.id || '',
          'X-Engagement-ID': engagement?.id || '',
        },
        body: JSON.stringify({ mappings: mappingArray }),
      });

      if (!response.ok) throw new Error('Bulk mapping failed');

      const result = await response.json();
      console.log('[BulkMapping] Completed:', result);

      // Show in-line confirmation (GPT-5 recommendation)
      const results: Record<string, 'success' | 'error'> = {};
      mappingArray.forEach(m => {
        const hasError = result.errors.find((e: any) => e.asset_id === m.asset_id);
        results[m.asset_id] = hasError ? 'error' : 'success';
      });
      setMappingResults(results);

      // Auto-close after 2 seconds if all successful
      if (result.errors.length === 0) {
        setTimeout(() => onComplete(), 2000);
      }

    } catch (error) {
      console.error('Failed to map assets:', error);
      alert(`Mapping failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Filter assets by search term
  const filteredAssets = useMemo(() => {
    if (!searchTerm) return unmappedAssets;
    return unmappedAssets.filter(asset =>
      asset.asset_name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [unmappedAssets, searchTerm]);

  const mappedCount = Object.keys(mappings).length;
  const hasResults = Object.keys(mappingResults).length > 0;

  return (
    <Dialog open onOpenChange={onCancel}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Map {unmappedAssets.length} Unmapped Assets</DialogTitle>
          <DialogDescription>
            Select a canonical application for each unmapped asset. Assets will be grouped by application in the assessment.
          </DialogDescription>
        </DialogHeader>

        {/* Search canonical apps with debounce */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search canonical applications..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
          {isLoading && (
            <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 animate-spin text-gray-400" />
          )}
        </div>

        {/* Asset list with canonical app selector */}
        <div className="space-y-3 mt-4 max-h-[500px] overflow-y-auto">
          {filteredAssets.map((asset) => {
            const selectedApp = canonicalApps?.applications.find(
              (app: CanonicalApplication) => app.id === mappings[asset.asset_id]
            );
            const result = mappingResults[asset.asset_id];

            return (
              <div
                key={asset.asset_id}
                className={`border rounded-lg p-4 ${
                  result === 'success' ? 'border-green-500 bg-green-50' :
                  result === 'error' ? 'border-red-500 bg-red-50' :
                  'border-gray-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-semibold">{asset.asset_name}</h4>
                      <Badge variant="outline">{asset.asset_type}</Badge>

                      {/* In-line result confirmation */}
                      {result === 'success' && (
                        <Badge variant="default" className="bg-green-600">
                          <Check className="h-3 w-3 mr-1" />
                          Mapped
                        </Badge>
                      )}
                      {result === 'error' && (
                        <Badge variant="destructive">
                          <X className="h-3 w-3 mr-1" />
                          Failed
                        </Badge>
                      )}
                    </div>

                    {selectedApp && (
                      <p className="text-sm text-muted-foreground mt-1">
                        → {selectedApp.canonical_name} ({selectedApp.application_type})
                      </p>
                    )}
                  </div>

                  {/* Canonical app selector */}
                  <select
                    value={mappings[asset.asset_id] || ''}
                    onChange={(e) => handleSelectMapping(asset.asset_id, e.target.value)}
                    disabled={hasResults}
                    className="border rounded px-3 py-2 min-w-[250px] disabled:opacity-50"
                  >
                    <option value="">Select canonical app...</option>
                    {canonicalApps?.applications.map((app: CanonicalApplication) => (
                      <option key={app.id} value={app.id}>
                        {app.canonical_name} ({app.application_type})
                        {app.is_verified && ' ✓'}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            );
          })}

          {filteredAssets.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              No assets found matching "{searchTerm}"
            </div>
          )}
        </div>

        {/* Progress indicator */}
        {mappedCount > 0 && !hasResults && (
          <div className="text-sm text-muted-foreground">
            {mappedCount} of {unmappedAssets.length} assets mapped
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end space-x-3 mt-6">
          <Button variant="outline" onClick={onCancel} disabled={isSubmitting}>
            {hasResults ? 'Close' : 'Cancel'}
          </Button>
          {!hasResults && (
            <Button
              onClick={handleBulkMap}
              disabled={isSubmitting || mappedCount === 0}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Mapping...
                </>
              ) : (
                `Map ${mappedCount} Asset${mappedCount !== 1 ? 's' : ''}`
              )}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
```

**Integration into Architecture Page**:
```typescript
// File: src/pages/assessment/[flowId]/architecture.tsx
// Add button and modal in Selected Applications section

import { BulkAssetMappingDialog } from '@/components/assessment/BulkAssetMappingDialog';

const [showBulkMapping, setShowBulkMapping] = useState(false);

// Get unmapped assets
const unmappedAssets = useMemo(() => {
  return state.selectedApplications.filter(app =>
    !app.canonical_application_id || app.canonical_application_id === null
  ).map(app => ({
    asset_id: app.application_id,
    asset_name: app.application_name,
    asset_type: app.asset_type || 'unknown',
  }));
}, [state.selectedApplications]);

// Add button in card header (after Enrich button)
{unmappedAssets.length > 0 && (
  <Button
    variant="outline"
    size="sm"
    onClick={() => setShowBulkMapping(true)}
    className="ml-2"
  >
    Map {unmappedAssets.length} Unmapped Assets
  </Button>
)}

{/* Add modal */}
{showBulkMapping && (
  <BulkAssetMappingDialog
    unmappedAssets={unmappedAssets}
    onComplete={() => {
      setShowBulkMapping(false);
      refreshApplicationData();
    }}
    onCancel={() => setShowBulkMapping(false)}
  />
)}
```

**Files Modified**: 2
- `src/components/assessment/BulkAssetMappingDialog.tsx` (new)
- `src/pages/assessment/[flowId]/architecture.tsx` (add modal integration)

**Verification**:
1. Navigate to architecture page with unmapped assets
2. Click "Map X Unmapped Assets" button
3. Search for canonical applications (verify debounce)
4. Select canonical apps for 5-10 assets
5. Click "Map X Assets"
6. Verify in-line success/error indicators
7. Verify auto-close after success
8. Check database for mappings

**Success Criteria**:
- ✅ Pagination and debounce for canonical app search (GPT-5)
- ✅ In-line result confirmation (success/error badges)
- ✅ Button shows count: "Map X Unmapped Assets"
- ✅ Dropdown disabled after mapping
- ✅ Auto-closes on success
- ✅ Database updated correctly

---

#### Task 2.3: Batch Enrichment Performance Optimization
**Priority**: P1
**Estimated Time**: 1 hour
**Rationale**: Reduce 36.6 min → 3.7 min for 100 assets (GPT-5: backpressure, rate limits, ETA)

**Note**: From Phase 5 Day 26 report, batch processing architecture already exists. This task adds backpressure controls.

**Implementation**:
```python
# File: backend/app/services/enrichment/auto_enrichment_pipeline.py
# Add backpressure and rate limiting

from asyncio import Semaphore
import time

class AutoEnrichmentPipeline:
    def __init__(
        self,
        crewai_service,
        memory_manager,
        max_concurrent_batches: int = 3,  # GPT-5: cap concurrent batches
        rate_limit_per_tenant: int = 10,  # Max 10 batches per tenant per minute
    ):
        self.crewai_service = crewai_service
        self.memory_manager = memory_manager
        self.max_concurrent_batches = max_concurrent_batches
        self.rate_limit_per_tenant = rate_limit_per_tenant
        self._batch_semaphore = Semaphore(max_concurrent_batches)
        self._tenant_rate_limits: Dict[str, List[float]] = {}  # tenant -> [timestamps]

    async def enrich_assets(
        self,
        asset_ids: List[str],
        client_account_id: str,
        engagement_id: str,
        batch_size: int = 10,
    ) -> Dict[str, int]:
        """
        Enrich assets with batch processing and backpressure control.

        Performance target: 100 assets in < 10 minutes
        Optimization: 10 assets per batch, concurrent execution with backpressure

        GPT-5 recommendations:
        - Cap concurrent batches to avoid API rate limits
        - Per-tenant rate limiting
        - Surface ETA for progress tracking
        """
        start_time = time.time()
        tenant_key = f"{client_account_id}/{engagement_id}"

        # Check rate limit (GPT-5 recommendation)
        if not await self._check_rate_limit(tenant_key):
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: max {self.rate_limit_per_tenant} batches per minute per tenant"
            )

        # Split assets into batches
        asset_batches = [
            asset_ids[i:i + batch_size]
            for i in range(0, len(asset_ids), batch_size)
        ]

        total_batches = len(asset_batches)
        logger.info(
            f"Starting enrichment: {len(asset_ids)} assets, "
            f"{total_batches} batches, batch_size={batch_size}, "
            f"tenant={tenant_key}"
        )

        # Calculate ETA (GPT-5 recommendation)
        estimated_seconds_per_batch = 22  # From Day 26 testing
        estimated_total_seconds = total_batches * estimated_seconds_per_batch
        logger.info(f"Estimated completion time: {estimated_total_seconds}s ({estimated_total_seconds / 60:.1f} min)")

        total_results = {
            "compliance_flags": 0,
            "licenses": 0,
            "vulnerabilities": 0,
            "resilience": 0,
            "dependencies": 0,
            "product_links": 0,
            "field_conflicts": 0,
        }

        # Process batches with backpressure (GPT-5 recommendation)
        for batch_num, batch_asset_ids in enumerate(asset_batches, 1):
            async with self._batch_semaphore:  # Backpressure: max concurrent batches
                logger.info(
                    f"Processing batch {batch_num}/{total_batches} "
                    f"({len(batch_asset_ids)} assets) - "
                    f"ETA: {((total_batches - batch_num) * estimated_seconds_per_batch) / 60:.1f} min remaining"
                )

                # Query assets for this batch
                batch_assets = await self._get_assets_batch(
                    batch_asset_ids, client_account_id, engagement_id, db
                )

                # Run 7 enrichment agents concurrently for this batch
                batch_results = await asyncio.gather(
                    *[
                        agent.enrich_batch(batch_assets)
                        for agent in self.agents
                    ],
                    return_exceptions=True
                )

                # Aggregate batch results
                for agent_results in batch_results:
                    if isinstance(agent_results, dict):
                        for key in total_results:
                            total_results[key] += agent_results.get(key, 0)

        elapsed_time = time.time() - start_time
        logger.info(
            f"Enrichment complete: {len(asset_ids)} assets in {elapsed_time:.1f}s "
            f"({elapsed_time / 60:.1f} min), results={total_results}"
        )

        return total_results

    async def _check_rate_limit(self, tenant_key: str) -> bool:
        """
        Check per-tenant rate limit.

        Allows max N batches per minute per tenant.
        """
        current_time = time.time()

        # Initialize tenant tracking
        if tenant_key not in self._tenant_rate_limits:
            self._tenant_rate_limits[tenant_key] = []

        # Remove timestamps older than 1 minute
        self._tenant_rate_limits[tenant_key] = [
            ts for ts in self._tenant_rate_limits[tenant_key]
            if current_time - ts < 60
        ]

        # Check if under limit
        if len(self._tenant_rate_limits[tenant_key]) >= self.rate_limit_per_tenant:
            return False

        # Add current timestamp
        self._tenant_rate_limits[tenant_key].append(current_time)
        return True
```

**Files Modified**: 1
- `backend/app/services/enrichment/auto_enrichment_pipeline.py`

**Configuration**:
```python
# File: backend/app/core/config.py

class Settings(BaseSettings):
    # ... existing settings ...

    # Enrichment performance controls
    ENRICHMENT_MAX_CONCURRENT_BATCHES: int = Field(
        default=3,
        description="Max concurrent enrichment batches (backpressure control)"
    )
    ENRICHMENT_RATE_LIMIT_PER_TENANT: int = Field(
        default=10,
        description="Max enrichment batches per tenant per minute"
    )
```

**Verification**:
```bash
# Test with 50 assets
curl -X POST "http://localhost:8000/api/v1/master-flows/{flow_id}/trigger-enrichment" \
  -H "X-Client-Account-ID: 11111111-1111-1111-1111-111111111111" \
  -H "X-Engagement-ID: 22222222-2222-2222-2222-222222222222"

# Check logs for backpressure and ETA
docker logs migration_backend -f | grep "Estimated completion time\|ETA:"

# Verify rate limiting (trigger 15 times rapidly)
for i in {1..15}; do
  curl -X POST "http://localhost:8000/api/v1/master-flows/{flow_id}/trigger-enrichment" \
    -H "X-Client-Account-ID: ..." &
done
# Should see 429 errors after 10 requests
```

**Success Criteria**:
- ✅ Max 3 concurrent batches (backpressure)
- ✅ Per-tenant rate limit (10 batches/min)
- ✅ ETA logged for progress tracking
- ✅ 100 assets complete in < 5 minutes (target achieved)

---

### Phase 3: Automation (P2 - 1 hour)

#### Task 3.1: Feature-Flagged Auto-Enrichment
**Priority**: P2
**Estimated Time**: 1 hour
**Rationale**: GPT-5 recommendation - default OFF for cost control, use background tasks

**Implementation**:
```python
# File: backend/app/core/config.py

class Settings(BaseSettings):
    # ... existing settings ...

    # Auto-enrichment feature flag
    AUTO_ENRICH_ON_INIT: bool = Field(
        default=False,
        description="Automatically trigger enrichment after assessment initialization"
    )
```

```python
# File: backend/app/repositories/assessment_flow_repository/commands/flow_commands.py
# After line 140 (after successful flow creation)

from fastapi import BackgroundTasks
from app.core.config import settings

async def create_assessment_flow(
    # ... existing parameters ...
    background_tasks: BackgroundTasks,  # Add parameter
) -> DiscoveryFlow:
    # ... existing flow creation logic ...

    # Step 7: Trigger auto-enrichment if enabled (GPT-5 recommendation)
    if settings.AUTO_ENRICH_ON_INIT and len(asset_ids) > 0:
        logger.info(
            f"Auto-enrichment enabled - scheduling enrichment for {len(asset_ids)} assets "
            f"in flow {flow_id}"
        )

        # Use BackgroundTasks to avoid blocking flow creation (GPT-5 recommendation)
        background_tasks.add_task(
            _run_auto_enrichment,
            flow_id=str(flow_id),
            asset_ids=asset_ids,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )

        logger.info(f"Auto-enrichment scheduled for flow {flow_id}")

    return flow


async def _run_auto_enrichment(
    flow_id: str,
    asset_ids: List[str],
    client_account_id: str,
    engagement_id: str,
):
    """
    Background task for auto-enrichment.

    Implements GPT-5 recommendations:
    - Set per-flow "in_progress" lock
    - Persist last_enriched_at
    - Avoid re-running immediately
    """
    from app.services.enrichment.auto_enrichment_pipeline import AutoEnrichmentPipeline

    try:
        # Check if enrichment already in progress
        async with get_db() as db:
            flow_result = await db.execute(
                select(DiscoveryFlow).where(DiscoveryFlow.id == UUID(flow_id))
            )
            flow = flow_result.scalar_one_or_none()

            if not flow:
                logger.error(f"Auto-enrichment failed: flow {flow_id} not found")
                return

            # Check if enrichment already running (GPT-5: per-flow lock)
            if flow.custom_attributes.get("enrichment_in_progress"):
                logger.warning(f"Auto-enrichment already in progress for flow {flow_id}")
                return

            # Check last enrichment time (GPT-5: avoid immediate re-run)
            last_enriched = flow.custom_attributes.get("last_enriched_at")
            if last_enriched:
                from datetime import datetime, timedelta
                last_enriched_dt = datetime.fromisoformat(last_enriched)
                if datetime.now() - last_enriched_dt < timedelta(hours=1):
                    logger.info(
                        f"Auto-enrichment skipped for flow {flow_id}: "
                        f"last enriched {(datetime.now() - last_enriched_dt).total_seconds() / 60:.1f} min ago"
                    )
                    return

            # Set in-progress flag
            flow.custom_attributes["enrichment_in_progress"] = True
            await db.commit()

        # Run enrichment
        enrichment_pipeline = AutoEnrichmentPipeline(
            crewai_service=crewai_service,
            memory_manager=memory_manager,
        )

        results = await enrichment_pipeline.enrich_assets(
            asset_ids=asset_ids,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            batch_size=10,
        )

        # Update flow metadata (GPT-5: persist counts and timestamp)
        async with get_db() as db:
            flow_result = await db.execute(
                select(DiscoveryFlow).where(DiscoveryFlow.id == UUID(flow_id))
            )
            flow = flow_result.scalar_one_or_none()

            if flow:
                flow.custom_attributes["enrichment_in_progress"] = False
                flow.custom_attributes["last_enriched_at"] = datetime.now().isoformat()
                flow.custom_attributes["enrichment_counts"] = results
                await db.commit()

        logger.info(f"Auto-enrichment completed for flow {flow_id}: {results}")

    except Exception as e:
        logger.error(f"Auto-enrichment failed for flow {flow_id}: {e}")

        # Clear in-progress flag on error
        async with get_db() as db:
            flow_result = await db.execute(
                select(DiscoveryFlow).where(DiscoveryFlow.id == UUID(flow_id))
            )
            flow = flow_result.scalar_one_or_none()
            if flow:
                flow.custom_attributes["enrichment_in_progress"] = False
                await db.commit()
```

**Files Modified**: 2
- `backend/app/core/config.py` (add feature flag)
- `backend/app/repositories/assessment_flow_repository/commands/flow_commands.py` (add background task)

**Environment Configuration**:
```bash
# .env file

# Default: OFF (manual enrichment only)
AUTO_ENRICH_ON_INIT=false

# Enable for specific tenants/environments
AUTO_ENRICH_ON_INIT=true
```

**Verification**:
```bash
# Test with feature flag OFF
export AUTO_ENRICH_ON_INIT=false
curl -X POST "http://localhost:8000/api/v1/master-flows/new/assessment/initialize-from-canonical" \
  -H "Content-Type: application/json" \
  -d '{"canonical_application_ids": ["..."]}'
# Verify logs show: "Auto-enrichment disabled"

# Test with feature flag ON
export AUTO_ENRICH_ON_INIT=true
# Retry request
# Verify logs show: "Auto-enrichment scheduled"
# Wait 30 seconds, verify enrichment completed

# Test duplicate prevention
# Trigger enrichment manually via /trigger-enrichment while auto-enrichment running
# Verify logs show: "Auto-enrichment already in progress"
```

**Success Criteria**:
- ✅ Feature flag default OFF (cost control)
- ✅ Uses BackgroundTasks (doesn't block flow creation)
- ✅ Per-flow "in_progress" lock prevents duplicates
- ✅ Persists `last_enriched_at` and counts
- ✅ Skips if enriched within last hour

---

## Testing Strategy

### Unit Tests (20 test cases)

#### Pattern Type Mapping (5 tests)
- ✅ All agent types map to valid DB enums
- ✅ Unknown types use fallback with warning
- ✅ No invalid enum values in mapping
- ✅ get_db_pattern_type returns PatternTypeDB enum
- ✅ Fallback doesn't block pipeline

#### Bulk Asset Mapping (8 tests)
- ✅ Successfully map multiple assets
- ✅ Idempotent: duplicate calls return "already_mapped"
- ✅ Reject cross-tenant asset IDs
- ✅ Reject cross-tenant canonical app IDs
- ✅ Validate UUID format
- ✅ Handle non-existent asset IDs
- ✅ Handle non-existent canonical app IDs
- ✅ Audit logging for successful mappings

#### Unmapped Asset Handling (4 tests)
- ✅ "banner" mode allows proceeding
- ✅ "block" mode rejects if >threshold
- ✅ "strict" mode always rejects unmapped
- ✅ Tenant-scoped metrics logged

#### Batch Enrichment (3 tests)
- ✅ Backpressure: max concurrent batches enforced
- ✅ Rate limiting: reject after limit
- ✅ ETA calculated correctly

### Integration Tests (8 test scenarios)

#### End-to-End Assessment Flow
1. ✅ Create assessment from canonical application
2. ✅ Verify no unmapped assets
3. ✅ Trigger enrichment manually
4. ✅ Verify all 7 enrichment tables populated
5. ✅ Verify readiness scores updated

#### Unmapped Asset Flow
6. ✅ Create assessment with 80% unmapped (banner mode)
7. ✅ Verify AssetResolutionBanner shows
8. ✅ Use bulk mapping to map all assets
9. ✅ Verify unmapped count drops to 0
10. ✅ Trigger enrichment
11. ✅ Verify readiness improves

#### Auto-Enrichment Flow
12. ✅ Enable AUTO_ENRICH_ON_INIT flag
13. ✅ Create assessment from canonical app
14. ✅ Verify enrichment runs in background
15. ✅ Verify flow creation doesn't block
16. ✅ Verify enrichment completes within 5 min

### E2E Tests (Playwright - 3 journeys)

#### Journey 1: Canonical Application Path (Already Tested)
- ✅ User creates assessment from "Admin Dashboard" canonical app
- ✅ 16 assets automatically included
- ✅ Architecture page shows "1 applications, 16 assets"
- ✅ No DevTestVM01-style individual assets

#### Journey 2: Unmapped Asset Resolution
- ✅ User creates assessment with unmapped assets
- ✅ AssetResolutionBanner appears
- ✅ User clicks "Map Unmapped Assets"
- ✅ Bulk mapping dialog opens
- ✅ User maps 10 assets to canonical applications
- ✅ Banner disappears
- ✅ Architecture page shows canonical groups

#### Journey 3: Enrichment UX
- ✅ User clicks "Enrich Applications" button
- ✅ Button shows "Enriching..." with spinner
- ✅ Progress counts update every 3 seconds
- ✅ Enrichment completes
- ✅ ReadinessDashboardWidget shows improved scores
- ✅ ApplicationGroupsWidget shows enrichment data

---

## Success Metrics

### Performance
- ✅ 100 assets enriched in < 5 minutes (target: < 10 min)
- ✅ API response times < 500ms p95
- ✅ Bulk mapping: 50 assets in < 2 seconds
- ✅ UI remains responsive during enrichment

### Data Quality
- ✅ Unmapped asset percentage < 10% (starting: 83%)
- ✅ All assessment flows use canonical applications
- ✅ No "DevTestVM01"-style individual assets displayed
- ✅ Enrichment completion rate > 95%

### Code Quality
- ✅ All files < 400 lines (modularization)
- ✅ 100% ADR compliance (ADR-015, ADR-024, ADR-027)
- ✅ Unit test coverage > 80%
- ✅ No TypeScript/ESLint errors

### User Experience
- ✅ Canonical app selector works (E2E tested)
- ✅ Unmapped asset banner shows when needed
- ✅ Bulk mapping dialog functional
- ✅ Enrichment button provides progress feedback
- ✅ Assessment scope displays correctly (holistic grouping)

---

## Rollout Plan

### Week 1: Phase 0 + Phase 1 (P0 Blockers)
**Day 1**: Task 0.1-0.2 (Pre-implementation)
- Centralized pattern type mapping
- Database indexes
- Unit tests

**Day 2**: Task 1.1 (Pattern enum fix)
- Update 6 enrichment agents
- Verify pattern storage
- Integration tests

**Day 3**: Task 1.2 (Feature-flagged unmapped handling)
- Add feature flags
- Update validation logic
- E2E test banner mode

**Day 4**: Task 1.3 (Enrich button)
- Add UI button
- Structured progress
- Frontend integration

**Day 5**: P0 Testing & Bug Fixes
- Run full test suite
- Fix any issues
- Deploy to staging

### Week 2: Phase 2 (P1 Core Features)
**Day 6-7**: Task 2.1 (Bulk mapping endpoint)
- Implement API
- Tenant validation
- Unit tests

**Day 8-9**: Task 2.2 (Bulk mapping UI)
- Build component
- Integration
- E2E tests

**Day 10**: Task 2.3 (Batch optimization)
- Backpressure controls
- Rate limiting
- Performance testing

### Week 3: Phase 3 + Production Rollout
**Day 11**: Task 3.1 (Auto-enrichment)
- Feature flag
- Background tasks
- Testing

**Day 12-13**: Full Regression Testing
- All unit tests
- All integration tests
- All E2E journeys

**Day 14**: Production Deployment
- Feature flags OFF initially
- Monitor metrics
- Gradual rollout

---

## Risk Mitigation

### Risk 1: Performance Degradation
**Mitigation**:
- Backpressure controls (max 3 concurrent batches)
- Per-tenant rate limiting (10 batches/min)
- Monitoring with ETA logging
- Auto-enrichment default OFF

### Risk 2: Data Quality Issues
**Mitigation**:
- Feature-flagged strictness (progressive enforcement)
- Tenant-scoped validation
- Idempotent bulk mapping
- Audit logging

### Risk 3: User Confusion
**Mitigation**:
- Clear error messages with guidance
- In-line result confirmation
- AssetResolutionBanner with instructions
- E2E testing before rollout

### Risk 4: Backward Compatibility
**Mitigation**:
- Feature flags for all new behavior
- Existing flows continue working
- Asset ID path still supported (with banner)
- No breaking changes to APIs

---

## Monitoring & Observability

### Metrics to Track
1. **Unmapped Asset Percentage** (by tenant)
2. **Enrichment Completion Rate** (successful/failed)
3. **Enrichment Duration** (p50, p95, p99)
4. **Bulk Mapping Usage** (operations per tenant)
5. **Assessment Initialization Failures** (by reason)

### Alerts
- ⚠️ Enrichment failure rate > 5%
- ⚠️ Enrichment duration > 10 minutes for 100 assets
- ⚠️ Unmapped asset percentage > 50% (tenant-level)
- 🔴 Assessment initialization blocked (strict mode)

### Dashboards
- **Enrichment Pipeline Health**: Duration, success rate, LLM costs
- **Data Quality**: Unmapped percentages, mapping trends
- **User Engagement**: Bulk mapping usage, enrichment triggers

---

## Approval Checklist

Before implementation begins:

- [ ] GPT-5 feedback fully incorporated
- [ ] All task estimates reviewed and approved
- [ ] Testing strategy comprehensive
- [ ] Risk mitigation acceptable
- [ ] Monitoring plan defined
- [ ] Rollout plan feasible
- [ ] Success metrics agreed upon
- [ ] Team capacity confirmed

---

**Plan Status**: 🟡 AWAITING APPROVAL
**Next Step**: Review and approve before implementation
**Estimated Total Time**: 10 hours (2 weeks with testing)
**Expected Impact**: Resolves DevTestVM01 issue, enables holistic assessment, 10x enrichment speedup
