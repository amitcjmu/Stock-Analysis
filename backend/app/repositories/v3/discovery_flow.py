"""
V3 Discovery Flow Repository
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from app.repositories.v3.base import V3BaseRepository
from app.models.v3 import V3DiscoveryFlow, FlowStatus
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class V3DiscoveryFlowRepository(V3BaseRepository[V3DiscoveryFlow]):
    """Repository for V3 discovery flows"""
    
    def __init__(self, db: AsyncSession, client_account_id: Optional[str] = None, engagement_id: Optional[str] = None):
        super().__init__(db, V3DiscoveryFlow, client_account_id, engagement_id)
    
    async def get_active_flows(self) -> List[V3DiscoveryFlow]:
        """Get all active flows"""
        query = select(V3DiscoveryFlow).where(
            V3DiscoveryFlow.status.in_([
                FlowStatus.INITIALIZING,
                FlowStatus.RUNNING,
                FlowStatus.PAUSED
            ])
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_import_id(self, import_id: str) -> Optional[V3DiscoveryFlow]:
        """Get flow by import ID"""
        query = select(V3DiscoveryFlow).where(
            V3DiscoveryFlow.data_import_id == import_id
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_flow_state(
        self,
        flow_id: str,
        phase: str,
        state: Dict[str, Any],
        progress: float
    ) -> bool:
        """Update flow state and progress"""
        # Get current flow to verify context and update phases
        flow = await self.get_by_id(flow_id)
        if not flow:
            return False
        
        # Update phases completed
        phases_completed = flow.phases_completed or []
        if phase not in phases_completed and flow.current_phase and phase != flow.current_phase:
            phases_completed.append(flow.current_phase)
        
        # Update flow
        query = update(V3DiscoveryFlow).where(
            V3DiscoveryFlow.id == flow_id
        ).values(
            current_phase=phase,
            phases_completed=phases_completed,
            flow_state=state,
            progress_percentage=progress,
            status=FlowStatus.RUNNING,
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def complete_flow(
        self,
        flow_id: str,
        final_state: Dict[str, Any]
    ) -> bool:
        """Mark flow as completed"""
        # First get the flow to verify context
        flow = await self.get_by_id(flow_id)
        if not flow:
            return False
        
        query = update(V3DiscoveryFlow).where(
            V3DiscoveryFlow.id == flow_id
        ).values(
            status=FlowStatus.COMPLETED,
            flow_state=final_state,
            progress_percentage=100.0,
            completed_at=func.now(),
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def fail_flow(
        self,
        flow_id: str,
        error_message: str,
        error_phase: str,
        error_details: Dict[str, Any]
    ) -> bool:
        """Mark flow as failed"""
        # First get the flow to verify context
        flow = await self.get_by_id(flow_id)
        if not flow:
            return False
        
        query = update(V3DiscoveryFlow).where(
            V3DiscoveryFlow.id == flow_id
        ).values(
            status=FlowStatus.FAILED,
            error_message=error_message,
            error_phase=error_phase,
            error_details=error_details,
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def pause_flow(self, flow_id: str) -> bool:
        """Pause a running flow"""
        # First get the flow to verify context
        flow = await self.get_by_id(flow_id)
        if not flow or flow.status != FlowStatus.RUNNING:
            return False
        
        query = update(V3DiscoveryFlow).where(
            V3DiscoveryFlow.id == flow_id
        ).values(
            status=FlowStatus.PAUSED,
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def resume_flow(self, flow_id: str) -> bool:
        """Resume a paused flow"""
        # First get the flow to verify context
        flow = await self.get_by_id(flow_id)
        if not flow or flow.status != FlowStatus.PAUSED:
            return False
        
        query = update(V3DiscoveryFlow).where(
            V3DiscoveryFlow.id == flow_id
        ).values(
            status=FlowStatus.RUNNING,
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def cancel_flow(self, flow_id: str) -> bool:
        """Cancel a flow"""
        # First get the flow to verify context
        flow = await self.get_by_id(flow_id)
        if not flow:
            return False
        
        query = update(V3DiscoveryFlow).where(
            V3DiscoveryFlow.id == flow_id
        ).values(
            status=FlowStatus.CANCELLED,
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0