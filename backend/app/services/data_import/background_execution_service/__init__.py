"""
Background Execution Service Module

Modularized background execution service with:
- core: Main BackgroundExecutionService class
- utils: Pure utility functions for status management

This module preserves full backward compatibility with the original
background_execution_service.py file.
"""

from .core import BackgroundExecutionService
from .import_processor_runner import ImportProcessorBackgroundRunner
from .utils import (
    calculate_progress_percentage,
    determine_final_status,
    determine_final_status_from_phase_result,
    get_execution_status,
    update_flow_status,
)

# Maintain backward compatibility - expose all public symbols
__all__ = [
    # Main service class
    "BackgroundExecutionService",
    "ImportProcessorBackgroundRunner",
    # Utility functions
    "calculate_progress_percentage",
    "determine_final_status",
    "determine_final_status_from_phase_result",
    "get_execution_status",
    "update_flow_status",
]
