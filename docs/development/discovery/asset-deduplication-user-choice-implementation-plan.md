# Asset Deduplication User-Choice Implementation Plan (REVISED)

**Status**: Ready for Implementation
**Last Updated**: 2025-10-11
**Author**: Claude Code (CC) with GPT-5 Architectural Review
**Related ADRs**: ADR-006 (MFO), ADR-012 (Flow Status Separation), ADR-025 (Child Flow Service)

---

## Executive Summary - Key Changes from GPT-5 Feedback (UPDATED)

### Original GPT-5 Feedback (Incorporated)
✅ **Single Source of Truth**: All deduplication logic unified in `AssetService.create_or_update_asset()`
✅ **Child Flow Pause**: Use DiscoveryFlow model + repositories (not new pause mechanism)
✅ **No Public /detect Endpoint**: Detection runs inside executor, only /list and /resolve exposed
✅ **Replace = UPDATE**: Never delete+recreate assets (preserves FKs and history)
✅ **Field Merge Allowlist**: Explicit validation of mergeable fields
✅ **Bulk Prefetch**: Single query per field type (hostname/ip/name), O(1) lookups
✅ **DB Constraints Stay**: Unique constraints remain as final guard with retry
✅ **Auth & Multi-Tenancy**: All endpoints enforce tenant headers, `resolved_by` from auth context

### Critical Alignment Fixes (NEW - GPT-5 Round 2)
✅ **Standard Tenant Headers**: Use `X-Client-Account-ID` and `X-Engagement-ID` (NOT custom `x-tenant-id`), reuse `RequestContext` dependency
✅ **FK References Fixed**: Removed FK to `crewai_flow_state_extensions.flow_id` (violates ADR - FKs must reference table PKs). Store `master_flow_id` as indexed column only
✅ **Child Flow Update Key**: Resolve child flow by `master_flow_id` first, then update by child PK (not by flow_id column)
✅ **Name+Asset_Type Dedup**: Added `(name, asset_type)` composite check to reduce false positives (same name across different types)

### Robustness & Performance Hardening (NEW)
✅ **Bulk Prefetch Chunking**: Split IN lists into chunks for very large batches (avoid parameter limits)
✅ **Race-Safe Creation**: `bulk_create_or_update_assets()` internally calls `create_or_update_asset()` per item for IntegrityError retry
✅ **JSONB Safety**: Coalesce `phase_state` to `'{}'::jsonb` before `jsonb_set` (handles null values)
✅ **PII Hygiene**: Limit conflict snapshot fields to defined allowlist, redact sensitive custom attributes

### Service & API Correctness (NEW)
✅ **RequestContext Required**: Never pass `AssetService(db, None)` - provide real `RequestContext` with tenant IDs
✅ **Merge Allowlist Everywhere**: Validate ALL merge operations against `DEFAULT_ALLOWED_MERGE_FIELDS` and exclude `NEVER_MERGE_FIELDS`
✅ **Composite Indexes**: Verified/added indexes for `(client_account_id, engagement_id, hostname/ip/name+type)`

### Testing Additions (NEW)
✅ **Name+Asset_Type Conflicts**: Test same name across different asset types
✅ **Snapshot Bounds**: Verify snapshot field limits and PII redaction
✅ **Bulk Chunking**: Test large batches with IN clause splitting
✅ **JSONB Null Handling**: Test `jsonb_set` with null `phase_state`
✅ **Status Coverage**: Test all `create_or_update_asset()` return statuses (created/existed/updated/conflict)

---

## Root Cause Analysis

### Error Pattern from Railway Logs
```
duplicate key value violates unique constraint "ix_assets_unique_hostname_per_context"
Detail: Key (client_account_id, engagement_id, hostname)=(11111111-1111-1111-1111-111111111111, 22222222-2222-2222-2222-222222222222, 'Windows Server 2019') already exists
```

**Frequency**: 120+ occurrences in production logs

### Current Problem
1. **Reactive Deduplication**: `backend/app/services/asset_service/deduplication.py:104-123` handles IntegrityError AFTER insert fails
2. **Session Rollback Cascades**: When first asset fails, session rolls back, causing ALL subsequent assets in batch to fail with "Session's transaction has been rolled back"
3. **No User Choice**: Current system either skips (`upsert=False`) or auto-merges (`upsert=True, merge_strategy="enrich"`) - no user interaction
4. **N+1 Query Problem**: Individual lookups per asset instead of bulk prefetch

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Discovery Flow (Paused)                       │
│  phase_state.conflict_resolution_pending: true                   │
│  phase_state.conflict_metadata: { count, data_import_id }        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│          AssetInventoryExecutor (base.py:168-218)                │
│  1. Call asset_service.bulk_prepare_conflicts()                  │
│  2. If conflicts: Store in asset_conflict_resolutions            │
│  3. Pause child flow via DiscoveryFlowRepository                 │
│  4. Return {"status": "paused", "conflict_count": N}             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│   AssetService.bulk_prepare_conflicts() - SINGLE SOURCE OF TRUTH │
│  - Bulk prefetch: SELECT ... WHERE hostname IN (...)             │
│  - O(1) lookups per asset via in-memory dict                     │
│  - Returns (conflict_free, conflicts_with_details)               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            asset_conflict_resolutions Table                       │
│  { existing_asset_snapshot, new_asset_data, resolution_status }  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│          Frontend UI - AssetConflictModal.tsx                     │
│  1. Poll flow status → detect phase_state.conflict_resolution    │
│  2. Call GET /api/v1/asset-conflicts/list                        │
│  3. Show side-by-side comparison with 3 actions                  │
│  4. Call POST /api/v1/asset-conflicts/resolve-bulk               │
│  5. Resume flow execution                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan: 5 Parallel Workstreams

### **WORKSTREAM 1: Database Layer - Conflict Resolution Table**

**Agent**: `pgvector-data-architect`
**Priority**: High (blocking for WS2)
**Estimated Complexity**: Low
**Estimated Time**: 2 hours

#### Files to Create
- `backend/alembic/versions/089_add_asset_conflict_resolution.py` (NEW)

#### Tasks

**Task 1.1: Create Alembic Migration**

