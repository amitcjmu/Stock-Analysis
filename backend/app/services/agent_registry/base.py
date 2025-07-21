"""
Base Agent Registry Types and Classes

Core types and base classes for the agent registry system.
"""

import logging
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)


class AgentPhase(Enum):
    """Agent execution phases"""
    DISCOVERY = "discovery"
    ASSESSMENT = "assessment"  
    PLANNING = "planning"
    MIGRATION = "migration"
    MODERNIZATION = "modernization"
    DECOMMISSION = "decommission"
    FINOPS = "finops"
    LEARNING_CONTEXT = "learning_context"
    OBSERVABILITY = "observability"


class AgentStatus(Enum):
    """Agent operational status"""
    ACTIVE = "active"
    STANDBY = "standby"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    PLANNED = "planned"
    IN_DEVELOPMENT = "in_development"


@dataclass
class AgentRegistration:
    """Complete agent registration information"""
    agent_id: str
    name: str
    role: str
    phase: AgentPhase
    status: AgentStatus
    expertise: str
    specialization: str
    key_skills: List[str]
    capabilities: List[str]
    api_endpoints: List[str]
    description: str
    version: str = "1.0.0"
    registration_time: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    tasks_completed: int = 0
    success_rate: float = 0.0
    avg_execution_time: float = 0.0
    memory_utilization: float = 0.0
    confidence: float = 0.0
    learning_enabled: bool = False
    cross_page_communication: bool = False
    modular_handlers: bool = False