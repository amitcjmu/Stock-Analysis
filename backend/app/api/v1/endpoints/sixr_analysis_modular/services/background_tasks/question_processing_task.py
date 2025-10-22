"""
Question response processing background task.
Handles processing of qualifying question responses and incorporates them into analysis.
"""

import logging
from typing import Any, Dict, List

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.sixr_analysis import SixRAnalysis, SixRQuestionResponse
from app.models.sixr_analysis import SixRAnalysisParameters as SixRParametersModel
from app.models.sixr_analysis import SixRRecommendation as SixRRecommendationModel
from app.schemas.sixr_analysis import AnalysisStatus, SixRParameterBase

logger = logging.getLogger(__name__)


async def process_question_responses(
    decision_engine, analysis_id: int, responses: List[Dict[str, Any]], user: str
):
    """
    Process qualifying question responses and update analysis.

    Args:
        decision_engine: SixRDecisionEngine instance for analysis
        analysis_id: Analysis ID
        responses: List of question responses
        user: User who provided the responses
    """
    try:
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(SixRAnalysis).where(SixRAnalysis.id == analysis_id)
                )
                analysis = result.scalar_one_or_none()
                if not analysis:
                    return

                # Store question responses
                for response_data in responses:
                    response = SixRQuestionResponse(
                        analysis_id=analysis_id,
                        iteration_number=analysis.current_iteration,
                        question_id=response_data["question_id"],
                        response_value=response_data["response"],
                        confidence_score=response_data.get("confidence", 0.8),
                        response_source=response_data.get("source", "user_input"),
                        created_by=user,
                    )
                    db.add(response)

                # Update analysis status
                analysis.status = AnalysisStatus.IN_PROGRESS
                analysis.progress_percentage = 40.0
                await db.commit()

                # Get current parameters
                params_result = await db.execute(
                    select(SixRParametersModel)
                    .where(SixRParametersModel.analysis_id == analysis_id)
                    .order_by(SixRParametersModel.iteration_number.desc())
                )
                current_params = params_result.scalar_one_or_none()
                if current_params:
                    param_dict = {
                        "business_value": current_params.business_value,
                        "technical_complexity": current_params.technical_complexity,
                        "migration_urgency": current_params.migration_urgency,
                        "compliance_requirements": current_params.compliance_requirements,
                        "cost_sensitivity": current_params.cost_sensitivity,
                        "risk_tolerance": current_params.risk_tolerance,
                        "innovation_priority": current_params.innovation_priority,
                        "application_type": current_params.application_type,
                    }

                    # Incorporate question responses into analysis context
                    question_context = {
                        "responses": responses,
                        "application_data": analysis.application_data,
                    }

                    param_obj = SixRParameterBase(**param_dict)

                    # Run enhanced analysis
                    recommendation_data = await decision_engine.analyze_parameters(
                        param_obj, question_context
                    )

                    # Create updated recommendation
                    recommendation = SixRRecommendationModel(
                        analysis_id=analysis_id,
                        iteration_number=analysis.current_iteration,
                        recommended_strategy=recommendation_data[
                            "recommended_strategy"
                        ],
                        confidence_score=recommendation_data["confidence_score"],
                        strategy_scores=recommendation_data["strategy_scores"],
                        key_factors=recommendation_data["key_factors"],
                        assumptions=recommendation_data["assumptions"],
                        next_steps=recommendation_data["next_steps"],
                        estimated_effort=recommendation_data.get(
                            "estimated_effort", "medium"
                        ),
                        estimated_timeline=recommendation_data.get(
                            "estimated_timeline", "3-6 months"
                        ),
                        estimated_cost_impact=recommendation_data.get(
                            "estimated_cost_impact", "moderate"
                        ),
                        created_by=user,
                    )

                    db.add(recommendation)

                    # Update analysis
                    analysis.status = AnalysisStatus.COMPLETED
                    analysis.progress_percentage = 100.0
                    analysis.final_recommendation = recommendation_data[
                        "recommended_strategy"
                    ]
                    analysis.confidence_score = recommendation_data["confidence_score"]

                    await db.commit()

            except Exception as e:
                logger.error(
                    f"Database error in question processing {analysis_id}: {e}"
                )
                await db.rollback()

    except Exception as e:
        logger.error(f"Failed to process question responses for {analysis_id}: {e}")
