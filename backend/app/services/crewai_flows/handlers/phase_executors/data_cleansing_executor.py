"""
Data Cleansing Executor - Backward Compatibility Facade

This file maintains backward compatibility while the implementation
has been modularized for better code organization.
"""

# Import from the modular implementation
from .data_cleansing import DataCleansingExecutor

# Maintain backward compatibility
__all__ = ["DataCleansingExecutor"]
