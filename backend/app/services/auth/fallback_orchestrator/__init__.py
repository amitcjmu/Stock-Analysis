"""
Fallback Orchestrator Module

Smart routing and fallback coordination for the auth performance optimization system.
Provides intelligent routing between service layers with graceful degradation patterns
and automatic service recovery detection.

This module preserves backward compatibility for all existing imports.
"""

# Import all public classes and functions to maintain backward compatibility
from .base import (
    FallbackAttempt,
    FallbackConfig,
    FallbackLevel,
    FallbackResult,
    FallbackStrategy,
    OperationType,
    ServiceLevelMapping,
)
from .configs import DefaultConfigurationManager
from .handlers import EmergencyHandlerManager, LevelExecutor
from .orchestrator import FallbackOrchestrator
from .strategies import FallbackStrategyManager
from .utils import get_fallback_orchestrator, shutdown_fallback_orchestrator

# Preserve original module structure for backward compatibility
__all__ = [
    # Enums
    "FallbackLevel",
    "OperationType",
    "FallbackStrategy",
    # Data classes
    "FallbackConfig",
    "FallbackAttempt",
    "FallbackResult",
    "ServiceLevelMapping",
    # Main classes
    "FallbackOrchestrator",
    "FallbackStrategyManager",
    "EmergencyHandlerManager",
    "LevelExecutor",
    "DefaultConfigurationManager",
    # Utility functions
    "get_fallback_orchestrator",
    "shutdown_fallback_orchestrator",
]
