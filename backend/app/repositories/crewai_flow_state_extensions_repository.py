"""
CrewAI Flow State Extensions Repository (modularized facade)

This module now provides a thin facade over modular components:
- base.py (BaseRepo with init, feature flags, serialization)
- queries.py (read-only queries)
- enrichment.py (JSONB enrichment helpers)
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.crewai_flow_state_extensions.base import BaseRepo
from app.repositories.crewai_flow_state_extensions.queries import MasterFlowQueries
from app.repositories.crewai_flow_state_extensions.enrichment import (
    MasterFlowEnrichment,
)
from app.repositories.crewai_flow_state_extensions.commands import MasterFlowCommands

logger = logging.getLogger(__name__)


class CrewAIFlowStateExtensionsRepository(BaseRepo):
    """
    Repository for master CrewAI flow state management.
    This is the central coordination table for all flow types.
    """

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str = None,
        user_id: Optional[str] = None,
    ):
        # BaseRepo handles UUID parsing and demo fallbacks
        super().__init__(
            db=db,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            user_id=user_id,
        )
        self.queries = MasterFlowQueries(db, self.client_account_id, self.engagement_id)
        self.enrich = MasterFlowEnrichment(
            db, self.client_account_id, self.engagement_id, user_id
        )
        self.commands = MasterFlowCommands(
            db, self.client_account_id, self.engagement_id, user_id
        )

    async def create_master_flow(
        self,
        flow_id: str,
        flow_type: str,
        user_id: str = None,
        flow_name: str = None,
        flow_configuration: Dict[str, Any] = None,
        initial_state: Dict[str, Any] = None,
        auto_commit: bool = True,
    ) -> CrewAIFlowStateExtensions:
        return await self.commands.create_master_flow(
            flow_id,
            flow_type,
            user_id,
            flow_name,
            flow_configuration,
            initial_state,
            auto_commit,
        )

    async def get_by_flow_id(self, flow_id: str) -> Optional[CrewAIFlowStateExtensions]:
        return await self.queries.get_by_flow_id(flow_id)

    async def get_by_flow_id_global(
        self, flow_id: str
    ) -> Optional[CrewAIFlowStateExtensions]:
        return await self.queries.get_by_flow_id_global(flow_id)

    # Delegate JSON serialization to BaseRepo implementation
    def _ensure_json_serializable(
        self, obj: Any, _visited: Optional[set] = None, _depth: int = 0
    ) -> Any:
        return super()._ensure_json_serializable(obj, _visited, _depth)

    async def update_flow_status(
        self,
        flow_id: str,
        status: str,
        phase_data: Dict[str, Any] = None,
        collaboration_entry: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
    ) -> CrewAIFlowStateExtensions:
        return await self.commands.update_flow_status(
            flow_id, status, phase_data, collaboration_entry, metadata
        )

    async def get_flows_by_type(
        self, flow_type: str, limit: int = 10
    ) -> List[CrewAIFlowStateExtensions]:
        return await self.queries.get_flows_by_type(flow_type, limit)

    async def get_active_flows(
        self, limit: int = 10, flow_type: Optional[str] = None
    ) -> List[CrewAIFlowStateExtensions]:
        return await self.queries.get_active_flows(limit, flow_type)

    async def get_flows_by_engagement(
        self, engagement_id: str, flow_type: Optional[str] = None, limit: int = 50
    ) -> List[CrewAIFlowStateExtensions]:
        return await self.queries.get_flows_by_engagement(
            engagement_id, flow_type, limit
        )

    async def delete_master_flow(self, flow_id: str) -> bool:
        return await self.queries.delete_master_flow(flow_id)

    async def get_master_flow_by_id(
        self, flow_id: str
    ) -> Optional[CrewAIFlowStateExtensions]:
        return await self.queries.get_by_flow_id(flow_id)

    async def get_master_flow_summary(self) -> Dict[str, Any]:
        return await self.queries.get_master_flow_summary()

    # =============================
    # Enrichment helpers (JSONB)
    # =============================

    async def update_flow_metadata(
        self, flow_id: str, metadata_updates: Dict[str, Any]
    ) -> None:
        if not self._enrichment_enabled:
            return
        await self.enrich.update_flow_metadata(flow_id, metadata_updates)

    async def add_phase_transition(
        self,
        flow_id: str,
        phase: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append a phase transition record. Keeps last 200.
        Honors feature flag.
        """
        if not self._enrichment_enabled:
            return

        await self.enrich.add_phase_transition(flow_id, phase, status, metadata)

    async def record_phase_execution_time(
        self, flow_id: str, phase: str, execution_time_ms: float
    ) -> None:
        """Record total execution time for a phase.
        Lightweight data only. Honors feature flag.
        """
        if not self._enrichment_enabled:
            return

        await self.enrich.record_phase_execution_time(flow_id, phase, execution_time_ms)

    async def append_agent_collaboration(
        self, flow_id: str, entry: Dict[str, Any]
    ) -> None:
        """Append an agent collaboration entry. Keep last 100. Honors feature flag."""
        if not self._enrichment_enabled:
            return

        await self.enrich.append_agent_collaboration(flow_id, entry)

    async def update_memory_usage_metrics(
        self, flow_id: str, metrics: Dict[str, Any]
    ) -> None:
        """Merge memory usage metrics. Honors feature flag."""
        if not self._enrichment_enabled:
            return

        await self.enrich.update_memory_usage_metrics(flow_id, metrics)

    async def update_agent_performance_metrics(
        self, flow_id: str, metrics: Dict[str, Any]
    ) -> None:
        """Merge agent performance metrics. Honors feature flag."""
        if not self._enrichment_enabled:
            return

        await self.enrich.update_agent_performance_metrics(flow_id, metrics)

    async def add_error_entry(
        self,
        flow_id: str,
        phase: str,
        error: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append an error entry. Keep last 100. Honors feature flag."""
        if not self._enrichment_enabled:
            return

        await self.enrich.add_error_entry(flow_id, phase, error, details)

    async def increment_retry_count(self, flow_id: str) -> None:
        """Increment retry_count. Honors feature flag."""
        if not self._enrichment_enabled:
            return

        await self.enrich.increment_retry_count(flow_id)
