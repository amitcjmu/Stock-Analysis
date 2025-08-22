"""
Collection-Discovery Handoff Protocol

Manages seamless transitions between Collection and Discovery phases.
Ensures data integrity, validation requirements, and proper state management
during workflow transitions.

Agent Team: Flow orchestration and state management
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class HandoffStatus(Enum):
    """Status of handoff execution"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    REQUIRES_APPROVAL = "requires_approval"


class HandoffTrigger(Enum):
    """Triggers that can initiate handoff"""

    COLLECTION_COMPLETED = "collection_completed"
    QUALITY_THRESHOLD_MET = "quality_threshold_met"
    USER_INITIATED = "user_initiated"
    SCHEDULED = "scheduled"
    ERROR_RECOVERY = "error_recovery"


class ValidationLevel(Enum):
    """Validation strictness levels"""

    STRICT = "strict"
    STANDARD = "standard"
    LENIENT = "lenient"
    BYPASS = "bypass"


@dataclass
class HandoffCriteria:
    """Criteria that must be met for successful handoff"""

    minimum_data_quality: float
    required_fields: Set[str]
    validation_level: ValidationLevel
    approval_required: bool
    timeout_minutes: int
    rollback_on_failure: bool


@dataclass
class DataTransferPackage:
    """Package containing data and metadata for handoff"""

    source_phase: str
    target_phase: str
    data_payload: Dict[str, Any]
    metadata: Dict[str, Any]
    validation_results: Dict[str, Any]
    quality_metrics: Dict[str, float]
    transfer_timestamp: datetime


@dataclass
class HandoffExecution:
    """Record of handoff execution"""

    handoff_id: str
    flow_id: str
    trigger: HandoffTrigger
    source_phase: str
    target_phase: str
    status: HandoffStatus
    started_at: datetime
    completed_at: Optional[datetime]
    criteria: HandoffCriteria
    data_package: DataTransferPackage
    validation_errors: List[str]
    execution_log: List[Dict[str, Any]]


