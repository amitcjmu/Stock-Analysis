"""
Dependency Analysis Phase

Handles the dependency analysis phase of the discovery flow.
"""

import logging
from typing import Dict, Any, Optional

# from app.services.agents.dependency_analysis_agent import DependencyAnalysisAgent
# Handled by MasterFlowOrchestrator with real CrewAI agents
from ..flow_config import PhaseNames

logger = logging.getLogger(__name__)


class DependencyAnalysisPhase:
    """Handles dependency analysis phase execution"""
    
    def __init__(self, state, dependency_analysis_agent, init_context: Dict[str, Any], flow_bridge=None):
        """
        Initialize dependency analysis phase
        
        Args:
            state: The flow state object
            dependency_analysis_agent: The dependency analysis agent instance
            init_context: Initial context for agent execution
            flow_bridge: Optional flow bridge for state persistence
        """
        self.state = state
        self.dependency_analysis_agent = dependency_analysis_agent
        self._init_context = init_context
        self.flow_bridge = flow_bridge
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the dependency analysis phase
        
        Args:
            input_data: Input data containing assets and context
            
        Returns:
            Analysis results
        """
        logger.info("🤖 Starting Dependency Analysis with Agent-First Architecture")
        
        try:
            # Execute dependency analysis agent
            analysis_result = await self.dependency_analysis_agent.execute_analysis(
                input_data, 
                self._init_context
            )
            
            # Process results
            dependencies = {
                "dependencies": analysis_result.data,
                "confidence": analysis_result.confidence_score,
                "insights": [insight.model_dump() for insight in analysis_result.insights_generated]
            }
            
            # Store in state
            self.state.dependencies = dependencies
            self.state.agent_confidences['dependency_analysis'] = analysis_result.confidence_score
            
            logger.info(f"✅ Dependency analysis completed (confidence: {analysis_result.confidence_score:.1f}%)")
            return dependencies
            
        except Exception as e:
            logger.error(f"❌ Dependency analysis failed: {e}")
            self.state.add_error("dependency_analysis", f"Agent execution failed: {str(e)}")
            raise