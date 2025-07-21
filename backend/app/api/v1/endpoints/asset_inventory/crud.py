"""
Asset CRUD operations endpoints.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.asset_schemas import AssetCreate, AssetUpdate, AssetResponse
from app.core.context import get_user_id, get_current_context, RequestContext
from app.repositories.asset_repository import AssetRepository
from app.core.database import get_db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Asset CRUD"])


@router.get("/")
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    asset_type: Optional[str] = None,
    environment: Optional[str] = None
):
    # This is a placeholder for the agentic, non-DB endpoint
    # The main paginated endpoint is below
    return {"message": "Use the paginated endpoint for database queries."}


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    repo = AssetRepository(db, context.client_account_id)
    asset = await repo.get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.post("/", response_model=AssetResponse, status_code=201)
async def create_asset(
    asset: AssetCreate,
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    user_id: str = Depends(get_user_id)
):
    repo = AssetRepository(db, context.client_account_id)
    new_asset = await repo.create_asset(asset, user_id, context.engagement_id)
    return new_asset


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: str,
    asset: AssetUpdate,
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    repo = AssetRepository(db, context.client_account_id)
    updated_asset = await repo.update_asset(asset_id, asset.dict(exclude_unset=True))
    if not updated_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return updated_asset


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    repo = AssetRepository(db, context.client_account_id)
    success = await repo.delete_asset(asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return None


@router.post("/bulk-create", response_model=Dict[str, Any])
async def bulk_create_assets(
    assets: List[AssetCreate],
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    user_id: str = Depends(get_user_id)
):
    repo = AssetRepository(db, context.client_account_id)
    result = await repo.bulk_create_assets(assets, user_id, context.engagement_id)
    return result