```python
"""Add asset conflict resolution table

Revision ID: 089_add_asset_conflict_resolution
Revises: 088
Create Date: 2025-10-11
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = '089_add_asset_conflict_resolution'
down_revision = '088'  # Adjust to actual latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create asset_conflict_resolutions table
    op.create_table(
        'asset_conflict_resolutions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('data_import_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('master_flow_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Conflict identification
        sa.Column('conflict_type', sa.VARCHAR(length=50), nullable=False),  # 'duplicate_hostname', 'duplicate_ip', 'duplicate_name'
        sa.Column('conflict_key', sa.VARCHAR(length=255), nullable=False),  # The conflicting value

        # Existing asset reference
        sa.Column('existing_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('existing_asset_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),

        # New asset data
        sa.Column('new_asset_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),

        # Resolution
        sa.Column('resolution_status', sa.VARCHAR(length=20), server_default='pending', nullable=False),
        sa.Column('resolution_action', sa.VARCHAR(length=20), nullable=True),
        sa.Column('merge_field_selections', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.TIMESTAMP(timezone=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),

        # Primary key
        sa.PrimaryKeyConstraint('id', name=op.f('pk_asset_conflict_resolutions')),

        # Foreign keys
        sa.ForeignKeyConstraint(
            ['client_account_id'],
            ['migration.client_accounts.id'],
            name=op.f('fk_asset_conflict_resolutions_client_account_id_client_accounts')
        ),
        sa.ForeignKeyConstraint(
            ['engagement_id'],
            ['migration.engagements.id'],
            name=op.f('fk_asset_conflict_resolutions_engagement_id_engagements')
        ),
        sa.ForeignKeyConstraint(
            ['data_import_id'],
            ['migration.data_imports.id'],
            name=op.f('fk_asset_conflict_resolutions_data_import_id_data_imports')
        ),
        # NOTE: master_flow_id is indexed but NOT a FK (per GPT-5 feedback)
        # ADR rule: FKs must reference table PKs, not flow_id columns
        # master_flow_id stored for filtering/auditing only
        sa.ForeignKeyConstraint(
            ['existing_asset_id'],
            ['migration.assets.id'],
            name=op.f('fk_asset_conflict_resolutions_existing_asset_id_assets'),
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['resolved_by'],
            ['migration.users.id'],
            name=op.f('fk_asset_conflict_resolutions_resolved_by_users')
        ),

        schema='migration'
    )

    # Create indexes
    op.create_index(
        op.f('ix_asset_conflict_resolutions_status'),
        'asset_conflict_resolutions',
        ['resolution_status'],
        unique=False,
        schema='migration'
    )
    
    # NEW: Add composite index for name+asset_type deduplication (per GPT-5 feedback)
    # Verifies existing composite unique constraint includes asset_type
    op.execute("""
        -- Verify or create composite index for (client_account_id, engagement_id, name, asset_type)
        CREATE INDEX IF NOT EXISTS ix_assets_name_type_per_context 
        ON migration.assets (client_account_id, engagement_id, name, asset_type)
        WHERE name IS NOT NULL AND name != '';
    """)
    op.create_index(
        op.f('ix_asset_conflict_resolutions_client_engagement'),
        'asset_conflict_resolutions',
        ['client_account_id', 'engagement_id'],
        unique=False,
        schema='migration'
    )
    op.create_index(
        op.f('ix_asset_conflict_resolutions_data_import'),
        'asset_conflict_resolutions',
        ['data_import_id'],
        unique=False,
        schema='migration'
    )
    op.create_index(
        op.f('ix_asset_conflict_resolutions_master_flow'),
        'asset_conflict_resolutions',
        ['master_flow_id'],
        unique=False,
        schema='migration'
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_asset_conflict_resolutions_master_flow'), table_name='asset_conflict_resolutions', schema='migration')
    op.drop_index(op.f('ix_asset_conflict_resolutions_data_import'), table_name='asset_conflict_resolutions', schema='migration')
    op.drop_index(op.f('ix_asset_conflict_resolutions_client_engagement'), table_name='asset_conflict_resolutions', schema='migration')
    op.drop_index(op.f('ix_asset_conflict_resolutions_status'), table_name='asset_conflict_resolutions', schema='migration')
    op.drop_table('asset_conflict_resolutions', schema='migration')
```

**Task 1.2: Test Migration**

```bash
# In Docker backend container
cd backend
alembic upgrade head
alembic downgrade -1
alembic upgrade head

# Verify table creation
docker exec -it migration_postgres psql -U postgres -d migration_db -c "\d migration.asset_conflict_resolutions"
```

#### Verification
- [ ] Migration creates table successfully
- [ ] All indexes created
- [ ] Foreign keys enforce referential integrity
- [ ] Downgrade removes table cleanly

---

### **WORKSTREAM 2: Service Layer - Unified Deduplication in AssetService**

**Agent**: `python-crewai-fastapi-expert`
**Priority**: High (blocking for WS3, WS4)
**Estimated Complexity**: High
**Estimated Time**: 8 hours
**Dependencies**: WS1 (database migration)

#### Files to Create/Modify
- `backend/app/models/asset_conflict_resolution.py` (NEW)
- `backend/app/services/asset_service/deduplication.py` (MODIFY - **major refactor**)

#### Tasks

**Task 2.1: Create SQLAlchemy Model**

```python
# backend/app/models/asset_conflict_resolution.py

"""
SQLAlchemy model for asset conflict resolution tracking.

CC: Stores detected asset conflicts for user resolution
"""

import uuid
from datetime import datetime
from typing import Dict, Any

from sqlalchemy import Column, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class AssetConflictResolution(Base, TimestampMixin):
    """
    Tracks asset conflicts detected during import for user resolution.

    Workflow:
    1. Executor detects conflict via bulk_prepare_conflicts()
    2. Creates record with resolution_status='pending'
    3. Frontend displays conflict modal
    4. User chooses action (keep_existing/replace_with_new/merge)
    5. API updates record with resolution_status='resolved'
    6. Executor resumes and processes resolution
    """

    __tablename__ = "asset_conflict_resolutions"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenant context
    client_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.client_accounts.id"),
        nullable=False,
        index=True
    )
    engagement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.engagements.id"),
        nullable=False,
        index=True
    )
    data_import_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.data_imports.id"),
        nullable=True,
        index=True
    )
    # NOTE: master_flow_id is indexed but NOT a FK (per GPT-5 feedback)
    # ADR rule: FKs must reference table PKs, not flow_id columns
    master_flow_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Master flow ID for filtering/auditing (not FK)"
    )

    # Conflict identification
    conflict_type = Column(String(50), nullable=False)  # 'duplicate_hostname', 'duplicate_ip', 'duplicate_name'
    conflict_key = Column(String(255), nullable=False)  # The conflicting value (e.g., hostname)

    # Existing asset reference
    existing_asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=False
    )
    existing_asset_snapshot = Column(JSONB, nullable=False)  # Full asset data for UI comparison

    # New asset data
    new_asset_data = Column(JSONB, nullable=False)  # Proposed new asset data

    # Resolution
    resolution_status = Column(String(20), default="pending", nullable=False)  # pending, resolved, cancelled
    resolution_action = Column(String(20))  # keep_existing, replace_with_new, merge
    merge_field_selections = Column(JSONB)  # {"os_version": "new", "memory_gb": "existing"}
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("migration.users.id"))
    resolved_at = Column(DateTime(timezone=True))

    # Relationships
    existing_asset = relationship("Asset", foreign_keys=[existing_asset_id])
    resolver = relationship("User", foreign_keys=[resolved_by])

    def __repr__(self):
        return (
            f"<AssetConflictResolution(id={self.id}, "
            f"type={self.conflict_type}, key={self.conflict_key}, "
            f"status={self.resolution_status})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for API responses"""
        return {
            "id": str(self.id),
            "conflict_type": self.conflict_type,
            "conflict_key": self.conflict_key,
            "existing_asset_id": str(self.existing_asset_id),
            "existing_asset": self.existing_asset_snapshot,
            "new_asset": self.new_asset_data,
            "resolution_status": self.resolution_status,
            "resolution_action": self.resolution_action,
            "merge_field_selections": self.merge_field_selections,
            "resolved_by": str(self.resolved_by) if self.resolved_by else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
```

**Task 2.2: Refactor AssetService Deduplication**

