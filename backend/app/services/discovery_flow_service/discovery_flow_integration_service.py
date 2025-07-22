"""
Discovery flow integration service that orchestrates CrewAI integration.
Provides backward compatibility with the original DiscoveryFlowIntegrationService.
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.discovery_flow import DiscoveryFlow

from .discovery_flow_service import DiscoveryFlowService
from .integrations.crewai_integration import CrewAIIntegrationService

logger = logging.getLogger(__name__)


class DiscoveryFlowIntegrationService:
    """
    Integration service for bridging CrewAI flows with new database architecture.
    Handles the transition from existing unified flow to new tables.
    
    This class orchestrates the CrewAI integration component to provide the same interface
    as the original monolithic DiscoveryFlowIntegrationService.
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        
        # Initialize main discovery service and CrewAI integration
        self.discovery_service = DiscoveryFlowService(db, context)
        self.crewai_integration = CrewAIIntegrationService(db, context)
    
    async def create_flow_from_crewai(
        self,
        crewai_flow_id: str,
        crewai_state: Dict[str, Any],
        raw_data: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None
    ) -> DiscoveryFlow:
        """
        Create discovery flow from CrewAI flow initialization.
        Bridges CrewAI flow state with new database architecture.
        """
        return await self.crewai_integration.create_flow_from_crewai(
            crewai_flow_id=crewai_flow_id,
            crewai_state=crewai_state,
            raw_data=raw_data,
            metadata=metadata
        )
    
    async def sync_crewai_state(
        self,
        flow_id: str,
        crewai_state: Dict[str, Any],
        phase: str = None
    ) -> DiscoveryFlow:
        """
        Sync CrewAI flow state with discovery flow database.
        Maintains hybrid persistence as described in the implementation plan.
        """
        return await self.crewai_integration.sync_crewai_state(
            flow_id=flow_id,
            crewai_state=crewai_state,
            phase=phase
        )
    
    # Enhanced methods using modular integration component
    
    async def export_flow_to_crewai(self, flow_id: str) -> Dict[str, Any]:
        """
        Export discovery flow data back to CrewAI format.
        Useful for CrewAI flow resumption and state reconstruction.
        """
        return await self.crewai_integration.export_flow_to_crewai(flow_id)
    
    async def validate_crewai_state_sync(
        self,
        flow_id: str,
        crewai_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate that CrewAI state is properly synced with discovery flow database.
        Returns validation report with any discrepancies.
        """
        return await self.crewai_integration.validate_crewai_state_sync(
            flow_id=flow_id,
            crewai_state=crewai_state
        )
    
    async def synchronize_with_crewai_flow(
        self,
        flow_id: str,
        crewai_flow_state: Dict[str, Any],
        force_sync: bool = False
    ) -> Dict[str, Any]:
        """
        Perform comprehensive synchronization with CrewAI flow state.
        """
        try:
            logger.info(f"🔄 Synchronizing with CrewAI flow: {flow_id}")
            
            # Validate current sync state
            validation_result = await self.validate_crewai_state_sync(flow_id, crewai_flow_state)
            
            if validation_result["is_synced"] and not force_sync:
                logger.info(f"✅ Flow already synchronized: {flow_id}")
                return {
                    "status": "already_synced",
                    "validation_result": validation_result,
                    "actions_taken": []
                }
            
            actions_taken = []
            
            # Sync the state
            updated_flow = await self.sync_crewai_state(
                flow_id=flow_id,
                crewai_state=crewai_flow_state
            )
            actions_taken.append("state_synchronized")
            
            # Re-validate after sync
            post_sync_validation = await self.validate_crewai_state_sync(flow_id, crewai_flow_state)
            
            sync_result = {
                "status": "synchronized",
                "flow_id": flow_id,
                "pre_sync_validation": validation_result,
                "post_sync_validation": post_sync_validation,
                "actions_taken": actions_taken,
                "improvement": {
                    "discrepancies_resolved": len(validation_result["discrepancies"]) - len(post_sync_validation["discrepancies"]),
                    "sync_quality_improved": post_sync_validation["sync_quality"] != validation_result["sync_quality"]
                }
            }
            
            logger.info(f"✅ CrewAI synchronization completed: {flow_id}")
            return sync_result
            
        except Exception as e:
            logger.error(f"❌ Failed to synchronize with CrewAI flow {flow_id}: {e}")
            raise
    
    async def get_crewai_integration_status(self, flow_id: str) -> Dict[str, Any]:
        """
        Get comprehensive CrewAI integration status for a flow.
        """
        try:
            logger.info(f"📊 Getting CrewAI integration status: {flow_id}")
            
            # Get flow
            flow = await self.discovery_service.get_flow_by_id(flow_id)
            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")
            
            # Export to CrewAI format to check data completeness
            crewai_export = await self.export_flow_to_crewai(flow_id)
            
            # Analyze integration status
            has_crewai_state = bool(flow.crewai_state_data)
            has_crew_status = bool(flow.crewai_state_data and flow.crewai_state_data.get("crew_status"))
            has_agent_insights = bool(flow.crewai_state_data and flow.crewai_state_data.get("agent_insights"))
            
            integration_status = {
                "flow_id": flow_id,
                "integration_level": "full" if all([has_crewai_state, has_crew_status, has_agent_insights]) else (
                    "partial" if has_crewai_state else "minimal"
                ),
                "features": {
                    "crewai_state_stored": has_crewai_state,
                    "crew_status_available": has_crew_status,
                    "agent_insights_available": has_agent_insights,
                    "exportable_to_crewai": bool(crewai_export),
                    "data_import_linked": bool(flow.data_import_id)
                },
                "data_completeness": {
                    "raw_data_available": bool(flow.raw_data),
                    "metadata_available": bool(flow.metadata),
                    "phase_data_available": any([
                        getattr(flow, f"{phase}_data", None) for phase in 
                        ["data_import", "attribute_mapping", "data_cleansing", "inventory", "dependencies", "tech_debt"]
                    ])
                },
                "last_sync": flow.updated_at.isoformat() if flow.updated_at else None,
                "recommendations": self._generate_integration_recommendations(flow, has_crewai_state, has_crew_status)
            }
            
            logger.info(f"✅ CrewAI integration status retrieved: {flow_id}")
            return integration_status
            
        except Exception as e:
            logger.error(f"❌ Failed to get CrewAI integration status for {flow_id}: {e}")
            raise
    
    def _generate_integration_recommendations(
        self,
        flow: DiscoveryFlow,
        has_crewai_state: bool,
        has_crew_status: bool
    ) -> List[str]:
        """Generate recommendations for improving CrewAI integration."""
        
        recommendations = []
        
        if not has_crewai_state:
            recommendations.append("Initialize CrewAI state synchronization")
        
        if not has_crew_status:
            recommendations.append("Capture crew status information for better tracking")
        
        if not flow.crewai_state_data or not flow.crewai_state_data.get("agent_insights"):
            recommendations.append("Enable agent insights collection for enhanced analysis")
        
        if flow.progress_percentage and flow.progress_percentage < 50:
            recommendations.append("Continue flow execution to capture more phase data")
        
        if not flow.data_import_id:
            recommendations.append("Link flow to data import for full traceability")
        
        return recommendations