"""
Field Mapping Phase

Handles the attribute/field mapping phase of the discovery flow.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from app.services.agents.attribute_mapping_agent import AttributeMappingAgent
from app.services.agent_ui_bridge import agent_ui_bridge
from ..flow_config import PhaseNames

logger = logging.getLogger(__name__)


class FieldMappingPhase:
    """Handles field mapping phase execution"""
    
    def __init__(self, state, attribute_mapping_agent: AttributeMappingAgent, init_context: Dict[str, Any], flow_bridge=None):
        """
        Initialize field mapping phase
        
        Args:
            state: The flow state object
            attribute_mapping_agent: The attribute mapping agent instance
            init_context: Initial context for agent execution
            flow_bridge: Optional flow bridge for state persistence
        """
        self.state = state
        self.attribute_mapping_agent = attribute_mapping_agent
        self._init_context = init_context
        self.flow_bridge = flow_bridge
    
    async def execute(self, previous_result: str) -> str:
        """
        Execute the field mapping phase
        
        Args:
            previous_result: Result from the previous phase
            
        Returns:
            Phase result status
        """
        if previous_result in ["data_validation_skipped", "data_validation_failed"]:
            logger.warning("⚠️ Proceeding with attribute mapping despite validation issues")
        
        logger.info("🤖 Starting Attribute Mapping with Agent-First Architecture")
        self.state.current_phase = PhaseNames.FIELD_MAPPING
        
        # Update database immediately when phase starts
        await self._update_flow_state()
        
        # Send real-time update
        await self._send_phase_start_update()
        
        try:
            # Prepare agent data
            agent_data = self._prepare_agent_data()
            
            # Execute attribute mapping agent
            mapping_result = await self.attribute_mapping_agent.execute_analysis(
                agent_data, 
                self._init_context
            )
            
            # Process and store results
            self._process_mapping_results(mapping_result)
            
            # Send completion update
            await self._send_completion_update(mapping_result)
            
            # Persist state with agent insights and progress
            await self._update_flow_state()
            
            logger.info(f"✅ Attribute mapping agent completed (confidence: {mapping_result.confidence_score:.1f}%)")
            return "field_mapping_completed"
            
        except Exception as e:
            logger.error(f"❌ Attribute mapping agent failed: {e}")
            self.state.add_error("attribute_mapping", f"Agent execution failed: {str(e)}")
            
            # Send error update
            await self._send_error_update(str(e))
            
            # Update database even on failure
            await self._update_flow_state()
            
            return "attribute_mapping_failed"
    
    def _prepare_agent_data(self) -> Dict[str, Any]:
        """Prepare data for agent execution"""
        return {
            'raw_data': self.state.raw_data,
            'source_columns': list(self.state.raw_data[0].keys()) if self.state.raw_data else [],
            'validation_results': self.state.data_validation_results,
            'flow_metadata': {
                'flow_id': self.state.flow_id,
                'client_account_id': self.state.client_account_id,
                'engagement_id': self.state.engagement_id
            }
        }
    
    def _process_mapping_results(self, mapping_result):
        """Process and store mapping results in state"""
        # Store agent results and confidence
        self.state.field_mappings = mapping_result.data
        self.state.agent_confidences['attribute_mapping'] = mapping_result.confidence_score
        
        # Collect insights and clarifications
        if mapping_result.insights_generated:
            self.state.agent_insights.extend([
                insight.model_dump() for insight in mapping_result.insights_generated
            ])
        
        if mapping_result.clarifications_requested:
            self.state.user_clarifications.extend([
                req.model_dump() for req in mapping_result.clarifications_requested
            ])
        
        # Update phase completion
        self.state.phase_completion['attribute_mapping'] = True
        self.state.progress_percentage = 40.0
    
    async def _update_flow_state(self):
        """Update flow state in database"""
        if self.flow_bridge:
            try:
                await self.flow_bridge.update_flow_state(self.state)
            except Exception as e:
                logger.warning(f"⚠️ Failed to update flow state: {e}")
    
    async def _send_phase_start_update(self):
        """Send real-time update when phase starts"""
        try:
            agent_ui_bridge.add_agent_insight(
                agent_id="attribute_mapping_agent",
                agent_name="Attribute Mapping Agent",
                insight_type="processing",
                page=f"flow_{self.state.flow_id}",
                title="Starting Field Mapping Analysis",
                description="Analyzing source columns and determining optimal field mappings",
                supporting_data={
                    'phase': 'attribute_mapping',
                    'source_columns': list(self.state.raw_data[0].keys()) if self.state.raw_data else [],
                    'progress_percentage': 30.0,
                    'start_time': datetime.utcnow().isoformat()
                },
                confidence="high"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not send phase start update: {e}")
    
    async def _send_completion_update(self, mapping_result):
        """Send completion update with results"""
        try:
            mapped_fields = len(mapping_result.data.get('mappings', {}))
            agent_ui_bridge.add_agent_insight(
                agent_id="attribute_mapping_agent",
                agent_name="Attribute Mapping Agent",
                insight_type="success",
                page=f"flow_{self.state.flow_id}",
                title="Field Mapping Completed",
                description=f"Successfully mapped {mapped_fields} fields with {mapping_result.confidence_score:.1f}% confidence",
                supporting_data={
                    'phase': 'attribute_mapping',
                    'progress_percentage': 40.0,
                    'mapped_fields': mapped_fields,
                    'confidence_score': mapping_result.confidence_score,
                    'mappings': mapping_result.data,
                    'completion_time': datetime.utcnow().isoformat()
                },
                confidence="high"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not send completion update: {e}")
    
    async def _send_error_update(self, error_message: str):
        """Send error update when phase fails"""
        try:
            agent_ui_bridge.add_agent_insight(
                agent_id="attribute_mapping_agent",
                agent_name="Attribute Mapping Agent",
                insight_type="error",
                page=f"flow_{self.state.flow_id}",
                title="Field Mapping Failed",
                description=f"Mapping failed: {error_message}",
                supporting_data={
                    'phase': 'attribute_mapping',
                    'error_type': 'agent_execution_failure',
                    'error_message': error_message,
                    'failure_time': datetime.utcnow().isoformat()
                },
                confidence="high"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not send error update: {e}")