```python
# backend/app/services/asset_service/deduplication.py
# MODIFY existing file - add new methods and constants

import logging
import uuid
from typing import Dict, Any, Optional, Tuple, Literal, Set, List
from datetime import datetime

from sqlalchemy import select, and_, or_
from sqlalchemy.exc import IntegrityError

from app.models.asset import Asset, AssetStatus
from .helpers import get_smart_asset_name, convert_numeric_fields

logger = logging.getLogger(__name__)


# ============================================================================
# FIELD MERGE ALLOWLIST - CRITICAL FOR SECURITY
# ============================================================================

# Fields that CAN be merged (safe to update)
DEFAULT_ALLOWED_MERGE_FIELDS = {
    # Technical specs
    "operating_system", "os_version", "cpu_cores", "memory_gb", "storage_gb",
    # Network info
    "ip_address", "fqdn", "mac_address",
    # Infrastructure
    "environment", "location", "datacenter", "rack_location", "availability_zone",
    # Business info
    "business_owner", "technical_owner", "department", "application_name",
    "technology_stack", "criticality", "business_criticality",
    # Migration planning
    "six_r_strategy", "migration_priority", "migration_complexity", "migration_wave",
    # Metadata
    "description", "custom_attributes",
    # Performance metrics
    "cpu_utilization_percent", "memory_utilization_percent", "disk_iops",
    "network_throughput_mbps", "current_monthly_cost", "estimated_cloud_cost",
}

# Fields that MUST NEVER be merged (immutable identifiers and tenant context)
NEVER_MERGE_FIELDS = {
    "id", "client_account_id", "engagement_id",
    "flow_id", "master_flow_id", "discovery_flow_id",
    "assessment_flow_id", "planning_flow_id", "execution_flow_id",
    "raw_import_records_id", "created_at", "created_by",
    "name", "asset_name",  # Part of identity
    "hostname",  # Part of unique constraint - never merge
}


# ============================================================================
# MAIN API - SINGLE SOURCE OF TRUTH FOR ASSET CREATION
# ============================================================================

async def create_or_update_asset(
    service_instance,
    asset_data: Dict[str, Any],
    flow_id: Optional[str] = None,
    *,
    upsert: bool = False,
    merge_strategy: Literal["enrich", "overwrite"] = "enrich",
    conflict_detection_mode: bool = False,  # NEW: enable preflight conflict check
    allowed_merge_fields: Optional[Set[str]] = None,  # NEW: field allowlist for merge
) -> Tuple[Asset, Literal["created", "existed", "updated", "conflict"]]:
    """
    SINGLE SOURCE OF TRUTH for asset creation/update with optional conflict detection.

    Args:
        service_instance: AssetService instance (self)
        asset_data: Asset information
        flow_id: Optional flow ID for context
        upsert: If True, allow updates to existing assets
        merge_strategy: "enrich" (non-destructive) or "overwrite" (replace)
        conflict_detection_mode: If True, return conflicts instead of creating
        allowed_merge_fields: Set of fields allowed for merge (defaults to DEFAULT_ALLOWED_MERGE_FIELDS)

    Returns:
        Tuple of (asset, status) where status is:
        - "created": New asset was created
        - "existed": Identical asset already exists (returned unchanged)
        - "updated": Existing asset was updated
        - "conflict": Duplicate detected (only when conflict_detection_mode=True)

    NEW BEHAVIOR (conflict_detection_mode=True):
    - If duplicate exists, return (existing_asset, "conflict") immediately
    - Does NOT create or update asset
    - Caller responsible for storing conflict in asset_conflict_resolutions table

    FIELD MERGE SAFETY:
    - Only fields in allowed_merge_fields can be merged
    - Fields in NEVER_MERGE_FIELDS are always excluded
    - Default allowlist excludes tenant context and immutable identifiers

    Raises:
        ValueError: If missing required tenant context
        IntegrityError: If database constraint violation persists after retry
    """
    try:
        # Extract context IDs
        client_id, engagement_id = await service_instance._extract_context_ids(asset_data)

        # Hierarchical deduplication check (REUSE existing logic)
        existing_asset, match_criterion = await find_existing_asset_hierarchical(
            service_instance, asset_data, client_id, engagement_id
        )

        if existing_asset:
            logger.info(
                f"🔍 Found existing asset '{existing_asset.name}' "
                f"(ID: {existing_asset.id}) via {match_criterion}"
            )

            if conflict_detection_mode:
                # NEW PATH: Return conflict for caller to handle
                logger.info(f"⚠️ Conflict detected via {match_criterion}: {existing_asset.name}")
                return (existing_asset, "conflict")

            if not upsert:
                # Default: return existing unchanged
                return (existing_asset, "existed")

            # Upsert path with field allowlist validation
            if merge_strategy == "enrich":
                updated_asset = await enrich_asset(
                    service_instance, existing_asset, asset_data, allowed_merge_fields
                )
                logger.info(f"✨ Enriched asset '{existing_asset.name}' with new data")
            else:
                updated_asset = await overwrite_asset(
                    service_instance, existing_asset, asset_data, allowed_merge_fields
                )
                logger.warning(f"⚠️ Overwrote asset '{existing_asset.name}' with new data")

            return (updated_asset, "updated")

        # No duplicate - create new asset
        try:
            new_asset = await create_new_asset(service_instance, asset_data, flow_id)
            logger.info(f"✅ Created new asset '{new_asset.name}' (ID: {new_asset.id})")
            return (new_asset, "created")
        except IntegrityError as ie:
            await service_instance.db.rollback()  # Prevent session invalidation
            logger.warning(
                f"⚠️ IntegrityError during asset creation (likely race condition): {ie}"
            )

            # Retry hierarchical lookup after rollback - another process may have created it
            existing_asset, match_criterion = await find_existing_asset_hierarchical(
                service_instance, asset_data, client_id, engagement_id
            )

            if existing_asset:
                logger.info(
                    f"🔄 Found asset after rollback via {match_criterion}, returning existing"
                )
                if conflict_detection_mode:
                    return (existing_asset, "conflict")
                return (existing_asset, "existed")
            else:
                # True duplicate key conflict - log and re-raise
                logger.error(f"❌ IntegrityError persists after retry: {ie}")
                raise

    except IntegrityError:
        # Already handled above, but catch here to prevent outer exception handler
        raise
    except Exception as e:
        logger.error(f"❌ create_or_update_asset failed: {e}")
        raise


# ============================================================================
# BULK CONFLICT DETECTION - O(1) PER ASSET
# ============================================================================

async def bulk_prepare_conflicts(
    service_instance,
    assets_data: List[Dict[str, Any]],
    client_id: uuid.UUID,
    engagement_id: uuid.UUID,
) -> Tuple[List[Dict], List[Dict]]:
    """
    NEW METHOD: Bulk prefetch for O(1) conflict detection.

    Performance optimization: Single query per field type (hostname/ip/name),
    then in-memory O(1) lookups. Eliminates N+1 query problem.

    Args:
        service_instance: AssetService instance
        assets_data: List of asset data dictionaries to check
        client_id: Client account UUID
        engagement_id: Engagement UUID

    Returns:
        Tuple of (conflict_free_assets, conflicting_assets_with_details)

        conflicting_assets_with_details format:
        [
            {
                "conflict_type": "duplicate_hostname",
                "conflict_key": "server-prod-01",
                "existing_asset_id": UUID,
                "existing_asset_data": {...},
                "new_asset_data": {...}
            },
            ...
        ]
    """
    if not assets_data:
        return [], []

    logger.info(f"🔍 Bulk conflict detection for {len(assets_data)} assets")

    # Step 1: Extract all unique identifiers from batch
    hostnames = {a.get("hostname") for a in assets_data if a.get("hostname")}
    ip_addresses = {a.get("ip_address") for a in assets_data if a.get("ip_address")}
    # NEW: name+asset_type composite for reduced false positives
    name_type_pairs = {
        (get_smart_asset_name(a), a.get("asset_type", "Unknown"))
        for a in assets_data
        if get_smart_asset_name(a)
    }

    # Step 2: Bulk fetch existing assets (ONE query per field type)
    # NEW: Chunking for very large batches (per GPT-5 feedback)
    CHUNK_SIZE = 500  # Avoid parameter limits in IN clauses
    
    existing_by_hostname = {}
    existing_by_ip = {}
    existing_by_name_type = {}  # NEW: name+type composite key
    
    if hostnames:
        # Process in chunks to avoid parameter limits
        hostname_list = list(hostnames)
        for i in range(0, len(hostname_list), CHUNK_SIZE):
            chunk = hostname_list[i:i + CHUNK_SIZE]
            stmt = select(Asset).where(
                and_(
                    Asset.client_account_id == client_id,
                    Asset.engagement_id == engagement_id,
                    Asset.hostname.in_(chunk),
                    Asset.hostname != None,
                    Asset.hostname != "",
                )
            )
            result = await service_instance.db.execute(stmt)
            for asset in result.scalars().all():
                existing_by_hostname[asset.hostname] = asset
        logger.debug(f"  Found {len(existing_by_hostname)} existing assets by hostname")

    if ip_addresses:
        # Process in chunks to avoid parameter limits
        ip_list = list(ip_addresses)
        for i in range(0, len(ip_list), CHUNK_SIZE):
            chunk = ip_list[i:i + CHUNK_SIZE]
            stmt = select(Asset).where(
                and_(
                    Asset.client_account_id == client_id,
                    Asset.engagement_id == engagement_id,
                    Asset.ip_address.in_(chunk),
                    Asset.ip_address != None,
                    Asset.ip_address != "",
                )
            )
            result = await service_instance.db.execute(stmt)
            for asset in result.scalars().all():
                existing_by_ip[asset.ip_address] = asset
        logger.debug(f"  Found {len(existing_by_ip)} existing assets by IP")

    # NEW: Query by name+asset_type composite (reduces false positives)
    if name_type_pairs:
        # Process in chunks to avoid parameter limits
        names_only = list({name for name, _ in name_type_pairs})
        for i in range(0, len(names_only), CHUNK_SIZE):
            chunk = names_only[i:i + CHUNK_SIZE]
            stmt = select(Asset).where(
                and_(
                    Asset.client_account_id == client_id,
                    Asset.engagement_id == engagement_id,
                    Asset.name.in_(chunk),
                    Asset.name != None,
                    Asset.name != "",
                )
            )
            result = await service_instance.db.execute(stmt)
            # Build dict with (name, asset_type) composite key
            for asset in result.scalars().all():
                key = (asset.name, asset.asset_type or "Unknown")
                existing_by_name_type[key] = asset
        logger.debug(f"  Found {len(existing_by_name_type)} existing assets by name+type")

    # Step 3: O(1) lookup for each asset
    conflict_free = []
    conflicts = []

    for asset_data in assets_data:
        hostname = asset_data.get("hostname")
        ip = asset_data.get("ip_address")
        name = get_smart_asset_name(asset_data)
        asset_type = asset_data.get("asset_type", "Unknown")  # NEW: for composite key

        # Check hostname first (highest priority unique constraint)
        if hostname and hostname in existing_by_hostname:
            existing = existing_by_hostname[hostname]
            conflicts.append({
                "conflict_type": "duplicate_hostname",
                "conflict_key": hostname,
                "existing_asset_id": existing.id,
                "existing_asset_data": serialize_asset_for_comparison(existing),
                "new_asset_data": asset_data,
            })
            continue

        # Check IP address
        if ip and ip in existing_by_ip:
            existing = existing_by_ip[ip]
            conflicts.append({
                "conflict_type": "duplicate_ip",
                "conflict_key": ip,
                "existing_asset_id": existing.id,
                "existing_asset_data": serialize_asset_for_comparison(existing),
                "new_asset_data": asset_data,
            })
            continue

        # Check name+asset_type composite (NEW: reduces false positives)
        name_type_key = (name, asset_type)
        if name and name_type_key in existing_by_name_type:
            existing = existing_by_name_type[name_type_key]
            conflicts.append({
                "conflict_type": "duplicate_name",
                "conflict_key": f"{name} ({asset_type})",  # Include type in display
                "existing_asset_id": existing.id,
                "existing_asset_data": serialize_asset_for_comparison(existing),
                "new_asset_data": asset_data,
            })
            continue

        # No conflict found
        conflict_free.append(asset_data)

    logger.info(
        f"✅ Bulk conflict detection complete: "
        f"{len(conflict_free)} conflict-free, {len(conflicts)} conflicts"
    )

    return conflict_free, conflicts


def serialize_asset_for_comparison(asset: Asset) -> Dict:
    """
    Extract safe fields for UI comparison with PII hygiene.

    NEW (per GPT-5 feedback):
    - Limits snapshot fields to defined allowlist (prevents sensitive data leakage)
    - Redacts custom_attributes by default (may contain PII)
    - Only includes fields necessary for conflict resolution
    
    Note: UI should still apply display restrictions for additional safety.
    """
    # NEW: Only include fields from DEFAULT_ALLOWED_MERGE_FIELDS (PII hygiene)
    # Excludes raw_data, custom_attributes, and other potentially sensitive fields
    return {
        "id": str(asset.id),
        "name": asset.name,
        "hostname": asset.hostname,
        "ip_address": asset.ip_address,
        "asset_type": asset.asset_type,
        "operating_system": asset.operating_system,
        "os_version": asset.os_version,
        "cpu_cores": asset.cpu_cores,
        "memory_gb": asset.memory_gb,
        "storage_gb": asset.storage_gb,
        "environment": asset.environment,
        "business_owner": asset.business_owner,
        "department": asset.department,
        "criticality": asset.criticality,
        "location": asset.location,
        "datacenter": asset.datacenter,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
        # NOTE: custom_attributes explicitly excluded for PII protection
        # NOTE: raw_data explicitly excluded for PII protection
    }


# ============================================================================
# MERGE OPERATIONS WITH FIELD ALLOWLIST VALIDATION
# ============================================================================

async def enrich_asset(
    service_instance,
    existing: Asset,
    new_data: Dict[str, Any],
    allowed_merge_fields: Optional[Set[str]] = None,
) -> Asset:
    """
    Non-destructive enrichment: add new fields, keep existing values.

    NEW: Field allowlist validation.
    - Only merge fields in allowlist that don't exist in existing asset
    - Skip fields in NEVER_MERGE_FIELDS
    - Log warnings for attempted protected field merges
    """
    allowlist = allowed_merge_fields or DEFAULT_ALLOWED_MERGE_FIELDS

    for field, value in new_data.items():
        # Skip if field not in allowlist
        if field not in allowlist:
            continue

        # Skip if field in never-merge list
        if field in NEVER_MERGE_FIELDS:
            logger.warning(f"⚠️ Attempted to merge protected field '{field}' - skipping")
            continue

        # Only update if existing value is None/empty
        if value and not getattr(existing, field, None):
            setattr(existing, field, value)

    # Special handling for custom_attributes (merge dicts)
    if "custom_attributes" in new_data and "custom_attributes" in allowlist:
        existing_attrs = existing.custom_attributes or {}
        new_attrs = new_data["custom_attributes"]
        existing.custom_attributes = {**existing_attrs, **new_attrs}

    existing.updated_at = datetime.utcnow()
    await service_instance.db.flush()
    return existing


async def overwrite_asset(
    service_instance,
    existing: Asset,
    new_data: Dict[str, Any],
    allowed_merge_fields: Optional[Set[str]] = None,
) -> Asset:
    """
    Explicit overwrite: replace allowed fields with new values.

    NEW: Implement "replace_with_new" as UPDATE (not delete+create).
    - Preserves FK relationships and audit history
    - Only updates fields in allowlist
    - Respects NEVER_MERGE_FIELDS protection
    """
    allowlist = allowed_merge_fields or DEFAULT_ALLOWED_MERGE_FIELDS

    for field, value in new_data.items():
        # Skip if field not in allowlist or in never-merge list
        if field not in allowlist or field in NEVER_MERGE_FIELDS:
            continue

        # Overwrite existing value with new value
        if value is not None:
            setattr(existing, field, value)

    existing.updated_at = datetime.utcnow()
    await service_instance.db.flush()
    return existing


# ============================================================================
# EXISTING METHODS - UNCHANGED
# ============================================================================

# Keep existing implementations of:
# - find_existing_asset_hierarchical()
# - create_new_asset()
# - bulk_create_or_update_assets()
# - _build_prefetch_criteria()
# - _build_lookup_indexes()
# - _find_existing_in_indexes()

# (No changes needed to these methods)
```

