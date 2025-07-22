"""
Data Models for Intelligent Flow Agent

This module contains the data models used by the Intelligent Flow Agent
for representing flow intelligence results and analysis data.
"""

from typing import List

from pydantic import BaseModel


class FlowIntelligenceResult(BaseModel):
    """Result from the intelligent flow agent"""
    success: bool
    flow_id: str
    flow_type: str
    current_phase: str
    routing_decision: str
    user_guidance: str
    reasoning: str
    confidence: float
    next_actions: List[str] = []
    issues_found: List[str] = []