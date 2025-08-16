"""Write/command operations for master CrewAI flow state."""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.crewai_flow_state_extensions.base import BaseRepo
from app.repositories.crewai_flow_state_extensions.enrichment import (
    MasterFlowEnrichment,
)

logger = logging.getLogger(__name__)


class MasterFlowCommands(BaseRepo):
    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str,
        user_id: Optional[str] = None,
    ) -> None:
        super().__init__(db, client_account_id, engagement_id, user_id)
        self.enrich = MasterFlowEnrichment(
            db, self.client_account_id, self.engagement_id, user_id
        )

    async def create_master_flow(
        self,
        flow_id: str,
        flow_type: str,
        user_id: Optional[str] = None,
        flow_name: Optional[str] = None,
        flow_configuration: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None,
        auto_commit: bool = True,
    ) -> CrewAIFlowStateExtensions:
        demo_client_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        demo_engagement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")

        try:
            parsed_flow_id = (
                flow_id if isinstance(flow_id, uuid.UUID) else uuid.UUID(flow_id)
            )
        except (ValueError, TypeError) as e:
            logger.error("Invalid CrewAI Flow ID provided: %s, error: %s", flow_id, e)
            raise ValueError(
                f"Invalid CrewAI Flow ID: {flow_id}. Must be a valid UUID."
            )

        valid_flow_types = {
            "discovery",
            "assessment",
            "collection",
            "planning",
            "execution",
            "modernize",
            "finops",
            "observability",
            "decommission",
        }
        normalized_flow_type = (flow_type or "").strip().lower()
        if normalized_flow_type not in valid_flow_types:
            raise ValueError(
                f"Invalid flow_type: {flow_type}. Must be one of: {sorted(valid_flow_types)}"
            )

        if not flow_name:
            flow_name = f"{flow_type.title()} Flow {str(flow_id)[:8]}"

        safe_user_id = user_id or "test-user"

        master_flow = CrewAIFlowStateExtensions(
            flow_id=parsed_flow_id,
            client_account_id=(
                uuid.UUID(self.client_account_id)
                if self.client_account_id
                else demo_client_id
            ),
            engagement_id=(
                uuid.UUID(self.engagement_id)
                if self.engagement_id
                else demo_engagement_id
            ),
            user_id=safe_user_id,
            flow_type=flow_type,
            flow_name=flow_name,
            flow_status="initialized",
            flow_configuration=flow_configuration or {},
            flow_persistence_data=initial_state or {},
            agent_collaboration_log=[],
            phase_execution_times={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(master_flow)
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(master_flow)
            logger.info(
                "Master flow created with commit: flow_id=%s, type=%s",
                flow_id,
                flow_type,
            )
        else:
            await self.db.flush()
            await self.db.refresh(master_flow)
            logger.info(
                "Master flow created with flush: flow_id=%s, type=%s",
                flow_id,
                flow_type,
            )

        return master_flow

    async def update_flow_status(
        self,
        flow_id: str,
        status: str,
        phase_data: Optional[Dict[str, Any]] = None,
        collaboration_entry: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CrewAIFlowStateExtensions:
        # Validate UUIDs early
        try:
            _ = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            _ = uuid.UUID(self.client_account_id)
            _ = uuid.UUID(self.engagement_id)
        except (ValueError, TypeError) as e:
            logger.error("Invalid UUID format in update_flow_status: %s", e)
            raise ValueError(f"Invalid UUID format: {e}")

        try:
            async with self.db.begin():
                # Apply enrichment deltas
                if metadata:
                    await self.enrich.update_flow_metadata(
                        flow_id, self._ensure_json_serializable(metadata)
                    )
                if collaboration_entry:
                    if isinstance(collaboration_entry, dict):
                        entry = dict(collaboration_entry)
                        if "timestamp" not in entry:
                            entry["timestamp"] = datetime.utcnow().isoformat()
                        await self.enrich.append_agent_collaboration(
                            flow_id, self._ensure_json_serializable(entry)
                        )
                    else:
                        logger.warning(
                            "Invalid collaboration_entry type '%s' for flow_id=%s; skipping",
                            type(collaboration_entry).__name__,
                            flow_id,
                        )
                if phase_data:
                    await self.enrich.update_flow_metadata(
                        flow_id, self._ensure_json_serializable(phase_data)
                    )

                # OCC-guarded status update
                flow = await self._get_flow_for_context(flow_id)
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
                    if not result.rowcount:
                        raise RuntimeError("OCC conflict on flow_status update")
        except Exception as e:
            logger.error("Failed update_flow_status for flow_id=%s: %s", flow_id, e)
            raise
        return await self._get_flow_for_context(flow_id)

    async def _get_flow_for_context(
        self, flow_id: str
    ) -> Optional[CrewAIFlowStateExtensions]:
        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
        except (ValueError, TypeError):
            return None
        stmt = and_(
            CrewAIFlowStateExtensions.flow_id == flow_uuid,
            CrewAIFlowStateExtensions.client_account_id
            == uuid.UUID(self.client_account_id),
            CrewAIFlowStateExtensions.engagement_id == uuid.UUID(self.engagement_id),
        )
        result = await self.db.execute(
            update(CrewAIFlowStateExtensions).where(
                False
            )  # no-op to hint type checkers
        )
        del result  # silence linters for the no-op above
        # Use queries through direct select to get the instance
        from sqlalchemy import select

        res = await self.db.execute(select(CrewAIFlowStateExtensions).where(stmt))
        return res.scalar_one_or_none()
