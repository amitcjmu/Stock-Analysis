"""
Learning Pattern Models - Patterns learned by the agent system
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any

from .learning_context import LearningContext


@dataclass
class LearningPattern:
    """Represents a learned pattern with context isolation."""
    pattern_id: str
    pattern_type: str
    context: LearningContext
    pattern_data: Dict[str, Any]
    confidence: float
    usage_count: int
    created_at: datetime
    last_used: datetime
    success_rate: float = 1.0


@dataclass
class PerformanceLearningPattern:
    """Performance-based learning pattern for optimization."""
    pattern_id: str
    operation_type: str
    performance_metrics: Dict[str, float]
    optimization_applied: List[str]
    improvement_factor: float
    context_data: Dict[str, Any]
    created_at: datetime
    usage_count: int = 0
    success_rate: float = 1.0