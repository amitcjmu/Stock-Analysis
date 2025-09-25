"""
Collection Flow Bulk Import Handler
Handles bulk data import for Collection flows through CSV upload.
Processes each row through the Collection questionnaire system.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.rbac_utils import COLLECTION_CREATE_ROLES, require_role
from app.models import User
from app.models.collection_flow import (
    CollectionFlow,
    CollectionFlowStatus,
    CollectionPhase,
)
from app.models.collection_questionnaire import CollectionQuestionnaireResponse
from app.api.v1.endpoints.collection_bulk_import_assets import create_or_update_asset

# Import removed - unused in this module

logger = logging.getLogger(__name__)


async def _validate_collection_flow_for_import(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> CollectionFlow:
    """Validate that the collection flow exists and is in correct state for import."""
    flow_result = await db.execute(
        select(CollectionFlow).where(
            CollectionFlow.flow_id == uuid.UUID(flow_id),
            CollectionFlow.engagement_id == context.engagement_id,
        )
    )
    collection_flow = flow_result.scalar_one_or_none()

    if not collection_flow:
        raise HTTPException(
            status_code=404, detail=f"Collection flow {flow_id} not found"
        )

    # Check flow is in a state that allows bulk import
    allowed_statuses = [
        CollectionFlowStatus.INITIALIZED.value,
        CollectionFlowStatus.ASSET_SELECTION.value,
        CollectionFlowStatus.GAP_ANALYSIS.value,
        CollectionFlowStatus.MANUAL_COLLECTION.value,
    ]

    if collection_flow.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Collection flow is in {collection_flow.status} state. "
            f"Bulk import is only allowed in: {', '.join(allowed_statuses)}",
        )

    return collection_flow


async def _process_csv_rows(
    csv_data: List[Dict[str, Any]],
    asset_type: str,
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> tuple[int, List[Dict], List[Any]]:
    """Process CSV rows and create assets."""
    processed_count = 0
    errors = []
    created_assets = []

    for row_idx, row_data in enumerate(csv_data):
        try:
            # Map CSV row to questionnaire format
            questionnaire_data = map_csv_to_questionnaire(row_data, asset_type)

            # Create/update asset based on type
            asset = await create_or_update_asset(
                asset_type=asset_type,
                data=questionnaire_data,
                db=db,
                context=context,
            )

            if asset:
                created_assets.append(asset)

                # Store questionnaire response for this asset
                response = CollectionQuestionnaireResponse(
                    id=uuid.uuid4(),
                    flow_id=uuid.UUID(flow_id),
                    questionnaire_id=f"bulk_import_{asset_type}",
                    asset_id=asset.id,
                    asset_type=asset_type,
                    responses=questionnaire_data,
                    submitted_by=current_user.id,
                    submitted_at=datetime.now(timezone.utc),
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                )
                db.add(response)
                processed_count += 1

        except Exception as e:
            errors.append({"row": row_idx + 1, "error": str(e), "data": row_data})
            logger.error(f"Error processing row {row_idx + 1}: {e}")

    return processed_count, errors, created_assets


def _update_flow_after_import(
    collection_flow: CollectionFlow,
    asset_type: str,
    processed_count: int,
    created_assets: List[Any],
    current_user: User,
):
    """Update flow configuration and status after successful import."""
    if processed_count == 0:
        return

    # Update flow configuration
    if not collection_flow.collection_config:
        collection_flow.collection_config = {}

    collection_flow.collection_config["bulk_import"] = {
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "asset_type": asset_type,
        "asset_count": processed_count,
        "imported_by": str(current_user.id),
    }

    # Add imported asset IDs to flow configuration
    if "selected_assets" not in collection_flow.collection_config:
        collection_flow.collection_config["selected_assets"] = {}

    asset_key = f"{asset_type}_ids"
    if asset_key not in collection_flow.collection_config["selected_assets"]:
        collection_flow.collection_config["selected_assets"][asset_key] = []

    collection_flow.collection_config["selected_assets"][asset_key].extend(
        [str(asset.id) for asset in created_assets]
    )

    # Update flow status and phase after successful import
    if collection_flow.status == CollectionFlowStatus.INITIALIZED.value:
        collection_flow.status = CollectionFlowStatus.ASSET_SELECTION.value

    # After successful asset import, set current phase to GAP_ANALYSIS
    collection_flow.current_phase = CollectionPhase.GAP_ANALYSIS.value
    collection_flow.updated_at = datetime.now(timezone.utc)


async def _trigger_gap_analysis_if_needed(
    flow_id: str,
    created_assets: List[Any],
    asset_type: str,
    processed_count: int,
    db: AsyncSession,
    context: RequestContext,
) -> bool:
    """Trigger gap analysis if assets were imported."""
    if processed_count == 0:
        return False

    try:
        # Trigger gap analysis through MFO
        from app.api.v1.endpoints import collection_utils

        gap_result = await collection_utils.trigger_gap_analysis(
            flow_id=flow_id,
            asset_ids=[str(asset.id) for asset in created_assets],
            asset_type=asset_type,
            db=db,
            context=context,
        )
        gap_analysis_triggered = bool(gap_result)
        logger.info(f"Gap analysis triggered for flow {flow_id}: {gap_result}")
        return gap_analysis_triggered

    except Exception as e:
        logger.error(f"Failed to trigger gap analysis: {e}")
        # Don't fail the import if gap analysis fails
        return False


async def process_bulk_import(
    flow_id: str,
    file_path: Optional[str],
    csv_data: Optional[List[Dict[str, Any]]],
    asset_type: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Process bulk CSV import for Collection flow.

    This function orchestrates the bulk import process by:
    1. Validating the Collection flow exists and is in correct state
    2. Processing each row through the Collection questionnaire system
    3. Creating/updating assets in the database
    4. Updating flow configuration and status
    5. Triggering gap analysis for all imported assets

    Args:
        flow_id: The Collection flow ID to import data into
        file_path: Path to the uploaded CSV file (unused - for future compatibility)
        csv_data: CSV data to import
        asset_type: Type of assets being imported
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Dict with import results including processed count and any errors
    """
    require_role(current_user, COLLECTION_CREATE_ROLES, "bulk import collection data")

    try:
        # 1. Validate Collection flow
        collection_flow = await _validate_collection_flow_for_import(
            flow_id, db, context
        )

        # 2. Validate CSV data
        if csv_data is None:
            raise HTTPException(
                status_code=400, detail="csv_data must be provided for bulk import"
            )

        if not csv_data:
            return {
                "success": False,
                "errors": ["No data provided for import"],
                "warnings": [],
            }

        # 3. Process CSV rows and create assets
        processed_count, errors, created_assets = await _process_csv_rows(
            csv_data, asset_type, flow_id, db, current_user, context
        )

        # 4. Update flow configuration and status
        _update_flow_after_import(
            collection_flow, asset_type, processed_count, created_assets, current_user
        )

        await db.commit()

        # 5. Trigger gap analysis
        gap_analysis_triggered = await _trigger_gap_analysis_if_needed(
            flow_id, created_assets, asset_type, processed_count, db, context
        )

        logger.info(
            f"Bulk import completed for flow {flow_id}: "
            f"{processed_count} {asset_type} processed, {len(errors)} errors"
        )

        return {
            "success": True,
            "flow_id": flow_id,
            "asset_type": asset_type,
            "processed_count": processed_count,
            "created_assets": [str(asset.id) for asset in created_assets],
            "errors": errors,
            "gap_analysis_triggered": gap_analysis_triggered,
            "message": f"Successfully imported {processed_count} {asset_type}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk import failed for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk import failed: {str(e)}")


