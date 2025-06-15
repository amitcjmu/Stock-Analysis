"""
Service for CRUD operations on WorkflowState model.
"""
from sqlalchemy.orm import Session
from app.models.workflow_state import WorkflowState
from typing import Optional, List, Any
import uuid

class WorkflowStateService:
    def __init__(self, db: Session):
        self.db = db

    def create_workflow_state(self, *, session_id: str, client_account_id: uuid.UUID, engagement_id: uuid.UUID, workflow_type: str, current_phase: str, status: str, state_data: Any) -> WorkflowState:
        ws = WorkflowState(
            session_id=session_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            workflow_type=workflow_type,
            current_phase=current_phase,
            status=status,
            state_data=state_data
        )
        self.db.add(ws)
        self.db.commit()
        self.db.refresh(ws)
        return ws

    def get_workflow_state_by_session_id(self, session_id: str, client_account_id: uuid.UUID, engagement_id: uuid.UUID) -> Optional[WorkflowState]:
        return self.db.query(WorkflowState).filter_by(
            session_id=session_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id
        ).first()

    def update_workflow_state(self, session_id: str, client_account_id: uuid.UUID, engagement_id: uuid.UUID, **kwargs) -> Optional[WorkflowState]:
        ws = self.get_workflow_state_by_session_id(session_id, client_account_id, engagement_id)
        if not ws:
            return None
        for key, value in kwargs.items():
            if hasattr(ws, key):
                setattr(ws, key, value)
        self.db.commit()
        self.db.refresh(ws)
        return ws

    def list_workflow_states_by_engagement(self, engagement_id: uuid.UUID, client_account_id: uuid.UUID) -> List[WorkflowState]:
        return self.db.query(WorkflowState).filter_by(
            engagement_id=engagement_id,
            client_account_id=client_account_id
        ).all()
