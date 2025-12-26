"""
Asset data audit and lineage tracking endpoints.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.context import RequestContext, get_current_context
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db

# REMOVED: Data import models
# from app.models.data_import.core import RawImportRecord
from app.repositories.asset_repository import AssetRepository

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


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

        # REMOVED: Data import functionality - RawImportRecord model was removed
        # This endpoint is no longer functional as it depends on data import models
        return {
            "asset_id": asset_id,
            "asset_name": asset.name,
            "message": "Data audit functionality is no longer available - data import models were removed",
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Data audit failed for asset {asset_id}: {e}", asset_id=asset_id, e=e
            )
        )
        raise HTTPException(status_code=500, detail=f"Data audit failed: {str(e)}")
