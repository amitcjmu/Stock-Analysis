"""
Flow handler for agent service layer flow management operations.
"""

import logging
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.context import RequestContext
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logger = logging.getLogger(__name__)


class FlowHandler:
    """Handles flow management operations for the agent service layer."""
    
    def __init__(self, context: RequestContext):
        self.context = context
    
    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """
        Get flow status prioritizing child flow operational data per ADR-012
        
        ADR-012: Use child flow status for operational decisions, master flow for lifecycle only
        """
        async with AsyncSessionLocal() as db:
            try:
                # ADR-012: First determine flow type from master flow
                from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
                master_repo = CrewAIFlowStateExtensionsRepository(db, self.context.client_account_id, self.context.engagement_id, self.context.user_id)
                master_flow = await master_repo.get_by_flow_id(flow_id)
                
                if not master_flow:
                    logger.info(f"Master flow not found: {flow_id}")
                    return {"status": "not_found", "flow_exists": False}
                
                # ADR-012: Get operational status from appropriate child flow
                if master_flow.flow_type == "discovery":
                    # Use discovery flow repository for operational status
                    flow_repo = DiscoveryFlowRepository(
                        db=db,
                        client_account_id=str(self.context.client_account_id),
                        engagement_id=str(self.context.engagement_id)
                    )
                    
                    # Get real flow data from discovery flows table (child flow)
                    flow = await flow_repo.get_by_flow_id(flow_id)
                    
                    if flow:
                        logger.info(f"Found discovery flow in legacy table: {flow_id}")
                        
                        # CRITICAL FIX: Check for actual data via data_import_id 
                        actual_data_status = await self._check_actual_data_via_import_id(flow)
                        
                        # Merge the database completion flags with actual data detection
                        actual_phases = {
                            "data_import": actual_data_status.get("has_import_data", flow.data_import_completed),
                            "field_mapping": actual_data_status.get("has_field_mappings", flow.field_mapping_completed), 
                            "data_cleansing": flow.data_cleansing_completed,
                            "asset_inventory": flow.asset_inventory_completed,
                            "dependency_analysis": flow.dependency_analysis_completed,
                            "tech_debt_assessment": flow.tech_debt_assessment_completed
                        }
                        
                        # Determine current phase based on actual data
                        current_phase = self._determine_actual_current_phase(actual_phases, flow)
                        next_phase = self._determine_next_phase(actual_phases)
                        
                        return {
                            "status": "success",
                            "flow_exists": True,
                            "flow": {
                                "flow_id": str(flow.flow_id),
                                "flow_type": "discovery",
                                "status": flow.status,
                                "current_phase": current_phase,
                                "next_phase": next_phase,
                                "progress": flow.progress_percentage,
                                "phases_completed": actual_phases,
                                "raw_data_count": actual_data_status.get("field_mapping_count", 0),
                                "field_mapping_count": actual_data_status.get("field_mapping_count", 0),
                                "data_import_id": str(flow.data_import_id) if flow.data_import_id else None
                            },
                            "flow_type": "discovery"
                        }
                    else:
                        logger.info(f"Discovery flow not found in child repository: {flow_id}")
                        return {
                            "status": "not_found",
                            "flow_exists": False,
                            "message": "Discovery flow not found in child repository"
                        }
                        
                elif master_flow.flow_type == "assessment":
                    # TODO: Add assessment flow repository support
                    logger.warning(f"[ADR-012] Assessment flow type not yet fully supported: {flow_id}")
                    return {
                        "status": "not_implemented", 
                        "flow_exists": True,
                        "message": "Assessment flows not yet supported in child flow status"
                    }
                else:
                    # Other flow types - return master flow data for now
                    logger.warning(f"[ADR-012] Unsupported flow type, using master flow: {master_flow.flow_type}")
                    return {
                        "status": "success",
                        "flow_exists": True,
                        "flow": {
                            "flow_id": flow_id,
                            "flow_type": master_flow.flow_type,
                            "status": master_flow.flow_status,  # Using master status for unsupported types
                            "current_phase": master_flow.current_phase,
                            "message": f"Using master flow status for unsupported type: {master_flow.flow_type}"
                        },
                        "flow_type": master_flow.flow_type
                    }
                        
            except Exception as e:
                logger.error(f"[ADR-012] Error getting flow status: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "flow_exists": False
                }
    
    async def get_navigation_guidance(self, flow_id: str, current_phase: str) -> Dict[str, Any]:
        """Get navigation guidance using flow repository"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                # Direct repository call - no HTTP needed
                flow = await flow_repo.get_by_flow_id(flow_id)
                
                if not flow:
                    return {
                        "status": "flow_not_found",
                        "guidance": [],
                        "message": "Cannot provide guidance for non-existent flow"
                    }
                
                # Extract phases completed from flow model
                phases_completed = {
                    "data_import": flow.data_import_completed,
                    "field_mapping": flow.field_mapping_completed,
                    "data_cleansing": flow.data_cleansing_completed,
                    "asset_inventory": flow.asset_inventory_completed,
                    "dependency_analysis": flow.dependency_analysis_completed,
                    "tech_debt_assessment": flow.tech_debt_assessment_completed
                }
                
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
                elif not phases_completed.get("field_mapping"):
                    guidance.append({
                        "action": "complete_field_mapping",
                        "description": "Complete field mapping phase",
                        "priority": "high",
                        "next_url": f"/discovery/{flow_id}/field-mapping"
                    })
                elif not phases_completed.get("data_cleansing"):
                    guidance.append({
                        "action": "complete_data_cleansing",
                        "description": "Complete data cleansing phase",
                        "priority": "high",
                        "next_url": f"/discovery/{flow_id}/data-cleansing"
                    })
                elif not phases_completed.get("asset_inventory"):
                    guidance.append({
                        "action": "complete_asset_inventory",
                        "description": "Complete asset inventory phase",
                        "priority": "high",
                        "next_url": f"/discovery/{flow_id}/asset-inventory"
                    })
                elif not phases_completed.get("dependency_analysis"):
                    guidance.append({
                        "action": "complete_dependency_analysis",
                        "description": "Complete dependency analysis phase",
                        "priority": "medium",
                        "next_url": f"/discovery/{flow_id}/dependency-analysis"
                    })
                elif not phases_completed.get("tech_debt_assessment"):
                    guidance.append({
                        "action": "complete_tech_debt_assessment",
                        "description": "Complete technical debt assessment phase",
                        "priority": "medium",
                        "next_url": f"/discovery/{flow_id}/tech-debt-assessment"
                    })
                else:
                    guidance.append({
                        "action": "flow_complete",
                        "description": "All phases complete - ready for assessment",
                        "priority": "low",
                        "next_url": f"/assessment/{flow_id}/summary"
                    })
                
                flow_data = {
                    "flow_id": str(flow.flow_id),
                    "status": flow.status,
                    "current_phase": getattr(flow, 'current_phase', 'data_import'),
                    "next_phase": "field_mapping" if not flow.field_mapping_completed else "data_cleansing",
                    "progress": flow.progress_percentage,
                    "phases_completed": phases_completed
                }
                
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
                    "field_mapping": flow.field_mapping_completed,
                    "data_cleansing": flow.data_cleansing_completed,
                    "asset_inventory": flow.asset_inventory_completed,
                    "dependency_analysis": flow.dependency_analysis_completed,
                    "tech_debt_assessment": flow.tech_debt_assessment_completed
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
                    "field_mapping", 
                    "data_cleansing",
                    "asset_inventory",
                    "dependency_analysis",
                    "tech_debt_assessment"
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
                    "field_mapping": flow.field_mapping_completed,
                    "data_cleansing": flow.data_cleansing_completed,
                    "asset_inventory": flow.asset_inventory_completed,
                    "dependency_analysis": flow.dependency_analysis_completed,
                    "tech_debt_assessment": flow.tech_debt_assessment_completed
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
    
    async def _check_actual_data_via_import_id(self, flow) -> dict:
        """Check for actual data via data_import_id - CRITICAL ARCHITECTURE FIX"""
        try:
            if not flow.data_import_id:
                return {"has_import_data": False, "has_field_mappings": False, "field_mapping_count": 0}
            
            from sqlalchemy import text
            async with AsyncSessionLocal() as db:
                # Check for field mappings (proves data was imported and mapped)
                result = await db.execute(text('''
                    SELECT COUNT(*) as mapping_count,
                           COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count
                    FROM import_field_mappings 
                    WHERE data_import_id = :data_import_id
                '''), {'data_import_id': flow.data_import_id})
                
                row = result.fetchone()
                mapping_count = row.mapping_count if row else 0
                approved_count = row.approved_count if row else 0
                
                # Check for raw imported data
                data_result = await db.execute(text('''
                    SELECT COUNT(*) as data_count
                    FROM data_imports 
                    WHERE id = :data_import_id AND status IN ('completed', 'processing', 'discovery_initiated')
                '''), {'data_import_id': flow.data_import_id})
                
                data_row = data_result.fetchone()
                has_import_data = (data_row.data_count > 0) if data_row else False
                
                logger.info(f"Data import check for {flow.data_import_id}: "
                          f"mappings={mapping_count}, approved={approved_count}, has_data={has_import_data}")
                
                return {
                    "has_import_data": has_import_data,
                    "has_field_mappings": mapping_count > 0,
                    "field_mapping_count": mapping_count,
                    "approved_mappings": approved_count,
                    "data_import_exists": has_import_data
                }
                
        except Exception as e:
            logger.error(f"Error checking actual data via import_id: {e}")
            return {"has_import_data": False, "has_field_mappings": False, "field_mapping_count": 0}
    
    def _determine_actual_current_phase(self, actual_phases: dict, flow) -> str:
        """Determine current phase based on actual data detection"""
        try:
            # Phase order for discovery flows
            phase_order = [
                "data_import",
                "field_mapping", 
                "data_cleansing",
                "asset_inventory",
                "dependency_analysis",
                "tech_debt_assessment"
            ]
            
            # Find the first incomplete phase
            for phase in phase_order:
                if not actual_phases.get(phase, False):
                    return phase
            
            # All phases complete
            return "completed"
            
        except Exception as e:
            logger.error(f"Error determining current phase: {e}")
            return "data_import"
    
    def _determine_next_phase(self, actual_phases: dict) -> str:
        """Determine next phase based on actual completion status"""
        try:
            # Phase progression mapping
            phase_progression = {
                "data_import": "field_mapping",
                "field_mapping": "data_cleansing", 
                "data_cleansing": "asset_inventory",
                "asset_inventory": "dependency_analysis",
                "dependency_analysis": "tech_debt_assessment",
                "tech_debt_assessment": "completed"
            }
            
            # Find current phase
            current_phase = self._determine_actual_current_phase(actual_phases, None)
            
            # Return next phase
            return phase_progression.get(current_phase, "completed")
            
        except Exception as e:
            logger.error(f"Error determining next phase: {e}")
            return "field_mapping"