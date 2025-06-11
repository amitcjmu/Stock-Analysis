"""
Enhanced Discovery Workflow Manager with retry logic and state validation.
"""

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

from app.schemas.flow_schemas import DiscoveryFlowState
from ..utils.retry import async_retry
from ..state_validation import WorkflowStateValidator

# Import handlers
from .data_source_analysis import DataSourceAnalysisHandler
from .data_validation_handler import DataValidationHandler
from .field_mapping_handler import FieldMappingHandler
from .asset_classification_handler import AssetClassificationHandler
from .dependency_analysis_handler import DependencyAnalysisHandler
from .database_integration_handler import DatabaseIntegrationHandler

if TYPE_CHECKING:
    from app.services.crewai_flow_service import CrewAIFlowService

logger = logging.getLogger(__name__)

class DiscoveryWorkflowManager:
    """
    Enhanced workflow manager with retry logic, state validation, and better error handling.
    """
    
    def __init__(self, crewai_service: "CrewAIFlowService"):
        self.crewai_service = crewai_service
        self.validator = WorkflowStateValidator()
        
        # Initialize all the handlers for the discovery workflow
        self.handlers = {
            'data_source_analysis': DataSourceAnalysisHandler(),
            'data_validation': DataValidationHandler(crewai_service),
            'field_mapping': FieldMappingHandler(crewai_service),
            'asset_classification': AssetClassificationHandler(crewai_service),
            'dependency_analysis': DependencyAnalysisHandler(crewai_service),
            'database_integration': DatabaseIntegrationHandler(crewai_service)
        }
    
    @async_retry(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    async def run_workflow(
        self, 
        flow_state: DiscoveryFlowState, 
        cmdb_data: Dict[str, Any], 
        client_account_id: str, 
        engagement_id: str, 
        user_id: str
    ) -> DiscoveryFlowState:
        """
        Execute the discovery workflow with enhanced error handling and retries.
        
        Args:
            flow_state: The current workflow state
            cmdb_data: The CMDB data to process
            client_account_id: The client account ID
            engagement_id: The engagement ID
            user_id: The user ID
            
        Returns:
            The updated workflow state
            
        Raises:
            RuntimeError: If the workflow fails after all retries
        """
        logger.info(f"Starting discovery workflow for session: {flow_state.session_id}")
        
        # Define the workflow steps in order
        workflow_steps = [
            ('data_source_analysis', self._run_data_source_analysis),
            ('data_validation', self._run_data_validation),
            ('field_mapping', self._run_field_mapping),
            ('asset_classification', self._run_asset_classification),
            ('dependency_analysis', self._run_dependency_analysis),
            ('database_integration', self._run_database_integration)
        ]
        
        # Store additional context
        context = {
            'cmdb_data': cmdb_data,
            'client_account_id': client_account_id,
            'engagement_id': engagement_id,
            'user_id': user_id,
            'start_time': datetime.utcnow()
        }
        
        try:
            # Execute each step in sequence
            for step_name, step_func in workflow_steps:
                try:
                    flow_state = await self._execute_workflow_step(
                        step_name=step_name,
                        step_func=step_func,
                        flow_state=flow_state,
                        context=context
                    )
                except Exception as e:
                    logger.error(
                        f"Workflow failed at step '{step_name}': {str(e)}", 
                        exc_info=True
                    )
                    flow_state = await self._handle_workflow_failure(
                        flow_state=flow_state,
                        step_name=step_name,
                        error=str(e),
                        context=context
                    )
                    break
            
            # If we get here, all steps completed successfully
            if flow_state.current_phase != 'failed':
                flow_state.current_phase = 'completed'
                flow_state.completion_complete = True
                logger.info(
                    f"Discovery workflow for session {flow_state.session_id} completed successfully"
                )
            
            return flow_state
            
        except Exception as e:
            logger.critical(
                f"Unexpected error in workflow execution: {str(e)}", 
                exc_info=True
            )
            raise RuntimeError(
                f"Workflow execution failed: {str(e)}"
            ) from e
    
    async def _execute_workflow_step(
        self,
        step_name: str,
        step_func: callable,
        flow_state: DiscoveryFlowState,
        context: Dict[str, Any]
    ) -> DiscoveryFlowState:
        """Execute a single workflow step with validation and error handling."""
        logger.info(f"Starting workflow step: {step_name}")
        
        # Update the current phase
        previous_phase = flow_state.current_phase
        flow_state.current_phase = step_name
        
        try:
            # Validate the state transition
            self.validator.validate_state_transition(
                current_state=flow_state,
                new_state=flow_state
            )
            
            # Execute the step
            step_start = datetime.utcnow()
            flow_state = await step_func(flow_state, context)
            step_duration = (datetime.utcnow() - step_start).total_seconds()
            
            # Log step completion
            logger.info(
                f"Completed workflow step '{step_name}' in {step_duration:.2f}s"
            )
            
            # Mark the step as complete
            setattr(flow_state, f"{step_name}_complete", True)
            
            return flow_state
            
        except Exception as e:
            # Log the error and re-raise
            logger.error(
                f"Error in workflow step '{step_name}': {str(e)}",
                exc_info=True
            )
            raise
    
    async def _handle_workflow_failure(
        self,
        flow_state: DiscoveryFlowState,
        step_name: str,
        error: str,
        context: Dict[str, Any]
    ) -> DiscoveryFlowState:
        """Handle workflow failure and update state accordingly."""
        logger.error(f"Workflow failed at step '{step_name}': {error}")
        
        # Update the workflow state
        flow_state.current_phase = 'failed'
        flow_state.error = error
        flow_state.failed_step = step_name
        
        # Log the failure
        if 'failure_count' not in flow_state.metadata:
            flow_state.metadata['failure_count'] = 0
        flow_state.metadata['failure_count'] += 1
        
        # Store error details
        if 'errors' not in flow_state.metadata:
            flow_state.metadata['errors'] = []
        flow_state.metadata['errors'].append({
            'step': step_name,
            'error': error,
            'timestamp': datetime.utcnow().isoformat(),
            'context': context
        })
        
        return flow_state
    
    # Individual step methods with retry decorators
    @async_retry(max_retries=2, initial_delay=1.0)
    async def _run_data_source_analysis(
        self, 
        flow_state: DiscoveryFlowState, 
        context: Dict[str, Any]
    ) -> DiscoveryFlowState:
        """Execute the data source analysis step."""
        return await self.handlers['data_source_analysis'].handle(
            flow_state=flow_state,
            cmdb_data=context['cmdb_data']
        )
    
    @async_retry(max_retries=2, initial_delay=1.0)
    async def _run_data_validation(
        self, 
        flow_state: DiscoveryFlowState, 
        context: Dict[str, Any]
    ) -> DiscoveryFlowState:
        """Execute the data validation step."""
        return await self.handlers['data_validation'].handle(
            flow_state=flow_state,
            cmdb_data=context['cmdb_data']
        )
    
    @async_retry(max_retries=2, initial_delay=1.0)
    async def _run_field_mapping(
        self, 
        flow_state: DiscoveryFlowState, 
        context: Dict[str, Any]
    ) -> DiscoveryFlowState:
        """Execute the field mapping step."""
        return await self.handlers['field_mapping'].handle(
            flow_state=flow_state,
            cmdb_data=context['cmdb_data']
        )
    
    @async_retry(max_retries=2, initial_delay=1.0)
    async def _run_asset_classification(
        self, 
        flow_state: DiscoveryFlowState, 
        context: Dict[str, Any]
    ) -> DiscoveryFlowState:
        """Execute the asset classification step."""
        return await self.handlers['asset_classification'].handle(flow_state)
    
    @async_retry(max_retries=2, initial_delay=1.0)
    async def _run_dependency_analysis(
        self, 
        flow_state: DiscoveryFlowState, 
        context: Dict[str, Any]
    ) -> DiscoveryFlowState:
        """Execute the dependency analysis step."""
        return await self.handlers['dependency_analysis'].handle(flow_state)
    
    @async_retry(max_retries=3, initial_delay=2.0, backoff_factor=2.0)
    async def _run_database_integration(
        self, 
        flow_state: DiscoveryFlowState, 
        context: Dict[str, Any]
    ) -> DiscoveryFlowState:
        """Execute the database integration step with more retries."""
        return await self.handlers['database_integration'].handle(
            flow_state=flow_state,
            client_account_id=context['client_account_id'],
            engagement_id=context['engagement_id'],
            user_id=context['user_id']
        )