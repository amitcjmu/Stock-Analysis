"""
6R Analysis API endpoints for migration strategy analysis workflow.
Provides REST API for 6R analysis, parameter updates, question handling, and recommendations.
"""

import logging
from datetime import datetime
from typing import Optional

from app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service import (
    analysis_service,
)
from app.core.database import get_db
from app.models.sixr_analysis import SixRAnalysis
from app.models.sixr_analysis import SixRAnalysisParameters as SixRParametersModel
from app.models.sixr_analysis import SixRIteration, SixRQuestionResponse
from app.models.sixr_analysis import SixRRecommendation as SixRRecommendationModel
from app.schemas.sixr_analysis import (
    AnalysisStatus,
    BulkAnalysisRequest,
    BulkAnalysisResponse,
    IterationRequest,
    QualifyingQuestionsRequest,
    SixRAnalysisListResponse,
    SixRAnalysisRequest,
    SixRAnalysisResponse,
    SixRParameterBase,
    SixRParameters,
    SixRParameterUpdateRequest,
    SixRRecommendation,
    SixRRecommendationResponse,
)
from app.services.sixr_engine_modular import SixRDecisionEngine
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Conditional import for CrewAI technical debt crew
try:
    from app.services.crewai_flows.crews.technical_debt_crew import (
        create_technical_debt_crew,
    )

    TECHNICAL_DEBT_CREW_AVAILABLE = True
except ImportError:
    TECHNICAL_DEBT_CREW_AVAILABLE = False

    def create_technical_debt_crew(*args, **kwargs):
        return None


logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
decision_engine = SixRDecisionEngine()
if TECHNICAL_DEBT_CREW_AVAILABLE:
    logger.info(
        "6R services initialized successfully (using CrewAI Technical Debt Crew)"
    )
else:
    logger.info(
        "6R services initialized successfully (using fallback mode - CrewAI not available)"
    )