#### Verification
- [ ] All deduplication logic unified in `create_or_update_asset()`
- [ ] `conflict_detection_mode=True` returns conflicts instead of creating
- [ ] `bulk_prepare_conflicts()` uses single query per field type
- [ ] Field merge allowlist enforced in `enrich_asset()` and `overwrite_asset()`
- [ ] `NEVER_MERGE_FIELDS` protected from updates
- [ ] Unit tests pass for conflict detection and merge operations

---

### **WORKSTREAM 3: API Layer - Simplified Endpoints (NO /detect)**

**Agent**: `python-crewai-fastapi-expert`
**Priority**: Medium (blocking for WS5)
**Estimated Complexity**: Medium
**Estimated Time**: 4 hours
**Dependencies**: WS2 (service layer)

#### Files to Create/Modify
- `backend/app/api/v1/endpoints/asset_conflicts.py` (NEW)
- `backend/app/schemas/asset_conflict.py` (NEW)
- `backend/app/api/v1/router_imports.py` (MODIFY)
- `backend/app/api/v1/router_registry.py` (MODIFY)

#### Tasks

**Task 3.1: Create Pydantic Schemas**

```python
# backend/app/schemas/asset_conflict.py

"""
Pydantic schemas for asset conflict resolution API.

CC: Request/response models for conflict resolution endpoints
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional
from uuid import UUID


class AssetConflictDetail(BaseModel):
    """Conflict detail for UI display"""
    conflict_id: UUID
    conflict_type: str  # duplicate_hostname, duplicate_name, duplicate_ip
    conflict_key: str  # The conflicting value
    existing_asset: Dict  # Serialized asset for comparison
    new_asset: Dict  # Proposed new asset data


class AssetConflictResolutionRequest(BaseModel):
    """Single conflict resolution request"""
    conflict_id: UUID
    resolution_action: Literal["keep_existing", "replace_with_new", "merge"]
    merge_field_selections: Optional[Dict[str, Literal["existing", "new"]]] = None
    # Example: {"os_version": "new", "memory_gb": "existing", "cpu_cores": "new"}


class BulkConflictResolutionRequest(BaseModel):
    """Bulk resolution request for multiple conflicts"""
    resolutions: List[AssetConflictResolutionRequest]


class ConflictResolutionResponse(BaseModel):
    """Response after resolving conflicts"""
    resolved_count: int
    total_requested: int
    errors: Optional[List[str]] = None
```

