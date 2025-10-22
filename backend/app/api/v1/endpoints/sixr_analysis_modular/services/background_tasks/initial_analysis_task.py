"""
Initial analysis background task.
Handles the initial 6R analysis operation including application data fetching
and recommendation generation.

SECURITY NOTE: Contains critical tenant scoping fixes (Qodo Bot review, Oct 2024)
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from app.models.sixr_analysis import SixRAnalysis
from app.models.sixr_analysis import SixRAnalysisParameters as SixRParametersModel
from app.models.sixr_analysis import SixRRecommendation as SixRRecommendationModel
from app.schemas.sixr_analysis import AnalysisStatus, SixRParameterBase

logger = logging.getLogger(__name__)


async def run_initial_analysis(
    decision_engine,
    analysis_id: int,
    parameters: Dict[str, Any],
    user: str,
    client_account_id: Optional[int] = None,
    engagement_id: Optional[int] = None,
):
    """
    Run initial 6R analysis in background.

    Args:
        decision_engine: SixRDecisionEngine instance for analysis
        analysis_id: Analysis ID
        parameters: Analysis parameters
        user: User who initiated the analysis
        client_account_id: Client account ID for tenant scoping (SECURITY FIX)
        engagement_id: Engagement ID for tenant scoping (SECURITY FIX)
    """
    try:
        # Create a proper async session for background task
        async with AsyncSessionLocal() as db:
            try:
                # SECURITY FIX (Qodo Bot): Get analysis record with tenant scoping
                # Lines 64-83 from original file - CRITICAL for multi-tenant isolation
                query = select(SixRAnalysis).where(SixRAnalysis.id == analysis_id)

                # Add tenant scoping if provided (SECURITY: Prevents cross-tenant access)
                if client_account_id is not None:
                    query = query.where(
                        SixRAnalysis.client_account_id == client_account_id
                    )
                if engagement_id is not None:
                    query = query.where(SixRAnalysis.engagement_id == engagement_id)

                result = await db.execute(query)
                analysis = result.scalar_one_or_none()
                if not analysis:
                    logger.error(
                        f"Analysis {analysis_id} not found for tenant "
                        f"(client={client_account_id}, engagement={engagement_id})"
                    )
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
                            if isinstance(app_id, str):
                                UUID(app_id)  # Validate UUID format

                                # SECURITY FIX (Qodo Bot): Add tenant scoping to asset query
                                # Lines 104-115 from original - CRITICAL for data isolation
                                asset_query = select(Asset).where(Asset.id == app_id)
                                if client_account_id is not None:
                                    asset_query = asset_query.where(
                                        Asset.client_account_id == client_account_id
                                    )
                                if engagement_id is not None:
                                    asset_query = asset_query.where(
                                        Asset.engagement_id == engagement_id
                                    )
                                app_result = await db.execute(asset_query)
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
                                "technology_stack": app_asset.technology_stack or [],
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
                recommendation_data = await decision_engine.analyze_parameters(
                    param_obj, application_data[0] if application_data else None
                )

                analysis.progress_percentage = 80.0
                await db.commit()

                # Create recommendation record
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
                    risk_factors=recommendation_data.get("risk_factors", []),
                    business_benefits=recommendation_data.get("business_benefits", []),
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
