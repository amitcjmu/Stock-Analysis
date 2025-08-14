"""
Flow Progress Tracker

Provides real-time progress tracking for CrewAI flows by storing progress updates
in the database for HTTP polling. Designed for Vercel/Railway deployment where
WebSockets are not available.

Progress updates are stored in the master flow's metadata and can be retrieved
via the flow status API endpoint.
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class FlowPhase(Enum):
    """Discovery flow phases with progress percentages"""

    INITIALIZATION = ("initialization", 0)
    DATA_IMPORT = ("data_import", 10)
    DATA_VALIDATION = ("data_validation", 20)
    FIELD_MAPPING_GENERATION = ("field_mapping_generation", 30)
    FIELD_MAPPING_APPROVAL = ("field_mapping_approval", 40)
    DATA_CLEANSING = ("data_cleansing", 50)
    ASSET_INVENTORY = ("asset_inventory", 60)
    DEPENDENCY_ANALYSIS = ("dependency_analysis", 70)
    TECH_DEBT_ASSESSMENT = ("tech_debt_assessment", 80)
    SIXR_STRATEGY = ("sixr_strategy", 90)
    FINALIZATION = ("finalization", 100)

    def __init__(self, phase_name: str, progress: int):
        self.phase_name = phase_name
        self.progress = progress


class FlowProgressTracker:
    """
    Tracks flow progress updates and stores them in the database for HTTP polling.

    Key features:
    - Progress updates stored in master flow metadata
    - Phase transition tracking with handoff validation
    - Agent processing status updates
    - Error state persistence
    - Optimized for HTTP polling (no WebSocket dependency)
    """

    def __init__(self, flow_id: str, context: Any):
        self.flow_id = flow_id
        self.context = context
        self.current_phase = FlowPhase.INITIALIZATION
        self.is_processing = False
        self.awaiting_user_input = False
        self.phase_start_time = None
        self.progress_cache = {}

    async def start_phase(
        self, phase: FlowPhase, message: Optional[str] = None
    ) -> None:
        """
        Mark the start of a new phase and broadcast progress update.

        Args:
            phase: The phase being started
            message: Optional status message for the UI
        """
        self.current_phase = phase
        self.is_processing = True
        self.awaiting_user_input = False
        self.phase_start_time = datetime.utcnow()

        logger.info(f"🚀 Starting phase {phase.phase_name} for flow {self.flow_id}")

        # Broadcast progress update
        await self._broadcast_progress_update(
            phase=phase.phase_name,
            progress=phase.progress,
            status="processing",
            message=message or f"Starting {phase.phase_name.replace('_', ' ').title()}",
            is_processing=True,
            awaiting_user_input=False,
        )

    async def complete_phase(
        self,
        phase: FlowPhase,
        result: Any = None,
        next_phase: Optional[FlowPhase] = None,
        message: Optional[str] = None,
    ) -> None:
        """
        Mark phase completion and handle transition to next phase.

        Args:
            phase: The phase being completed
            result: Result data from the phase
            next_phase: The next phase to transition to
            message: Optional status message for the UI
        """
        if self.phase_start_time:
            duration = (datetime.utcnow() - self.phase_start_time).total_seconds()
            logger.info(
                f"✅ Completed phase {phase.phase_name} in {duration:.2f}s "
                f"for flow {self.flow_id}"
            )

        # Special handling for phases requiring user input
        if phase == FlowPhase.FIELD_MAPPING_GENERATION:
            self.awaiting_user_input = True
            self.is_processing = False

            await self._broadcast_progress_update(
                phase=phase.phase_name,
                progress=phase.progress,
                status="awaiting_approval",
                message=message
                or "Field mappings generated. Please review and approve.",
                is_processing=False,
                awaiting_user_input=True,
                requires_navigation=True,
                navigation_target="/discovery/attribute-mapping",
            )
        else:
            # Normal phase completion
            await self._broadcast_progress_update(
                phase=phase.phase_name,
                progress=phase.progress,
                status="completed",
                message=message
                or f"Completed {phase.phase_name.replace('_', ' ').title()}",
                is_processing=self.is_processing,
                awaiting_user_input=self.awaiting_user_input,
            )

            # Auto-transition to next phase if specified
            if next_phase and not self.awaiting_user_input:
                await asyncio.sleep(0.5)  # Brief pause for UI update
                await self.start_phase(next_phase)

    async def report_agent_activity(
        self, agent_name: str, activity: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Report agent-level activity for granular progress tracking.

        Args:
            agent_name: Name of the agent performing the activity
            activity: Description of the activity
            details: Additional details about the activity
        """
        logger.debug(f"🤖 Agent {agent_name}: {activity}")

        await self._broadcast_progress_update(
            phase=self.current_phase.phase_name,
            progress=self.current_phase.progress,
            status="processing",
            message=f"{agent_name}: {activity}",
            is_processing=True,
            awaiting_user_input=False,
            agent_activity={
                "agent": agent_name,
                "activity": activity,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def report_error(
        self, phase: FlowPhase, error: str, is_recoverable: bool = True
    ) -> None:
        """
        Report an error during phase execution.

        Args:
            phase: The phase where the error occurred
            error: Error message
            is_recoverable: Whether the error is recoverable
        """
        logger.error(f"❌ Error in phase {phase.phase_name}: {error}")

        self.is_processing = False

        await self._broadcast_progress_update(
            phase=phase.phase_name,
            progress=phase.progress,
            status="error" if is_recoverable else "failed",
            message=error,
            is_processing=False,
            awaiting_user_input=False,
            error={
                "message": error,
                "phase": phase.phase_name,
                "is_recoverable": is_recoverable,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def pause_for_user_input(
        self, phase: FlowPhase, prompt: str, navigation_target: Optional[str] = None
    ) -> None:
        """
        Pause execution and wait for user input.

        Args:
            phase: Current phase
            prompt: Message prompting user action
            navigation_target: Optional URL to navigate to
        """
        self.is_processing = False
        self.awaiting_user_input = True

        logger.info(f"⏸️ Pausing for user input in phase {phase.phase_name}")

        await self._broadcast_progress_update(
            phase=phase.phase_name,
            progress=phase.progress,
            status="awaiting_input",
            message=prompt,
            is_processing=False,
            awaiting_user_input=True,
            requires_navigation=bool(navigation_target),
            navigation_target=navigation_target,
        )

    async def resume_after_user_input(self, phase: FlowPhase) -> None:
        """Resume execution after user input."""
        self.is_processing = True
        self.awaiting_user_input = False

        logger.info(f"▶️ Resuming execution in phase {phase.phase_name}")

        await self._broadcast_progress_update(
            phase=phase.phase_name,
            progress=phase.progress,
            status="processing",
            message=f"Resuming {phase.phase_name.replace('_', ' ').title()}",
            is_processing=True,
            awaiting_user_input=False,
        )

    async def _broadcast_progress_update(
        self,
        phase: str,
        progress: int,
        status: str,
        message: str,
        is_processing: bool,
        awaiting_user_input: bool,
        **extra_data,
    ) -> None:
        """
        Store progress update in database for HTTP polling.

        Args:
            phase: Current phase name
            progress: Progress percentage (0-100)
            status: Status string
            message: Status message
            is_processing: Whether agents are currently processing
            awaiting_user_input: Whether waiting for user input
            **extra_data: Additional data to include in the event
        """
        event_data = {
            "flow_id": self.flow_id,
            "phase": phase,
            "current_phase": phase,  # Add for compatibility
            "progress": progress,
            "progress_percentage": progress,  # Add for compatibility
            "status": status,
            "workflow_status": status,  # Add for compatibility
            "message": message,
            "status_message": message,  # Add for compatibility
            "is_processing": is_processing,
            "awaiting_user_input": awaiting_user_input,
            "awaiting_user_approval": awaiting_user_input,  # Add for compatibility
            "timestamp": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            **extra_data,
        }

        # Update local cache
        self.progress_cache = event_data

        # Store in database for polling
        await self._persist_progress_to_database(event_data)

        logger.debug(f"📊 Stored progress update: {phase} - {progress}%")

    async def _persist_progress_to_database(
        self, progress_data: Dict[str, Any]
    ) -> None:
        """Persist progress data to database for HTTP polling."""
        try:
            from app.core.database import AsyncSessionLocal
            from app.repositories.master_flow_repository import MasterFlowRepository
            from app.services.crewai_flows.persistence.postgres_store import (
                PostgresFlowStateStore,
            )

            async with AsyncSessionLocal() as db:
                # Update master flow metadata for general status
                repo = MasterFlowRepository(db, self.context)
                await repo.update_flow_metadata(
                    flow_id=self.flow_id,
                    metadata_updates={
                        "last_progress_update": progress_data,
                        "last_update_timestamp": datetime.utcnow().isoformat(),
                        "current_progress": progress_data,
                    },
                )

                # Also update flow state for status endpoint
                store = PostgresFlowStateStore(db, self.context)
                await store.update_flow_status(
                    flow_id=self.flow_id,
                    status=progress_data.get("workflow_status", "processing"),
                    current_phase=progress_data.get("phase"),
                    metadata={
                        "progress_data": progress_data,
                        "is_processing": progress_data.get("is_processing"),
                        "awaiting_user_approval": progress_data.get(
                            "awaiting_user_input"
                        ),
                    },
                )

                await db.commit()
                logger.debug(
                    f"✅ Progress persisted to database for flow {self.flow_id}"
                )
        except Exception as e:
            logger.error(f"Failed to persist progress to database: {e}")


def create_progress_tracker(flow_id: str, context: Any) -> FlowProgressTracker:
    """
    Factory function to create a progress tracker.

    Args:
        flow_id: The flow ID to track
        context: Request context with tenant information

    Returns:
        FlowProgressTracker instance
    """
    return FlowProgressTracker(flow_id, context)