class CollectionDiscoveryHandoffProtocol:
    """
    Protocol for managing handoffs between Collection and Discovery phases.

    Ensures smooth transitions with proper validation, data integrity checks,
    and rollback capabilities.
    """

    def __init__(self):
        """Initialize handoff protocol."""
        self.logger = logging.getLogger(__name__)
        self._active_handoffs = {}
        self._handoff_history = []

    async def initiate_collection_to_discovery_handoff(
        self,
        flow_id: str,
        collection_results: Dict[str, Any],
        trigger: HandoffTrigger = HandoffTrigger.COLLECTION_COMPLETED,
        custom_criteria: Optional[HandoffCriteria] = None,
    ) -> HandoffExecution:
        """
        Initiate handoff from Collection phase to Discovery phase.

        Args:
            flow_id: Unique identifier for the flow
            collection_results: Results from collection phase
            trigger: What triggered this handoff
            custom_criteria: Override default handoff criteria

        Returns:
            HandoffExecution object tracking the handoff process
        """
        handoff_id = f"handoff_{flow_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Use default criteria if not provided
        criteria = custom_criteria or self._get_default_criteria()

        # Create data transfer package
        data_package = DataTransferPackage(
            source_phase="collection",
            target_phase="discovery",
            data_payload=collection_results,
            metadata={
                "flow_id": flow_id,
                "collection_timestamp": datetime.utcnow().isoformat(),
                "trigger": trigger.value,
            },
            validation_results={},  # Will be populated during validation
            quality_metrics={},  # Will be calculated during validation
            transfer_timestamp=datetime.utcnow(),
        )

        # Create handoff execution record
        handoff = HandoffExecution(
            handoff_id=handoff_id,
            flow_id=flow_id,
            trigger=trigger,
            source_phase="collection",
            target_phase="discovery",
            status=HandoffStatus.PENDING,
            started_at=datetime.utcnow(),
            completed_at=None,
            criteria=criteria,
            data_package=data_package,
            validation_errors=[],
            execution_log=[],
        )

        # Store active handoff
        self._active_handoffs[handoff_id] = handoff

        self.logger.info(f"Initiated handoff {handoff_id} for flow {flow_id}")

        # Begin execution
        return await self._execute_handoff(handoff)

    async def _execute_handoff(self, handoff: HandoffExecution) -> HandoffExecution:
        """Execute the handoff process."""
        try:
            handoff.status = HandoffStatus.IN_PROGRESS
            self._log_execution_step(handoff, "Started handoff execution")

            # Step 1: Validate data quality
            if not await self._validate_data_quality(handoff):
                handoff.status = HandoffStatus.FAILED
                return handoff

            # Step 2: Check required fields
            if not await self._validate_required_fields(handoff):
                handoff.status = HandoffStatus.FAILED
                return handoff

            # Step 3: Perform data transformation if needed
            await self._prepare_data_for_discovery(handoff)

            # Step 4: Check if approval is required
            if handoff.criteria.approval_required:
                handoff.status = HandoffStatus.REQUIRES_APPROVAL
                self._log_execution_step(handoff, "Waiting for manual approval")
                return handoff

            # Step 5: Complete handoff
            await self._finalize_handoff(handoff)

            handoff.status = HandoffStatus.COMPLETED
            handoff.completed_at = datetime.utcnow()
            self._log_execution_step(handoff, "Handoff completed successfully")

            return handoff

        except Exception as e:
            self.logger.error(f"Handoff execution failed: {e}")
            handoff.status = HandoffStatus.FAILED
            handoff.validation_errors.append(str(e))
            self._log_execution_step(handoff, f"Failed with error: {e}")

            if handoff.criteria.rollback_on_failure:
                await self._rollback_handoff(handoff)

            return handoff

    async def _validate_data_quality(self, handoff: HandoffExecution) -> bool:
        """Validate data quality meets criteria."""
        data = handoff.data_package.data_payload

        # Calculate quality metrics
        total_fields = len(data)
        populated_fields = sum(1 for v in data.values() if v is not None and v != "")

        quality_score = populated_fields / total_fields if total_fields > 0 else 0.0
        handoff.data_package.quality_metrics["completeness"] = quality_score

        # Check against criteria
        if quality_score < handoff.criteria.minimum_data_quality:
            error_msg = f"Data quality {quality_score:.2f} below threshold {handoff.criteria.minimum_data_quality}"
            handoff.validation_errors.append(error_msg)
            self._log_execution_step(handoff, error_msg)
            return False

        self._log_execution_step(
            handoff, f"Data quality validation passed: {quality_score:.2f}"
        )
        return True

    async def _validate_required_fields(self, handoff: HandoffExecution) -> bool:
        """Validate all required fields are present."""
        data = handoff.data_package.data_payload
        missing_fields = []

        for field in handoff.criteria.required_fields:
            if field not in data or data[field] is None or data[field] == "":
                missing_fields.append(field)

        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            handoff.validation_errors.append(error_msg)
            self._log_execution_step(handoff, error_msg)
            return False

        self._log_execution_step(handoff, "Required fields validation passed")
        return True

    async def _prepare_data_for_discovery(self, handoff: HandoffExecution) -> None:
        """Prepare and transform data for discovery phase."""
        # Data transformation logic would go here
        # For now, we'll just log the step
        self._log_execution_step(handoff, "Data preparation for discovery completed")

    async def _finalize_handoff(self, handoff: HandoffExecution) -> None:
        """Finalize the handoff process."""
        # Finalization logic would go here
        # This might include updating flow state, notifying downstream systems, etc.
        self._log_execution_step(handoff, "Handoff finalization completed")

    async def _rollback_handoff(self, handoff: HandoffExecution) -> None:
        """Rollback failed handoff."""
        handoff.status = HandoffStatus.ROLLED_BACK
        self._log_execution_step(handoff, "Handoff rolled back due to failure")

    def _get_default_criteria(self) -> HandoffCriteria:
        """Get default handoff criteria."""
        return HandoffCriteria(
            minimum_data_quality=0.7,
            required_fields={"application_name", "environment"},
            validation_level=ValidationLevel.STANDARD,
            approval_required=False,
            timeout_minutes=30,
            rollback_on_failure=True,
        )

    def _log_execution_step(self, handoff: HandoffExecution, message: str) -> None:
        """Log an execution step."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "status": handoff.status.value,
        }
        handoff.execution_log.append(log_entry)
        self.logger.info(f"Handoff {handoff.handoff_id}: {message}")

    async def get_handoff_status(self, handoff_id: str) -> Optional[HandoffExecution]:
        """Get status of a handoff."""
        return self._active_handoffs.get(handoff_id)

    async def approve_handoff(self, handoff_id: str, approver: str) -> bool:
        """Approve a handoff that requires manual approval."""
        handoff = self._active_handoffs.get(handoff_id)
        if not handoff or handoff.status != HandoffStatus.REQUIRES_APPROVAL:
            return False

        self._log_execution_step(handoff, f"Approved by {approver}")

        # Continue execution
        await self._finalize_handoff(handoff)
        handoff.status = HandoffStatus.COMPLETED
        handoff.completed_at = datetime.utcnow()

        return True

    async def reject_handoff(self, handoff_id: str, rejector: str, reason: str) -> bool:
        """Reject a handoff that requires manual approval."""
        handoff = self._active_handoffs.get(handoff_id)
        if not handoff or handoff.status != HandoffStatus.REQUIRES_APPROVAL:
            return False

        handoff.status = HandoffStatus.FAILED
        handoff.validation_errors.append(f"Rejected by {rejector}: {reason}")
        self._log_execution_step(handoff, f"Rejected by {rejector}: {reason}")

        if handoff.criteria.rollback_on_failure:
            await self._rollback_handoff(handoff)

        return True
