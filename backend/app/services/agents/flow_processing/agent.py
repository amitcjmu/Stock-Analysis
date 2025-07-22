"""
Flow Processing Agent - Legacy Compatibility Wrapper

This module provides backward compatibility for the legacy FlowProcessingAgent
interface while delegating to the new modular CrewAI implementation.
"""

import asyncio
from typing import Any, Dict

from .crew import UniversalFlowProcessingCrew
from .models import FlowContinuationResult


class FlowProcessingAgent:
    """
    Legacy compatibility wrapper for the new CrewAI-based implementation
    """
    
    def __init__(self, db_session=None, client_account_id=None, engagement_id=None):
        self.crew = UniversalFlowProcessingCrew(db_session, client_account_id, engagement_id)
    
    async def process_flow_continuation(self, flow_id: str, user_context: Dict[str, Any] = None) -> FlowContinuationResult:
        """Legacy method that delegates to the new crew-based implementation"""
        return await self.crew.process_flow_continuation(flow_id, user_context)
    
    def _run(self, flow_id: str, user_context: Dict[str, Any] = None) -> str:
        """Legacy method for backwards compatibility"""
        try:
            result = asyncio.run(self.process_flow_continuation(flow_id, user_context))
            return f"Flow {flow_id} processed. Route: {result.routing_decision.target_page}"
        except Exception as e:
            return f"Flow processing failed: {str(e)}"