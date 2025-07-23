"""
Asset management API endpoints.
Handles CRUD operations for infrastructure assets.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_assets():
    """List all assets - placeholder endpoint."""
    return {"message": "Assets endpoint - coming in Sprint 2"}


@router.post("/")
async def create_asset():
    """Create a new asset - placeholder endpoint."""
    return {"message": "Create asset endpoint - coming in Sprint 2"}


@router.get("/{asset_id}")
async def get_asset(asset_id: int):
    """Get asset by ID - placeholder endpoint."""
    return {"message": f"Get asset {asset_id} - coming in Sprint 2"}


@router.put("/{asset_id}")
async def update_asset(asset_id: int):
    """Update asset - placeholder endpoint."""
    return {"message": f"Update asset {asset_id} - coming in Sprint 2"}


@router.delete("/{asset_id}")
async def delete_asset(asset_id: int):
    """Delete asset - placeholder endpoint."""
    return {"message": f"Delete asset {asset_id} - coming in Sprint 2"}
