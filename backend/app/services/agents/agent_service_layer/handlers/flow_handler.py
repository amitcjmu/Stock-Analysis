"""
Flow handler for agent service layer flow management operations.
"""

import logging
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.context import RequestContext
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.api.v1.discovery_handlers.flow_management import FlowManagementHandler

logger = logging.getLogger(__name__)


class FlowHandler:
    """Handles flow management operations for the agent service layer."""
    
    def __init__(self, context: RequestContext):
        self.context = context
    
    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get flow status using direct repository access"""
        async with AsyncSessionLocal() as db:
            try:
                # Direct repository access - no HTTP, no auth needed
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                # Get real flow data
                flow = await flow_repo.get_by_flow_id(flow_id)
                
                if not flow:
                    return {
                        "status": "not_found",
                        "flow_exists": False,
                        "message": "Flow not found in database"
                    }
                
                # Get active flows to provide context
                active_flows = await flow_repo.get_active_flows()
                
                return {
                    "status": "success",
                    "flow_exists": True,
                    "flow": {
                        "flow_id": str(flow.flow_id),
                        "status": flow.status,
                        "current_phase": flow.get_current_phase(),
                        "next_phase": flow.get_next_phase(),
                        "progress": flow.progress_percentage,
                        "phases_completed": {
                            "data_import": flow.data_import_completed,
                            "attribute_mapping": flow.attribute_mapping_completed,
                            "data_cleansing": flow.data_cleansing_completed,
                            "inventory": flow.inventory_completed,
                            "dependencies": flow.dependencies_completed,
                            "tech_debt": flow.tech_debt_completed
                        }
                    },
                    "active_flows_count": len(active_flows),
                    "has_incomplete_flows": any(not f.is_complete() for f in active_flows)
                }
                
            except Exception as e:
                logger.error(f"Database error in get_flow_status: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "flow_exists": False
                }
    
    async def get_navigation_guidance(self, flow_id: str, current_phase: str) -> Dict[str, Any]:
        """Get navigation guidance using flow management handler"""
        async with AsyncSessionLocal() as db:
            try:
                handler = FlowManagementHandler(db, self.context)
                
                # Direct service call - no HTTP needed
                flow_status = await handler.get_flow_status(flow_id)
                
                if not flow_status or flow_status.get("status") != "success":
                    return {
                        "status": "flow_not_found",
                        "guidance": [],
                        "message": "Cannot provide guidance for non-existent flow"
                    }
                
                flow_data = flow_status.get("flow", {})
                phases_completed = flow_data.get("phases_completed", {})
                
                # Generate contextual guidance
                guidance = []
                
                # Check what's been completed and suggest next steps
                if not phases_completed.get("data_import"):
                    guidance.append({
                        "action": "complete_data_import",
                        "description": "Complete data import phase",
                        "priority": "high",
                        "next_url": f"/discovery/{flow_id}/data-import"
                    })
                elif not phases_completed.get("attribute_mapping"):
                    guidance.append({
                        "action": "complete_attribute_mapping",
                        "description": "Complete attribute mapping phase",
                        "priority": "high",
                        "next_url": f"/discovery/{flow_id}/attribute-mapping"
                    })
                elif not phases_completed.get("data_cleansing"):
                    guidance.append({
                        "action": "complete_data_cleansing",
                        "description": "Complete data cleansing phase",
                        "priority": "high",
                        "next_url": f"/discovery/{flow_id}/data-cleansing"
                    })
                elif not phases_completed.get("inventory"):
                    guidance.append({
                        "action": "complete_inventory",
                        "description": "Complete asset inventory phase",
                        "priority": "high",
                        "next_url": f"/discovery/{flow_id}/inventory"
                    })
                elif not phases_completed.get("dependencies"):
                    guidance.append({
                        "action": "complete_dependencies",
                        "description": "Complete dependency analysis phase",
                        "priority": "medium",
                        "next_url": f"/discovery/{flow_id}/dependencies"
                    })
                elif not phases_completed.get("tech_debt"):
                    guidance.append({
                        "action": "complete_tech_debt",
                        "description": "Complete technical debt analysis phase",
                        "priority": "medium",
                        "next_url": f"/discovery/{flow_id}/tech-debt"
                    })
                else:
                    guidance.append({
                        "action": "flow_complete",
                        "description": "All phases complete - ready for assessment",
                        "priority": "low",
                        "next_url": f"/assessment/{flow_id}/summary"
                    })
                
                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "current_phase": current_phase,
                    "guidance": guidance,
                    "flow_status": flow_data
                }
                
            except Exception as e:
                logger.error(f"Error in get_navigation_guidance: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "guidance": []
                }
    
    async def validate_phase_completion(self, flow_id: str, phase: str) -> Dict[str, Any]:
        """Validate if a phase is properly completed"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return {
                        "status": "error",
                        "error": "Flow not found",
                        "is_complete": False
                    }
                
                # Check phase completion based on phase name
                phase_completion_map = {
                    "data_import": flow.data_import_completed,
                    "attribute_mapping": flow.attribute_mapping_completed,
                    "data_cleansing": flow.data_cleansing_completed,
                    "inventory": flow.inventory_completed,
                    "dependencies": flow.dependencies_completed,
                    "tech_debt": flow.tech_debt_completed
                }
                
                is_complete = phase_completion_map.get(phase, False)
                
                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "phase": phase,
                    "is_complete": is_complete,
                    "completion_details": {
                        "progress_percentage": flow.progress_percentage,
                        "last_updated": flow.updated_at.isoformat() if flow.updated_at else None
                    }
                }
                
            except Exception as e:
                logger.error(f"Error validating phase completion: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "is_complete": False
                }
    
    async def get_active_flows(self) -> List[Dict[str, Any]]:
        """Get all active discovery flows"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                flows = await flow_repo.get_active_flows()
                
                flow_list = []
                for flow in flows:
                    flow_data = {
                        "flow_id": str(flow.flow_id),
                        "status": flow.status,
                        "current_phase": flow.get_current_phase(),
                        "next_phase": flow.get_next_phase(),
                        "progress": flow.progress_percentage,
                        "is_complete": flow.is_complete(),
                        "created_at": flow.created_at.isoformat() if flow.created_at else None,
                        "updated_at": flow.updated_at.isoformat() if flow.updated_at else None
                    }
                    flow_list.append(flow_data)
                
                return flow_list
                
            except Exception as e:
                logger.error(f"Database error in get_active_flows: {e}")
                raise
    
    async def validate_phase_transition(self, flow_id: str, from_phase: str, to_phase: str) -> Dict[str, Any]:
        """Validate if phase transition is allowed"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return {
                        "status": "error",
                        "error": "Flow not found",
                        "transition_allowed": False
                    }
                
                # Define phase order and dependencies
                phase_order = [
                    "data_import",
                    "attribute_mapping", 
                    "data_cleansing",
                    "inventory",
                    "dependencies",
                    "tech_debt"
                ]
                
                # Check if transition is valid based on phase order
                try:
                    from_index = phase_order.index(from_phase)
                    to_index = phase_order.index(to_phase)
                except ValueError:
                    return {
                        "status": "error",
                        "error": "Invalid phase names",
                        "transition_allowed": False
                    }
                
                # Only allow forward transitions and completion transitions
                transition_allowed = to_index >= from_index
                
                # Check if prerequisite phases are complete
                prerequisite_phases = phase_order[:to_index]
                phase_completion_map = {
                    "data_import": flow.data_import_completed,
                    "attribute_mapping": flow.attribute_mapping_completed,
                    "data_cleansing": flow.data_cleansing_completed,
                    "inventory": flow.inventory_completed,
                    "dependencies": flow.dependencies_completed,
                    "tech_debt": flow.tech_debt_completed
                }
                
                incomplete_prerequisites = [
                    phase for phase in prerequisite_phases 
                    if not phase_completion_map.get(phase, False)
                ]
                
                if incomplete_prerequisites:
                    transition_allowed = False
                
                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "from_phase": from_phase,
                    "to_phase": to_phase,
                    "transition_allowed": transition_allowed,
                    "incomplete_prerequisites": incomplete_prerequisites,
                    "validation_details": {
                        "phase_order_valid": to_index >= from_index,
                        "prerequisites_complete": len(incomplete_prerequisites) == 0
                    }
                }
                
            except Exception as e:
                logger.error(f"Error validating phase transition: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "transition_allowed": False
                }