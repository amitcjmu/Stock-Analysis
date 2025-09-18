"""
Database operations for Master Flow Synchronization Service
"""

import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow
from app.models.assessment_flow.core_models import AssessmentFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = logging.getLogger(__name__)


class FlowSyncDatabase:
    """Database operations for flow synchronization"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def get_master_flow(
        self, flow_id: UUID
    ) -> Optional[CrewAIFlowStateExtensions]:
        """Retrieve master flow by ID with tenant scoping"""
        try:
            result = await self.db.execute(
                select(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id
                    == self.context.client_account_id,
                    CrewAIFlowStateExtensions.engagement_id
                    == self.context.engagement_id,
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error retrieving master flow {flow_id}: {e}")
            return None

    async def get_all_collection_flows(self) -> List[CollectionFlow]:
        """Retrieve all collection flows for the current tenant"""
        try:
            result = await self.db.execute(
                select(CollectionFlow).where(
                    CollectionFlow.client_account_id == self.context.client_account_id,
                    CollectionFlow.engagement_id == self.context.engagement_id,
                )
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving collection flows: {e}")
            return []

    async def get_all_assessment_flows(self) -> List[AssessmentFlow]:
        """Retrieve all assessment flows for the current tenant"""
        try:
            result = await self.db.execute(
                select(AssessmentFlow).where(
                    AssessmentFlow.client_account_id == self.context.client_account_id,
                    AssessmentFlow.engagement_id == self.context.engagement_id,
                )
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving assessment flows: {e}")
            return []

    async def update_collection_flow(
        self, collection_flow_id: UUID, update_fields: dict
    ):
        """Update collection flow with given fields"""
        await self.db.execute(
            update(CollectionFlow)
            .where(CollectionFlow.flow_id == collection_flow_id)
            .where(CollectionFlow.client_account_id == self.context.client_account_id)
            .where(CollectionFlow.engagement_id == self.context.engagement_id)
            .values(**update_fields)
        )

    async def update_master_flow(self, master_flow_id: UUID, update_fields: dict):
        """Update master flow with given fields"""
        await self.db.execute(
            update(CrewAIFlowStateExtensions)
            .where(CrewAIFlowStateExtensions.flow_id == master_flow_id)
            .where(
                CrewAIFlowStateExtensions.client_account_id
                == self.context.client_account_id
            )
            .where(
                CrewAIFlowStateExtensions.engagement_id == self.context.engagement_id
            )
            .values(**update_fields)
        )

    async def update_assessment_flow(
        self, assessment_flow_id: UUID, update_fields: dict
    ):
        """Update assessment flow with given fields"""
        await self.db.execute(
            update(AssessmentFlow)
            .where(AssessmentFlow.flow_id == assessment_flow_id)
            .where(AssessmentFlow.client_account_id == self.context.client_account_id)
            .where(AssessmentFlow.engagement_id == self.context.engagement_id)
            .values(**update_fields)
        )
