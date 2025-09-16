"""
Utility Functions and Singleton Management

This module contains utility functions and singleton management
for the fallback orchestrator system.
"""

from typing import Optional

from .orchestrator import FallbackOrchestrator

# Singleton instance
_fallback_orchestrator_instance: Optional[FallbackOrchestrator] = None


def get_fallback_orchestrator() -> FallbackOrchestrator:
    """Get singleton FallbackOrchestrator instance"""
    global _fallback_orchestrator_instance
    if _fallback_orchestrator_instance is None:
        _fallback_orchestrator_instance = FallbackOrchestrator()
    return _fallback_orchestrator_instance


# Cleanup function for app shutdown
async def shutdown_fallback_orchestrator():
    """Shutdown fallback orchestrator (call during app shutdown)"""
    global _fallback_orchestrator_instance
    if _fallback_orchestrator_instance:
        await _fallback_orchestrator_instance.clear_emergency_cache()
        _fallback_orchestrator_instance = None