def map_csv_to_questionnaire(
    csv_row: Dict[str, Any], asset_type: str
) -> Dict[str, Any]:
    """Map CSV row data to questionnaire response format.

    This maps the CSV fields to the format expected by the Collection
    questionnaire system for each asset type.
    """
    questionnaire_data = {
        "metadata": {
            "source": "bulk_import",
            "imported_at": datetime.now(timezone.utc).isoformat(),
        }
    }

    if asset_type == "applications":
        questionnaire_data.update(
            {
                "application_name": csv_row.get("Application Name", ""),
                "business_criticality": csv_row.get("Business Criticality", "Medium"),
                "application_owner": csv_row.get("Application Owner", ""),
                "technical_owner": csv_row.get("Technical Owner", ""),
                "description": csv_row.get("Description", ""),
                "technology_stack": (
                    csv_row.get("Technology Stack", "").split(",")
                    if csv_row.get("Technology Stack")
                    else []
                ),
                "deployment_type": csv_row.get("Deployment Type", "On-Premise"),
                "migration_priority": csv_row.get("Migration Priority", "Medium"),
                "dependencies": csv_row.get("Dependencies", ""),
                "compliance_requirements": csv_row.get("Compliance Requirements", ""),
            }
        )
    elif asset_type == "servers":
        questionnaire_data.update(
            {
                "server_name": csv_row.get("Server Name", ""),
                "hostname": csv_row.get("Hostname", ""),
                "ip_address": csv_row.get("IP Address", ""),
                "operating_system": csv_row.get("Operating System", ""),
                "os_version": csv_row.get("OS Version", ""),
                "cpu_cores": csv_row.get("CPU Cores", ""),
                "memory_gb": csv_row.get("Memory (GB)", ""),
                "storage_gb": csv_row.get("Storage (GB)", ""),
                "environment": csv_row.get("Environment", "Production"),
                "virtualization": csv_row.get("Virtualization", "Physical"),
            }
        )
    elif asset_type == "databases":
        questionnaire_data.update(
            {
                "database_name": csv_row.get("Database Name", ""),
                "database_type": csv_row.get("Database Type", ""),
                "version": csv_row.get("Version", ""),
                "size_gb": csv_row.get("Size (GB)", ""),
                "criticality": csv_row.get("Criticality", "Medium"),
                "backup_frequency": csv_row.get("Backup Frequency", ""),
                "recovery_time_objective": csv_row.get("RTO", ""),
                "recovery_point_objective": csv_row.get("RPO", ""),
                "compliance_requirements": csv_row.get("Compliance Requirements", ""),
                "hosted_on_server": csv_row.get("Hosted On Server", ""),
            }
        )
    elif asset_type == "devices":
        questionnaire_data.update(
            {
                "device_name": csv_row.get("Device Name", ""),
                "device_type": csv_row.get("Device Type", ""),
                "manufacturer": csv_row.get("Manufacturer", ""),
                "model": csv_row.get("Model", ""),
                "serial_number": csv_row.get("Serial Number", ""),
                "location": csv_row.get("Location", ""),
                "network_connectivity": csv_row.get("Network Connectivity", ""),
                "management_interface": csv_row.get("Management Interface", ""),
                "criticality": csv_row.get("Criticality", "Medium"),
                "migration_approach": csv_row.get("Migration Approach", ""),
            }
        )

    return questionnaire_data
