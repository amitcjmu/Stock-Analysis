"""
Collection to Discovery Handoff Protocol
Team C1 - Task C1.4

Seamless handoff protocol between Collection Flow and Discovery Flow, ensuring proper data
transfer, validation, and continuity of the modernization assessment process.

Integrates with Master Flow Orchestrator to coordinate flow transitions and maintains
complete audit trail and data integrity throughout the handoff process.
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.exceptions import FlowError, InvalidFlowStateError
from app.core.logging import get_logger

# Import AI analysis for validation
from app.services.ai_analysis import (
    AIValidationService,
    BusinessContextAnalyzer,
    ConfidenceScoring,
)

# Import Collection Flow components
from app.services.collection_flow import (
    AuditLoggingService,
    CollectionFlowStateService,
    DataTransformationService,
    QualityAssessmentService,
)

# Import Discovery Flow integration
from app.services.discovery_flow_service import DiscoveryFlowService
from app.services.integrations.discovery_integration import DiscoveryIntegrationService

# Import Master Flow Orchestrator for flow coordination
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

logger = get_logger(__name__)


class HandoffStatus(Enum):
    """Status of handoff process"""

    INITIATED = "initiated"
    VALIDATING = "validating"
    TRANSFORMING = "transforming"
    TRANSFERRING = "transferring"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK = "rollback"


class HandoffTrigger(Enum):
    """Triggers for handoff initiation"""

    COLLECTION_COMPLETED = "collection_completed"
    QUALITY_THRESHOLD_MET = "quality_threshold_met"
    MANUAL_TRIGGER = "manual_trigger"
    SCHEDULED_TRIGGER = "scheduled_trigger"
    SIXR_READY = "sixr_ready"


class ValidationLevel(Enum):
    """Validation levels for handoff"""

    BASIC = "basic"  # Basic data presence and format validation
    STANDARD = "standard"  # Standard business rules validation
    COMPREHENSIVE = "comprehensive"  # Full validation including AI analysis
    STRICT = "strict"  # Strict validation with high confidence requirements


@dataclass
class HandoffCriteria:
    """Criteria for successful handoff"""

    minimum_quality_score: float
    minimum_confidence_score: float
    minimum_sixr_readiness: float
    required_data_completeness: float
    mandatory_phases: List[str]
    validation_level: ValidationLevel
    timeout_minutes: int
    retry_attempts: int


@dataclass
class DataTransferPackage:
    """Package of data being transferred in handoff"""

    collection_flow_id: str
    collection_results: Dict[str, Any]
    synthesized_data: List[Dict[str, Any]]
    quality_metrics: Dict[str, float]
    confidence_scores: Dict[str, float]
    sixr_readiness_data: Dict[str, Any]
    metadata: Dict[str, Any]
    validation_results: Dict[str, Any]
    transformation_log: List[Dict[str, Any]]


@dataclass
class HandoffExecution:
    """Tracking record for handoff execution"""

    handoff_id: str
    collection_flow_id: str
    discovery_flow_id: Optional[str]
    status: HandoffStatus
    trigger: HandoffTrigger
    criteria: HandoffCriteria
    data_package: Optional[DataTransferPackage]
    validation_results: Optional[Dict[str, Any]]
    start_time: datetime
    end_time: Optional[datetime]
    execution_time_ms: Optional[int]
    error_message: Optional[str]
    retry_count: int
    metadata: Dict[str, Any]


class CollectionDiscoveryHandoffProtocol:
    """
    Collection to Discovery Handoff Protocol

    Provides seamless transition between Collection and Discovery flows with:
    - Automated handoff triggering based on completion criteria
    - Comprehensive data validation and transformation
    - Quality assurance and confidence scoring
    - SIXR readiness assessment
    - Rollback capabilities for failed handoffs
    - Complete audit trail and monitoring
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize the Handoff Protocol service"""
        self.db = db
        self.context = context

        # Initialize orchestrator and flow services
        self.master_orchestrator = MasterFlowOrchestrator(db, context)
        self.discovery_service = DiscoveryFlowService(db, context)
        self.discovery_integration = DiscoveryIntegrationService(db, context)

        # Initialize collection flow services
        self.collection_state = CollectionFlowStateService(db, context)
        self.data_transformation = DataTransformationService()
        self.quality_assessment = QualityAssessmentService()
        self.audit_logging = AuditLoggingService(db, context)

        # Initialize AI analysis services
        self.ai_validation = AIValidationService()
        self.business_analyzer = BusinessContextAnalyzer()
        self.confidence_scoring = ConfidenceScoring()

        # Handoff tracking
        self.active_handoffs: Dict[str, HandoffExecution] = {}
        self.handoff_history: List[HandoffExecution] = []

        # Default configuration
        self.default_criteria = HandoffCriteria(
            minimum_quality_score=0.8,
            minimum_confidence_score=0.75,
            minimum_sixr_readiness=0.75,
            required_data_completeness=0.85,
            mandatory_phases=[
                "platform_detection",
                "automated_collection",
                "synthesis",
            ],
            validation_level=ValidationLevel.STANDARD,
            timeout_minutes=30,
            retry_attempts=3,
        )

        logger.info("✅ Collection to Discovery Handoff Protocol initialized")

    async def initiate_handoff(
        self,
        collection_flow_id: str,
        trigger: str = "collection_completed",
        criteria_overrides: Optional[Dict[str, Any]] = None,
        discovery_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Initiate handoff from Collection Flow to Discovery Flow

        Args:
            collection_flow_id: ID of the completed Collection Flow
            trigger: Trigger type for handoff initiation
            criteria_overrides: Override default handoff criteria
            discovery_config: Configuration for Discovery Flow creation

        Returns:
            Handoff ID for tracking
        """
        handoff_id = f"handoff-{uuid.uuid4()}"

        try:
            logger.info(
                f"🔄 Initiating handoff: {collection_flow_id} -> Discovery ({trigger})"
            )

            # Create handoff criteria
            criteria = self._create_handoff_criteria(criteria_overrides)

            # Create handoff execution record
            handoff_execution = HandoffExecution(
                handoff_id=handoff_id,
                collection_flow_id=collection_flow_id,
                discovery_flow_id=None,
                status=HandoffStatus.INITIATED,
                trigger=HandoffTrigger(trigger),
                criteria=criteria,
                data_package=None,
                validation_results=None,
                start_time=datetime.utcnow(),
                end_time=None,
                execution_time_ms=None,
                error_message=None,
                retry_count=0,
                metadata={
                    "discovery_config": discovery_config or {},
                    "initiated_by": self.context.user_id,
                    "tenant": self.context.client_account_id,
                    "engagement": self.context.engagement_id,
                },
            )

            # Add to active handoffs
            self.active_handoffs[handoff_id] = handoff_execution

            # Start asynchronous handoff execution
            asyncio.create_task(self._execute_handoff(handoff_execution))

            # Log audit event
            await self.audit_logging.log_handoff_event(
                handoff_id=handoff_id,
                collection_flow_id=collection_flow_id,
                event_type="handoff_initiated",
                trigger=trigger,
                metadata={"criteria": criteria.__dict__},
            )

            logger.info(f"✅ Handoff initiated: {handoff_id}")
            return handoff_id

        except Exception as e:
            logger.error(f"❌ Failed to initiate handoff: {e}")
            raise FlowError(f"Handoff initiation failed: {str(e)}")

    async def validate_handoff_readiness(
        self, collection_flow_id: str, criteria: Optional[HandoffCriteria] = None
    ) -> Dict[str, Any]:
        """
        Validate if Collection Flow is ready for handoff

        Args:
            collection_flow_id: ID of the Collection Flow to validate
            criteria: Handoff criteria to validate against

        Returns:
            Validation results with readiness status
        """
        try:
            logger.info(f"🔍 Validating handoff readiness: {collection_flow_id}")

            criteria = criteria or self.default_criteria

            # Get Collection Flow status
            collection_status = await self.master_orchestrator.get_flow_status(
                collection_flow_id, include_details=True
            )

            if not collection_status:
                raise ValueError(f"Collection Flow not found: {collection_flow_id}")

            # Extract validation data
            flow_state = collection_status.get("state", {})
            phase_results = collection_status.get("phase_results", {})
            quality_metrics = collection_status.get("quality_metrics", {})

            # Perform validation checks
            validation_results = await self._perform_comprehensive_validation(
                collection_flow_id=collection_flow_id,
                flow_state=flow_state,
                phase_results=phase_results,
                quality_metrics=quality_metrics,
                criteria=criteria,
            )

            # Determine overall readiness
            is_ready = self._determine_handoff_readiness(validation_results, criteria)

            # Generate recommendations
            recommendations = await self._generate_readiness_recommendations(
                validation_results=validation_results,
                criteria=criteria,
                is_ready=is_ready,
            )

            return {
                "collection_flow_id": collection_flow_id,
                "is_ready": is_ready,
                "overall_score": validation_results.get("overall_score", 0.0),
                "validation_results": validation_results,
                "criteria": criteria.__dict__,
                "recommendations": recommendations,
                "validated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Handoff readiness validation failed: {e}")
            raise FlowError(f"Readiness validation failed: {str(e)}")

    async def get_handoff_status(self, handoff_id: str) -> Dict[str, Any]:
        """Get status of handoff execution"""
        try:
            # Find handoff record
            handoff = self._find_handoff(handoff_id)
            if not handoff:
                raise ValueError(f"Handoff not found: {handoff_id}")

            # Build status response
            status = {
                "handoff_id": handoff_id,
                "collection_flow_id": handoff.collection_flow_id,
                "discovery_flow_id": handoff.discovery_flow_id,
                "status": handoff.status.value,
                "trigger": handoff.trigger.value,
                "start_time": handoff.start_time.isoformat(),
                "end_time": handoff.end_time.isoformat() if handoff.end_time else None,
                "execution_time_ms": handoff.execution_time_ms,
                "retry_count": handoff.retry_count,
                "error_message": handoff.error_message,
            }

            # Add detailed information
            if handoff.validation_results:
                status["validation_results"] = handoff.validation_results

            if handoff.data_package:
                status["data_transfer"] = {
                    "synthesized_data_count": len(
                        handoff.data_package.synthesized_data
                    ),
                    "quality_metrics": handoff.data_package.quality_metrics,
                    "confidence_scores": handoff.data_package.confidence_scores,
                    "sixr_readiness": handoff.data_package.sixr_readiness_data,
                }

            return status

        except Exception as e:
            logger.error(f"❌ Failed to get handoff status: {e}")
            raise FlowError(f"Failed to get handoff status: {str(e)}")

    async def cancel_handoff(
        self, handoff_id: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel an active handoff"""
        try:
            handoff = self._find_handoff(handoff_id)
            if not handoff:
                raise ValueError(f"Handoff not found: {handoff_id}")

            if handoff.status not in [
                HandoffStatus.INITIATED,
                HandoffStatus.VALIDATING,
                HandoffStatus.TRANSFORMING,
            ]:
                raise InvalidFlowStateError(
                    f"Cannot cancel handoff in status: {handoff.status.value}"
                )

            # Update handoff status
            handoff.status = HandoffStatus.FAILED
            handoff.end_time = datetime.utcnow()
            handoff.error_message = reason or "Cancelled by user"
            handoff.execution_time_ms = int(
                (handoff.end_time - handoff.start_time).total_seconds() * 1000
            )

            # Move to history
            if handoff_id in self.active_handoffs:
                del self.active_handoffs[handoff_id]
            self.handoff_history.append(handoff)

            # Log audit event
            await self.audit_logging.log_handoff_event(
                handoff_id=handoff_id,
                collection_flow_id=handoff.collection_flow_id,
                event_type="handoff_cancelled",
                metadata={"reason": reason},
            )

            logger.info(f"❌ Handoff cancelled: {handoff_id}")
            return {"handoff_id": handoff_id, "status": "cancelled", "reason": reason}

        except Exception as e:
            logger.error(f"❌ Failed to cancel handoff: {e}")
            raise

    async def list_handoffs(
        self,
        collection_flow_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List handoffs with optional filtering"""
        try:
            # Combine all handoffs
            all_handoffs = (
                list(self.active_handoffs.values()) + self.handoff_history[-100:]
            )

            # Apply filters
            if collection_flow_id:
                all_handoffs = [
                    h
                    for h in all_handoffs
                    if h.collection_flow_id == collection_flow_id
                ]

            if status_filter:
                all_handoffs = [
                    h for h in all_handoffs if h.status.value == status_filter
                ]

            # Sort by start time (newest first)
            all_handoffs.sort(key=lambda h: h.start_time, reverse=True)

            # Limit results
            limited_handoffs = all_handoffs[:limit]

            # Build response
            handoff_list = []
            for handoff in limited_handoffs:
                handoff_list.append(
                    {
                        "handoff_id": handoff.handoff_id,
                        "collection_flow_id": handoff.collection_flow_id,
                        "discovery_flow_id": handoff.discovery_flow_id,
                        "status": handoff.status.value,
                        "trigger": handoff.trigger.value,
                        "start_time": handoff.start_time.isoformat(),
                        "end_time": (
                            handoff.end_time.isoformat() if handoff.end_time else None
                        ),
                        "execution_time_ms": handoff.execution_time_ms,
                        "retry_count": handoff.retry_count,
                        "error_message": handoff.error_message,
                    }
                )

            return handoff_list

        except Exception as e:
            logger.error(f"❌ Failed to list handoffs: {e}")
            raise FlowError(f"Failed to list handoffs: {str(e)}")

    # Private methods

    async def _execute_handoff(self, handoff: HandoffExecution):
        """Execute the complete handoff process"""
        try:
            logger.info(f"🚀 Executing handoff: {handoff.handoff_id}")

            # Step 1: Validate Collection Flow readiness
            handoff.status = HandoffStatus.VALIDATING
            validation_results = await self._validate_collection_flow(handoff)
            handoff.validation_results = validation_results

            if not validation_results.get("is_ready", False):
                raise FlowError(
                    f"Collection Flow not ready for handoff: {validation_results.get('reason', 'Unknown')}"
                )

            # Step 2: Transform and package data
            handoff.status = HandoffStatus.TRANSFORMING
            data_package = await self._create_data_transfer_package(handoff)
            handoff.data_package = data_package

            # Step 3: Transfer to Discovery Flow
            handoff.status = HandoffStatus.TRANSFERRING
            discovery_flow_id = await self._transfer_to_discovery_flow(
                handoff, data_package
            )
            handoff.discovery_flow_id = discovery_flow_id

            # Step 4: Complete handoff
            handoff.status = HandoffStatus.COMPLETED
            handoff.end_time = datetime.utcnow()
            handoff.execution_time_ms = int(
                (handoff.end_time - handoff.start_time).total_seconds() * 1000
            )

            # Move to history
            if handoff.handoff_id in self.active_handoffs:
                del self.active_handoffs[handoff.handoff_id]
            self.handoff_history.append(handoff)

            # Log completion
            await self.audit_logging.log_handoff_event(
                handoff_id=handoff.handoff_id,
                collection_flow_id=handoff.collection_flow_id,
                event_type="handoff_completed",
                metadata={
                    "discovery_flow_id": discovery_flow_id,
                    "execution_time_ms": handoff.execution_time_ms,
                    "data_points_transferred": len(data_package.synthesized_data),
                },
            )

            logger.info(
                f"✅ Handoff completed: {handoff.handoff_id} -> {discovery_flow_id}"
            )

        except Exception as e:
            # Handle handoff failure
            handoff.status = HandoffStatus.FAILED
            handoff.end_time = datetime.utcnow()
            handoff.execution_time_ms = int(
                (handoff.end_time - handoff.start_time).total_seconds() * 1000
            )
            handoff.error_message = str(e)

            logger.error(f"❌ Handoff failed: {handoff.handoff_id} - {str(e)}")

            # Check if retry is needed
            if handoff.retry_count < handoff.criteria.retry_attempts:
                await self._schedule_handoff_retry(handoff)
            else:
                # Move to history after max retries
                if handoff.handoff_id in self.active_handoffs:
                    del self.active_handoffs[handoff.handoff_id]
                self.handoff_history.append(handoff)

                # Log failure
                await self.audit_logging.log_handoff_event(
                    handoff_id=handoff.handoff_id,
                    collection_flow_id=handoff.collection_flow_id,
                    event_type="handoff_failed",
                    metadata={"error": str(e), "retry_count": handoff.retry_count},
                )

    async def _validate_collection_flow(
        self, handoff: HandoffExecution
    ) -> Dict[str, Any]:
        """Validate Collection Flow for handoff readiness"""
        return await self.validate_handoff_readiness(
            collection_flow_id=handoff.collection_flow_id, criteria=handoff.criteria
        )

    async def _create_data_transfer_package(
        self, handoff: HandoffExecution
    ) -> DataTransferPackage:
        """Create data transfer package for Discovery Flow"""

        # Get Collection Flow results
        collection_status = await self.master_orchestrator.get_flow_status(
            handoff.collection_flow_id, include_details=True
        )

        collection_results = collection_status.get("result", {})
        phase_results = collection_status.get("phase_results", {})

        # Extract synthesized data
        synthesized_data = []
        if "synthesis" in phase_results:
            synthesis_output = phase_results["synthesis"].get("output_data", {})
            synthesized_data = synthesis_output.get("synthesized_data", [])

        # Transform data for Discovery Flow format
        transformed_data = await self.data_transformation.transform_for_discovery_flow(
            synthesized_data=synthesized_data,
            collection_metadata=collection_results.get("metadata", {}),
            automation_tier=collection_results.get("automation_tier", "tier_2"),
        )

        # Calculate quality metrics
        quality_metrics = (
            await self.quality_assessment.calculate_handoff_quality_metrics(
                synthesized_data=transformed_data,
                phase_results=phase_results,
                collection_metadata=collection_results.get("metadata", {}),
            )
        )

        # Calculate confidence scores
        confidence_scores = await self.confidence_scoring.calculate_handoff_confidence(
            data=transformed_data,
            quality_metrics=quality_metrics,
            phase_results=phase_results,
        )

        # Assess SIXR readiness
        sixr_readiness = await self.business_analyzer.assess_sixr_handoff_readiness(
            synthesized_data=transformed_data,
            quality_metrics=quality_metrics,
            confidence_scores=confidence_scores,
        )

        # Create validation log
        validation_results = await self.ai_validation.validate_handoff_data(
            data=transformed_data,
            quality_metrics=quality_metrics,
            validation_level=handoff.criteria.validation_level.value,
        )

        # Create transformation log
        transformation_log = [
            {
                "step": "data_extraction",
                "timestamp": datetime.utcnow().isoformat(),
                "source_data_count": len(synthesized_data),
                "status": "completed",
            },
            {
                "step": "format_transformation",
                "timestamp": datetime.utcnow().isoformat(),
                "transformed_data_count": len(transformed_data),
                "status": "completed",
            },
            {
                "step": "quality_assessment",
                "timestamp": datetime.utcnow().isoformat(),
                "overall_quality": quality_metrics.get("overall_quality", 0.0),
                "status": "completed",
            },
            {
                "step": "validation",
                "timestamp": datetime.utcnow().isoformat(),
                "validation_passed": validation_results.get("passed", False),
                "status": "completed",
            },
        ]

        return DataTransferPackage(
            collection_flow_id=handoff.collection_flow_id,
            collection_results=collection_results,
            synthesized_data=transformed_data,
            quality_metrics=quality_metrics,
            confidence_scores=confidence_scores,
            sixr_readiness_data=sixr_readiness,
            metadata={
                "transformation_timestamp": datetime.utcnow().isoformat(),
                "automation_tier": collection_results.get("automation_tier"),
                "phase_count": len(phase_results),
                "handoff_criteria": handoff.criteria.__dict__,
            },
            validation_results=validation_results,
            transformation_log=transformation_log,
        )

    async def _transfer_to_discovery_flow(
        self, handoff: HandoffExecution, data_package: DataTransferPackage
    ) -> str:
        """Transfer data to new Discovery Flow"""

        # Prepare Discovery Flow configuration
        discovery_config = {
            "source_flow_type": "collection",
            "source_flow_id": handoff.collection_flow_id,
            "handoff_id": handoff.handoff_id,
            "automation_context": {
                "automation_tier": data_package.collection_results.get(
                    "automation_tier"
                ),
                "quality_level": data_package.quality_metrics.get("overall_quality"),
                "confidence_level": data_package.confidence_scores.get(
                    "overall_confidence"
                ),
            },
            "discovery_preferences": handoff.metadata.get("discovery_config", {}),
            "sixr_context": data_package.sixr_readiness_data,
        }

        # Prepare initial Discovery Flow state
        initial_state = {
            "source_collection_data": data_package.synthesized_data,
            "collection_metadata": data_package.metadata,
            "quality_metrics": data_package.quality_metrics,
            "confidence_scores": data_package.confidence_scores,
            "handoff_timestamp": datetime.utcnow().isoformat(),
            "handoff_validation": data_package.validation_results,
        }

        # Create Discovery Flow using Master Flow Orchestrator
        (
            discovery_flow_id,
            discovery_flow_data,
        ) = await self.master_orchestrator.create_flow(
            flow_type="discovery",
            flow_name=f"Discovery Flow from Collection {handoff.collection_flow_id}",
            configuration=discovery_config,
            initial_state=initial_state,
        )

        # Initialize Discovery Flow with transferred data
        await self.discovery_integration.initialize_from_collection_handoff(
            discovery_flow_id=str(discovery_flow_id),
            data_package=data_package,
            handoff_context={
                "handoff_id": handoff.handoff_id,
                "collection_flow_id": handoff.collection_flow_id,
                "transfer_timestamp": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"📊 Data transferred to Discovery Flow: {discovery_flow_id}")
        return str(discovery_flow_id)

    async def _perform_comprehensive_validation(
        self,
        collection_flow_id: str,
        flow_state: Dict[str, Any],
        phase_results: Dict[str, Any],
        quality_metrics: Dict[str, Any],
        criteria: HandoffCriteria,
    ) -> Dict[str, Any]:
        """Perform comprehensive validation for handoff readiness"""

        validation_results = {
            "overall_score": 0.0,
            "validation_checks": {},
            "passed_checks": 0,
            "total_checks": 0,
            "failures": [],
            "warnings": [],
        }

        # Check 1: Flow completion status
        flow_status = flow_state.get("status", "")
        completion_check = flow_status in ["completed", "completed_with_failures"]
        validation_results["validation_checks"]["flow_completion"] = {
            "passed": completion_check,
            "value": flow_status,
            "requirement": "completed or completed_with_failures",
        }
        if completion_check:
            validation_results["passed_checks"] += 1
        else:
            validation_results["failures"].append("Flow not completed")
        validation_results["total_checks"] += 1

        # Check 2: Mandatory phases completion
        mandatory_phases_check = True
        for phase in criteria.mandatory_phases:
            if phase not in phase_results:
                mandatory_phases_check = False
                validation_results["failures"].append(
                    f"Mandatory phase missing: {phase}"
                )
            elif phase_results[phase].get("status") != "completed":
                mandatory_phases_check = False
                validation_results["failures"].append(
                    f"Mandatory phase not completed: {phase}"
                )

        validation_results["validation_checks"]["mandatory_phases"] = {
            "passed": mandatory_phases_check,
            "completed_phases": list(phase_results.keys()),
            "required_phases": criteria.mandatory_phases,
        }
        if mandatory_phases_check:
            validation_results["passed_checks"] += 1
        validation_results["total_checks"] += 1

        # Check 3: Quality score threshold
        overall_quality = quality_metrics.get("overall_quality_score", 0.0)
        quality_check = overall_quality >= criteria.minimum_quality_score
        validation_results["validation_checks"]["quality_threshold"] = {
            "passed": quality_check,
            "value": overall_quality,
            "requirement": criteria.minimum_quality_score,
        }
        if quality_check:
            validation_results["passed_checks"] += 1
        else:
            validation_results["failures"].append(
                f"Quality score below threshold: {overall_quality} < {criteria.minimum_quality_score}"
            )
        validation_results["total_checks"] += 1

        # Check 4: Confidence score threshold
        overall_confidence = quality_metrics.get("overall_confidence_score", 0.0)
        confidence_check = overall_confidence >= criteria.minimum_confidence_score
        validation_results["validation_checks"]["confidence_threshold"] = {
            "passed": confidence_check,
            "value": overall_confidence,
            "requirement": criteria.minimum_confidence_score,
        }
        if confidence_check:
            validation_results["passed_checks"] += 1
        else:
            validation_results["failures"].append(
                f"Confidence score below threshold: {overall_confidence} < {criteria.minimum_confidence_score}"
            )
        validation_results["total_checks"] += 1

        # Check 5: SIXR readiness
        sixr_readiness = flow_state.get("sixr_readiness_score", 0.0)
        sixr_check = sixr_readiness >= criteria.minimum_sixr_readiness
        validation_results["validation_checks"]["sixr_readiness"] = {
            "passed": sixr_check,
            "value": sixr_readiness,
            "requirement": criteria.minimum_sixr_readiness,
        }
        if sixr_check:
            validation_results["passed_checks"] += 1
        else:
            validation_results["failures"].append(
                f"SIXR readiness below threshold: {sixr_readiness} < {criteria.minimum_sixr_readiness}"
            )
        validation_results["total_checks"] += 1

        # Check 6: Data completeness
        data_summary = flow_state.get("data_summary", {})
        synthesized_count = data_summary.get("synthesized_data_points", 0)
        total_expected = data_summary.get(
            "total_platforms_detected", 1
        )  # Avoid division by zero
        completeness = synthesized_count / max(total_expected, 1)
        completeness_check = completeness >= criteria.required_data_completeness
        validation_results["validation_checks"]["data_completeness"] = {
            "passed": completeness_check,
            "value": completeness,
            "requirement": criteria.required_data_completeness,
            "synthesized_count": synthesized_count,
            "expected_count": total_expected,
        }
        if completeness_check:
            validation_results["passed_checks"] += 1
        else:
            validation_results["failures"].append(
                f"Data completeness below threshold: {completeness:.2f} < {criteria.required_data_completeness}"
            )
        validation_results["total_checks"] += 1

        # Calculate overall score
        if validation_results["total_checks"] > 0:
            validation_results["overall_score"] = (
                validation_results["passed_checks"] / validation_results["total_checks"]
            )

        return validation_results

    def _determine_handoff_readiness(
        self, validation_results: Dict[str, Any], criteria: HandoffCriteria
    ) -> bool:
        """Determine if handoff is ready based on validation results"""

        # All critical checks must pass
        critical_checks = ["flow_completion", "mandatory_phases", "quality_threshold"]
        for check in critical_checks:
            if (
                not validation_results["validation_checks"]
                .get(check, {})
                .get("passed", False)
            ):
                return False

        # Overall score must meet minimum threshold
        min_overall_score = 0.8  # 80% of checks must pass
        if validation_results["overall_score"] < min_overall_score:
            return False

        return True

    async def _generate_readiness_recommendations(
        self,
        validation_results: Dict[str, Any],
        criteria: HandoffCriteria,
        is_ready: bool,
    ) -> List[str]:
        """Generate recommendations for handoff readiness"""
        recommendations = []

        if is_ready:
            recommendations.append(
                "Collection Flow is ready for handoff to Discovery Flow"
            )

            # Add optimization suggestions
            if validation_results["overall_score"] < 1.0:
                recommendations.append(
                    "Consider addressing minor validation warnings for optimal handoff"
                )
        else:
            recommendations.append(
                "Collection Flow requires improvements before handoff"
            )

            # Add specific recommendations based on failures
            for failure in validation_results.get("failures", []):
                if "Quality score" in failure:
                    recommendations.append(
                        "Improve data collection quality through additional validation or manual collection"
                    )
                elif "Confidence score" in failure:
                    recommendations.append(
                        "Increase confidence through improved automation or validation processes"
                    )
                elif "SIXR readiness" in failure:
                    recommendations.append(
                        "Enhance SIXR alignment through better business context analysis"
                    )
                elif "Data completeness" in failure:
                    recommendations.append(
                        "Collect additional data to improve completeness metrics"
                    )
                elif "phase" in failure.lower():
                    recommendations.append(f"Complete required phase: {failure}")

        return recommendations

    async def _schedule_handoff_retry(self, handoff: HandoffExecution):
        """Schedule handoff retry with backoff"""
        handoff.retry_count += 1

        # Calculate retry delay (exponential backoff)
        base_delay = 60  # 1 minute base delay
        retry_delay = base_delay * (2 ** (handoff.retry_count - 1))
        max_delay = 1800  # 30 minutes max
        retry_delay = min(retry_delay, max_delay)

        # Reset handoff for retry
        handoff.status = HandoffStatus.INITIATED
        handoff.start_time = datetime.utcnow() + timedelta(seconds=retry_delay)
        handoff.end_time = None
        handoff.execution_time_ms = None
        handoff.error_message = None
        handoff.validation_results = None
        handoff.data_package = None

        logger.info(
            f"🔄 Scheduled handoff retry {handoff.retry_count}: {handoff.handoff_id} (delay: {retry_delay}s)"
        )

        # Schedule retry execution
        async def delayed_retry():
            await asyncio.sleep(retry_delay)
            await self._execute_handoff(handoff)

        asyncio.create_task(delayed_retry())

    def _create_handoff_criteria(
        self, criteria_overrides: Optional[Dict[str, Any]]
    ) -> HandoffCriteria:
        """Create handoff criteria with optional overrides"""
        criteria = HandoffCriteria(
            minimum_quality_score=self.default_criteria.minimum_quality_score,
            minimum_confidence_score=self.default_criteria.minimum_confidence_score,
            minimum_sixr_readiness=self.default_criteria.minimum_sixr_readiness,
            required_data_completeness=self.default_criteria.required_data_completeness,
            mandatory_phases=self.default_criteria.mandatory_phases.copy(),
            validation_level=self.default_criteria.validation_level,
            timeout_minutes=self.default_criteria.timeout_minutes,
            retry_attempts=self.default_criteria.retry_attempts,
        )

        # Apply overrides using secure attribute setting
        if criteria_overrides:
            from app.core.security.secure_setattr import secure_setattr, SAFE_ATTRIBUTES

            # Define allowed attributes for handoff criteria updates
            allowed_attrs = SAFE_ATTRIBUTES | {
                "validation_level",
                "required_confidence",
                "timeout_seconds",
                "max_attempts",
                "error_threshold",
                "success_criteria",
                "failure_criteria",
                "enabled",
                "priority",
            }

            for key, value in criteria_overrides.items():
                if hasattr(criteria, key):
                    if key == "validation_level":
                        processed_value = ValidationLevel(value)
                    else:
                        processed_value = value

                    if not secure_setattr(
                        criteria, key, processed_value, allowed_attrs, strict_mode=False
                    ):
                        self.logger.warning(
                            f"Skipped updating potentially sensitive criteria attribute: {key}"
                        )

        return criteria

    def _find_handoff(self, handoff_id: str) -> Optional[HandoffExecution]:
        """Find handoff by ID"""
        # Check active handoffs
        if handoff_id in self.active_handoffs:
            return self.active_handoffs[handoff_id]

        # Check history
        for handoff in self.handoff_history:
            if handoff.handoff_id == handoff_id:
                return handoff

        return None
