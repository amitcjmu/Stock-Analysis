"""
Asset analysis and overview endpoints.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.repositories.asset_repository import AssetRepository

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("/analysis/overview", response_model=Dict[str, Any])
async def get_asset_overview(
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    repo = AssetRepository(db, context.client_account_id)
    return await repo.get_asset_overview()


@router.get("/analysis/by-type", response_model=Dict[str, int])
async def get_assets_by_type(
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    repo = AssetRepository(db, context.client_account_id)
    return await repo.get_assets_by_type()


@router.get("/analysis/by-status", response_model=Dict[str, int])
async def get_assets_by_status(
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    repo = AssetRepository(db, context.client_account_id)
    return await repo.get_assets_by_status()
