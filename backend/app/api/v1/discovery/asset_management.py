"""
Asset Management - Modular & Robust
Combines robust error handling with clean modular architecture.
"""

import logging
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .asset_handlers import (
    AssetCRUDHandler,
    AssetProcessingHandler,
    AssetValidationHandler,
    AssetAnalysisHandler,
    AssetUtilsHandler
)

logger = logging.getLogger(__name__)

# Create main router
router = APIRouter()

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

@router.get("/health")
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

@router.get("/assets")
async def get_processed_assets_paginated(
    page: int = 1,
    page_size: int = 50,
    asset_type: str = None,
    environment: str = None,
    department: str = None,
    criticality: str = None,
    search: str = None
):
    """
    Get paginated processed assets with filtering capabilities.
    Enhanced with agentic intelligence and asset inventory management.
    """
    try:
        # First try to get assets using existing CRUD handler
        params = {
            'page': page,
            'page_size': page_size,
            'asset_type': asset_type,
            'environment': environment,
            'department': department,
            'criticality': criticality,
            'search': search
        }
        
        result = await crud_handler.get_assets_paginated(params)
        
        # Enhance with agentic intelligence if available
        try:
            from app.services.crewai_service import crewai_service
            if crewai_service.is_available() and result.get("assets"):
                # Add agentic enhancement metadata
                result["enhanced_capabilities"] = {
                    "intelligent_analysis": "Available via agentic asset intelligence",
                    "auto_classification": "AI-powered asset classification available",
                    "bulk_operations": "Intelligent bulk operation planning available",
                    "continuous_learning": "System learns from user interactions",
                    "agentic_framework_active": True
                }
                
                # Add intelligence status for UI
                result["intelligence_status"] = {
                    "asset_intelligence_agent": "asset_intelligence" in (crewai_service.agents or {}),
                    "field_mapping_intelligence": hasattr(crewai_service, 'field_mapping_tool'),
                    "learning_system": hasattr(crewai_service, 'memory')
                }
                
                logger.info(f"Enhanced asset response with agentic intelligence for {len(result.get('assets', []))} assets")
        
        except ImportError:
            logger.info("CrewAI service not available, using standard asset response")
        except Exception as e:
            logger.warning(f"Failed to enhance with agentic intelligence: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_processed_assets_paginated: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve assets: {str(e)}")

@router.put("/assets/bulk")
async def bulk_update_assets_endpoint(request: Request):
    """
    Bulk update multiple assets.
    """
    try:
        request_body = await request.json()
        result = await crud_handler.bulk_update_assets(request_body)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Bulk update failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk_update_assets_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk update assets: {str(e)}")

@router.delete("/assets/bulk")
async def bulk_delete_assets_endpoint(request: BulkDeleteRequest):
    """
    Bulk delete multiple assets.
    """
    try:
        result = await crud_handler.bulk_delete_assets(request.asset_ids)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Bulk delete failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk_delete_assets_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk delete assets: {str(e)}")

@router.put("/assets/{asset_id}")
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

@router.post("/reprocess-assets")
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
async def get_applications_for_analysis():
    """
    Get applications data specially formatted for 6R analysis.
    """
    try:
        result = await processing_handler.get_applications_for_analysis()
        return result
        
    except Exception as e:
        logger.error(f"Error in get_applications_for_analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get applications: {str(e)}")

@router.get("/assets/duplicates")
async def find_duplicate_assets_endpoint():
    """Find potential duplicate assets in the inventory."""
    try:
        result = await crud_handler.find_duplicates()
        return result
        
    except Exception as e:
        logger.error(f"Error in find_duplicate_assets_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find duplicates: {str(e)}")

@router.post("/assets/cleanup-duplicates")
async def cleanup_duplicate_assets_endpoint():
    """Remove duplicate assets from the inventory."""
    try:
        result = await crud_handler.cleanup_duplicates()
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

