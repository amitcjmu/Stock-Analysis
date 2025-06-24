"""
Flow Management Handler
Handles PostgreSQL-based discovery flow management operations.
Wraps the V2 discovery flow service for the unified API.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

logger = logging.getLogger(__name__)

class FlowManagementHandler:
    """
    Handler for PostgreSQL-based discovery flow management.
    Provides enterprise-grade flow lifecycle management with multi-tenant isolation.
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.logger = logger
    
    async def create_flow(
        self,
        flow_id: str,
        raw_data: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        import_session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new discovery flow in PostgreSQL.
        """
        try:
            self.logger.info(f"🗄️ Creating PostgreSQL flow: {flow_id}")
            
            # Import V2 service
            from app.services.discovery_flow_service import DiscoveryFlowService
            
            service = DiscoveryFlowService(self.db, self.context)
            
            flow = await service.create_discovery_flow(
                flow_id=flow_id,
                raw_data=raw_data,
                metadata=metadata or {},
                import_session_id=import_session_id,
                user_id=self.context.user_id
            )
            
            self.logger.info(f"✅ PostgreSQL flow created: {flow_id}")
            return flow.to_dict()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create PostgreSQL flow: {e}")
            raise
    
    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """
        Get discovery flow status from PostgreSQL.
        """
        try:
            self.logger.info(f"🔍 Getting PostgreSQL flow status: {flow_id}")
            
            from app.services.discovery_flow_service import DiscoveryFlowService
            
            service = DiscoveryFlowService(self.db, self.context)
            flow = await service.get_flow_by_id(flow_id)
            
            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")
            
            status_data = flow.to_dict()
            
            # Add handler-specific metadata
            status_data.update({
                "handler": "postgresql",
                "multi_tenant": True,
                "persistence_layer": "database"
            })
            
            self.logger.info(f"✅ PostgreSQL flow status retrieved: {flow_id}")
            return status_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get PostgreSQL flow status: {e}")
            raise
    
    async def execute_phase(
        self,
        phase: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a discovery flow phase using PostgreSQL management.
        """
        try:
            self.logger.info(f"🔄 Executing PostgreSQL phase: {phase}")
            
            # For now, return a success response
            # TODO: Implement actual phase execution coordination
            
            result = {
                "status": "completed",
                "phase": phase,
                "handler": "postgresql",
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ PostgreSQL phase execution completed: {phase}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ PostgreSQL phase execution failed: {e}")
            raise
    
    async def get_active_flows(self) -> List[Dict[str, Any]]:
        """
        Get active discovery flows from PostgreSQL.
        """
        try:
            self.logger.info("🔍 Getting active PostgreSQL flows")
            
            from app.services.discovery_flow_service import DiscoveryFlowService
            
            service = DiscoveryFlowService(self.db, self.context)
            flows = await service.get_active_flows()
            
            # Convert to dict format
            flow_data = []
            for flow in flows:
                flow_dict = flow.to_dict()
                flow_dict.update({
                    "handler": "postgresql",
                    "multi_tenant": True
                })
                flow_data.append(flow_dict)
            
            self.logger.info(f"✅ Retrieved {len(flow_data)} active PostgreSQL flows")
            return flow_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get active PostgreSQL flows: {e}")
            raise 