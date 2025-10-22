"""
Parameter update analysis background task.
Handles re-analysis when parameters are updated by the user.
"""

import logging
from typing import Any, Dict

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.sixr_analysis import SixRAnalysis
from app.models.sixr_analysis import SixRAnalysisParameters as SixRParametersModel
from app.models.sixr_analysis import SixRRecommendation as SixRRecommendationModel
from app.schemas.sixr_analysis import AnalysisStatus, SixRParameterBase

logger = logging.getLogger(__name__)


async def run_parameter_update_analysis(
    decision_engine, analysis_id: int, parameters: Dict[str, Any], user: str
):
    """
    Run analysis after parameter update.

    Args:
        decision_engine: SixRDecisionEngine instance for analysis
        analysis_id: Analysis ID
        parameters: Updated analysis parameters
        user: User who initiated the update
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

                # Update status
                analysis.status = AnalysisStatus.IN_PROGRESS
                analysis.progress_percentage = 20.0
                await db.commit()

                # Get updated parameters
                params_result = await db.execute(
                    select(SixRParametersModel)
                    .where(SixRParametersModel.analysis_id == analysis_id)
                    .order_by(SixRParametersModel.iteration_number.desc())
                )
                current_params = params_result.scalar_one_or_none()
                if not current_params:
                    return

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

                # Get application context
                app_context = (
                    analysis.application_data[0] if analysis.application_data else None
                )

                # Run updated analysis
                analysis.progress_percentage = 60.0
                await db.commit()

                recommendation_data = await decision_engine.analyze_parameters(
                    param_obj, app_context
                )

                # Create new recommendation for this iteration
                recommendation = SixRRecommendationModel(
                    analysis_id=analysis_id,
                    iteration_number=analysis.current_iteration,
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
                logger.error(
                    f"Database error in parameter update analysis {analysis_id}: {e}"
                )
                await db.rollback()

    except Exception as e:
        logger.error(f"Failed to run parameter update analysis for {analysis_id}: {e}")
