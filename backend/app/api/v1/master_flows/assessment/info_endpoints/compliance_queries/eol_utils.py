"""
EOL (End-of-Life) utility functions for compliance queries.

Helper functions for querying and processing EOL status data.
Uses agent-enriched data from AssetEOLAssessment records when available,
with fallback to EOLLifecycleService for unassessed technologies.
"""

import logging
import re
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def _get_eol_status_for_tech_stack(
    tech_stack: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Get EOL status for technologies in a stack (legacy fallback).

    NOTE: Prefer _get_eol_status_for_assets() which uses agent-enriched data
    and Asset.asset_type for proper classification instead of regex heuristics.

    This function uses regex heuristics to guess product_type, which is less
    accurate than using the actual asset_type from the Asset model.

    Args:
        tech_stack: Dict of technology -> version pairs

    Returns:
        List of EOL status dicts for each technology
    """
    from app.services.eol_lifecycle.eol_lifecycle_service import get_eol_service

    eol_results: List[Dict[str, Any]] = []

    try:
        eol_service = await get_eol_service()

        for tech, version in tech_stack.items():
            if not version or version == "unknown":
                continue

            try:
                # Determine product type based on technology name (legacy heuristic)
                # Use word boundaries to prevent false matches
                tech_lower = tech.lower()
                if any(
                    re.search(rf"\b{os_name}\b", tech_lower)
                    for os_name in [
                        "windows",
                        "linux",
                        "rhel",
                        "ubuntu",
                        "debian",
                        "centos",
                    ]
                ):
                    product_type = "os"
                elif any(
                    re.search(rf"\b{db_name}\b", tech_lower)
                    for db_name in [
                        "sql server",
                        "sqlserver",
                        "oracle",
                        "postgres",
                        "postgresql",
                        "mysql",
                        "mongodb",
                        "mongo",
                        "redis",
                        "mariadb",
                    ]
                ):
                    product_type = "database"
                else:
                    product_type = "runtime"

                eol_status = await eol_service.get_eol_status(
                    tech, version, product_type
                )

                eol_results.append(
                    {
                        "product": eol_status.product,
                        "version": eol_status.version,
                        "status": eol_status.status.value,
                        "eol_date": (
                            eol_status.eol_date.isoformat()
                            if eol_status.eol_date
                            else None
                        ),
                        "support_type": eol_status.support_type.value,
                        "source": eol_status.source.value,
                        "confidence": eol_status.confidence,
                    }
                )
            except Exception as e:
                logger.debug(f"Failed to get EOL status for {tech} {version}: {e}")
                continue

    except Exception as e:
        logger.warning(f"Failed to initialize EOL service: {e}")

    return eol_results


def _parse_asset_ids(asset_ids: List[str]) -> List[UUID]:
    """Convert string IDs to UUIDs, filtering out invalid ones."""
    valid_ids = []
    for aid in asset_ids:
        if aid:
            try:
                valid_ids.append(UUID(aid))
            except ValueError:
                logger.debug(f"Invalid asset ID format: {aid}")
    return valid_ids


def _map_risk_level_to_status(risk_level: Optional[str]) -> str:
    """Map EOL risk_level to API status for consistency."""
    if risk_level == "critical":
        return "eol_expired"
    elif risk_level in ("high", "medium"):
        return "eol_soon"
    return "active"


def _get_product_type_from_asset_type(asset_type: Optional[str]) -> str:
    """Derive product_type from Asset.asset_type (NOT regex heuristics)."""
    asset_type_lower = (asset_type or "").lower()
    if asset_type_lower == "database":
        return "database"
    elif asset_type_lower in ("server", "virtual_machine", "vm"):
        return "os"
    return "runtime"


async def _collect_agent_eol_assessments(
    db: AsyncSession,
    valid_asset_ids: List[UUID],
    client_account_id: int,
    engagement_id: UUID,
) -> tuple[List[Dict[str, Any]], set[str]]:
    """Query existing AssetEOLAssessment records (agent-populated data)."""
    from app.models.asset.specialized import AssetEOLAssessment

    eol_results: List[Dict[str, Any]] = []
    assessed_components: set[str] = set()

    eol_stmt = select(AssetEOLAssessment).where(
        AssetEOLAssessment.asset_id.in_(valid_asset_ids),
        AssetEOLAssessment.client_account_id == client_account_id,
        AssetEOLAssessment.engagement_id == engagement_id,
    )
    eol_result = await db.execute(eol_stmt)
    existing_assessments = eol_result.scalars().all()

    for assessment in existing_assessments:
        component_key = f"{assessment.technology_component}".lower()
        assessed_components.add(component_key)

        eol_results.append(
            {
                "product": assessment.technology_component,
                "version": "assessed",
                "status": _map_risk_level_to_status(assessment.eol_risk_level),
                "eol_date": (
                    assessment.eol_date.isoformat() if assessment.eol_date else None
                ),
                "support_type": "agent_assessed",
                "source": "agent_enrichment",
                "confidence": 0.95,
                "asset_id": str(assessment.asset_id),
            }
        )

    if existing_assessments:
        logger.info(
            f"Found {len(existing_assessments)} existing EOL assessments from agents"
        )

    return eol_results, assessed_components


async def _collect_components_to_check(
    db: AsyncSession,
    valid_asset_ids: List[UUID],
    client_account_id: int,
    engagement_id: UUID,
    assessed_components: set[str],
) -> Dict[str, Dict[str, Any]]:
    """For assets without EOL assessments, collect components needing EOL lookup."""
    from app.models.asset import Asset

    components_to_check: Dict[str, Dict[str, Any]] = {}

    asset_stmt = select(Asset).where(
        Asset.id.in_(valid_asset_ids),
        Asset.client_account_id == client_account_id,
        Asset.engagement_id == engagement_id,
        Asset.deleted_at.is_(None),
    )
    asset_result = await db.execute(asset_stmt)
    assets = asset_result.scalars().all()

    for asset in assets:
        product_type = _get_product_type_from_asset_type(asset.asset_type)

        # Check OS version if available
        if asset.operating_system and asset.os_version:
            os_key = f"{asset.operating_system}:{asset.os_version}".lower()
            if os_key not in assessed_components:
                components_to_check[os_key] = {
                    "tech": asset.operating_system,
                    "version": asset.os_version,
                    "product_type": "os",
                }

        # Check technology_stack if structured
        tech_stack = asset.technology_stack
        if tech_stack and isinstance(tech_stack, dict):
            for tech, version in tech_stack.items():
                if version and version != "unknown":
                    tech_key = f"{tech}:{version}".lower()
                    if tech_key not in assessed_components:
                        components_to_check[tech_key] = {
                            "tech": tech,
                            "version": version,
                            "product_type": product_type,
                        }

    return components_to_check


async def _query_eol_service_for_components(
    components_to_check: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Query EOL service for components not already assessed by agents."""
    from app.services.eol_lifecycle.eol_lifecycle_service import get_eol_service

    eol_results: List[Dict[str, Any]] = []

    if not components_to_check:
        return eol_results

    try:
        eol_service = await get_eol_service()

        for comp_data in components_to_check.values():
            try:
                eol_status = await eol_service.get_eol_status(
                    comp_data["tech"],
                    comp_data["version"],
                    comp_data["product_type"],
                )

                eol_results.append(
                    {
                        "product": eol_status.product,
                        "version": eol_status.version,
                        "status": eol_status.status.value,
                        "eol_date": (
                            eol_status.eol_date.isoformat()
                            if eol_status.eol_date
                            else None
                        ),
                        "support_type": eol_status.support_type.value,
                        "source": eol_status.source.value,
                        "confidence": eol_status.confidence,
                    }
                )
            except Exception as e:
                logger.debug(
                    f"Failed to get EOL status for {comp_data['tech']} "
                    f"{comp_data['version']}: {e}"
                )

    except Exception as e:
        logger.warning(f"Failed to initialize EOL service: {e}")

    return eol_results


async def _get_eol_status_for_assets(
    db: AsyncSession,
    asset_ids: List[str],
    client_account_id: int,
    engagement_id: UUID,
) -> List[Dict[str, Any]]:
    """
    Get EOL status for assets using existing agent-populated data.

    This is the preferred method over _get_eol_status_for_tech_stack as it:
    1. Uses AssetEOLAssessment records populated by discovery/enrichment agents
    2. Uses Asset.asset_type for proper classification (not regex heuristics)
    3. Falls back to EOLLifecycleService only for unassessed technologies

    Args:
        db: Async database session
        asset_ids: List of asset UUIDs to check
        client_account_id: Client account for tenant scoping
        engagement_id: Engagement ID for tenant scoping

    Returns:
        List of EOL status dicts for each technology component
    """
    try:
        valid_asset_ids = _parse_asset_ids(asset_ids)
        if not valid_asset_ids:
            return []

        # Step 1: Collect agent-populated EOL assessments
        eol_results, assessed_components = await _collect_agent_eol_assessments(
            db, valid_asset_ids, client_account_id, engagement_id
        )

        # Step 2: Collect components needing EOL lookup
        components_to_check = await _collect_components_to_check(
            db, valid_asset_ids, client_account_id, engagement_id, assessed_components
        )

        # Step 3: Query EOL service for remaining components
        service_results = await _query_eol_service_for_components(components_to_check)
        eol_results.extend(service_results)

        return eol_results

    except Exception as e:
        logger.error(f"Failed to get EOL status for assets: {e}", exc_info=True)
        return []
