"""
Agent Health Module

Provides health monitoring data structures and utilities.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AgentHealth:
    """Agent health status information."""

    is_healthy: bool
    last_check: datetime
    response_time: float
    memory_usage: float
    error_count: int
    last_error: Optional[str] = None
