"""
Adaptive Form Service Configuration Package

This package provides configuration constants for the adaptive form service.
All public APIs are re-exported here to maintain backward compatibility.
"""

from .critical_attributes import CRITICAL_ATTRIBUTES_CONFIG
from .field_options import FIELD_OPTIONS

__all__ = [
    "CRITICAL_ATTRIBUTES_CONFIG",
    "FIELD_OPTIONS",
]
