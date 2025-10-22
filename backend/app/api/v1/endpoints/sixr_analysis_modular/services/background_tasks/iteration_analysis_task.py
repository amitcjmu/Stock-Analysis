"""
Iteration analysis background task.
Handles analysis iterations with updated parameters and iteration-specific context.
"""

import logging
from typing import Any, Dict

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security.cache_encryption import secure_setattr
from app.models.sixr_analysis import SixRAnalysis
from app.models.sixr_analysis import SixRAnalysisParameters as SixRParametersModel
from app.models.sixr_analysis import SixRRecommendation as SixRRecommendationModel
from app.schemas.sixr_analysis import AnalysisStatus, SixRParameterBase

logger = logging.getLogger(__name__)


async def run_iteration_analysis(
    decision_engine,
    analysis_id: int,
    iteration_number: int,
    request_data: Dict[str, Any],
    user: str,
):
    """
    Run analysis iteration with updated parameters.

    Args:
        decision_engine: SixRDecisionEngine instance for analysis
        analysis_id: Analysis ID
        iteration_number: Iteration number
        request_data: Request data including parameters and notes
        user: User who initiated the iteration
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

                # Update iteration number
                analysis.current_iteration = iteration_number
                analysis.status = AnalysisStatus.IN_PROGRESS
                analysis.progress_percentage = 25.0
                await db.commit()

                # Get current parameters
                params_result = await db.execute(
                    select(SixRParametersModel)
                    .where(SixRParametersModel.analysis_id == analysis_id)
                    .order_by(SixRParametersModel.iteration_number.desc())
                )
                current_params = params_result.scalar_one_or_none()
                if not current_params:
                    return

                # Apply any parameter updates from the iteration request
                if "parameters" in request_data:
                    for key, value in request_data["parameters"].items():
                        if hasattr(current_params, key):
                            secure_setattr(current_params, key, value)

                # Convert to parameter object
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
                param_obj = SixRParameterBase(**param_dict)

                # Get enhanced context including previous iterations
                context = {
                    "application_data": analysis.application_data,
                    "iteration_number": iteration_number,
                    "iteration_notes": request_data.get("iteration_notes", ""),
                }

                # Run analysis
                analysis.progress_percentage = 70.0
                await db.commit()

                recommendation_data = await decision_engine.analyze_parameters(
                    param_obj, context
                )

                # Create new recommendation for this iteration
                recommendation = SixRRecommendationModel(
                    analysis_id=analysis_id,
                    iteration_number=iteration_number,
                    recommended_strategy=recommendation_data["recommended_strategy"],
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
                logger.error(f"Database error in iteration analysis {analysis_id}: {e}")
                await db.rollback()

    except Exception as e:
        logger.error(f"Failed to run iteration analysis for {analysis_id}: {e}")
