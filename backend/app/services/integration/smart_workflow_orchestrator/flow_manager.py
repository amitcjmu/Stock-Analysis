"""
Flow Management Utilities for Smart Workflow Orchestrator

This module provides flow retrieval, creation, and management functionality
for collection, discovery, and assessment flows.

Generated with CC for ADCS end-to-end integration.
"""

from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.assessment_flow import AssessmentFlow
from app.models.collection_flow import CollectionFlow
from app.models.discovery_flow import DiscoveryFlow

from .workflow_types import SmartWorkflowContext, WorkflowPhase

logger = get_logger(__name__)


class FlowManager:
    """Handles flow retrieval and management operations"""

    def __init__(self):
        pass

    async def get_collection_flow(
        self, session: AsyncSession, engagement_id: UUID
    ) -> Optional[CollectionFlow]:
        """Get collection flow for engagement"""
        result = await session.execute(
            select(CollectionFlow).where(CollectionFlow.engagement_id == engagement_id)
        )
        return result.scalar_one_or_none()

    async def get_discovery_flow(
        self, session: AsyncSession, engagement_id: UUID
    ) -> Optional[DiscoveryFlow]:
        """Get discovery flow for engagement"""
        result = await session.execute(
            select(DiscoveryFlow).where(DiscoveryFlow.engagement_id == engagement_id)
        )
        return result.scalar_one_or_none()

    async def get_assessment_flow(
        self, session: AsyncSession, engagement_id: UUID
    ) -> Optional[AssessmentFlow]:
        """Get assessment flow for engagement"""
        result = await session.execute(
            select(AssessmentFlow).where(AssessmentFlow.engagement_id == engagement_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_discovery_flow(
        self, session: AsyncSession, context: SmartWorkflowContext
    ) -> DiscoveryFlow:
        """Get or create discovery flow"""
        discovery_flow = await self.get_discovery_flow(session, context.engagement_id)

        if not discovery_flow:
            # Create new discovery flow
            discovery_flow = DiscoveryFlow(
                engagement_id=context.engagement_id,
                user_id=context.user_id,
                client_id=context.client_id,
                status="initiated",
                current_phase="data_import_validation",
                metadata={"initiated_by": "smart_workflow"},
            )
            session.add(discovery_flow)
            await session.commit()
            await session.refresh(discovery_flow)

        return discovery_flow

    async def get_or_create_assessment_flow(
        self, session: AsyncSession, context: SmartWorkflowContext
    ) -> AssessmentFlow:
        """Get or create assessment flow"""
        assessment_flow = await self.get_assessment_flow(session, context.engagement_id)

        if not assessment_flow:
            # Create new assessment flow
            assessment_flow = AssessmentFlow(
                engagement_id=context.engagement_id,
                user_id=context.user_id,
                client_id=context.client_id,
                status="initiated",
                current_phase="strategy_analysis",
                metadata={"initiated_by": "smart_workflow"},
            )
            session.add(assessment_flow)
            await session.commit()
            await session.refresh(assessment_flow)

        return assessment_flow

    async def get_workflow_status(
        self, session: AsyncSession, engagement_id: UUID
    ) -> Dict[str, Any]:
        """Get current workflow status for an engagement"""

        # Check all flows
        collection_flow = await self.get_collection_flow(session, engagement_id)
        discovery_flow = await self.get_discovery_flow(session, engagement_id)
        assessment_flow = await self.get_assessment_flow(session, engagement_id)

        # Determine current phase and overall status
        current_phase = WorkflowPhase.COLLECTION
        overall_status = "pending"

        if assessment_flow and assessment_flow.status == "completed":
            current_phase = WorkflowPhase.COMPLETED
            overall_status = "completed"
        elif assessment_flow:
            current_phase = WorkflowPhase.ASSESSMENT
            overall_status = assessment_flow.status
        elif discovery_flow and discovery_flow.status == "completed":
            current_phase = WorkflowPhase.ASSESSMENT
            overall_status = "ready_for_assessment"
        elif discovery_flow:
            current_phase = WorkflowPhase.DISCOVERY
            overall_status = discovery_flow.status
        elif collection_flow and collection_flow.status == "completed":
            current_phase = WorkflowPhase.DISCOVERY
            overall_status = "ready_for_discovery"
        elif collection_flow:
            current_phase = WorkflowPhase.COLLECTION
            overall_status = collection_flow.status

        return {
            "engagement_id": str(engagement_id),
            "current_phase": current_phase.value,
            "overall_status": overall_status,
            "flows": {
                "collection": {
                    "exists": collection_flow is not None,
                    "status": collection_flow.status if collection_flow else None,
                    "id": str(collection_flow.id) if collection_flow else None,
                },
                "discovery": {
                    "exists": discovery_flow is not None,
                    "status": discovery_flow.status if discovery_flow else None,
                    "id": str(discovery_flow.id) if discovery_flow else None,
                },
                "assessment": {
                    "exists": assessment_flow is not None,
                    "status": assessment_flow.status if assessment_flow else None,
                    "id": str(assessment_flow.id) if assessment_flow else None,
                },
            },
        }
