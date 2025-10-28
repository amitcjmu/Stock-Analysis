"""
Analysis creation endpoint handler for 6R analysis.
Contains handler for: create analysis with Tier 1 gap detection.
"""

import logging
from datetime import datetime

from fastapi import BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service import (
    AnalysisService,
)
from app.api.v1.endpoints.sixr_analysis_modular.services.gap_detection_service import (
    detect_tier1_gaps_for_analysis,
    build_blocked_response,
    build_proceed_response,
)
from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.services.persistent_agents import TenantScopedAgentPool
from app.models.sixr_analysis import SixRAnalysis
from app.models.sixr_analysis import SixRAnalysisParameters as SixRParametersModel
from app.schemas.sixr_analysis import (
    AnalysisStatus,
    SixRAnalysisRequest,
    SixRParameterBase,
    SixRParameters,
)

logger = logging.getLogger(__name__)


async def create_sixr_analysis(
    request: SixRAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Create a new 6R analysis for the specified applications.

    This endpoint initiates the 6R analysis workflow:
    1. Creates analysis record
    2. Runs discovery analysis on application data
    3. Performs initial 6R recommendation
    4. Generates qualifying questions for refinement

    Bug #666 - Phase 2: Now using AI-powered analysis via TenantScopedAgentPool
    """
    try:
        # Bug #666 - Phase 2: Use TenantScopedAgentPool for AI-powered analysis
        # Pass the pool CLASS (not instance) - it manages singleton agents per tenant
        service = AnalysisService(
            crewai_service=TenantScopedAgentPool, require_ai=False
        )

        # Create analysis record with tenant context
        analysis = SixRAnalysis(
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            name=request.analysis_name
            or f"6R Analysis {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            description=request.description,
            status=AnalysisStatus.PENDING,
            priority=request.priority,
            application_ids=request.application_ids,
            current_iteration=1,
            progress_percentage=0.0,
            created_by="system",
        )

        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)

        # Create initial parameters
        initial_params = request.initial_parameters or SixRParameterBase()

        # Handle application types if provided
        if request.application_types and len(request.application_ids) == 1:
            app_id = request.application_ids[0]
            if app_id in request.application_types:
                initial_params.application_type = request.application_types[app_id]

        parameters = SixRParametersModel(
            analysis_id=analysis.id,
            iteration_number=1,
            **initial_params.dict(),
            created_by="system",
        )

        db.add(parameters)
        await db.commit()

        # SERVER-SIDE GATE (October 2025): Check for Tier 1 gaps BEFORE starting AI agents
        # Per Two-Tier Inline Gap-Filling Design - prevents wasted LLM executions
        tier1_gaps_by_asset = await detect_tier1_gaps_for_analysis(
            asset_ids=request.application_ids,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            db=db,
        )

        # If Tier 1 gaps exist, return blocked status (frontend shows modal)
        if tier1_gaps_by_asset:
            # Use helper to build blocked response (reduces file length)
            return build_blocked_response(
                analysis_id=analysis.id,
                tier1_gaps_by_asset=tier1_gaps_by_asset,
                applications=[{"id": app_id} for app_id in request.application_ids],
                parameters=SixRParameters(
                    business_value=initial_params.business_value,
                    technical_complexity=initial_params.technical_complexity,
                    migration_urgency=initial_params.migration_urgency,
                    compliance_requirements=initial_params.compliance_requirements,
                    cost_sensitivity=initial_params.cost_sensitivity,
                    risk_tolerance=initial_params.risk_tolerance,
                    innovation_priority=initial_params.innovation_priority,
                    application_type=initial_params.application_type,
                    parameter_source="user_input",
                    confidence_level=0.0,  # Low confidence until gaps filled
                    last_updated=datetime.utcnow(),
                    updated_by="system",
                ),
                logger_instance=logger,
            )

        # No Tier 1 gaps - proceed with AI agents (legacy behavior)
        logger.info(
            f"Analysis {analysis.id} PROCEED: No Tier 1 gaps, starting AI agents"
        )

        # SECURITY FIX: Pass tenant context to prevent cross-tenant data access (Qodo Bot)
        # Lines 128-136 from original file - CRITICAL: Do not remove
        background_tasks.add_task(
            service.run_initial_analysis,
            analysis.id,
            initial_params.dict(),
            "system",
            context.client_account_id,
            context.engagement_id,
        )

        # Return initial response (agents starting) - use helper to reduce file length
        return build_proceed_response(
            analysis_id=analysis.id,
            applications=[{"id": app_id} for app_id in request.application_ids],
            parameters=SixRParameters(
                business_value=initial_params.business_value,
                technical_complexity=initial_params.technical_complexity,
                migration_urgency=initial_params.migration_urgency,
                compliance_requirements=initial_params.compliance_requirements,
                cost_sensitivity=initial_params.cost_sensitivity,
                risk_tolerance=initial_params.risk_tolerance,
                innovation_priority=initial_params.innovation_priority,
                application_type=initial_params.application_type,
                parameter_source="user_input",
                confidence_level=0.8,
                last_updated=datetime.utcnow(),
                updated_by="system",
            ),
            created_at=analysis.created_at,
            updated_at=analysis.updated_at or analysis.created_at,
        )

    except Exception as e:
        logger.error(f"Failed to create 6R analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create analysis: {str(e)}",
        )
