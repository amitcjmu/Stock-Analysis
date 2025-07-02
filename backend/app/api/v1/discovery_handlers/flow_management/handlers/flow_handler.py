"""
Flow Handler

Main handler that orchestrates all flow management operations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

# Import sub-handlers
from .create_handler import CreateHandler
from .status_handler import StatusHandler
from .update_handler import UpdateHandler
from .delete_handler import DeleteHandler

# Import validators
from ..validators.flow_validator import FlowValidator
from ..validators.permission_validator import PermissionValidator

# Import services
from ..services.flow_service import FlowService

logger = logging.getLogger(__name__)


class FlowManagementHandler:
    """Main handler for PostgreSQL-based discovery flow management"""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize with database session and request context"""
        self.db = db
        self.context = context
        self.client_account_id = context.client_account_id
        self.engagement_id = context.engagement_id
        self.user_id = context.user_id
        
        # Initialize repository with context handling
        client_id = str(context.client_account_id) if context.client_account_id else "11111111-1111-1111-1111-111111111111"
        engagement_id = str(context.engagement_id) if context.engagement_id else "22222222-2222-2222-2222-222222222222"
        
        self.flow_repo = DiscoveryFlowRepository(
            db=db,
            client_account_id=client_id,
            engagement_id=engagement_id
        )
        
        # Initialize validators
        self.flow_validator = FlowValidator(self.flow_repo)
        self.permission_validator = PermissionValidator(context)
        
        # Initialize service
        self.flow_service = FlowService(db)
        
        # Initialize handlers
        self.create_handler = CreateHandler(db, context)
        self.status_handler = StatusHandler(db, self.flow_repo)
        self.update_handler = UpdateHandler(db, self.flow_repo)
        self.delete_handler = DeleteHandler(db, self.flow_repo, self.permission_validator)
    
    # Delegate to create handler
    async def create_flow(self, flow_id: str, raw_data: List[Dict[str, Any]], 
                         metadata: Dict[str, Any], data_import_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new discovery flow"""
        return await self.create_handler.create_flow(flow_id, raw_data, metadata, data_import_id)
    
    # Delegate to status handler
    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get detailed status of a discovery flow"""
        return await self.status_handler.get_flow_status(flow_id)
    
    async def get_active_flows(self) -> List[Dict[str, Any]]:
        """Get active flows from PostgreSQL"""
        try:
            logger.info(f"🔍 Getting active flows for context - client: {self.client_account_id}, engagement: {self.engagement_id}")
            
            # Get actual flows from database
            flows = await self.flow_repo.get_active_flows()
            
            # If no flows found with current context, try getting ALL active flows
            if not flows:
                logger.info("🔍 No flows found with current context, trying global search for active flows")
                
                # Get all flows globally and filter for active ones
                from sqlalchemy import select, desc
                from app.models.discovery_flow import DiscoveryFlow
                
                valid_active_statuses = [
                    "initialized", "active", "running", "paused",
                    # Phase names that might have been set as status
                    "data_import", "attribute_mapping", "field_mapping", 
                    "data_cleansing", "inventory", "dependencies", "tech_debt"
                ]
                
                stmt = select(DiscoveryFlow).where(
                    DiscoveryFlow.status.in_(valid_active_statuses)
                ).order_by(desc(DiscoveryFlow.updated_at))
                
                result = await self.db.execute(stmt)
                all_flows = result.scalars().all()
                
                if all_flows:
                    logger.info(f"✅ Found {len(all_flows)} active flows globally")
                    
                    # Convert to list of dicts
                    flows = []
                    for flow in all_flows:
                        flows.append({
                            "flow_id": str(flow.flow_id),
                            "data_import_id": str(flow.data_import_id) if flow.data_import_id else None,
                            "status": flow.status,
                            "current_phase": flow.get_next_phase() or "completed",
                            "phases": {
                                "data_import": flow.data_import_completed or False,
                                "attribute_mapping": flow.attribute_mapping_completed or False,
                                "data_cleansing": flow.data_cleansing_completed or False,
                                "inventory": flow.inventory_completed or False,
                                "dependencies": flow.dependencies_completed or False,
                                "tech_debt": flow.tech_debt_completed or False
                            },
                            "client_account_id": str(flow.client_account_id) if flow.client_account_id else None,
                            "engagement_id": str(flow.engagement_id) if flow.engagement_id else None,
                            "created_at": flow.created_at.isoformat() if flow.created_at else "",
                            "updated_at": flow.updated_at.isoformat() if flow.updated_at else ""
                        })
                else:
                    logger.info("🔍 No active flows found globally")
            else:
                # Convert ORM flows to dicts
                flows = [self._flow_to_dict(flow) for flow in flows]
            
            logger.info(f"✅ Returning {len(flows)} active flows")
            return flows
            
        except Exception as e:
            logger.error(f"❌ Failed to get active flows: {e}")
            raise
    
    # Delegate to update handler
    async def continue_flow(self, flow_id: str) -> Dict[str, Any]:
        """Continue flow to the next phase"""
        return await self.update_handler.continue_flow(flow_id)
    
    async def complete_flow(self, flow_id: str) -> Dict[str, Any]:
        """Complete a discovery flow"""
        return await self.update_handler.complete_flow(flow_id)
    
    # Delegate to delete handler
    async def delete_flow(self, flow_id: str, force_delete: bool = False) -> Dict[str, Any]:
        """Delete a discovery flow and cleanup"""
        return await self.delete_handler.delete_flow(flow_id, force_delete)
    
    # Phase execution method (complex logic stays in main handler for now)
    async def execute_phase(self, phase: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific phase of the discovery flow"""
        try:
            logger.info(f"🚀 Executing phase: {phase}")
            
            # Validate phase
            valid_phases = ["data_import", "attribute_mapping", "field_mapping", 
                          "data_cleansing", "inventory", "dependencies", "tech_debt"]
            
            if phase not in valid_phases:
                raise ValueError(f"Invalid phase: {phase}. Must be one of {valid_phases}")
            
            # Map attribute_mapping to field_mapping for consistency
            if phase == "attribute_mapping":
                phase = "field_mapping"
            
            # Execute phase-specific logic
            if phase == "data_import":
                return await self._execute_data_import(data)
            elif phase == "field_mapping":
                return await self._execute_field_mapping(data)
            elif phase == "data_cleansing":
                return await self._execute_data_cleansing(data)
            elif phase == "inventory":
                return await self._execute_inventory(data)
            elif phase == "dependencies":
                return await self._execute_dependencies(data)
            elif phase == "tech_debt":
                return await self._execute_tech_debt(data)
            else:
                raise ValueError(f"Phase {phase} not implemented")
                
        except Exception as e:
            logger.error(f"❌ Phase execution failed: {e}")
            raise
    
    # Private helper methods
    def _flow_to_dict(self, flow) -> Dict[str, Any]:
        """Convert flow ORM object to dictionary"""
        return {
            "flow_id": str(flow.flow_id),
            "data_import_id": str(flow.data_import_id) if flow.data_import_id else None,
            "status": flow.status,
            "current_phase": flow.get_next_phase() or "completed",
            "phases": {
                "data_import": flow.data_import_completed or False,
                "attribute_mapping": flow.attribute_mapping_completed or False,
                "data_cleansing": flow.data_cleansing_completed or False,
                "inventory": flow.inventory_completed or False,
                "dependencies": flow.dependencies_completed or False,
                "tech_debt": flow.tech_debt_completed or False
            },
            "client_account_id": str(flow.client_account_id) if flow.client_account_id else None,
            "engagement_id": str(flow.engagement_id) if flow.engagement_id else None,
            "created_at": flow.created_at.isoformat() if flow.created_at else "",
            "updated_at": flow.updated_at.isoformat() if flow.updated_at else ""
        }
    
    # Phase execution methods (simplified for modularization)
    async def _execute_data_import(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data import phase"""
        flow_id = data.get("flow_id")
        if not flow_id:
            raise ValueError("flow_id is required for data import")
        
        # Mark phase as complete
        await self.flow_repo.update_phase_completion(
            flow_id=flow_id,
            phase="data_import",
            data={"records_processed": data.get("records_processed", 0)},
            completed=True
        )
        
        return {
            "status": "completed",
            "phase": "data_import",
            "message": "Data import phase completed",
            "next_phase": "field_mapping"
        }
    
    async def _execute_field_mapping(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute field mapping phase"""
        flow_id = data.get("flow_id")
        if not flow_id:
            raise ValueError("flow_id is required for field mapping")
        
        # Update phase completion
        await self.flow_repo.update_phase_completion(
            flow_id=flow_id,
            phase="attribute_mapping",
            data={"mappings": data.get("field_mappings", {})},
            completed=True
        )
        
        return {
            "status": "completed",
            "phase": "field_mapping",
            "message": "Field mapping phase completed",
            "next_phase": "data_cleansing"
        }
    
    async def _execute_data_cleansing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data cleansing phase"""
        flow_id = data.get("flow_id")
        if not flow_id:
            raise ValueError("flow_id is required for data cleansing")
        
        # Get flow to access data
        flow = await self.flow_repo.get_by_flow_id(flow_id)
        if not flow:
            raise ValueError(f"Flow {flow_id} not found")
        
        # Perform data cleansing
        raw_data = data.get("raw_data", [])
        field_mappings = data.get("field_mappings", {})
        
        cleaned_data, quality_metrics = await self.flow_service.perform_data_cleansing(
            raw_data, field_mappings
        )
        
        # Create discovery assets if data is clean
        if cleaned_data:
            assets_created = await self.flow_service.create_discovery_assets_from_cleaned_data(
                flow, cleaned_data, []
            )
            quality_metrics["assets_created"] = assets_created
        
        # Update phase completion
        await self.flow_repo.update_phase_completion(
            flow_id=flow_id,
            phase="data_cleansing",
            data={"quality_metrics": quality_metrics},
            completed=True
        )
        
        return {
            "status": "completed",
            "phase": "data_cleansing",
            "message": "Data cleansing phase completed",
            "quality_metrics": quality_metrics,
            "next_phase": "inventory"
        }
    
    async def _execute_inventory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute inventory phase"""
        flow_id = data.get("flow_id")
        
        await self.flow_repo.update_phase_completion(
            flow_id=flow_id,
            phase="inventory",
            data={"assets_classified": True},
            completed=True
        )
        
        return {
            "status": "completed",
            "phase": "inventory",
            "message": "Inventory phase completed",
            "next_phase": "dependencies"
        }
    
    async def _execute_dependencies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute dependencies phase"""
        flow_id = data.get("flow_id")
        
        await self.flow_repo.update_phase_completion(
            flow_id=flow_id,
            phase="dependencies",
            data={"dependencies_analyzed": True},
            completed=True
        )
        
        return {
            "status": "completed",
            "phase": "dependencies",
            "message": "Dependencies phase completed",
            "next_phase": "tech_debt"
        }
    
    async def _execute_tech_debt(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tech debt phase"""
        flow_id = data.get("flow_id")
        
        await self.flow_repo.update_phase_completion(
            flow_id=flow_id,
            phase="tech_debt",
            data={"tech_debt_analyzed": True},
            completed=True
        )
        
        return {
            "status": "completed",
            "phase": "tech_debt",
            "message": "Tech debt phase completed",
            "next_phase": None
        }