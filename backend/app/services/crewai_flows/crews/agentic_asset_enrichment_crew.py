"""
Agentic Asset Enrichment Crew - True AI-Powered Asset Analysis

This crew demonstrates the transition from rule-based systems to true agentic intelligence.
Instead of hard-coded rules, agents use memory, pattern discovery, and reasoning tools
to enrich assets with business intelligence.

Key Features:
- Pattern-based learning from previous enrichments
- Multi-tier memory integration (conversational, episodic, semantic)
- Agent tools for data querying and pattern discovery
- Reasoning-based asset enrichment (not rule-based)
- Multi-tenant pattern isolation
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from crewai import Agent, Crew, Process, Task

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

try:
    from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
    from app.services.agentic_memory import ThreeTierMemoryManager
    from app.services.agentic_memory.agent_tools import create_agent_tools

    AGENTIC_MEMORY_AVAILABLE = True
except ImportError:
    AGENTIC_MEMORY_AVAILABLE = False

logger = logging.getLogger(__name__)


class AgenticAssetEnrichmentCrew:
    """
    CrewAI crew that performs truly agentic asset enrichment using:
    - Three-tier memory architecture
    - Pattern search and discovery tools
    - Reasoning-based business value assessment
    - Learning from previous enrichment decisions
    """

    def __init__(
        self,
        crewai_service,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        flow_id: uuid.UUID,
    ):
        self.crewai_service = crewai_service
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.flow_id = flow_id

        # Initialize three-tier memory system
        self.memory_manager = ThreeTierMemoryManager(client_account_id, engagement_id)

        # Get LLM configuration
        try:
            from app.services.llm_config import get_crewai_llm

            self.llm_model = get_crewai_llm()
            logger.info("✅ Using configured LLM for agentic enrichment")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM: {e}")
            self.llm_model = getattr(crewai_service, "llm", None)

        logger.info(
            f"✅ Agentic Asset Enrichment Crew initialized for engagement {engagement_id}"
        )

    def create_agents(self) -> List[Agent]:
        """Create agents with memory and reasoning tools"""

        if not CREWAI_AVAILABLE or not AGENTIC_MEMORY_AVAILABLE:
            logger.error("CrewAI or Agentic Memory not available")
            return []

        # Create agent tools for pattern-based reasoning
        tools = create_agent_tools(
            client_account_id=self.client_account_id,
            engagement_id=self.engagement_id,
            agent_name="Asset Intelligence Agent",
            flow_id=self.flow_id,
        )

        # Asset Intelligence Agent - Uses patterns and memory for business value assessment
        asset_intelligence_agent = Agent(
            role="Asset Intelligence Specialist",
            goal="Analyze assets using discovered patterns and memory to determine "
            "business value, risk, and modernization potential",
            backstory="""You are an expert asset intelligence specialist who uses pattern recognition
            and institutional memory to assess business value and migration readiness. You learn from
            previous enrichment decisions and discover new patterns during analysis. Your intelligence
            comes from reasoning, not hard-coded rules.""",
            tools=tools,
            memory=True,  # Enable CrewAI memory (Tier 1)
            llm=self.llm_model,
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            max_execution_time=300,
        )

        # Pattern Discovery Agent - Identifies new patterns for future learning
        pattern_discovery_agent = Agent(
            role="Pattern Discovery Specialist",
            goal="Identify and record new patterns in asset data that can improve future enrichment decisions",
            backstory="""You are a pattern recognition expert who analyzes asset enrichment results
            to discover repeatable patterns. You look for correlations between asset attributes and
            business outcomes, recording insights for future agent reasoning.""",
            tools=tools,
            memory=True,  # Enable CrewAI memory (Tier 1)
            llm=self.llm_model,
            verbose=True,
            allow_delegation=False,
            max_iter=2,
            max_execution_time=300,
        )

        return [asset_intelligence_agent, pattern_discovery_agent]

    def create_tasks(
        self, agents: List[Agent], assets_data: List[Dict[str, Any]]
    ) -> List[Task]:
        """Create tasks for agentic asset enrichment"""

        if len(agents) < 2:
            logger.error("Insufficient agents for agentic enrichment")
            return []

        asset_intelligence_agent = agents[0]
        pattern_discovery_agent = agents[1]

        # Prepare asset summary for agents
        asset_summary = {
            "total_assets": len(assets_data),
            "asset_types": list(
                set(asset.get("asset_type", "unknown") for asset in assets_data)
            ),
            "environments": list(
                set(
                    asset.get("environment", "unknown")
                    for asset in assets_data
                    if asset.get("environment")
                )
            ),
            "sample_assets": assets_data[:3],  # Show sample for context
        }

        # Task 1: Intelligent Asset Enrichment
        # This is not SQL, it's a task description for an AI agent
        enrichment_task = Task(  # nosec B608
            description=f"""  # nosec B608
            Perform intelligent asset enrichment for {len(assets_data)} assets using pattern-based reasoning.

            Asset Overview:
            - Total assets: {asset_summary['total_assets']}
            - Asset types: {asset_summary['asset_types']}
            - Environments: {asset_summary['environments']}

            Your Process:
            1. Use the pattern_search tool to find existing patterns that might apply to these assets
            2. Use the asset_data_query tool to examine asset characteristics and relationships
            3. Apply reasoning (not rules) to assess business value, risk, and modernization potential
            4. Use the asset_enrichment tool to update assets with your intelligence
            5. Document your reasoning process for each enrichment decision

            Focus on:
            - Business value assessment based on asset characteristics and usage patterns
            - Risk evaluation considering technology, dependencies, and criticality
            - Modernization potential analysis based on current state and cloud readiness
            - Pattern recognition for similar assets

            Remember: Your intelligence comes from reasoning and pattern recognition, not hard-coded rules.
            Learn from existing patterns and apply contextual judgment to each asset.
            """,
            expected_output="""A comprehensive enrichment report containing:
            1. Summary of patterns discovered and applied
            2. Business value scores with reasoning for each asset category
            3. Risk assessments and mitigation considerations
            4. Modernization recommendations with priority rankings
            5. New patterns identified during analysis
            6. Confidence levels and validation recommendations""",
            agent=asset_intelligence_agent,
            max_execution_time=300,
        )

        # Task 2: Pattern Discovery and Learning
        pattern_discovery_task = Task(
            description="""
            Analyze the enrichment results to discover and record new patterns for future learning.

            Your Process:
            1. Use the asset_data_query tool to examine enriched assets and identify correlations
            2. Look for repeatable patterns in business value assignments, risk assessments, and modernization decisions
            3. Use the pattern_recording tool to capture significant patterns you discover
            4. Validate patterns against multiple asset examples
            5. Assess pattern confidence based on evidence strength

            Pattern Types to Consider:
            - Business value indicators (what makes an asset valuable?)
            - Risk factors (what increases migration risk?)
            - Modernization opportunities (what indicates cloud readiness?)
            - Technology correlations (how do tech stacks relate to outcomes?)
            - Naming conventions and organizational patterns

            Record patterns with:
            - Clear descriptions of when they apply
            - Confidence scores based on evidence
            - Supporting asset examples
            - Validation recommendations
            """,
            expected_output="""A pattern discovery report containing:
            1. List of new patterns discovered with confidence scores
            2. Evidence supporting each pattern (asset examples)
            3. Recommendations for pattern validation
            4. Suggestions for improving future enrichment processes
            5. Insights about asset portfolio characteristics""",
            agent=pattern_discovery_agent,
            max_execution_time=300,
        )

        return [enrichment_task, pattern_discovery_task]

    def create_crew(self, assets_data: List[Dict[str, Any]]) -> Optional[Crew]:
        """Create the agentic enrichment crew"""

        if not CREWAI_AVAILABLE or not AGENTIC_MEMORY_AVAILABLE:
            logger.error("Cannot create agentic crew - dependencies not available")
            return None

        agents = self.create_agents()
        tasks = self.create_tasks(agents, assets_data)

        if not agents or not tasks:
            logger.error("Failed to create agents or tasks for agentic crew")
            return None

        crew_config = {
            "agents": agents,
            "tasks": tasks,
            "process": Process.sequential,
            "memory": True,  # Enable crew-level memory
            "verbose": True,
            "max_execution_time": 300,  # 5 minutes total
        }

        # Add manager LLM if hierarchical process is needed
        if len(agents) > 2:
            crew_config.update(
                {
                    "process": Process.hierarchical,
                    "manager_llm": self.llm,
                    "planning": True,
                    "planning_llm": self.llm,
                }
            )

        logger.info(
            f"✅ Creating Agentic Asset Enrichment Crew with {len(agents)} agents and {len(tasks)} tasks"
        )
        return Crew(**crew_config)

    async def enrich_assets_with_agents(
        self, assets_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform agentic asset enrichment using the crew

        This method demonstrates true agentic intelligence by:
        1. Using memory to learn from previous enrichments
        2. Applying pattern-based reasoning instead of rules
        3. Recording new discoveries for future learning
        4. Providing reasoning transparency for validation
        """

        try:
            logger.info(f"🤖 Starting agentic enrichment for {len(assets_data)} assets")

            # Create crew
            crew = self.create_crew(assets_data)
            if not crew:
                return {
                    "status": "error",
                    "message": "Failed to create agentic enrichment crew",
                    "enriched_assets": 0,
                }

            # Execute crew
            start_time = datetime.utcnow()
            result = crew.kickoff()
            end_time = datetime.utcnow()

            # Process results
            execution_time = (end_time - start_time).total_seconds()

            response = {
                "status": "success",
                "message": "Agentic asset enrichment completed",
                "enriched_assets": len(assets_data),
                "execution_time_seconds": execution_time,
                "crew_result": str(result)[:1000],  # Truncate for readability
                "intelligence_source": "CrewAI agents with pattern-based reasoning",
                "memory_tiers_used": ["conversational", "semantic"],
                "patterns_discovered": "See pattern discovery task results",
                "validation_required": "Human validation recommended for new patterns",
            }

            logger.info(
                f"✅ Agentic enrichment completed in {execution_time:.1f} seconds"
            )
            return response

        except Exception as e:
            logger.error(f"Agentic enrichment failed: {e}")
            return {
                "status": "error",
                "message": f"Agentic enrichment error: {str(e)}",
                "enriched_assets": 0,
            }


def create_agentic_asset_enrichment_crew(
    crewai_service,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    flow_id: uuid.UUID,
    state: UnifiedDiscoveryFlowState,
) -> Optional[Crew]:
    """
    Factory function to create agentic asset enrichment crew

    This function demonstrates the architectural shift from rule-based to agentic systems:
    - No hard-coded business logic
    - Agent reasoning with memory and tools
    - Pattern discovery and learning
    - Multi-tenant context awareness
    """

    try:
        logger.info("🚀 Creating Agentic Asset Enrichment Crew")

        enrichment_crew = AgenticAssetEnrichmentCrew(
            crewai_service=crewai_service,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            flow_id=flow_id,
        )

        # Convert state data to asset format
        assets_data = []
        if hasattr(state, "raw_data") and state.raw_data:
            assets_data = state.raw_data[:10]  # Limit for testing

        crew = enrichment_crew.create_crew(assets_data)

        if crew:
            logger.info("✅ Agentic Asset Enrichment Crew created successfully")
        else:
            logger.error("❌ Failed to create agentic crew")

        return crew

    except Exception as e:
        logger.error(f"Failed to create agentic enrichment crew: {e}")
        return None
