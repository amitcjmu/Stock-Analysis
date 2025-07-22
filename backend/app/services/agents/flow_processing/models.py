"""
Data Models for Flow Processing

This module contains all the data models used by the Flow Processing Agent
for representing flow analysis results, routing decisions, and continuation results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class FlowAnalysisResult:
    """Result of flow state analysis"""
    flow_id: str
    flow_type: str
    current_phase: str
    status: str
    progress_percentage: float
    phases_data: Dict[str, Any] = field(default_factory=dict)
    agent_insights: List[Dict] = field(default_factory=list)
    validation_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteDecision:
    """Routing decision made by the agent"""
    target_page: str
    flow_id: str
    phase: str
    flow_type: str
    reasoning: str
    confidence: float
    next_actions: List[str] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowContinuationResult:
    """Complete result of flow continuation analysis"""
    flow_id: str
    flow_type: str
    current_phase: str
    routing_decision: RouteDecision
    user_guidance: Dict[str, Any]
    success: bool = True
    error_message: Optional[str] = None