# Enhanced Agentic Asset Intelligence Endpoints 🆕
@router.post("/assets/analyze")
async def analyze_assets_with_intelligence(request: Request):
    """
    Use Asset Intelligence Agent to analyze asset patterns and provide recommendations.
    Integrates with the existing discovery workflow.
    """
    try:
        from app.services.crewai_service import crewai_service
        
        if not crewai_service.is_available():
            # Fallback to traditional analysis
            return await analysis_handler.get_data_issues()
        
        request_body = await request.json()
        asset_ids = request_body.get('asset_ids', [])
        operation = request_body.get('operation', 'pattern_analysis')
        
        # Get assets from CRUD handler first
        if asset_ids:
            assets_data = []
            for asset_id in asset_ids:
                try:
                    asset = await crud_handler.get_asset_by_id(asset_id)
                    if asset:
                        assets_data.append(asset)
                except:
                    pass  # Skip missing assets
        else:
            # Get sample of assets for analysis
            params = {'page': 1, 'page_size': 50}
            result = await crud_handler.get_assets_paginated(params)
            assets_data = result.get('assets', [])
        
        # Use Asset Intelligence Agent for analysis
        inventory_data = {
            "assets": assets_data,
            "operation": operation,
            "include_patterns": request_body.get('include_patterns', True),
            "include_quality_assessment": request_body.get('include_quality_assessment', True),
            "total_asset_count": len(assets_data)
        }
        
        analysis_result = await crewai_service.analyze_asset_inventory(inventory_data)
        
        # Enhance result with discovery context
        analysis_result.update({
            "discovery_integration": True,
            "assets_analyzed": len(assets_data),
            "endpoint": "/api/v1/discovery/assets/analyze"
        })
        
        return analysis_result
        
    except ImportError:
        logger.info("CrewAI service not available, falling back to traditional analysis")
        return await analysis_handler.get_data_issues()
    except Exception as e:
        logger.error(f"Asset intelligence analysis failed: {e}")
        # Fallback to traditional analysis
        return await analysis_handler.get_data_issues()

@router.post("/assets/auto-classify")
async def auto_classify_assets_with_intelligence(request: Request):
    """
    Use Asset Intelligence Agent for automatic asset classification.
    """
    try:
        from app.services.crewai_service import crewai_service
        
        if not crewai_service.is_available():
            return {"status": "ai_not_available", "message": "AI classification not available"}
        
        request_body = await request.json()
        asset_ids = request_body.get('asset_ids', [])
        
        # Get assets from CRUD handler
        assets_data = []
        for asset_id in asset_ids:
            try:
                asset = await crud_handler.get_asset_by_id(asset_id)
                if asset:
                    assets_data.append(asset)
            except:
                pass  # Skip missing assets
        
        if not assets_data:
            return {"status": "no_assets", "message": "No assets found for classification"}
        
        # Use Asset Intelligence Agent for classification
        classification_data = {
            "asset_ids": asset_ids,
            "assets": assets_data,
            "use_learned_patterns": request_body.get('use_learned_patterns', True),
            "confidence_threshold": request_body.get('confidence_threshold', 0.8)
        }
        
        classification_result = await crewai_service.classify_assets(classification_data)
        
        # Enhance result with discovery context
        classification_result.update({
            "discovery_integration": True,
            "endpoint": "/api/v1/discovery/assets/auto-classify"
        })
        
        return classification_result
        
    except ImportError:
        return {"status": "ai_not_available", "message": "AI classification not available"}
    except Exception as e:
        logger.error(f"Asset auto-classification failed: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/assets/intelligence-status")
async def get_asset_intelligence_status():
    """
    Get status of asset intelligence capabilities integrated with discovery.
    """
    try:
        from app.services.crewai_service import crewai_service
        
        intelligence_status = {
            "discovery_integration": True,
            "endpoint": "/api/v1/discovery/assets/intelligence-status",
            "agentic_framework": {
                "available": crewai_service.is_available(),
                "asset_intelligence_agent": "asset_intelligence" in (crewai_service.agents or {}),
                "learning_agent": "learning_agent" in (crewai_service.agents or {}),
                "total_agents": len(crewai_service.agents or {})
            },
            "capabilities": {
                "intelligent_analysis": True,
                "auto_classification": True,
                "pattern_recognition": True,
                "continuous_learning": True
            }
        }
        
        # Get field mapping intelligence status
        if hasattr(crewai_service, 'field_mapping_tool') and crewai_service.field_mapping_tool:
            try:
                field_context = crewai_service.field_mapping_tool.get_mapping_context()
                intelligence_status["field_mapping_intelligence"] = {
                    "available": True,
                    "learned_mappings": field_context.get("learned_mappings", {}),
                    "total_variations_learned": field_context.get("total_variations_learned", 0)
                }
            except:
                intelligence_status["field_mapping_intelligence"] = {"available": False}
        
        return intelligence_status
        
    except ImportError:
        return {
            "discovery_integration": True,
            "agentic_framework": {"available": False},
            "capabilities": {
                "intelligent_analysis": False,
                "auto_classification": False,
                "pattern_recognition": False,
                "continuous_learning": False
            },
            "message": "CrewAI service not available"
        } 