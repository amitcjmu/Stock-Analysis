"""
Asset Selection Bootstrap Handler

Generates a bootstrap questionnaire for asset selection when a collection flow
enters the ASSET_SELECTION phase without pre-selected assets.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow
from app.models.collection_flow.schemas import CollectionPhase
from app.models.asset import Asset

logger = logging.getLogger(__name__)


async def generate_asset_selection_bootstrap(
    flow: CollectionFlow,
    db: AsyncSession,
    context: RequestContext,
) -> Dict[str, Any]:
    """Generate bootstrap questionnaire for asset selection when no assets exist.

    Args:
        flow: The collection flow instance
        db: Database session
        context: Request context with tenant information

    Returns:
        Dict containing bootstrap questionnaire or status
    """
    try:
        # Check if assets are already selected - could be a stuck flow recovery scenario
        selected_apps = (
            flow.collection_config.get("selected_application_ids", [])
            if flow.collection_config
            else []
        )
        if selected_apps:
            logger.info(
                f"Flow {flow.flow_id} already has {len(selected_apps)} selected assets"
            )
            # Check if bootstrap was generated but might be missing (stuck flow case)
            if not flow.collection_config.get(
                "bootstrap_questionnaire_generated"
            ) or not flow.collection_config.get("bootstrap_questionnaire"):
                logger.warning(
                    f"Flow {flow.flow_id} has selected assets but missing bootstrap "
                    f"questionnaire - possible stuck flow recovery"
                )
                # Continue with bootstrap generation for recovery
            else:
                return {
                    "status": "assets_already_selected",
                    "count": len(selected_apps),
                }

        # Check if bootstrap was already generated
        if flow.collection_config and flow.collection_config.get(
            "bootstrap_questionnaire_generated"
        ):
            logger.info(
                f"Bootstrap questionnaire already generated for flow {flow.flow_id}"
            )
            return {"status": "bootstrap_already_generated"}

        # Fetch available applications/assets from the engagement
        available_assets = await get_available_assets(db, context)

        if not available_assets:
            logger.warning(
                f"No assets available for engagement {context.engagement_id}"
            )
            return {
                "status": "no_assets_available",
                "message": "No applications found. Please run Discovery flow first or add applications manually.",
            }

        # Generate bootstrap questionnaire structure
        questionnaire = {
            "questionnaire_id": "bootstrap_asset_selection",
            "title": "Select Applications for Collection",
            "description": "Choose which applications you want to collect detailed information about.",
            "type": "asset_selection",
            "phase": "asset_selection",
            "required": True,
            "fields": [
                {
                    "id": "selected_assets",
                    "name": "Select Applications",
                    "type": "multiselect",
                    "required": True,
                    "description": "Choose one or more applications to analyze for data gaps",
                    "options": [
                        {
                            "value": f"{asset['name']} (ID: {asset['id']})",
                            "label": f"{asset['name']} - {asset.get('environment', 'Unknown')} Environment",
                            "metadata": {
                                "asset_id": str(asset["id"]),
                                "environment": asset.get("environment", "unknown"),
                                "type": asset.get("type", "unknown"),
                            },
                        }
                        for asset in available_assets
                    ],
                    "validation": {
                        "min_selections": 1,
                        "max_selections": len(available_assets),
                    },
                }
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "flow_id": str(flow.flow_id),
            "engagement_id": context.engagement_id,
        }

        # Mark bootstrap as generated in flow config
        if not flow.collection_config:
            flow.collection_config = {}

        flow.collection_config["bootstrap_questionnaire_generated"] = True
        flow.collection_config["bootstrap_generated_at"] = datetime.now(
            timezone.utc
        ).isoformat()
        flow.collection_config["available_asset_count"] = len(available_assets)

        # Bug #997 Fix: Store available asset metadata for later reference
        # This allows preserving metadata when assets are selected
        flow.collection_config["available_asset_metadata"] = {
            asset["id"]: {
                "name": asset.get("name"),
                "environment": asset.get("environment"),
                "type": asset.get("type"),
                "criticality": asset.get("criticality"),
            }
            for asset in available_assets
        }

        # Store questionnaire in flow config for retrieval
        flow.collection_config["bootstrap_questionnaire"] = questionnaire

        # CRITICAL: Tell SQLAlchemy the JSONB column changed (prevents mutation tracking issues)
        # Bug #1102: Without flag_modified(), in-place dict modifications don't trigger DB updates
        # This caused bootstrap questionnaires to never persist, regenerating on every request
        flag_modified(flow, "collection_config")

        await db.flush()
        await db.commit()  # Commit changes to database to persist questionnaire

        logger.info(
            f"Generated bootstrap questionnaire for flow {flow.flow_id} with {len(available_assets)} available assets"
        )

        return {
            "status": "bootstrap_generated",
            "questionnaire": questionnaire,
            "available_assets": len(available_assets),
        }

    except Exception as e:
        logger.error(
            f"Failed to generate asset selection bootstrap for flow {flow.flow_id}: {e}"
        )
        return {"status": "error", "error": str(e)}


async def get_available_assets(
    db: AsyncSession, context: RequestContext
) -> List[Dict[str, Any]]:
    """Fetch available assets/applications for the engagement.

    Args:
        db: Database session
        context: Request context with tenant information

    Returns:
        List of asset dictionaries
    """
    try:
        # Query assets for the engagement with tenant scoping
        result = await db.execute(
            select(Asset)
            .where(Asset.client_account_id == context.client_account_id)
            .where(Asset.engagement_id == context.engagement_id)
            # Note: Asset model doesn't have is_deleted field, using status field instead
            .where(Asset.status != "decommissioned")  # Filter out decommissioned assets
            .order_by(Asset.name)
        )

        assets = result.scalars().all()

        # Convert to list of dicts for easier processing
        asset_list = []
        for asset in assets:
            asset_dict = {
                "id": str(asset.id),
                "name": asset.name or f"Asset-{str(asset.id)[:8]}",
                "environment": getattr(asset, "environment", "unknown"),
                "type": getattr(asset, "application_type", "unknown"),
                "criticality": getattr(asset, "criticality", "medium"),
                "created_at": (
                    asset.created_at.isoformat() if asset.created_at else None
                ),
            }
            asset_list.append(asset_dict)

        logger.info(
            f"Found {len(asset_list)} available assets for engagement {context.engagement_id}"
        )

        return asset_list

    except Exception as e:
        logger.error(f"Failed to fetch available assets: {e}")
        return []


async def should_generate_bootstrap(
    flow: CollectionFlow,
) -> bool:
    """Check if bootstrap questionnaire should be generated.

    Args:
        flow: The collection flow instance

    Returns:
        True if bootstrap should be generated, False otherwise
    """
    # Only generate for ASSET_SELECTION phase
    if flow.current_phase != CollectionPhase.ASSET_SELECTION.value:
        return False

    # Check if assets are already selected
    selected_apps = flow.collection_config.get("selected_application_ids", [])
    if selected_apps:
        return False

    # Check if bootstrap was already generated
    if flow.collection_config.get("bootstrap_questionnaire_generated"):
        return False

    return True


async def handle_asset_selection_preparation(
    flow_id: str,
    db: AsyncSession,
    context: RequestContext,
) -> Dict[str, Any]:
    """Pre-handler for asset_selection phase to generate bootstrap if needed.

    This function is called as a pre_handler when entering the asset_selection phase.

    Args:
        flow_id: The collection flow ID
        db: Database session
        context: Request context

    Returns:
        Handler result dictionary
    """
    try:
        # Fetch the flow with tenant scoping
        result = await db.execute(
            select(CollectionFlow)
            .where(CollectionFlow.flow_id == flow_id)
            .where(CollectionFlow.client_account_id == context.client_account_id)
            .where(CollectionFlow.engagement_id == context.engagement_id)
        )

        flow = result.scalar_one_or_none()
        if not flow:
            logger.error(f"Collection flow {flow_id} not found")
            return {"status": "error", "error": "Flow not found"}

        # Check if bootstrap should be generated
        if await should_generate_bootstrap(flow):
            bootstrap_result = await generate_asset_selection_bootstrap(
                flow, db, context
            )

            if bootstrap_result.get("status") == "bootstrap_generated":
                await db.commit()
                logger.info(f"Asset selection bootstrap generated for flow {flow_id}")

            return bootstrap_result

        return {"status": "skip", "reason": "Bootstrap not needed"}

    except Exception as e:
        logger.error(f"Asset selection preparation failed for flow {flow_id}: {e}")
        return {"status": "error", "error": str(e)}
