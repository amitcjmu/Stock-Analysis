"""
Analysis service for 6R analysis business logic.
Handles background analysis tasks including initial analysis, parameter updates,
question processing, iteration analysis, and bulk analysis operations.
"""

import asyncio
import logging
from typing import Any, Dict, List

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security.cache_encryption import secure_setattr
from app.models.asset import Asset
from app.models.sixr_analysis import SixRAnalysis, SixRQuestionResponse
from app.models.sixr_analysis import SixRAnalysisParameters as SixRParametersModel
from app.models.sixr_analysis import SixRRecommendation as SixRRecommendationModel
from app.schemas.sixr_analysis import AnalysisStatus, SixRParameterBase
from app.services.sixr_engine_modular import SixRDecisionEngine

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service class for handling 6R analysis business logic."""

    def __init__(self):
        """Initialize the analysis service with decision engine."""
        self.decision_engine = SixRDecisionEngine()

    async def run_initial_analysis(
        self, analysis_id: int, parameters: Dict[str, Any], user: str
    ):
        """Run initial 6R analysis in background."""
        try:
            # Create a proper async session for background task
            async with AsyncSessionLocal() as db:
                try:
                    # Get analysis record
                    result = await db.execute(
                        select(SixRAnalysis).where(SixRAnalysis.id == analysis_id)
                    )
                    analysis = result.scalar_one_or_none()
                    if not analysis:
                        logger.error(f"Analysis {analysis_id} not found")
                        return

                    # Update status to in_progress
                    analysis.status = AnalysisStatus.IN_PROGRESS
                    analysis.progress_percentage = 10.0
                    await db.commit()

                    # Get real application data from discovery
                    application_data = []
                    for app_id in analysis.application_ids:
                        try:
                            # CC: Skip asset lookup if app_id is not a UUID
                            # Frontend may send integer IDs which don't match asset UUIDs
                            app_asset = None
                            try:
                                # Only attempt asset lookup if app_id could be a UUID
                                from uuid import UUID

                                if isinstance(app_id, str):
                                    UUID(app_id)  # Validate UUID format
                                    app_result = await db.execute(
                                        select(Asset).where(Asset.id == app_id)
                                    )
                                    app_asset = app_result.scalar_one_or_none()
                            except (ValueError, TypeError):
                                # app_id is not a valid UUID, skip asset lookup
                                logger.debug(
                                    f"Application ID {app_id} is not a UUID, using fallback data"
                                )

                            if app_asset:
                                # Extract real application characteristics
                                app_data = {
                                    "id": app_id,
                                    "name": app_asset.name or f"Application {app_id}",
                                    "asset_type": app_asset.asset_type,
                                    "location": app_asset.location,
                                    "environment": app_asset.environment,
                                    "department": app_asset.department,
                                    "criticality": app_asset.criticality,
                                    "technology_stack": app_asset.technology_stack
                                    or [],
                                    "complexity_score": app_asset.complexity_score or 5,
                                    "business_criticality": app_asset.criticality
                                    or "medium",
                                    "operating_system": app_asset.operating_system,
                                    "ip_address": app_asset.ip_address,
                                    "cpu_cores": app_asset.cpu_cores,
                                    "memory_gb": app_asset.memory_gb,
                                    "storage_gb": app_asset.storage_gb,
                                    "network_dependencies": app_asset.network_dependencies
                                    or [],
                                    "database_dependencies": app_asset.database_dependencies
                                    or [],
                                    "external_integrations": app_asset.external_integrations
                                    or [],
                                    "compliance_requirements": app_asset.compliance_requirements
                                    or [],
                                    "last_patched": app_asset.last_patched,
                                    "support_model": app_asset.support_model,
                                    "backup_frequency": app_asset.backup_frequency,
                                    "dr_tier": app_asset.dr_tier,
                                }
                            else:
                                # Fallback for missing asset data
                                app_data = {
                                    "id": app_id,
                                    "name": f"Application {app_id}",
                                    "asset_type": "application",
                                    "location": "unknown",
                                    "environment": "production",
                                    "department": "unknown",
                                    "criticality": "medium",
                                    "technology_stack": [],
                                    "complexity_score": 5,
                                    "business_criticality": "medium",
                                }

                            application_data.append(app_data)

                        except Exception as e:
                            logger.warning(
                                f"Failed to get data for application {app_id}: {e}"
                            )
                            # Use minimal fallback data
                            application_data.append(
                                {
                                    "id": app_id,
                                    "name": f"Application {app_id}",
                                    "asset_type": "application",
                                    "complexity_score": 5,
                                }
                            )

                    analysis.application_data = application_data
                    analysis.progress_percentage = 30.0
                    await db.commit()

                    # Get current parameters
                    params_result = await db.execute(
                        select(SixRParametersModel)
                        .where(SixRParametersModel.analysis_id == analysis_id)
                        .order_by(SixRParametersModel.iteration_number.desc())
                    )
                    current_params = params_result.scalar_one_or_none()
                    if not current_params:
                        logger.error(f"No parameters found for analysis {analysis_id}")
                        return

                    # Convert to parameter object for decision engine
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

                    # Run decision engine analysis
                    analysis.progress_percentage = 50.0
                    await db.commit()

                    # Calculate recommendation using decision engine
                    recommendation_data = await self.decision_engine.analyze_parameters(
                        param_obj, application_data[0] if application_data else None
                    )

                    analysis.progress_percentage = 80.0
                    await db.commit()

                    # Create recommendation record
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
                        risk_factors=recommendation_data.get("risk_factors", []),
                        business_benefits=recommendation_data.get(
                            "business_benefits", []
                        ),
                        technical_benefits=recommendation_data.get(
                            "technical_benefits", []
                        ),
                        created_by=user,
                    )

                    db.add(recommendation)

                    # Update analysis status
                    analysis.status = AnalysisStatus.COMPLETED
                    analysis.progress_percentage = 100.0
                    analysis.final_recommendation = recommendation_data[
                        "recommended_strategy"
                    ]
                    analysis.confidence_score = recommendation_data["confidence_score"]

                    await db.commit()

                    logger.info(f"Analysis {analysis_id} completed successfully")

                except Exception as e:
                    logger.error(f"Database error in analysis {analysis_id}: {e}")
                    await db.rollback()

        except Exception as e:
            logger.error(f"Failed to run initial analysis for {analysis_id}: {e}")
            # Update analysis status to failed
            try:
                async with AsyncSessionLocal() as db:
                    try:
                        result = await db.execute(
                            select(SixRAnalysis).where(SixRAnalysis.id == analysis_id)
                        )
                        analysis = result.scalar_one_or_none()
                        if analysis:
                            analysis.status = AnalysisStatus.FAILED
                            await db.commit()
                    except Exception as rollback_error:
                        logger.error(
                            f"Failed to update analysis status to failed: {rollback_error}"
                        )
                        await db.rollback()
            except Exception as session_error:
                logger.error(
                    f"Failed to create session for error handling: {session_error}"
                )

    async def run_parameter_update_analysis(
        self, analysis_id: int, parameters: Dict[str, Any], user: str
    ):
        """Run analysis after parameter update."""
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
                        analysis.application_data[0]
                        if analysis.application_data
                        else None
                    )

                    # Run updated analysis
                    analysis.progress_percentage = 60.0
                    await db.commit()

                    recommendation_data = await self.decision_engine.analyze_parameters(
                        param_obj, app_context
                    )

                    # Create new recommendation for this iteration
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
                        f"Database error in parameter update analysis {analysis_id}: {e}"
                    )
                    await db.rollback()

        except Exception as e:
            logger.error(
                f"Failed to run parameter update analysis for {analysis_id}: {e}"
            )

    async def process_question_responses(
        self, analysis_id: int, responses: List[Dict[str, Any]], user: str
    ):
        """Process qualifying question responses and update analysis."""
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
                        recommendation_data = await self.decision_engine.analyze_parameters(
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
                        analysis.confidence_score = recommendation_data[
                            "confidence_score"
                        ]

                        await db.commit()

                except Exception as e:
                    logger.error(
                        f"Database error in question processing {analysis_id}: {e}"
                    )
                    await db.rollback()

        except Exception as e:
            logger.error(f"Failed to process question responses for {analysis_id}: {e}")

    async def run_iteration_analysis(
        self,
        analysis_id: int,
        iteration_number: int,
        request_data: Dict[str, Any],
        user: str,
    ):
        """Run analysis iteration with updated parameters."""
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

                    recommendation_data = await self.decision_engine.analyze_parameters(
                        param_obj, context
                    )

                    # Create new recommendation for this iteration
                    recommendation = SixRRecommendationModel(
                        analysis_id=analysis_id,
                        iteration_number=iteration_number,
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
                        f"Database error in iteration analysis {analysis_id}: {e}"
                    )
                    await db.rollback()

        except Exception as e:
            logger.error(f"Failed to run iteration analysis for {analysis_id}: {e}")

    async def run_bulk_analysis(
        self, analysis_ids: List[int], batch_size: int, user: str
    ):
        """Run bulk analysis for multiple applications."""
        try:
            for i in range(0, len(analysis_ids), batch_size):
                batch = analysis_ids[i : i + batch_size]

                # Process batch in parallel
                tasks = []
                for analysis_id in batch:
                    task = self.run_initial_analysis(analysis_id, {}, user)
                    tasks.append(task)

                # Wait for batch completion
                await asyncio.gather(*tasks, return_exceptions=True)

                # Small delay between batches
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Failed to run bulk analysis: {e}")


# Create a singleton instance
analysis_service = AnalysisService()
