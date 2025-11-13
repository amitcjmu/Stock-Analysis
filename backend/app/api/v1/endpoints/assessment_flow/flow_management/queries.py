"""
Assessment flow query endpoints.
Handles retrieval of flow status, applications, and phase navigation.
Uses MFO integration layer per ADR-006 (Master Flow Orchestrator pattern).
"""

import logging
from typing import List
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
    AssessmentApplicationInfo,
    AssessmentFlowStatusResponse,
)

# Import MFO integration functions (per ADR-006)
from ..mfo_integration import get_assessment_status_via_mfo

# Import integration services
try:
    from app.services.integrations.discovery_integration import DiscoveryFlowIntegration

    DISCOVERY_INTEGRATION_AVAILABLE = True
except ImportError:
    DISCOVERY_INTEGRATION_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{flow_id}/status", response_model=AssessmentFlowStatusResponse)
async def get_assessment_flow_status(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get current status and progress of assessment flow via MFO.

    - **flow_id**: Assessment flow identifier
    - Returns detailed status including phase data and progress
    - Uses MFO integration (ADR-006) for unified state view
    """
    try:
        # Get unified status via MFO (queries both master and child tables)
        mfo_state = await get_assessment_status_via_mfo(UUID(flow_id), db)

        # For backward compatibility, also get child flow data for phase_data
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        # Calculate progress based on completed phases
        progress_percentage = mfo_state.get("progress", 0)

        return AssessmentFlowStatusResponse(
            flow_id=flow_id,
            status=mfo_state["status"],
            current_phase=mfo_state["current_phase"],
            progress_percentage=progress_percentage,
            phase_data=flow_state.phase_data if flow_state else {},
            created_at=mfo_state["created_at"],
            updated_at=mfo_state["updated_at"],
            selected_applications=mfo_state["selected_applications"],
            assessment_complete=(
                mfo_state["status"] == AssessmentFlowStatus.COMPLETED.value
            ),
        )

    except ValueError:
        logger.warning(
            safe_log_format(
                "Assessment flow not found: flow_id={flow_id}", flow_id=flow_id
            )
        )
        raise HTTPException(status_code=404, detail="Assessment flow not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to get assessment flow status: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(status_code=500, detail="Failed to get flow status")


@router.get("/{flow_id}/applications", response_model=List[AssessmentApplicationInfo])
async def get_assessment_flow_applications(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get applications in assessment flow with their details.

    - **flow_id**: Assessment flow identifier
    - Returns list of applications with names, types, and other metadata
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        if not flow_state.selected_application_ids:
            return []

        # Get application details using Discovery Integration
        applications = []
        if DISCOVERY_INTEGRATION_AVAILABLE:
            discovery_integration = DiscoveryFlowIntegration()

            for app_id in flow_state.selected_application_ids:
                try:
                    # Get application metadata from discovery
                    metadata = await discovery_integration.get_application_metadata(
                        db, str(app_id), client_account_id
                    )

                    # Extract basic info for the response
                    basic_info = metadata.get("basic_info", {})
                    technical_info = metadata.get("technical_info", {})
                    assessment_readiness = metadata.get("assessment_readiness", {})
                    discovery_info = metadata.get("discovery_info", {})

                    app_info = AssessmentApplicationInfo(
                        id=basic_info.get("id", str(app_id)),
                        name=basic_info.get("name", f"Application {app_id}"),
                        type=basic_info.get("type"),
                        environment=basic_info.get("environment"),
                        business_criticality=basic_info.get("business_criticality"),
                        technology_stack=technical_info.get("technology_stack", []),
                        complexity_score=metadata.get("performance_metrics", {}).get(
                            "complexity_score"
                        ),
                        readiness_score=assessment_readiness.get("score"),
                        discovery_completed_at=discovery_info.get("completed_at"),
                    )
                    applications.append(app_info)

                except Exception as e:
                    logger.warning(
                        safe_log_format(
                            "Failed to get metadata for application {app_id}: {str_e}",
                            app_id=str(app_id),
                            str_e=str(e),
                        )
                    )
                    # Add fallback entry with just ID and name
                    applications.append(
                        AssessmentApplicationInfo(
                            id=str(app_id),
                            name=f"Application {app_id}",
                        )
                    )
        else:
            # Fallback when Discovery Integration is not available
            for app_id in flow_state.selected_application_ids:
                applications.append(
                    AssessmentApplicationInfo(
                        id=str(app_id),
                        name=f"Application {app_id}",
                    )
                )

        return applications

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to get assessment flow applications: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(status_code=500, detail="Failed to get applications")
