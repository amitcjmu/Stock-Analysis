"""
Asset Management - Modular & Robust
Combines robust error handling with clean modular architecture.
"""

import logging
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
import asyncio

from app.api.v1.discovery.asset_handlers.asset_crud import AssetCRUDHandler
from app.api.v1.discovery.asset_handlers.asset_processing import AssetProcessingHandler
from app.api.v1.discovery.asset_handlers.asset_validation import AssetValidationHandler
from app.api.v1.discovery.asset_handlers.asset_analysis import AssetAnalysisHandler
from app.api.v1.discovery.asset_handlers.asset_utils import AssetUtilsHandler

from app.core.context import RequestContext, get_current_context

logger = logging.getLogger(__name__)

# Create main router
router = APIRouter(prefix="/assets", tags=["Assets"])

# Initialize handlers
crud_handler = AssetCRUDHandler()
processing_handler = AssetProcessingHandler()
validation_handler = AssetValidationHandler()
analysis_handler = AssetAnalysisHandler()
utils_handler = AssetUtilsHandler()

# Request models
class BulkUpdateRequest(BaseModel):
    asset_ids: List[str]
    updates: Dict[str, Any]

class BulkDeleteRequest(BaseModel):
    asset_ids: List[str]

@router.get("/health_check")
async def asset_management_health_check():
    """Health check endpoint for asset management module."""
    return {
        "status": "healthy",
        "module": "asset-management",
        "version": "2.0.0",
        "components": {
            "crud": crud_handler.is_available(),
            "processing": processing_handler.is_available(),
            "validation": validation_handler.is_available(),
            "analysis": analysis_handler.is_available(),
            "utils": utils_handler.is_available()
        }
    }

@router.get("/")
async def get_processed_assets_paginated(
    page: int = 1,
    page_size: int = 50,
    asset_type: str = None,
    environment: str = None,
    department: str = None,
    criticality: str = None,
    search: str = None,
    context: RequestContext = Depends(get_current_context)
):
    """
    Get paginated processed assets with filtering capabilities.
    """
    try:
        params = {
            'page': page,
            'page_size': page_size,
            'asset_type': asset_type,
            'environment': environment,
            'department': department,
            'criticality': criticality,
            'search': search,
            'client_account_id': context.client_account_id
        }
        
        result = await crud_handler.get_assets_paginated(params)
        return result
        
    except Exception as e:
        logger.error(f"Error in get_processed_assets_paginated: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve assets: {str(e)}")

@router.put("/bulk")
async def bulk_update_assets_endpoint(
    request: Request,
    context: RequestContext = Depends(get_current_context)
):
    """
    Bulk update multiple assets with proper client/engagement scoping.
    """
    try:
        request_body = await request.json()
        
        # Add context information to the request
        request_body['client_account_id'] = context.client_account_id
        request_body['engagement_id'] = context.engagement_id
        
        result = await crud_handler.bulk_update_assets(request_body)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Bulk update failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk_update_assets_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk update assets: {str(e)}")

