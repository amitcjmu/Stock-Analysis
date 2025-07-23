"""
Collection Flow Phase Execution Engine
Team C1 - Task C1.1

This engine now acts as a lightweight wrapper around the UnifiedCollectionFlow,
delegating the actual execution to the CrewAI Flow implementation.

The engine maintains backward compatibility while leveraging the new CrewAI-based
collection flow for all execution logic.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.exceptions import FlowError
from app.core.logging import get_logger
# Import models for backward compatibility
from app.models.collection_flow import AutomationTier
# Import the new unified collection flow
from app.services.crewai_flows.unified_collection_flow import (
    CREWAI_FLOW_AVAILABLE, UnifiedCollectionFlow,
    create_unified_collection_flow)

logger = get_logger(__name__)


class CollectionPhaseStatus(Enum):
    """Status of collection phases"""

    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    SKIPPED = "skipped"


@dataclass
class PhaseResult:
    """Result of a phase execution"""

    phase_name: str
    status: CollectionPhaseStatus
    start_time: datetime
    end_time: Optional[datetime]
    execution_time_ms: Optional[int]
    output_data: Dict[str, Any]
    quality_score: Optional[float]
    confidence_score: Optional[float]
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionContext:
    """Context for phase execution"""

    flow_id: str
    automation_tier: AutomationTier
    client_requirements: Dict[str, Any]
    environment_config: Dict[str, Any]
    quality_thresholds: Dict[str, float]
    timeout_config: Dict[str, int]


class CollectionPhaseExecutionEngine:
    """
    Collection Flow Phase Execution Engine

    This engine now delegates to the UnifiedCollectionFlow for all execution logic,
    maintaining backward compatibility with existing interfaces.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize the Collection Phase Execution Engine"""
        self.db = db
        self.context = context

        # Store CrewAI service reference (will be set when needed)
        self.crewai_service = None

        # Store reference to the unified flow instance
        self.unified_flow: Optional[UnifiedCollectionFlow] = None

        # Phase execution tracking for backward compatibility
        self.phase_results: Dict[str, PhaseResult] = {}
        self.execution_context: Optional[ExecutionContext] = None

        logger.info(
            "✅ Collection Phase Execution Engine initialized (using UnifiedCollectionFlow)"
        )

    async def execute_collection_flow(
        self,
        flow_id: str,
        automation_tier: str = "tier_2",
        client_requirements: Optional[Dict[str, Any]] = None,
        environment_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the complete Collection Flow with all phases

        This method now delegates to UnifiedCollectionFlow for execution.

        Args:
            flow_id: Unique identifier for the collection flow
            automation_tier: Level of automation (tier_1 to tier_4)
            client_requirements: Client-specific requirements and preferences
            environment_config: Environment configuration for discovery

        Returns:
            Complete execution results with all phase outputs
        """
        try:
            # Check if CrewAI is available
            if not CREWAI_FLOW_AVAILABLE:
                raise FlowError("CrewAI Flow is required for collection flow execution")

            # Get or create CrewAI service
            if not self.crewai_service:
                from app.services.crewai_flow_service import CrewAIFlowService

                self.crewai_service = CrewAIFlowService()

            # Create configuration for the flow
            config = {
                "client_requirements": client_requirements or {},
                "environment_config": environment_config or {},
                "quality_thresholds": self._get_quality_thresholds(automation_tier),
                "timeout_config": self._get_timeout_config(automation_tier),
            }

            # Create unified collection flow
            self.unified_flow = create_unified_collection_flow(
                crewai_service=self.crewai_service,
                context=self.context,
                automation_tier=automation_tier,
                flow_id=flow_id,
                db_session=self.db,
                config=config,
            )

            logger.info(
                f"🚀 Starting Collection Flow execution via UnifiedCollectionFlow: {flow_id} ({automation_tier})"
            )

            # Execute the flow
            result = await self.unified_flow.kickoff()

            # Extract phase results for backward compatibility
            if hasattr(self.unified_flow, "state") and self.unified_flow.state:
                flow_state = self.unified_flow.state

                # Convert phase results to legacy format
                for phase_name, phase_data in flow_state.phase_results.items():
                    self.phase_results[phase_name] = PhaseResult(
                        phase_name=phase_name,
                        status=CollectionPhaseStatus.COMPLETED,
                        start_time=flow_state.created_at,
                        end_time=flow_state.updated_at,
                        execution_time_ms=0,  # Not tracked in new flow
                        output_data=phase_data,
                        quality_score=phase_data.get("quality_score"),
                        confidence_score=phase_data.get("confidence_score"),
                    )

            # Return the result from unified flow
            return result

        except Exception as e:
            logger.error(f"❌ Collection Flow execution failed: {flow_id} - {str(e)}")
            raise FlowError(f"Collection Flow execution failed: {str(e)}")

    async def resume_flow(
        self, user_inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resume a paused collection flow

        Args:
            user_inputs: Optional user inputs for the paused phase

        Returns:
            Flow execution results
        """
        if not self.unified_flow:
            raise FlowError("No active collection flow to resume")

        return await self.unified_flow.resume_flow(user_inputs)

    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """
        Get the current status of a collection flow

        Args:
            flow_id: The flow ID to check

        Returns:
            Current flow status and progress
        """
        if self.unified_flow and self.unified_flow.flow_id == flow_id:
            state = self.unified_flow.state
            return {
                "flow_id": flow_id,
                "status": state.status.value if state.status else "unknown",
                "current_phase": (
                    state.current_phase.value if state.current_phase else None
                ),
                "progress": state.progress,
                "quality_score": state.collection_quality_score,
                "confidence_score": state.confidence_score,
                "errors": state.errors,
            }

        # If no active flow, would need to query database
        raise FlowError(f"No active flow with ID: {flow_id}")

    # Keep only the helper methods for backward compatibility
    def _should_skip_phase(self, phase_name: str, automation_tier: str) -> bool:
        """Determine if a phase should be skipped based on automation tier"""
        skip_rules = {
            AutomationTier.TIER_1: ["manual_collection"],  # Full automation
            AutomationTier.TIER_2: [],  # Minimal manual
            AutomationTier.TIER_3: [],  # Moderate manual
            AutomationTier.TIER_4: [],  # Manual-heavy
        }

        tier = AutomationTier(automation_tier)
        return phase_name in skip_rules.get(tier, [])

    def _is_critical_phase(self, phase_name: str) -> bool:
        """Determine if a phase is critical for flow continuation"""
        critical_phases = ["platform_detection", "synthesis"]
        return phase_name in critical_phases

    def _get_quality_thresholds(self, automation_tier: str) -> Dict[str, float]:
        """Get quality thresholds based on automation tier"""
        thresholds = {
            "tier_1": {
                "overall": 0.95,
                "platform_detection": 0.95,
                "collection": 0.95,
                "synthesis": 0.95,
            },
            "tier_2": {
                "overall": 0.85,
                "platform_detection": 0.85,
                "collection": 0.85,
                "synthesis": 0.85,
            },
            "tier_3": {
                "overall": 0.75,
                "platform_detection": 0.75,
                "collection": 0.75,
                "synthesis": 0.75,
            },
            "tier_4": {
                "overall": 0.60,
                "platform_detection": 0.60,
                "collection": 0.60,
                "synthesis": 0.60,
            },
        }
        return thresholds.get(automation_tier, thresholds["tier_2"])

    def _get_timeout_config(self, automation_tier: str) -> Dict[str, int]:
        """Get timeout configuration based on automation tier"""
        return {
            "platform_detection": 600,  # 10 minutes
            "automated_collection": 3600,  # 60 minutes
            "gap_analysis": 900,  # 15 minutes
            "manual_collection": 7200,  # 2 hours
            "synthesis": 1200,  # 20 minutes
        }