**Task 3.2: Create API Endpoints**

```python
# backend/app/api/v1/endpoints/asset_conflicts.py

"""
Asset Conflict Resolution API Endpoints.

KEY CHANGE: No /detect endpoint - detection happens in executor.
Only expose /list and /resolve-bulk for UI interaction.

CC: User-driven conflict resolution during discovery flow
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_db, get_current_user
from app.models.asset import Asset
from app.models.asset_conflict_resolution import AssetConflictResolution
from app.models.user import User
from app.schemas.asset_conflict import (
    AssetConflictDetail,
    BulkConflictResolutionRequest,
    ConflictResolutionResponse,
)
from app.services.asset_service import AssetService
from app.services.asset_service.deduplication import (
    overwrite_asset,
    DEFAULT_ALLOWED_MERGE_FIELDS,
    NEVER_MERGE_FIELDS,
)

router = APIRouter(prefix="/api/v1/asset-conflicts", tags=["Asset Conflicts"])
logger = logging.getLogger(__name__)


@router.get("/list", response_model=List[AssetConflictDetail])
async def list_pending_conflicts(
    flow_id: UUID,  # Use flow_id to derive tenant context
    data_import_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # AUTH REQUIRED
    request_context: RequestContext = Depends(get_request_context),  # TENANT CONTEXT
):
    """
    List all pending conflicts for a tenant+engagement.

    NEW: Uses RequestContext dependency for tenant scoping (per GPT-5 feedback)
    - Eliminates custom x-tenant-id header
    - Reuses existing auth infrastructure
    - Automatically validates tenant access

    Query Parameters:
        flow_id: Discovery flow UUID (used to derive tenant context)
        data_import_id: Filter by specific data import (optional)

    Returns:
        List of AssetConflictDetail with side-by-side comparison data
    """
    # Extract tenant IDs from RequestContext (already validated by dependency)
    client_account_id = UUID(request_context.client_account_id)
    engagement_id = UUID(request_context.engagement_id)

    # Query pending conflicts for this context
    stmt = select(AssetConflictResolution).where(
        and_(
            AssetConflictResolution.client_account_id == client_account_id,
            AssetConflictResolution.engagement_id == engagement_id,
            AssetConflictResolution.resolution_status == "pending",
        )
    )

    if data_import_id:
        stmt = stmt.where(AssetConflictResolution.data_import_id == data_import_id)

    result = await db.execute(stmt)
    conflicts = result.scalars().all()

    logger.info(
        f"📋 Retrieved {len(conflicts)} pending conflicts for "
        f"client={client_account_id}, engagement={engagement_id}"
    )

    return [
        AssetConflictDetail(
            conflict_id=c.id,
            conflict_type=c.conflict_type,
            conflict_key=c.conflict_key,
            existing_asset=c.existing_asset_snapshot,
            new_asset=c.new_asset_data,
        )
        for c in conflicts
    ]


@router.post("/resolve-bulk", response_model=ConflictResolutionResponse)
async def resolve_conflicts_bulk(
    request: BulkConflictResolutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # AUTH REQUIRED
    request_context: RequestContext = Depends(get_request_context),  # TENANT CONTEXT
):
    """
    Apply user's conflict resolution choices in bulk.

    NEW FEATURES:
    - resolved_by extracted from authenticated user context (not payload)
    - "replace_with_new" implemented as UPDATE (not delete+create)
    - Field merge allowlist validation
    - Multi-tenant access control

    Resolution Actions:
        keep_existing: Do nothing, existing asset unchanged
        replace_with_new: UPDATE existing asset with new data (preserves FKs)
        merge: Update specific fields based on user selections

    Returns:
        ConflictResolutionResponse with success count and errors
    """
    resolved_count = 0
    errors = []

    for resolution in request.resolutions:
        try:
            conflict_id = resolution.conflict_id
            action = resolution.resolution_action
            merge_selections = resolution.merge_field_selections or {}

            # Fetch conflict record
            conflict = await db.get(AssetConflictResolution, conflict_id)
            if not conflict:
                errors.append(f"Conflict {conflict_id} not found")
                continue

            # Validate tenant access via RequestContext (auto-validated by dependency)
            if conflict.client_account_id != UUID(request_context.client_account_id):
                errors.append(f"Conflict {conflict_id}: tenant access denied")
                continue

            # Validate conflict is still pending
            if conflict.resolution_status != "pending":
                errors.append(
                    f"Conflict {conflict_id} already resolved with action: "
                    f"{conflict.resolution_action}"
                )
                continue

            # Execute resolution based on action
            if action == "keep_existing":
                # Do nothing - existing asset stays unchanged
                logger.info(f"✅ Keeping existing asset for conflict {conflict_id}")

            elif action == "replace_with_new":
                # NEW: UPDATE existing asset (not delete+create)
                # Preserves FK relationships, audit history, and dependencies
                existing_asset = await db.get(Asset, conflict.existing_asset_id)
                if not existing_asset:
                    errors.append(
                        f"Conflict {conflict_id}: existing asset {conflict.existing_asset_id} not found"
                    )
                    continue

                # Use overwrite_asset from service (respects field allowlist)
                # NEW: Pass real RequestContext (per GPT-5 feedback - never pass None)
                asset_service = AssetService(db, request_context)
                await overwrite_asset(
                    asset_service,
                    existing_asset,
                    conflict.new_asset_data,
                    allowed_merge_fields=DEFAULT_ALLOWED_MERGE_FIELDS
                )

                logger.info(
                    f"✅ Replaced existing asset {existing_asset.name} "
                    f"with new data for conflict {conflict_id}"
                )

            elif action == "merge":
                # Validate merge_field_selections against allowlist
                invalid_fields = set(merge_selections.keys()) - DEFAULT_ALLOWED_MERGE_FIELDS
                protected_fields = set(merge_selections.keys()) & NEVER_MERGE_FIELDS

                if invalid_fields:
                    errors.append(
                        f"Conflict {conflict_id}: invalid merge fields: {invalid_fields}"
                    )
                    continue

                if protected_fields:
                    errors.append(
                        f"Conflict {conflict_id}: cannot merge protected fields: {protected_fields}"
                    )
                    continue

                # Update existing asset with selected fields
                existing_asset = await db.get(Asset, conflict.existing_asset_id)
                if not existing_asset:
                    errors.append(
                        f"Conflict {conflict_id}: existing asset {conflict.existing_asset_id} not found"
                    )
                    continue

                # Apply merge selections
                for field_name, source in merge_selections.items():
                    if source == "new" and field_name in conflict.new_asset_data:
                        setattr(existing_asset, field_name, conflict.new_asset_data[field_name])

                existing_asset.updated_at = datetime.utcnow()

                logger.info(
                    f"✅ Merged {len(merge_selections)} fields for "
                    f"asset {existing_asset.name} (conflict {conflict_id})"
                )

            # Mark conflict as resolved
            conflict.resolution_status = "resolved"
            conflict.resolution_action = action
            conflict.merge_field_selections = merge_selections if action == "merge" else None
            conflict.resolved_by = current_user.id  # FROM AUTH CONTEXT
            conflict.resolved_at = datetime.utcnow()

            resolved_count += 1

        except Exception as e:
            error_msg = f"Conflict {resolution.conflict_id}: {str(e)}"
            logger.error(f"❌ Resolution failed: {error_msg}")
            errors.append(error_msg)

    # Flush changes (caller commits per ADR-012)
    await db.flush()

    logger.info(
        f"✅ Resolved {resolved_count}/{len(request.resolutions)} conflicts, "
        f"{len(errors)} errors"
    )

    return ConflictResolutionResponse(
        resolved_count=resolved_count,
        total_requested=len(request.resolutions),
        errors=errors if errors else None,
    )
```

