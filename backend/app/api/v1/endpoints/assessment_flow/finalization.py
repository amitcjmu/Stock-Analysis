"""
Assessment flow finalization and reporting endpoints.
Handles flow finalization, app-on-page views, and report generation.
Uses MFO integration layer per ADR-006 (Master Flow Orchestrator pattern).
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context_helpers import verify_client_access
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db
from app.models.assessment_flow import AssessmentFlowStatus
from app.repositories.assessment_flow_repository import AssessmentFlowRepository
from app.schemas.assessment_flow import (
    AppOnPageResponse,
    AssessmentFinalization,
    AssessmentReport,
)

# Import MFO integration functions (per ADR-006)
from .mfo_integration import (
    get_assessment_status_via_mfo,
    complete_assessment_flow,
)

# Assessment flow utilities are available at assessment_flow_utils.py
# but not currently used in this finalization module

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{flow_id}/app-on-page/{app_id}", response_model=AppOnPageResponse)
async def get_app_on_page_view(
    flow_id: str,
    app_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get comprehensive app-on-page view for specific application via MFO.

    - **flow_id**: Assessment flow identifier
    - **app_id**: Application identifier
    - Returns complete application assessment data for single-page view
    - Uses MFO integration (ADR-006) to verify flow existence
    """
    try:
        # Verify flow exists via MFO (checks both master and child tables)
        try:
            await get_assessment_status_via_mfo(UUID(flow_id), db)
        except ValueError:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Get child flow data for application details
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Validate application is part of the flow
        if app_id not in (flow_state.selected_application_ids or []):
            raise HTTPException(
                status_code=400, detail="Application not part of this assessment flow"
            )

        # Get comprehensive application data
        app_data = await repository.get_comprehensive_app_data(flow_id, app_id)

        # Get architecture standards relevant to this app
        standards = await repository.get_application_standards(flow_id, app_id)

        # Get components analysis
        components = await repository.get_application_components(flow_id, app_id)

        # Get tech debt analysis
        tech_debt = await repository.get_tech_debt_analysis(flow_id, app_id)

        # Get 6R decision
        sixr_decision = await repository.get_sixr_decision(flow_id, app_id)

        return AppOnPageResponse(
            application_id=app_id,
            application_data=app_data,
            architecture_standards=standards,
            components=components,
            tech_debt_analysis=tech_debt,
            sixr_decision=sixr_decision,
            assessment_complete=(
                sixr_decision is not None and sixr_decision.get("strategy") is not None
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to get app-on-page view: {str_e}", str_e=str(e))
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve app-on-page view"
        )


@router.post("/{flow_id}/finalize")
async def finalize_assessment_flow(
    flow_id: str,
    request: AssessmentFinalization,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Finalize assessment flow and mark as complete via MFO.

    - **flow_id**: Assessment flow identifier
    - **finalization_notes**: Optional notes for finalization
    - Validates all applications have 6R decisions before finalizing
    - Uses MFO integration (ADR-006) for atomic completion
    """
    try:
        # Get flow state via MFO (checks both master and child tables)
        mfo_state = await get_assessment_status_via_mfo(UUID(flow_id), db)

        if mfo_state["status"] == AssessmentFlowStatus.COMPLETED.value:
            raise HTTPException(
                status_code=400, detail="Assessment flow already completed"
            )

        # Get child flow data for validation
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Validate all applications have required data
        validation_results = await _validate_flow_completion_requirements(
            repository, flow_id, flow_state.selected_application_ids or []
        )

        if not validation_results["all_complete"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Assessment flow cannot be finalized",
                    "missing_data": validation_results["missing_data"],
                },
            )

        # Save finalization notes to repository before MFO completion
        await repository.finalize_assessment_flow(
            flow_id, request.finalization_notes, current_user.email
        )

        # Complete flow via MFO (updates both master and child tables atomically)
        result = await complete_assessment_flow(UUID(flow_id), db)

        return {
            "flow_id": flow_id,
            "status": result["status"],
            "finalized_by": current_user.email,
            "applications_assessed": len(flow_state.selected_application_ids or []),
            "message": "Assessment flow finalized successfully via MFO",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to finalize assessment flow: {str_e}", str_e=str(e))
        )
        raise HTTPException(
            status_code=500, detail="Failed to finalize assessment flow"
        )


@router.get("/{flow_id}/report", response_model=AssessmentReport)
async def generate_assessment_report(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Generate comprehensive assessment report via MFO.

    - **flow_id**: Assessment flow identifier
    - Returns complete assessment report with all analysis data
    - Uses MFO integration (ADR-006) to verify flow existence
    """
    try:
        # Get flow state via MFO (checks both master and child tables)
        _ = await get_assessment_status_via_mfo(UUID(flow_id), db)

        # Get child flow data for report details
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Generate report data
        report_data = await repository.generate_assessment_report(flow_id)

        # Get summary statistics
        summary_stats = await _calculate_report_statistics(repository, flow_id)

        return AssessmentReport(
            flow_id=flow_id,
            engagement_id=flow_state.engagement_id,
            status=flow_state.status,
            created_at=flow_state.created_at,
            completed_at=flow_state.completed_at,
            applications_assessed=len(flow_state.selected_application_ids or []),
            report_data=report_data,
            summary_statistics=summary_stats,
        )

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


async def _validate_flow_completion_requirements(repository, flow_id, application_ids):
    """Validate that all applications have the required assessment data."""
    missing_data = []

    for app_id in application_ids:
        app_missing = []

        # Check for 6R decision
        sixr_decision = await repository.get_sixr_decision(flow_id, app_id)
        if not sixr_decision or not sixr_decision.get("strategy"):
            app_missing.append("6R decision")

        # Check for components analysis
        components = await repository.get_application_components(flow_id, app_id)
        if not components:
            app_missing.append("component analysis")

        # Check for tech debt analysis
        tech_debt = await repository.get_tech_debt_analysis(flow_id, app_id)
        if not tech_debt:
            app_missing.append("tech debt analysis")

        if app_missing:
            missing_data.append(
                {"application_id": app_id, "missing_items": app_missing}
            )

    return {"all_complete": len(missing_data) == 0, "missing_data": missing_data}


async def _calculate_report_statistics(repository, flow_id):
    """Calculate summary statistics for the assessment report."""
    try:
        # Get all 6R decisions
        all_decisions = await repository.get_all_sixr_decisions(flow_id)

        # Count by strategy
        strategy_counts = {}
        for app_id, decision in (all_decisions or {}).items():
            strategy = decision.get("strategy", "undefined")
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        # Calculate confidence distribution
        confidence_distribution = {"high": 0, "medium": 0, "low": 0}
        for app_id, decision in (all_decisions or {}).items():
            confidence = decision.get("confidence_level", "medium")
            if confidence in confidence_distribution:
                confidence_distribution[confidence] += 1

        return {
            "total_applications": len(all_decisions or {}),
            "strategy_distribution": strategy_counts,
            "confidence_distribution": confidence_distribution,
        }

    except Exception as e:
        logger.warning(f"Failed to calculate report statistics: {e}")
        return {
            "total_applications": 0,
            "strategy_distribution": {},
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
        }
