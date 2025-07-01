"""
Data Cleansing Phase

Handles the data cleansing phase of the discovery flow.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from app.services.agents.data_cleansing_agent import DataCleansingAgent
from ..flow_config import PhaseNames

logger = logging.getLogger(__name__)


class DataCleansingPhase:
    """Handles data cleansing phase execution"""
    
    def __init__(self, state, data_cleansing_agent: DataCleansingAgent, init_context: Dict[str, Any], flow_bridge=None):
        """
        Initialize data cleansing phase
        
        Args:
            state: The flow state object
            data_cleansing_agent: The data cleansing agent instance
            init_context: Initial context for agent execution
            flow_bridge: Optional flow bridge for state persistence
        """
        self.state = state
        self.data_cleansing_agent = data_cleansing_agent
        self._init_context = init_context
        self.flow_bridge = flow_bridge
    
    async def execute(self, previous_result: str) -> str:
        """
        Execute the data cleansing phase
        
        Args:
            previous_result: Result from the previous phase
            
        Returns:
            Phase result status
        """
        logger.info("🤖 Starting Data Cleansing with Agent-First Architecture")
        self.state.current_phase = PhaseNames.DATA_CLEANSING
        
        # Update database immediately when phase starts
        await self._update_flow_state()
        
        try:
            # Prepare agent data
            agent_data = self._prepare_agent_data()
            
            # Execute data cleansing agent
            cleansing_result = await self.data_cleansing_agent.execute_analysis(
                agent_data, 
                self._init_context
            )
            
            # Process and store results
            self._process_cleansing_results(cleansing_result)
            
            # Persist state with agent insights and progress
            await self._update_flow_state()
            
            logger.info(f"✅ Data cleansing agent completed (confidence: {cleansing_result.confidence_score:.1f}%)")
            return "data_cleansing_completed"
            
        except Exception as e:
            logger.error(f"❌ Data cleansing agent failed: {e}")
            self.state.add_error("data_cleansing", f"Agent execution failed: {str(e)}")
            
            # Update database even on failure
            await self._update_flow_state()
            
            return "data_cleansing_failed"
    
    def _prepare_agent_data(self) -> Dict[str, Any]:
        """Prepare data for agent execution"""
        return {
            'raw_data': self.state.raw_data,
            'field_mappings': self.state.field_mappings,
            'validation_results': self.state.data_validation_results,
            'flow_metadata': {
                'session_id': self.state.session_id,
                'flow_id': self.state.flow_id
            }
        }
    
    def _process_cleansing_results(self, cleansing_result):
        """Process and store cleansing results in state"""
        # Store agent results and confidence
        self.state.cleaned_data = cleansing_result.data.get('cleaned_data', self.state.raw_data)
        self.state.data_cleansing_results = cleansing_result.data
        self.state.agent_confidences['data_cleansing'] = cleansing_result.confidence_score
        
        # Collect insights and clarifications
        if cleansing_result.insights_generated:
            self.state.agent_insights.extend([
                insight.model_dump() for insight in cleansing_result.insights_generated
            ])
        
        if cleansing_result.clarifications_requested:
            self.state.user_clarifications.extend([
                req.model_dump() for req in cleansing_result.clarifications_requested
            ])
        
        # Update phase completion
        self.state.phase_completion['data_cleansing'] = True
        self.state.progress_percentage = 60.0
    
    async def _update_flow_state(self):
        """Update flow state in database"""
        if self.flow_bridge:
            try:
                await self.flow_bridge.update_flow_state(self.state)
            except Exception as e:
                logger.warning(f"⚠️ Failed to update flow state: {e}")