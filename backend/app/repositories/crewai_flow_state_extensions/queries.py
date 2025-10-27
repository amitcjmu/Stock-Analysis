"""Read-only queries for master flow repository."""

import uuid
from typing import List, Optional

from sqlalchemy import and_, delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions


class MasterFlowQueries:
    def __init__(self, db: AsyncSession, client_account_id: str, engagement_id: str):
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def get_by_flow_id(self, flow_id: str) -> Optional[CrewAIFlowStateExtensions]:
        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)
        except (ValueError, TypeError):
            return None
        stmt = select(CrewAIFlowStateExtensions).where(
            and_(
                CrewAIFlowStateExtensions.flow_id == flow_uuid,
                CrewAIFlowStateExtensions.client_account_id == client_uuid,
                CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
            )
        )
        result = await self.db.execute(stmt)
        flow = result.scalar_one_or_none()

        # BUGFIX: Eagerly access all scalar attributes to prevent MissingGreenlet errors
        # when object is accessed outside session context or after session expires
        if flow:
            # Touch all scalar attributes to ensure they're loaded into instance state
            # This prevents lazy loading when the object is passed across async boundaries
            _ = (
                flow.id,
                flow.flow_id,
                flow.client_account_id,
                flow.engagement_id,
                flow.user_id,
                flow.flow_type,
                flow.flow_name,
                flow.flow_status,
            )

        return flow

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

    async def get_master_flow_summary(self) -> dict:
        try:
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)
        except (ValueError, TypeError):
            return {
                "total_master_flows": 0,
                "unique_flow_types": 0,
                "flow_type_distribution": {},
                "flow_status_distribution": {},
                "master_coordination_health": "error",
            }

        stmt = select(
            func.count(CrewAIFlowStateExtensions.id).label("total_master_flows"),
            func.count(func.distinct(CrewAIFlowStateExtensions.flow_type)).label(
                "unique_flow_types"
            ),
        ).where(
            and_(
                CrewAIFlowStateExtensions.client_account_id == client_uuid,
                CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
            )
        )
        result = await self.db.execute(stmt)
        stats = result.first()

        type_stmt = (
            select(
                CrewAIFlowStateExtensions.flow_type,
                func.count(CrewAIFlowStateExtensions.id).label("count"),
            )
            .where(
                and_(
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                )
            )
            .group_by(CrewAIFlowStateExtensions.flow_type)
        )
        type_result = await self.db.execute(type_stmt)
        type_stats = {row.flow_type: row.count for row in type_result}

        status_stmt = (
            select(
                CrewAIFlowStateExtensions.flow_status,
                func.count(CrewAIFlowStateExtensions.id).label("count"),
            )
            .where(
                and_(
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                )
            )
            .group_by(CrewAIFlowStateExtensions.flow_status)
        )
        status_result = await self.db.execute(status_stmt)
        status_stats = {row.flow_status: row.count for row in status_result}

        return {
            "total_master_flows": stats.total_master_flows if stats else 0,
            "unique_flow_types": stats.unique_flow_types if stats else 0,
            "flow_type_distribution": type_stats,
            "flow_status_distribution": status_stats,
            "master_coordination_health": (
                "healthy"
                if (stats and stats.total_master_flows > 0)
                else "missing_master_flows"
            ),
        }

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
