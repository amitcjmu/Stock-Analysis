"""
Demo Data API Endpoints
Provides access to persistent mock data for demonstration and development purposes.
"""

import logging
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.demo_repository import DemoRepository
from app.services.embedding_service import EmbeddingService
from app.schemas.demo import (
    DemoAssetResponse, DemoAssetCreate, DemoAssetUpdate,
    DemoAnalysisResponse, DemoWaveResponse, DemoTagResponse,
    DemoSummaryResponse, DemoEngagementResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

def get_demo_repository(db: AsyncSession = Depends(get_db)) -> DemoRepository:
    """Get demo repository instance."""
    return DemoRepository(db)

def get_embedding_service() -> EmbeddingService:
    """Get embedding service instance."""
    return EmbeddingService()

@router.get("/assets", response_model=List[DemoAssetResponse])
async def get_demo_assets(
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    asset_type: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    business_criticality: Optional[str] = Query(None),
    demo_repo: DemoRepository = Depends(get_demo_repository)
) -> List[DemoAssetResponse]:
    """Get demo assets with optional filtering."""
    try:
        filters = {}
        if asset_type:
            filters['asset_type'] = asset_type
        if environment:
            filters['environment'] = environment
        if business_criticality:
            filters['business_criticality'] = business_criticality
        
        assets = await demo_repo.get_demo_assets(
            limit=limit,
            offset=offset,
            filters=filters
        )
        
        return [DemoAssetResponse.from_orm(asset) for asset in assets]
    
    except Exception as e:
        logger.error(f"Error fetching demo assets: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch demo assets")

@router.get("/assets/summary", response_model=DemoSummaryResponse)
async def get_demo_assets_summary(
    demo_repo: DemoRepository = Depends(get_demo_repository)
) -> DemoSummaryResponse:
    """Get summary statistics for demo assets."""
    try:
        summary = await demo_repo.get_demo_assets_summary()
        return DemoSummaryResponse(**summary)
    
    except Exception as e:
        logger.error(f"Error fetching demo assets summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch demo assets summary")

@router.get("/assets/{asset_id}", response_model=DemoAssetResponse)
async def get_demo_asset(
    asset_id: str,
    demo_repo: DemoRepository = Depends(get_demo_repository)
) -> DemoAssetResponse:
    """Get a specific demo asset by ID."""
    try:
        asset = await demo_repo.get_demo_asset_by_id(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Demo asset not found")
        
        return DemoAssetResponse.from_orm(asset)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching demo asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch demo asset")

@router.post("/assets", response_model=DemoAssetResponse)
async def create_demo_asset(
    asset_data: DemoAssetCreate,
    demo_repo: DemoRepository = Depends(get_demo_repository)
) -> DemoAssetResponse:
    """Create a new demo asset."""
    try:
        asset = await demo_repo.create_demo_asset(asset_data.dict())
        return DemoAssetResponse.from_orm(asset)
    
    except Exception as e:
        logger.error(f"Error creating demo asset: {e}")
        raise HTTPException(status_code=500, detail="Failed to create demo asset")

@router.put("/assets/{asset_id}", response_model=DemoAssetResponse)
async def update_demo_asset(
    asset_id: str,
    asset_data: DemoAssetUpdate,
    demo_repo: DemoRepository = Depends(get_demo_repository)
) -> DemoAssetResponse:
    """Update an existing demo asset."""
    try:
        asset = await demo_repo.update_demo_asset(asset_id, asset_data.dict(exclude_unset=True))
        if not asset:
            raise HTTPException(status_code=404, detail="Demo asset not found")
        
        return DemoAssetResponse.from_orm(asset)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating demo asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update demo asset")

@router.delete("/assets/{asset_id}")
async def delete_demo_asset(
    asset_id: str,
    demo_repo: DemoRepository = Depends(get_demo_repository)
) -> Dict[str, str]:
    """Delete a demo asset."""
    try:
        deleted = await demo_repo.delete_demo_asset(asset_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Demo asset not found")
        
        return {"message": "Demo asset deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting demo asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete demo asset")

@router.post("/assets/text-search", response_model=List[DemoAssetResponse])
async def search_demo_assets_by_text(
    query_text: str = Query(..., min_length=1),
    limit: int = Query(10, le=50),
    demo_repo: DemoRepository = Depends(get_demo_repository),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> List[DemoAssetResponse]:
    """Search demo assets using text similarity."""
    try:
        assets = await embedding_service.search_similar_assets(
            query_text=query_text,
            limit=limit,
            is_mock_only=True
        )
        
        return [DemoAssetResponse.from_orm(asset) for asset in assets]
    
    except Exception as e:
        logger.error(f"Error searching demo assets by text: {e}")
        raise HTTPException(status_code=500, detail="Failed to search demo assets")

@router.post("/assets/{asset_id}/similar", response_model=List[DemoAssetResponse])
async def find_similar_demo_assets(
    asset_id: str,
    limit: int = Query(5, le=20),
    demo_repo: DemoRepository = Depends(get_demo_repository),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> List[DemoAssetResponse]:
    """Find demo assets similar to the specified asset."""
    try:
        # Get the target asset
        target_asset = await demo_repo.get_demo_asset_by_id(asset_id)
        if not target_asset:
            raise HTTPException(status_code=404, detail="Demo asset not found")
        
        # Find similar assets
        similar_assets = await embedding_service.find_similar_assets(
            asset_id=asset_id,
            limit=limit,
            is_mock_only=True
        )
        
        return [DemoAssetResponse.from_orm(asset) for asset in similar_assets]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar demo assets: {e}")
        raise HTTPException(status_code=500, detail="Failed to find similar demo assets")

@router.post("/assets/{asset_id}/auto-tag", response_model=List[DemoTagResponse])
async def auto_tag_demo_asset(
    asset_id: str,
    confidence_threshold: float = Query(0.8, ge=0.0, le=1.0),
    max_tags: int = Query(5, ge=1, le=10),
    demo_repo: DemoRepository = Depends(get_demo_repository),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> List[DemoTagResponse]:
    """Auto-tag a demo asset using AI suggestions."""
    try:
        # Get the target asset
        target_asset = await demo_repo.get_demo_asset_by_id(asset_id)
        if not target_asset:
            raise HTTPException(status_code=404, detail="Demo asset not found")
        
        # Get AI tag suggestions
        suggested_tags = await embedding_service.suggest_tags(
            asset_id=asset_id,
            confidence_threshold=confidence_threshold,
            max_tags=max_tags,
            is_mock_only=True
        )
        
        # Apply tags to the asset
        applied_tags = await demo_repo.apply_tags_to_asset(asset_id, [tag.name for tag in suggested_tags])
        
        return [DemoTagResponse.from_orm(tag) for tag in applied_tags]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error auto-tagging demo asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to auto-tag demo asset")

@router.get("/analyses", response_model=List[DemoAnalysisResponse])
async def get_demo_analyses(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    analysis_type: Optional[str] = Query(None),
    demo_repo: DemoRepository = Depends(get_demo_repository)
) -> List[DemoAnalysisResponse]:
    """Get demo 6R analyses."""
    try:
        filters = {}
        if analysis_type:
            filters['analysis_type'] = analysis_type
        
        analyses = await demo_repo.get_demo_analyses(
            limit=limit,
            offset=offset,
            filters=filters
        )
        
        return [DemoAnalysisResponse.from_orm(analysis) for analysis in analyses]
    
    except Exception as e:
        logger.error(f"Error fetching demo analyses: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch demo analyses")

@router.get("/waves", response_model=List[DemoWaveResponse])
async def get_demo_waves(
    demo_repo: DemoRepository = Depends(get_demo_repository)
) -> List[DemoWaveResponse]:
    """Get demo migration waves."""
    try:
        waves = await demo_repo.get_demo_waves()
        return [DemoWaveResponse.from_orm(wave) for wave in waves]
    
    except Exception as e:
        logger.error(f"Error fetching demo waves: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch demo waves")

@router.get("/tags", response_model=List[DemoTagResponse])
async def get_demo_tags(
    category: Optional[str] = Query(None),
    demo_repo: DemoRepository = Depends(get_demo_repository)
) -> List[DemoTagResponse]:
    """Get demo tags."""
    try:
        filters = {}
        if category:
            filters['category'] = category
        
        tags = await demo_repo.get_demo_tags(filters=filters)
        return [DemoTagResponse.from_orm(tag) for tag in tags]
    
    except Exception as e:
        logger.error(f"Error fetching demo tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch demo tags")

@router.get("/engagement", response_model=DemoEngagementResponse)
async def get_demo_engagement_info(
    demo_repo: DemoRepository = Depends(get_demo_repository)
) -> DemoEngagementResponse:
    """Get demo engagement information."""
    try:
        engagement_info = await demo_repo.get_demo_engagement_info()
        return DemoEngagementResponse(**engagement_info)
    
    except Exception as e:
        logger.error(f"Error fetching demo engagement info: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch demo engagement info")

@router.get("/health")
async def demo_health_check() -> Dict[str, Any]:
    """Health check for demo endpoints."""
    return {
        "status": "healthy",
        "service": "demo_api",
        "timestamp": "2024-01-15T10:00:00Z"
    } 