import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import and_, select, update

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = logging.getLogger(__name__)


class MetricsEnrichmentMixin:
    async def update_memory_usage_metrics(
        self, flow_id: str, metrics: Dict[str, Any]
    ) -> None:
        if not getattr(self, "_enrichment_enabled", False):
            return
        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)
        except (ValueError, TypeError) as e:
            logger.error(
                "Invalid UUID in enrichment call for flow_id=%s: %s", flow_id, e
            )
            return
        stmt = (
            select(CrewAIFlowStateExtensions)
            .where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_uuid,
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                )
            )
            .with_for_update()
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
            # 🔧 CC FIX: Remove duplicate commit - transaction boundary managed by caller
            # await self.db.commit()  # REMOVED to prevent double commit
            pass
        else:
            # 🔧 CC FIX: Don't rollback here - let parent transaction handle it
            # await self.db.rollback()  # REMOVED - parent manages transaction
            logger.warning(
                "OCC conflict updating memory_usage_metrics for flow_id=%s, client=%s, engagement=%s",
                flow_id,
                self.client_account_id,
                self.engagement_id,
            )

    async def update_agent_performance_metrics(
        self, flow_id: str, metrics: Dict[str, Any]
    ) -> None:
        if not getattr(self, "_enrichment_enabled", False):
            return
        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)
        except (ValueError, TypeError) as e:
            logger.error(
                "Invalid UUID in enrichment call for flow_id=%s: %s", flow_id, e
            )
            return
        stmt = (
            select(CrewAIFlowStateExtensions)
            .where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_uuid,
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                )
            )
            .with_for_update()
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
            # 🔧 CC FIX: Remove duplicate commit - transaction boundary managed by caller
            # await self.db.commit()  # REMOVED to prevent double commit
            pass
        else:
            # 🔧 CC FIX: Don't rollback here - let parent transaction handle it
            # await self.db.rollback()  # REMOVED - parent manages transaction
            logger.warning(
                "OCC conflict updating agent_performance_metrics for flow_id=%s, client=%s, engagement=%s",
                flow_id,
                self.client_account_id,
                self.engagement_id,
            )
