"""
State management utilities for phase handlers.
Provides state tracking and enrichment functionality.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class StateUtils:
    """Utilities for state management and tracking."""

    def __init__(self, flow_instance):
        """Initialize with reference to the main flow instance."""
        self.flow = flow_instance
        self.logger = logger

    async def add_phase_transition(
        self, phase: str, status: str, metadata: Dict[str, Any] = None
    ):
        """Add phase transition to master flow record for enrichment tracking."""
        try:
            if hasattr(self.flow, "flow_bridge") and self.flow.flow_bridge:
                from app.core.database import AsyncSessionLocal
                from app.repositories.crewai_flow_state_extensions_repository import (
                    CrewAIFlowStateExtensionsRepository,
                )

                async with AsyncSessionLocal() as db:
                    master_repo = CrewAIFlowStateExtensionsRepository(
                        db=db,
                        client_account_id=self.flow.context.client_account_id,
                        engagement_id=self.flow.context.engagement_id,
                        user_id=self.flow.context.user_id,
                    )
                    await master_repo.add_phase_transition(
                        flow_id=self.flow._flow_id,
                        phase=phase,
                        status=status,
                        metadata=metadata,
                    )

        except Exception as e:
            self.logger.warning(
                f"⚠️ [ENRICHMENT] Failed to add phase transition {phase}:{status}: {e}"
            )

    async def record_phase_execution_time(self, phase: str, execution_time_ms: float):
        """Record phase execution time in master flow record."""
        try:
            if hasattr(self.flow, "flow_bridge") and self.flow.flow_bridge:
                from app.core.database import AsyncSessionLocal
                from app.repositories.crewai_flow_state_extensions_repository import (
                    CrewAIFlowStateExtensionsRepository,
                )

                async with AsyncSessionLocal() as db:
                    master_repo = CrewAIFlowStateExtensionsRepository(
                        db=db,
                        client_account_id=self.flow.context.client_account_id,
                        engagement_id=self.flow.context.engagement_id,
                        user_id=self.flow.context.user_id,
                    )
                    await master_repo.record_phase_execution_time(
                        flow_id=self.flow._flow_id,
                        phase=phase,
                        execution_time_ms=execution_time_ms,
                    )

        except Exception as e:
            self.logger.warning(
                f"⚠️ [ENRICHMENT] Failed to record execution time for {phase}: {e}"
            )

    async def add_error_entry(
        self, phase: str, error: str, details: Dict[str, Any] = None
    ):
        """Add error entry to master flow record."""
        try:
            if hasattr(self.flow, "flow_bridge") and self.flow.flow_bridge:
                from app.core.database import AsyncSessionLocal
                from app.repositories.crewai_flow_state_extensions_repository import (
                    CrewAIFlowStateExtensionsRepository,
                )

                async with AsyncSessionLocal() as db:
                    master_repo = CrewAIFlowStateExtensionsRepository(
                        db=db,
                        client_account_id=self.flow.context.client_account_id,
                        engagement_id=self.flow.context.engagement_id,
                        user_id=self.flow.context.user_id,
                    )
                    await master_repo.add_error_entry(
                        flow_id=self.flow._flow_id,
                        phase=phase,
                        error=error,
                        details=details,
                    )

        except Exception as e:
            self.logger.warning(
                f"⚠️ [ENRICHMENT] Failed to add error entry for {phase}: {e}"
            )

    async def append_agent_collaboration(self, entry: Dict[str, Any]):
        """Append agent collaboration entry to master flow record."""
        try:
            if hasattr(self.flow, "flow_bridge") and self.flow.flow_bridge:
                from app.core.database import AsyncSessionLocal
                from app.repositories.crewai_flow_state_extensions_repository import (
                    CrewAIFlowStateExtensionsRepository,
                )

                async with AsyncSessionLocal() as db:
                    master_repo = CrewAIFlowStateExtensionsRepository(
                        db=db,
                        client_account_id=self.flow.context.client_account_id,
                        engagement_id=self.flow.context.engagement_id,
                        user_id=self.flow.context.user_id,
                    )
                    await master_repo.append_agent_collaboration(
                        flow_id=self.flow._flow_id, entry=entry
                    )

        except Exception as e:
            self.logger.warning(
                f"⚠️ [ENRICHMENT] Failed to append agent collaboration entry: {e}"
            )
