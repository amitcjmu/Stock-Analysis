"""
Callback Handler Integration for CrewAI Flows
Integrates the enhanced callback handler with agent monitoring
Part of the Agent Observability Enhancement Phase 2
"""

import logging
from typing import Any, Dict, Optional

from app.core.context import RequestContext
from app.services.crewai_flows.handlers.callback_handler import CallbackHandler

logger = logging.getLogger(__name__)


class CallbackHandlerIntegration:
    """Manages callback handler creation with proper context for monitoring"""
    
    @staticmethod
    def create_callback_handler(
        flow_id: str,
        context: Optional[RequestContext] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CallbackHandler:
        """
        Create a callback handler with proper context for monitoring
        
        Args:
            flow_id: The CrewAI flow ID
            context: Request context with client/engagement IDs
            metadata: Additional metadata (may contain master_flow_id)
            
        Returns:
            Configured CallbackHandler instance
        """
        # Extract IDs from context
        client_account_id = None
        engagement_id = None
        
        if context:
            client_account_id = str(context.client_account_id) if context.client_account_id else None
            engagement_id = str(context.engagement_id) if context.engagement_id else None
        
        # If not in context, try metadata
        if not client_account_id and metadata:
            client_account_id = metadata.get('client_account_id')
            engagement_id = metadata.get('engagement_id')
        
        # Create callback handler with context
        callback_handler = CallbackHandler(
            flow_id=flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id
        )
        
        # Setup callbacks
        callback_handler.setup_callbacks()
        
        logger.info(f"✅ Created callback handler for flow {flow_id} with monitoring context")
        logger.info(f"   Client: {client_account_id}, Engagement: {engagement_id}")
        
        return callback_handler
    
    @staticmethod
    def get_crewai_callbacks(callback_handler: CallbackHandler) -> Dict[str, Any]:
        """
        Get callbacks in CrewAI format
        
        Args:
            callback_handler: The configured callback handler
            
        Returns:
            Dictionary of callbacks for CrewAI
        """
        if not callback_handler:
            return {}
        
        return {
            "on_agent_start": lambda agent_info: callback_handler._agent_callback({
                **agent_info,
                "action": "start"
            }),
            "on_agent_end": lambda agent_info: callback_handler._agent_callback({
                **agent_info,
                "action": "end"
            }),
            "on_task_start": lambda task_info: callback_handler._step_callback({
                **task_info,
                "status": "starting",
                "type": "task_start"
            }),
            "on_task_end": lambda task_info: callback_handler._task_completion_callback(task_info),
            "on_tool_start": lambda tool_info: callback_handler._step_callback({
                **tool_info,
                "type": "tool_use",
                "status": "starting"
            }),
            "on_tool_end": lambda tool_info: callback_handler._step_callback({
                **tool_info,
                "type": "tool_use",
                "status": "completed"
            }),
            "on_error": lambda error_info: callback_handler._error_callback(error_info)
        }