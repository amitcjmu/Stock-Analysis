"""
Flow Commands - Core flow management operations
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import AssessmentFlow
from app.models.assessment_flow_state import (AssessmentFlowStatus,
                                              AssessmentPhase)

logger = logging.getLogger(__name__)


class FlowCommands:
    """Commands for core assessment flow operations"""

    def __init__(self, db: AsyncSession, client_account_id: int):
        self.db = db
        self.client_account_id = client_account_id

    async def create_assessment_flow(
        self,
        engagement_id: str,
        selected_application_ids: List[str],
        created_by: Optional[str] = None,
    ) -> str:
        """Create new assessment flow with initial state and register with master flow system"""

        flow_record = AssessmentFlow(
            client_account_id=self.client_account_id,
            engagement_id=engagement_id,
            selected_application_ids=selected_application_ids,
            status=AssessmentFlowStatus.INITIALIZED.value,
            current_phase=AssessmentPhase.INITIALIZATION.value,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(flow_record)
        await self.db.commit()
        await self.db.refresh(flow_record)

        # Register with master flow system
        from app.repositories.crewai_flow_state_extensions_repository import \
            CrewAIFlowStateExtensionsRepository

        try:
            extensions_repo = CrewAIFlowStateExtensionsRepository(
                self.db,
                str(self.client_account_id),
                str(engagement_id),
                user_id=created_by,
            )

            await extensions_repo.create_master_flow(
                flow_id=str(flow_record.id),
                flow_type="assessment",  # Using 'assessment' for consistency
                user_id=created_by or "system",
                flow_name=f"Assessment Flow - {len(selected_application_ids)} Applications",
                flow_configuration={
                    "selected_applications": selected_application_ids,
                    "assessment_type": "sixr_analysis",
                    "created_by": created_by,
                    "engagement_id": str(engagement_id),
                },
                initial_state={
                    "phase": AssessmentPhase.INITIALIZATION.value,
                    "applications_count": len(selected_application_ids),
                },
            )

            logger.info(
                f"Registered assessment flow {flow_record.id} with master flow system"
            )

        except Exception as e:
            logger.error(
                f"Failed to register assessment flow {flow_record.id} with master flow: {e}"
            )
            # Don't fail the entire creation if master flow registration fails
            # The flow still exists and can function, just without master coordination

        logger.info(
            f"Created assessment flow {flow_record.id} for engagement {engagement_id}"
        )
        return str(flow_record.id)

    async def update_flow_phase(
        self,
        flow_id: str,
        current_phase: str,
        next_phase: Optional[str] = None,
        progress: Optional[int] = None,
        status: Optional[str] = None,
    ):
        """Update flow phase and progress, sync with master flow"""

        update_data = {"current_phase": current_phase, "updated_at": datetime.utcnow()}

        if next_phase:
            update_data["next_phase"] = next_phase
        if progress is not None:
            update_data["progress"] = progress
        if status:
            update_data["status"] = status

        await self.db.execute(
            update(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
            .values(**update_data)
        )
        await self.db.commit()

        logger.info(f"Updated flow {flow_id} phase to {current_phase}")

    async def save_user_input(
        self, flow_id: str, phase: str, user_input: Dict[str, Any]
    ):
        """Save user input for specific phase"""

        # Get current user_inputs
        from sqlalchemy import select

        result = await self.db.execute(
            select(AssessmentFlow.user_inputs).where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
        )
        current_inputs = result.scalar() or {}
        current_inputs[phase] = user_input

        await self.db.execute(
            update(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
            .values(
                user_inputs=current_inputs,
                last_user_interaction=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        await self.db.commit()

    async def save_agent_insights(
        self, flow_id: str, phase: str, insights: List[Dict[str, Any]]
    ):
        """Save agent insights for specific phase and log to master flow"""

        # Get current agent insights
        from sqlalchemy import select

        result = await self.db.execute(
            select(AssessmentFlow.agent_insights).where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
        )
        current_insights = result.scalar() or []

        # Add phase context to insights
        phase_insights = [
            {**insight, "phase": phase, "timestamp": datetime.utcnow().isoformat()}
            for insight in insights
        ]
        current_insights.extend(phase_insights)

        await self.db.execute(
            update(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
            .values(agent_insights=current_insights, updated_at=datetime.utcnow())
        )
        await self.db.commit()
