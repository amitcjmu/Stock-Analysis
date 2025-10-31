"""
Context building functions for agent questionnaire generation.
Internal helper functions for building agent context and processing data.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from app.core.context import RequestContext
from app.models import Asset
from app.models.asset import AssetDependency
from app.models.collection_flow import CollectionFlow
from app.models.collected_data_inventory import CollectedDataInventory

logger = logging.getLogger(__name__)


def _validate_and_convert_flow_id(flow_id: Union[int, str, UUID]) -> Union[int, UUID]:
    """Validate and convert flow_id to proper type."""
    if isinstance(flow_id, str):
        try:
            return UUID(flow_id)
        except (ValueError, TypeError):
            # If it's not a UUID string, try to convert to int
            try:
                return int(flow_id)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid flow_id format: {flow_id}")
    elif isinstance(flow_id, UUID):
        # Already a UUID, no conversion needed
        return flow_id
    elif isinstance(flow_id, int):
        return flow_id
    else:
        raise ValueError(f"flow_id must be int, str, or UUID, got {type(flow_id)}")


async def _get_flow_with_tenant_scoping(
    db: AsyncSession, flow_id: Union[int, UUID], context: RequestContext
) -> CollectionFlow:
    """Get flow details with tenant scoping."""
    flow_result = await db.execute(
        # SKIP_TENANT_CHECK - Service-level/monitoring query
        select(CollectionFlow).where(
            and_(
                CollectionFlow.id == flow_id,
                CollectionFlow.client_account_id == context.client_account_id,
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
    )
    flow = flow_result.scalar_one_or_none()

    if not flow:
        logger.error(
            f"Flow not found: flow_id={flow_id}, tenant={context.client_account_id}, "
            f"engagement={context.engagement_id}"
        )
        raise ValueError(
            f"Flow not found with id {flow_id} for tenant {context.client_account_id}"
        )

    return flow


async def _get_filtered_assets(
    db: AsyncSession,
    context: RequestContext,
    selected_asset_ids: Optional[list[str]] = None,
) -> List[Asset]:
    """Get assets with optional filtering by selected asset IDs."""
    # SKIP_TENANT_CHECK - Service-level/monitoring query
    assets_query = select(Asset).where(
        Asset.engagement_id == context.engagement_id,
        Asset.client_account_id == context.client_account_id,
    )

    if selected_asset_ids:
        # Filter by selected asset IDs
        try:
            # Convert string IDs to UUIDs if necessary
            selected_uuids = []
            for asset_id in selected_asset_ids:
                if isinstance(asset_id, str):
                    try:
                        selected_uuids.append(UUID(asset_id))
                    except ValueError:
                        logger.warning(f"Invalid asset ID format: {asset_id}")
                        continue
                else:
                    selected_uuids.append(asset_id)

            if selected_uuids:
                assets_query = assets_query.where(Asset.id.in_(selected_uuids))
        except Exception as e:
            logger.error(f"Error filtering assets by selected IDs: {e}")
            # Continue without filtering if there's an error

    assets_result = await db.execute(assets_query)
    return list(assets_result.scalars().all())


async def _process_assets_with_gaps(
    db: AsyncSession,
    assets: List[Asset],
    flow: CollectionFlow,
    context: RequestContext,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Process assets with gap analysis and comprehensive enrichment data."""
    from .gaps import identify_comprehensive_gaps
    from .assets import calculate_completeness
    from .serializers import serialize_asset_for_agent_context

    assets_with_gaps = []
    all_gaps = []

    for asset in assets:
        # Calculate completeness
        completeness = calculate_completeness(asset)

        # Identify comprehensive gaps
        gaps = await identify_comprehensive_gaps(asset, db, context)
        all_gaps.extend(gaps)

        # Serialize asset with ALL enriched data for intelligent cloud migration decisions
        # This includes: core fields, resilience, compliance, vulnerabilities, licenses,
        # EOL assessments, contacts - everything the agent needs for smart questionnaires
        asset_data = serialize_asset_for_agent_context(
            asset=asset,
            completeness=completeness,
            gaps=gaps,
        )

        assets_with_gaps.append(asset_data)

    return assets_with_gaps, all_gaps


async def _get_dependency_summary(db: AsyncSession) -> Dict[str, Any]:
    """Get dependency summary for the context."""
    try:
        # Get total count of relationships
        # SKIP_TENANT_CHECK - Service-level/monitoring query
        total_deps_result = await db.execute(select(AssetDependency))
        total_relationships = len(list(total_deps_result.scalars().all()))

        # Group by dependency type
        # SKIP_TENANT_CHECK - Service-level/monitoring query
        all_deps_result = await db.execute(select(AssetDependency))
        all_deps = list(all_deps_result.scalars().all())

        relationship_types = {}
        for dep in all_deps:
            dep_type = dep.dependency_type or "unknown"
            relationship_types[dep_type] = relationship_types.get(dep_type, 0) + 1

        return {
            "total_relationships": total_relationships,
            "relationship_types": relationship_types,
        }
    except Exception as e:
        logger.error(f"Error getting dependency summary: {e}")
        return {"total_relationships": 0, "relationship_types": {}}


