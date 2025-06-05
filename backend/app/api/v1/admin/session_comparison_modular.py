"""
Session Comparison API - Modular Implementation
Admin endpoints for session comparison and analysis.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac_middleware import require_admin_access

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin/session-comparison", tags=["Session Comparison"])

@router.get("/health")
async def session_comparison_health():
    """Health check for session comparison service."""
    return {
        "status": "healthy",
        "service": "session-comparison-modular",
        "version": "2.0.0",
        "capabilities": {
            "session_comparison": True,
            "diff_analysis": True,
            "metrics_tracking": True,
            "modular_architecture": True
        }
    }

@router.get("/engagement/{engagement_id}/sessions")
async def get_sessions_for_comparison(
    engagement_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Get sessions available for comparison."""
    try:
        # Demo data
        demo_sessions = [
            {
                "session_id": "1",
                "session_name": "Initial Discovery Session",
                "created_at": "2025-01-10T10:30:00Z",
                "status": "completed",
                "total_assets": 1250,
                "quality_score": 78.5,
                "estimated_cost_savings": 2500000,
                "processing_time_hours": 2.5,
                "can_compare": True
            },
            {
                "session_id": "2",
                "session_name": "Enhanced Data Import",
                "created_at": "2025-01-15T14:20:00Z",
                "status": "completed",
                "total_assets": 1380,
                "quality_score": 85.2,
                "estimated_cost_savings": 2750000,
                "processing_time_hours": 3.1,
                "can_compare": True
            }
        ]
        
        return {
            "success": True,
            "data": {
                "sessions": demo_sessions
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting sessions for comparison: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")

@router.post("/compare")
async def perform_session_comparison(
    comparison_request: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Perform session comparison."""
    try:
        source_session_id = comparison_request.get("source_session_id")
        target_session_id = comparison_request.get("target_session_id")
        comparison_type = comparison_request.get("comparison_type", "full_comparison")
        
        if not source_session_id or not target_session_id:
            raise HTTPException(status_code=400, detail="Both source and target session IDs are required")
        
        # Demo comparison result
        comparison_result = {
            "comparison_id": f"comp_{source_session_id}_{target_session_id}",
            "source_session_id": source_session_id,
            "target_session_id": target_session_id,
            "comparison_type": comparison_type,
            "generated_at": "2025-01-16T10:00:00Z",
            "summary": {
                "total_metrics_compared": 15,
                "significant_changes": [
                    {"metric": "Quality Score", "change": 6.7, "direction": "improvement"},
                    {"metric": "Total Assets", "change": 130, "direction": "improvement"},
                    {"metric": "Cost Savings", "change": 250000, "direction": "improvement"}
                ],
                "overall_improvement": 8.5,
                "overall_regression": 1.2,
                "source_session": "Initial Discovery Session",
                "target_session": "Enhanced Data Import"
            },
            "key_metrics_diff": {
                "quality_score": {
                    "source_value": 78.5,
                    "target_value": 85.2,
                    "difference": 6.7,
                    "percentage_change": 8.5,
                    "improvement": True
                },
                "total_assets": {
                    "source_value": 1250,
                    "target_value": 1380,
                    "difference": 130,
                    "percentage_change": 10.4,
                    "improvement": True
                }
            },
            "assets_added_count": 130,
            "assets_removed_count": 0,
            "assets_modified_count": 45,
            "assets_unchanged_count": 1205
        }
        
        return {
            "success": True,
            "data": comparison_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing session comparison: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to perform comparison: {str(e)}")

@router.get("/history")
async def get_comparison_history(
    engagement_id: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Get comparison history."""
    try:
        # Demo data
        demo_history = [
            {
                "comparison_id": "comp_1_2",
                "source_session_name": "Initial Discovery Session",
                "target_session_name": "Enhanced Data Import",
                "comparison_type": "full_comparison",
                "created_at": "2025-01-16T09:00:00Z",
                "created_by": admin_user,
                "key_findings": [
                    "Quality score improved by 8.5%",
                    "130 new assets discovered",
                    "Cost savings increased by $250,000"
                ]
            }
        ]
        
        return {
            "items": demo_history,
            "total": len(demo_history),
            "page": page,
            "page_size": page_size,
            "total_pages": 1
        }
        
    except Exception as e:
        logger.error(f"Error getting comparison history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get comparison history: {str(e)}")

@router.get("/comparisons/{comparison_id}/details")
async def get_detailed_comparison(
    comparison_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Get detailed comparison analysis."""
    try:
        # Demo detailed comparison
        detailed_comparison = {
            "comparison_id": comparison_id,
            "generated_at": "2025-01-16T09:00:00Z",
            "detailed_metrics": {
                "asset_changes": {
                    "added": 130,
                    "removed": 0,
                    "modified": 45,
                    "unchanged": 1205
                },
                "quality_improvements": {
                    "data_completeness": 5.2,
                    "field_accuracy": 3.8,
                    "consistency_score": 2.1
                },
                "business_impact": {
                    "cost_savings_change": 250000,
                    "risk_reduction": 2.3,
                    "complexity_increase": 1.5
                }
            }
        }
        
        return {
            "success": True,
            "data": detailed_comparison
        }
        
    except Exception as e:
        logger.error(f"Error getting detailed comparison: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get detailed comparison: {str(e)}") 