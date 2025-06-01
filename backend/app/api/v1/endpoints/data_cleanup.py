"""
Data Cleanup API Endpoints - Agentic Intelligence
Provides AI-powered data quality assessment and intelligent cleanup recommendations.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.agent_ui_bridge import agent_ui_bridge
from app.services.data_cleanup_service import DataCleanupService

logger = logging.getLogger(__name__)

router = APIRouter()
data_cleanup_service = DataCleanupService()

@router.post("/agent-analyze")
async def analyze_data_quality_with_agents(
    request_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Agent-driven data quality assessment with intelligent prioritization.
    
    Request body:
    {
        "asset_data": [...],
        "page_context": "data-cleansing",
        "client_account_id": null,
        "engagement_id": null
    }
    """
    try:
        asset_data = request_data.get("asset_data", [])
        page_context = request_data.get("page_context", "data-cleansing")
        client_account_id = request_data.get("client_account_id")
        engagement_id = request_data.get("engagement_id")
        
        if not asset_data:
            return {
                "analysis_type": "no_data",
                "total_assets": 0,
                "quality_assessment": {},
                "priority_issues": [],
                "cleansing_recommendations": [],
                "quality_buckets": {
                    "clean_data": 0,
                    "needs_attention": 0,
                    "critical_issues": 0
                },
                "agent_confidence": 0.0,
                "agent_insights": ["No data available for analysis"],
                "suggested_operations": []
            }
        
        # Perform agent-driven quality analysis
        analysis_result = await data_cleanup_service.agent_analyze_data_quality(
            asset_data=asset_data,
            page_context=page_context,
            client_account_id=client_account_id,
            engagement_id=engagement_id
        )
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error in agent data quality analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Data quality analysis failed: {str(e)}")

@router.post("/agent-process")
async def process_data_with_agents(
    request_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Agent-driven data processing with intelligent cleanup operations.
    
    Request body:
    {
        "asset_data": [...],
        "agent_operations": [...],
        "user_preferences": {...},
        "client_account_id": null,
        "engagement_id": null
    }
    """
    try:
        asset_data = request_data.get("asset_data", [])
        agent_operations = request_data.get("agent_operations", [])
        user_preferences = request_data.get("user_preferences", {})
        client_account_id = request_data.get("client_account_id")
        engagement_id = request_data.get("engagement_id")
        
        if not asset_data:
            raise HTTPException(status_code=400, detail="Asset data is required for processing")
        
        # Perform agent-driven cleanup
        cleanup_result = await data_cleanup_service.agent_process_data_cleanup(
            asset_data=asset_data,
            agent_operations=agent_operations,
            user_preferences=user_preferences,
            client_account_id=client_account_id,
            engagement_id=engagement_id
        )
        
        return cleanup_result
        
    except Exception as e:
        logger.error(f"Error in agent data processing: {e}")
        raise HTTPException(status_code=500, detail=f"Data processing failed: {str(e)}")

@router.get("/quality-issues")
async def get_quality_issues(
    client_account_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
    page_context: str = "data-cleansing",
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current data quality issues for stored assets.
    """
    try:
        # Get persisted asset data for quality analysis
        from app.repositories.asset_repository import AssetRepository
        
        if client_account_id:
            asset_repo = AssetRepository(db, int(client_account_id))
        else:
            # Fallback for development
            asset_repo = AssetRepository(db, 1)
        
        assets = await asset_repo.get_all_assets()
        
        if not assets:
            return {
                "status": "no_data",
                "total_assets": 0,
                "quality_issues": [],
                "recommendations": []
            }
        
        # Convert to analysis format
        asset_data = []
        for asset in assets:
            asset_dict = {
                "id": asset.id,
                "asset_name": asset.asset_name,
                "hostname": asset.hostname,
                "asset_type": asset.asset_type.value if asset.asset_type else None,
                "environment": asset.environment,
                "department": asset.department,
                "ip_address": asset.ip_address,
                "operating_system": asset.operating_system
            }
            asset_data.append(asset_dict)
        
        # Analyze quality
        analysis_result = await data_cleanup_service.agent_analyze_data_quality(
            asset_data=asset_data,
            page_context=page_context,
            client_account_id=client_account_id,
            engagement_id=engagement_id
        )
        
        return {
            "status": "success",
            "total_assets": len(asset_data),
            "quality_analysis": analysis_result,
            "priority_issues": analysis_result.get("priority_issues", []),
            "recommendations": analysis_result.get("cleansing_recommendations", [])
        }
        
    except Exception as e:
        logger.error(f"Error getting quality issues: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quality issues: {str(e)}")

@router.get("/health")
async def get_data_cleanup_health() -> Dict[str, Any]:
    """Get health status of data cleanup service."""
    try:
        return data_cleanup_service.get_health_status()
    except Exception as e:
        logger.error(f"Error getting data cleanup health: {e}")
        return {"status": "error", "error": str(e)} 