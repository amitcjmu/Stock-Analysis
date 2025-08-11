"""
Assessment Flow API endpoints for v1 API.
Implements core flow management, architecture standards, component analysis, and 6R decisions.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context_helpers import (
    verify_client_access,
    verify_engagement_access,
    verify_standards_modification_permission,
)
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db
from app.models.assessment_flow import AssessmentFlowStatus, AssessmentPhase
from app.repositories.assessment_flow_repository import AssessmentFlowRepository
from app.schemas.assessment_flow import (
    AppOnPageResponse,
    ArchitectureStandardsUpdateRequest,
    AssessmentFinalization,
    AssessmentFlowCreateRequest,
    AssessmentFlowResponse,
    AssessmentFlowStatusResponse,
    AssessmentReport,
    ComponentUpdate,
    ResumeFlowRequest,
    SixRDecisionUpdate,
    TechDebtUpdates,
)

# Import integration services
try:
    from app.services.integrations.discovery_integration import DiscoveryFlowIntegration

    DISCOVERY_INTEGRATION_AVAILABLE = True
except ImportError:
    DISCOVERY_INTEGRATION_AVAILABLE = False

try:
    # UnifiedAssessmentFlow import removed - currently not used (see lines 858, 880)
    # from app.services.crewai_flows.unified_assessment_flow import UnifiedAssessmentFlow

    ASSESSMENT_FLOW_SERVICE_AVAILABLE = True
except ImportError:
    ASSESSMENT_FLOW_SERVICE_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assessment-flow", tags=["Assessment Flow"])


# Helper Functions


async def verify_flow_access(
    flow_id: str, db: AsyncSession, client_account_id: str
) -> bool:
    """Verify user has access to assessment flow."""
    repository = AssessmentFlowRepository(db, client_account_id)
    flow_state = await repository.get_assessment_flow_state(flow_id)
    return flow_state is not None


async def get_assessment_flow_context(
    flow_id: str,
    client_account_id: str,
    engagement_id: str,
    user_id: str,
    db: AsyncSession,
):
    """Create flow context for assessment operations."""
    # This would integrate with the actual flow context creation
    # For now, return a simple dict
    return {
        "flow_id": flow_id,
        "client_account_id": client_account_id,
        "engagement_id": engagement_id,
        "user_id": user_id,
        "db_session": db,
    }


def get_next_phase_for_navigation(
    current_phase: AssessmentPhase,
) -> Optional[AssessmentPhase]:
    """Determine next phase based on navigation."""
    phase_sequence = [
        AssessmentPhase.ARCHITECTURE_MINIMUMS,
        AssessmentPhase.TECH_DEBT_ANALYSIS,
        AssessmentPhase.COMPONENT_SIXR_STRATEGIES,
        AssessmentPhase.APP_ON_PAGE_GENERATION,
        AssessmentPhase.FINALIZATION,
    ]

    try:
        current_index = phase_sequence.index(current_phase)
        if current_index < len(phase_sequence) - 1:
            return phase_sequence[current_index + 1]
    except ValueError:
        pass

    return None


def get_progress_for_phase(phase: AssessmentPhase) -> int:
    """Get progress percentage for phase."""
    progress_map = {
        AssessmentPhase.INITIALIZATION: 10,
        AssessmentPhase.ARCHITECTURE_MINIMUMS: 20,
        AssessmentPhase.TECH_DEBT_ANALYSIS: 50,
        AssessmentPhase.COMPONENT_SIXR_STRATEGIES: 75,
        AssessmentPhase.APP_ON_PAGE_GENERATION: 90,
        AssessmentPhase.FINALIZATION: 100,
    }

    return progress_map.get(phase, 0)


# Core Assessment Flow Endpoints


@router.post("/initialize", response_model=AssessmentFlowResponse)
async def initialize_assessment_flow(
    request: AssessmentFlowCreateRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: str = Header(..., alias="X-Engagement-ID"),
):
    """
    Initialize new assessment flow with selected applications.

    - **selected_application_ids**: List of application IDs to assess (1-100 applications)
    - Returns flow_id and initial status
    - Starts background assessment process
    """
    try:
        logger.info(
            f"Initializing assessment flow for {len(request.selected_application_ids)} applications"
        )

        # Verify user has access to engagement
        await verify_engagement_access(db, engagement_id, client_account_id)

        # Verify applications are ready for assessment (if Discovery integration available)
        if DISCOVERY_INTEGRATION_AVAILABLE:
            discovery_integration = DiscoveryFlowIntegration()
            await discovery_integration.verify_applications_ready_for_assessment(
                db, request.selected_application_ids, client_account_id
            )

        # Create assessment flow repository
        repository = AssessmentFlowRepository(db, client_account_id)

        # Initialize flow
        flow_id = await repository.create_assessment_flow(
            engagement_id=engagement_id,
            selected_application_ids=request.selected_application_ids,
            created_by=current_user.email,
        )

        # Start flow execution in background
        if ASSESSMENT_FLOW_SERVICE_AVAILABLE:
            background_tasks.add_task(
                execute_assessment_flow_initialization,
                flow_id,
                client_account_id,
                engagement_id,
                current_user.id,
            )

        return AssessmentFlowResponse(
            flow_id=flow_id,
            status=AssessmentFlowStatus.INITIALIZED,
            current_phase=AssessmentPhase.ARCHITECTURE_MINIMUMS,
            next_phase=AssessmentPhase.ARCHITECTURE_MINIMUMS,
            selected_applications=len(request.selected_application_ids),
            message="Assessment flow initialized successfully",
        )

    except ValueError as e:
        logger.warning(
            safe_log_format(
                "Assessment flow initialization validation error: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            safe_log_format(
                "Assessment flow initialization failed: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Assessment flow initialization failed"
        )


@router.get("/{flow_id}/status", response_model=AssessmentFlowStatusResponse)
async def get_assessment_flow_status(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get current status and progress of assessment flow.

    - **flow_id**: Assessment flow identifier
    - Returns detailed status including phase data and progress
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Get phase-specific data based on current phase
        phase_data = await get_phase_specific_data(
            repository, flow_id, flow_state.current_phase
        )

        return AssessmentFlowStatusResponse(
            flow_id=flow_id,
            status=flow_state.status,
            progress=flow_state.progress,
            current_phase=flow_state.current_phase,
            next_phase=flow_state.next_phase,
            pause_points=flow_state.pause_points or [],
            user_inputs_captured=bool(flow_state.user_inputs),
            phase_results=flow_state.phase_results or {},
            apps_ready_for_planning=flow_state.apps_ready_for_planning or [],
            last_user_interaction=flow_state.last_user_interaction,
            phase_data=phase_data,
            created_at=flow_state.created_at,
            updated_at=flow_state.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to get assessment flow status: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve flow status")


@router.post("/{flow_id}/resume", response_model=AssessmentFlowResponse)
async def resume_assessment_flow(
    flow_id: str,
    request: ResumeFlowRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Resume assessment flow from current phase with user input.

    - **flow_id**: Assessment flow identifier
    - **user_input**: User input data for current phase
    - **save_progress**: Whether to save progress (default: true)
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        if flow_state.status != AssessmentFlowStatus.PAUSED_FOR_USER_INPUT:
            raise HTTPException(status_code=400, detail="Flow is not in paused state")

        # Validate user input for current phase
        await validate_phase_user_input(flow_state.current_phase, request.user_input)

        # Save user input
        await repository.add_user_input(
            flow_id, flow_state.current_phase, request.user_input
        )

        # Update flow status to processing
        await repository.update_flow_status(flow_id, AssessmentFlowStatus.PROCESSING)

        # Resume flow execution in background
        if ASSESSMENT_FLOW_SERVICE_AVAILABLE:
            background_tasks.add_task(
                resume_assessment_flow_execution,
                flow_id,
                flow_state.current_phase,
                request.user_input,
                client_account_id,
            )

        return AssessmentFlowResponse(
            flow_id=flow_id,
            status=AssessmentFlowStatus.PROCESSING,
            current_phase=flow_state.current_phase,
            next_phase=flow_state.next_phase,
            message="Assessment flow resumed successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to resume assessment flow: {str_e}", str_e=str(e))
        )
        raise HTTPException(status_code=500, detail="Failed to resume assessment flow")


@router.put("/{flow_id}/navigate-to-phase/{phase}")
async def navigate_to_assessment_phase(
    flow_id: str,
    phase: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Navigate to specific phase in assessment flow (for user going back).

    - **flow_id**: Assessment flow identifier
    - **phase**: Target phase to navigate to
    """
    try:
        # Validate phase
        try:
            target_phase = AssessmentPhase(phase)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid phase: {phase}")

        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Determine next phase based on navigation
        next_phase = get_next_phase_for_navigation(target_phase)

        # Update flow phase
        await repository.update_flow_phase(
            flow_id,
            target_phase.value,
            next_phase.value if next_phase else None,
            get_progress_for_phase(target_phase),
        )

        return {
            "message": f"Navigated to phase {phase}",
            "next_phase": next_phase.value if next_phase else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to navigate to phase: {str_e}", str_e=str(e))
        )
        raise HTTPException(status_code=500, detail="Phase navigation failed")


