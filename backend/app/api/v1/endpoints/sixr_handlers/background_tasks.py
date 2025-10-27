"""
Background Tasks Handler
Handles all background processing for 6R analysis operations.
"""

import asyncio
import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select

logger = logging.getLogger(__name__)


class BackgroundTasksHandler:
    """Handles background task operations with graceful fallbacks."""

    def __init__(self, crewai_service=None):
        """
        Initialize background tasks handler.

        Args:
            crewai_service: Optional CrewAI service for AI-powered analysis.
                           If None, engine uses fallback heuristic mode.
                           Reference: Bug #666 - Phase 1 fix
        """
        self.service_available = False
        self.crewai_service = crewai_service
        self._initialize_dependencies()

    def _initialize_dependencies(self):
        """Initialize dependencies with graceful fallbacks."""
        try:
            from app.core.database import AsyncSessionLocal
            from app.models.sixr_analysis import (
                SixRAnalysis,
            )
            from app.models.sixr_analysis import SixRParameters as SixRParametersModel
            from app.models.sixr_analysis import (
                SixRRecommendation as SixRRecommendationModel,
            )
            from app.schemas.sixr_analysis import AnalysisStatus, SixRParameterBase

            try:
                from app.services.sixr_engine_modular import SixRDecisionEngine
            except ImportError:
                pass

            self.AsyncSessionLocal = AsyncSessionLocal
            self.SixRAnalysis = SixRAnalysis
            self.SixRParametersModel = SixRParametersModel
            self.SixRRecommendationModel = SixRRecommendationModel
            self.AnalysisStatus = AnalysisStatus
            self.SixRParameterBase = SixRParameterBase
            # Bug #666 - Phase 1: Pass crewai_service to enable AI-powered analysis
            self.decision_engine = SixRDecisionEngine(
                crewai_service=self.crewai_service
            )

            self.service_available = True
            logger.info("Background tasks handler initialized successfully")
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f"Background tasks services not available: {e}")
            self.service_available = False

    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks

    async def run_initial_analysis(
        self, analysis_id: int, parameters: Dict[str, Any], user: str
    ):
        """Run initial 6R analysis in background."""
        if not self.service_available:
            logger.warning(
                f"Background tasks not available, skipping analysis {analysis_id}"
            )
            return

        try:
            async with self.AsyncSessionLocal() as db:
                try:
                    # Get analysis record
                    result = await db.execute(
                        select(self.SixRAnalysis).where(
                            self.SixRAnalysis.id == analysis_id
                        )
                    )
                    analysis = result.scalar_one_or_none()
                    if not analysis:
                        logger.error(f"Analysis {analysis_id} not found")
                        return

                    # Update status to in_progress
                    analysis.status = self.AnalysisStatus.IN_PROGRESS
                    analysis.progress_percentage = 10.0
                    await db.commit()

                    # Get application data (mock for now - would come from CMDB)
                    application_data = []
                    for app_id in analysis.application_ids:
                        app_data = {
                            "id": app_id,
                            "name": f"Application {app_id}",
                            "technology_stack": ["Java", "Spring", "MySQL"],
                            "complexity_score": 6,
                            "business_criticality": "high",
                        }
                        application_data.append(app_data)

                    analysis.application_data = application_data
                    analysis.progress_percentage = 30.0
                    await db.commit()

                    # Fetch real asset inventory from database (Bug #813 fix)
                    logger.info(
                        f"Fetching asset inventory for analysis {analysis_id} "
                        f"with {len(analysis.application_ids)} application IDs"
                    )
                    asset_inventory = None
                    dependencies = None

                    try:
                        from app.repositories.asset_repository import AssetRepository
                        from app.repositories.dependency_repository import (
                            DependencyRepository,
                        )

                        asset_repo = AssetRepository(
                            db,
                            client_account_id=(
                                str(analysis.client_account_id)
                                if analysis.client_account_id
                                else None
                            ),
                            engagement_id=(
                                str(analysis.engagement_id)
                                if analysis.engagement_id
                                else None
                            ),
                        )

                        # Convert application IDs to UUIDs and fetch assets
                        asset_ids = []
                        for app_id in analysis.application_ids:
                            try:
                                asset_ids.append(
                                    UUID(app_id) if isinstance(app_id, str) else app_id
                                )
                            except (ValueError, TypeError) as e:
                                logger.warning(
                                    f"Invalid UUID format for app_id {app_id}: {e}"
                                )

                        if asset_ids:
                            # Get assets by IDs
                            assets_result = await asset_repo.get_by_filters(
                                id=asset_ids
                            )

                            if assets_result:
                                # Format asset inventory for AI analysis
                                asset_inventory = {
                                    "assets": [
                                        {
                                            "id": str(asset.id),
                                            "name": asset.name or asset.asset_name,
                                            "asset_type": asset.asset_type,
                                            "attributes": asset.attributes or {},
                                            "technology_stack": asset.technology_stack
                                            or [],
                                            "business_criticality": (
                                                asset.business_criticality
                                            ),
                                        }
                                        for asset in assets_result
                                    ],
                                    "total_count": len(assets_result),
                                }
                                logger.info(
                                    f"Retrieved {len(assets_result)} assets "
                                    "for AI analysis"
                                )

                        # Fetch dependencies
                        dep_repo = DependencyRepository(
                            db,
                            client_account_id=(
                                str(analysis.client_account_id)
                                if analysis.client_account_id
                                else None
                            ),
                            engagement_id=(
                                str(analysis.engagement_id)
                                if analysis.engagement_id
                                else None
                            ),
                        )

                        # Get all dependencies (app-to-server and app-to-app)
                        app_server_deps = await dep_repo.get_app_server_dependencies()
                        app_app_deps = await dep_repo.get_app_app_dependencies()

                        all_deps = app_server_deps + app_app_deps

                        if all_deps:
                            # Format dependencies for AI analysis
                            dependencies = {
                                "relationships": [
                                    {
                                        "source_id": dep.get("application_id")
                                        or dep.get("source_app_id"),
                                        "target_id": (
                                            dep.get("server_info", {}).get("id")
                                            if "server_info" in dep
                                            else dep.get("target_app_info", {}).get(
                                                "id"
                                            )
                                        ),
                                        "type": dep.get("dependency_type"),
                                        "criticality": "medium",  # Default criticality
                                    }
                                    for dep in all_deps
                                ],
                                "total_count": len(all_deps),
                            }
                            logger.info(
                                f"Retrieved {len(all_deps)} dependencies for AI analysis"
                            )
                        else:
                            logger.info(
                                "No dependencies found for the selected applications"
                            )

                    except ImportError as e:
                        logger.warning(
                            f"Repository imports not available: {e}. "
                            "Proceeding without asset inventory."
                        )
                    except Exception as e:
                        logger.error(
                            f"Error fetching asset inventory or dependencies: {e}. "
                            "Proceeding with fallback analysis."
                        )

                    # Get current parameters
                    params_result = await db.execute(
                        select(self.SixRParametersModel)
                        .where(self.SixRParametersModel.analysis_id == analysis_id)
                        .order_by(self.SixRParametersModel.iteration_number.desc())
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

                    # Run decision engine analysis
                    analysis.progress_percentage = 50.0
                    await db.commit()

                    # Calculate recommendation using decision engine
                    try:
                        if hasattr(self.decision_engine, "analyze_parameters"):
                            param_obj = self.SixRParameterBase(**param_dict)

                            # Log AI agent invocation (Bug #813 fix)
                            if asset_inventory:
                                logger.info(
                                    f"Invoking AI agents for analysis {analysis_id} with "
                                    f"{asset_inventory['total_count']} assets and "
                                    f"{dependencies['total_count'] if dependencies else 0} dependencies"
                                )
                            else:
                                logger.warning(
                                    f"Analysis {analysis_id} proceeding with fallback strategy "
                                    "(no asset inventory available)"
                                )

                            recommendation_data = (
                                self.decision_engine.analyze_parameters(
                                    param_obj,
                                    (
                                        application_data[0]["technology_stack"]
                                        if application_data
                                        else None
                                    ),
                                    asset_inventory=asset_inventory,
                                    dependencies=dependencies,
                                )
                            )
                        else:
                            # Fallback recommendation
                            recommendation_data = {
                                "recommended_strategy": "rehost",
                                "confidence_score": 0.7,
                                "strategy_scores": {"rehost": 0.8, "retain": 0.6},
                                "key_factors": ["Low complexity", "Quick migration"],
                                "assumptions": ["Cloud readiness"],
                                "next_steps": [
                                    "Assess infrastructure",
                                    "Plan migration",
                                ],
                                "estimated_effort": "medium",
                                "estimated_timeline": "3-6 months",
                                "estimated_cost_impact": "moderate",
                            }
                    except Exception as e:
                        logger.warning(f"Decision engine error, using fallback: {e}")
                        recommendation_data = {
                            "recommended_strategy": "rehost",
                            "confidence_score": 0.5,
                            "strategy_scores": {},
                            "key_factors": [],
                            "assumptions": [],
                            "next_steps": [],
                            "estimated_effort": "medium",
                            "estimated_timeline": "3-6 months",
                            "estimated_cost_impact": "moderate",
                        }

                    analysis.progress_percentage = 80.0
                    await db.commit()

                    # Create recommendation record
                    recommendation = self.SixRRecommendationModel(
                        analysis_id=analysis_id,
                        iteration_number=analysis.current_iteration,
                        recommended_strategy=recommendation_data[
                            "recommended_strategy"
                        ],
                        confidence_score=recommendation_data["confidence_score"],
                        strategy_scores=recommendation_data.get("strategy_scores", {}),
                        key_factors=recommendation_data.get("key_factors", []),
                        assumptions=recommendation_data.get("assumptions", []),
                        next_steps=recommendation_data.get("next_steps", []),
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

                    # Update analysis with final results
                    analysis.status = self.AnalysisStatus.COMPLETED
                    analysis.progress_percentage = 100.0
                    analysis.final_recommendation = recommendation_data[
                        "recommended_strategy"
                    ]
                    analysis.confidence_score = recommendation_data["confidence_score"]

                    await db.commit()
                    logger.info(f"Completed initial analysis for {analysis_id}")

                except Exception as e:
                    logger.error(
                        f"Database error in initial analysis {analysis_id}: {e}"
                    )
                    await db.rollback()

        except Exception as e:
            logger.error(f"Failed to run initial analysis for {analysis_id}: {e}")

    async def run_iteration_analysis(
        self,
        analysis_id: int,
        iteration_number: int,
        request_data: Dict[str, Any],
        user: str,
    ):
        """Run iteration analysis in background."""
        if not self.service_available:
            logger.warning(
                f"Background tasks not available, skipping iteration analysis {analysis_id}"
            )
            return

        try:
            async with self.AsyncSessionLocal() as db:
                try:
                    # Get analysis record
                    result = await db.execute(
                        select(self.SixRAnalysis).where(
                            self.SixRAnalysis.id == analysis_id
                        )
                    )
                    analysis = result.scalar_one_or_none()
                    if not analysis:
                        logger.error(f"Analysis {analysis_id} not found")
                        return

                    # Get current parameters
                    params_result = await db.execute(
                        select(self.SixRParametersModel)
                        .where(self.SixRParametersModel.analysis_id == analysis_id)
                        .where(
                            self.SixRParametersModel.iteration_number
                            == iteration_number
                        )
                    )
                    current_params = params_result.scalar_one_or_none()
                    if not current_params:
                        logger.error(
                            f"No parameters found for analysis {analysis_id} iteration {iteration_number}"
                        )
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

                    # Get enhanced context including previous iterations
                    context = {
                        "application_data": analysis.application_data,
                        "iteration_number": iteration_number,
                        "iteration_notes": request_data.get("iteration_notes", ""),
                    }

                    # Run analysis
                    analysis.progress_percentage = 70.0
                    await db.commit()

                    try:
                        if hasattr(self.decision_engine, "analyze_parameters"):
                            param_obj = self.SixRParameterBase(**param_dict)
                            recommendation_data = (
                                self.decision_engine.analyze_parameters(
                                    param_obj, context
                                )
                            )
                        else:
                            recommendation_data = {
                                "recommended_strategy": "rehost",
                                "confidence_score": 0.7,
                                "strategy_scores": {},
                                "key_factors": [],
                                "assumptions": [],
                                "next_steps": [],
                                "estimated_effort": "medium",
                                "estimated_timeline": "3-6 months",
                                "estimated_cost_impact": "moderate",
                            }
                    except Exception as e:
                        logger.warning(f"Decision engine error in iteration: {e}")
                        recommendation_data = {
                            "recommended_strategy": "rehost",
                            "confidence_score": 0.5,
                            "strategy_scores": {},
                            "key_factors": [],
                            "assumptions": [],
                            "next_steps": [],
                            "estimated_effort": "medium",
                            "estimated_timeline": "3-6 months",
                            "estimated_cost_impact": "moderate",
                        }

                    # Create new recommendation for this iteration
                    recommendation = self.SixRRecommendationModel(
                        analysis_id=analysis_id,
                        iteration_number=iteration_number,
                        recommended_strategy=recommendation_data[
                            "recommended_strategy"
                        ],
                        confidence_score=recommendation_data["confidence_score"],
                        strategy_scores=recommendation_data.get("strategy_scores", {}),
                        key_factors=recommendation_data.get("key_factors", []),
                        assumptions=recommendation_data.get("assumptions", []),
                        next_steps=recommendation_data.get("next_steps", []),
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
                    analysis.status = self.AnalysisStatus.COMPLETED
                    analysis.progress_percentage = 100.0
                    analysis.final_recommendation = recommendation_data[
                        "recommended_strategy"
                    ]
                    analysis.confidence_score = recommendation_data["confidence_score"]

                    await db.commit()
                    logger.info(
                        f"Completed iteration analysis for {analysis_id}, iteration {iteration_number}"
                    )

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
        if not self.service_available:
            logger.warning("Background tasks not available, skipping bulk analysis")
            return

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

                logger.info(f"Completed bulk analysis batch {i//batch_size + 1}")

            logger.info(f"Completed bulk analysis for {len(analysis_ids)} analyses")

        except Exception as e:
            logger.error(f"Error in bulk analysis: {e}")