@router.delete("/bulk")
async def bulk_delete_assets_endpoint(
    request: BulkDeleteRequest,
    context: RequestContext = Depends(get_current_context)
):
    """
    Bulk delete multiple assets with proper client/engagement scoping.
    """
    try:
        # Pass context information to the CRUD handler
        result = await crud_handler.bulk_delete_assets(
            request.asset_ids,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Bulk delete failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk_delete_assets_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk delete assets: {str(e)}")

@router.put("/{asset_id}")
async def update_asset(asset_id: str, asset_data: Dict[str, Any]):
    """
    Update an existing asset.
    """
    try:
        result = await crud_handler.update_asset(asset_id, asset_data)
        
        if result.get("status") == "error":
            if "not found" in result.get("message", "").lower():
                raise HTTPException(status_code=404, detail=result.get("message"))
            else:
                raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_asset: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update asset: {str(e)}")

@router.post("/reprocess")
async def reprocess_stored_assets():
    """
    Reprocess stored assets with updated algorithms.
    """
    try:
        result = await processing_handler.reprocess_stored_assets()
        return result
        
    except Exception as e:
        logger.error(f"Error in reprocess_stored_assets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reprocess assets: {str(e)}")

@router.get("/applications")
async def get_applications_for_analysis(
    context: RequestContext = Depends(get_current_context)
):
    """
    Get applications data specially formatted for 6R analysis with proper client/engagement scoping.
    """
    try:
        result = await processing_handler.get_applications_for_analysis(
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        return result
        
    except Exception as e:
        logger.error(f"Error in get_applications_for_analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get applications: {str(e)}")

@router.get("/unlinked")
async def get_unlinked_assets(
    context: RequestContext = Depends(get_current_context)
):
    """
    Get assets that are NOT tied to any application - critical for migration planning.
    """
    try:
        result = await processing_handler.get_unlinked_assets(
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        return result
        
    except Exception as e:
        logger.error(f"Error in get_unlinked_assets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get unlinked assets: {str(e)}")

@router.get("/discovery-metrics")
async def get_discovery_metrics(context: RequestContext = Depends(get_current_context)):
    """
    Get discovery metrics for the Discovery Overview dashboard.
    """
    try:
        result = await analysis_handler.get_discovery_metrics(
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        return result
        
    except Exception as e:
        logger.error(f"Error in get_discovery_metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get discovery metrics: {str(e)}")

@router.get("/application-landscape")
async def get_application_landscape(context: RequestContext = Depends(get_current_context)):
    """
    Get application landscape data for the Discovery Overview dashboard.
    """
    try:
        result = await analysis_handler.get_application_landscape(
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        return result
        
    except Exception as e:
        logger.error(f"Error in get_application_landscape: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get application landscape: {str(e)}")

@router.get("/infrastructure-landscape") 
async def get_infrastructure_landscape(context: RequestContext = Depends(get_current_context)):
    """
    Get infrastructure landscape data for the Discovery Overview dashboard.
    """
    try:
        result = await analysis_handler.get_infrastructure_landscape(
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        return result
        
    except Exception as e:
        logger.error(f"Error in get_infrastructure_landscape: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get infrastructure landscape: {str(e)}")

@router.get("/duplicates")
async def find_duplicate_assets_endpoint():
    """Find potential duplicate assets in the inventory."""
    try:
        result = await crud_handler.find_duplicates()
        return result
        
    except Exception as e:
        logger.error(f"Error in find_duplicate_assets_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find duplicates: {str(e)}")

@router.post("/cleanup-duplicates")
async def cleanup_duplicate_assets_endpoint(
    context: RequestContext = Depends(get_current_context)
):
    """Remove duplicate assets from the inventory with proper client/engagement scoping."""
    try:
        # Call the method with context information
        result = crud_handler.cleanup_duplicates(
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        return result
        
    except Exception as e:
        logger.error(f"Error in cleanup_duplicate_assets_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup duplicates: {str(e)}")

@router.get("/data-issues")
async def get_data_issues():
    """
    Get comprehensive data quality analysis optimized for 3-section UI.
    """
    try:
        result = await analysis_handler.get_data_issues()
        return result
        
    except Exception as e:
        logger.error(f"Error in get_data_issues: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze data issues: {str(e)}")

@router.post("/validate-data")
async def validate_data():
    """
    Validate asset data and return validation results.
    """
    try:
        result = await validation_handler.validate_data()
        return result
        
    except Exception as e:
        logger.error(f"Error in validate_data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate data: {str(e)}")

@router.post("/data-issues/{issue_id}/approve")
async def approve_data_issue(issue_id: str):
    """
    Approve a data issue resolution.
    """
    try:
        result = await validation_handler.approve_data_issue(issue_id)
        return result
        
    except Exception as e:
        logger.error(f"Error in approve_data_issue: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to approve data issue: {str(e)}")

@router.post("/data-issues/{issue_id}/reject")
async def reject_data_issue(issue_id: str, request: Request):
    """
    Reject a data issue resolution.
    """
    try:
        request_body = await request.json()
        rejection_reason = request_body.get("reason", "No reason provided")
        
        result = await validation_handler.reject_data_issue(issue_id, rejection_reason)
        return result
        
    except Exception as e:
        logger.error(f"Error in reject_data_issue: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reject data issue: {str(e)}")

# Legacy endpoints for backward compatibility
@router.get("/legacy/summary")
async def get_legacy_summary():
    """
    Legacy summary endpoint for backward compatibility.
    """
    try:
        # Use CRUD handler to get basic asset count
        params = {'page': 1, 'page_size': 1}
        result = await crud_handler.get_assets_paginated(params)
        
        return {
            "status": "success", 
            "total_assets": result.get("total", 0),
            "summary": result.get("summary", {}),
            "note": "This is a legacy endpoint. Please use /assets for full functionality."
        }
        
    except Exception as e:
        logger.error(f"Error in get_legacy_summary: {e}")
        return {
            "status": "error",
            "total_assets": 0,
            "summary": {},
            "error": str(e)
        } 