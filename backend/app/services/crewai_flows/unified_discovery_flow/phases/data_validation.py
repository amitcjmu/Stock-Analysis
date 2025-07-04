"""
Data Validation Phase

Handles the data import validation phase of the discovery flow.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

# from app.services.agents.data_import_validation_agent import DataImportValidationAgent
# TODO: Replace with real CrewAI agent
from app.services.agent_ui_bridge import agent_ui_bridge
from ..flow_config import PhaseNames

logger = logging.getLogger(__name__)


class DataValidationPhase:
    """Handles data import validation phase execution"""
    
    def __init__(self, state, data_validation_agent, init_context: Dict[str, Any]):
        """
        Initialize data validation phase
        
        Args:
            state: The flow state object
            data_validation_agent: The data validation agent instance
            init_context: Initial context for agent execution
        """
        self.state = state
        self.data_validation_agent = data_validation_agent
        self._init_context = init_context
    
    async def execute(self, previous_result: str) -> str:
        """
        Execute the data validation phase
        
        Args:
            previous_result: Result from the previous phase
            
        Returns:
            Phase result status
        """
        if previous_result == "initialization_failed":
            logger.error("❌ Skipping data validation due to initialization failure")
            return "data_validation_skipped"
        
        logger.info("🤖 Starting Data Import Validation with Agent-First Architecture")
        self.state.current_phase = PhaseNames.DATA_IMPORT_VALIDATION
        self.state.status = "running"
        self.state.progress_percentage = 10.0
        
        # Store record count for proper tracking
        total_records = len(self.state.raw_data) if self.state.raw_data else 0
        self.state.records_processed = 0
        self.state.records_total = total_records
        
        # Send real-time update
        await self._send_phase_start_update(total_records)
        
        try:
            # Prepare agent data
            agent_data = self._prepare_agent_data()
            
            # Send progress update
            await self._send_progress_update(total_records)
            
            # Execute data validation agent
            validation_result = await self.data_validation_agent.execute_analysis(
                agent_data, 
                self._init_context
            )
            
            # Process and store results
            self._process_validation_results(validation_result)
            
            # Send completion update
            await self._send_completion_update(validation_result)
            
            logger.info(f"✅ Data validation agent completed (confidence: {validation_result.confidence_score:.1f}%)")
            return "data_validation_completed"
            
        except Exception as e:
            logger.error(f"❌ Data validation agent failed: {e}")
            self.state.add_error("data_import", f"Agent execution failed: {str(e)}")
            
            # Send error update
            await self._send_error_update(str(e))
            
            return "data_validation_failed"
    
    def _prepare_agent_data(self) -> Dict[str, Any]:
        """Prepare data for agent execution"""
        return {
            'raw_data': self.state.raw_data,
            'source_columns': list(self.state.raw_data[0].keys()) if self.state.raw_data else [],
            'file_info': self.state.metadata.get('file_info', {}),
            'flow_metadata': {
                'flow_id': self.state.flow_id
            }
        }
    
    def _process_validation_results(self, validation_result):
        """Process and store validation results in state"""
        # Store agent results and confidence
        self.state.data_validation_results = validation_result.data
        self.state.agent_confidences['data_validation'] = validation_result.confidence_score
        
        # Collect insights and clarifications
        if validation_result.insights_generated:
            self.state.agent_insights.extend([
                insight.model_dump() for insight in validation_result.insights_generated
            ])
        
        if validation_result.clarifications_requested:
            self.state.user_clarifications.extend([
                req.model_dump() for req in validation_result.clarifications_requested
            ])
        
        # Update phase completion
        self.state.phase_completion['data_import'] = True
        self.state.progress_percentage = 20.0
        self.state.records_processed = len(self.state.raw_data)
        self.state.records_valid = len(self.state.raw_data)  # Assume all valid for now
    
    async def _send_phase_start_update(self, total_records: int):
        """Send real-time update when phase starts"""
        try:
            agent_ui_bridge.add_agent_insight(
                agent_id="data_import_agent",
                agent_name="Data Import Agent",
                insight_type="processing",
                page=f"flow_{self.state.flow_id}",
                title="Starting Data Import Validation",
                description=f"Beginning validation of {total_records} records",
                supporting_data={
                    'phase': 'data_import',
                    'records_total': total_records,
                    'records_processed': 0,
                    'progress_percentage': 10.0,
                    'start_time': datetime.utcnow().isoformat(),
                    'estimated_duration': '2-3 minutes'
                },
                confidence="high"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not send phase start update: {e}")
    
    async def _send_progress_update(self, total_records: int):
        """Send progress update during processing"""
        try:
            agent_ui_bridge.add_agent_insight(
                agent_id="data_import_agent",
                agent_name="Data Import Agent",
                insight_type="progress",
                page=f"flow_{self.state.flow_id}",
                title="Processing Data Records",
                description=f"Analyzing {total_records} records for format validation, security scanning, and data quality assessment",
                supporting_data={
                    'phase': 'data_import',
                    'progress_percentage': 10.0,
                    'records_processed': total_records // 2,  # Mock progress
                    'validation_checks': ['format', 'security', 'quality']
                },
                confidence="high"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not send progress update: {e}")
    
    async def _send_completion_update(self, validation_result):
        """Send completion update with results"""
        try:
            agent_ui_bridge.add_agent_insight(
                agent_id="data_import_agent",
                agent_name="Data Import Agent",
                insight_type="success",
                page=f"flow_{self.state.flow_id}",
                title="Data Import Validation Completed",
                description=f"Successfully validated {len(self.state.raw_data)} records with {validation_result.confidence_score:.1f}% confidence",
                supporting_data={
                    'phase': 'data_import',
                    'progress_percentage': 20.0,
                    'records_processed': len(self.state.raw_data),
                    'records_total': self.state.records_total,
                    'confidence_score': validation_result.confidence_score,
                    'validation_results': validation_result.data,
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
                agent_id="data_import_agent",
                agent_name="Data Import Agent",
                insight_type="error",
                page=f"flow_{self.state.flow_id}",
                title="Data Import Validation Failed",
                description=f"Validation failed: {error_message}",
                supporting_data={
                    'phase': 'data_import',
                    'error_type': 'agent_execution_failure',
                    'error_message': error_message,
                    'failure_time': datetime.utcnow().isoformat()
                },
                confidence="high"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not send error update: {e}")