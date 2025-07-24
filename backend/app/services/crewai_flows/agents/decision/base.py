"""
Base Decision Agent Classes and Types

Core abstractions for intelligent decision-making agents.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from crewai import Agent

logger = logging.getLogger(__name__)


class PhaseAction(Enum):
    """Actions that agents can recommend for phase transitions"""

    PROCEED = "proceed"
    PAUSE = "pause"
    SKIP = "skip"
    RETRY = "retry"
    FAIL = "fail"


class AgentDecision:
    """Structured decision from an agent"""

    def __init__(
        self,
        action: PhaseAction,
        next_phase: str,
        confidence: float,
        reasoning: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.action = action
        self.next_phase = next_phase
        self.confidence = confidence
        self.reasoning = reasoning
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert decision to dictionary for serialization"""
        return {
            "action": self.action.value,
            "next_phase": self.next_phase,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class BaseDecisionAgent(Agent, ABC):
    """Base class for all decision-making agents"""

    def __init__(self, role: str, goal: str, backstory: str, **kwargs):
        """Initialize base decision agent"""
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=True,
            allow_delegation=False,
            **kwargs
        )

    @abstractmethod
    async def analyze_phase_transition(
        self, current_phase: str, results: Any, state: UnifiedDiscoveryFlowState
    ) -> AgentDecision:
        """
        Analyze current state and results to decide next phase transition.

        Args:
            current_phase: Current phase name
            results: Results from current phase execution
            state: Current flow state

        Returns:
            AgentDecision with recommended action
        """
        pass

    def _calculate_confidence(self, factors: Dict[str, float]) -> float:
        """
        Calculate overall confidence score from multiple factors.

        Args:
            factors: Dictionary of factor_name -> confidence (0-1)

        Returns:
            Weighted average confidence score
        """
        if not factors:
            return 0.0

        total_weight = sum(factors.values())
        if total_weight == 0:
            return 0.0

        return min(1.0, total_weight / len(factors))

    def _get_state_attr(self, state: Any, attr: str, default: Any = None) -> Any:
        """Get attribute from state, handling both dict and object types"""
        if isinstance(state, dict):
            return state.get(attr, default)
        return getattr(state, attr, default)
