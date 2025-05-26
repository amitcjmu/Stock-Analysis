"""
Discovery API endpoints.
Handles infrastructure discovery and scanning operations.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_discovery_status():
    """Get discovery status - placeholder endpoint."""
    return {"message": "Discovery status endpoint - coming in Sprint 2"}


@router.post("/scan")
async def start_discovery_scan():
    """Start infrastructure discovery scan - placeholder endpoint."""
    return {"message": "Discovery scan endpoint - coming in Sprint 2"}


@router.get("/scan/{scan_id}")
async def get_scan_results(scan_id: int):
    """Get scan results - placeholder endpoint."""
    return {"message": f"Scan results {scan_id} - coming in Sprint 2"}


@router.post("/import")
async def import_assets():
    """Import assets from external sources - placeholder endpoint."""
    return {"message": "Asset import endpoint - coming in Sprint 2"} 