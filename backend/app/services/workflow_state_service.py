"""
Service for CRUD operations on WorkflowState model with smart session management.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from app.models.workflow_state import WorkflowState
from typing import Optional, List, Any, Tuple
import uuid
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SessionConflictResolution:
    """Strategies for handling session conflicts when multiple workflows exist."""
    
    @staticmethod
    def get_active_or_most_recent(workflows: List[WorkflowState]) -> WorkflowState:
        """
        Returns the active workflow if one exists, otherwise the most recent completed/failed one.
        Priority: running > in_progress > processing > completed > failed > most recent
        """
        if not workflows:
            return None
            
        # Priority order for workflow status
        status_priority = {
            'running': 1,
            'in_progress': 2, 
            'processing': 3,
            'completed': 4,
            'failed': 5,
            'error': 6,
            'cancelled': 7,
            'idle': 8
        }
        
        # Sort by status priority (lower number = higher priority), then by created_at desc
        sorted_workflows = sorted(workflows, key=lambda w: (
            status_priority.get(w.status, 999),  # Unknown statuses get lowest priority
            -w.created_at.timestamp() if w.created_at else 0  # More recent = higher priority
        ))
        
        return sorted_workflows[0]
    
    @staticmethod
    def should_allow_new_workflow(existing_workflow: WorkflowState) -> Tuple[bool, str]:
        """
        Determines if a new workflow can be started given an existing one.
        Returns (can_start, reason/action_required)
        """
        if not existing_workflow:
            return True, "No existing workflow found"
            
        status = existing_workflow.status
        
        # Active states - don't allow new workflow
        if status in ['running', 'in_progress', 'processing']:
            return False, f"Workflow already {status}. Wait for completion or cancel existing workflow."
            
        # Terminal states - allow new workflow
        if status in ['completed', 'failed', 'error', 'cancelled']:
            return True, f"Previous workflow {status}. New workflow can be started."
            
        # Idle/unknown states - allow new workflow
        return True, f"Previous workflow in {status} state. New workflow can be started."


class WorkflowStateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_workflow_state(
        self, 
        session_id: str, 
        client_account_id: uuid.UUID, 
        engagement_id: uuid.UUID,
        workflow_type: str = "discovery",
        current_phase: str = "initialization",
        initial_state_data: Any = None,
        allow_concurrent: bool = False
    ) -> Tuple[WorkflowState, bool, str]:
        """
        Smart workflow state management that handles concurrent workflows and user intent.
        
        Returns:
            (WorkflowState, is_new, message)
            - WorkflowState: The workflow state to use
            - is_new: True if a new workflow was created, False if existing was returned
            - message: Explanation of what happened
        """
        # Convert session_id to UUID if it's a string
        if isinstance(session_id, str):
            try:
                session_uuid = uuid.UUID(session_id)
            except ValueError:
                raise ValueError(f"Invalid session_id format: {session_id}")
        else:
            session_uuid = session_id
            
        # Check for existing workflow (handles unique constraint gracefully)
        existing_workflow = await self.get_workflow_state_by_session_id(
            session_id, client_account_id, engagement_id
        )
        
        if existing_workflow:
            # Check if we can start a new workflow
            can_start_new, reason = SessionConflictResolution.should_allow_new_workflow(existing_workflow)
            
            if not can_start_new and not allow_concurrent:
                # Return existing active workflow
                logger.info(f"Returning existing active workflow for session {session_id}: {reason}")
                return existing_workflow, False, reason
            
            if can_start_new:
                # Update existing workflow to restart it
                logger.info(f"Restarting workflow for session {session_id}: Previous status was {existing_workflow.status}")
                updated_workflow = await self.update_workflow_state(
                    session_id=session_id,
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    workflow_type=workflow_type,
                    current_phase=current_phase,
                    status="running",
                    state_data=initial_state_data or {}
                )
                return updated_workflow, True, f"Workflow restarted. Previous status: {existing_workflow.status}"
            
            # Fallback - return existing workflow
            return existing_workflow, False, reason
        
        # No existing workflow - create new one
        try:
            new_workflow = await self.create_workflow_state(
                session_id=session_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                workflow_type=workflow_type,
                current_phase=current_phase,
                status="running",
                state_data=initial_state_data or {}
            )
            logger.info(f"Created new workflow for session {session_id}")
            return new_workflow, True, "New workflow created"
        except Exception as e:
            # Handle race condition where another process created the workflow
            if "unique constraint" in str(e).lower():
                logger.warning(f"Race condition detected for session {session_id}, retrieving existing workflow")
                existing_workflow = await self.get_workflow_state_by_session_id(
                    session_id, client_account_id, engagement_id
                )
                if existing_workflow:
                    return existing_workflow, False, "Existing workflow found after race condition"
            raise e

    async def archive_old_workflows(self, workflows: List[WorkflowState]):
        """Archive old workflows by updating their status."""
        for workflow in workflows:
            if workflow.status not in ['completed', 'failed', 'error']:
                # Mark as cancelled if it wasn't already terminal
                workflow.status = 'cancelled'
                workflow.updated_at = datetime.utcnow()
                await self.db.commit()
                logger.info(f"Archived workflow {workflow.id} with status cancelled")

    async def get_all_workflows_for_session(
        self, 
        session_id: str, 
        client_account_id: uuid.UUID, 
        engagement_id: uuid.UUID
    ) -> List[WorkflowState]:
        """Get all workflow states for a session, ordered by creation time desc."""
        if isinstance(session_id, str):
            try:
                session_uuid = uuid.UUID(session_id)
            except ValueError:
                return []
        else:
            session_uuid = session_id
            
        result = await self.db.execute(
            select(WorkflowState)
            .filter(
                and_(
                    WorkflowState.session_id == session_uuid,
                    WorkflowState.client_account_id == client_account_id,
                    WorkflowState.engagement_id == engagement_id
                )
            )
            .order_by(desc(WorkflowState.created_at))
        )
        return result.scalars().all()

    async def get_active_workflow_for_session(
        self, 
        session_id: str, 
        client_account_id: uuid.UUID, 
        engagement_id: uuid.UUID
    ) -> Optional[WorkflowState]:
        """Get the active workflow for a session, if any."""
        workflows = await self.get_all_workflows_for_session(session_id, client_account_id, engagement_id)
        
        # Find actively running workflow
        for workflow in workflows:
            if workflow.status in ['running', 'in_progress', 'processing']:
                return workflow
                
        # If no active workflow, return the most recent one for status checking
        return SessionConflictResolution.get_active_or_most_recent(workflows)

    async def create_workflow_state(self, *, session_id: str, client_account_id: uuid.UUID, engagement_id: uuid.UUID, workflow_type: str, current_phase: str, status: str, state_data: Any) -> WorkflowState:
        # Convert session_id to UUID if it's a string
        if isinstance(session_id, str):
            try:
                session_uuid = uuid.UUID(session_id)
            except ValueError:
                raise ValueError(f"Invalid session_id format: {session_id}")
        else:
            session_uuid = session_id
        
        # Try to find an existing workflow first to handle unique constraint gracefully
        existing = await self.get_workflow_state_by_session_id(
            session_id, client_account_id, engagement_id
        )
        
        if existing:
            # Update existing workflow instead of creating new one
            logger.info(f"Updating existing workflow for session {session_id}")
            updated_ws = await self.update_workflow_state(
                session_id=session_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                workflow_type=workflow_type,
                current_phase=current_phase,
                status=status,
                state_data=state_data
            )
            return updated_ws
        
        # Create new workflow state
        ws = WorkflowState(
            session_id=session_uuid,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            workflow_type=workflow_type,
            current_phase=current_phase,
            status=status,
            state_data=state_data
        )
        
        try:
            self.db.add(ws)
            await self.db.commit()
            await self.db.refresh(ws)
            logger.info(f"Created new workflow for session {session_id}")
            return ws
        except Exception as e:
            # Handle unique constraint violation gracefully
            await self.db.rollback()
            if "unique constraint" in str(e).lower() or "already exists" in str(e).lower():
                # If there's a unique constraint violation, try to get the existing one
                logger.warning(f"Unique constraint violation for session {session_id}, retrieving existing workflow")
                existing = await self.get_workflow_state_by_session_id(
                    session_id, client_account_id, engagement_id
                )
                if existing:
                    return existing
            # Re-raise if it's not a unique constraint issue
            raise e

    async def get_workflow_state_by_session_id(self, session_id: str, client_account_id: uuid.UUID, engagement_id: uuid.UUID) -> Optional[WorkflowState]:
        """Get the primary workflow state for a session."""
        return await self.get_active_workflow_for_session(session_id, client_account_id, engagement_id)

    async def update_workflow_state(self, session_id: str, client_account_id: uuid.UUID, engagement_id: uuid.UUID, **kwargs) -> Optional[WorkflowState]:
        ws = await self.get_workflow_state_by_session_id(session_id, client_account_id, engagement_id)
        if not ws:
            return None
        for key, value in kwargs.items():
            if hasattr(ws, key):
                setattr(ws, key, value)
        ws.updated_at = datetime.utcnow()
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

    async def cleanup_old_workflows(self, days_old: int = 30) -> int:
        """Clean up workflows older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        result = await self.db.execute(
            select(WorkflowState).filter(
                and_(
                    WorkflowState.created_at < cutoff_date,
                    WorkflowState.status.in_(['completed', 'failed', 'error', 'cancelled'])
                )
            )
        )
        old_workflows = result.scalars().all()
        
        for workflow in old_workflows:
            await self.db.delete(workflow)
            
        await self.db.commit()
        logger.info(f"Cleaned up {len(old_workflows)} old workflows")
        return len(old_workflows)
