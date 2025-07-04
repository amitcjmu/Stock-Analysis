"""
V3 Discovery Flow Service
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.v3.discovery_flow import V3DiscoveryFlowRepository
from app.repositories.v3.field_mapping import V3FieldMappingRepository
from app.models import DiscoveryFlow
from app.repositories.v3.discovery_flow import FlowStatus
from app.core.context import get_current_context
import logging
import uuid

logger = logging.getLogger(__name__)

class V3DiscoveryFlowService:
    """Service for V3 discovery flow operations"""
    
    def __init__(self, db: AsyncSession, client_account_id: Optional[str] = None, engagement_id: Optional[str] = None):
        self.db = db
        
        # Get context if not provided
        if not client_account_id or not engagement_id:
            try:
                context = get_current_context()
                client_account_id = client_account_id or str(context.client_account_id)
                engagement_id = engagement_id or str(context.engagement_id)
            except:
                # Default fallback if context not available
                client_account_id = client_account_id or str(uuid.uuid4())
                engagement_id = engagement_id or str(uuid.uuid4())
        
        self.flow_repo = V3DiscoveryFlowRepository(db, client_account_id, engagement_id)
        self.mapping_repo = V3FieldMappingRepository(db, client_account_id, engagement_id)
    
    async def create_flow(
        self,
        flow_name: str,
        data_import_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        master_flow_id: Optional[str] = None
    ) -> DiscoveryFlow:
        """Create a new discovery flow with consolidated fields"""
        try:
            # Generate CrewAI Flow ID
            flow_id = uuid.uuid4()
            
            flow_data = {
                "flow_id": flow_id,  # CrewAI Flow ID is required
                "flow_name": flow_name,
                "data_import_id": data_import_id,
                "master_flow_id": master_flow_id,  # For orchestration
                "status": FlowStatus.INITIALIZING,
                "current_phase": "initialization",
                "progress_percentage": 0.0,
                "flow_state": metadata or {},
                "phases_completed": [],
                "crew_outputs": {},
                "user_id": user_id or "system"
            }
            
            flow = await self.flow_repo.create(flow_data)
            
            logger.info(f"Created discovery flow {flow.id} with CrewAI flow_id {flow_id}")
            
            return flow
            
        except Exception as e:
            logger.error(f"Failed to create flow: {e}")
            raise
    
    async def get_flow_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive flow status"""
        flow = await self.flow_repo.get_by_id(flow_id)
        if not flow:
            return None
        
        # Get field mappings if available
        mappings = None
        if flow.data_import_id:
            mappings = await self.mapping_repo.get_by_import(str(flow.data_import_id))
        
        return {
            "flow_id": str(flow.id),
            "flow_name": flow.flow_name,
            "status": flow.status,
            "current_phase": flow.current_phase,
            "phases_completed": flow.phases_completed or [],
            "progress_percentage": flow.progress_percentage,
            "data_import_id": str(flow.data_import_id) if flow.data_import_id else None,
            "field_mappings": self._serialize_mappings(mappings) if mappings else None,
            "discovered_assets": flow.discovered_assets,
            "dependencies": flow.dependencies,
            "tech_debt_analysis": flow.tech_debt_analysis,
            "flow_state": flow.flow_state,
            "crew_outputs": flow.crew_outputs,
            "error": {
                "message": flow.error_message,
                "phase": flow.error_phase,
                "details": flow.error_details
            } if flow.error_message else None,
            "created_at": flow.created_at.isoformat() if flow.created_at else None,
            "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
            "started_at": flow.started_at.isoformat() if flow.started_at else None,
            "completed_at": flow.completed_at.isoformat() if flow.completed_at else None
        }
    
    async def update_flow_progress(
        self,
        flow_id: str,
        phase: str,
        progress: float,
        state_updates: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update flow progress and state"""
        try:
            # Get current flow state
            flow = await self.flow_repo.get_by_id(flow_id)
            if not flow:
                return False
            
            # Merge state updates
            current_state = flow.flow_state or {}
            if state_updates:
                current_state.update(state_updates)
            
            success = await self.flow_repo.update_flow_state(
                flow_id,
                phase,
                current_state,
                progress
            )
            
            if success:
                logger.info(f"Updated flow {flow_id}: phase={phase}, progress={progress}%")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update flow progress: {e}")
            return False
    
    async def continue_flow(self, flow_id: str) -> bool:
        """Continue a paused or failed flow"""
        flow = await self.flow_repo.get_by_id(flow_id)
        if not flow:
            return False
        
        if flow.status not in [FlowStatus.PAUSED, FlowStatus.FAILED]:
            logger.warning(f"Cannot continue flow {flow_id} in status {flow.status}")
            return False
        
        # Update status to running
        success = await self.flow_repo.resume_flow(flow_id)
        
        if success:
            logger.info(f"Resumed flow {flow_id}")
            # TODO: Integrate with actual flow manager if needed
            # await flow_manager.resume_flow(flow_id, self.db, context)
        
        return success
    
    async def pause_flow(self, flow_id: str) -> bool:
        """Pause a running flow"""
        success = await self.flow_repo.pause_flow(flow_id)
        
        if success:
            logger.info(f"Paused flow {flow_id}")
            # TODO: Integrate with actual flow manager if needed
            # await flow_manager.pause_flow(flow_id)
        
        return success
    
    async def cancel_flow(self, flow_id: str) -> bool:
        """Cancel a flow"""
        success = await self.flow_repo.cancel_flow(flow_id)
        
        if success:
            logger.info(f"Cancelled flow {flow_id}")
            # TODO: Integrate with actual flow manager if needed
            # await flow_manager.pause_flow(flow_id)
        
        return success
    
    async def complete_flow(
        self,
        flow_id: str,
        final_results: Dict[str, Any]
    ) -> bool:
        """Mark flow as completed with final results"""
        try:
            success = await self.flow_repo.complete_flow(flow_id, final_results)
            
            if success:
                logger.info(f"Completed flow {flow_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to complete flow: {e}")
            return False
    
    async def fail_flow(
        self,
        flow_id: str,
        error_message: str,
        error_phase: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Mark flow as failed"""
        try:
            success = await self.flow_repo.fail_flow(
                flow_id,
                error_message,
                error_phase,
                error_details or {}
            )
            
            if success:
                logger.info(f"Failed flow {flow_id} in phase {error_phase}: {error_message}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to mark flow as failed: {e}")
            return False
    
    async def get_active_flows(self) -> List[Dict[str, Any]]:
        """Get all active flows for current context"""
        flows = await self.flow_repo.get_active_flows()
        
        return [
            {
                "flow_id": str(flow.id),
                "flow_name": flow.flow_name,
                "status": flow.status,
                "current_phase": flow.current_phase,
                "progress_percentage": flow.progress_percentage,
                "data_import_id": str(flow.data_import_id) if flow.data_import_id else None,
                "created_at": flow.created_at.isoformat() if flow.created_at else None,
                "updated_at": flow.updated_at.isoformat() if flow.updated_at else None
            }
            for flow in flows
        ]
    
    async def list_flows(self, status: Optional[str] = None, limit: int = 50, offset: int = 0, 
                         status_filter: Optional[str] = None, execution_mode: Optional[str] = None) -> List[Dict[str, Any]]:
        """List flows with optional filtering"""
        # Use status_filter if provided, otherwise use status
        filter_status = status_filter or status
        
        if filter_status and filter_status == 'active':
            return await self.get_active_flows()
        
        # Get all flows with optional status filter
        flows = await self.flow_repo.get_all(limit=limit, offset=offset)
        
        # Filter by status if provided
        if filter_status:
            flows = [f for f in flows if f.status == filter_status]
        
        # Filter by execution mode if provided (currently all flows are in 'synchronous' mode)
        if execution_mode:
            # For now, all flows use synchronous mode
            pass
        
        return [
            {
                "flow_id": str(flow.id),
                "flow_name": flow.flow_name,
                "status": flow.status,
                "current_phase": flow.current_phase,
                "progress_percentage": flow.progress_percentage,
                "data_import_id": str(flow.data_import_id) if flow.data_import_id else None,
                "created_at": flow.created_at.isoformat() if flow.created_at else None,
                "updated_at": flow.updated_at.isoformat() if flow.updated_at else None
            }
            for flow in flows
        ]
    
    async def get_flow_by_import(self, import_id: str) -> Optional[Dict[str, Any]]:
        """Get flow associated with a data import"""
        flow = await self.flow_repo.get_by_import_id(import_id)
        if not flow:
            return None
        
        return await self.get_flow_status(str(flow.id))
    
    async def delete_flow(self, flow_id: str) -> bool:
        """Delete a flow"""
        try:
            success = await self.flow_repo.delete(flow_id)
            
            if success:
                logger.info(f"Deleted flow {flow_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete flow {flow_id}: {e}")
            return False
    
    def _serialize_mappings(self, mappings) -> List[Dict[str, Any]]:
        """Serialize field mappings for API response"""
        return [
            {
                "id": str(mapping.id),
                "source_field": mapping.source_field,
                "target_field": mapping.target_field,
                "confidence_score": mapping.confidence_score,
                "match_type": mapping.match_type,
                "status": mapping.status,
                "transformation_rules": mapping.transformation_rules,
                "approved_by": mapping.approved_by,
                "approved_at": mapping.approved_at.isoformat() if mapping.approved_at else None
            }
            for mapping in mappings
        ]
    
    async def complete_phase(
        self,
        flow_id: str,
        phase: str,
        phase_results: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Complete a specific phase (hybrid approach)"""
        try:
            # Update phase completion
            success = await self.flow_repo.update_phase_completion(flow_id, phase, True)
            
            if success and phase_results:
                # Store phase results in crew_outputs
                flow = await self.flow_repo.get_by_id(flow_id)
                if flow:
                    crew_outputs = flow.crew_outputs or {}
                    crew_outputs[phase] = phase_results
                    
                    await self.flow_repo.update(flow_id, {"crew_outputs": crew_outputs})
            
            if success:
                logger.info(f"Completed phase {phase} for flow {flow_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to complete phase: {e}")
            return False
    
    async def update_phase_state(
        self,
        flow_id: str,
        phase: str,
        phase_state: Dict[str, Any]
    ) -> bool:
        """Update state for a specific phase"""
        try:
            # Store phase-specific state
            flow = await self.flow_repo.get_by_id(flow_id)
            if not flow:
                return False
            
            flow_state = flow.flow_state or {}
            flow_state[phase] = phase_state
            
            success = await self.flow_repo.update(flow_id, {"flow_state": flow_state})
            
            if success:
                logger.info(f"Updated state for phase {phase} in flow {flow_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update phase state: {e}")
            return False
    
    async def get_flow_statistics(self, flow_id: str) -> Dict[str, Any]:
        """Get detailed flow statistics"""
        return await self.flow_repo.get_flow_statistics(flow_id)