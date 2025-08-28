"""
Flow Processing Models
Data structures for flow processing API endpoints
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class FlowContinuationRequest(BaseModel):
    user_context: Optional[Dict[str, Any]] = None


class TaskResult(BaseModel):
    task_id: str
    task_name: str
    status: str  # 'completed', 'in_progress', 'not_started', 'failed'
    confidence: float
    next_steps: List[str] = []


class PhaseStatus(BaseModel):
    phase_id: str
    phase_name: str
    status: str  # 'completed', 'in_progress', 'not_started', 'blocked'
    completion_percentage: float
    tasks: List[TaskResult]
    estimated_time_remaining: Optional[int] = None


class RoutingContext(BaseModel):
    target_page: str
    recommended_page: str
    flow_id: str
    phase: str
    flow_type: str


class UserGuidance(BaseModel):
    primary_message: str
    action_items: List[str]
    user_actions: List[str]
    system_actions: List[str]
    estimated_completion_time: Optional[int] = None


class FlowContinuationResponse(BaseModel):
    success: bool
    flow_id: str
    flow_type: str
    current_phase: str
    routing_context: RoutingContext
    user_guidance: UserGuidance
    checklist_status: List[PhaseStatus]
    agent_insights: List[Dict[str, Any]] = []
    confidence: float
    reasoning: str
    execution_time: float
