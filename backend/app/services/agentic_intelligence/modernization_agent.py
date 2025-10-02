"""
Modernization Agent - Agentic Intelligence Implementation

This agent analyzes assets to determine their modernization potential and cloud readiness using:
1. Real CrewAI agent reasoning instead of static modernization matrices
2. Pattern learning from successful migration projects and architectural decisions
3. Evidence-based cloud readiness scoring with detailed technical analysis
4. Integration with three-tier memory system for continuous modernization intelligence

The agent uses agentic memory tools to:
- Search for existing modernization patterns and successful migration strategies
- Record new modernization patterns discovered during analysis
- Learn from migration successes and failures across different technology stacks
- Build institutional knowledge about cloud adoption strategies and best practices
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# CrewAI imports
from crewai import Agent, Crew, Process, Task

# Internal imports
from app.services.agentic_intelligence.agent_reasoning_patterns import (
    AgentReasoning,
    AgentReasoningEngine,
)
from app.services.crewai_flows.memory.tenant_memory_manager import (
    TenantMemoryManager,
    LearningScope,
)
from app.services.agentic_memory.agent_tools_functional import (
    create_functional_agent_tools,
)
from sqlalchemy.ext.asyncio import AsyncSession

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

            Your expertise includes:
            - Cloud readiness assessment based on architecture patterns and technology stacks
            - Modernization strategy development using containerization, microservices, and cloud-native patterns
            - Migration complexity analysis considering technical debt, dependencies, and integration points
            - Technology stack evaluation for cloud compatibility and optimization opportunities
            - Cost-benefit analysis for different modernization approaches (lift-and-shift, re-platform, refactor)
            - DevOps and automation readiness assessment for CI/CD pipeline integration

            Your analytical approach:
            1. Search your memory for relevant modernization patterns from successful migration projects
            2. Analyze technology stacks for cloud compatibility and modernization readiness
            3. Evaluate architecture patterns for containerization and microservices potential
            4. Assess data architecture for cloud database and storage optimization
            5. Apply learned patterns and discover new modernization opportunities
            6. Record new modernization patterns for future project intelligence
            7. Provide modernization scores with detailed technical recommendations and migration strategies

            You have access to memory tools that allow you to:
            - Search for modernization patterns and successful migration strategies from previous projects
            - Query asset data to identify similar systems with known modernization outcomes
            - Record new modernization patterns and architectural insights you discover
            - Enrich assets with comprehensive modernization assessments and cloud readiness scores

            Always provide specific, actionable modernization recommendations with clear migration paths.
            Focus on practical modernization strategies that balance effort, risk, and business value.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=self.agent_tools,
            memory=False,  # Per ADR-024: Use TenantMemoryManager for enterprise memory
            max_iter=3,
            max_execution_time=60,
        )

        return agent

    def create_modernization_assessment_task(self, asset_data: Dict[str, Any]) -> Task:
        """Create a task for comprehensive modernization assessment of an asset"""

        asset_summary = {
            "name": asset_data.get("name"),
            "asset_type": asset_data.get("asset_type"),
            "technology_stack": asset_data.get("technology_stack"),
            "environment": asset_data.get("environment"),
            "business_criticality": asset_data.get("business_criticality"),
            "architecture_style": asset_data.get("architecture_style"),
            "integration_complexity": asset_data.get("integration_complexity"),
            "data_volume": asset_data.get("data_volume"),
        }

        # This is not SQL, it's a task description for an AI agent
        asset_details_json = json.dumps(asset_summary, indent=2)
        task_description = (  # nosec B608
            "Conduct a comprehensive modernization assessment for this asset using your cloud "
            "architecture intelligence and memory tools:\n\n"
            "Asset Details:\n" + asset_details_json + "\n\n"  # nosec B608
            "Complete Modernization Assessment Process:\n\n"
            "1. SEARCH FOR MODERNIZATION PATTERNS:\n"
            "   Use your pattern search tool to find relevant modernization patterns and successful "
            "migration strategies from previous projects.\n"
            "   Search for: cloud migration strategies, containerization patterns, microservices "
            "transformation, database modernization.\n\n"
            "2. TECHNOLOGY STACK ANALYSIS:\n"
            "   Use your asset query tool to examine similar technology stacks and identify:\n"
            "   - Cloud compatibility and native support for the technology stack\n"
            "   - Containerization readiness and Docker/Kubernetes potential\n"
            "   - Microservices decomposition opportunities for monolithic applications\n"
            "   - Database modernization options (managed services, cloud-native databases)\n"
            "   - Compare with other successfully modernized systems\n\n"
            "3. CLOUD READINESS ASSESSMENT:\n"
            "   Evaluate cloud readiness factors including:\n"
            "   - Stateless vs. stateful architecture considerations\n"
            "   - Configuration management and externalization readiness\n"
            "   - Service discovery and load balancing requirements\n"
            "   - Data persistence and storage optimization opportunities\n"
            "   - Network and security architecture cloud compatibility\n\n"
            "4. MODERNIZATION STRATEGY ANALYSIS:\n"
            "   Assess different modernization approaches:\n"
            "   - Lift-and-shift: Minimal changes, quick migration, cost analysis\n"
            "   - Re-platform: Cloud-optimized deployment with managed services\n"
            "   - Refactor: Containerization, microservices, cloud-native patterns\n"
            "   - Rebuild: Complete redesign using cloud-native architecture\n"
            "   - Migration complexity and effort estimation for each approach\n\n"
            "5. CONTAINERIZATION POTENTIAL:\n"
            "   Determine containerization readiness:\n"
            "   - Application architecture suitability for containers\n"
            "   - Dependency management and external service integration\n"
            "   - Configuration and secret management requirements\n"
            "   - Orchestration needs for Kubernetes deployment\n"
            "   - CI/CD pipeline integration opportunities\n\n"
            "6. MODERNIZATION SCORING:\n"
            "   Provide a comprehensive modernization assessment:\n"
            "   - Cloud Readiness Score (0-100): Current readiness for cloud deployment\n"
            "   - Modernization Potential (Low/Medium/High): Overall modernization opportunity\n"
            "   - Effort Estimation (Low/Medium/High): Resources required for modernization\n"
            "   - Business Impact (Low/Medium/High): Expected benefits from modernization\n\n"
            "7. PATTERN DISCOVERY:\n"
            "   If you identify new modernization patterns or architectural insights, use your pattern recording tool "
            "to save them for future project intelligence.\n\n"
            "8. ASSET ENRICHMENT:\n"
            "   Use your asset enrichment tool to update the asset with:\n"
            "   - Cloud readiness score and modernization potential assessment\n"
            "   - Recommended modernization strategy and migration approach\n"
            "   - Technical requirements and architecture recommendations\n"
            "   - Effort estimation and timeline considerations\n\n"
            "Provide your modernization assessment in this format:\n"
            "Cloud Readiness Score: [0-100]\n"
            "Modernization Potential: [Low/Medium/High]\n"
            "Recommended Strategy: [Lift-and-shift/Re-platform/Refactor/Rebuild]\n"
            "Migration Effort: [Low/Medium/High]\n"
            "Technical Confidence: [High/Medium/Low]\n"
            "Architecture Assessment: [Key architectural strengths and modernization opportunities]\n"
            "Technology Compatibility: [Cloud service compatibility and optimization opportunities]\n"
            "Containerization Readiness: [Container deployment feasibility and requirements]\n"
            "Modernization Patterns Applied: [Patterns used from memory]\n"
            "New Patterns Discovered: [New modernization patterns identified]\n"
            "Immediate Modernization Steps: [Quick wins and initial modernization actions]\n"
            "Long-term Migration Strategy: [Comprehensive modernization roadmap]\n"
            "Expected Benefits: [Business and technical benefits from modernization]\n"
        )

        task = Task(
            description=task_description,
            expected_output="""
            Comprehensive Modernization Assessment Report with:
            - Cloud readiness score (0-100) with detailed technical analysis
            - Modernization potential classification and recommended strategy
            - Technical architecture assessment for cloud compatibility
            - Containerization readiness and Kubernetes deployment analysis
            - Migration effort estimation and timeline considerations
            - New modernization patterns discovered and recorded
            - Asset enrichment confirmation with modernization metadata
            - Detailed modernization roadmap with immediate and long-term recommendations
            """,
            agent=self.create_modernization_agent(),  # Fix: Assign agent to task
            max_execution_time=50,
        )

        return task

    def create_modernization_crew(self, asset_data: Dict[str, Any]) -> Crew:
        """Create a crew for comprehensive modernization assessment"""

        agent = self.create_modernization_agent()
        task = self.create_modernization_assessment_task(asset_data)

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
            memory=False,  # Per ADR-024: Use TenantMemoryManager for enterprise memory
            max_execution_time=90,
        )

        return crew

    async def analyze_modernization_potential(
        self, asset_data: Dict[str, Any], db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Main method to analyze modernization potential of an asset using agentic intelligence.

        This method:
        1. Retrieves historical modernization patterns from TenantMemoryManager
        2. Creates a specialized modernization crew with architectural intelligence tools
        3. Executes comprehensive cloud readiness and modernization strategy analysis
        4. Stores discovered patterns back to TenantMemoryManager
        5. Returns structured results with modernization scores, strategies, and migration roadmaps

        Args:
            asset_data: Asset data to analyze
            db: Database session for TenantMemoryManager

        Returns:
            Modernization assessment with scores and recommendations
        """
        try:
            logger.info(
                f"☁️ Starting agentic modernization analysis for asset: {asset_data.get('name')}"
            )

            # Step 1: Initialize TenantMemoryManager
            memory_manager = TenantMemoryManager(
                crewai_service=self.crewai_service, database_session=db
            )

            # Step 2: Retrieve historical modernization patterns
            logger.info("📚 Retrieving historical modernization patterns...")
            query_context = {
                "asset_type": asset_data.get("asset_type"),
                "technology_stack": asset_data.get("technology_stack"),
                "architecture_style": asset_data.get("architecture_style"),
            }

            historical_patterns = await memory_manager.retrieve_similar_patterns(
                client_account_id=int(self.client_account_id),
                engagement_id=int(self.engagement_id),
                pattern_type="modernization_strategy",
                query_context=query_context,
                limit=10,
            )

            logger.info(f"✅ Found {len(historical_patterns)} historical patterns")

            # Step 3: Create and execute the modernization crew
            # TODO: Pass historical_patterns to crew context
            crew = self.create_modernization_crew(asset_data)

            # Execute the crew (this will run the agent with all memory tools)
            result = crew.kickoff()

            # Parse the agent's output
            parsed_result = self._parse_modernization_output(result, asset_data)

            # Step 4: Store discovered patterns if analysis was successful
            if parsed_result.get("cloud_readiness_score", 0) > 0:
                logger.info("💾 Storing discovered modernization patterns...")
                pattern_data = {
                    "name": f"modernization_analysis_{asset_data.get('name')}_{datetime.utcnow().isoformat()}",
                    "cloud_readiness_score": parsed_result.get("cloud_readiness_score"),
                    "modernization_potential": parsed_result.get(
                        "modernization_potential"
                    ),
                    "recommended_strategy": parsed_result.get("recommended_strategy"),
                    "asset_type": asset_data.get("asset_type"),
                    "technology_stack": asset_data.get("technology_stack"),
                    "architecture_assessment": parsed_result.get(
                        "architecture_assessment"
                    ),
                    "containerization_readiness": parsed_result.get(
                        "containerization_readiness"
                    ),
                    "historical_patterns_used": len(historical_patterns),
                    "confidence": parsed_result.get("technical_confidence", "medium"),
                }

                pattern_id = await memory_manager.store_learning(
                    client_account_id=int(self.client_account_id),
                    engagement_id=int(self.engagement_id),
                    scope=LearningScope.ENGAGEMENT,
                    pattern_type="modernization_strategy",
                    pattern_data=pattern_data,
                )

                logger.info(f"✅ Stored pattern with ID: {pattern_id}")
                parsed_result["pattern_id"] = pattern_id
                parsed_result["historical_patterns_used"] = len(historical_patterns)

            logger.info(
                f"✅ Modernization analysis completed - Cloud Readiness: "
                f"{parsed_result.get('cloud_readiness_score')}/100"
            )

            return parsed_result

        except Exception as e:
            logger.error(f"❌ Modernization analysis failed: {e}")

            # Fallback to reasoning engine if crew fails
            try:
                logger.info("🔄 Falling back to reasoning engine analysis")
                reasoning_result = (
                    await self.reasoning_engine.analyze_modernization_potential(
                        asset_data, "Modernization Agent"
                    )
                )
                return self._convert_reasoning_to_dict(reasoning_result)
            except Exception as fallback_error:
                logger.error(
                    f"❌ Fallback modernization analysis also failed: {fallback_error}"
                )
                return self._create_default_modernization_assessment(asset_data)

    def _parse_modernization_output(
        self, agent_output: str, asset_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse the agent's modernization assessment output into structured data"""
        try:
            result = {
                "agent_analysis_type": "modernization_assessment",
                "asset_id": asset_data.get("id"),
                "asset_name": asset_data.get("name"),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "agent_name": "Modernization Agent",
            }

            output_lower = str(agent_output).lower()

            # Extract cloud readiness score
            import re

            readiness_score_match = re.search(
                r"cloud readiness score:?\s*(\d+)", output_lower
            )
            result["cloud_readiness_score"] = (
                int(readiness_score_match.group(1)) if readiness_score_match else 50
            )

            # Extract modernization potential
            if "modernization potential: high" in output_lower:
                result["modernization_potential"] = "high"
            elif "modernization potential: medium" in output_lower:
                result["modernization_potential"] = "medium"
            else:
                result["modernization_potential"] = "low"

            # Extract recommended strategy
            if "recommended strategy: rebuild" in output_lower:
                result["recommended_strategy"] = "rebuild"
            elif "recommended strategy: refactor" in output_lower:
                result["recommended_strategy"] = "refactor"
            elif "recommended strategy: re-platform" in output_lower:
                result["recommended_strategy"] = "re-platform"
            else:
                result["recommended_strategy"] = "lift-and-shift"

            # Extract migration effort
            if "migration effort: high" in output_lower:
                result["migration_effort"] = "high"
            elif "migration effort: medium" in output_lower:
                result["migration_effort"] = "medium"
            else:
                result["migration_effort"] = "low"

            # Extract technical confidence
            if "high" in output_lower and "confidence" in output_lower:
                result["technical_confidence"] = "high"
            elif "medium" in output_lower and "confidence" in output_lower:
                result["technical_confidence"] = "medium"
            else:
                result["technical_confidence"] = "medium"

            # Extract architecture assessment
            arch_match = re.search(
                r"architecture assessment:(.+?)(?:technology compatibility|$)",
                output_lower,
                re.DOTALL,
            )
            if arch_match:
                result["architecture_assessment"] = arch_match.group(1).strip()
            else:
                result["architecture_assessment"] = (
                    "Architecture evaluated for cloud modernization compatibility"
                )

            # Extract technology compatibility
            tech_match = re.search(
                r"technology compatibility:(.+?)(?:containerization readiness|$)",
                output_lower,
                re.DOTALL,
            )
            if tech_match:
                result["technology_compatibility"] = tech_match.group(1).strip()
            else:
                result["technology_compatibility"] = (
                    "Technology stack assessed for cloud services integration"
                )

            # Extract containerization readiness
            container_match = re.search(
                r"containerization readiness:(.+?)(?:modernization patterns|$)",
                output_lower,
                re.DOTALL,
            )
            if container_match:
                result["containerization_readiness"] = container_match.group(1).strip()
            else:
                result["containerization_readiness"] = (
                    "Containerization potential evaluated"
                )

            # Extract immediate modernization steps
            immediate_match = re.search(
                r"immediate modernization steps:(.+?)(?:long-term migration|$)",
                output_lower,
                re.DOTALL,
            )
            if immediate_match:
                immediate_text = immediate_match.group(1).strip()
                result["immediate_steps"] = [
                    step.strip() for step in immediate_text.split("-") if step.strip()
                ]
            else:
                result["immediate_steps"] = [
                    "Assess current architecture",
                    "Plan containerization approach",
                ]

            # Extract long-term migration strategy
            longterm_match = re.search(
                r"long-term migration strategy:(.+?)(?:expected benefits|$)",
                output_lower,
                re.DOTALL,
            )
            if longterm_match:
                longterm_text = longterm_match.group(1).strip()
                result["migration_strategy"] = longterm_text
            else:
                result["migration_strategy"] = (
                    "Develop comprehensive modernization roadmap with phased approach"
                )

            # Extract expected benefits
            benefits_match = re.search(
                r"expected benefits:(.+?)$", output_lower, re.DOTALL
            )
            if benefits_match:
                benefits_text = benefits_match.group(1).strip()
                result["expected_benefits"] = [
                    benefit.strip()
                    for benefit in benefits_text.split("-")
                    if benefit.strip()
                ]
            else:
                result["expected_benefits"] = [
                    "Improved scalability",
                    "Enhanced operational efficiency",
                    "Reduced infrastructure costs",
                ]

            # Set enrichment status
            result["enrichment_status"] = "agent_analyzed"
            result["analysis_method"] = "agentic_intelligence"

            return result

        except Exception as e:
            logger.warning(f"Failed to parse modernization output: {e}")
            return self._create_default_modernization_assessment(asset_data)

    def _convert_reasoning_to_dict(self, reasoning: "AgentReasoning") -> Dict[str, Any]:
        """Convert AgentReasoning object to dictionary format for modernization assessment"""

        # Convert score to modernization potential
        modernization_potential = "low"
        if reasoning.score >= 80:
            modernization_potential = "high"
        elif reasoning.score >= 60:
            modernization_potential = "medium"

        return {
            "agent_analysis_type": "modernization_assessment",
            "cloud_readiness_score": reasoning.score,
            "modernization_potential": modernization_potential,
            "recommended_strategy": (
                "re-platform" if reasoning.score >= 70 else "lift-and-shift"
            ),
            "migration_effort": "medium",
            "technical_confidence": (
                "high"
                if reasoning.confidence >= 0.7
                else "medium" if reasoning.confidence >= 0.4 else "low"
            ),
            "architecture_assessment": reasoning.reasoning_summary,
            "evidence_count": len(reasoning.evidence_pieces),
            "patterns_applied": len(reasoning.applied_patterns),
            "patterns_discovered": len(reasoning.discovered_patterns),
            "immediate_steps": reasoning.recommendations[:3],  # First 3 as immediate
            "migration_strategy": reasoning.reasoning_summary,
            "expected_benefits": (
                reasoning.recommendations[3:]
                if len(reasoning.recommendations) > 3
                else ["Improved cloud efficiency"]
            ),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "enrichment_status": "agent_analyzed",
            "analysis_method": "reasoning_engine",
        }

    def _create_default_modernization_assessment(
        self, asset_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a default modernization assessment when both agent and reasoning engine fail"""
        return {
            "agent_analysis_type": "modernization_assessment",
            "cloud_readiness_score": 50,  # Default medium readiness
            "modernization_potential": "medium",
            "recommended_strategy": "lift-and-shift",
            "migration_effort": "medium",
            "technical_confidence": "low",
            "architecture_assessment": "Basic modernization assessment - detailed analysis unavailable",
            "technology_compatibility": "Standard cloud migration compatibility",
            "containerization_readiness": "Containerization potential requires further analysis",
            "immediate_steps": [
                "Assess current dependencies",
                "Plan migration approach",
            ],
            "migration_strategy": "Standard lift-and-shift with gradual optimization",
            "expected_benefits": [
                "Cloud infrastructure benefits",
                "Operational efficiency improvements",
            ],
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "enrichment_status": "basic",
            "analysis_method": "fallback",
        }


async def analyze_modernization_potential_agentic(
    asset_data: Dict[str, Any],
    crewai_service,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    db: AsyncSession,
    flow_id: Optional[uuid.UUID] = None,
) -> Dict[str, Any]:
    """
    Main function to analyze modernization potential using agentic intelligence.

    This function creates a ModernizationAgent and executes comprehensive cloud readiness
    and modernization strategy analysis with TenantMemoryManager integration.

    Args:
        asset_data: Asset data to analyze
        crewai_service: CrewAI service instance
        client_account_id: Client account ID
        engagement_id: Engagement ID
        db: Database session for TenantMemoryManager
        flow_id: Optional flow ID

    Returns:
        Modernization assessment with scores and recommendations
    """

    agent = ModernizationAgent(
        crewai_service=crewai_service,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_id=flow_id,
    )

    return await agent.analyze_modernization_potential(asset_data, db)


# Example usage pattern for integration with discovery flow
async def enrich_assets_with_modernization_intelligence(
    assets: List[Dict[str, Any]],
    crewai_service,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    db: AsyncSession,
    flow_id: Optional[uuid.UUID] = None,
) -> List[Dict[str, Any]]:
    """
    Enrich multiple assets with comprehensive modernization intelligence.

    This function processes assets in batches and enriches them with:
    - Cloud readiness scores (0-100)
    - Modernization potential and recommended strategies
    - Architecture assessment and containerization readiness
    - Migration effort estimation and timeline planning
    - Immediate modernization steps and long-term roadmaps

    Args:
        assets: List of assets to analyze
        crewai_service: CrewAI service instance
        client_account_id: Client account ID
        engagement_id: Engagement ID
        db: Database session for TenantMemoryManager
        flow_id: Optional flow ID

    Returns:
        List of enriched assets with modernization assessments
    """

    enriched_assets = []

    # Initialize the modernization agent once for batch processing
    agent = ModernizationAgent(
        crewai_service=crewai_service,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_id=flow_id,
    )

    for i, asset in enumerate(assets):
        try:
            logger.info(
                f"☁️ Analyzing modernization potential for asset {i+1}/{len(assets)}: {asset.get('name')}"
            )

            # Perform agentic modernization analysis with TenantMemoryManager
            analysis_result = await agent.analyze_modernization_potential(asset, db)

            # Merge analysis results with asset data
            enriched_asset = {**asset}
            enriched_asset.update(
                {
                    "cloud_readiness_score": analysis_result.get(
                        "cloud_readiness_score"
                    ),
                    "modernization_potential": analysis_result.get(
                        "modernization_potential"
                    ),
                    "recommended_migration_strategy": analysis_result.get(
                        "recommended_strategy"
                    ),
                    "migration_effort_estimate": analysis_result.get(
                        "migration_effort"
                    ),
                    "architecture_assessment": analysis_result.get(
                        "architecture_assessment"
                    ),
                    "containerization_readiness": analysis_result.get(
                        "containerization_readiness"
                    ),
                    "modernization_recommendations": analysis_result.get(
                        "immediate_steps"
                    ),
                    "migration_roadmap": analysis_result.get("migration_strategy"),
                    "expected_modernization_benefits": analysis_result.get(
                        "expected_benefits"
                    ),
                    "enrichment_status": "agent_enriched",
                    "last_enriched_at": datetime.utcnow(),
                    "last_enriched_by_agent": "Modernization Agent",
                }
            )

            enriched_assets.append(enriched_asset)

            logger.info(
                f"✅ Modernization analysis completed - Readiness: {analysis_result.get('cloud_readiness_score')}/100"
            )

        except Exception as e:
            logger.error(
                f"❌ Failed to analyze modernization for asset {asset.get('name')}: {e}"
            )

            # Add asset with basic modernization assessment
            enriched_asset = {**asset}
            enriched_asset.update(
                {
                    "cloud_readiness_score": 50,  # Default medium readiness
                    "modernization_potential": "medium",
                    "recommended_migration_strategy": "lift-and-shift",
                    "modernization_analysis_reasoning": "Modernization analysis failed - using default assessment",
                    "enrichment_status": "basic",
                    "last_enriched_at": datetime.utcnow(),
                }
            )
            enriched_assets.append(enriched_asset)

    logger.info(
        f"✅ Completed modernization analysis for {len(enriched_assets)} assets"
    )
    return enriched_assets