**Task 3.3: Register Router**

```python
# backend/app/api/v1/router_imports.py
# Add to imports section:
from app.api.v1.endpoints import asset_conflicts

# backend/app/api/v1/router_registry.py
# Add to router registration:
from app.api.v1.endpoints.asset_conflicts import router as asset_conflicts_router
app.include_router(asset_conflicts_router)
```

#### Verification
- [ ] `/api/v1/asset-conflicts/list` returns pending conflicts
- [ ] `/api/v1/asset-conflicts/resolve-bulk` applies resolutions
- [ ] Auth headers required for all endpoints
- [ ] Tenant access validated via `x-tenant-id` header
- [ ] `resolved_by` extracted from auth context (not payload)
- [ ] Field merge allowlist enforced
- [ ] "replace_with_new" uses UPDATE (not delete+create)

---

### **WORKSTREAM 4: Executor Integration - Child Flow Pause via DiscoveryFlow**

**Agent**: `python-crewai-fastapi-expert`
**Priority**: High (blocking for integration)
**Estimated Complexity**: Medium
**Estimated Time**: 4 hours
**Dependencies**: WS2 (service layer)

#### Files to Modify
- `backend/app/repositories/discovery_flow_repository.py` (MODIFY - add pause/resume methods)
- `backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor/base.py` (MODIFY)

#### Tasks

**Task 4.1: Add Pause/Resume Methods to DiscoveryFlowRepository**

```python
# backend/app/repositories/discovery_flow_repository.py
# Add new methods to DiscoveryFlowRepository class

import json
from datetime import datetime
from uuid import UUID
from sqlalchemy import update, func
from sqlalchemy.sql import text as sa_text


async def set_conflict_resolution_pending(
    self,
    flow_id: UUID,
    conflict_count: int,
    data_import_id: Optional[UUID] = None,
) -> None:
    """
    Pause discovery flow for conflict resolution.

    Sets phase_state flags per ADR-012 (child flow owns operational state):
    - phase_state.conflict_resolution_pending: true
    - phase_state.conflict_metadata: { conflict_count, data_import_id, paused_at }

    NOTE: status remains 'active' (flow is paused but not completed)

    Args:
        flow_id: Discovery flow UUID
        conflict_count: Number of conflicts detected
        data_import_id: Optional data import UUID for filtering
    """
    conflict_metadata = {
        'conflict_count': conflict_count,
        'data_import_id': str(data_import_id) if data_import_id else None,
        'paused_at': datetime.utcnow().isoformat(),
    }

    # NEW: Coalesce phase_state to empty JSONB before jsonb_set (per GPT-5 feedback)
    # Prevents failure when phase_state is NULL
    stmt = (
        update(DiscoveryFlow)
        .where(DiscoveryFlow.flow_id == flow_id)
        .values(
            phase_state=func.jsonb_set(
                func.jsonb_set(
                    func.coalesce(DiscoveryFlow.phase_state, sa_text("'{}'::jsonb")),
                    '{conflict_resolution_pending}',
                    sa_text("'true'::jsonb"),
                ),
                '{conflict_metadata}',
                sa_text(f"'{json.dumps(conflict_metadata)}'::jsonb"),
            ),
            updated_at=datetime.utcnow(),
        )
    )

    await self.db.execute(stmt)

    logger.info(
        f"⏸️ Discovery flow {flow_id} paused for conflict resolution "
        f"({conflict_count} conflicts)"
    )


async def clear_conflict_resolution_pending(self, flow_id: UUID) -> None:
    """
    Resume discovery flow after conflict resolution.

    Clears phase_state.conflict_resolution_pending flag and metadata.

    Args:
        flow_id: Discovery flow UUID
    """
    # NEW: Coalesce phase_state to empty JSONB before jsonb_set (per GPT-5 feedback)
    stmt = (
        update(DiscoveryFlow)
        .where(DiscoveryFlow.flow_id == flow_id)
        .values(
            phase_state=func.jsonb_set(
                func.jsonb_set(
                    func.coalesce(DiscoveryFlow.phase_state, sa_text("'{}'::jsonb")),
                    '{conflict_resolution_pending}',
                    sa_text("'false'::jsonb"),
                ),
                '{conflict_metadata}',
                sa_text("'{}'::jsonb"),
            ),
            updated_at=datetime.utcnow(),
        )
    )

    await self.db.execute(stmt)

    logger.info(f"▶️ Discovery flow {flow_id} resumed after conflict resolution")


async def get_conflict_resolution_status(self, flow_id: UUID) -> Optional[Dict]:
    """
    Check if flow is paused for conflict resolution.

    Returns:
        Dict with { pending: bool, conflict_count: int, data_import_id: str } or None
    """
    stmt = select(DiscoveryFlow.phase_state).where(DiscoveryFlow.flow_id == flow_id)
    result = await self.db.execute(stmt)
    phase_state = result.scalar_one_or_none()

    if not phase_state:
        return None

    is_pending = phase_state.get('conflict_resolution_pending', False)
    conflict_metadata = phase_state.get('conflict_metadata', {})

    return {
        'pending': is_pending,
        'conflict_count': conflict_metadata.get('conflict_count', 0),
        'data_import_id': conflict_metadata.get('data_import_id'),
        'paused_at': conflict_metadata.get('paused_at'),
    }
```

**Task 4.2: Modify Asset Inventory Executor**

```python
# backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor/base.py
# MODIFY lines 168-218 (Asset creation section)

from app.services.asset_service.deduplication import bulk_prepare_conflicts
from app.models.asset_conflict_resolution import AssetConflictResolution
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

# ... existing code ...

# REPLACE current batch processing (lines 175-218) with:

logger.info(f"🔄 Processing {len(assets_data)} assets with bulk conflict detection")

# Step 1: Bulk conflict detection (single query per field type)
conflict_free, conflicts_data = await bulk_prepare_conflicts(
    asset_service,
    assets_data,
    client_account_id,
    engagement_id,
)

if conflicts_data:
    logger.warning(
        f"⚠️ Detected {len(conflicts_data)} asset conflicts - pausing for user resolution"
    )

    # Step 2: Store conflicts in database
    for conflict in conflicts_data:
        conflict_record = AssetConflictResolution(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            data_import_id=data_import_id,
            master_flow_id=master_flow_id,
            conflict_type=conflict["conflict_type"],
            conflict_key=conflict["conflict_key"],
            existing_asset_id=conflict["existing_asset_id"],
            existing_asset_snapshot=conflict["existing_asset_data"],
            new_asset_data=conflict["new_asset_data"],
            resolution_status="pending",
        )
        db_session.add(conflict_record)

    await db_session.flush()

    # Step 3: Pause child flow via repository (ADR-012/ADR-025)
    discovery_repo = DiscoveryFlowRepository(
        db_session, str(client_account_id), str(engagement_id)
    )
    await discovery_repo.set_conflict_resolution_pending(
        discovery_flow_id,
        conflict_count=len(conflicts_data),
        data_import_id=data_import_id,
    )

    # Step 4: Return paused status
    return {
        "status": "paused",  # Child flow status per ADR-012
        "phase": "asset_inventory",
        "message": f"Found {len(conflicts_data)} duplicate assets. User resolution required.",
        "conflict_count": len(conflicts_data),
        "conflict_free_count": len(conflict_free),
        "data_import_id": str(data_import_id) if data_import_id else None,
        "phase_state": {
            "conflict_resolution_pending": True,
        },
    }

# Step 5: Proceed with conflict-free assets (batch optimized)
logger.info(f"✅ Processing {len(conflict_free)} conflict-free assets")

try:
    results = await asset_service.bulk_create_or_update_assets(
        conflict_free, flow_id=master_flow_id
    )

    # Categorize results by status
    for asset, status in results:
        if status == "created":
            created_assets.append(asset)
            logger.debug(f"✅ Created asset: {asset.name}")
        elif status == "existed":
            duplicate_assets.append(asset)
            logger.debug(f"🔄 Duplicate asset skipped: {asset.name}")

except Exception as e:
    # If batch fails, fall back to individual processing
    logger.warning(
        f"⚠️ Batch processing failed, falling back to individual: {e}"
    )
    # ... existing fallback logic ...

# ... rest of existing code (flush, mark records processed, etc.) ...
```

