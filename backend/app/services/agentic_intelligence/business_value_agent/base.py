"""
Business Value Agent - Base Module
Contains the core BusinessValueAgent class and initialization logic.
"""

import logging
import uuid
from typing import Optional

# CrewAI imports
from crewai import Agent

# Internal imports
from app.services.agentic_intelligence.agent_reasoning_patterns import (
    AgentReasoningEngine,
)
from app.services.agentic_memory.agent_tools_functional import (
    create_functional_agent_tools,
)

logger = logging.getLogger(__name__)


class BusinessValueAgent:
    """
    Agentic Business Value Analyst that learns and applies business value patterns.

    Unlike rule-based systems, this agent:
    - Discovers patterns from data and stores them in memory
    - Uses evidence-based reasoning with confidence scores
    - Learns from previous analyses and user feedback
    - Adapts its reasoning based on accumulated knowledge
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
        # Note: TenantMemoryManager will be initialized per-method with AsyncSession
        self.reasoning_engine = AgentReasoningEngine(
            None,
            client_account_id,
            engagement_id,  # Will use TenantMemoryManager in methods
        )

        # Get configured LLM
        try:
            from app.services.llm_config import get_crewai_llm

            self.llm = get_crewai_llm()
            logger.info("✅ Business Value Agent using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM: {e}")
            self.llm = getattr(crewai_service, "llm", None)

        # Create agent tools for memory access
        self.agent_tools = create_functional_agent_tools(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            agent_name="Business Value Agent",
            flow_id=flow_id,
        )

        logger.info(
            f"✅ Business Value Agent initialized with {len(self.agent_tools)} memory tools"
        )

    def create_business_value_agent(self) -> Agent:
        """Create the CrewAI agent with agentic memory tools"""

        agent = Agent(
            role="Business Value Intelligence Analyst",
            goal="Analyze assets to determine their business value using evidence-based reasoning and learned patterns",
            backstory="""You are an intelligent business analyst who specializes in evaluating
            the business value of IT assets. Instead of following rigid rules, you analyze evidence,
            discover patterns, and learn from experience.

            Your approach:
            1. Search your memory for relevant business value patterns from previous analyses
            2. Examine asset characteristics for business value indicators
            3. Apply discovered patterns and reasoning to determine business value scores
            4. Record new patterns you discover for future use
            5. Enrich assets with your analysis and reasoning

            You have access to tools that let you:
            - Search for patterns you've learned before
            - Query asset data to gather evidence
            - Record new patterns you discover
            - Enrich assets with your business value analysis

            Always provide detailed reasoning for your conclusions and be transparent about
            your confidence levels. Your goal is to learn and improve with each analysis.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=self.agent_tools,
            memory=False,  # Per ADR-024: Use TenantMemoryManager for enterprise memory
            max_iter=3,
            max_execution_time=60,
        )

        return agent
