"""
Enhanced Agent Memory System - Public API
"""

from app.services.enhanced_agent_memory.base import (
    MemoryConfiguration,
    MemoryItem,
    EnhancedAgentMemory as _BaseMemory,
)
from app.services.enhanced_agent_memory.storage import StorageMixin
from app.services.enhanced_agent_memory.utils import UtilsMixin


# Combine all functionality
class EnhancedAgentMemory(_BaseMemory, StorageMixin, UtilsMixin):
    """
    Complete EnhancedAgentMemory with all functionality.
    """

    pass


# Global instance
enhanced_agent_memory = EnhancedAgentMemory()

__all__ = [
    "MemoryConfiguration",
    "MemoryItem",
    "EnhancedAgentMemory",
    "enhanced_agent_memory",
]
