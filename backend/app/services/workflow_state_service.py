"""
Service for CRUD operations on WorkflowState model.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.workflow_state import WorkflowState
from typing import Optional, List, Any
import uuid

class WorkflowStateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_workflow_state(self, *, session_id: str, client_account_id: uuid.UUID, engagement_id: uuid.UUID, workflow_type: str, current_phase: str, status: str, state_data: Any) -> WorkflowState:
        # Convert session_id to UUID if it's a string
        if isinstance(session_id, str):
            try:
                session_uuid = uuid.UUID(session_id)
            except ValueError:
                raise ValueError(f"Invalid session_id format: {session_id}")
        else:
            session_uuid = session_id
            
        ws = WorkflowState(
            session_id=session_uuid,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            workflow_type=workflow_type,
            current_phase=current_phase,
            status=status,
            state_data=state_data
        )
        self.db.add(ws)
        await self.db.commit()
        await self.db.refresh(ws)
        return ws

    async def get_workflow_state_by_session_id(self, session_id: str, client_account_id: uuid.UUID, engagement_id: uuid.UUID) -> Optional[WorkflowState]:
        # Convert session_id to UUID if it's a string
        if isinstance(session_id, str):
            try:
                session_uuid = uuid.UUID(session_id)
            except ValueError:
                return None
        else:
            session_uuid = session_id
            
        result = await self.db.execute(
            select(WorkflowState).filter_by(
                session_id=session_uuid,
                client_account_id=client_account_id,
                engagement_id=engagement_id
            )
        )
        return result.scalar_one_or_none()

    async def update_workflow_state(self, session_id: str, client_account_id: uuid.UUID, engagement_id: uuid.UUID, **kwargs) -> Optional[WorkflowState]:
        ws = await self.get_workflow_state_by_session_id(session_id, client_account_id, engagement_id)
        if not ws:
            return None
        for key, value in kwargs.items():
            if hasattr(ws, key):
                setattr(ws, key, value)
        await self.db.commit()
        await self.db.refresh(ws)
        return ws

    async def list_workflow_states_by_engagement(self, engagement_id: uuid.UUID, client_account_id: uuid.UUID) -> List[WorkflowState]:
        result = await self.db.execute(
            select(WorkflowState).filter_by(
                engagement_id=engagement_id,
                client_account_id=client_account_id
            )
        )
        return result.scalars().all()
