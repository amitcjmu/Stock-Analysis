"""
Asset Workflow Management API Endpoints.
Handles workflow progression for assets through discovery → mapping → cleanup → assessment phases.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.asset import Asset, AssetStatus
from app.repositories.asset_repository import AssetRepository
from app.repositories.context_aware_repository import ContextAwareRepository

router = APIRouter()

# Request/Response Models
class WorkflowAdvanceRequest(BaseModel):
    """Request to advance asset workflow to next phase."""
    phase: str = Field(..., description="Target phase: mapping, cleanup, assessment")
    notes: Optional[str] = Field(None, description="Optional notes about the advancement")
    force: bool = Field(False, description="Force advancement even if prerequisites not met")

class WorkflowStatusUpdate(BaseModel):
    """Request to update workflow status."""
    discovery_status: Optional[str] = None
    mapping_status: Optional[str] = None
    cleanup_status: Optional[str] = None
    assessment_readiness: Optional[str] = None
    notes: Optional[str] = None

class WorkflowSummaryResponse(BaseModel):
    """Workflow summary statistics."""
    total_assets: int
    discovery_completed: int
    mapping_completed: int
    cleanup_completed: int
    assessment_ready: int
    phase_distribution: Dict[str, int]
    readiness_scores: Dict[str, float]

class AssetWorkflowStatus(BaseModel):
    """Asset workflow status response."""
    asset_id: int
    name: str
    current_phase: str
    discovery_status: str
    mapping_status: str
    cleanup_status: str
    assessment_readiness: str
    completeness_score: Optional[float]
    quality_score: Optional[float]
    migration_readiness_score: Optional[float]
    can_advance: bool
    next_phase: Optional[str]
    blocking_issues: List[str]

@router.post("/assets/{asset_id}/workflow/advance")
async def advance_asset_workflow(
    asset_id: int,
    request: WorkflowAdvanceRequest,
    db: AsyncSession = Depends(get_db)
) -> AssetWorkflowStatus:
    """
    Advance an asset's workflow to the next phase.
    
    Workflow phases:
    1. Discovery (completed) → Mapping
    2. Mapping (completed) → Cleanup  
    3. Cleanup (completed) → Assessment Ready
    """
    
    # Get asset with current workflow status
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {asset_id} not found"
        )
    
    # Determine current phase and validate advancement
    current_phase = _get_current_phase(asset)
    target_phase = request.phase.lower()
    
    # Validate advancement rules
    if not request.force:
        blocking_issues = _validate_phase_advancement(asset, target_phase)
        if blocking_issues:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot advance to {target_phase}: {', '.join(blocking_issues)}"
            )
    
    # Update workflow status based on target phase
    if target_phase == "mapping":
        asset.discovery_status = "completed"
        asset.mapping_status = "in_progress"
    elif target_phase == "cleanup":
        asset.mapping_status = "completed"
        asset.cleanup_status = "in_progress"
    elif target_phase == "assessment":
        asset.cleanup_status = "completed"
        asset.assessment_readiness = "ready"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target phase: {target_phase}"
        )
    
    # Update asset in database
    await db.commit()
    await db.refresh(asset)
    
    # Return updated workflow status
    return _build_workflow_status(asset)

@router.put("/assets/{asset_id}/workflow/status")
async def update_asset_workflow_status(
    asset_id: int,
    update: WorkflowStatusUpdate,
    db: AsyncSession = Depends(get_db)
) -> AssetWorkflowStatus:
    """
    Update specific workflow status fields for an asset.
    """
    
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {asset_id} not found"
        )
    
    # Update provided fields
    if update.discovery_status is not None:
        asset.discovery_status = update.discovery_status
    if update.mapping_status is not None:
        asset.mapping_status = update.mapping_status
    if update.cleanup_status is not None:
        asset.cleanup_status = update.cleanup_status
    if update.assessment_readiness is not None:
        asset.assessment_readiness = update.assessment_readiness
    
    await db.commit()
    await db.refresh(asset)
    
    return _build_workflow_status(asset)

@router.get("/assets/{asset_id}/workflow/status")
async def get_asset_workflow_status(
    asset_id: int,
    db: AsyncSession = Depends(get_db)
) -> AssetWorkflowStatus:
    """
    Get current workflow status for a specific asset.
    """
    
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {asset_id} not found"
        )
    
    return _build_workflow_status(asset)

@router.get("/assets/workflow/summary")
async def get_workflow_summary(
    db: AsyncSession = Depends(get_db)
) -> WorkflowSummaryResponse:
    """
    Get workflow summary statistics across all assets.
    """
    
    # Get total asset count
    total_result = await db.execute(select(func.count(Asset.id)))
    total_assets = total_result.scalar() or 0
    
    # Get status counts
    discovery_result = await db.execute(
        select(func.count(Asset.id)).where(Asset.discovery_status == "completed")
    )
    discovery_completed = discovery_result.scalar() or 0
    
    mapping_result = await db.execute(
        select(func.count(Asset.id)).where(Asset.mapping_status == "completed")
    )
    mapping_completed = mapping_result.scalar() or 0
    
    cleanup_result = await db.execute(
        select(func.count(Asset.id)).where(Asset.cleanup_status == "completed")
    )
    cleanup_completed = cleanup_result.scalar() or 0
    
    assessment_result = await db.execute(
        select(func.count(Asset.id)).where(Asset.assessment_readiness == "ready")
    )
    assessment_ready = assessment_result.scalar() or 0
    
    # Calculate phase distribution
    phase_distribution = {
        "discovery": total_assets - discovery_completed,
        "mapping": discovery_completed - mapping_completed,
        "cleanup": mapping_completed - cleanup_completed,
        "assessment_ready": assessment_ready
    }
    
    # Calculate average readiness scores
    completeness_result = await db.execute(
        select(func.avg(Asset.completeness_score)).where(Asset.completeness_score.isnot(None))
    )
    avg_completeness = completeness_result.scalar() or 0.0
    
    quality_result = await db.execute(
        select(func.avg(Asset.quality_score)).where(Asset.quality_score.isnot(None))
    )
    avg_quality = quality_result.scalar() or 0.0
    
    readiness_scores = {
        "average_completeness": float(avg_completeness),
        "average_quality": float(avg_quality),
        "overall_readiness": (float(avg_completeness) + float(avg_quality)) / 2
    }
    
    return WorkflowSummaryResponse(
        total_assets=total_assets,
        discovery_completed=discovery_completed,
        mapping_completed=mapping_completed,
        cleanup_completed=cleanup_completed,
        assessment_ready=assessment_ready,
        phase_distribution=phase_distribution,
        readiness_scores=readiness_scores
    )

@router.get("/assets/workflow/by-phase/{phase}")
async def get_assets_by_workflow_phase(
    phase: str,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
) -> List[AssetWorkflowStatus]:
    """
    Get assets currently in a specific workflow phase.
    """
    
    # Build query based on phase
    if phase == "discovery":
        query = select(Asset).where(Asset.discovery_status != "completed")
    elif phase == "mapping":
        query = select(Asset).where(
            Asset.discovery_status == "completed",
            Asset.mapping_status != "completed"
        )
    elif phase == "cleanup":
        query = select(Asset).where(
            Asset.mapping_status == "completed",
            Asset.cleanup_status != "completed"
        )
    elif phase == "assessment_ready":
        query = select(Asset).where(Asset.assessment_readiness == "ready")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid phase: {phase}"
        )
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    assets = result.scalars().all()
    
    return [_build_workflow_status(asset) for asset in assets]

# Helper Functions

def _get_current_phase(asset: Asset) -> str:
    """Determine the current workflow phase for an asset."""
    if asset.assessment_readiness == "ready":
        return "assessment_ready"
    elif asset.cleanup_status == "completed":
        return "assessment_pending"
    elif asset.mapping_status == "completed":
        return "cleanup"
    elif asset.discovery_status == "completed":
        return "mapping"
    else:
        return "discovery"

def _validate_phase_advancement(asset: Asset, target_phase: str) -> List[str]:
    """Validate if an asset can advance to the target phase."""
    blocking_issues = []
    
    if target_phase == "mapping":
        if asset.discovery_status != "completed":
            blocking_issues.append("Discovery phase not completed")
    
    elif target_phase == "cleanup":
        if asset.discovery_status != "completed":
            blocking_issues.append("Discovery phase not completed")
        if asset.mapping_status != "completed":
            blocking_issues.append("Mapping phase not completed")
    
    elif target_phase == "assessment":
        if asset.discovery_status != "completed":
            blocking_issues.append("Discovery phase not completed")
        if asset.mapping_status != "completed":
            blocking_issues.append("Mapping phase not completed")
        if asset.cleanup_status != "completed":
            blocking_issues.append("Cleanup phase not completed")
        
        # Check data quality requirements
        if asset.completeness_score and asset.completeness_score < 80.0:
            blocking_issues.append("Completeness score below 80%")
        if asset.quality_score and asset.quality_score < 70.0:
            blocking_issues.append("Quality score below 70%")
    
    return blocking_issues

def _build_workflow_status(asset: Asset) -> AssetWorkflowStatus:
    """Build workflow status response for an asset."""
    current_phase = _get_current_phase(asset)
    
    # Determine next phase and if advancement is possible
    next_phase = None
    can_advance = False
    blocking_issues = []
    
    if current_phase == "discovery":
        next_phase = "mapping"
        blocking_issues = _validate_phase_advancement(asset, "mapping")
    elif current_phase == "mapping":
        next_phase = "cleanup"
        blocking_issues = _validate_phase_advancement(asset, "cleanup")
    elif current_phase == "cleanup":
        next_phase = "assessment"
        blocking_issues = _validate_phase_advancement(asset, "assessment")
    
    can_advance = len(blocking_issues) == 0
    
    # Calculate migration readiness score
    migration_readiness_score = None
    if hasattr(asset, 'get_migration_readiness_score'):
        try:
            migration_readiness_score = asset.get_migration_readiness_score()
        except:
            migration_readiness_score = None
    
    return AssetWorkflowStatus(
        asset_id=asset.id,
        name=asset.name,
        current_phase=current_phase,
        discovery_status=asset.discovery_status or "pending",
        mapping_status=asset.mapping_status or "pending",
        cleanup_status=asset.cleanup_status or "pending",
        assessment_readiness=asset.assessment_readiness or "not_ready",
        completeness_score=asset.completeness_score,
        quality_score=asset.quality_score,
        migration_readiness_score=migration_readiness_score,
        can_advance=can_advance,
        next_phase=next_phase,
        blocking_issues=blocking_issues
    ) 