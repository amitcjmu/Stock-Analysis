"""Read-only queries for master flow repository."""

import uuid
from typing import List, Optional

from sqlalchemy import and_, delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions


class MasterFlowQueries:
    def __init__(self, db: AsyncSession, client_account_id: str, engagement_id: str):
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def get_by_flow_id(self, flow_id: str) -> Optional[CrewAIFlowStateExtensions]:
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
        return result.scalar_one_or_none()

    async def get_by_flow_id_global(
        self, flow_id: str
    ) -> Optional[CrewAIFlowStateExtensions]:
        # Tenant-scoped "global" lookup (explicitly not cross-tenant)
        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
        except (ValueError, TypeError):
            return None
        stmt = select(CrewAIFlowStateExtensions).where(
            and_(
                CrewAIFlowStateExtensions.flow_id == flow_uuid,
                CrewAIFlowStateExtensions.client_account_id == client_uuid,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_flows_by_type(
        self, flow_type: str, limit: int = 10
    ) -> List[CrewAIFlowStateExtensions]:
        try:
            client_uuid = uuid.UUID(self.client_account_id)
        except (ValueError, TypeError):
            return []
        try:
            engagement_uuid = uuid.UUID(self.engagement_id)
        except (ValueError, TypeError):
            return []
        stmt = (
            select(CrewAIFlowStateExtensions)
            .where(
                and_(
                    CrewAIFlowStateExtensions.flow_type == flow_type,
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                )
            )
            .order_by(desc(CrewAIFlowStateExtensions.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_active_flows(
        self, limit: int = 10, flow_type: Optional[str] = None
    ) -> List[CrewAIFlowStateExtensions]:
        client_uuid = uuid.UUID(self.client_account_id)
        conditions = [CrewAIFlowStateExtensions.client_account_id == client_uuid]
        active_statuses = [
            "initialized",
            "active",
            "processing",
            "paused",
            "waiting_for_approval",
        ]
        conditions.append(CrewAIFlowStateExtensions.flow_status.in_(active_statuses))
        if self.engagement_id:
            try:
                engagement_uuid = uuid.UUID(self.engagement_id)
                conditions.append(
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid
                )
            except (ValueError, TypeError):
                return []
        if flow_type:
            conditions.append(CrewAIFlowStateExtensions.flow_type == flow_type)
        stmt = (
            select(CrewAIFlowStateExtensions)
            .where(and_(*conditions))
            .order_by(desc(CrewAIFlowStateExtensions.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_flows_by_engagement(
        self, engagement_id: str, flow_type: Optional[str] = None, limit: int = 50
    ) -> List[CrewAIFlowStateExtensions]:
        client_uuid = uuid.UUID(self.client_account_id)
        engagement_uuid = uuid.UUID(engagement_id)
        conditions = [
            CrewAIFlowStateExtensions.client_account_id == client_uuid,
            CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
        ]
        if flow_type:
            conditions.append(CrewAIFlowStateExtensions.flow_type == flow_type)
        stmt = (
            select(CrewAIFlowStateExtensions)
            .where(and_(*conditions))
            .order_by(desc(CrewAIFlowStateExtensions.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def delete_master_flow(self, flow_id: str) -> bool:
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
        return result.rowcount > 0
