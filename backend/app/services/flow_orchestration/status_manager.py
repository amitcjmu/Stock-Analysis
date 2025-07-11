"""
Flow Status Manager

Handles status retrieval, flow information aggregation, and status calculation logic.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.context import RequestContext
from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
from app.services.flow_type_registry import FlowTypeRegistry
from app.services.agent_ui_bridge import AgentUIBridge

logger = get_logger(__name__)


class FlowStatusManager:
    """
    Manages flow status retrieval, aggregation, and calculation with comprehensive flow information.
    """
    
    def __init__(self, 
                 db: AsyncSession,
                 context: RequestContext,
                 master_repo: CrewAIFlowStateExtensionsRepository,
                 flow_registry: FlowTypeRegistry):
        """
        Initialize the Flow Status Manager
        
        Args:
            db: Database session
            context: Request context
            master_repo: Repository for master flow operations
            flow_registry: Registry for flow type configurations
        """
        self.db = db
        self.context = context
        self.master_repo = master_repo
        self.flow_registry = flow_registry
        
        logger.info(f"✅ Flow Status Manager initialized for client {context.client_account_id}")
    
    async def get_flow_status(
        self,
        flow_id: str,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive flow status
        
        Args:
            flow_id: Flow identifier
            include_details: Whether to include detailed information
            
        Returns:
            Flow status information
            
        Raises:
            ValueError: If flow not found
        """
        try:
            # Get flow
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                raise ValueError(f"Flow not found: {flow_id}")
            
            # Get flow configuration
            flow_config = self.flow_registry.get_flow_config(master_flow.flow_type)
            
            # Build basic status
            status = {
                "flow_id": flow_id,
                "flow_type": master_flow.flow_type,
                "flow_name": master_flow.flow_name,
                "status": master_flow.flow_status,
                "created_at": master_flow.created_at.isoformat(),
                "updated_at": master_flow.updated_at.isoformat(),
                "created_by": getattr(master_flow, 'created_by', self.context.user_id),
                "current_phase": getattr(master_flow, 'current_phase', None),
                "progress_percentage": getattr(master_flow, 'progress_percentage', 0.0),
                "configuration": master_flow.flow_configuration if hasattr(master_flow, 'flow_configuration') and master_flow.flow_configuration else {},
                "metadata": {}
            }
            
            if include_details:
                # Add detailed information
                detailed_status = await self._get_detailed_status(master_flow, flow_config)
                status.update(detailed_status)
            
            return status
            
        except ValueError as e:
            # Flow not found - this is a legitimate 404 case
            logger.warning(f"Flow not found: {flow_id}")
            raise e
        except Exception as e:
            logger.error(f"Failed to get flow status for {flow_id}: {e}")
            raise RuntimeError(f"Failed to get flow status: {str(e)}")
    
    async def _get_detailed_status(
        self,
        master_flow,
        flow_config
    ) -> Dict[str, Any]:
        """Get detailed status information for a flow"""
        detailed_status = {}
        
        # Get agent insights for this flow
        logger.info(f"🔍 Getting agent insights for flow {master_flow.flow_id} (type: {master_flow.flow_type})")
        agent_insights = await self._get_flow_agent_insights(master_flow.flow_id, master_flow.flow_type)
        logger.info(f"🔍 Retrieved {len(agent_insights)} agent insights for flow {master_flow.flow_id}")
        
        # Get field mappings for discovery flows
        field_mappings = []
        if master_flow.flow_type == "discovery":
            field_mappings = await self._get_discovery_field_mappings(master_flow)
        
        # Get phase information
        phase_info = self._get_phase_information(master_flow, flow_config)
        
        # Get performance summary
        performance_summary = self._get_performance_summary(master_flow)
        
        # Get collaboration log
        collaboration_log = master_flow.agent_collaboration_log[-10:] if master_flow.agent_collaboration_log else []
        
        # Get state data
        state_data = master_flow.flow_persistence_data if master_flow.flow_persistence_data else {}
        
        detailed_status = {
            "configuration": master_flow.flow_configuration,
            "phases": phase_info,
            "performance": performance_summary,
            "collaboration_log": collaboration_log,
            "state_data": state_data,
            "agent_insights": agent_insights,
            "field_mappings": field_mappings
        }
        
        return detailed_status
    
    async def _get_flow_agent_insights(self, flow_id: str, flow_type: str) -> List[Dict[str, Any]]:
        """
        Get agent insights for a specific flow from multiple sources.
        
        Args:
            flow_id: Flow identifier
            flow_type: Type of flow (discovery, assessment, etc.)
            
        Returns:
            List of agent insights
        """
        try:
            insights = []
            logger.info(f"🔍 _get_flow_agent_insights called for flow_id={flow_id}, flow_type={flow_type}")
            
            # Try to get insights from agent_ui_bridge service
            try:
                bridge = AgentUIBridge(data_dir="backend/data")
                
                # Get insights by page context based on flow type
                page_context = "discovery" if flow_type == "discovery" else "assessment" if flow_type == "assessment" else "general"
                logger.info(f"🔍 Searching for insights with page_context: {page_context}")
                bridge_insights = bridge.get_insights_for_page(page_context)
                
                # Also get flow-specific insights
                flow_page_context = f"flow_{flow_id}"
                logger.info(f"🔍 Searching for flow-specific insights with page_context: {flow_page_context}")
                flow_insights = bridge.get_insights_for_page(flow_page_context)
                
                if bridge_insights:
                    logger.info(f"🔗 Found {len(bridge_insights)} insights from agent_ui_bridge for {flow_type} flow")
                    # Filter insights by flow_id if available, or include those with null flow_id for the flow type
                    flow_specific_insights = [
                        insight for insight in bridge_insights 
                        if insight.get("flow_id") == flow_id or 
                           (insight.get("flow_id") is None and insight.get("page") == page_context)
                    ]
                    insights.extend(flow_specific_insights)
                    logger.info(f"🔍 Filtered {len(flow_specific_insights)} flow-specific insights for flow {flow_id} from {len(bridge_insights)} total insights")
                    if len(flow_specific_insights) > 0:
                        logger.info(f"🔍 Sample insight: {flow_specific_insights[0]}")
                else:
                    logger.info(f"🔍 No bridge insights found for page_context: {page_context}")
                
                if flow_insights:
                    logger.info(f"🔗 Found {len(flow_insights)} flow-specific insights for flow {flow_id}")
                    insights.extend(flow_insights)
                    if len(flow_insights) > 0:
                        logger.info(f"🔍 Sample flow insight: {flow_insights[0]}")
                else:
                    logger.info(f"🔍 No flow-specific insights found for page_context: {flow_page_context}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Could not get insights from agent_ui_bridge: {e}")
            
            # Get insights from flow persistence data if available
            try:
                master_flow = await self.master_repo.get_by_flow_id(flow_id)
                if master_flow and master_flow.flow_persistence_data:
                    flow_data = master_flow.flow_persistence_data
                    
                    # Check if there are agent insights stored in the flow data
                    flow_insights_found = []
                    
                    # Look for agent insights in multiple possible locations
                    if "agent_insights" in flow_data:
                        flow_insights = flow_data["agent_insights"]
                        if isinstance(flow_insights, list):
                            flow_insights_found.extend(flow_insights)
                            logger.info(f"📊 Found {len(flow_insights)} insights from flow_data.agent_insights")
                    
                    # Check for insights in nested structures (like crewai_state_data)
                    if "crewai_state_data" in flow_data and isinstance(flow_data["crewai_state_data"], dict):
                        crewai_data = flow_data["crewai_state_data"]
                        if "agent_insights" in crewai_data and isinstance(crewai_data["agent_insights"], list):
                            nested_insights = crewai_data["agent_insights"]
                            # Transform nested insights to standard format
                            for insight in nested_insights:
                                if isinstance(insight, dict):
                                    # Convert from nested format to standard format
                                    standardized_insight = {
                                        "id": f"nested-{flow_id}-{len(flow_insights_found)}",
                                        "agent_id": insight.get("agent", "unknown").lower().replace(" ", "_"),
                                        "agent_name": insight.get("agent", "Unknown Agent"),
                                        "insight_type": "agent_analysis",
                                        "title": insight.get("insight", "")[:50] + "..." if len(insight.get("insight", "")) > 50 else insight.get("insight", ""),
                                        "description": insight.get("insight", "No description available"),
                                        "confidence": insight.get("confidence", 0.5),
                                        "supporting_data": {
                                            "flow_id": flow_id,
                                            "timestamp": insight.get("timestamp"),
                                            "original_data": insight
                                        },
                                        "actionable": True,
                                        "page": f"flow_{flow_id}",
                                        "created_at": insight.get("timestamp"),
                                        "flow_id": flow_id
                                    }
                                    flow_insights_found.append(standardized_insight)
                            logger.info(f"📊 Found {len(nested_insights)} insights from crewai_state_data.agent_insights")
                    
                    # Add all found insights
                    if flow_insights_found:
                        insights.extend(flow_insights_found)
                        logger.info(f"📊 Total {len(flow_insights_found)} insights extracted from flow persistence data")
                    
                    # Generate insights from flow state
                    status_insight = self._generate_flow_status_insight(flow_id, flow_type, master_flow, flow_data)
                    if status_insight:
                        insights.append(status_insight)
                        
            except Exception as e:
                logger.warning(f"⚠️ Could not get insights from flow persistence data: {e}")
            
            # If no insights found, provide a default message
            if not insights:
                insights.append(self._generate_default_insight(flow_id, flow_type))
            
            logger.info(f"✅ Returning {len(insights)} agent insights for flow {flow_id}")
            return insights
            
        except Exception as e:
            logger.error(f"❌ Error getting agent insights for flow {flow_id}: {e}")
            return []
    
    def _generate_flow_status_insight(
        self,
        flow_id: str,
        flow_type: str,
        master_flow,
        flow_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate an insight from flow status"""
        try:
            # Check multiple locations for current phase and progress
            current_phase = flow_data.get("current_phase")
            progress_percentage = flow_data.get("progress_percentage", 0.0)
            
            # Also check nested crewai_state_data
            if not current_phase and "crewai_state_data" in flow_data:
                crewai_data = flow_data["crewai_state_data"]
                if isinstance(crewai_data, dict):
                    current_phase = crewai_data.get("current_phase")
                    if not progress_percentage:
                        progress_percentage = crewai_data.get("progress_percentage", 0.0)
            
            # Check phase_execution_times for phase information
            if not current_phase and master_flow.phase_execution_times:
                try:
                    phase_times = master_flow.phase_execution_times
                    if isinstance(phase_times, dict):
                        current_phase = phase_times.get("current_phase")
                        if not progress_percentage:
                            progress_percentage = phase_times.get("progress_percentage", 0.0)
                except Exception as e:
                    logger.debug(f"Could not extract phase from phase_execution_times: {e}")
            
            # Default if still not found
            current_phase = current_phase or "unknown"
            
            logger.info(f"🔍 Flow status insight: phase={current_phase}, progress={progress_percentage}, status={master_flow.flow_status}")
            
            if master_flow.flow_status:
                return {
                    "id": f"flow-status-{flow_id}",
                    "agent_id": "flow-orchestrator",
                    "agent_name": "Flow Orchestrator",
                    "insight_type": "flow_status",
                    "title": f"Flow Status: {master_flow.flow_status.title()}",
                    "description": f"Flow is currently in {current_phase} phase with {master_flow.flow_status} status",
                    "confidence": "high",
                    "supporting_data": {
                        "flow_id": flow_id,
                        "flow_type": flow_type,
                        "status": master_flow.flow_status,
                        "phase": current_phase,
                        "progress": progress_percentage
                    },
                    "actionable": master_flow.flow_status in ["paused", "error"],
                    "page": "discovery" if flow_type == "discovery" else "assessment",
                    "created_at": master_flow.updated_at.isoformat() if master_flow.updated_at else None
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Could not generate flow status insight: {e}")
            return None
    
    def _generate_default_insight(self, flow_id: str, flow_type: str) -> Dict[str, Any]:
        """Generate a default insight when no insights are found"""
        return {
            "id": f"no-insights-{flow_id}",
            "agent_id": "system-monitor",
            "agent_name": "System Monitor",
            "insight_type": "system_status",
            "title": "Flow Monitoring Active",
            "description": f"Flow {flow_id} is being monitored - agents will provide insights as they analyze your data",
            "confidence": "medium",
            "supporting_data": {"flow_id": flow_id, "flow_type": flow_type},
            "actionable": False,
            "page": "discovery" if flow_type == "discovery" else "assessment",
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _get_discovery_field_mappings(self, master_flow) -> List[Dict[str, Any]]:
        """Get field mappings for discovery flows"""
        try:
            # Get data_import_id from flow persistence data
            persistence_data = master_flow.flow_persistence_data or {}
            data_import_id = persistence_data.get('data_import_id')
            
            if data_import_id:
                from app.models.data_import.mapping import ImportFieldMapping
                from sqlalchemy import select
                
                logger.info(f"🔍 Loading field mappings for data_import_id: {data_import_id}")
                
                query = select(ImportFieldMapping).where(
                    ImportFieldMapping.data_import_id == data_import_id
                )
                result = await self.db.execute(query)
                mappings = result.scalars().all()
                
                # Convert to frontend format
                field_mappings = [
                    {
                        "id": str(mapping.id),
                        "source_field": mapping.source_field,
                        "target_field": mapping.target_field,
                        "status": mapping.status,
                        "confidence_score": mapping.confidence_score,
                        "match_type": mapping.match_type,
                        "suggested_by": mapping.suggested_by,
                        "approved_by": mapping.approved_by,
                        "approved_at": mapping.approved_at.isoformat() if mapping.approved_at else None,
                        "transformation_rules": mapping.transformation_rules,
                        "created_at": mapping.created_at.isoformat() if mapping.created_at else None,
                        "updated_at": mapping.updated_at.isoformat() if mapping.updated_at else None
                    }
                    for mapping in mappings
                ]
                
                logger.info(f"✅ Loaded {len(field_mappings)} field mappings for flow {master_flow.flow_id}")
                return field_mappings
            else:
                logger.warning(f"⚠️ No data_import_id found in flow persistence data for flow {master_flow.flow_id}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to load field mappings for flow {master_flow.flow_id}: {e}")
            return []
    
    def _get_phase_information(self, master_flow, flow_config) -> Dict[str, Any]:
        """Get phase information for a flow"""
        try:
            phase_info = {
                "total": len(flow_config.phases),
                "completed": len([
                    phase for phase in flow_config.phases
                    if master_flow.phase_execution_times.get(phase.name)
                ]),
                "execution_times": master_flow.phase_execution_times
            }
            
            return phase_info
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get phase information: {e}")
            return {
                "total": 0,
                "completed": 0,
                "execution_times": {}
            }
    
    def _get_performance_summary(self, master_flow) -> Dict[str, Any]:
        """Get performance summary for a flow"""
        try:
            return master_flow.get_performance_summary()
        except Exception as e:
            logger.warning(f"⚠️ Could not get performance summary: {e}")
            return {
                "total_execution_time": 0,
                "average_phase_time": 0,
                "phases_completed": 0
            }
    
    async def get_active_flows(
        self,
        flow_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get list of active flows
        
        Args:
            flow_type: Optional filter by flow type
            limit: Maximum number of flows to return
            
        Returns:
            List of active flows
        """
        try:
            if flow_type:
                # Get flows by specific type
                flows = await self.master_repo.get_flows_by_type(flow_type, limit)
            else:
                # Get all active flows
                flows = await self.master_repo.get_active_flows(limit)
            
            # Convert to dict format
            flow_list = []
            for flow in flows:
                flow_list.append({
                    "flow_id": str(flow.flow_id),
                    "flow_type": flow.flow_type,
                    "flow_name": flow.flow_name,
                    "status": flow.flow_status,
                    "created_at": flow.created_at.isoformat(),
                    "updated_at": flow.updated_at.isoformat(),
                    "created_by": getattr(flow, 'created_by', self.context.user_id),
                    "current_phase": getattr(flow, 'current_phase', None),
                    "progress_percentage": getattr(flow, 'progress_percentage', 0.0),
                    "configuration": flow.flow_configuration if hasattr(flow, 'flow_configuration') and flow.flow_configuration else {},
                    "metadata": {}
                })
            
            return flow_list
            
        except Exception as e:
            logger.error(f"Failed to get active flows: {e}")
            raise RuntimeError(f"Failed to get active flows: {str(e)}")
    
    async def list_flows_by_engagement(
        self,
        engagement_id: str,
        flow_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List flows for a specific engagement
        
        Args:
            engagement_id: The engagement ID to filter by
            flow_type: Optional filter by flow type
            limit: Maximum number of flows to return
            
        Returns:
            List of flows for the engagement
        """
        try:
            # Get flows for the engagement using the repository
            flows = await self.master_repo.get_flows_by_engagement(
                engagement_id=engagement_id,
                flow_type=flow_type,
                limit=limit
            )
            
            # Convert to dict format expected by user service
            flow_list = []
            for flow in flows:
                flow_dict = {
                    "id": str(flow.flow_id),  # User service expects 'id' not 'flow_id'
                    "flow_id": str(flow.flow_id),
                    "name": flow.flow_name or f"{flow.flow_type.title()} Flow",
                    "flow_type": flow.flow_type,
                    "status": flow.flow_status,
                    "created_at": flow.created_at.isoformat() if flow.created_at else None,
                    "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
                    "created_by": getattr(flow, 'created_by', self.context.user_id),
                    "current_phase": getattr(flow, 'current_phase', None),
                    "progress_percentage": getattr(flow, 'progress_percentage', 0.0),
                    "configuration": flow.flow_configuration if hasattr(flow, 'flow_configuration') and flow.flow_configuration else {},
                    "metadata": {}
                }
                flow_list.append(flow_dict)
            
            logger.info(f"Retrieved {len(flow_list)} flows for engagement {engagement_id}")
            return flow_list
            
        except Exception as e:
            logger.error(f"Failed to list flows by engagement {engagement_id}: {e}")
            # Return empty list instead of raising to prevent user context failures
            return []
    
    async def get_flow_summary(self, flow_id: str) -> Dict[str, Any]:
        """
        Get a summary of flow information
        
        Args:
            flow_id: Flow identifier
            
        Returns:
            Flow summary information
        """
        try:
            status = await self.get_flow_status(flow_id, include_details=False)
            
            # Add summary-specific information
            summary = {
                **status,
                "summary": {
                    "status_description": self._get_status_description(status["status"]),
                    "next_actions": self._get_next_actions(status),
                    "estimated_completion": self._estimate_completion(status),
                    "key_metrics": self._get_key_metrics(status)
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get flow summary for {flow_id}: {e}")
            raise RuntimeError(f"Failed to get flow summary: {str(e)}")
    
    def _get_status_description(self, status: str) -> str:
        """Get human-readable status description"""
        status_descriptions = {
            "initialized": "Flow has been created and is ready to start",
            "active": "Flow is currently active and processing",
            "processing": "Flow is actively processing data",
            "waiting_for_approval": "Flow is paused waiting for user approval",
            "paused": "Flow has been paused by user or system",
            "completed": "Flow has completed successfully",
            "failed": "Flow has failed and requires attention",
            "cancelled": "Flow has been cancelled by user"
        }
        
        return status_descriptions.get(status, f"Flow status: {status}")
    
    def _get_next_actions(self, status: Dict[str, Any]) -> List[str]:
        """Get next recommended actions based on flow status"""
        flow_status = status.get("status")
        actions = []
        
        if flow_status == "waiting_for_approval":
            actions.append("Review and approve pending field mappings")
        elif flow_status == "paused":
            actions.append("Resume flow execution")
        elif flow_status == "failed":
            actions.append("Review error logs and retry")
        elif flow_status == "processing":
            actions.append("Monitor flow progress")
        elif flow_status == "completed":
            actions.append("Review results and export data")
        
        return actions
    
    def _estimate_completion(self, status: Dict[str, Any]) -> Optional[str]:
        """Estimate completion time based on current progress"""
        progress = status.get("progress_percentage", 0)
        
        if progress >= 100:
            return "Completed"
        elif progress >= 80:
            return "~5-10 minutes"
        elif progress >= 50:
            return "~10-20 minutes"
        elif progress >= 20:
            return "~20-30 minutes"
        else:
            return "~30+ minutes"
    
    def _get_key_metrics(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """Get key metrics for flow status"""
        return {
            "progress_percentage": status.get("progress_percentage", 0),
            "current_phase": status.get("current_phase", "unknown"),
            "runtime_minutes": self._calculate_runtime_minutes(status),
            "status": status.get("status", "unknown")
        }
    
    def _calculate_runtime_minutes(self, status: Dict[str, Any]) -> float:
        """Calculate runtime in minutes"""
        try:
            created_at = datetime.fromisoformat(status["created_at"].replace("Z", "+00:00"))
            updated_at = datetime.fromisoformat(status["updated_at"].replace("Z", "+00:00"))
            runtime = (updated_at - created_at).total_seconds() / 60
            return round(runtime, 2)
        except:
            return 0.0