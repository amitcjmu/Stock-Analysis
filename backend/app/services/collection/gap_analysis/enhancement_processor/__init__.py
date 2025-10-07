"""AI enhancement processor for gap analysis.

Modularized structure (December 2024):
- base.py: EnhancementProcessorMixin with core logic
- agent_setup.py: Agent and memory manager initialization
- asset_processor.py: Core asset processing functions
- gap_helpers.py: Gap grouping and context loading
- redis_lock.py: Distributed locking
- constants.py: Configuration constants

This package provides backward compatibility with the original
enhancement_processor.py module.
"""

from .base import EnhancementProcessorMixin
from .constants import (
    CIRCUIT_BREAKER_THRESHOLD,
    MIN_ATTEMPTS_BEFORE_BREAKING,
    PER_ASSET_TIMEOUT,
)

__all__ = [
    "EnhancementProcessorMixin",
    "PER_ASSET_TIMEOUT",
    "CIRCUIT_BREAKER_THRESHOLD",
    "MIN_ATTEMPTS_BEFORE_BREAKING",
]
