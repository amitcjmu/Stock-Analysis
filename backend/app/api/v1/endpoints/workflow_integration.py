"""
Workflow Integration Endpoints
Provides API endpoints for integrating field mapping and data cleanup with workflow advancement.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.field_mapper_modular import field_mapper
from app.services.data_cleanup_service import data_cleanup_service
from app.services.workflow_service import WorkflowService
from app.repositories.asset_repository import AssetRepository

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/mapping/batch-process")
async def process_field_mapping_batch(
    mapping_request: Dict[str, Any],
    client_account_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Process a batch of assets for field mapping with automatic workflow advancement.
    
    Request body:
    {
        "asset_ids": ["asset-1", "asset-2"],
        "mapping_operations": ["analyze_columns", "suggest_mappings"],
        "auto_advance_workflow": true
    }
    """
    try:
        asset_ids = mapping_request.get("asset_ids", [])
        auto_advance = mapping_request.get("auto_advance_workflow", True)
        
        if not asset_ids:
            raise HTTPException(status_code=400, detail="No asset IDs provided")
        
        # Get assets from database
        asset_repo = AssetRepository(db, client_account_id, engagement_id)
        assets = []
        
        for asset_id in asset_ids:
            asset = await asset_repo.get_by_id(asset_id)
            if asset:
                assets.append(asset.__dict__)
            else:
                logger.warning(f"Asset {asset_id} not found")
        
        if not assets:
            raise HTTPException(status_code=404, detail="No valid assets found")
        
        # Process field mapping with workflow integration
        if auto_advance:
            mapping_results = await field_mapper.process_field_mapping_batch(
                assets, client_account_id, engagement_id
            )
        else:
            # Process mapping without workflow advancement
            mapping_results = {
                "total_assets": len(assets),
                "successfully_mapped": len(assets),
                "mapping_completeness": {},
                "workflow_updates": []
            }
            
            for asset in assets:
                asset_columns = list(asset.keys())
                mapping_analysis = field_mapper.analyze_columns(asset_columns)
                completeness = field_mapper._calculate_mapping_completeness(asset, mapping_analysis)
                mapping_results["mapping_completeness"][asset.get('id', 'unknown')] = completeness
        
        return {
            "status": "success",
            "message": f"Processed {len(assets)} assets for field mapping",
            "results": mapping_results
        }
        
    except Exception as e:
        logger.error(f"Error in batch field mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Field mapping failed: {str(e)}")