def _build_context_response(
    flow: CollectionFlow,
    assets_with_gaps: List[Dict[str, Any]],
    all_gaps: List[Dict[str, Any]],
    dependency_summary: Dict[str, Any],
    context: RequestContext,
    selected_asset_ids: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """Build the final context response."""
    return {
        "flow_id": str(flow.id),
        "tenant_id": context.client_account_id,
        "engagement_id": context.engagement_id,
        "assets": assets_with_gaps,
        "comprehensive_gaps": all_gaps,
        "dependency_summary": dependency_summary,
        "context_metadata": {
            "total_assets": len(assets_with_gaps),
            "total_gaps": len(all_gaps),
            "selected_asset_ids": selected_asset_ids,
        },
        "import_summary": _get_import_summary_from_flow(flow),
    }


def _get_import_summary_from_flow(flow: CollectionFlow) -> Dict[str, Any]:
    """Extract import summary from flow metadata."""
    if not flow.flow_metadata:
        return {}

    import_summary = flow.flow_metadata.get("import_summary", {})
    if not isinstance(import_summary, dict):
        return {}

    return import_summary


async def _analyze_collected_data_gaps(
    asset: Asset, db: AsyncSession, context: RequestContext
) -> List[Dict[str, Any]]:
    """Analyze gaps in collected data for an asset."""
    gaps = []

    # Get collected data for this asset
    collected_data = await _get_collected_data_for_asset(asset, db, context)

    if not collected_data:
        gaps.append(
            {
                "field": "collected_data",
                "severity": "medium",
                "category": "data_collection",
                "description": "No imported data found for this asset",
                "source": "data_collection_analysis",
            }
        )
        return gaps

    # Analyze data quality
    for data in collected_data:
        if not data.normalized_data:
            continue

        # Check for data normalization issues
        original_fields = set(data.raw_data.keys()) if data.raw_data else set()
        normalized_fields = (
            set(data.normalized_data.keys()) if data.normalized_data else set()
        )

        # Find fields that were lost during normalization
        lost_fields = original_fields - normalized_fields
        for field in lost_fields:
            if field not in ["id", "created_at", "updated_at"]:  # Skip metadata fields
                gaps.append(
                    {
                        "field": field,
                        "severity": "low",
                        "category": "data_normalization",
                        "description": f"Field '{field}' present in imported data but lost during normalization",
                        "source": "data_collection_analysis",
                        "original_value": (
                            data.raw_data.get(field) if data.raw_data else None
                        ),
                    }
                )

    return gaps


async def _check_dependency_gaps(
    asset: Asset, db: AsyncSession
) -> List[Dict[str, Any]]:
    """Check for dependency-related gaps."""
    gaps = []

    # Get dependencies for this asset
    dependencies = await _get_asset_dependencies(asset, db)

    if not dependencies:
        # No dependencies found - this could be a gap
        gaps.append(
            {
                "field": "dependencies",
                "severity": "high",
                "category": "dependency_unknown",
                "description": "No dependency information available - unable to assess impact",
                "6r_impact": ["all"],
                "source": "relationship_analysis",
            }
        )
    else:
        # Check if dependencies have sufficient detail
        for dep in dependencies:
            # AssetDependency doesn't have relationship_metadata, so check description
            if not dep.description or len(dep.description.strip()) < 10:
                gaps.append(
                    {
                        "field": "dependency_detail",
                        "severity": "medium",
                        "category": "dependency_detail",
                        "description": f"Dependency details missing for {dep.dependency_type} relationship",
                        "6r_impact": ["retire", "retain"],
                        "source": "relationship_analysis",
                        "relationship_id": str(dep.id),
                    }
                )

    return gaps


async def _get_collected_data_for_asset(
    asset: Asset, db: AsyncSession, context: RequestContext
) -> List[CollectedDataInventory]:
    """Get collected data for an asset."""
    collected_query = (
        # SKIP_TENANT_CHECK - Service-level/monitoring query
        select(CollectedDataInventory)
        .where(
            and_(
                CollectedDataInventory.client_account_id == context.client_account_id,
                CollectedDataInventory.engagement_id == context.engagement_id,
                CollectedDataInventory.normalized_data["asset_id"].astext
                == str(asset.id),
            )
        )
        .order_by(desc(CollectedDataInventory.collected_at))
        .limit(200)
    )

    collected_result = await db.execute(collected_query)
    return collected_result.scalars().all()


async def _get_asset_dependencies(
    asset: Asset, db: AsyncSession
) -> List[AssetDependency]:
    """Get dependencies for an asset."""
    dependency_query = select(AssetDependency).where(  # SKIP_TENANT_CHECK
        (AssetDependency.asset_id == asset.id)
        | (AssetDependency.depends_on_asset_id == asset.id)
    )
    dependency_result = await db.execute(dependency_query)
    return dependency_result.scalars().all()


def _prioritize_and_sort_gaps(gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prioritize and sort gaps by severity and field name."""
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    gaps.sort(
        key=lambda x: (severity_order.get(x.get("severity", "low"), 3), x.get("field"))
    )
    return gaps
