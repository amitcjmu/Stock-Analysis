"""
Base Crew for Discovery and Collection flows
Provides common functionality for CrewAI-based services
"""

import logging
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

try:
    from crewai import Agent, Crew, Process, Task
    from litellm import completion

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = Crew = Process = Task = object

logger = logging.getLogger(__name__)


class BaseDiscoveryCrew(ABC):
    """Base class for CrewAI-based discovery and collection crews"""

    def __init__(
        self,
        name: str = "base_crew",
        description: str = "Base crew for discovery",
        process: Any = None,
        verbose: bool = True,
        memory: bool = False,
        cache: bool = False,
    ):
        self.name = name
        self.description = description
        self.verbose = verbose
        self.agents: List[Any] = []
        self.tasks: List[Any] = []
        self.crew: Optional[Any] = None

        if CREWAI_AVAILABLE:
            self.process = process or Process.sequential
            self.memory = memory
            self.cache = cache
            self.llm = self._get_llm()
        else:
            logger.warning("CrewAI not available - crews will return mock results")
            self.llm = None

    def _get_llm(self):
        """Get LLM instance for agents"""
        if not CREWAI_AVAILABLE:
            return None

        try:
            # Using the same LLM configuration as the rest of the system
            import os

            model = os.getenv("LLM_MODEL", "gpt-4")
            return lambda prompt: completion(
                model=model, messages=[{"role": "user", "content": prompt}]
            )
        except Exception as e:
            logger.warning(f"Could not initialize LLM: {e}")
            return None

    @abstractmethod
    def create_agents(self) -> List[Any]:
        """Create agents for the crew - must be implemented by subclasses"""
        pass

    @abstractmethod
    def create_tasks(self, inputs: Dict[str, Any]) -> List[Task]:
        """Create tasks for the crew - must be implemented by subclasses"""
        pass

    @abstractmethod
    def process_results(self, raw_results: Any) -> Dict[str, Any]:
        """Process crew results - must be implemented by subclasses"""
        pass

    async def kickoff_async(self, inputs: Dict[str, Any]) -> Any:
        """Execute the crew asynchronously"""
        if not CREWAI_AVAILABLE:
            logger.warning("CrewAI not available - returning mock results")
            return self._get_mock_results(inputs)

        try:
            # Create agents if not already created
            if not self.agents:
                self.agents = self.create_agents()

            # Create tasks with inputs
            self.tasks = self.create_tasks(inputs)

            # Create and execute crew
            self.crew = Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=self.process,
                verbose=self.verbose,
                memory=self.memory,
                cache=self.cache,
            )

            # Execute crew
            result = await self.crew.kickoff_async(inputs=inputs)
            return result

        except Exception as e:
            logger.error(f"Error executing crew {self.name}: {e}")
            return self._get_mock_results(inputs)

    def kickoff(self, inputs: Dict[str, Any]) -> Any:
        """Execute the crew synchronously"""
        if not CREWAI_AVAILABLE:
            logger.warning("CrewAI not available - returning mock results")
            return self._get_mock_results(inputs)

        try:
            # Create agents if not already created
            if not self.agents:
                self.agents = self.create_agents()

            # Create tasks with inputs
            self.tasks = self.create_tasks(inputs)

            # Create and execute crew
            self.crew = Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=self.process,
                verbose=self.verbose,
                memory=self.memory,
                cache=self.cache,
            )

            # Execute crew
            result = self.crew.kickoff(inputs=inputs)
            return result

        except Exception as e:
            logger.error(f"Error executing crew {self.name}: {e}")
            return self._get_mock_results(inputs)

    def _get_mock_results(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Return mock results when CrewAI is not available"""
        return {
            "status": "mock",
            "message": "CrewAI not available - returning mock results",
            "inputs": inputs,
            "crew_name": self.name,
        }
