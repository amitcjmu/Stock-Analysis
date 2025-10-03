"""
Optimized Agent Configuration - Public API
"""

from app.services.optimized_agent_config.base import (
    AgentOptimizationConfig,
    OptimizedAgentConfigurator as _BaseConfigurator,
)
from app.services.optimized_agent_config.factory import ConfigFactoryMixin
from app.services.optimized_agent_config.utils import ConfigUtilsMixin


# Combine all functionality
class OptimizedAgentConfigurator(
    _BaseConfigurator, ConfigFactoryMixin, ConfigUtilsMixin
):
    """
    Complete OptimizedAgentConfigurator with all functionality.
    """

    pass


# Global configurator instance
optimized_agent_configurator = OptimizedAgentConfigurator()

__all__ = [
    "AgentOptimizationConfig",
    "OptimizedAgentConfigurator",
    "optimized_agent_configurator",
]
