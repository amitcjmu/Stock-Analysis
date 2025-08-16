"""
CrewAI Flow State Extensions Repository (modularized facade)

This module now provides a thin facade over modular components:
- base.py (BaseRepo with init, feature flags, serialization)
- queries.py (read-only queries)
- enrichment.py (JSONB enrichment helpers)
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, select, update
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
        # Handle None values and invalid UUIDs with proper fallbacks
        demo_client_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        demo_engagement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")

        # Safely convert client_account_id
        try:
            if client_account_id and client_account_id != "None":
                # Handle if already a UUID object
                if isinstance(client_account_id, uuid.UUID):
                    parsed_client_id = client_account_id
                else:
                    parsed_client_id = uuid.UUID(str(client_account_id))
            else:
                parsed_client_id = demo_client_id
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid client_account_id '{client_account_id}', using demo fallback"
            )
            parsed_client_id = demo_client_id

        # Safely convert engagement_id
        try:
            if engagement_id and engagement_id != "None":
                # Handle if already a UUID object
                if isinstance(engagement_id, uuid.UUID):
                    parsed_engagement_id = engagement_id
                else:
                    parsed_engagement_id = uuid.UUID(str(engagement_id))
            else:
                parsed_engagement_id = demo_engagement_id
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid engagement_id '{engagement_id}', using demo fallback"
            )
            parsed_engagement_id = demo_engagement_id

        # Initialize base repo
        super().__init__(
            db=db,
            client_account_id=str(parsed_client_id),
            engagement_id=str(parsed_engagement_id),
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
        """Update master flow status and state"""

        try:
            # validate UUID inputs early for clear error messages
            _ = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            _ = uuid.UUID(self.client_account_id)
            _ = uuid.UUID(self.engagement_id)
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Invalid UUID format in update_flow_status: {e}")
            raise ValueError(f"Invalid UUID format: {e}")

        # Apply minimal, delegated updates
        await self.enrich.update_flow_metadata(
            flow_id, self._ensure_json_serializable(metadata or {})
        )
        if collaboration_entry:
            entry = dict(collaboration_entry)
            if "timestamp" not in entry:
                entry["timestamp"] = datetime.utcnow().isoformat()
            await self.enrich.append_agent_collaboration(
                flow_id, self._ensure_json_serializable(entry)
            )
        if phase_data:
            await self.enrich.update_flow_metadata(
                flow_id, self._ensure_json_serializable(phase_data)
            )
        # Finally, set the flow_status
        flow = await self.queries.get_by_flow_id(flow_id)
        if flow:
            prev_updated_at = flow.updated_at
            stmt_upd = (
                update(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.id == flow.id,
                        CrewAIFlowStateExtensions.client_account_id
                        == uuid.UUID(self.client_account_id),
                        CrewAIFlowStateExtensions.engagement_id
                        == uuid.UUID(self.engagement_id),
                        CrewAIFlowStateExtensions.updated_at == prev_updated_at,
                    )
                )
                .values(flow_status=status, updated_at=datetime.utcnow())
            )
            result = await self.db.execute(stmt_upd)
            if result.rowcount:
                await self.db.commit()
            else:
                await self.db.rollback()
                logger.warning(
                    "OCC conflict updating flow_status for flow_id=%s, client=%s, engagement=%s",
                    flow_id,
                    self.client_account_id,
                    self.engagement_id,
                )
        return await self.queries.get_by_flow_id(flow_id)

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
        """Delete master flow and all subordinate flows (cascade)"""
        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)

            stmt = delete(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_uuid,
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                )
            )

            result = await self.db.execute(stmt)
            await self.db.commit()

            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"✅ Master flow deleted: {flow_id}")
            else:
                logger.warning(f"⚠️ Master flow not found for deletion: {flow_id}")

            return deleted

        except Exception as e:
            logger.error(f"❌ Failed to delete master flow {flow_id}: {e}")
            return False

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
        """Merge arbitrary metadata into flow_metadata JSONB.

        Lightweight summaries only. Honors feature flag.
        """
        if not self._enrichment_enabled:
            return

        try:
            # Load existing
            flow = await self.queries.get_by_flow_id(flow_id)
            if not flow:
                return

            metadata = flow.flow_metadata or {}
            serializable_updates = self._ensure_json_serializable(metadata_updates)
            if not isinstance(metadata, dict):
                metadata = {}
            metadata.update(serializable_updates)

            await self.enrich.update_flow_metadata(flow_id, metadata)
        except Exception as e:
            logger.error(f"❌ Failed update_flow_metadata for {flow_id}: {e}")
            await self.db.rollback()

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

        try:
            # Use modular query helper
            flow = await self.queries.get_by_flow_id(flow_id)
            if not flow:
                return

            transitions = list(flow.phase_transitions or [])
            entry = self._ensure_json_serializable(
                {
                    "phase": phase,
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": self._ensure_json_serializable(metadata or {}),
                }
            )
            transitions.append(entry)
            # Cap size
            if len(transitions) > 200:
                transitions = transitions[-200:]

            await self.enrich.add_phase_transition(flow_id, phase, status, metadata)
        except Exception as e:
            logger.error(f"❌ Failed add_phase_transition for {flow_id}: {e}")
            await self.db.rollback()

    async def record_phase_execution_time(
        self, flow_id: str, phase: str, execution_time_ms: float
    ) -> None:
        """Record total execution time for a phase.
        Lightweight data only. Honors feature flag.
        """
        if not self._enrichment_enabled:
            return

        try:
            # Use modular query helper
            flow = await self.queries.get_by_flow_id(flow_id)
            if not flow:
                return

            times = dict(flow.phase_execution_times or {})
            times[phase] = {
                "execution_time_ms": float(execution_time_ms),
                "completed_at": datetime.utcnow().isoformat(),
            }

            await self.enrich.record_phase_execution_time(
                flow_id, phase, execution_time_ms
            )
        except Exception as e:
            logger.error(f"❌ Failed record_phase_execution_time for {flow_id}: {e}")
            await self.db.rollback()

    async def append_agent_collaboration(
        self, flow_id: str, entry: Dict[str, Any]
    ) -> None:
        """Append an agent collaboration entry. Keep last 100. Honors feature flag."""
        if not self._enrichment_enabled:
            return

        try:
            flow = await self.queries.get_by_flow_id(flow_id)
            if not flow:
                return

            log = list(flow.agent_collaboration_log or [])
            entry_data: Dict[str, Any] = dict(entry or {})
            if "timestamp" not in entry_data:
                entry_data["timestamp"] = datetime.utcnow().isoformat()
            serializable = self._ensure_json_serializable(entry_data)
            log.append(serializable)
            if len(log) > 100:
                log = log[-100:]

            prev_updated_at = flow.updated_at
            stmt_upd = (
                update(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.id == flow.id,
                        CrewAIFlowStateExtensions.client_account_id
                        == uuid.UUID(self.client_account_id),
                        CrewAIFlowStateExtensions.engagement_id
                        == uuid.UUID(self.engagement_id),
                        CrewAIFlowStateExtensions.updated_at == prev_updated_at,
                    )
                )
                .values(agent_collaboration_log=log, updated_at=datetime.utcnow())
            )
            result_upd = await self.db.execute(stmt_upd)
            if result_upd.rowcount:
                await self.db.commit()
            else:
                await self.db.rollback()
        except Exception as e:
            logger.error(f"❌ Failed append_agent_collaboration for {flow_id}: {e}")
            await self.db.rollback()

    async def update_memory_usage_metrics(
        self, flow_id: str, metrics: Dict[str, Any]
    ) -> None:
        """Merge memory usage metrics. Honors feature flag."""
        if not self._enrichment_enabled:
            return

        try:
            flow = await self.queries.get_by_flow_id(flow_id)
            if not flow:
                return

            current = dict(flow.memory_usage_metrics or {})
            serializable = self._ensure_json_serializable(metrics)
            current.update(serializable)
            current["last_updated"] = datetime.utcnow().isoformat()

            prev_updated_at = flow.updated_at
            stmt_upd = (
                update(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.id == flow.id,
                        CrewAIFlowStateExtensions.client_account_id
                        == uuid.UUID(self.client_account_id),
                        CrewAIFlowStateExtensions.engagement_id
                        == uuid.UUID(self.engagement_id),
                        CrewAIFlowStateExtensions.updated_at == prev_updated_at,
                    )
                )
                .values(memory_usage_metrics=current, updated_at=datetime.utcnow())
            )
            result_upd = await self.db.execute(stmt_upd)
            if result_upd.rowcount:
                await self.db.commit()
            else:
                await self.db.rollback()
        except Exception as e:
            logger.error(f"❌ Failed update_memory_usage_metrics for {flow_id}: {e}")
            await self.db.rollback()

    async def update_agent_performance_metrics(
        self, flow_id: str, metrics: Dict[str, Any]
    ) -> None:
        """Merge agent performance metrics. Honors feature flag."""
        if not self._enrichment_enabled:
            return

        try:
            flow = await self.queries.get_by_flow_id(flow_id)
            if not flow:
                return

            current = dict(flow.agent_performance_metrics or {})
            serializable = self._ensure_json_serializable(metrics) or {}
            allowed_keys = {
                "response_time_ms",
                "success_rate",
                "throughput",
                "latency_ms",
                "token_usage",
            }
            # Allow extension via env var PERF_METRICS_ALLOWED_KEYS=key1,key2
            extra = os.getenv("PERF_METRICS_ALLOWED_KEYS", "").strip()
            if extra:
                for k in [x.strip() for x in extra.split(",") if x.strip()]:
                    allowed_keys.add(k)
            filtered = {k: serializable[k] for k in serializable.keys() & allowed_keys}
            # Log dropped keys at debug level for visibility without noise
            dropped = set(serializable.keys()) - set(filtered.keys())
            if dropped:
                logger.debug(
                    f"Performance metrics keys dropped for flow {flow_id}: {sorted(dropped)}"
                )
            current.update(filtered)

            prev_updated_at = flow.updated_at
            stmt_upd = (
                update(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.id == flow.id,
                        CrewAIFlowStateExtensions.client_account_id
                        == uuid.UUID(self.client_account_id),
                        CrewAIFlowStateExtensions.engagement_id
                        == uuid.UUID(self.engagement_id),
                        CrewAIFlowStateExtensions.updated_at == prev_updated_at,
                    )
                )
                .values(agent_performance_metrics=current, updated_at=datetime.utcnow())
            )
            result_upd = await self.db.execute(stmt_upd)
            if result_upd.rowcount:
                await self.db.commit()
            else:
                await self.db.rollback()
        except Exception as e:
            logger.error(
                f"❌ Failed update_agent_performance_metrics for {flow_id}: {e}"
            )
            await self.db.rollback()

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

        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)

            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_uuid,
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                )
            )
            result = await self.db.execute(stmt)
            flow = result.scalar_one_or_none()
            if not flow:
                return

            history = list(flow.error_history or [])
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "phase": phase,
                "error": error,
                "details": self._ensure_json_serializable(details or {}),
                "retry_count": flow.retry_count or 0,
            }
            history.append(entry)
            if len(history) > 100:
                history = history[-100:]

            prev_updated_at = flow.updated_at
            stmt_upd = (
                update(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.id == flow.id,
                        CrewAIFlowStateExtensions.client_account_id == client_uuid,
                        CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                        CrewAIFlowStateExtensions.updated_at == prev_updated_at,
                    )
                )
                .values(error_history=history, updated_at=datetime.utcnow())
            )
            result_upd = await self.db.execute(stmt_upd)
            if result_upd.rowcount:
                await self.db.commit()
            else:
                await self.db.rollback()
        except Exception as e:
            logger.error(f"❌ Failed add_error_entry for {flow_id}: {e}")
            await self.db.rollback()

    async def increment_retry_count(self, flow_id: str) -> None:
        """Increment retry_count. Honors feature flag."""
        if not self._enrichment_enabled:
            return

        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)

            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_uuid,
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                )
            )
            result = await self.db.execute(stmt)
            flow = result.scalar_one_or_none()
            if not flow:
                return

            new_retry = (flow.retry_count or 0) + 1
            prev_updated_at = flow.updated_at
            stmt_upd = (
                update(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.id == flow.id,
                        CrewAIFlowStateExtensions.client_account_id == client_uuid,
                        CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                        CrewAIFlowStateExtensions.updated_at == prev_updated_at,
                    )
                )
                .values(retry_count=new_retry, updated_at=datetime.utcnow())
            )
            result_upd = await self.db.execute(stmt_upd)
            if result_upd.rowcount:
                await self.db.commit()
            else:
                await self.db.rollback()
        except Exception as e:
            logger.error(f"❌ Failed increment_retry_count for {flow_id}: {e}")
            await self.db.rollback()
