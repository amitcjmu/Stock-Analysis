"""
AssessmentApplicationResolver Service

Provides core business logic for resolving assets to canonical applications
and calculating enrichment/readiness metadata for Assessment flow initialization.

Per ADR-027 and Phase 1 Day 5 requirements.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.canonical_applications import (
    CanonicalApplication,
    CollectionFlowApplication,
)
from app.models.asset_resilience import (
    AssetComplianceFlags,
    AssetLicenses,
    AssetVulnerabilities,
    AssetResilience,
)
from app.models.asset_agnostic.asset_field_conflicts import AssetFieldConflict
from app.models.asset import AssetDependency
from app.models.vendor_products_catalog import AssetProductLinks
from app.schemas.assessment_flow import (
    ApplicationAssetGroup,
    AssetDetail,
    EnrichmentStatus,
    ReadinessSummary,
)


class AssessmentApplicationResolver:
    """
    Service for resolving assets to canonical applications in Assessment flow.
    Provides rich application-centric view with asset groupings and enrichment metadata.

    This service is the core business logic for:
    - Resolving asset IDs to canonical applications
    - Grouping multiple assets under same application
    - Calculating enrichment status across 7 enrichment tables
    - Computing readiness summaries for assessment dashboard

    Multi-Tenant Scoping:
    ALL database queries MUST include tenant scoping with client_account_id
    and engagement_id per CLAUDE.md requirements.
    """

    def __init__(self, db: AsyncSession, client_account_id: UUID, engagement_id: UUID):
        """
        Initialize resolver with database session and tenant context.

        Args:
            db: Async SQLAlchemy session
            client_account_id: Multi-tenant client account UUID
            engagement_id: Multi-tenant engagement UUID
        """
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def resolve_assets_to_applications(
        self,
        asset_ids: List[UUID],
        collection_flow_id: Optional[UUID] = None,
    ) -> List[ApplicationAssetGroup]:
        """
        Resolve asset IDs to canonical applications with grouping.

        This is the CORE method that transforms flat asset list into application-centric view.

        Query strategy:
        1. Join assets → collection_flow_applications → canonical_applications
        2. Group by canonical_application_id (or asset_id for unmapped)
        3. Aggregate asset types, readiness counts
        4. Return structured ApplicationAssetGroup objects

        Args:
            asset_ids: List of asset UUIDs from assessment flow
            collection_flow_id: Optional collection flow for scoping

        Returns:
            List of ApplicationAssetGroup objects with:
            - canonical_application_id (or None for unmapped)
            - canonical_application_name
            - asset_ids (all assets belonging to this app)
            - asset_types (distinct types: server, database, etc.)
            - readiness_summary (how many assets ready/not_ready)
        """
        if not asset_ids:
            return []

        # Build query with LEFT JOINs to handle unmapped assets
        query = (
            select(
                Asset.id.label("asset_id"),
                Asset.asset_name,
                Asset.name,
                Asset.asset_type,
                Asset.environment,
                Asset.assessment_readiness,
                Asset.assessment_readiness_score,
                CollectionFlowApplication.canonical_application_id,
                CollectionFlowApplication.deduplication_method,
                CollectionFlowApplication.match_confidence,
                CanonicalApplication.canonical_name,
                CanonicalApplication.application_type,
                CanonicalApplication.technology_stack,
            )
            .select_from(Asset)
            .outerjoin(
                CollectionFlowApplication,
                Asset.id == CollectionFlowApplication.asset_id,
            )
            .outerjoin(
                CanonicalApplication,
                CollectionFlowApplication.canonical_application_id
                == CanonicalApplication.id,
            )
            .where(
                Asset.id.in_(asset_ids),
                Asset.client_account_id == self.client_account_id,
                Asset.engagement_id == self.engagement_id,
            )
        )

        # Optional: Filter by collection flow if provided
        if collection_flow_id:
            query = query.where(
                CollectionFlowApplication.collection_flow_id == collection_flow_id
            )

        result = await self.db.execute(query)
        rows = result.all()

        # Group assets by canonical application
        app_groups: Dict[str, Dict[str, Any]] = {}

        for row in rows:
            # Use canonical_application_id as key, fallback to "unmapped-{asset_id}" for unmapped
            if row.canonical_application_id:
                app_key = str(row.canonical_application_id)
            else:
                app_key = f"unmapped-{row.asset_id}"

            if app_key not in app_groups:
                # Initialize group
                app_groups[app_key] = {
                    "canonical_application_id": row.canonical_application_id,
                    "canonical_application_name": (
                        row.canonical_name
                        or row.asset_name
                        or row.name
                        or "Unknown Application"
                    ),
                    "assets": [],
                    "asset_types": set(),
                    "readiness": {"ready": 0, "not_ready": 0, "in_progress": 0},
                    "readiness_scores": [],  # Track scores for avg calculation
                    "seen_asset_ids": set(),  # Track seen assets to prevent duplicates
                }

            # Skip duplicate assets (can occur when asset has multiple collection_flow_applications entries)
            if row.asset_id in app_groups[app_key]["seen_asset_ids"]:
                continue

            # Mark this asset as seen for this group
            app_groups[app_key]["seen_asset_ids"].add(row.asset_id)

            # Add asset to group
            app_groups[app_key]["assets"].append(
                {
                    "asset_id": row.asset_id,
                    "asset_name": row.asset_name or row.name,
                    "asset_type": row.asset_type,
                    "environment": row.environment,
                    "assessment_readiness": row.assessment_readiness,
                    "assessment_readiness_score": row.assessment_readiness_score,
                    "match_confidence": row.match_confidence,
                }
            )

            # Track asset type
            if row.asset_type:
                app_groups[app_key]["asset_types"].add(row.asset_type)

            # Track readiness
            readiness = row.assessment_readiness or "not_ready"
            if readiness in ["ready", "not_ready", "in_progress"]:
                app_groups[app_key]["readiness"][readiness] += 1
            else:
                # Default unknown readiness to not_ready
                app_groups[app_key]["readiness"]["not_ready"] += 1

            # Track readiness score for average calculation
            if row.assessment_readiness_score is not None:
                try:
                    score = float(row.assessment_readiness_score)
                    # Validate score is in range [0, 1]
                    if 0.0 <= score <= 1.0:
                        app_groups[app_key]["readiness_scores"].append(score)
                except (ValueError, TypeError):
                    # Skip invalid scores
                    pass

        # Convert to ApplicationAssetGroup objects
        groups = []
        for group_data in app_groups.values():
            # Calculate average completeness score for this application group
            scores = group_data["readiness_scores"]
            avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

            # Build readiness_summary with avg_completeness_score
            readiness_summary = {
                "ready": group_data["readiness"]["ready"],
                "not_ready": group_data["readiness"]["not_ready"],
                "in_progress": group_data["readiness"]["in_progress"],
                "avg_completeness_score": avg_score,
            }

            # Build detailed asset list for UI display
            asset_details = [
                AssetDetail(
                    asset_id=a["asset_id"],
                    asset_name=a["asset_name"] or "Unknown Asset",
                    asset_type=a.get("asset_type"),
                    environment=a.get("environment"),
                    assessment_readiness=a.get("assessment_readiness") or "not_ready",
                    assessment_readiness_score=a.get("assessment_readiness_score"),
                )
                for a in group_data["assets"]
            ]

            groups.append(
                ApplicationAssetGroup(
                    canonical_application_id=group_data["canonical_application_id"],
                    canonical_application_name=group_data["canonical_application_name"],
                    asset_ids=[a["asset_id"] for a in group_data["assets"]],
                    assets=asset_details,
                    asset_count=len(group_data["assets"]),
                    asset_types=sorted(list(group_data["asset_types"])),
                    readiness_summary=readiness_summary,
                )
            )

        # Sort by application name for consistent ordering
        groups.sort(key=lambda g: g.canonical_application_name)

        return groups

    async def calculate_enrichment_status(
        self, asset_ids: List[UUID]
    ) -> EnrichmentStatus:
        """
        Calculate how many assets have data in each enrichment table.

        Query strategy:
        1. For each of 7 enrichment tables:
           - AssetComplianceFlags
           - AssetLicenses
           - AssetVulnerabilities
           - AssetResilience
           - AssetDependency
           - AssetProductLinks
           - AssetFieldConflict
        2. Count DISTINCT asset_id WHERE asset_id IN (asset_ids)
        3. Return EnrichmentStatus with counts

        Args:
            asset_ids: List of asset UUIDs

        Returns:
            EnrichmentStatus object with counts for each table
        """
        if not asset_ids:
            return EnrichmentStatus()

        enrichment_counts = {}

        # Define enrichment tables with their model classes
        # Note: We're checking the models that have tenant scoping where applicable
        enrichment_tables = [
            ("compliance_flags", AssetComplianceFlags),
            ("licenses", AssetLicenses),
            ("vulnerabilities", AssetVulnerabilities),
            ("resilience", AssetResilience),
            ("dependencies", AssetDependency),
            ("product_links", AssetProductLinks),
            ("field_conflicts", AssetFieldConflict),
        ]

        for field_name, model_class in enrichment_tables:
            # Build query with multi-tenant scoping where applicable
            query = select(func.count(func.distinct(model_class.asset_id))).where(
                model_class.asset_id.in_(asset_ids)
            )

            # SECURITY: Add tenant scoping for ALL models that have these fields
            # This prevents data leakage between tenants
            if hasattr(model_class, "client_account_id"):
                query = query.where(
                    model_class.client_account_id == self.client_account_id
                )
            if hasattr(model_class, "engagement_id"):
                query = query.where(model_class.engagement_id == self.engagement_id)

            result = await self.db.execute(query)
            count = result.scalar() or 0
            enrichment_counts[field_name] = count

        return EnrichmentStatus(**enrichment_counts)

    async def calculate_readiness_summary(
        self, asset_ids: List[UUID]
    ) -> ReadinessSummary:
        """
        Calculate assessment readiness summary for selected assets.

        Query strategy:
        1. SELECT assessment_readiness, assessment_readiness_score FROM assets
        2. Aggregate counts by readiness status (ready/not_ready/in_progress)
        3. Calculate average completeness score

        Args:
            asset_ids: List of asset UUIDs

        Returns:
            ReadinessSummary with totals, counts, and average score
        """
        if not asset_ids:
            return ReadinessSummary()

        # Query assets with multi-tenant scoping
        query = select(
            Asset.assessment_readiness, Asset.assessment_readiness_score
        ).where(
            Asset.id.in_(asset_ids),
            Asset.client_account_id == self.client_account_id,
            Asset.engagement_id == self.engagement_id,
        )

        result = await self.db.execute(query)
        rows = result.all()

        if not rows:
            return ReadinessSummary()

        # Aggregate readiness counts
        readiness_counts = {"ready": 0, "not_ready": 0, "in_progress": 0}
        scores = []

        for row in rows:
            # Handle readiness status
            readiness = row.assessment_readiness or "not_ready"
            if readiness in readiness_counts:
                readiness_counts[readiness] += 1
            else:
                # Unknown readiness defaults to not_ready
                readiness_counts["not_ready"] += 1

            # Collect scores for average calculation
            if row.assessment_readiness_score is not None:
                try:
                    score = float(row.assessment_readiness_score)
                    # Validate score is in range [0, 1]
                    if 0.0 <= score <= 1.0:
                        scores.append(score)
                except (ValueError, TypeError):
                    # Skip invalid scores
                    pass

        # Calculate average score (avoid division by zero)
        avg_score = 0.0
        if scores:
            avg_score = sum(scores) / len(scores)

        return ReadinessSummary(
            total_assets=len(rows),
            ready=readiness_counts["ready"],
            not_ready=readiness_counts["not_ready"],
            in_progress=readiness_counts["in_progress"],
            avg_completeness_score=round(avg_score, 2),
        )
