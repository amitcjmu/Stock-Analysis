"""
Modernization Agent - Base Module
Contains the core ModernizationAgent class and initialization logic.
"""

import logging
import uuid
from typing import Optional

from crewai import Agent

from app.services.agentic_intelligence.agent_reasoning_patterns import (
    AgentReasoningEngine,
)
from app.services.agentic_memory.agent_tools_functional import (
    create_functional_agent_tools,
)

logger = logging.getLogger(__name__)


class ModernizationAgent:
    """
    Agentic Modernization and Cloud Readiness Specialist that learns and applies modernization patterns.

    This agent specializes in:
    - Cloud readiness assessment based on architecture and technology stack
    - Modernization strategy recommendation using learned best practices
    - Migration complexity analysis considering dependencies and technical debt
    - Pattern discovery for successful modernization approaches
    - Learning from migration project outcomes and architectural decisions
    """

    def __init__(
        self,
        crewai_service,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        flow_id: Optional[uuid.UUID] = None,
    ):
        self.crewai_service = crewai_service
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.flow_id = flow_id

        # Initialize reasoning engine
        self.reasoning_engine = AgentReasoningEngine(
            None,
            client_account_id,
            engagement_id,
        )

        # Get configured LLM
        try:
            from app.services.llm_config import get_crewai_llm

            self.llm = get_crewai_llm()
            logger.info("✅ Modernization Agent using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM: {e}")
            self.llm = getattr(crewai_service, "llm", None)

        # Create agent tools for memory access
        self.agent_tools = create_functional_agent_tools(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            agent_name="Modernization Agent",
            flow_id=flow_id,
        )

        logger.info(
            f"✅ Modernization Agent initialized with {len(self.agent_tools)} memory tools"
        )

    def create_modernization_agent(self) -> Agent:
        """Create the CrewAI agent specialized in modernization and cloud readiness with memory tools"""

        agent = Agent(
            role="Cloud Modernization and Architecture Specialist",
            goal=(
                "Assess modernization potential and cloud readiness using evidence-based analysis "
                "and learned migration patterns"
            ),
            backstory="""You are a cloud architecture and modernization expert who specializes in
            evaluating IT assets for cloud migration and modernization opportunities through intelligent
            analysis rather than generic migration frameworks.

            Your expertise includes cloud readiness assessment, modernization strategy development,
            migration complexity analysis, technology stack evaluation, cost-benefit analysis, and
            DevOps automation readiness. You apply learned patterns and discover new modernization
            opportunities.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=self.agent_tools,
            memory=False,
            max_iter=3,
            max_execution_time=60,
        )

        return agent
