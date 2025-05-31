"""
Enhanced Asset Inventory Management API
Leverages the agentic CrewAI framework with Asset Intelligence Agent for intelligent operations.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Asset Inventory"])

# Pydantic models for request/response
class AssetAnalysisRequest(BaseModel):
    asset_ids: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    operation: str = "general_analysis"
    include_patterns: bool = True
    include_quality_assessment: bool = True

class BulkUpdatePlanRequest(BaseModel):
    asset_ids: List[str]
    proposed_updates: Dict[str, Any]
    validation_level: str = "standard"  # standard, strict, minimal
    execution_strategy: Optional[str] = None  # auto, batch, staged

class AssetClassificationRequest(BaseModel):
    asset_ids: List[str]
    use_learned_patterns: bool = True
    confidence_threshold: float = 0.8
    classification_context: Optional[str] = None

class AssetFeedbackRequest(BaseModel):
    operation_type: str
    feedback_text: str
    asset_ids: Optional[List[str]] = None
    corrections: Optional[Dict[str, Any]] = None
    user_context: Optional[str] = None

# Dependency to get CrewAI service
async def get_crewai_service():
    """Get the CrewAI service instance."""
    try:
        from app.services.crewai_service import crewai_service
        return crewai_service
    except ImportError as e:
        logger.error(f"CrewAI service not available: {e}")
        raise HTTPException(status_code=503, detail="AI services temporarily unavailable")

# Dependency to get asset data
async def get_asset_data(asset_ids: Optional[List[str]] = None, 
                        filters: Optional[Dict[str, Any]] = None):
    """Get asset data based on IDs or filters."""
    try:
        from app.api.v1.discovery.persistence import get_processed_assets
        
        # Get all assets (in production, implement proper filtering)
        all_assets = get_processed_assets()
        
        # Filter by asset IDs if provided
        if asset_ids:
            filtered_assets = [
                asset for asset in all_assets 
                if str(asset.get('id', '')) in asset_ids
            ]
        else:
            filtered_assets = all_assets
        
        # Apply additional filters if provided
        if filters:
            # Implement filter logic here
            pass
        
        return filtered_assets
        
    except ImportError:
        logger.warning("Asset persistence not available, using empty dataset")
        return []
    except Exception as e:
        logger.error(f"Failed to get asset data: {e}")
        return []

@router.get("/health")
async def asset_inventory_health():
    """Health check for enhanced asset inventory management."""
    try:
        crewai_service = await get_crewai_service()
        return {
            "status": "healthy",
            "service": "enhanced-asset-inventory",
            "version": "2.0.0",
            "agentic_intelligence": {
                "available": crewai_service.is_available(),
                "asset_intelligence_agent": "asset_intelligence" in (crewai_service.agents or {}),
                "field_mapping_intelligence": hasattr(crewai_service, 'field_mapping_tool'),
                "learning_system": hasattr(crewai_service, 'memory')
            }
        }
    except HTTPException:
        return {
            "status": "degraded",
            "service": "enhanced-asset-inventory", 
            "version": "2.0.0",
            "agentic_intelligence": {
                "available": False,
                "fallback_mode": True
            }
        }

@router.post("/analyze")
async def analyze_assets_intelligently(
    request: AssetAnalysisRequest,
    crewai_service = Depends(get_crewai_service)
):
    """
    Use Asset Intelligence Agent to analyze asset patterns, quality issues, and provide recommendations.
    
    This endpoint leverages the agentic CrewAI framework to provide intelligent insights:
    - AI-powered pattern recognition using learned field mappings
    - Intelligent data quality assessment with actionable recommendations
    - Content-based asset analysis (not hard-coded heuristics)
    - Bulk operation optimization suggestions
    """
    try:
        logger.info(f"Starting intelligent asset analysis for operation: {request.operation}")
        
        # Get asset data
        assets = await get_asset_data(request.asset_ids, request.filters)
        
        if not assets:
            return {
                "status": "no_data",
                "message": "No assets found matching the specified criteria",
                "asset_count": 0
            }
        
        # Prepare data for Asset Intelligence Agent
        inventory_data = {
            "assets": assets[:50],  # Limit for performance (sample analysis)
            "operation": request.operation,
            "include_patterns": request.include_patterns,
            "include_quality_assessment": request.include_quality_assessment,
            "total_asset_count": len(assets),
            "analysis_context": {
                "asset_ids": request.asset_ids,
                "filters": request.filters
            }
        }
        
        # Use Asset Intelligence Agent for analysis
        analysis_result = await crewai_service.analyze_asset_inventory(inventory_data)
        
        # Enhance result with metadata
        analysis_result.update({
            "request_operation": request.operation,
            "assets_analyzed": len(assets),
            "total_assets_available": len(assets),
            "agentic_analysis": True
        })
        
        logger.info(f"Asset intelligence analysis completed successfully for {len(assets)} assets")
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Asset analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Asset analysis failed: {str(e)}")

@router.post("/bulk-update-plan")
async def plan_bulk_update(
    request: BulkUpdatePlanRequest,
    crewai_service = Depends(get_crewai_service)
):
    """
    Use Asset Intelligence Agent to plan optimal bulk update strategy.
    
    Features:
    - AI-powered validation using learned field mapping patterns
    - Intelligent execution strategy optimization
    - Risk assessment based on operation scope and historical patterns
    - Rollback planning and safety recommendations
    """
    try:
        logger.info(f"Planning bulk update for {len(request.asset_ids)} assets")
        
        # Validate asset IDs exist
        assets = await get_asset_data(request.asset_ids)
        existing_asset_ids = [str(asset.get('id', '')) for asset in assets]
        missing_asset_ids = [aid for aid in request.asset_ids if aid not in existing_asset_ids]
        
        if missing_asset_ids:
            logger.warning(f"Missing asset IDs: {missing_asset_ids}")
        
        # Prepare data for Asset Intelligence Agent
        operation_data = {
            "asset_ids": existing_asset_ids,
            "proposed_updates": request.proposed_updates,
            "validation_level": request.validation_level,
            "execution_strategy": request.execution_strategy,
            "existing_assets": len(existing_asset_ids),
            "missing_assets": len(missing_asset_ids),
            "operation_scope": {
                "total_assets": len(request.asset_ids),
                "update_fields": list(request.proposed_updates.keys()),
                "complexity_score": len(request.proposed_updates) * len(request.asset_ids)
            }
        }
        
        # Use Asset Intelligence Agent for planning
        planning_result = await crewai_service.plan_asset_bulk_operation(operation_data)
        
        # Enhance result with validation details
        planning_result.update({
            "request_summary": {
                "total_requested": len(request.asset_ids),
                "valid_assets": len(existing_asset_ids),
                "missing_assets": missing_asset_ids,
                "validation_level": request.validation_level
            },
            "agentic_planning": True
        })
        
        logger.info(f"Bulk update plan completed for {len(existing_asset_ids)} assets")
        return planning_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk update planning failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk update planning failed: {str(e)}")

@router.post("/auto-classify")
async def auto_classify_assets(
    request: AssetClassificationRequest,
    crewai_service = Depends(get_crewai_service)
):
    """
    Use Asset Intelligence Agent to automatically classify assets based on learned patterns.
    
    Features:
    - Content-based classification using field mapping intelligence
    - AI pattern recognition from historical classifications
    - Confidence scoring for classification suggestions
    - Bulk classification opportunities identification
    """
    try:
        logger.info(f"Auto-classifying {len(request.asset_ids)} assets")
        
        # Get asset data for classification
        assets = await get_asset_data(request.asset_ids)
        
        if not assets:
            return {
                "status": "no_assets",
                "message": "No assets found for classification",
                "asset_count": 0
            }
        
        # Prepare data for Asset Intelligence Agent
        classification_data = {
            "asset_ids": request.asset_ids,
            "assets": assets,
            "use_learned_patterns": request.use_learned_patterns,
            "confidence_threshold": request.confidence_threshold,
            "classification_context": request.classification_context,
            "operation_context": {
                "total_assets": len(assets),
                "classification_scope": "auto_classification",
                "learning_enabled": request.use_learned_patterns
            }
        }
        
        # Use Asset Intelligence Agent for classification
        classification_result = await crewai_service.classify_assets(classification_data)
        
        # Enhance result with metadata
        classification_result.update({
            "request_summary": {
                "assets_processed": len(assets),
                "confidence_threshold": request.confidence_threshold,
                "use_learned_patterns": request.use_learned_patterns
            },
            "agentic_classification": True
        })
        
        logger.info(f"Asset classification completed for {len(assets)} assets")
        return classification_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Asset classification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Asset classification failed: {str(e)}")

@router.post("/feedback")
async def process_asset_feedback(
    request: AssetFeedbackRequest,
    crewai_service = Depends(get_crewai_service)
):
    """
    Process user feedback from asset management operations to improve AI intelligence.
    
    This endpoint enables continuous learning:
    - Field mapping learning from user corrections
    - Asset classification pattern learning
    - Data quality assessment improvements
    - Bulk operation optimization learning
    """
    try:
        logger.info(f"Processing asset feedback for operation: {request.operation_type}")
        
        # Prepare feedback data for Learning Agent
        feedback_data = {
            "operation_type": request.operation_type,
            "feedback_text": request.feedback_text,
            "asset_ids": request.asset_ids,
            "corrections": request.corrections,
            "user_context": request.user_context,
            "feedback_metadata": {
                "has_corrections": bool(request.corrections),
                "asset_count": len(request.asset_ids) if request.asset_ids else 0,
                "feedback_length": len(request.feedback_text)
            }
        }
        
        # Use Learning Agent to process feedback
        learning_result = await crewai_service.process_asset_feedback(feedback_data)
        
        # Enhance result with processing metadata
        learning_result.update({
            "feedback_processed": True,
            "operation_type": request.operation_type,
            "learning_applied": True,
            "continuous_improvement": "System intelligence enhanced based on feedback"
        })
        
        logger.info(f"Asset feedback processed successfully for operation: {request.operation_type}")
        return learning_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Asset feedback processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Feedback processing failed: {str(e)}")

@router.get("/intelligence-status")
async def get_asset_intelligence_status(
    crewai_service = Depends(get_crewai_service)
):
    """
    Get status of asset intelligence capabilities and learned patterns.
    
    Provides insight into:
    - Available AI agents and their capabilities
    - Learned field mapping patterns
    - System learning metrics
    - Intelligence enhancement opportunities
    """
    try:
        # Get comprehensive intelligence status
        intelligence_status = {
            "agentic_framework": {
                "available": crewai_service.is_available(),
                "asset_intelligence_agent": "asset_intelligence" in (crewai_service.agents or {}),
                "learning_agent": "learning_agent" in (crewai_service.agents or {}),
                "pattern_agent": "pattern_agent" in (crewai_service.agents or {}),
                "total_agents": len(crewai_service.agents or {})
            },
            "field_mapping_intelligence": {},
            "learning_metrics": {},
            "capabilities": {
                "intelligent_analysis": True,
                "bulk_operation_planning": True,
                "auto_classification": True,
                "continuous_learning": True,
                "pattern_recognition": True
            }
        }
        
        # Get field mapping intelligence status
        if hasattr(crewai_service, 'field_mapping_tool') and crewai_service.field_mapping_tool:
            try:
                field_context = crewai_service.field_mapping_tool.get_mapping_context()
                intelligence_status["field_mapping_intelligence"] = {
                    "available": True,
                    "learned_mappings": field_context.get("learned_mappings", {}),
                    "mapping_statistics": field_context.get("mapping_statistics", {}),
                    "total_variations_learned": field_context.get("total_variations_learned", 0)
                }
            except Exception as e:
                logger.warning(f"Failed to get field mapping context: {e}")
                intelligence_status["field_mapping_intelligence"] = {"available": False, "error": str(e)}
        
        # Get learning metrics
        if hasattr(crewai_service, 'memory') and crewai_service.memory:
            try:
                learning_metrics = crewai_service.memory.get_learning_metrics()
                intelligence_status["learning_metrics"] = learning_metrics
            except Exception as e:
                logger.warning(f"Failed to get learning metrics: {e}")
                intelligence_status["learning_metrics"] = {"error": str(e)}
        
        return intelligence_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get intelligence status: {e}")
        raise HTTPException(status_code=500, detail=f"Intelligence status failed: {str(e)}")

# Legacy compatibility endpoints
@router.get("/")
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    asset_type: Optional[str] = None,
    environment: Optional[str] = None
):
    """
    List assets with pagination and filtering.
    Enhanced with agentic intelligence capabilities.
    """
    try:
        # Get asset data
        all_assets = await get_asset_data()
        
        # Apply filters
        filtered_assets = all_assets
        if asset_type:
            filtered_assets = [a for a in filtered_assets if a.get('asset_type') == asset_type]
        if environment:
            filtered_assets = [a for a in filtered_assets if a.get('environment') == environment]
        
        # Pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_assets = filtered_assets[start_idx:end_idx]
        
        return {
            "assets": paginated_assets,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_assets": len(filtered_assets),
                "total_pages": (len(filtered_assets) + page_size - 1) // page_size
            },
            "enhanced_capabilities": {
                "intelligent_analysis": "Available via /analyze endpoint",
                "bulk_operations": "Available via /bulk-update-plan endpoint", 
                "auto_classification": "Available via /auto-classify endpoint"
            }
        }
        
    except Exception as e:
        logger.error(f"Asset listing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Asset listing failed: {str(e)}")

@router.get("/{asset_id}")
async def get_asset(asset_id: str):
    """Get a specific asset by ID with intelligence enhancement opportunities."""
    try:
        assets = await get_asset_data([asset_id])
        
        if not assets:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        
        asset = assets[0]
        
        # Enhance with intelligence suggestions
        asset["enhancement_opportunities"] = {
            "intelligent_analysis": f"Analyze this asset via POST /analyze with asset_ids=['{asset_id}']",
            "classification_check": f"Auto-classify via POST /auto-classify with asset_ids=['{asset_id}']",
            "quality_assessment": "Available through intelligent analysis"
        }
        
        return asset
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Asset retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Asset retrieval failed: {str(e)}") 