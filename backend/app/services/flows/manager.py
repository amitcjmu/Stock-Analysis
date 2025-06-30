"""
Flow Manager for lifecycle management
"""

from typing import Dict, Any, Optional, List
from app.services.flows.base_flow import BaseDiscoveryFlow
from app.services.flows.discovery_flow import UnifiedDiscoveryFlow, DiscoveryFlowState
from app.core.context import RequestContext
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import logging

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
        """Create and start a new discovery flow"""
        flow = UnifiedDiscoveryFlow(db, context)
        flow_id = import_data["flow_id"]
        
        # Store flow instance
        self.active_flows[flow_id] = flow
        
        # Start flow execution in background
        task = asyncio.create_task(
            flow.kickoff(inputs={"import_data": import_data})
        )
        self.flow_tasks[flow_id] = task
        
        logger.info(f"Created and started discovery flow: {flow_id}")
        return flow_id
    
    async def get_flow_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a flow"""
        flow = self.active_flows.get(flow_id)
        if not flow:
            return None
        
        # Load current state
        state = await flow.load_state(flow_id)
        if not state:
            return None
        
        return {
            "flow_id": flow_id,
            "current_phase": state.current_phase,
            "phases_completed": state.phases_completed,
            "progress_percentage": state.progress_percentage,
            "error": state.error,
            "is_active": flow_id in self.flow_tasks and not self.flow_tasks[flow_id].done(),
            "status": state.status
        }
    
    async def pause_flow(self, flow_id: str) -> bool:
        """Pause a running flow"""
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
        # Create new flow instance
        flow = UnifiedDiscoveryFlow(db, context)
        
        # Load existing state
        state = await flow.load_state(flow_id)
        if not state:
            logger.error(f"No state found for flow: {flow_id}")
            return False
        
        # Determine resume point based on completed phases
        resume_method = self._get_resume_method(flow, state.phases_completed)
        if not resume_method:
            logger.error(f"Cannot determine resume point for flow: {flow_id}")
            return False
        
        # Store flow instance
        self.active_flows[flow_id] = flow
        
        # Resume execution
        task = asyncio.create_task(
            resume_method(state)
        )
        self.flow_tasks[flow_id] = task
        
        logger.info(f"Resumed flow: {flow_id} from phase {state.current_phase}")
        return True
    
    def _get_resume_method(self, flow: UnifiedDiscoveryFlow, phases_completed: List[str]):
        """Determine which method to call for resumption"""
        phase_methods = {
            "initialization": flow.validate_and_analyze_data,
            "data_validation": flow.perform_field_mapping,
            "field_mapping": flow.cleanse_data,
            "data_cleansing": flow.build_asset_inventory,
            "asset_inventory": flow.analyze_dependencies,
            "dependency_analysis": flow.assess_technical_debt
        }
        
        # Find next phase
        for phase, method in phase_methods.items():
            if phase not in phases_completed:
                return method
        
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
        """Force complete a flow (for emergency situations)"""
        flow = self.active_flows.get(flow_id)
        if not flow:
            return False
        
        try:
            # Load current state
            state = await flow.load_state(flow_id)
            if state:
                state.status = "completed"
                state.current_phase = "completed"
                state.progress_percentage = 100.0
                state.metadata["force_completed"] = True
                state.metadata["force_reason"] = reason
                
                # Save final state
                await flow.save_state(state)
                
                # Emit forced completion event
                flow.emit_event("flow_force_completed", {
                    "flow_id": flow_id,
                    "reason": reason
                })
                
                logger.warning(f"Force completed flow {flow_id}: {reason}")
                return True
        except Exception as e:
            logger.error(f"Failed to force complete flow {flow_id}: {e}")
        
        return False


# Global flow manager instance
flow_manager = FlowManager()