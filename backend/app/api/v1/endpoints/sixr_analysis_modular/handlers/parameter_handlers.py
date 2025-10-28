"""
Parameter endpoint handlers for 6R analysis parameter management.
Contains handlers for: update parameters, submit qualifying responses, create iterations.
"""

import logging
from uuid import UUID

from fastapi import BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.sixr_analysis_modular.handlers.analysis_handlers import (
    get_analysis,
)
from app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service import (
    AnalysisService,
)
from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.asset.models import Asset
from app.models.sixr_analysis import SixRAnalysis, SixRIteration, SixRQuestionResponse
from app.models.sixr_analysis import SixRAnalysisParameters as SixRParametersModel
from app.schemas.sixr_analysis import (
    AnalysisStatus,
    InlineAnswersRequest,
    InlineAnswersResponse,
    IterationRequest,
    QualifyingQuestionsRequest,
    SixRParameterUpdateRequest,
)
from app.services.persistent_agents import TenantScopedAgentPool

logger = logging.getLogger(__name__)


async def update_sixr_parameters(
    analysis_id: UUID,
    request: SixRParameterUpdateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Update 6R analysis parameters and trigger re-analysis.

    This endpoint:
    1. Updates the parameter values
    2. Triggers background re-analysis with new parameters
    3. Returns updated analysis state

    Bug #666 - Phase 2: Now using AI-powered analysis via TenantScopedAgentPool
    """
    try:
        # Bug #666 - Phase 2: Create AI-powered service per request
        service = AnalysisService(
            crewai_service=TenantScopedAgentPool, require_ai=False
        )
        # Get analysis
        result = await db.execute(
            select(SixRAnalysis).where(SixRAnalysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()

        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found"
            )

        # Get current parameters to update
        params_result = await db.execute(
            select(SixRParametersModel).where(
                SixRParametersModel.analysis_id == analysis_id,
                SixRParametersModel.iteration_number == analysis.current_iteration,
            )
        )
        current_params = params_result.scalar_one_or_none()

        if current_params:
            # Update existing parameters
            from app.core.security.cache_encryption import secure_setattr

            for key, value in request.parameters.dict().items():
                if hasattr(current_params, key):
                    secure_setattr(current_params, key, value)

            current_params.parameter_notes = request.update_reason
            current_params.updated_by = "system"
        else:
            # Create new parameter record if none exists
            current_params = SixRParametersModel(
                analysis_id=analysis.id,
                iteration_number=analysis.current_iteration,
                **request.parameters.dict(),
                parameter_notes=request.update_reason,
                updated_by="system",
            )
            db.add(current_params)

        # Update analysis status
        analysis.status = AnalysisStatus.IN_PROGRESS
        analysis.updated_by = "system"

        await db.commit()

        # Trigger background re-analysis with AI-powered service
        background_tasks.add_task(
            service.run_parameter_update_analysis,
            analysis.id,
            request.parameters.dict(),
            "system",
        )

        return await get_analysis(analysis.id, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update parameters for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update parameters: {str(e)}",
        )


async def submit_qualifying_responses(
    analysis_id: UUID,
    request: QualifyingQuestionsRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Submit responses to qualifying questions and trigger analysis refinement.

    This endpoint:
    1. Stores question responses
    2. Processes responses to update parameters
    3. Triggers refined analysis

    Bug #666 - Phase 2: Now using AI-powered analysis via TenantScopedAgentPool
    """
    try:
        # Bug #666 - Phase 2: Create AI-powered service per request
        service = AnalysisService(
            crewai_service=TenantScopedAgentPool, require_ai=False
        )
        analysis = await db.get(SixRAnalysis, analysis_id)

        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found"
            )

        # Store question responses
        for response in request.responses:
            question_response = SixRQuestionResponse(
                analysis_id=analysis.id,
                iteration_number=analysis.current_iteration,
                question_id=response.question_id,
                response_value=response.response,
                confidence=response.confidence,
                source=response.source,
                created_by="system",
            )
            db.add(question_response)

        # Update analysis status
        analysis.status = AnalysisStatus.IN_PROGRESS
        analysis.updated_by = "system"

        await db.commit()

        # Trigger background processing with AI-powered service
        background_tasks.add_task(
            service.process_question_responses,
            analysis.id,
            [r.dict() for r in request.responses],
            "system",
        )

        return await get_analysis(analysis.id, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit responses for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit responses: {str(e)}",
        )


