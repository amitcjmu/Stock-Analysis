"""JSONB enrichment helpers for master flow repository.

Contains update helpers that apply tenant-scoped optimistic concurrency (updated_at guard)
and best-effort rollbacks on conflict.
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = logging.getLogger(__name__)


class MasterFlowEnrichment:
    def __init__(self, db: AsyncSession, client_account_id: str, engagement_id: str):
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self._enrichment_enabled = os.getenv(
            "MASTER_STATE_ENRICHMENT_ENABLED", "true"
        ).lower() in (
            "1",
            "true",
            "yes",
        )

    async def update_flow_metadata(
        self, flow_id: str, metadata_updates: Dict[str, Any]
    ) -> None:
        if not self._enrichment_enabled:
            return
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
        metadata = flow.flow_metadata or {}
        metadata.update(self._ensure_json_serializable(metadata_updates))
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
            .values(flow_metadata=metadata, updated_at=datetime.utcnow())
        )
        result_upd = await self.db.execute(stmt_upd)
        if result_upd.rowcount:
            await self.db.commit()
        else:
            await self.db.rollback()

    async def add_phase_transition(
        self,
        flow_id: str,
        phase: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self._enrichment_enabled:
            return
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
        if len(transitions) > 200:
            transitions = transitions[-200:]
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
            .values(phase_transitions=transitions, updated_at=datetime.utcnow())
        )
        result_upd = await self.db.execute(stmt_upd)
        if result_upd.rowcount:
            await self.db.commit()
        else:
            await self.db.rollback()

    async def record_phase_execution_time(
        self, flow_id: str, phase: str, execution_time_ms: float
    ) -> None:
        if not self._enrichment_enabled:
            return
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
        times = dict(flow.phase_execution_times or {})
        times[phase] = {
            "execution_time_ms": float(execution_time_ms),
            "completed_at": datetime.utcnow().isoformat(),
        }
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
            .values(phase_execution_times=times, updated_at=datetime.utcnow())
        )
        result_upd = await self.db.execute(stmt_upd)
        if result_upd.rowcount:
            await self.db.commit()
        else:
            await self.db.rollback()

    async def append_agent_collaboration(
        self, flow_id: str, entry: Dict[str, Any]
    ) -> None:
        if not self._enrichment_enabled:
            return
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
        log = list(flow.agent_collaboration_log or [])
        log.append(self._ensure_json_serializable(entry))
        if len(log) > 100:
            log = log[-100:]
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
            .values(agent_collaboration_log=log, updated_at=datetime.utcnow())
        )
        result_upd = await self.db.execute(stmt_upd)
        if result_upd.rowcount:
            await self.db.commit()
        else:
            await self.db.rollback()

    async def update_memory_usage_metrics(
        self, flow_id: str, metrics: Dict[str, Any]
    ) -> None:
        if not self._enrichment_enabled:
            return
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
        current = dict(flow.memory_usage_metrics or {})
        current.update(self._ensure_json_serializable(metrics))
        current["last_updated"] = datetime.utcnow().isoformat()
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
            .values(memory_usage_metrics=current, updated_at=datetime.utcnow())
        )
        result_upd = await self.db.execute(stmt_upd)
        if result_upd.rowcount:
            await self.db.commit()
        else:
            await self.db.rollback()

    async def update_agent_performance_metrics(
        self, flow_id: str, metrics: Dict[str, Any]
    ) -> None:
        if not self._enrichment_enabled:
            return
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
        current = dict(flow.agent_performance_metrics or {})
        serializable = self._ensure_json_serializable(metrics) or {}
        allowed_keys = {
            "response_time_ms",
            "success_rate",
            "throughput",
            "latency_ms",
            "token_usage",
        }
        extra = os.getenv("PERF_METRICS_ALLOWED_KEYS", "").strip()
        if extra:
            for k in [x.strip() for x in extra.split(",") if x.strip()]:
                allowed_keys.add(k)
        filtered = {k: serializable[k] for k in serializable.keys() & allowed_keys}
        current.update(filtered)
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
            .values(agent_performance_metrics=current, updated_at=datetime.utcnow())
        )
        result_upd = await self.db.execute(stmt_upd)
        if result_upd.rowcount:
            await self.db.commit()
        else:
            await self.db.rollback()

    async def add_error_entry(
        self,
        flow_id: str,
        phase: str,
        error: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self._enrichment_enabled:
            return
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

    async def increment_retry_count(self, flow_id: str) -> None:
        if not self._enrichment_enabled:
            return
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

    def _ensure_json_serializable(self, obj: Any) -> Any:
        # Lightweight wrapper; reuse logic if needed
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: self._ensure_json_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._ensure_json_serializable(v) for v in obj]
        return obj
