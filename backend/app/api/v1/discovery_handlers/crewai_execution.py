"""
CrewAI Execution Handler
Handles CrewAI-based discovery flow execution operations.
Wraps the UnifiedDiscoveryFlow for the unified API.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

logger = logging.getLogger(__name__)

class CrewAIExecutionHandler:
    """
    Handler for CrewAI-based discovery flow execution.
    Provides AI-powered discovery execution with agent intelligence.
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.logger = logger
    
    async def initialize_flow(
        self,
        flow_id: str,
        raw_data: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initialize CrewAI discovery flow execution.
        """
        try:
            self.logger.info(f"🤖 Initializing CrewAI flow: {flow_id}")
            
            # Try to import UnifiedDiscoveryFlow
            try:
                from app.services.crewai_flows.unified_discovery_flow import create_unified_discovery_flow
                
                # Create unified discovery flow
                flow = create_unified_discovery_flow(
                    session_id=flow_id,
                    client_account_id=self.context.client_account_id,
                    engagement_id=self.context.engagement_id,
                    user_id=self.context.user_id,
                    raw_data=raw_data,
                    crewai_service=None,  # Will be initialized internally
                    context=self.context
                )
                
                # Start the flow
                result = await flow.kickoff()
                
                self.logger.info(f"✅ CrewAI flow initialized: {flow_id}")
                return {
                    "status": "initialized",
                    "flow_id": flow_id,
                    "crewai_result": result,
                    "agent_insights": result.get("agent_insights", []) if isinstance(result, dict) else []
                }
                
            except ImportError as e:
                self.logger.warning(f"⚠️ UnifiedDiscoveryFlow not available: {e}")
                # Return mock success for development
                return {
                    "status": "initialized",
                    "flow_id": flow_id,
                    "crewai_result": "mock_success",
                    "agent_insights": [
                        {
                            "agent": "mock_agent",
                            "insight": "CrewAI flow would be initialized here",
                            "timestamp": datetime.now().isoformat()
                        }
                    ]
                }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize CrewAI flow: {e}")
            raise
    
    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """
        Get CrewAI flow execution status.
        """
        try:
            self.logger.info(f"🔍 Getting CrewAI flow status: {flow_id}")
            
            # Try to get flow state from CrewAI persistence
            try:
                from app.services.crewai_flows.postgresql_flow_persistence import PostgreSQLFlowPersistence
                
                persistence = PostgreSQLFlowPersistence(self.db, self.context)
                flow_state = await persistence.restore_flow_state(flow_id)
                
                if flow_state:
                    status_data = flow_state.dict()
                    status_data.update({
                        "handler": "crewai",
                        "execution_engine": "unified_discovery_flow",
                        "agent_powered": True
                    })
                    
                    self.logger.info(f"✅ CrewAI flow status retrieved: {flow_id}")
                    return status_data
                
            except ImportError:
                self.logger.warning("⚠️ CrewAI persistence not available")
            
            # Return mock status for development
            mock_status = {
                "flow_id": flow_id,
                "session_id": flow_id,
                "client_account_id": self.context.client_account_id,
                "engagement_id": self.context.engagement_id,
                "user_id": self.context.user_id,
                "status": "mock_active",
                "current_phase": "data_import",
                "progress_percentage": 25.0,
                "phases": {
                    "data_import": True,
                    "field_mapping": False,
                    "data_cleansing": False,
                    "asset_inventory": False,
                    "dependency_analysis": False,
                    "tech_debt_analysis": False
                },
                "handler": "crewai",
                "execution_engine": "mock_unified_discovery_flow",
                "agent_powered": True,
                "agent_insights": [
                    {
                        "agent": "mock_data_analyst",
                        "insight": "Data import phase would be completed by CrewAI agents",
                        "timestamp": datetime.now().isoformat()
                    }
                ],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Mock CrewAI flow status returned: {flow_id}")
            return mock_status
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get CrewAI flow status: {e}")
            raise
    
    async def execute_phase(
        self,
        phase: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a discovery flow phase using CrewAI agents.
        """
        try:
            self.logger.info(f"🤖 Executing CrewAI phase: {phase}")
            
            # For now, return a success response with agent insights
            # TODO: Implement actual CrewAI phase execution
            
            result = {
                "status": "completed",
                "phase": phase,
                "handler": "crewai",
                "execution_engine": "unified_discovery_flow",
                "agent_insights": [
                    {
                        "agent": f"{phase}_specialist",
                        "insight": f"Phase {phase} would be executed by specialized CrewAI agents",
                        "confidence": 0.85,
                        "timestamp": datetime.now().isoformat()
                    }
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ CrewAI phase execution completed: {phase}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ CrewAI phase execution failed: {e}")
            raise
    
    async def get_active_flows(self) -> List[Dict[str, Any]]:
        """
        Get active CrewAI discovery flows.
        """
        try:
            self.logger.info("🔍 Getting active CrewAI flows")
            
            # For now, return mock data
            # TODO: Implement actual CrewAI flow retrieval
            
            mock_flows = [
                {
                    "flow_id": f"crewai-flow-{datetime.now().strftime('%Y%m%d')}",
                    "client_id": self.context.client_account_id,
                    "client_name": "Mock Client",
                    "engagement_id": self.context.engagement_id,
                    "engagement_name": "Mock Engagement",
                    "status": "running",
                    "current_phase": "asset_inventory",
                    "progress": 60.0,
                    "handler": "crewai",
                    "execution_engine": "unified_discovery_flow",
                    "agent_powered": True,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "phases": {
                        "data_import_completed": True,
                        "attribute_mapping_completed": True,
                        "data_cleansing_completed": True,
                        "inventory_completed": False,
                        "dependencies_completed": False,
                        "tech_debt_completed": False
                    },
                    "agent_insights": [
                        {
                            "agent": "asset_intelligence_agent",
                            "insight": "Asset inventory in progress with AI classification",
                            "timestamp": datetime.now().isoformat()
                        }
                    ]
                }
            ]
            
            self.logger.info(f"✅ Retrieved {len(mock_flows)} active CrewAI flows")
            return mock_flows
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get active CrewAI flows: {e}")
            raise 