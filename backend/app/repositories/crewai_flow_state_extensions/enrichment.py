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
