"""
Pydantic schemas for CrewAI agent-related data structures.
"""
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Agent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str
    goal: str
    backstory: str

class CrewTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    agent: Agent

class TaskOutput(BaseModel):
    task_id: str
    output: str
    timestamp: str

class Crew(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    tasks: List[CrewTask]
    agents: List[Agent]

class CrewProcess(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    crew_id: str
    status: str

class TaskContext(BaseModel):
    task_id: str
    context: Dict[str, Any] 