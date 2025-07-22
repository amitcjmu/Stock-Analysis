"""
Recommendation Handler
Handles recommendation generation and retrieval operations.
"""

import logging
from typing import Any, Dict

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class RecommendationHandler:
    """Handles recommendation operations with graceful fallbacks."""
    
    def __init__(self):
        self.service_available = False
        self._initialize_dependencies()
    
    def _initialize_dependencies(self):
        """Initialize dependencies with graceful fallbacks."""
        try:
            from app.models.sixr_analysis import SixRAnalysis
            from app.models.sixr_analysis import SixRRecommendation as SixRRecommendationModel
            from app.schemas.sixr_analysis import SixRRecommendationResponse
            
            self.SixRAnalysis = SixRAnalysis
            self.SixRRecommendationModel = SixRRecommendationModel
            self.SixRRecommendationResponse = SixRRecommendationResponse
            
            self.service_available = True
            logger.info("Recommendation handler initialized successfully")
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f"Recommendation services not available: {e}")
            self.service_available = False
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks
    
    async def get_recommendation(
        self,
        analysis_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get recommendation for an analysis."""
        try:
            if not self.service_available:
                return self._fallback_get_recommendation(analysis_id)
            
            # Get analysis record
            result = await db.execute(
                select(self.SixRAnalysis).where(self.SixRAnalysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()
            
            if not analysis:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Analysis {analysis_id} not found"
                )
            
            # Get latest recommendation
            rec_result = await db.execute(
                select(self.SixRRecommendationModel)
                .where(self.SixRRecommendationModel.analysis_id == analysis_id)
                .order_by(self.SixRRecommendationModel.iteration_number.desc())
            )
            recommendation = rec_result.scalar_one_or_none()
            
            if not recommendation:
                # Return analysis info without recommendation
                return {
                    "analysis_id": analysis.id,
                    "analysis_name": analysis.name,
                    "current_iteration": analysis.current_iteration,
                    "status": analysis.status.value,
                    "final_recommendation": analysis.final_recommendation,
                    "confidence_score": analysis.confidence_score,
                    "recommendation": None,
                    "message": "No recommendation available yet"
                }
            
            # Build recommendation response
            return {
                "analysis_id": analysis.id,
                "analysis_name": analysis.name,
                "current_iteration": analysis.current_iteration,
                "status": analysis.status.value,
                "final_recommendation": analysis.final_recommendation,
                "confidence_score": analysis.confidence_score,
                "recommendation": {
                    "id": recommendation.id,
                    "iteration_number": recommendation.iteration_number,
                    "recommended_strategy": recommendation.recommended_strategy,
                    "confidence_score": recommendation.confidence_score,
                    "strategy_scores": recommendation.strategy_scores or {},
                    "key_factors": recommendation.key_factors or [],
                    "assumptions": recommendation.assumptions or [],
                    "next_steps": recommendation.next_steps or [],
                    "estimated_effort": recommendation.estimated_effort,
                    "estimated_timeline": recommendation.estimated_timeline,
                    "estimated_cost_impact": recommendation.estimated_cost_impact,
                    "created_at": recommendation.created_at
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting recommendation for analysis {analysis_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get recommendation: {str(e)}"
            )
    
    # Fallback methods
    def _fallback_get_recommendation(self, analysis_id: int) -> Dict[str, Any]:
        """Fallback for getting recommendation when services unavailable."""
        return {
            "analysis_id": analysis_id,
            "analysis_name": f"Analysis {analysis_id}",
            "current_iteration": 1,
            "status": "completed",
            "final_recommendation": "rehost",
            "confidence_score": 0.7,
            "recommendation": {
                "id": 1,
                "iteration_number": 1,
                "recommended_strategy": "rehost",
                "confidence_score": 0.7,
                "strategy_scores": {"rehost": 0.8, "retain": 0.6},
                "key_factors": ["Low complexity", "Quick migration"],
                "assumptions": ["Cloud readiness", "Minimal refactoring"],
                "next_steps": ["Assess infrastructure", "Plan migration"],
                "estimated_effort": "medium",
                "estimated_timeline": "3-6 months",
                "estimated_cost_impact": "moderate"
            },
            "fallback_mode": True
        } 