@router.post("/analyze", response_model=SixRAnalysisResponse)
async def create_sixr_analysis(
    request: SixRAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new 6R analysis for the specified applications.

    This endpoint initiates the 6R analysis workflow:
    1. Creates analysis record
    2. Runs discovery analysis on application data
    3. Performs initial 6R recommendation
    4. Generates qualifying questions for refinement
    """
    try:
        # Create analysis record
        analysis = SixRAnalysis(
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

        # Start background analysis
        background_tasks.add_task(
            analysis_service.run_initial_analysis,
            analysis.id,
            initial_params.dict(),
            "system",
        )

        # Return initial response
        return SixRAnalysisResponse(
            analysis_id=analysis.id,
            status=AnalysisStatus.PENDING,
            current_iteration=1,
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
            qualifying_questions=[],
            recommendation=None,
            progress_percentage=5.0,
            estimated_completion=None,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at or analysis.created_at,
        )

    except Exception as e:
        logger.error(f"Failed to create 6R analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create analysis: {str(e)}",
        )


@router.get("/{analysis_id}", response_model=SixRAnalysisResponse)
async def get_analysis(analysis_id: int, db: AsyncSession = Depends(get_db)):
    """Get analysis by ID with current recommendation."""
    # Get analysis
    result = await db.execute(
        select(SixRAnalysis).where(SixRAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Get current parameters
    params_result = await db.execute(
        select(SixRParametersModel)
        .where(SixRParametersModel.analysis_id == analysis_id)
        .order_by(SixRParametersModel.iteration_number.desc())
    )
    current_params = params_result.scalar_one_or_none()
    if not current_params:
        raise HTTPException(status_code=404, detail="Analysis parameters not found")

    # Get latest recommendation for this analysis
    rec_result = await db.execute(
        select(SixRRecommendationModel)
        .where(SixRRecommendationModel.analysis_id == analysis_id)
        .order_by(SixRRecommendationModel.iteration_number.desc())
        .limit(1)  # Ensure we only get one row
    )
    latest_recommendation = rec_result.scalar_one_or_none()

    # Convert to response format
    response_data = {
        "analysis_id": analysis.id,
        "status": analysis.status,
        "current_iteration": analysis.current_iteration,
        "applications": [{"id": app_id} for app_id in analysis.application_ids],
        "parameters": SixRParameters(
            business_value=current_params.business_value,
            technical_complexity=current_params.technical_complexity,
            migration_urgency=current_params.migration_urgency,
            compliance_requirements=current_params.compliance_requirements,
            cost_sensitivity=current_params.cost_sensitivity,
            risk_tolerance=current_params.risk_tolerance,
            innovation_priority=current_params.innovation_priority,
            application_type=current_params.application_type,
            parameter_source=current_params.parameter_source,
            confidence_level=current_params.confidence_level,
            last_updated=current_params.updated_at or current_params.created_at,
            updated_by=current_params.updated_by,
        ),
        "qualifying_questions": [],
        "recommendation": None,
        "progress_percentage": analysis.progress_percentage,
        "estimated_completion": analysis.estimated_completion,
        "created_at": analysis.created_at,
        "updated_at": analysis.updated_at or analysis.created_at,
    }

    # Add current recommendation if available
    if latest_recommendation:
        response_data["recommendation"] = SixRRecommendation(
            recommended_strategy=latest_recommendation.recommended_strategy,
            confidence_score=latest_recommendation.confidence_score,
            strategy_scores=latest_recommendation.strategy_scores or [],
            key_factors=latest_recommendation.key_factors or [],
            assumptions=latest_recommendation.assumptions or [],
            next_steps=latest_recommendation.next_steps or [],
            estimated_effort=latest_recommendation.estimated_effort,
            estimated_timeline=latest_recommendation.estimated_timeline,
            estimated_cost_impact=latest_recommendation.estimated_cost_impact,
        )

    return SixRAnalysisResponse(**response_data)


@router.put("/{analysis_id}/parameters", response_model=SixRAnalysisResponse)
async def update_sixr_parameters(
    analysis_id: int,
    request: SixRParameterUpdateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Update 6R analysis parameters and trigger re-analysis.

    This endpoint:
    1. Updates the parameter values
    2. Triggers background re-analysis with new parameters
    3. Returns updated analysis state
    """
    try:
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
            for key, value in request.parameters.dict().items():
                if hasattr(current_params, key):
                    setattr(current_params, key, value)

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

        # Trigger background re-analysis
        background_tasks.add_task(
            analysis_service.run_parameter_update_analysis,
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


@router.post("/{analysis_id}/questions", response_model=SixRAnalysisResponse)
async def submit_qualifying_responses(
    analysis_id: int,
    request: QualifyingQuestionsRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit responses to qualifying questions and trigger analysis refinement.

    This endpoint:
    1. Stores question responses
    2. Processes responses to update parameters
    3. Triggers refined analysis
    """
    try:
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

        # Trigger background processing
        background_tasks.add_task(
            analysis_service.process_question_responses,
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


@router.post("/{analysis_id}/iterate", response_model=SixRAnalysisResponse)
async def create_analysis_iteration(
    analysis_id: int,
    request: IterationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new iteration of the 6R analysis based on feedback.

    This endpoint:
    1. Creates new iteration record
    2. Applies parameter changes and feedback
    3. Triggers refined analysis
    """
    try:
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

        # Trigger background refinement
        background_tasks.add_task(
            analysis_service.run_iteration_analysis,
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


@router.get("/{analysis_id}/recommendation", response_model=SixRRecommendationResponse)
async def get_sixr_recommendation(
    analysis_id: int,
    iteration_number: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the 6R recommendation for a specific analysis and iteration.

    If no iteration is specified, returns the latest recommendation.
    """
    try:
        # Get analysis
        result = await db.execute(
            select(SixRAnalysis).where(SixRAnalysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()

        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found"
            )

        # Get recommendation for specific iteration or latest
        if iteration_number:
            rec_result = await db.execute(
                select(SixRRecommendationModel).where(
                    SixRRecommendationModel.analysis_id == analysis_id,
                    SixRRecommendationModel.iteration_number == iteration_number,
                )
            )
            recommendation = rec_result.scalar_one_or_none()
        else:
            # Get latest recommendation
            rec_result = await db.execute(
                select(SixRRecommendationModel)
                .where(SixRRecommendationModel.analysis_id == analysis_id)
                .order_by(SixRRecommendationModel.iteration_number.desc())
            )
            recommendation = rec_result.scalar_one_or_none()
            iteration_number = analysis.current_iteration

        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found"
            )

        # Build response
        return SixRRecommendationResponse(
            analysis_id=analysis_id,
            iteration_number=iteration_number,
            recommendation=recommendation,
            comparison_with_previous=None,  # TODO: Implement comparison logic
            confidence_evolution=[],  # TODO: Implement confidence tracking
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recommendation for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendation: {str(e)}",
        )


@router.get("/", response_model=SixRAnalysisListResponse)
async def list_sixr_analyses(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[AnalysisStatus] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List all 6R analyses with optional filtering and pagination.
    """
    try:
        # Build query
        query = select(SixRAnalysis)

        if status_filter:
            query = query.where(SixRAnalysis.status == status_filter)

        # Get total count
        count_result = await db.execute(
            select(func.count(SixRAnalysis.id)).select_from(query.subquery())
        )
        total_count = count_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        analyses = result.scalars().all()

        # Convert to response format
        analysis_responses = []
        for analysis in analyses:
            # Get parameters for this analysis
            params_result = await db.execute(
                select(SixRParametersModel)
                .where(SixRParametersModel.analysis_id == analysis.id)
                .order_by(SixRParametersModel.iteration_number.desc())
            )
            current_params = params_result.scalar_one_or_none()

            if current_params:
                params = SixRParameters(
                    business_value=current_params.business_value,
                    technical_complexity=current_params.technical_complexity,
                    migration_urgency=current_params.migration_urgency,
                    compliance_requirements=current_params.compliance_requirements,
                    cost_sensitivity=current_params.cost_sensitivity,
                    risk_tolerance=current_params.risk_tolerance,
                    innovation_priority=current_params.innovation_priority,
                    application_type=current_params.application_type,
                    parameter_source=current_params.parameter_source,
                    confidence_level=current_params.confidence_level,
                    last_updated=current_params.updated_at or current_params.created_at,
                    updated_by=current_params.updated_by,
                )
            else:
                params = SixRParameters()

            # Get latest recommendation for this analysis
            rec_result = await db.execute(
                select(SixRRecommendationModel)
                .where(SixRRecommendationModel.analysis_id == analysis.id)
                .order_by(SixRRecommendationModel.iteration_number.desc())
                .limit(1)  # Ensure we only get one row
            )
            latest_recommendation = rec_result.scalar_one_or_none()

            recommendation = None
            if latest_recommendation:
                recommendation = SixRRecommendation(
                    recommended_strategy=latest_recommendation.recommended_strategy,
                    confidence_score=latest_recommendation.confidence_score,
                    strategy_scores=latest_recommendation.strategy_scores or [],
                    key_factors=latest_recommendation.key_factors or [],
                    assumptions=latest_recommendation.assumptions or [],
                    next_steps=latest_recommendation.next_steps or [],
                    estimated_effort=latest_recommendation.estimated_effort,
                    estimated_timeline=latest_recommendation.estimated_timeline,
                    estimated_cost_impact=latest_recommendation.estimated_cost_impact,
                    risk_factors=latest_recommendation.risk_factors or [],
                    business_benefits=latest_recommendation.business_benefits or [],
                    technical_benefits=latest_recommendation.technical_benefits or [],
                )

            analysis_responses.append(
                SixRAnalysisResponse(
                    analysis_id=analysis.id,
                    status=analysis.status,
                    current_iteration=analysis.current_iteration,
                    applications=analysis.application_data
                    or [{"id": app_id} for app_id in analysis.application_ids],
                    parameters=params,
                    qualifying_questions=[],
                    recommendation=recommendation,  # Now includes actual recommendation data
                    progress_percentage=analysis.progress_percentage,
                    estimated_completion=analysis.estimated_completion,
                    created_at=analysis.created_at,
                    updated_at=analysis.updated_at or analysis.created_at,
                )
            )

        return SixRAnalysisListResponse(
            analyses=analysis_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Failed to list analyses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list analyses: {str(e)}",
        )


@router.post("/bulk", response_model=BulkAnalysisResponse)
async def create_bulk_analysis(
    request: BulkAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Create bulk 6R analysis for multiple applications.

    This endpoint creates individual analyses for each application
    and processes them in batches.
    """
    try:
        individual_analyses = []

        # Create individual analyses
        for app_id in request.application_ids:
            analysis_request = SixRAnalysisRequest(
                application_ids=[app_id],
                initial_parameters=request.default_parameters,
                analysis_name=f"{request.analysis_name} - App {app_id}",
                priority=request.priority,
            )

            # Create analysis (simplified version)
            analysis = SixRAnalysis(
                name=analysis_request.analysis_name,
                status=AnalysisStatus.PENDING,
                priority=analysis_request.priority,
                application_ids=[app_id],
                current_iteration=1,
                progress_percentage=0.0,
                created_by="system",
            )

            db.add(analysis)
            individual_analyses.append(analysis)

        db.commit()

        # Start background bulk processing
        background_tasks.add_task(
            analysis_service.run_bulk_analysis,
            [a.id for a in individual_analyses],
            request.batch_size,
            "system",
        )

        # Build response
        analysis_responses = []
        for analysis in individual_analyses:
            params = request.default_parameters or SixRParameterBase()
            analysis_responses.append(
                SixRAnalysisResponse(
                    analysis_id=analysis.id,
                    status=analysis.status,
                    current_iteration=1,
                    applications=[{"id": analysis.application_ids[0]}],
                    parameters=params,
                    qualifying_questions=[],
                    recommendation=None,
                    progress_percentage=0.0,
                    estimated_completion=None,
                    created_at=analysis.created_at,
                    updated_at=analysis.updated_at or analysis.created_at,
                )
            )

        return BulkAnalysisResponse(
            bulk_analysis_id=individual_analyses[
                0
            ].id,  # Use first analysis ID as bulk ID
            total_applications=len(request.application_ids),
            completed_applications=0,
            failed_applications=0,
            progress_percentage=0.0,
            individual_analyses=analysis_responses,
            estimated_completion=None,
            status=AnalysisStatus.PENDING,
        )

    except Exception as e:
        logger.error(f"Failed to create bulk analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bulk analysis: {str(e)}",
        )


# Background task functions have been moved to AnalysisService
# See: app.api.v1.endpoints.sixr_analysis.services.analysis_service
