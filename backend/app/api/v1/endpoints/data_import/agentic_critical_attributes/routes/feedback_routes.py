"""
Agentic feedback route handlers.
"""

import logging
from typing import List

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.attribute_schemas import AgentFeedback
from ..services.learning_service import LearningService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["agentic-feedback"])


def get_learning_service(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> LearningService:
    """Dependency injection for learning service."""
    return LearningService(db, context)


@router.post("/record-feedback")
async def record_agent_feedback(
    feedback: AgentFeedback,
    learning_service: LearningService = Depends(get_learning_service),
):
    """Record user feedback on agent analysis for learning improvement."""
    try:
        result = await learning_service.record_feedback(feedback)

        if result["success"]:
            logger.info(f"Recorded feedback for analysis {feedback.analysis_id}")
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")


@router.get("/learning-insights")
async def get_learning_insights(
    learning_service: LearningService = Depends(get_learning_service),
):
    """Get learning insights from collected user feedback."""
    try:
        insights = await learning_service.get_learning_insights()
        return insights

    except Exception as e:
        logger.error(f"Error getting learning insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get learning insights")


@router.get("/attribute-recommendations/{attribute_name}")
async def get_attribute_recommendations(
    attribute_name: str,
    learning_service: LearningService = Depends(get_learning_service),
):
    """Get recommendations for a specific attribute based on learning."""
    try:
        recommendations = await learning_service.get_attribute_recommendations(
            attribute_name
        )
        return recommendations

    except Exception as e:
        logger.error(f"Error getting attribute recommendations: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get attribute recommendations"
        )


@router.post("/batch-feedback")
async def record_batch_feedback(
    feedback_list: List[AgentFeedback],
    learning_service: LearningService = Depends(get_learning_service),
):
    """Record multiple feedback items in batch."""
    try:
        results = []

        for feedback in feedback_list:
            try:
                result = await learning_service.record_feedback(feedback)
                results.append(
                    {
                        "analysis_id": feedback.analysis_id,
                        "attribute_name": feedback.attribute_name,
                        "success": result["success"],
                        "message": result.get("message", ""),
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "analysis_id": feedback.analysis_id,
                        "attribute_name": feedback.attribute_name,
                        "success": False,
                        "message": str(e),
                    }
                )

        successful_count = len([r for r in results if r["success"]])

        return {
            "total_submitted": len(feedback_list),
            "successful_count": successful_count,
            "failed_count": len(feedback_list) - successful_count,
            "results": results,
        }

    except Exception as e:
        logger.error(f"Error in batch feedback recording: {e}")
        raise HTTPException(status_code=500, detail="Failed to record batch feedback")


@router.get("/feedback-summary")
async def get_feedback_summary(
    learning_service: LearningService = Depends(get_learning_service),
):
    """Get summary of all feedback collected."""
    try:
        insights = await learning_service.get_learning_insights()

        return {
            "total_feedback": insights["total_feedback"],
            "accuracy_summary": {
                "overall_accuracy": insights["accuracy_metrics"]["overall_accuracy"],
                "correct_predictions": insights["accuracy_metrics"][
                    "correct_predictions"
                ],
                "incorrect_predictions": insights["accuracy_metrics"][
                    "incorrect_predictions"
                ],
            },
            "improvement_areas": len(insights["improvement_suggestions"]),
            "learning_patterns": insights["learning_patterns"],
        }

    except Exception as e:
        logger.error(f"Error getting feedback summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get feedback summary")


@router.post("/export-learning-data")
async def export_learning_data(
    learning_service: LearningService = Depends(get_learning_service),
):
    """Export learning data for analysis or backup."""
    try:
        export_data = await learning_service.export_learning_data()

        return {
            "success": True,
            "export_data": export_data,
            "message": "Learning data exported successfully",
        }

    except Exception as e:
        logger.error(f"Error exporting learning data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export learning data")


@router.post("/import-learning-data")
async def import_learning_data(
    learning_data: dict,
    learning_service: LearningService = Depends(get_learning_service),
):
    """Import learning data from backup or external source."""
    try:
        result = await learning_service.import_learning_data(learning_data)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing learning data: {e}")
        raise HTTPException(status_code=500, detail="Failed to import learning data")
