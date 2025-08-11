"""
Asset data audit and lineage tracking endpoints.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.context import RequestContext, get_current_context
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db
from app.models.data_import.core import RawImportRecord
from app.repositories.asset_repository import AssetRepository

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Asset Audit"])


@router.get("/data-audit/{asset_id}")
async def get_asset_data_audit(
    asset_id: str,
    context: RequestContext = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    """
    Get data audit trail for an asset using existing linkage.
    Shows raw_data -> cleansed_data -> final asset transformation.
    """
    try:
        # Get asset
        asset_repo = AssetRepository(context)
        asset = await asset_repo.get_by_id(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        # Find linked raw import record using asset_id
        from sqlalchemy import select

        from app.core.database import get_async_db_session

        async with get_async_db_session() as session:
            result = await session.execute(
                select(RawImportRecord)
                .where(RawImportRecord.asset_id == asset.id)
                .where(RawImportRecord.client_account_id == context.client_account_id)
            )
            raw_record = result.scalar_one_or_none()

        if not raw_record:
            return {
                "asset_id": asset_id,
                "asset_name": asset.name,
                "message": "No raw import record linked to this asset",
                "raw_data": None,
                "cleansed_data": None,
                "final_asset": {
                    "name": asset.name,
                    "asset_type": asset.asset_type,
                    "environment": asset.environment,
                    "hostname": asset.hostname,
                    "operating_system": asset.operating_system,
                },
            }

        # Compare name fields specifically
        raw_name_fields = {
            "App_Name": raw_record.raw_data.get("App_Name"),
            "app_name": raw_record.raw_data.get("app_name"),
            "name": raw_record.raw_data.get("name"),
            "asset_name": raw_record.raw_data.get("asset_name"),
            "hostname": raw_record.raw_data.get("hostname"),
            "application_name": raw_record.raw_data.get("application_name"),
        }

        cleansed_name_fields = (
            {}
            if not raw_record.cleansed_data
            else {
                "App_Name": raw_record.cleansed_data.get("App_Name"),
                "app_name": raw_record.cleansed_data.get("app_name"),
                "name": raw_record.cleansed_data.get("name"),
                "asset_name": raw_record.cleansed_data.get("asset_name"),
                "hostname": raw_record.cleansed_data.get("hostname"),
                "application_name": raw_record.cleansed_data.get("application_name"),
            }
        )

        return {
            "asset_id": asset_id,
            "row_number": raw_record.row_number,
            "data_import_id": str(raw_record.data_import_id),
            "is_valid": raw_record.is_valid,
            "is_processed": raw_record.is_processed,
            "validation_errors": raw_record.validation_errors,
            "processing_notes": raw_record.processing_notes,
            "name_field_analysis": {
                "raw_name_fields": {
                    k: v for k, v in raw_name_fields.items() if v is not None
                },
                "cleansed_name_fields": {
                    k: v for k, v in cleansed_name_fields.items() if v is not None
                },
                "final_asset_name": asset.name,
                "name_transformation_issue": (
                    len([v for v in raw_name_fields.values() if v]) > 0
                    and (not asset.name or asset.name.startswith("Asset-"))
                ),
            },
            "raw_data": raw_record.raw_data,
            "cleansed_data": raw_record.cleansed_data,
            "final_asset": {
                "name": asset.name,
                "asset_type": asset.asset_type,
                "environment": asset.environment,
                "hostname": asset.hostname,
                "operating_system": asset.operating_system,
                "application_name": asset.application_name,
                "cpu_cores": asset.cpu_cores,
                "memory_gb": asset.memory_gb,
                "storage_gb": asset.storage_gb,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Data audit failed for asset {asset_id}: {e}", asset_id=asset_id, e=e
            )
        )
        raise HTTPException(status_code=500, detail=f"Data audit failed: {str(e)}")
