"""
Discovery Router (Legacy)
This is a legacy router that redirects to unified-discovery endpoints
"""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/")
async def redirect_to_unified():
    """Redirect to unified discovery"""
    return RedirectResponse(url="/api/v1/unified-discovery", status_code=307)


@router.get("/flows")
async def redirect_flows():
    """Redirect to unified discovery flows"""
    return RedirectResponse(url="/api/v1/unified-discovery/flows", status_code=307)


@router.get("/status")
async def discovery_status():
    """Legacy discovery status endpoint"""
    return {
        "status": "deprecated",
        "message": "Please use /api/v1/unified-discovery instead",
        "redirect": "/api/v1/unified-discovery",
    }
