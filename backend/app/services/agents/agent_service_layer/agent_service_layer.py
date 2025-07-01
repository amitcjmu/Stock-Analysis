"""
Main agent service layer that orchestrates the modular components.
Provides backward compatibility with the original AgentServiceLayer interface.
"""

import logging
from typing import Dict, Any, List, Optional

from .core.service_layer import AgentServiceLayer as CoreAgentServiceLayer

logger = logging.getLogger(__name__)


class AgentServiceLayer(CoreAgentServiceLayer):
    """
    Main agent service layer providing backward compatibility.
    
    This class inherits from the core service layer and provides the same interface
    as the original monolithic AgentServiceLayer for full backward compatibility.
    """
    
    def __init__(self, client_account_id: str, engagement_id: str, user_id: Optional[str] = None):
        """Initialize with multi-tenant context"""
        super().__init__(client_account_id, engagement_id, user_id)
        logger.info(f"Initialized AgentServiceLayer for client: {client_account_id}, engagement: {engagement_id}")
    
    # All methods are inherited from CoreAgentServiceLayer
    # This class exists primarily for backward compatibility and future extensions


# Singleton instance for common use cases
_default_agent_service = None


def get_agent_service(client_account_id: str, engagement_id: str, user_id: Optional[str] = None) -> AgentServiceLayer:
    """Get or create agent service instance"""
    global _default_agent_service
    
    # For now, create new instance each time to ensure proper context isolation
    # In the future, this could be enhanced with caching and context validation
    return AgentServiceLayer(client_account_id, engagement_id, user_id)