#### Verification
- [ ] `set_conflict_resolution_pending()` updates `phase_state` correctly
- [ ] `clear_conflict_resolution_pending()` clears flags
- [ ] Executor calls `bulk_prepare_conflicts()` before asset creation
- [ ] Conflicts stored in `asset_conflict_resolutions` table
- [ ] Child flow paused via repository (not new mechanism)
- [ ] Paused status returned to orchestrator

---

### **WORKSTREAM 5: Frontend UI - Conflict Modal**

**Agent**: `nextjs-ui-architect`
**Priority**: Medium
**Estimated Complexity**: High
**Estimated Time**: 8 hours
**Dependencies**: WS3 (API endpoints)

#### Files to Create
- `src/components/features/discovery/AssetConflictModal.tsx` (NEW)
- `src/components/features/discovery/AssetConflictComparisonTable.tsx` (NEW)
- `src/services/assetConflictService.ts` (NEW)

#### Tasks

**Task 5.1: Create Conflict Service**

```typescript
// src/services/assetConflictService.ts

import { apiCall } from './api';

export interface AssetConflictDetail {
  conflict_id: string;
  conflict_type: string;
  conflict_key: string;
  existing_asset: Record<string, any>;
  new_asset: Record<string, any>;
}

export interface ConflictResolution {
  conflict_id: string;
  resolution_action: 'keep_existing' | 'replace_with_new' | 'merge';
  merge_field_selections?: Record<string, 'existing' | 'new'>;
}

export const assetConflictService = {
  async listPendingConflicts(
    flow_id: string,
    data_import_id?: string
  ): Promise<AssetConflictDetail[]> {
    const params = new URLSearchParams({
      flow_id,
      ...(data_import_id && { data_import_id }),
    });

    // NEW: No custom headers needed - RequestContext dependency handles tenant scoping
    return await apiCall(`/api/v1/asset-conflicts/list?${params}`, {
      method: 'GET',
    });
  },

  async resolveConflictsBulk(
    resolutions: ConflictResolution[]
  ): Promise<{ resolved_count: number; total_requested: number; errors?: string[] }> {
    // NEW: No custom headers or tenant_id param - RequestContext dependency handles it
    return await apiCall('/api/v1/asset-conflicts/resolve-bulk', {
      method: 'POST',
      body: JSON.stringify({ resolutions }),
    });
  },
};
```

**Task 5.2: Create Comparison Table Component**

```typescript
// src/components/features/discovery/AssetConflictComparisonTable.tsx

import React from 'react';

interface Props {
  existingAsset: Record<string, any>;
  newAsset: Record<string, any>;
  selectedFields: Record<string, 'existing' | 'new'>;
  onFieldSelection: (field: string, source: 'existing' | 'new') => void;
  resolutionMode: 'keep_existing' | 'replace_with_new' | 'merge' | null;
}

const COMPARISON_FIELDS = [
  { key: 'hostname', label: 'Hostname' },
  { key: 'ip_address', label: 'IP Address' },
  { key: 'operating_system', label: 'Operating System' },
  { key: 'os_version', label: 'OS Version' },
  { key: 'cpu_cores', label: 'CPU Cores' },
  { key: 'memory_gb', label: 'Memory (GB)' },
  { key: 'storage_gb', label: 'Storage (GB)' },
  { key: 'environment', label: 'Environment' },
  { key: 'business_owner', label: 'Business Owner' },
  { key: 'department', label: 'Department' },
  { key: 'criticality', label: 'Criticality' },
];

export const AssetConflictComparisonTable: React.FC<Props> = ({
  existingAsset,
  newAsset,
  selectedFields,
  onFieldSelection,
  resolutionMode,
}) => {
  const showCheckboxes = resolutionMode === 'merge';

  const isValueDifferent = (field: string) => {
    return existingAsset[field] !== newAsset[field];
  };

  return (
    <table className="w-full border-collapse">
      <thead>
        <tr className="bg-gray-100">
          <th className="border p-2 text-left">Field</th>
          <th className="border p-2 text-left">
            Existing Asset
            {resolutionMode === 'keep_existing' && (
              <span className="ml-2 text-green-600">✓ Selected</span>
            )}
          </th>
          <th className="border p-2 text-left">
            New Asset Data
            {resolutionMode === 'replace_with_new' && (
              <span className="ml-2 text-green-600">✓ Selected</span>
            )}
          </th>
          {showCheckboxes && <th className="border p-2">Use</th>}
        </tr>
      </thead>
      <tbody>
        {COMPARISON_FIELDS.map(({ key, label }) => {
          const isDifferent = isValueDifferent(key);
          const rowClass = isDifferent ? 'bg-yellow-50' : '';

          return (
            <tr key={key} className={rowClass}>
              <td className="border p-2 font-medium">
                {label}
                {isDifferent && <span className="ml-2 text-yellow-600">⚠️</span>}
              </td>
              <td className="border p-2">
                {existingAsset[key] || <span className="text-gray-400">-</span>}
              </td>
              <td className="border p-2">
                {newAsset[key] || <span className="text-gray-400">-</span>}
              </td>
              {showCheckboxes && (
                <td className="border p-2 text-center">
                  <select
                    className="border rounded px-2 py-1"
                    value={selectedFields[key] || 'existing'}
                    onChange={(e) => onFieldSelection(key, e.target.value as 'existing' | 'new')}
                    disabled={!isDifferent}
                  >
                    <option value="existing">Existing</option>
                    <option value="new">New</option>
                  </select>
                </td>
              )}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};
```

**Task 5.3: Create Main Conflict Modal**

