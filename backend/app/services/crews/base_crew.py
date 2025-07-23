"""
Base Crew implementation with context awareness and standard patterns
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from crewai import Crew, Process, Task

from app.core.context import get_current_context
from app.services.llm_config import get_crewai_llm

logger = logging.getLogger(__name__)


class BaseDiscoveryCrew(ABC):
    """
    Base class for all discovery crews.
    Provides:
    - Standard crew initialization
    - Context-aware execution
    - Task creation patterns
    - Result handling
    """

    def __init__(
        self,
        name: str,
        description: str,
        process: Process = Process.sequential,
        verbose: bool = True,
        memory: bool = True,
        cache: bool = True,
        max_rpm: int = 100,
        share_crew: bool = False,
    ):
        """Initialize base crew with configuration"""
        self.name = name
        self.description = description

        # Store context safely without triggering during module import
        try:
            self.context = get_current_context()
        except Exception:
            # Context may not be available during import/discovery
            self.context = None

        self.llm = get_crewai_llm()

        # Crew configuration
        self.process = process
        self.verbose = verbose
        self.memory = memory
        self.cache = cache
        self.max_rpm = max_rpm
        self.share_crew = share_crew

        # Will be populated by subclasses
        self.agents: List[Any] = []
        self.tasks: List[Task] = []
        self.crew: Optional[Crew] = None

    @abstractmethod
    def create_agents(self) -> List[Any]:
        """Create and return agents for this crew"""
        pass

    @abstractmethod
    def create_tasks(self, inputs: Dict[str, Any]) -> List[Task]:
        """Create and return tasks for this crew"""
        pass

    def initialize_crew(self, inputs: Dict[str, Any]) -> Crew:
        """Initialize the crew with agents and tasks"""
        # Create agents
        self.agents = self.create_agents()
        if not self.agents:
            raise ValueError(f"No agents created for crew {self.name}")

        # Create tasks
        self.tasks = self.create_tasks(inputs)
        if not self.tasks:
            raise ValueError(f"No tasks created for crew {self.name}")

        # Create crew
        self.crew = Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=self.process,
            verbose=self.verbose,
            memory=self.memory,
            cache=self.cache,
            max_rpm=self.max_rpm,
            share_crew=self.share_crew,
        )

        logger.info(
            f"Initialized crew: {self.name} with {len(self.agents)} agents and {len(self.tasks)} tasks"
        )
        return self.crew

    def execute(self, inputs: Dict[str, Any]) -> Any:
        """Execute the crew with given inputs"""
        try:
            # Ensure context is available for execution
            if not self.context:
                try:
                    self.context = get_current_context()
                except Exception:
                    raise ValueError("No context available for multi-tenant execution")

            logger.info(
                f"Executing crew {self.name} for client {self.context.client_account_id}"
            )

            # Initialize crew if not already done
            if not self.crew:
                self.initialize_crew(inputs)

            # Execute crew
            result = self.crew.kickoff(inputs=inputs)

            logger.info(f"Crew {self.name} completed successfully")
            return self.process_results(result)

        except Exception as e:
            logger.error(f"Crew {self.name} execution failed: {e}")
            raise

    def process_results(self, raw_results: Any) -> Dict[str, Any]:
        """Process crew results into standard format"""
        return {
            "crew_name": self.name,
            "status": "completed",
            "results": raw_results,
            "context": {
                "client_account_id": (
                    self.context.client_account_id if self.context else None
                ),
                "engagement_id": self.context.engagement_id if self.context else None,
            },
        }

    async def kickoff_async(self, inputs: Dict[str, Any]) -> Any:
        """Execute the crew asynchronously with given inputs"""
        try:
            # Ensure context is available for execution
            if not self.context:
                try:
                    self.context = get_current_context()
                except:
                    raise ValueError("No context available for multi-tenant execution")

            logger.info(
                f"Executing crew {self.name} asynchronously for client {self.context.client_account_id}"
            )

            # Initialize crew if not already done
            if not self.crew:
                self.initialize_crew(inputs)

            # Execute crew in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.crew.kickoff, inputs)

            logger.info(f"Crew {self.name} completed successfully (async)")
            return result

        except Exception as e:
            logger.error(f"Crew {self.name} async execution failed: {e}")
            raise
