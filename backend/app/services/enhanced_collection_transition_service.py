"""
Enhanced Collection to Assessment Transition Service

This service extends the collection transition logic to properly implement
the validation checklist requirements for assessment flow creation and
data transfer verification.

Key Features:
- Comprehensive readiness assessment using CollectionReadinessService
- Proper assessment_flows record creation
- Data transfer verification between collection and assessment
- Master flow synchronization
- Phase transition logging
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from pydantic import BaseModel

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow
from app.models.assessment_flow.core_models import AssessmentFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.services.collection_readiness_service import (
    CollectionReadinessService,
    ReadinessAssessmentResult,
)
from app.services.collection_data_population_service import (
    CollectionDataPopulationService,
)
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

logger = logging.getLogger(__name__)


class AssessmentTransitionRequest(BaseModel):
    """Request model for collection to assessment transition"""

    collection_flow_id: UUID
    force_transition: bool = False
    skip_readiness_check: bool = False
    selected_application_ids: Optional[List[UUID]] = None


class AssessmentTransitionResult(BaseModel):
    """Result model for assessment transition"""

    success: bool
    assessment_flow_id: Optional[UUID] = None
    master_flow_id: Optional[UUID] = None

    # Validation details
    readiness_assessment: Optional[ReadinessAssessmentResult] = None
    data_transfer_verified: bool = False

    # Transition metadata
    transitioned_at: datetime
    transitioned_by: Optional[str] = None

    # Application data
    applications_transferred: int = 0
    total_applications: int = 0

    # Status and errors
    transition_status: str = "completed"
    errors: List[str] = []
    warnings: List[str] = []

    # Next steps
    next_steps: List[Dict[str, str]] = []


class EnhancedCollectionTransitionService:
    """Enhanced service for collection to assessment transitions"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.readiness_service = CollectionReadinessService(db, context)
        self.population_service = CollectionDataPopulationService(db, context)

    async def transition_to_assessment(
        self, request: AssessmentTransitionRequest
    ) -> AssessmentTransitionResult:
        """
        Perform complete collection to assessment transition.

        Implements all validation checklist requirements:
        - Section 9: Assessment Flow Creation
        - Section 10: Data Transfer Verification
        - Master flow synchronization
        - Phase transition logging
        """
        logger.info(
            f"Starting assessment transition for collection flow {request.collection_flow_id}"
        )

        result = AssessmentTransitionResult(
            success=False,
            transitioned_at=datetime.utcnow(),
            transitioned_by=str(self.context.user_id) if self.context.user_id else None,
        )

        try:
            # 1. Get and validate collection flow
            collection_flow = await self._get_collection_flow(
                request.collection_flow_id
            )
            if not collection_flow:
                result.errors.append("Collection flow not found or access denied")
                return result

            # 2. Ensure data population is complete
            await self._ensure_data_population_complete(collection_flow)

            # 3. Perform readiness assessment (unless skipped)
            if not request.skip_readiness_check:
                readiness_result = await self.readiness_service.assess_readiness(
                    request.collection_flow_id
                )
                result.readiness_assessment = readiness_result

                if not readiness_result.is_ready and not request.force_transition:
                    result.errors.append(
                        f"Collection not ready for assessment: {readiness_result.reason}"
                    )
                    result.transition_status = "failed_readiness_check"
                    return result

                if not readiness_result.is_ready and request.force_transition:
                    result.warnings.append(
                        f"Forced transition despite readiness issues: {readiness_result.reason}"
                    )

            # 4. Create assessment flow with proper data structure
            assessment_flow = await self._create_assessment_flow(
                collection_flow, request
            )
            result.assessment_flow_id = assessment_flow.id
            result.master_flow_id = assessment_flow.master_flow_id

            # 5. Transfer data from collection to assessment
            transfer_result = await self._transfer_collection_data(
                collection_flow, assessment_flow
            )
            result.data_transfer_verified = transfer_result["success"]
            result.applications_transferred = transfer_result[
                "applications_transferred"
            ]
            result.total_applications = transfer_result["total_applications"]

            if transfer_result["errors"]:
                result.warnings.extend(transfer_result["errors"])

            # 6. Update collection flow with assessment linkage
            await self._update_collection_flow_assessment_linkage(
                collection_flow, assessment_flow
            )

            # 7. Synchronize master flow status
            if assessment_flow.master_flow_id:
                await self._synchronize_master_flow_status(
                    assessment_flow.master_flow_id, collection_flow, assessment_flow
                )

            # 8. Log phase transition
            await self._log_phase_transition(collection_flow, assessment_flow)

            # 9. Commit all changes
            await self.db.commit()

            result.success = True
            result.transition_status = "completed"
            result.next_steps = self._generate_next_steps(assessment_flow)

            logger.info(
                f"Assessment transition completed successfully. "
                f"Assessment flow: {assessment_flow.id}, "
                f"Applications transferred: {result.applications_transferred}"
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Assessment transition failed: {e}", exc_info=True)
            result.errors.append(f"Transition failed: {str(e)}")
            result.transition_status = "failed_system_error"

        return result

    async def verify_assessment_flow_data(
        self, assessment_flow_id: UUID
    ) -> Dict[str, Any]:
        """
        Verify data integrity after assessment flow creation.

        Implements Section 10 of validation checklist:
        - Data Transfer Verification
        """
        verification_result = {
            "assessment_flow_id": str(assessment_flow_id),
            "data_integrity_verified": False,
            "collection_flow_linked": False,
            "applications_data_present": False,
            "master_flow_synchronized": False,
            "issues": [],
            "recommendations": [],
        }

        try:
            # Get assessment flow
            assessment_result = await self.db.execute(
                select(AssessmentFlow).where(
                    and_(
                        AssessmentFlow.id == assessment_flow_id,
                        AssessmentFlow.client_account_id
                        == self.context.client_account_id,
                        AssessmentFlow.engagement_id == self.context.engagement_id,
                    )
                )
            )
            assessment_flow = assessment_result.scalar_one_or_none()

            if not assessment_flow:
                verification_result["issues"].append("Assessment flow not found")
                return verification_result

            # Check collection flow linkage
            collection_flow_id = assessment_flow.configuration.get("collection_flow_id")
            if collection_flow_id:
                collection_result = await self.db.execute(
                    select(CollectionFlow).where(
                        CollectionFlow.flow_id == UUID(collection_flow_id)
                    )
                )
                collection_flow = collection_result.scalar_one_or_none()

                if (
                    collection_flow
                    and collection_flow.assessment_flow_id == assessment_flow.id
                ):
                    verification_result["collection_flow_linked"] = True
                else:
                    verification_result["issues"].append(
                        "Collection flow linkage broken"
                    )
            else:
                verification_result["issues"].append(
                    "No collection flow ID in assessment configuration"
                )

            # Check applications data
            selected_app_ids = assessment_flow.configuration.get(
                "selected_application_ids", []
            )
            if selected_app_ids:
                verification_result["applications_data_present"] = True
                verification_result["application_count"] = len(selected_app_ids)
            else:
                verification_result["issues"].append(
                    "No application IDs found in assessment configuration"
                )

            # Check master flow synchronization
            if assessment_flow.master_flow_id:
                master_result = await self.db.execute(
                    select(CrewAIFlowStateExtensions).where(
                        CrewAIFlowStateExtensions.flow_id
                        == assessment_flow.master_flow_id
                    )
                )
                master_flow = master_result.scalar_one_or_none()

                if master_flow:
                    verification_result["master_flow_synchronized"] = True
                    verification_result["master_flow_status"] = master_flow.status
                else:
                    verification_result["issues"].append("Master flow not found")
            else:
                verification_result["issues"].append("No master flow ID linked")

            # Overall verification
            verification_result["data_integrity_verified"] = (
                verification_result["collection_flow_linked"]
                and verification_result["applications_data_present"]
                and verification_result["master_flow_synchronized"]
            )

            # Generate recommendations
            if not verification_result["data_integrity_verified"]:
                verification_result["recommendations"].extend(
                    [
                        "Run data integrity repair service",
                        "Verify collection flow completion status",
                        "Check master flow orchestrator configuration",
                    ]
                )

        except Exception as e:
            verification_result["issues"].append(f"Verification failed: {str(e)}")
            logger.error(f"Assessment flow data verification failed: {e}")

        return verification_result

    async def _get_collection_flow(self, flow_id: UUID) -> Optional[CollectionFlow]:
        """Get collection flow with tenant scoping"""
        result = await self.db.execute(
            select(CollectionFlow).where(
                and_(
                    CollectionFlow.flow_id == flow_id,
                    CollectionFlow.client_account_id == self.context.client_account_id,
                    CollectionFlow.engagement_id == self.context.engagement_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def _ensure_data_population_complete(
        self, collection_flow: CollectionFlow
    ) -> None:
        """Ensure all collection data is properly populated in child tables"""

        # Check if data population is needed
        apps_count = await self.db.scalar(
            f"""
            SELECT COUNT(*) FROM migration.collection_flow_applications
            WHERE collection_flow_id = '{collection_flow.id}'
            """
        )

        if apps_count == 0 and collection_flow.collection_config:
            selected_apps = collection_flow.collection_config.get(
                "selected_application_ids", []
            )
            if selected_apps:
                logger.info("Data population needed, running population service")
                await self.population_service.populate_collection_data(
                    collection_flow, force_repopulate=False
                )

    async def _create_assessment_flow(
        self, collection_flow: CollectionFlow, request: AssessmentTransitionRequest
    ) -> AssessmentFlow:
        """Create assessment flow record with proper configuration"""

        # Determine selected applications
        selected_app_ids = request.selected_application_ids or []
        if not selected_app_ids and collection_flow.collection_config:
            selected_app_ids = collection_flow.collection_config.get(
                "selected_application_ids", []
            )

        # Create master flow first (if needed)
        master_flow_id = await self._create_assessment_master_flow(collection_flow)

        # Create assessment flow record
        assessment_flow = AssessmentFlow(
            id=uuid4(),
            client_account_id=self.context.client_account_id,
            engagement_id=self.context.engagement_id,
            master_flow_id=master_flow_id,
            flow_name=f"Assessment for {collection_flow.flow_name}",
            description=f"Assessment flow created from collection flow {collection_flow.flow_id}",
            status="initialized",
            current_phase="initialization",
            progress=0.0,
            configuration={
                "collection_flow_id": str(collection_flow.flow_id),
                "selected_application_ids": [
                    str(app_id) for app_id in selected_app_ids
                ],
                "automation_tier": (
                    collection_flow.automation_tier.value
                    if hasattr(collection_flow.automation_tier, "value")
                    else str(collection_flow.automation_tier)
                ),
                "transition_date": datetime.utcnow().isoformat(),
                "transition_type": "collection_to_assessment",
            },
            flow_metadata={
                "source": "collection_transition",
                "collection_flow_status": collection_flow.status,
                "collection_progress": collection_flow.progress_percentage,
                "created_by_service": "enhanced_collection_transition_service",
            },
            started_at=datetime.utcnow(),
        )

        self.db.add(assessment_flow)
        await self.db.flush()  # Get the ID

        return assessment_flow

    async def _create_assessment_master_flow(
        self, collection_flow: CollectionFlow
    ) -> Optional[UUID]:
        """Create master flow for assessment if needed"""

        try:
            # Use MasterFlowOrchestrator to create assessment flow
            orchestrator = MasterFlowOrchestrator(self.db, self.context)

            master_flow_id = await orchestrator.create_flow(
                flow_type="assessment",
                client_account_id=self.context.client_account_id,
                engagement_id=self.context.engagement_id,
                user_id=self.context.user_id,
                flow_config={
                    "source_flow_id": str(collection_flow.flow_id),
                    "source_flow_type": "collection",
                    "transition_type": "collection_to_assessment",
                },
            )

            logger.info(f"Created assessment master flow: {master_flow_id}")
            return master_flow_id

        except Exception as e:
            logger.warning(f"Failed to create assessment master flow: {e}")
            return None

    async def _transfer_collection_data(
        self, collection_flow: CollectionFlow, assessment_flow: AssessmentFlow
    ) -> Dict[str, Any]:
        """Transfer data from collection flow to assessment flow"""

        transfer_result = {
            "success": False,
            "applications_transferred": 0,
            "total_applications": 0,
            "data_transferred": {},
            "errors": [],
        }

        try:
            # Get selected application IDs
            selected_app_ids = assessment_flow.configuration.get(
                "selected_application_ids", []
            )
            transfer_result["total_applications"] = len(selected_app_ids)

            # Transfer collection summary data
            collection_summary = collection_flow.prepare_assessment_package()

            # Update assessment flow with transferred data
            current_runtime = assessment_flow.runtime_state or {}
            current_runtime["collection_data"] = {
                "collection_summary": collection_summary,
                "gap_analysis": collection_flow.gap_analysis_results or {},
                "collection_results": collection_flow.collection_results or {},
                "phase_results": collection_flow.phase_results or {},
                "agent_insights": collection_flow.agent_insights or [],
                "collected_platforms": collection_flow.collected_platforms or [],
                "quality_metrics": {
                    "collection_quality_score": collection_flow.collection_quality_score,
                    "confidence_score": collection_flow.confidence_score,
                    "progress_percentage": collection_flow.progress_percentage,
                },
            }

            assessment_flow.runtime_state = current_runtime
            transfer_result["applications_transferred"] = len(selected_app_ids)
            transfer_result["data_transferred"] = {
                "collection_summary": True,
                "gap_analysis": bool(collection_flow.gap_analysis_results),
                "collection_results": bool(collection_flow.collection_results),
                "phase_results": bool(collection_flow.phase_results),
                "agent_insights": bool(collection_flow.agent_insights),
                "quality_metrics": True,
            }

            transfer_result["success"] = True

        except Exception as e:
            error_msg = f"Data transfer failed: {str(e)}"
            logger.error(error_msg)
            transfer_result["errors"].append(error_msg)

        return transfer_result

    async def _update_collection_flow_assessment_linkage(
        self, collection_flow: CollectionFlow, assessment_flow: AssessmentFlow
    ) -> None:
        """Update collection flow with assessment linkage"""

        # Update collection flow fields
        if hasattr(collection_flow, "assessment_flow_id"):
            collection_flow.assessment_flow_id = assessment_flow.id

        collection_flow.assessment_transition_date = datetime.utcnow()
        collection_flow.assessment_ready = True

        # Update metadata
        current_metadata = collection_flow.flow_metadata or {}
        current_metadata["assessment_transition"] = {
            "assessment_flow_id": str(assessment_flow.id),
            "transitioned_at": datetime.utcnow().isoformat(),
            "transition_status": "completed",
            "master_flow_id": (
                str(assessment_flow.master_flow_id)
                if assessment_flow.master_flow_id
                else None
            ),
        }
        collection_flow.flow_metadata = current_metadata

    async def _synchronize_master_flow_status(
        self,
        master_flow_id: UUID,
        collection_flow: CollectionFlow,
        assessment_flow: AssessmentFlow,
    ) -> None:
        """Synchronize master flow status with assessment transition"""

        try:
            # Update master flow status to indicate assessment phase
            await self.db.execute(
                update(CrewAIFlowStateExtensions)
                .where(CrewAIFlowStateExtensions.flow_id == master_flow_id)
                .values(
                    status="assessment_phase",
                    current_phase="assessment_initialization",
                    updated_at=datetime.utcnow(),
                    phase_metadata={
                        "collection_flow_id": str(collection_flow.flow_id),
                        "assessment_flow_id": str(assessment_flow.id),
                        "transition_completed_at": datetime.utcnow().isoformat(),
                        "applications_count": len(
                            assessment_flow.configuration.get(
                                "selected_application_ids", []
                            )
                        ),
                    },
                )
            )

            logger.info(
                f"Master flow {master_flow_id} synchronized with assessment transition"
            )

        except Exception as e:
            logger.error(f"Failed to synchronize master flow status: {e}")

    async def _log_phase_transition(
        self, collection_flow: CollectionFlow, assessment_flow: AssessmentFlow
    ) -> None:
        """Log the phase transition for audit purposes"""

        try:
            # This could be expanded to use a dedicated audit logging service
            transition_log = {
                "event": "collection_to_assessment_transition",
                "timestamp": datetime.utcnow().isoformat(),
                "collection_flow_id": str(collection_flow.flow_id),
                "assessment_flow_id": str(assessment_flow.id),
                "master_flow_id": (
                    str(assessment_flow.master_flow_id)
                    if assessment_flow.master_flow_id
                    else None
                ),
                "client_account_id": str(self.context.client_account_id),
                "engagement_id": str(self.context.engagement_id),
                "user_id": str(self.context.user_id) if self.context.user_id else None,
                "collection_status": collection_flow.status,
                "assessment_status": assessment_flow.status,
                "applications_count": len(
                    assessment_flow.configuration.get("selected_application_ids", [])
                ),
            }

            logger.info(f"Phase transition logged: {transition_log}")

        except Exception as e:
            logger.error(f"Failed to log phase transition: {e}")

    def _generate_next_steps(
        self, assessment_flow: AssessmentFlow
    ) -> List[Dict[str, str]]:
        """Generate next steps for the user after assessment creation"""

        next_steps = [
            {
                "action": "view_assessment_flow",
                "description": "View the newly created assessment flow",
                "endpoint": f"/api/v1/assessment/flows/{assessment_flow.id}",
                "priority": "high",
            },
            {
                "action": "start_assessment_execution",
                "description": "Begin assessment phase execution",
                "endpoint": f"/api/v1/assessment/flows/{assessment_flow.id}/execute",
                "priority": "high",
            },
            {
                "action": "review_transferred_data",
                "description": "Review data transferred from collection phase",
                "endpoint": f"/api/v1/assessment/flows/{assessment_flow.id}/data",
                "priority": "medium",
            },
        ]

        # Add application-specific next steps if applications were selected
        selected_apps = assessment_flow.configuration.get(
            "selected_application_ids", []
        )
        if selected_apps:
            next_steps.append(
                {
                    "action": "configure_applications",
                    "description": f"Configure assessment for {len(selected_apps)} selected applications",
                    "endpoint": f"/api/v1/assessment/flows/{assessment_flow.id}/applications",
                    "priority": "medium",
                }
            )

        return next_steps