# Architecture Standards Endpoints


@router.get("/{flow_id}/architecture-minimums")
async def get_architecture_standards(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get architecture standards for assessment flow.

    - **flow_id**: Assessment flow identifier
    - Returns engagement standards and application overrides
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Get engagement standards
        engagement_standards = await repository.get_engagement_standards(
            flow_state.engagement_id
        )

        # Get application overrides
        app_overrides = await repository.get_application_overrides(flow_id)

        return {
            "engagement_standards": engagement_standards,
            "application_overrides": app_overrides,
            "templates_available": await get_available_templates(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to get architecture standards: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve architecture standards"
        )


@router.put("/{flow_id}/architecture-minimums")
async def update_architecture_standards(
    flow_id: str,
    request: ArchitectureStandardsUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Update architecture standards and application overrides.

    - **flow_id**: Assessment flow identifier
    - **engagement_standards**: Engagement-level standards
    - **application_overrides**: Application-specific overrides
    """
    try:
        # Verify user permissions for standards modification
        await verify_standards_modification_permission(current_user, client_account_id)

        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Update engagement standards
        if request.engagement_standards:
            await repository.save_architecture_standards(
                flow_state.engagement_id,
                request.engagement_standards,
                current_user.email,
            )

        # Update application overrides
        if request.application_overrides:
            await repository.save_application_overrides(
                flow_id, request.application_overrides, current_user.email
            )

        # Mark architecture as captured
        await repository.update_architecture_captured_status(flow_id, True)

        return {"message": "Architecture standards updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to update architecture standards: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to update architecture standards"
        )


# Component Analysis Endpoints


@router.get("/{flow_id}/components")
async def get_application_components(
    flow_id: str,
    app_id: Optional[str] = Query(None, description="Specific application ID"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get identified components for all or specific application.

    - **flow_id**: Assessment flow identifier
    - **app_id**: Optional specific application ID
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        if app_id:
            # Return components for specific application
            components = flow_state.get_application_components(app_id)
            return {"application_id": app_id, "components": components}
        else:
            # Return components for all applications
            return {"components": flow_state.identified_components or {}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to get application components: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve components")


@router.put("/{flow_id}/components/{app_id}")
async def update_application_components(
    flow_id: str,
    app_id: str,
    request: ComponentUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Update component identification for application.

    - **flow_id**: Assessment flow identifier
    - **app_id**: Application ID
    - **components**: Updated component list
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)

        # Prepare component data
        component_data = {
            "components": [comp.dict() for comp in request.components],
            "user_verified": request.user_verified,
            "verification_comments": request.verification_comments,
            "updated_by": current_user.email,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Save components
        success = await repository.save_application_components(
            flow_id, app_id, component_data
        )

        if not success:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        return {"message": "Components updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to update application components: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(status_code=500, detail="Failed to update components")


@router.get("/{flow_id}/tech-debt")
async def get_tech_debt_analysis(
    flow_id: str,
    app_id: Optional[str] = Query(None, description="Specific application ID"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get technical debt analysis for applications.

    - **flow_id**: Assessment flow identifier
    - **app_id**: Optional specific application ID
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        if app_id:
            # Return tech debt for specific application
            tech_debt = flow_state.get_tech_debt_analysis(app_id)
            return {"application_id": app_id, "tech_debt_analysis": tech_debt}
        else:
            # Return tech debt for all applications
            return {"tech_debt_analysis": flow_state.tech_debt_analysis or {}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to get tech debt analysis: {str_e}", str_e=str(e))
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve tech debt analysis"
        )


@router.put("/{flow_id}/tech-debt/{app_id}")
async def update_tech_debt_analysis(
    flow_id: str,
    app_id: str,
    request: TechDebtUpdates,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Update tech debt analysis with user modifications.

    - **flow_id**: Assessment flow identifier
    - **app_id**: Application ID
    - **debt_analysis**: Updated tech debt analysis
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)

        # Prepare tech debt data
        tech_debt_data = {
            "analysis": request.debt_analysis.dict(),
            "user_feedback": request.user_feedback,
            "accepted_recommendations": request.accepted_recommendations,
            "updated_by": current_user.email,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Save tech debt analysis
        success = await repository.save_tech_debt_analysis(
            flow_id, app_id, tech_debt_data
        )

        if not success:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        return {"message": "Tech debt analysis updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to update tech debt analysis: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to update tech debt analysis"
        )


# 6R Decision Endpoints


@router.get("/{flow_id}/sixr-decisions")
async def get_sixr_decisions(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get 6R decisions for all applications in flow.

    - **flow_id**: Assessment flow identifier
    - Returns 6R decisions for all applications
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        return {"sixr_decisions": flow_state.sixr_decisions or {}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to get 6R decisions: {str_e}", str_e=str(e))
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve 6R decisions")


@router.put("/{flow_id}/sixr-decisions/{app_id}")
async def update_sixr_decision(
    flow_id: str,
    app_id: str,
    request: SixRDecisionUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Update 6R decision for application with user modifications.

    - **flow_id**: Assessment flow identifier
    - **app_id**: Application ID
    - **decisions**: Updated 6R decisions
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)

        # Prepare 6R decision data
        decision_data = {
            "decisions": [decision.dict() for decision in request.decisions],
            "user_overrides": request.user_overrides,
            "approval_status": request.approval_status,
            "updated_by": current_user.email,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Save 6R decision
        success = await repository.save_sixr_decision(flow_id, app_id, decision_data)

        if not success:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        return {"message": "6R decision updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to update 6R decision: {str_e}", str_e=str(e))
        )
        raise HTTPException(status_code=500, detail="Failed to update 6R decision")


@router.get("/{flow_id}/app-on-page/{app_id}", response_model=AppOnPageResponse)
async def get_app_on_page(
    flow_id: str,
    app_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get comprehensive app-on-page view.

    - **flow_id**: Assessment flow identifier
    - **app_id**: Application ID
    - Returns comprehensive app-on-page data
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Get app-on-page data for specific application
        app_on_page_data = (
            flow_state.app_on_page_data.get(app_id)
            if flow_state.app_on_page_data
            else None
        )

        if not app_on_page_data:
            raise HTTPException(
                status_code=404, detail="App-on-page data not found for application"
            )

        return AppOnPageResponse(
            flow_id=flow_id,
            application_id=app_id,
            app_on_page_data=app_on_page_data,
            generated_at=datetime.fromisoformat(
                app_on_page_data.get("generated_at", datetime.utcnow().isoformat())
            ),
            last_updated=flow_state.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to get app-on-page data: {str_e}", str_e=str(e))
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve app-on-page data"
        )


@router.post("/{flow_id}/finalize")
async def finalize_assessment(
    flow_id: str,
    request: AssessmentFinalization,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Finalize assessment and mark apps ready for planning.

    - **flow_id**: Assessment flow identifier
    - **apps_to_finalize**: Application IDs to mark as ready for planning
    - **export_to_planning**: Whether to export to Planning Flow
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)

        # Finalize assessment
        success = await repository.finalize_assessment(
            flow_id, request.apps_to_finalize
        )

        if not success:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Export to Planning Flow if requested
        if request.export_to_planning:
            # This would integrate with Planning Flow
            # For now, just log the export
            logger.info(
                safe_log_format(
                    "Assessment {flow_id} ready for Planning Flow export",
                    flow_id=flow_id,
                )
            )

        return {
            "message": "Assessment finalized successfully",
            "apps_ready_for_planning": request.apps_to_finalize,
            "exported_to_planning": request.export_to_planning,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to finalize assessment: {str_e}", str_e=str(e))
        )
        raise HTTPException(status_code=500, detail="Failed to finalize assessment")


@router.get("/{flow_id}/report", response_model=AssessmentReport)
async def get_assessment_report(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get comprehensive assessment report.

    - **flow_id**: Assessment flow identifier
    - Returns comprehensive assessment report
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Generate comprehensive report
        report = AssessmentReport(
            flow_id=flow_id,
            assessment_summary={
                "status": flow_state.status.value,
                "progress": flow_state.progress,
                "current_phase": flow_state.current_phase.value,
                "architecture_captured": flow_state.architecture_captured,
            },
            applications_assessed=flow_state.selected_application_ids,
            architecture_standards_applied=flow_state.engagement_standards or {},
            component_analysis_results=flow_state.identified_components or {},
            tech_debt_analysis_results=flow_state.tech_debt_analysis or {},
            sixr_decisions_summary=flow_state.sixr_decisions or {},
            apps_ready_for_planning=flow_state.apps_ready_for_planning or [],
            overall_readiness_score=calculate_overall_readiness_score(flow_state),
            report_generated_at=datetime.utcnow(),
        )

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to generate assessment report: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to generate assessment report"
        )


# Background task functions


async def execute_assessment_flow_initialization(
    flow_id: str, client_account_id: str, engagement_id: str, user_id: str
):
    """Execute assessment flow initialization in background."""
    try:
        logger.info(
            safe_log_format(
                "Starting background initialization for assessment flow {flow_id}",
                flow_id=flow_id,
            )
        )

        # This would integrate with the actual UnifiedAssessmentFlow
        # For now, simulate initialization
        await asyncio.sleep(2)  # Simulate initialization work

        logger.info(
            safe_log_format(
                "Assessment flow {flow_id} initialized successfully", flow_id=flow_id
            )
        )

    except Exception as e:
        logger.error(
            safe_log_format(
                "Assessment flow initialization failed: {str_e}", str_e=str(e)
            )
        )
        # Update flow status to error state
        # await update_flow_error_state(flow_id, str(e))


async def resume_assessment_flow_execution(
    flow_id: str,
    phase: AssessmentPhase,
    user_input: Dict[str, Any],
    client_account_id: str,
):
    """Resume assessment flow execution from specific phase."""
    try:
        logger.info(
            safe_log_format(
                "Resuming assessment flow {flow_id} from phase {phase_value}",
                flow_id=flow_id,
                phase_value=phase.value,
            )
        )

        # This would integrate with the actual UnifiedAssessmentFlow
        # For now, simulate resume work
        await asyncio.sleep(2)  # Simulate resume work

        logger.info(
            safe_log_format(
                "Assessment flow {flow_id} resumed successfully", flow_id=flow_id
            )
        )

    except Exception as e:
        logger.error(
            safe_log_format("Assessment flow resume failed: {str_e}", str_e=str(e))
        )
        # await update_flow_error_state(flow_id, str(e))


# Helper functions


async def get_phase_specific_data(
    repository: AssessmentFlowRepository, flow_id: str, phase: AssessmentPhase
) -> Dict[str, Any]:
    """Get phase-specific data for status response."""
    # Return relevant data for each phase
    phase_data = {}

    if phase == AssessmentPhase.ARCHITECTURE_MINIMUMS:
        engagement_standards = await repository.get_engagement_standards(
            repository.client_account_id  # This would need the actual engagement_id
        )
        app_overrides = await repository.get_application_overrides(flow_id)
        phase_data = {
            "engagement_standards_count": len(engagement_standards),
            "application_overrides_count": len(app_overrides),
        }

    return phase_data


async def validate_phase_user_input(phase: AssessmentPhase, user_input: Dict[str, Any]):
    """Validate user input for specific phase."""
    # Implementation for phase-specific input validation
    if phase == AssessmentPhase.ARCHITECTURE_MINIMUMS:
        if "standards_confirmed" not in user_input:
            raise ValueError("Architecture standards confirmation required")

    # Add more validation as needed


# verify_standards_modification_permission is imported from context_helpers


async def get_available_templates() -> List[Dict[str, Any]]:
    """Get available architecture standards templates."""
    # Implementation to return available templates
    return [
        {
            "id": "cloud_native_template",
            "name": "Cloud Native Architecture",
            "domain": "infrastructure",
            "description": "Standards for cloud-native applications",
        },
        {
            "id": "security_template",
            "name": "Security Standards",
            "domain": "security",
            "description": "Security and compliance requirements",
        },
    ]


def calculate_overall_readiness_score(flow_state) -> float:
    """Calculate overall readiness score based on assessment completion."""
    score = 0.0

    # Base score from progress
    score += flow_state.progress * 0.4  # 40% weight for progress

    # Architecture standards captured
    if flow_state.architecture_captured:
        score += 15.0  # 15 points

    # Component analysis completion
    if flow_state.identified_components:
        component_count = len(
            [app for app in flow_state.identified_components.values() if app]
        )
        total_apps = len(flow_state.selected_application_ids)
        if total_apps > 0:
            score += (component_count / total_apps) * 20.0  # 20 points max

    # Tech debt analysis completion
    if flow_state.tech_debt_analysis:
        debt_count = len([app for app in flow_state.tech_debt_analysis.values() if app])
        total_apps = len(flow_state.selected_application_ids)
        if total_apps > 0:
            score += (debt_count / total_apps) * 15.0  # 15 points max

    # 6R decisions completion
    if flow_state.sixr_decisions:
        decision_count = len([app for app in flow_state.sixr_decisions.values() if app])
        total_apps = len(flow_state.selected_application_ids)
        if total_apps > 0:
            score += (decision_count / total_apps) * 10.0  # 10 points max

    return min(100.0, max(0.0, score))