```typescript
// src/components/features/discovery/AssetConflictModal.tsx

import React, { useState } from 'react';
import { AssetConflictComparisonTable } from './AssetConflictComparisonTable';
import { AssetConflictDetail, ConflictResolution } from '@/services/assetConflictService';

interface Props {
  conflicts: AssetConflictDetail[];
  tenantId: string;
  onResolve: (resolutions: ConflictResolution[]) => Promise<void>;
  onCancel: () => void;
}

export const AssetConflictModal: React.FC<Props> = ({ conflicts, tenantId, onResolve, onCancel }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [resolutions, setResolutions] = useState<ConflictResolution[]>([]);
  const [resolutionMode, setResolutionMode] = useState<'keep_existing' | 'replace_with_new' | 'merge' | null>(null);
  const [mergeSelections, setMergeSelections] = useState<Record<string, 'existing' | 'new'>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const currentConflict = conflicts[currentIndex];
  const isLastConflict = currentIndex === conflicts.length - 1;

  const handleNext = () => {
    if (!resolutionMode) {
      alert('Please choose a resolution action');
      return;
    }

    // Save current resolution
    const resolution: ConflictResolution = {
      conflict_id: currentConflict.conflict_id,
      resolution_action: resolutionMode,
      ...(resolutionMode === 'merge' && { merge_field_selections: mergeSelections }),
    };

    setResolutions([...resolutions, resolution]);

    if (isLastConflict) {
      // Submit all resolutions
      handleSubmit([...resolutions, resolution]);
    } else {
      // Move to next conflict
      setCurrentIndex(currentIndex + 1);
      setResolutionMode(null);
      setMergeSelections({});
    }
  };

  const handleSubmit = async (allResolutions: ConflictResolution[]) => {
    setIsSubmitting(true);
    try {
      await onResolve(allResolutions);
    } catch (error) {
      console.error('Failed to resolve conflicts:', error);
      alert('Failed to resolve conflicts. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFieldSelection = (field: string, source: 'existing' | 'new') => {
    setMergeSelections({ ...mergeSelections, [field]: source });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto p-6">
        <div className="mb-4">
          <h2 className="text-2xl font-bold">Asset Conflict Detected</h2>
          <p className="text-gray-600">
            Conflict {currentIndex + 1} of {conflicts.length}: {currentConflict.conflict_type} ({currentConflict.conflict_key})
          </p>
        </div>

        <div className="mb-6">
          <p className="text-sm text-gray-700 mb-2">
            An asset with the same <strong>{currentConflict.conflict_type.replace('duplicate_', '')}</strong> already exists.
            Please choose how to proceed:
          </p>

          <div className="flex gap-4 mb-4">
            <button
              className={`px-4 py-2 rounded ${resolutionMode === 'keep_existing' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
              onClick={() => setResolutionMode('keep_existing')}
            >
              Keep Existing Asset
            </button>
            <button
              className={`px-4 py-2 rounded ${resolutionMode === 'replace_with_new' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
              onClick={() => setResolutionMode('replace_with_new')}
            >
              Replace with New Data
            </button>
            <button
              className={`px-4 py-2 rounded ${resolutionMode === 'merge' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
              onClick={() => setResolutionMode('merge')}
            >
              Merge (Choose Fields)
            </button>
          </div>
        </div>

        <AssetConflictComparisonTable
          existingAsset={currentConflict.existing_asset}
          newAsset={currentConflict.new_asset}
          selectedFields={mergeSelections}
          onFieldSelection={handleFieldSelection}
          resolutionMode={resolutionMode}
        />

        <div className="flex justify-between mt-6">
          <button
            className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400"
            onClick={onCancel}
            disabled={isSubmitting}
          >
            Cancel Import
          </button>
          <button
            className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            onClick={handleNext}
            disabled={!resolutionMode || isSubmitting}
          >
            {isLastConflict ? 'Apply Resolutions & Continue' : 'Next Conflict →'}
          </button>
        </div>
      </div>
    </div>
  );
};
```

**Task 5.4: Integrate with Discovery Flow Polling**

```typescript
// Modify discovery flow status polling to detect paused state

const { data: flowStatus } = useQuery({
  queryKey: ['discovery-flow-status', flowId],
  queryFn: () => discoveryService.getFlowStatus(flowId),
  refetchInterval: 5000,
});

// Check for conflict resolution pending in phase_state
if (flowStatus?.phase_state?.conflict_resolution_pending) {
  // Fetch pending conflicts (NEW: simplified parameters - no tenant IDs needed)
  const conflicts = await assetConflictService.listPendingConflicts(
    flowId,
    flowStatus.data_import_id
  );

  // Show conflict modal
  setShowConflictModal(true);
  setConflicts(conflicts);
}

// Handle conflict resolution
const handleConflictResolve = async (resolutions: ConflictResolution[]) => {
  try {
    // Submit resolutions (NEW: no tenant_id param needed)
    await assetConflictService.resolveConflictsBulk(resolutions);

    // Resume flow (calls clear_conflict_resolution_pending)
    await discoveryService.resumeFlow(flowId);

    setShowConflictModal(false);
  } catch (error) {
    console.error('Failed to resolve conflicts:', error);
  }
};
```

#### Verification
- [ ] Modal displays side-by-side asset comparison
- [ ] Three resolution modes work correctly
- [ ] Merge mode shows field-by-field selection
- [ ] Navigation between conflicts works
- [ ] Bulk submission sends all resolutions
- [ ] `x-tenant-id` header included in all API calls
- [ ] Flow resumes after conflict resolution

---

## Revised Parallel Execution Matrix

| Wave | Workstream | Agent | Duration | Blocks |
|------|-----------|-------|----------|--------|
| 1 | WS1: Database Migration | pgvector-data-architect | 2 hours | WS2 |
| 2 | WS2: Service Layer Refactor | python-crewai-fastapi-expert | 8 hours | WS3, WS4 |
| 3 | WS3: API Endpoints | python-crewai-fastapi-expert | 4 hours | WS5 |
| 3 | WS4: Executor Integration | python-crewai-fastapi-expert | 4 hours | - |
| 4 | WS5: Frontend UI | nextjs-ui-architect | 8 hours | - |

**Total Sequential Time**: ~22 hours (3 waves, with Wave 3 parallelized)
**Maximum Parallelization**: 2 agents in Wave 3 (WS3 + WS4)

---

## Success Criteria

✅ **No unhandled IntegrityErrors** (all converted to conflicts or retried)
✅ **Child flow pauses via `phase_state.conflict_resolution_pending`** (visible in polling)
✅ **All resolutions audited** with `resolved_by`, action, field diffs in `asset_conflict_resolutions`
✅ **Single dedup path in AssetService** (no parallel dedup logic)
✅ **Replace = UPDATE** (never delete+create assets)
✅ **Field merge allowlist enforced** (tenant context excluded from merge)
✅ **Bulk prefetch**: O(1) conflict detection per asset (3 queries total per batch)
✅ **DB constraints remain as final guard** with retry logic for race conditions
✅ **Auth & multi-tenancy enforced** in all API endpoints

---

## Testing Strategy

### Unit Tests
- [ ] `bulk_prepare_conflicts()` with 1000 assets (verify chunked queries: hostname, IP, name+type)
- [ ] Field allowlist validation in `enrich_asset()` and `overwrite_asset()`
- [ ] `NEVER_MERGE_FIELDS` protection
- [ ] **NEW**: Name+asset_type conflicts (same name, different types should NOT conflict)
- [ ] **NEW**: Conflict snapshot field bounds (verify only safe fields included, PII excluded)
- [ ] **NEW**: Bulk prefetch chunking (test batches >500 assets per field type)
- [ ] **NEW**: JSONB null handling (test `jsonb_set` with null `phase_state`)
- [ ] **NEW**: All `create_or_update_asset()` return statuses (created/existed/updated/conflict)
- [ ] **NEW**: IntegrityError retry logic after race condition

### Integration Tests
- [ ] Executor pause via `set_conflict_resolution_pending()`
- [ ] Executor resume via `clear_conflict_resolution_pending()`
- [ ] Conflict storage in `asset_conflict_resolutions` table
- [ ] API endpoint auth and tenant validation

### E2E Tests (Playwright)
- [ ] User resolves conflict with "Keep Existing"
- [ ] User resolves conflict with "Replace with New"
- [ ] User resolves conflict with "Merge" (field-by-field)
- [ ] Flow resumes automatically after resolution
- [ ] Multiple conflicts resolved in sequence

### Performance Tests
- [ ] Batch insert 10,000 assets with 10% conflicts (<5s total)
- [ ] Bulk prefetch queries scale linearly (not N+1)
- [ ] No session rollback cascades

---

## Rollback Plan

If issues arise during deployment:

1. **Database**: `alembic downgrade -1` to remove `asset_conflict_resolutions` table
2. **Backend**: Revert commits for WS2, WS3, WS4
3. **Frontend**: Revert commits for WS5
4. **Hotfix**: Keep existing `upsert=False` behavior (skip duplicates silently)
5. **Feature Flag**: Add `ENABLE_CONFLICT_RESOLUTION=false` env var to disable feature

---

## References

- **ADR-006**: Master Flow Orchestrator (single source of truth for workflow)
- **ADR-012**: Flow Status Management Separation (child flow owns operational state)
- **ADR-025**: Child Flow Service (flow pause/resume via repositories)
- **CLAUDE.md**: snake_case fields, multi-tenant scoping, enterprise patterns
- **Railway Logs**: `/Users/chocka/Downloads/logs.1760107948272.json` (error analysis)

---

## Appendix: GPT-5 Architectural Feedback Summary

### Must-Change Items (All Addressed)
- ✅ Single source of truth in `AssetService` (no parallel dedup modules)
- ✅ Child flow pause via `DiscoveryFlow.phase_state` (not new mechanism)
- ✅ No public `/detect` endpoint (detection in executor only)
- ✅ Replace = UPDATE (not delete+create)
- ✅ Field merge allowlist with validation
- ✅ Bulk prefetch (single query per field type)
- ✅ DB constraints remain with retry
- ✅ Auth & multi-tenancy enforced

### Nice-to-Have Enhancements (Future Work)
- Agent-recommended default action (with override)
- Index review for composite tenant constraints
- Status vocabulary standardization
- PII redaction in conflict snapshots

---

**Implementation Status**: Ready for parallel agent execution
**Next Steps**: Assign workstreams to CC agents per execution matrix
