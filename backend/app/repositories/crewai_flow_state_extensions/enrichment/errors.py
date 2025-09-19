import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import and_, select, update

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = logging.getLogger(__name__)


class ErrorsEnrichmentMixin:
    async def add_error_entry(
        self,
        flow_id: str,
        phase: str,
        error: str,
        details: Optional[Dict[str, Any]] = None,
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
            # 🔧 CC FIX: Remove duplicate commit - transaction boundary managed by caller
            # await self.db.commit()  # REMOVED to prevent double commit
            pass
        else:
            # 🔧 CC FIX: Don't rollback here - let parent transaction handle it
            # await self.db.rollback()  # REMOVED - parent manages transaction
            logger.warning(
                "OCC conflict updating error_history for flow_id=%s, client=%s, engagement=%s",
                flow_id,
                self.client_account_id,
                self.engagement_id,
            )

    async def increment_retry_count(self, flow_id: str) -> None:
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
            # 🔧 CC FIX: Remove duplicate commit - transaction boundary managed by caller
            # await self.db.commit()  # REMOVED to prevent double commit
            pass
        else:
            # 🔧 CC FIX: Don't rollback here - let parent transaction handle it
            # await self.db.rollback()  # REMOVED - parent manages transaction
            logger.warning(
                "OCC conflict updating retry_count for flow_id=%s, client=%s, engagement=%s",
                flow_id,
                self.client_account_id,
                self.engagement_id,
            )
