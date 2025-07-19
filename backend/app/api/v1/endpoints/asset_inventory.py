"""
Enhanced Asset Inventory Management API
Leverages the agentic CrewAI framework with Asset Intelligence Agent for intelligent operations.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies import get_crewai_flow_service
from app.services.crewai_flow_service import CrewAIFlowService
from app.schemas.asset_schemas import AssetCreate, AssetUpdate, AssetResponse, PaginatedAssetResponse
from app.core.context import get_user_id, get_current_context, RequestContext
from app.repositories.asset_repository import AssetRepository
from app.core.database import get_db
from app.core.database_timeout import get_db_for_asset_list, get_db_for_asset_analysis
from app.models.data_import.core import RawImportRecord
from app.models.asset import Asset
from sqlalchemy import select

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

# Dependency to get asset data
async def get_asset_data(asset_ids: Optional[List[str]] = None, 
                        filters: Optional[Dict[str, Any]] = None,
                        context: Optional[RequestContext] = None,
                        db: Optional[Session] = None):
    """Get asset data based on IDs or filters with proper multitenancy filtering."""
    try:
        # IMPORTANT: Enforce multitenancy - if context is available, filter by it
        if context and context.client_account_id and context.engagement_id:
            # Use database query with context filtering
            from app.models.asset import Asset
            from sqlalchemy import select
            from app.core.database import get_db
            
            # If no db session provided, get one
            if db is None:
                # This is a simplified approach for sync session
                # In practice, we should use dependency injection
                logger.warning("No database session provided to get_asset_data")
                return []
            
            # Use the repository pattern for proper context filtering
            from app.repositories.asset_repository import AssetRepository
            repo = AssetRepository(db, context.client_account_id)
            
            if asset_ids:
                # Get multiple assets by IDs
                assets = []
                for asset_id in asset_ids:
                    asset = await repo.get_by_id(asset_id)
                    if asset:
                        assets.append(asset)
            else:
                # Get all assets for the context
                assets = await repo.get_all(limit=1000)  # Reasonable limit
            
            # Convert to dict format
            return [
                {
                    'id': str(asset.id),
                    'name': asset.name,
                    'asset_type': asset.asset_type,
                    'environment': asset.environment,
                    'criticality': asset.criticality,
                    'status': asset.status,
                    'six_r_strategy': asset.six_r_strategy,
                    'migration_wave': asset.migration_wave,
                    'application_name': asset.application_name,
                    'hostname': asset.hostname,
                    'operating_system': asset.operating_system,
                    'cpu_cores': asset.cpu_cores,
                    'memory_gb': asset.memory_gb,
                    'storage_gb': asset.storage_gb
                }
                for asset in assets
            ]
        else:
            # Fallback to persistence layer with warning
            logger.warning("No context available for multitenancy filtering - returning empty dataset for security")
            return []
            
    except ImportError:
        logger.warning("Asset persistence not available, using empty dataset")
        return []
    except Exception as e:
        logger.error(f"Failed to get asset data: {e}")
        return []

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

@router.get("/data-audit/{asset_id}")
async def get_asset_data_audit(
    asset_id: str,
    context: RequestContext = Depends(get_current_context),
    db: Session = Depends(get_db)
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
        
        # Find linked raw import record using asset_id
        from sqlalchemy import select
        from app.core.database import get_async_db_session
        
        async with get_async_db_session() as session:
            result = await session.execute(
                select(RawImportRecord)
                .where(RawImportRecord.asset_id == asset.id)
                .where(RawImportRecord.client_account_id == context.client_account_id)
            )
            raw_record = result.scalar_one_or_none()
        
        if not raw_record:
            return {
                "asset_id": asset_id,
                "asset_name": asset.name,
                "message": "No raw import record linked to this asset",
                "raw_data": None,
                "cleansed_data": None,
                "final_asset": {
                    "name": asset.name,
                    "asset_type": asset.asset_type,
                    "environment": asset.environment,
                    "hostname": asset.hostname,
                    "operating_system": asset.operating_system
                }
            }
        
        # Compare name fields specifically
        raw_name_fields = {
            "App_Name": raw_record.raw_data.get("App_Name"),
            "app_name": raw_record.raw_data.get("app_name"), 
            "name": raw_record.raw_data.get("name"),
            "asset_name": raw_record.raw_data.get("asset_name"),
            "hostname": raw_record.raw_data.get("hostname"),
            "application_name": raw_record.raw_data.get("application_name")
        }
        
        cleansed_name_fields = {} if not raw_record.cleansed_data else {
            "App_Name": raw_record.cleansed_data.get("App_Name"),
            "app_name": raw_record.cleansed_data.get("app_name"),
            "name": raw_record.cleansed_data.get("name"),
            "asset_name": raw_record.cleansed_data.get("asset_name"),
            "hostname": raw_record.cleansed_data.get("hostname"),
            "application_name": raw_record.cleansed_data.get("application_name")
        }
        
        return {
            "asset_id": asset_id,
            "row_number": raw_record.row_number,
            "data_import_id": str(raw_record.data_import_id),
            "is_valid": raw_record.is_valid,
            "is_processed": raw_record.is_processed,
            "validation_errors": raw_record.validation_errors,
            "processing_notes": raw_record.processing_notes,
            "name_field_analysis": {
                "raw_name_fields": {k: v for k, v in raw_name_fields.items() if v is not None},
                "cleansed_name_fields": {k: v for k, v in cleansed_name_fields.items() if v is not None},
                "final_asset_name": asset.name,
                "name_transformation_issue": (
                    len([v for v in raw_name_fields.values() if v]) > 0 and 
                    (not asset.name or asset.name.startswith("Asset-"))
                )
            },
            "raw_data": raw_record.raw_data,
            "cleansed_data": raw_record.cleansed_data,
            "final_asset": {
                "name": asset.name,
                "asset_type": asset.asset_type,
                "environment": asset.environment,
                "hostname": asset.hostname,
                "operating_system": asset.operating_system,
                "application_name": asset.application_name,
                "cpu_cores": asset.cpu_cores,
                "memory_gb": asset.memory_gb,
                "storage_gb": asset.storage_gb
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data audit failed for asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Data audit failed: {str(e)}")

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

@router.get("/list/paginated-fallback")
async def list_assets_paginated_fallback(
    page: int = 1,
    page_size: int = 50,
    db: Optional[Session] = Depends(get_db_for_asset_list),
    context: RequestContext = Depends(get_current_context)
):
    """Lightweight fallback that returns an empty asset list when DB or context unavailable."""
    try:
        if db is None or context.client_account_id is None:
            # Return empty placeholder response
            total_pages = 0
            return {
                "assets": [],
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_items": 0,
                    "total_pages": total_pages,
                    "has_next": False,
                    "has_previous": False
                },
                "summary": {
                    "total": 0,
                    "filtered": 0,
                    "applications": 0,
                    "servers": 0,
                    "databases": 0,
                    "devices": 0,
                    "unknown": 0,
                    "discovered": 0,
                    "pending": 0,
                    "device_breakdown": {}
                },
                "last_updated": None,
                "data_source": "demo",
                "suggested_headers": [],
                "app_mappings": [],
                "unlinked_assets": [],
                "unlinked_summary": {
                    "total_unlinked": 0,
                    "by_type": {},
                    "by_environment": {},
                    "by_criticality": {},
                    "migration_impact": "none"
                }
            }
    except Exception:
        pass  # fallback to main implementation below
    
    # Ensure we always return something
    return None

@router.get("/list/paginated")
async def list_assets_paginated(
    db: AsyncSession = Depends(get_db_for_asset_list),
    context: RequestContext = Depends(get_current_context),
    page: int = Query(1, gt=0),
    page_size: int = Query(20, gt=0, le=100),
    per_page: int = Query(None)  # Support both page_size and per_page
):
    """Get paginated list of assets for the current context."""
    try:
        # Support both page_size and per_page parameters
        if per_page is not None:
            page_size = per_page
            
        # Import here to avoid circular imports
        from sqlalchemy import select, func
        from app.models.asset import Asset
        
        # Build base query with context filtering
        # SECURITY: Always enforce multi-tenancy - no platform admin bypass for regular users
        # Regular users see only their context assets
        query = select(Asset).where(
            Asset.client_account_id == context.client_account_id,
            Asset.engagement_id == context.engagement_id
        ).order_by(Asset.created_at.desc())
        
        # Get total count with proper context filtering
        count_query = select(func.count()).select_from(Asset).where(
            Asset.client_account_id == context.client_account_id,
            Asset.engagement_id == context.engagement_id
        )
        count_result = await db.execute(count_query)
        total_items = count_result.scalar() or 0
        
        # Calculate pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        assets = result.scalars().all()
        
        # Calculate totals
        total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0
        
        # Build response - optimize by pre-calculating summary stats
        # Convert assets to dicts first to avoid multiple attribute access
        asset_dicts = []
        for asset in assets:
            asset_dicts.append({
                "id": str(asset.id),
                "name": asset.name,
                "asset_type": asset.asset_type,
                "environment": asset.environment,
                "criticality": asset.criticality,
                "status": asset.status,
                "six_r_strategy": asset.six_r_strategy,
                "migration_wave": asset.migration_wave,
                "application_name": asset.application_name,
                "hostname": asset.hostname,
                "operating_system": asset.operating_system,
                "cpu_cores": asset.cpu_cores,
                "memory_gb": asset.memory_gb,
                "storage_gb": asset.storage_gb,
                "created_at": asset.created_at.isoformat() if asset.created_at else None,
                "updated_at": asset.updated_at.isoformat() if asset.updated_at else None
            })
        
        # Calculate summary stats efficiently using the dictionaries
        summary_stats = {
            "total": total_items,
            "filtered": total_items,
            "applications": 0,
            "servers": 0,
            "databases": 0,
            "devices": 0,
            "unknown": 0,
            "discovered": 0,
            "pending": 0,
            "device_breakdown": {}
        }
        
        # Debug logging to understand asset types
        logger.info(f"🔍 Asset Inventory Debug: Found {len(asset_dicts)} assets")
        asset_types_found = {}
        unclassified_count = 0
        for asset_dict in asset_dicts:
            asset_type = asset_dict.get('asset_type')
            if asset_type:
                asset_types_found[asset_type] = asset_types_found.get(asset_type, 0) + 1
            else:
                unclassified_count += 1
        logger.info(f"🔍 Asset types in database: {asset_types_found}")
        logger.info(f"🔍 Unclassified assets: {unclassified_count}")
        
        # Check if assets need CrewAI classification
        needs_classification = (
            unclassified_count > 0 or 
            len(asset_types_found) == 0 or 
            all(asset_type in ['unknown', 'other', None] for asset_type in asset_types_found.keys())
        )
        
        if needs_classification and len(asset_dicts) > 0:
            logger.warning(f"🚨 Assets need CrewAI classification: {unclassified_count} unclassified, types found: {asset_types_found}")
            # Add a header to indicate assets need classification
            # Note: The actual classification will be triggered by the frontend refresh button
        
        # Single pass through assets for counting
        for asset_dict in asset_dicts:
            asset_type = (asset_dict.get('asset_type') or '').lower()
            status = asset_dict.get('status')
            
            if asset_type == 'application':
                summary_stats['applications'] += 1
            elif asset_type == 'server':
                summary_stats['servers'] += 1
            elif asset_type == 'database':
                summary_stats['databases'] += 1
            elif any(term in asset_type for term in ['device', 'network', 'storage', 'security', 'infrastructure']):
                summary_stats['devices'] += 1
            elif not asset_type or asset_type == 'unknown':
                summary_stats['unknown'] += 1
                
            if status == 'discovered':
                summary_stats['discovered'] += 1
            elif status == 'pending':
                summary_stats['pending'] += 1
        
        # Find last updated efficiently
        last_updated = None
        for asset_dict in asset_dicts:
            if asset_dict.get('updated_at') and (not last_updated or asset_dict['updated_at'] > last_updated):
                last_updated = asset_dict['updated_at']
        
        return {
            "assets": asset_dicts,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            },
            "summary": summary_stats,
            "needs_classification": needs_classification,
            "last_updated": last_updated,
            "data_source": "database",
            "suggested_headers": [],
            "app_mappings": [],
            "unlinked_assets": [],
            "unlinked_summary": {
                "total_unlinked": 0,
                "by_type": {},
                "by_environment": {},
                "by_criticality": {},
                "migration_impact": "none"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in list_assets_paginated: {e}")
        # Return empty result on error
        return {
            "assets": [],
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_items": 0,
                "total_pages": 0,
                "has_next": False,
                "has_previous": False
            },
            "summary": {
                "total": 0,
                "filtered": 0,
                "applications": 0,
                "servers": 0,
                "databases": 0,
                "devices": 0,
                "unknown": 0,
                "discovered": 0,
                "pending": 0,
                "device_breakdown": {}
            },
            "last_updated": None,
            "data_source": "error",
            "suggested_headers": [],
            "app_mappings": [],
            "unlinked_assets": [],
            "unlinked_summary": {
                "total_unlinked": 0,
                "by_type": {},
                "by_environment": {},
                "by_criticality": {},
                "migration_impact": "none"
            }
        }

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

@router.get("/analysis/overview", response_model=Dict[str, Any])
async def get_asset_overview(
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    repo = AssetRepository(db, context.client_account_id)
    return await repo.get_asset_overview()

@router.get("/analysis/by-type", response_model=Dict[str, int])
async def get_assets_by_type(
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    repo = AssetRepository(db, context.client_account_id)
    return await repo.get_assets_by_type()

@router.get("/analysis/by-status", response_model=Dict[str, int])
async def get_assets_by_status(
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    repo = AssetRepository(db, context.client_account_id)
    return await repo.get_assets_by_status() 