"""
Agent metadata definitions to avoid circular imports
"""

from dataclasses import dataclass
from typing import List, Type

# Optional CrewAI import
try:
    from crewai import Agent
except ImportError:
    # Create a dummy Agent class for type hints when CrewAI is not available
    class Agent:
        pass

@dataclass
class AgentMetadata:
    """Metadata for registered agents"""
    name: str
    description: str
    agent_class: Type[Agent]
    required_tools: List[str]
    capabilities: List[str]
    max_iter: int = 15
    memory: bool = True
    verbose: bool = True
    allow_delegation: bool = False