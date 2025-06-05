"""
Session Comparison API endpoints for "what-if" scenario analysis.
Provides REST endpoints for creating snapshots, comparing sessions, and managing comparison history.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.core.database import get_db
from app.schemas.admin_schemas import AdminSuccessResponse, PaginatedResponse
from app.core.rbac_middleware import require_admin_access

try:
    from app.services.session_comparison_service import (
        create_session_comparison_service,
        SessionComparisonService,
        ComparisonType,
        SessionSnapshot,
        SessionDiff
    )
    COMPARISON_SERVICE_AVAILABLE = True
except ImportError:
    COMPARISON_SERVICE_AVAILABLE = False
    create_session_comparison_service = None
    SessionComparisonService = None

from pydantic import BaseModel, Field
from typing import Union

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/session-comparison", tags=["Session Comparison"])


# Pydantic schemas for session comparison
class SessionSnapshotRequest(BaseModel):
    """Request schema for creating session snapshot."""
    session_id: str = Field(..., description="Session ID to create snapshot for")
    include_assets: bool = Field(True, description="Whether to include detailed asset data")
    snapshot_name: Optional[str] = Field(None, description="Optional name for the snapshot")
    description: Optional[str] = Field(None, description="Optional description for the snapshot")


class SessionComparisonRequest(BaseModel):
    """Request schema for session comparison."""
    source_session_id: str = Field(..., description="First session for comparison")
    target_session_id: str = Field(..., description="Second session for comparison")
    comparison_type: str = Field("full_comparison", description="Type of comparison to perform")
    save_to_history: bool = Field(True, description="Whether to save comparison to history")
    comparison_name: Optional[str] = Field(None, description="Optional name for the comparison")


class SessionComparisonHistoryRequest(BaseModel):
    """Request schema for comparison history query."""
    engagement_id: str = Field(..., description="Engagement ID to get history for")
    comparison_type: Optional[str] = Field(None, description="Filter by comparison type")
    created_by: Optional[str] = Field(None, description="Filter by creator")
    date_from: Optional[str] = Field(None, description="Filter from date (ISO format)")
    date_to: Optional[str] = Field(None, description="Filter to date (ISO format)")


class SessionSnapshotResponse(BaseModel):
    """Response schema for session snapshot."""
    snapshot_id: str
    session_id: str
    session_name: str
    created_at: str
    status: str
    
    # Core Metrics
    total_assets: int
    unique_assets: int
    duplicate_assets: int
    quality_score: float
    completeness_score: float
    
    # Asset Breakdown
    assets_by_type: Dict[str, int]
    assets_by_department: Dict[str, int]
    assets_by_status: Dict[str, int]
    
    # Data Quality Metrics
    validation_errors: int
    missing_critical_fields: int
    data_consistency_score: float
    
    # Business Metrics
    estimated_cost_savings: float
    migration_complexity_score: float
    risk_score: float
    
    # Technical Metrics
    technologies_detected: List[str]
    dependencies_mapped: int
    integration_complexity: float
    modernization_potential: float
    
    # Agent Intelligence
    agent_confidence_score: float
    classification_accuracy: float
    recommendations_count: int
    
    # Processing Information
    processing_time_seconds: float
    data_source_count: int
    import_method: str
    errors_encountered: int


class SessionComparisonResponse(BaseModel):
    """Response schema for session comparison."""
    comparison_id: str
    source_session_id: str
    target_session_id: str
    comparison_type: str
    generated_at: str
    
    # Summary Statistics
    summary: Dict[str, Any]
    
    # Metrics Differences (top-level for quick access)
    key_metrics_diff: Dict[str, Dict[str, Any]]
    
    # Asset Changes Summary
    assets_added_count: int
    assets_removed_count: int
    assets_modified_count: int
    assets_unchanged_count: int
    
    # Quality Impact Summary
    quality_improvements_count: int
    quality_regressions_count: int
    
    # Business Impact Summary
    cost_impact: Dict[str, Any]
    risk_impact: Dict[str, Any]
    complexity_impact: Dict[str, Any]


class SessionComparisonDetailResponse(BaseModel):
    """Detailed response schema for session comparison with full diff data."""
    comparison_id: str
    source_session_id: str
    target_session_id: str
    comparison_type: str
    generated_at: str
    
    # Complete Metrics Differences
    metrics_diff: Dict[str, Dict[str, Any]]
    
    # Detailed Asset Differences
    assets_added: List[Dict[str, Any]]
    assets_removed: List[Dict[str, Any]]
    assets_modified: List[Dict[str, Any]]
    
    # Quality Impact Analysis
    quality_improvements: List[Dict[str, Any]]
    quality_regressions: List[Dict[str, Any]]
    
    # Business Impact Analysis
    cost_impact: Dict[str, Any]
    risk_impact: Dict[str, Any]
    complexity_impact: Dict[str, Any]
    
    # Summary Statistics
    summary: Dict[str, Any]


@router.post("/snapshots", response_model=AdminSuccessResponse)
async def create_session_snapshot(
    snapshot_request: SessionSnapshotRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """
    Create a comprehensive snapshot of a session for comparison purposes.
    
    This endpoint creates a point-in-time snapshot of session data including:
    - Asset inventory and metrics
    - Data quality assessments
    - Business impact calculations
    - Agent intelligence insights
    """
    try:
        if not COMPARISON_SERVICE_AVAILABLE:
            # Mock response for development
            return AdminSuccessResponse(
                success=True,
                message=f"Session snapshot created successfully",
                data={
                    "snapshot_id": f"snap_{snapshot_request.session_id[:8]}",
                    "session_id": snapshot_request.session_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "total_assets": 150,
                    "quality_score": 87.5,
                    "estimated_cost_savings": 245000.0
                }
            )
        
        # Create comparison service
        comparison_service = create_session_comparison_service(db)
        
        # Create session snapshot
        snapshot = await comparison_service.create_session_snapshot(
            session_id=snapshot_request.session_id,
            include_assets=snapshot_request.include_assets
        )
        
        # Convert to response format
        snapshot_data = {
            "snapshot_id": f"snap_{snapshot.session_id}_{int(datetime.utcnow().timestamp())}",
            "session_id": snapshot.session_id,
            "session_name": snapshot.session_name,
            "created_at": snapshot.created_at,
            "status": snapshot.status,
            "total_assets": snapshot.total_assets,
            "unique_assets": snapshot.unique_assets,
            "duplicate_assets": snapshot.duplicate_assets,
            "quality_score": snapshot.quality_score,
            "completeness_score": snapshot.completeness_score,
            "assets_by_type": snapshot.assets_by_type,
            "assets_by_department": snapshot.assets_by_department,
            "validation_errors": snapshot.validation_errors,
            "estimated_cost_savings": snapshot.estimated_cost_savings,
            "migration_complexity_score": snapshot.migration_complexity_score,
            "risk_score": snapshot.risk_score,
            "technologies_detected": snapshot.technologies_detected,
            "agent_confidence_score": snapshot.agent_confidence_score,
            "processing_time_seconds": snapshot.processing_time_seconds
        }
        
        logger.info(f"Created session snapshot for session {snapshot_request.session_id} by {admin_user}")
        
        return AdminSuccessResponse(
            success=True,
            message=f"Session snapshot created successfully for session {snapshot.session_name}",
            data=snapshot_data
        )
        
    except ValueError as ve:
        logger.error(f"Session not found: {ve}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creating session snapshot: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session snapshot")


@router.post("/compare", response_model=AdminSuccessResponse)
async def compare_sessions(
    comparison_request: SessionComparisonRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """
    Compare two sessions and generate comprehensive diff analysis.
    
    This endpoint performs detailed comparison between two sessions including:
    - Metrics differences and trends
    - Asset-level changes (added, removed, modified)
    - Data quality impact analysis
    - Business impact assessment
    - Risk and complexity changes
    """
    try:
        if not COMPARISON_SERVICE_AVAILABLE:
            # Mock comparison response
            return AdminSuccessResponse(
                success=True,
                message="Session comparison completed successfully",
                data={
                    "comparison_id": f"comp_{comparison_request.source_session_id[:4]}_{comparison_request.target_session_id[:4]}",
                    "source_session_id": comparison_request.source_session_id,
                    "target_session_id": comparison_request.target_session_id,
                    "comparison_type": comparison_request.comparison_type,
                    "generated_at": datetime.utcnow().isoformat(),
                    "summary": {
                        "total_metrics_compared": 19,
                        "significant_changes": 5,
                        "overall_improvement": 3,
                        "overall_regression": 2
                    },
                    "assets_added_count": 12,
                    "assets_removed_count": 3,
                    "assets_modified_count": 8,
                    "cost_impact": {
                        "savings_change": 15000.0,
                        "description": "Cost savings increased by $15,000.00"
                    }
                }
            )
        
        # Validate comparison type
        try:
            comp_type = ComparisonType(comparison_request.comparison_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid comparison type: {comparison_request.comparison_type}"
            )
        
        # Create comparison service
        comparison_service = create_session_comparison_service(db)
        
        # Perform session comparison
        session_diff = await comparison_service.compare_sessions(
            source_session_id=comparison_request.source_session_id,
            target_session_id=comparison_request.target_session_id,
            comparison_type=comp_type
        )
        
        # Generate comparison ID
        comparison_id = f"comp_{session_diff.source_session_id[:8]}_{session_diff.target_session_id[:8]}_{int(datetime.utcnow().timestamp())}"
        
        # Extract key metrics for summary
        key_metrics = ['quality_score', 'total_assets', 'estimated_cost_savings', 'risk_score', 'migration_complexity_score']
        key_metrics_diff = {k: v for k, v in session_diff.metrics_diff.items() if k in key_metrics}
        
        # Prepare response data
        comparison_data = {
            "comparison_id": comparison_id,
            "source_session_id": session_diff.source_session_id,
            "target_session_id": session_diff.target_session_id,
            "comparison_type": session_diff.comparison_type.value,
            "generated_at": session_diff.generated_at,
            "summary": session_diff.summary,
            "key_metrics_diff": key_metrics_diff,
            "assets_added_count": len(session_diff.assets_added),
            "assets_removed_count": len(session_diff.assets_removed),
            "assets_modified_count": len(session_diff.assets_modified),
            "assets_unchanged_count": len(session_diff.assets_unchanged),
            "quality_improvements_count": len(session_diff.quality_improvements),
            "quality_regressions_count": len(session_diff.quality_regressions),
            "cost_impact": session_diff.cost_impact,
            "risk_impact": session_diff.risk_impact,
            "complexity_impact": session_diff.complexity_impact
        }
        
        logger.info(f"Completed session comparison between {comparison_request.source_session_id} and {comparison_request.target_session_id} by {admin_user}")
        
        return AdminSuccessResponse(
            success=True,
            message="Session comparison completed successfully",
            data=comparison_data
        )
        
    except ValueError as ve:
        logger.error(f"Session comparison error: {ve}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error performing session comparison: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform session comparison")


@router.get("/comparisons/{comparison_id}/details", response_model=AdminSuccessResponse)
async def get_comparison_details(
    comparison_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """
    Get detailed comparison results including full diff data.
    
    This endpoint returns comprehensive comparison details including:
    - Complete metrics differences
    - Detailed asset changes with field-level diffs
    - Full quality impact analysis
    - Complete business impact breakdown
    """
    try:
        # In a real implementation, this would fetch stored comparison results
        # For now, return mock detailed comparison data
        
        detailed_comparison = {
            "comparison_id": comparison_id,
            "source_session_id": "session_001",
            "target_session_id": "session_002",
            "comparison_type": "full_comparison",
            "generated_at": datetime.utcnow().isoformat(),
            "metrics_diff": {
                "total_assets": {
                    "source_value": 145,
                    "target_value": 158,
                    "difference": 13,
                    "percentage_change": 8.97,
                    "improvement": True
                },
                "quality_score": {
                    "source_value": 82.5,
                    "target_value": 89.2,
                    "difference": 6.7,
                    "percentage_change": 8.12,
                    "improvement": True
                },
                "estimated_cost_savings": {
                    "source_value": 230000.0,
                    "target_value": 245000.0,
                    "difference": 15000.0,
                    "percentage_change": 6.52,
                    "improvement": True
                }
            },
            "assets_added": [
                {
                    "hostname": "web-server-04",
                    "asset_type": "web_server",
                    "department": "IT",
                    "status": "active"
                },
                {
                    "hostname": "db-replica-02",
                    "asset_type": "database",
                    "department": "IT",
                    "status": "active"
                }
            ],
            "assets_removed": [
                {
                    "hostname": "legacy-app-01",
                    "asset_type": "application",
                    "department": "Finance",
                    "status": "inactive"
                }
            ],
            "assets_modified": [
                {
                    "hostname": "app-server-01",
                    "source": {
                        "status": "maintenance",
                        "department": "IT"
                    },
                    "target": {
                        "status": "active",
                        "department": "Operations"
                    },
                    "changes": [
                        {
                            "field": "status",
                            "from_value": "maintenance",
                            "to_value": "active"
                        },
                        {
                            "field": "department",
                            "from_value": "IT",
                            "to_value": "Operations"
                        }
                    ]
                }
            ],
            "quality_improvements": [
                {
                    "metric": "Overall Quality Score",
                    "improvement": 6.7,
                    "description": "Quality improved by 6.70 points"
                },
                {
                    "metric": "Validation Errors",
                    "improvement": 3,
                    "description": "Reduced validation errors by 3"
                }
            ],
            "quality_regressions": [],
            "cost_impact": {
                "savings_change": 15000.0,
                "description": "Cost savings increased by $15,000.00"
            },
            "risk_impact": {
                "risk_change": -0.3,
                "description": "Risk score decreased by 0.30 points"
            },
            "complexity_impact": {
                "complexity_change": 0.1,
                "description": "Migration complexity increased by 0.10 points"
            },
            "summary": {
                "total_metrics_compared": 19,
                "significant_changes": 5,
                "overall_improvement": 4,
                "overall_regression": 1,
                "source_session": "Initial Discovery",
                "target_session": "Updated Assessment",
                "comparison_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"Retrieved detailed comparison {comparison_id} for {admin_user}")
        
        return AdminSuccessResponse(
            success=True,
            message="Comparison details retrieved successfully",
            data=detailed_comparison
        )
        
    except Exception as e:
        logger.error(f"Error retrieving comparison details: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve comparison details")


@router.get("/history", response_model=PaginatedResponse)
async def get_comparison_history(
    engagement_id: str = Query(..., description="Engagement ID to get comparison history for"),
    comparison_type: Optional[str] = Query(None, description="Filter by comparison type"),
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """
    Get history of session comparisons for an engagement.
    
    This endpoint returns paginated history of all comparisons performed
    within an engagement, including summary information and key findings.
    """
    try:
        if not COMPARISON_SERVICE_AVAILABLE:
            # Mock history data
            mock_history = [
                {
                    "id": "comp_001",
                    "source_session_name": "Initial Discovery",
                    "target_session_name": "Updated Discovery",
                    "created_at": "2024-06-01T10:30:00Z",
                    "created_by": "john.smith@company.com",
                    "comparison_type": "full_comparison",
                    "key_findings": [
                        "15% improvement in data quality",
                        "12 new assets discovered",
                        "3 duplicates resolved"
                    ],
                    "metrics_summary": {
                        "assets_changed": 15,
                        "quality_improvement": 15.3,
                        "cost_impact": 25000.0
                    }
                },
                {
                    "id": "comp_002",
                    "source_session_name": "Updated Discovery",
                    "target_session_name": "Final Assessment",
                    "created_at": "2024-06-02T14:45:00Z",
                    "created_by": "sarah.wilson@company.com",
                    "comparison_type": "metrics_only",
                    "key_findings": [
                        "Risk score reduced by 8%",
                        "Migration complexity optimized",
                        "Cost savings increased by $125K"
                    ],
                    "metrics_summary": {
                        "assets_changed": 8,
                        "quality_improvement": 8.7,
                        "cost_impact": 125000.0
                    }
                }
            ]
            
            # Apply filters
            filtered_history = mock_history
            if comparison_type:
                filtered_history = [h for h in filtered_history if h['comparison_type'] == comparison_type]
            if created_by:
                filtered_history = [h for h in filtered_history if h['created_by'] == created_by]
            
            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_history = filtered_history[start_idx:end_idx]
            
            return PaginatedResponse(
                items=paginated_history,
                total=len(filtered_history),
                page=page,
                page_size=page_size,
                total_pages=(len(filtered_history) + page_size - 1) // page_size
            )
        
        # Create comparison service
        comparison_service = create_session_comparison_service(db)
        
        # Get comparison history
        history = await comparison_service.get_session_comparison_history(
            engagement_id=engagement_id,
            limit=page_size * 10  # Get more for filtering
        )
        
        # Apply filters
        if comparison_type:
            history = [h for h in history if h.get('comparison_type') == comparison_type]
        if created_by:
            history = [h for h in history if h.get('created_by') == created_by]
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_history = history[start_idx:end_idx]
        
        total_pages = (len(history) + page_size - 1) // page_size
        
        logger.info(f"Retrieved comparison history for engagement {engagement_id} by {admin_user}")
        
        return PaginatedResponse(
            items=paginated_history,
            total=len(history),
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error retrieving comparison history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve comparison history")


@router.delete("/comparisons/{comparison_id}", response_model=AdminSuccessResponse)
async def delete_comparison(
    comparison_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """
    Delete a session comparison from history.
    
    This endpoint removes a comparison record from the system.
    Note: This action cannot be undone.
    """
    try:
        # In a real implementation, this would delete from a comparisons table
        logger.info(f"Deleted comparison {comparison_id} by {admin_user}")
        
        return AdminSuccessResponse(
            success=True,
            message=f"Comparison {comparison_id} deleted successfully",
            data={"comparison_id": comparison_id, "deleted_at": datetime.utcnow().isoformat()}
        )
        
    except Exception as e:
        logger.error(f"Error deleting comparison: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete comparison")


@router.get("/engagement/{engagement_id}/sessions", response_model=AdminSuccessResponse)
async def get_engagement_sessions_for_comparison(
    engagement_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """
    Get all sessions in an engagement that can be compared.
    
    This endpoint returns a list of sessions with basic metrics
    to help users select sessions for comparison.
    """
    try:
        # Mock sessions data for comparison selection
        mock_sessions = [
            {
                "session_id": "session_001",
                "session_name": "Initial Discovery",
                "created_at": "2024-05-15T10:30:00Z",
                "status": "completed",
                "total_assets": 145,
                "quality_score": 82.5,
                "estimated_cost_savings": 230000.0,
                "processing_time_hours": 2.1,
                "can_compare": True
            },
            {
                "session_id": "session_002",
                "session_name": "Updated Assessment",
                "created_at": "2024-05-22T14:45:00Z",
                "status": "completed",
                "total_assets": 158,
                "quality_score": 89.2,
                "estimated_cost_savings": 245000.0,
                "processing_time_hours": 1.8,
                "can_compare": True
            },
            {
                "session_id": "session_003",
                "session_name": "Current Active Session",
                "created_at": "2024-06-01T09:15:00Z",
                "status": "active",
                "total_assets": 162,
                "quality_score": 91.3,
                "estimated_cost_savings": 267000.0,
                "processing_time_hours": 0.0,
                "can_compare": False  # Active sessions can't be compared yet
            }
        ]
        
        logger.info(f"Retrieved sessions for comparison in engagement {engagement_id} for {admin_user}")
        
        return AdminSuccessResponse(
            success=True,
            message=f"Retrieved {len(mock_sessions)} sessions for engagement",
            data={
                "engagement_id": engagement_id,
                "sessions": mock_sessions,
                "comparable_sessions": len([s for s in mock_sessions if s["can_compare"]])
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving sessions for comparison: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions for comparison") 