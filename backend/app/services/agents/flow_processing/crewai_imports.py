"""
CrewAI Import Management and Fallback Classes

This module handles conditional imports for CrewAI and provides fallback
implementations when CrewAI is not available.
"""

import logging

logger = logging.getLogger(__name__)

try:
    from crewai import Agent, Crew, Process, Task
    from crewai.tools import BaseTool

    CREWAI_AVAILABLE = True
except ImportError:
    logger.warning("CrewAI not available, using fallback implementations")
    CREWAI_AVAILABLE = False

    class Agent:
        """Fallback Agent class when CrewAI is not available"""

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class Task:
        """Fallback Task class when CrewAI is not available"""

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class Crew:
        """Fallback Crew class when CrewAI is not available"""

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def kickoff(self, inputs=None):
            return {"result": "CrewAI not available - using fallback"}

    class Process:
        """Fallback Process class when CrewAI is not available"""

        sequential = "sequential"

    class BaseTool:
        """Fallback BaseTool class when CrewAI is not available"""

        name: str = "fallback_tool"
        description: str = "Fallback tool when CrewAI not available"

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def _run(self, *args, **kwargs):
            return "CrewAI not available - using fallback"


# Import LLM configuration
try:
    from app.services.llm_config import get_crewai_llm

    LLM_AVAILABLE = True
except ImportError:
    logger.warning("LLM configuration not available")
    LLM_AVAILABLE = False

    def get_crewai_llm():
        return None