@router.post("/mapping/update-from-user")
async def update_field_mapping_from_user(
    mapping_request: Dict[str, Any],
    client_account_id: Optional[str] = None,
    engagement_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update field mappings based on user input with workflow advancement.
    
    Request body:
    {
        "asset_id": "asset-123",
        "field_mappings": {
            "src_hostname": "hostname",
            "src_env": "environment",
            "src_dept": "department"
        },
        "auto_advance_workflow": true
    }
    """
    try:
        asset_id = mapping_request.get("asset_id")
        field_mappings = mapping_request.get("field_mappings", {})
        auto_advance = mapping_request.get("auto_advance_workflow", True)
        
        if not asset_id:
            raise HTTPException(status_code=400, detail="Asset ID is required")
        
        if not field_mappings:
            raise HTTPException(status_code=400, detail="Field mappings are required")
        
        if auto_advance:
            # Use workflow integration
            update_result = await field_mapper.update_field_mapping_from_user_input(
                field_mappings, asset_id, client_account_id, engagement_id
            )
        else:
            # Update without workflow advancement
            learning_results = []
            for source_field, target_field in field_mappings.items():
                learn_result = field_mapper.learn_field_mapping(target_field, [source_field], "user_mapping")
                learning_results.append(learn_result)
            
            update_result = {
                "success": True,
                "mappings_learned": len(learning_results),
                "learning_results": learning_results,
                "workflow_result": "disabled"
            }
        
        return {
            "status": "success",
            "message": f"Updated field mappings for asset {asset_id}",
            "results": update_result
        }
        
    except Exception as e:
        logger.error(f"Error updating field mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Field mapping update failed: {str(e)}")

@router.get("/mapping/assess-readiness")
async def assess_mapping_readiness(
    client_account_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Assess overall mapping readiness across all assets.
    """
    try:
        # Get all assets for assessment
        asset_repo = AssetRepository(db, client_account_id, engagement_id)
        assets = await asset_repo.get_all()
        
        # Convert to dictionaries for assessment
        asset_data = [asset.__dict__ for asset in assets]
        
        # Assess mapping readiness
        readiness_assessment = field_mapper.assess_mapping_readiness(asset_data)
        
        return {
            "status": "success",
            "message": "Mapping readiness assessment completed",
            "assessment": readiness_assessment
        }
        
    except Exception as e:
        logger.error(f"Error assessing mapping readiness: {e}")
        raise HTTPException(status_code=500, detail=f"Mapping readiness assessment failed: {str(e)}")

@router.post("/cleanup/batch-process")
async def process_data_cleanup_batch(
    cleanup_request: Dict[str, Any],
    client_account_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Process a batch of assets for data cleanup with automatic workflow advancement.
    
    Request body:
    {
        "asset_ids": ["asset-1", "asset-2"],
        "cleanup_operations": [
            "standardize_asset_types",
            "normalize_environments",
            "fix_hostnames",
            "complete_missing_fields"
        ],
        "auto_advance_workflow": true
    }
    """
    try:
        asset_ids = cleanup_request.get("asset_ids", [])
        cleanup_operations = cleanup_request.get("cleanup_operations", [])
        auto_advance = cleanup_request.get("auto_advance_workflow", True)
        
        if not asset_ids:
            raise HTTPException(status_code=400, detail="No asset IDs provided")
        
        if not cleanup_operations:
            raise HTTPException(status_code=400, detail="No cleanup operations specified")
        
        # Get assets from database
        asset_repo = AssetRepository(db, client_account_id, engagement_id)
        assets = []
        
        for asset_id in asset_ids:
            asset = await asset_repo.get_by_id(asset_id)
            if asset:
                assets.append(asset.__dict__)
            else:
                logger.warning(f"Asset {asset_id} not found")
        
        if not assets:
            raise HTTPException(status_code=404, detail="No valid assets found")
        
        # Process data cleanup with workflow integration
        if auto_advance:
            cleanup_results = await data_cleanup_service.process_data_cleanup_batch(
                assets, cleanup_operations, client_account_id, engagement_id
            )
        else:
            # Process cleanup without workflow advancement
            cleanup_results = {
                "total_assets": len(assets),
                "successfully_cleaned": 0,
                "quality_improvements": {},
                "workflow_updates": []
            }
            
            for asset in assets:
                original_quality = data_cleanup_service._calculate_data_quality(asset)
                cleaned_asset = data_cleanup_service._apply_cleanup_operations(asset, cleanup_operations)
                improved_quality = data_cleanup_service._calculate_data_quality(cleaned_asset)
                
                cleanup_results["quality_improvements"][asset.get('id', 'unknown')] = {
                    "original_quality": original_quality,
                    "improved_quality": improved_quality,
                    "improvement": improved_quality - original_quality
                }
                cleanup_results["successfully_cleaned"] += 1
        
        return {
            "status": "success",
            "message": f"Processed {len(assets)} assets for data cleanup",
            "results": cleanup_results
        }
        
    except Exception as e:
        logger.error(f"Error in batch data cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Data cleanup failed: {str(e)}")

@router.get("/cleanup/assess-readiness")
async def assess_cleanup_readiness(
    client_account_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Assess overall cleanup readiness across all assets.
    """
    try:
        # Get all assets for assessment
        asset_repo = AssetRepository(db, client_account_id, engagement_id)
        assets = await asset_repo.get_all()
        
        # Convert to dictionaries for assessment
        asset_data = [asset.__dict__ for asset in assets]
        
        # Assess cleanup readiness
        readiness_assessment = data_cleanup_service.assess_cleanup_readiness(asset_data)
        
        return {
            "status": "success",
            "message": "Cleanup readiness assessment completed",
            "assessment": readiness_assessment
        }
        
    except Exception as e:
        logger.error(f"Error assessing cleanup readiness: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup readiness assessment failed: {str(e)}")

@router.get("/assessment-readiness")
async def check_assessment_readiness(
    client_account_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check overall assessment readiness by combining mapping, cleanup, and workflow status.
    """
    try:
        # Get workflow service for comprehensive assessment
        workflow_service = WorkflowService(db, client_account_id, engagement_id)
        
        # Get comprehensive workflow summary
        workflow_summary = await workflow_service.get_workflow_summary()
        
        # Get asset repository for detailed assessment
        asset_repo = AssetRepository(db, client_account_id, engagement_id)
        assets = await asset_repo.get_all()
        asset_data = [asset.__dict__ for asset in assets]
        
        # Get mapping readiness
        mapping_readiness = field_mapper.assess_mapping_readiness(asset_data)
        
        # Get cleanup readiness
        cleanup_readiness = data_cleanup_service.assess_cleanup_readiness(asset_data)
        
        # Determine overall assessment readiness
        mapping_ready = mapping_readiness.get("ready_percentage", 0) >= 80
        cleanup_ready = cleanup_readiness.get("ready_percentage", 0) >= 70
        workflow_ready = workflow_summary.get("assessment_readiness_percentage", 0) >= 75
        
        overall_ready = mapping_ready and cleanup_ready and workflow_ready
        
        # Generate next steps
        next_steps = []
        if not mapping_ready:
            next_steps.extend(mapping_readiness.get("recommendations", [])[:2])
        if not cleanup_ready:
            next_steps.extend(cleanup_readiness.get("recommendations", [])[:2])
        if not workflow_ready:
            next_steps.append("Complete remaining workflow phases for more assets")
        
        if overall_ready:
            next_steps = ["Ready to proceed to Assessment phase! Begin 6R strategy analysis."]
        
        return {
            "status": "success",
            "overall_ready": overall_ready,
            "assessment_readiness": {
                "mapping": {
                    "ready": mapping_ready,
                    "percentage": mapping_readiness.get("ready_percentage", 0),
                    "threshold": 80
                },
                "cleanup": {
                    "ready": cleanup_ready,
                    "percentage": cleanup_readiness.get("ready_percentage", 0),
                    "threshold": 70
                },
                "workflow": {
                    "ready": workflow_ready,
                    "percentage": workflow_summary.get("assessment_readiness_percentage", 0),
                    "threshold": 75
                }
            },
            "detailed_assessments": {
                "mapping_readiness": mapping_readiness,
                "cleanup_readiness": cleanup_readiness,
                "workflow_summary": workflow_summary
            },
            "next_steps": next_steps,
            "summary": {
                "total_assets": len(asset_data),
                "ready_for_assessment": sum([
                    mapping_readiness.get("ready_assets", 0),
                    cleanup_readiness.get("ready_assets", 0)
                ]) // 2,  # Average of the two readiness measures
                "priority_actions": len(next_steps)
            }
        }
        
    except Exception as e:
        logger.error(f"Error checking assessment readiness: {e}")
        raise HTTPException(status_code=500, detail=f"Assessment readiness check failed: {str(e)}")

@router.post("/bulk-advance-workflow")
async def bulk_advance_workflow(
    advance_request: Dict[str, Any],
    client_account_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Bulk advance assets through workflow phases based on readiness criteria.
    
    Request body:
    {
        "phase": "mapping",  // or "cleanup" or "assessment"
        "criteria": {
            "min_completeness": 80.0,
            "min_quality": 70.0
        }
    }
    """
    try:
        target_phase = advance_request.get("phase")
        criteria = advance_request.get("criteria", {})
        
        if not target_phase:
            raise HTTPException(status_code=400, detail="Target phase is required")
        
        if target_phase not in ["mapping", "cleanup", "assessment"]:
            raise HTTPException(status_code=400, detail="Invalid phase. Must be 'mapping', 'cleanup', or 'assessment'")
        
        # Get workflow service
        workflow_service = WorkflowService(db, client_account_id, engagement_id)
        
        # Get all assets
        asset_repo = AssetRepository(db, client_account_id, engagement_id)
        assets = await asset_repo.get_all()
        
        advancement_results = {
            "total_assets": len(assets),
            "eligible_assets": 0,
            "advanced_assets": 0,
            "advancement_errors": [],
            "asset_details": []
        }
        
        min_completeness = criteria.get("min_completeness", 80.0)
        min_quality = criteria.get("min_quality", 70.0)
        
        for asset in assets:
            try:
                # Check if asset meets criteria for advancement
                eligible = False
                
                if target_phase == "mapping":
                    # Check if discovery is complete and asset has sufficient data
                    if (asset.discovery_status == "completed" and
                        (asset.completeness_score or 0) >= min_completeness):
                        eligible = True
                
                elif target_phase == "cleanup":
                    # Check if mapping is complete and asset has good completeness
                    if (asset.mapping_status == "completed" and
                        (asset.completeness_score or 0) >= min_completeness):
                        eligible = True
                
                elif target_phase == "assessment":
                    # Check if cleanup is complete and quality is good
                    if (asset.cleanup_status == "completed" and
                        (asset.quality_score or 0) >= min_quality and
                        (asset.completeness_score or 0) >= min_completeness):
                        eligible = True
                
                if eligible:
                    advancement_results["eligible_assets"] += 1
                    
                    # Advance the asset workflow
                    advance_result = await workflow_service.advance_asset_workflow(
                        asset.id, target_phase, f"Bulk advancement to {target_phase} phase"
                    )
                    
                    if advance_result.get("success"):
                        advancement_results["advanced_assets"] += 1
                        advancement_results["asset_details"].append({
                            "asset_id": asset.id,
                            "asset_name": asset.name,
                            "status": "advanced",
                            "new_phase": target_phase
                        })
                    else:
                        advancement_results["advancement_errors"].append({
                            "asset_id": asset.id,
                            "error": advance_result.get("message", "Unknown error")
                        })
                else:
                    advancement_results["asset_details"].append({
                        "asset_id": asset.id,
                        "asset_name": asset.name,
                        "status": "not_eligible",
                        "reason": f"Does not meet criteria for {target_phase} phase"
                    })
                    
            except Exception as e:
                logger.error(f"Error advancing asset {asset.id}: {e}")
                advancement_results["advancement_errors"].append({
                    "asset_id": asset.id,
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "message": f"Bulk workflow advancement completed for {target_phase} phase",
            "results": advancement_results
        }
        
    except Exception as e:
        logger.error(f"Error in bulk workflow advancement: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk workflow advancement failed: {str(e)}")

@router.get("/health")
async def workflow_integration_health():
    """Health check for workflow integration endpoints."""
    return {
        "status": "healthy",
        "service": "workflow-integration",
        "version": "1.0.0",
        "components": {
            "field_mapper": field_mapper.is_available(),
            "data_cleanup": data_cleanup_service.is_available(),
            "workflow_service": True  # Workflow service availability checked during request
        },
        "available_endpoints": [
            "/mapping/batch-process",
            "/mapping/update-from-user", 
            "/mapping/assess-readiness",
            "/cleanup/batch-process",
            "/cleanup/assess-readiness",
            "/assessment-readiness",
            "/bulk-advance-workflow",
            "/health"
        ]
    } 