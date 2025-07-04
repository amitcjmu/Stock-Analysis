"""
Technical Debt Assessment Phase

Handles the technical debt assessment phase of the discovery flow.
"""

import logging
from typing import Dict, Any, Optional

# from app.services.agents.tech_debt_analysis_agent import TechDebtAnalysisAgent
# TODO: Replace with real CrewAI agent
from ..flow_config import PhaseNames

logger = logging.getLogger(__name__)


class TechDebtAssessmentPhase:
    """Handles technical debt assessment phase execution"""
    
    def __init__(self, state, tech_debt_analysis_agent, init_context: Dict[str, Any], flow_bridge=None):
        """
        Initialize tech debt assessment phase
        
        Args:
            state: The flow state object
            tech_debt_analysis_agent: The tech debt analysis agent instance
            init_context: Initial context for agent execution
            flow_bridge: Optional flow bridge for state persistence
        """
        self.state = state
        self.tech_debt_analysis_agent = tech_debt_analysis_agent
        self._init_context = init_context
        self.flow_bridge = flow_bridge
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the technical debt assessment phase
        
        Args:
            input_data: Input data containing assets and context
            
        Returns:
            Analysis results
        """
        logger.info("🤖 Starting Technical Debt Assessment with Agent-First Architecture")
        
        try:
            # Execute tech debt analysis agent
            analysis_result = await self.tech_debt_analysis_agent.execute_analysis(
                input_data, 
                self._init_context
            )
            
            # Process results
            tech_debt = {
                "technical_debt": analysis_result.data,
                "confidence": analysis_result.confidence_score,
                "insights": [insight.model_dump() for insight in analysis_result.insights_generated],
                "severity_summary": self._summarize_severity(analysis_result.data)
            }
            
            # Store in state
            self.state.technical_debt = tech_debt
            self.state.agent_confidences['tech_debt_analysis'] = analysis_result.confidence_score
            
            logger.info(f"✅ Technical debt assessment completed (confidence: {analysis_result.confidence_score:.1f}%)")
            return tech_debt
            
        except Exception as e:
            logger.error(f"❌ Technical debt assessment failed: {e}")
            self.state.add_error("tech_debt_assessment", f"Agent execution failed: {str(e)}")
            raise
    
    def _summarize_severity(self, tech_debt_data: Dict[str, Any]) -> Dict[str, int]:
        """Summarize technical debt by severity level"""
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        # Count items by severity (implementation depends on data structure)
        if isinstance(tech_debt_data, dict) and "issues" in tech_debt_data:
            for issue in tech_debt_data.get("issues", []):
                severity = issue.get("severity", "medium").lower()
                if severity in severity_counts:
                    severity_counts[severity] += 1
        
        return severity_counts