"""
Flow Manager for lifecycle management
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

# Direct UnifiedDiscoveryFlow imports removed - use MasterFlowOrchestrator instead
from app.core.context import RequestContext
from app.services.flows.base_flow import BaseDiscoveryFlow

logger = logging.getLogger(__name__)


class FlowManager:
    """
    Manages flow lifecycle and execution.
    Features:
    - Flow creation and initialization
    - Execution management
    - Status tracking
    - Flow resumption
    """
    
    def __init__(self):
        self.active_flows: Dict[str, BaseDiscoveryFlow] = {}
        self.flow_tasks: Dict[str, asyncio.Task] = {}
    
    async def create_discovery_flow(
        self,
        db: AsyncSession,
        context: RequestContext,
        import_data: Dict[str, Any]
    ) -> str:
        """Create and start a new discovery flow through MasterFlowOrchestrator"""
        from app.services.master_flow_orchestrator import MasterFlowOrchestrator
        orchestrator = MasterFlowOrchestrator(db, context)
        
        # Extract flow_id and prepare initial state
        flow_id = import_data.get("flow_id")
        initial_state = {
            "import_data": import_data,
            "raw_data": import_data.get("raw_data", [])
        }
        
        # Create flow through orchestrator
        new_flow_id, flow_details = await orchestrator.create_flow(
            flow_type="discovery",
            flow_name=f"Discovery Flow {flow_id}",
            initial_state=initial_state
        )
        
        logger.info(f"Created and started discovery flow through MasterFlowOrchestrator: {new_flow_id}")
        return new_flow_id
    
    async def get_flow_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a flow through MasterFlowOrchestrator"""
        from app.core.context import RequestContext
        from app.core.database import AsyncSessionLocal
        from app.services.master_flow_orchestrator import MasterFlowOrchestrator
        
        # Create a new session for status check
        async with AsyncSessionLocal() as db:
            # Create minimal context for status check
            context = RequestContext()
            orchestrator = MasterFlowOrchestrator(db, context)
            
            try:
                status = await orchestrator.get_flow_status(flow_id)
                return status
            except Exception as e:
                logger.error(f"Failed to get flow status: {e}")
                return None
    
    async def pause_flow(self, flow_id: str) -> bool:
        """Pause a running flow - delegated to MasterFlowOrchestrator"""
        # This method should be implemented through MasterFlowOrchestrator
        logger.warning("pause_flow called but should use MasterFlowOrchestrator.pause_flow")
        return False
        task = self.flow_tasks.get(flow_id)
        if task and not task.done():
            task.cancel()
            logger.info(f"Paused flow: {flow_id}")
            return True
        return False
    
    async def resume_flow(
        self,
        flow_id: str,
        db: AsyncSession,
        context: RequestContext
    ) -> bool:
        """Resume a paused flow from last checkpoint"""
        # Flow resumption should be handled through MasterFlowOrchestrator
        from app.services.master_flow_orchestrator import MasterFlowOrchestrator
        orchestrator = MasterFlowOrchestrator(db, context)
        
        # Resume flow through orchestrator
        try:
            await orchestrator.resume_flow(flow_id)
            logger.info(f"Resumed flow: {flow_id} through MasterFlowOrchestrator")
            return True
        except Exception as e:
            logger.error(f"Failed to resume flow through orchestrator: {e}")
            return False
    
    def _get_resume_method(self, flow_id: str, phases_completed: List[str]):
        """Determine which phase to resume from - now handled by MasterFlowOrchestrator"""
        # This method is deprecated - MasterFlowOrchestrator handles resume logic
        logger.warning("_get_resume_method called but should use MasterFlowOrchestrator.resume_flow")
        return None
    
    async def cleanup_completed_flows(self) -> int:
        """Clean up completed flow instances"""
        cleaned = 0
        
        for flow_id in list(self.flow_tasks.keys()):
            task = self.flow_tasks[flow_id]
            if task.done():
                del self.flow_tasks[flow_id]
                if flow_id in self.active_flows:
                    del self.active_flows[flow_id]
                cleaned += 1
        
        logger.info(f"Cleaned up {cleaned} completed flows")
        return cleaned
    
    async def get_all_flow_statuses(self) -> List[Dict[str, Any]]:
        """Get status of all active flows"""
        statuses = []
        for flow_id in self.active_flows.keys():
            status = await self.get_flow_status(flow_id)
            if status:
                statuses.append(status)
        return statuses
    
    async def force_complete_flow(self, flow_id: str, reason: str = "forced") -> bool:
        """Force complete a flow (for emergency situations) - delegated to MasterFlowOrchestrator"""
        from app.core.context import RequestContext
        from app.core.database import AsyncSessionLocal
        from app.services.master_flow_orchestrator import MasterFlowOrchestrator
        
        async with AsyncSessionLocal() as db:
            context = RequestContext()
            orchestrator = MasterFlowOrchestrator(db, context)
            
            try:
                # Update flow status to completed
                await orchestrator.update_flow_status(flow_id, "completed", {"reason": reason})
                return True
            except Exception as e:
                logger.error(f"Failed to force complete flow: {e}")
                return False


# Global flow manager instance
flow_manager = FlowManager()