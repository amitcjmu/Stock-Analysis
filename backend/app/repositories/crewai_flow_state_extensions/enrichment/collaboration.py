import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import and_, select, update

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = logging.getLogger(__name__)


class CollaborationEnrichmentMixin:
    async def append_agent_collaboration(
        self, flow_id: str, entry: Dict[str, Any]
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
        log = list(flow.agent_collaboration_log or [])
        entry_data = dict(entry or {})
        if "timestamp" not in entry_data:
            entry_data["timestamp"] = datetime.utcnow().isoformat()
        log.append(self._ensure_json_serializable(entry_data))
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
        if not result_upd.rowcount:
            logger.warning(
                "OCC conflict updating agent_collaboration_log for flow_id=%s, client=%s, engagement=%s",
                flow_id,
                self.client_account_id,
                self.engagement_id,
            )
            return
