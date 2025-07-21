"""
AI-powered Asset Intelligence endpoints leveraging CrewAI framework.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_crewai_flow_service
from app.services.crewai_flow_service import CrewAIFlowService
from app.core.context import get_current_context, RequestContext
from app.core.database import get_db
from app.core.database_timeout import get_db_for_asset_analysis
from .models import (
    AssetAnalysisRequest,
    BulkUpdatePlanRequest,
    AssetClassificationRequest,
    AssetFeedbackRequest
)
from .utils import get_asset_data

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Asset Intelligence"])


@router.get("/health")
async def asset_inventory_health(service: CrewAIFlowService = Depends(get_crewai_flow_service)):
    """Health check for enhanced asset inventory management."""
    try:
        health_status = service.get_service_status()
        return {
            "status": "healthy",
            "service": "enhanced-asset-inventory",
            "version": "2.0.0",
            "agentic_intelligence": health_status
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "enhanced-asset-inventory", 
            "version": "2.0.0",
            "error": str(e),
            "agentic_intelligence": {
                "available": False,
                "fallback_mode": True
            }
        }


@router.post("/analyze")
async def analyze_assets_intelligently(
    request: AssetAnalysisRequest,
    service: CrewAIFlowService = Depends(get_crewai_flow_service),
    context: RequestContext = Depends(get_current_context),
    db: Session = Depends(get_db_for_asset_analysis)
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
        
        # Get asset data with context for multitenancy
        assets = await get_asset_data(request.asset_ids, request.filters, context, db)
        
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
        analysis_result = await service.call_ai_agent(
            prompt=f"Analyze the following assets: {inventory_data}"
        )
        
        # Enhance result with metadata
        result_data = {
            "analysis": analysis_result,
            "request_operation": request.operation,
            "assets_analyzed": len(assets),
            "total_assets_available": len(assets),
            "agentic_analysis": True
        }
        
        logger.info(f"Asset intelligence analysis completed successfully for {len(assets)} assets")
        return result_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Asset analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Asset analysis failed: {str(e)}")


@router.post("/bulk-update-plan")
async def plan_bulk_update(
    request: BulkUpdatePlanRequest,
    service: CrewAIFlowService = Depends(get_crewai_flow_service),
    context: RequestContext = Depends(get_current_context),
    db: Session = Depends(get_db)
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
        
        # Validate asset IDs exist with context for multitenancy
        assets = await get_asset_data(request.asset_ids, None, context, db)
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
        planning_result = await service.call_ai_agent(
            prompt=f"Plan a bulk update with the following data: {operation_data}"
        )
        
        # Enhance result with validation details
        result_data = {
            "plan": planning_result,
            "request_summary": {
                "total_requested": len(request.asset_ids),
                "valid_assets": len(existing_asset_ids),
                "missing_assets": missing_asset_ids,
                "validation_level": request.validation_level
            },
            "agentic_planning": True
        }
        
        logger.info(f"Bulk update plan completed for {len(existing_asset_ids)} assets")
        return result_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk update planning failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk update planning failed: {str(e)}")


@router.post("/auto-classify")
async def auto_classify_assets(
    request: AssetClassificationRequest,
    service: CrewAIFlowService = Depends(get_crewai_flow_service),
    context: RequestContext = Depends(get_current_context),
    db: Session = Depends(get_db)
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
        
        # Get asset data for classification with context for multitenancy
        assets = await get_asset_data(request.asset_ids, None, context, db)
        
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
        
        # Use real CrewAI inventory building crew for classification
        from app.services.crewai_flows.crews.inventory_building_crew import InventoryBuildingCrew
        from app.services.crewai_flows.handlers.unified_flow_crew_manager import UnifiedFlowCrewManager
        
        # Create crew manager and inventory crew
        crew_manager = UnifiedFlowCrewManager()
        inventory_crew = InventoryBuildingCrew()
        
        # Prepare assets for reclassification
        assets_for_classification = []
        for asset in assets:
            # Convert asset to format expected by crew
            asset_data = {
                'id': asset.get('id'),
                'name': asset.get('asset_name', ''),
                'raw_data': asset.get('raw_data', {}),
                'current_type': asset.get('asset_type', ''),
                'hostname': asset.get('hostname', ''),
                'ip_address': asset.get('ip_address', ''),
                'operating_system': asset.get('operating_system', ''),
                'application_name': asset.get('application_name', ''),
                # Include all available asset data
                **asset
            }
            assets_for_classification.append(asset_data)
        
        # Use inventory crew to reclassify assets
        classification_input = {
            "assets": assets_for_classification,
            "operation": "reclassify_selected",
            "confidence_threshold": request.confidence_threshold
        }
        
        try:
            # Execute crew in thread to avoid blocking
            import asyncio
            classification_result = await asyncio.to_thread(
                inventory_crew.kickoff, 
                inputs=classification_input
            )
            
            # Parse crew results
            if hasattr(classification_result, 'raw') and classification_result.raw:
                import json
                try:
                    if '{' in classification_result.raw and '}' in classification_result.raw:
                        start = classification_result.raw.find('{')
                        end = classification_result.raw.rfind('}') + 1
                        json_str = classification_result.raw[start:end]
                        parsed_result = json.loads(json_str)
                        classification_result = parsed_result
                    else:
                        classification_result = {"status": "no_json", "raw": classification_result.raw}
                except json.JSONDecodeError:
                    classification_result = {"status": "parse_error", "raw": classification_result.raw}
            else:
                classification_result = {"status": "no_results", "message": "No classification results returned"}
                
        except Exception as crew_error:
            logger.error(f"CrewAI classification failed: {crew_error}")
            classification_result = {"status": "error", "message": str(crew_error)}

        result_data = {
            "classification_results": classification_result,
            "assets_processed": len(assets),
            "agentic_classification": True,
            "crew_used": "inventory_building_crew",
            "real_agents": True,
            "parameters": {
                "use_learned_patterns": request.use_learned_patterns,
                "confidence_threshold": request.confidence_threshold
            }
        }

        logger.info(f"Auto-classification completed for {len(assets)} assets")
        return result_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Asset classification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Asset classification failed: {str(e)}")


@router.post("/feedback")
async def process_asset_feedback(
    request: AssetFeedbackRequest,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """
    Process user feedback to improve the Asset Intelligence Agent's performance.
    
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
        
        # Send feedback to the agent learning system
        learning_response = await service.call_ai_agent(
            prompt=f"Learn from this user feedback: {feedback_data}"
        )
        
        return {
            "status": "success",
            "message": "Feedback received and processed for agent learning.",
            "learning_response": learning_response,
            "agentic_feedback_loop": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Asset feedback processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Feedback processing failed: {str(e)}")


@router.get("/intelligence-status")
async def get_asset_intelligence_status(
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """
    Get the current status and health of the Asset Intelligence Agent and its subsystems.
    """
    try:
        health_status = service.get_health_status()
        
        # Extract relevant info for asset intelligence
        asset_agent_status = {
            "agent_available": "asset_classifier" in health_status.get("agents", {}),
            "llm_configured": health_status.get("llm_configured", False),
            "service_available": health_status.get("service_available", False)
        }

        return {
            "status": "success",
            "asset_intelligence_status": asset_agent_status,
            "full_service_health": health_status
        }
    except Exception as e:
        logger.error(f"Failed to get asset intelligence status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get asset intelligence status")