async def create_analysis_iteration(
    analysis_id: UUID,
    request: IterationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Create a new iteration of the 6R analysis based on feedback.

    This endpoint:
    1. Creates new iteration record
    2. Applies parameter changes and feedback
    3. Triggers refined analysis

    Bug #666 - Phase 2: Now using AI-powered analysis via TenantScopedAgentPool
    """
    try:
        # Bug #666 - Phase 2: Create AI-powered service per request
        service = AnalysisService(
            crewai_service=TenantScopedAgentPool, require_ai=False
        )
        # Get analysis
        result = await db.execute(
            select(SixRAnalysis).where(SixRAnalysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()

        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found"
            )

        # Create new iteration
        new_iteration_number = analysis.current_iteration + 1

        iteration = SixRIteration(
            analysis_id=analysis.id,
            iteration_number=new_iteration_number,
            iteration_reason=request.iteration_reason,
            stakeholder_feedback=request.stakeholder_feedback,
            parameter_changes=(
                request.parameter_changes.dict() if request.parameter_changes else None
            ),
            created_by="system",
        )

        db.add(iteration)

        # Update analysis
        analysis.current_iteration = new_iteration_number
        analysis.status = AnalysisStatus.IN_PROGRESS
        analysis.updated_by = "system"

        # Create new parameters if provided
        if request.parameter_changes:
            new_params = SixRParametersModel(
                analysis_id=analysis.id,
                iteration_number=new_iteration_number,
                **request.parameter_changes.dict(),
                created_by="system",
            )
            db.add(new_params)

        await db.commit()

        # Trigger background refinement with AI-powered service
        background_tasks.add_task(
            service.run_iteration_analysis,
            analysis_id,
            new_iteration_number,
            request.dict(),
            "system",
        )

        return await get_analysis(analysis_id, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create iteration for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create iteration: {str(e)}",
        )


async def submit_inline_answers(
    analysis_id: UUID,
    request: InlineAnswersRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Submit inline answers for Tier 1 gaps and resume analysis.

    Per Two-Tier Inline Gap-Filling Design (October 2025), this endpoint:
    1. Updates asset fields with user-provided values
    2. Marks analysis as ready to proceed
    3. Triggers background analysis task (AI agents start)
    4. Returns updated analysis state

    Args:
        analysis_id: Analysis UUID
        request: Inline answers with asset_id and field values
        background_tasks: FastAPI background tasks
        db: Database session
        context: Request context with tenant scoping

    Returns:
        InlineAnswersResponse with success status and remaining gaps
    """
    try:
        # Verify analysis exists and belongs to tenant
        analysis_result = await db.execute(
            select(SixRAnalysis).where(
                SixRAnalysis.id == analysis_id,
                SixRAnalysis.client_account_id == context.client_account_id,
                SixRAnalysis.engagement_id == context.engagement_id,
            )
        )
        analysis = analysis_result.scalar_one_or_none()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # Verify asset exists and belongs to tenant
        asset_result = await db.execute(
            select(Asset).where(
                Asset.id == request.asset_id,
                Asset.client_account_id == context.client_account_id,
                Asset.engagement_id == context.engagement_id,
            )
        )
        asset = asset_result.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        # Update asset fields with provided answers
        fields_updated = []
        for field_name, field_value in request.answers.items():
            # Map frontend field names to Asset model fields
            field_mapping = {
                "criticality": "criticality",
                "business_criticality": "business_criticality",
                "application_type": "asset_type",  # Maps to asset_type field
                "migration_priority": "migration_priority",
            }

            asset_field = field_mapping.get(field_name)
            if asset_field and hasattr(asset, asset_field):
                setattr(asset, asset_field, field_value)
                fields_updated.append(field_name)
                logger.info(
                    f"Updated asset {asset.name} field '{field_name}' = '{field_value}'"
                )

        await db.commit()
        await db.refresh(asset)

        logger.info(
            f"Inline answers submitted for analysis {analysis_id}: "
            f"Updated {len(fields_updated)} fields on asset {asset.name}"
        )

        # Update analysis status to indicate it can proceed
        analysis.status = AnalysisStatus.PENDING  # Ready to start
        await db.commit()

        # Trigger background analysis task (RESUME - same as create)
        service = AnalysisService(
            crewai_service=TenantScopedAgentPool, require_ai=False
        )

        # Get current parameters
        params_result = await db.execute(
            select(SixRParametersModel)
            .where(SixRParametersModel.analysis_id == analysis_id)
            .order_by(SixRParametersModel.iteration_number.desc())
        )
        current_params = params_result.scalar_one_or_none()

        if current_params:
            # Start AI agents with updated asset data
            background_tasks.add_task(
                service.run_initial_analysis,
                analysis.id,
                current_params.__dict__,
                "system",
                context.client_account_id,
                context.engagement_id,
            )
            logger.info(
                f"Analysis {analysis_id} RESUMED: AI agents starting with filled data"
            )

        # Return success response
        return InlineAnswersResponse(
            success=True,
            analysis_id=analysis_id,
            asset_id=request.asset_id,
            fields_updated=fields_updated,
            can_proceed=True,  # Analysis can now proceed
            remaining_tier1_gaps=0,  # Assume no gaps after submission
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit inline answers for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit inline answers: {str(e)}",
        )
