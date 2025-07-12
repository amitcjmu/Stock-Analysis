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

import logging
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# CrewAI imports
from crewai import Agent, Task, Crew, Process

# Internal imports
from app.services.agentic_intelligence.agent_reasoning_patterns import (
    AgentReasoningEngine, 
    ReasoningDimension,
    AssetReasoningPatterns
)
from app.services.agentic_memory import ThreeTierMemoryManager
from app.services.agentic_memory.agent_tools_functional import create_functional_agent_tools

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
    
    def __init__(self, crewai_service, client_account_id: uuid.UUID, engagement_id: uuid.UUID, flow_id: Optional[uuid.UUID] = None):
        self.crewai_service = crewai_service
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.flow_id = flow_id
        
        # Initialize agentic memory system
        self.memory_manager = ThreeTierMemoryManager(client_account_id, engagement_id)
        
        # Initialize reasoning engine
        self.reasoning_engine = AgentReasoningEngine(
            self.memory_manager, 
            client_account_id, 
            engagement_id
        )
        
        # Get configured LLM
        try:
            from app.services.llm_config import get_crewai_llm
            self.llm = get_crewai_llm()
            logger.info("✅ Modernization Agent using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM: {e}")
            self.llm = getattr(crewai_service, 'llm', None)
        
        # Create agent tools for memory access
        self.agent_tools = create_functional_agent_tools(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            agent_name="Modernization Agent",
            flow_id=flow_id
        )
        
        logger.info(f"✅ Modernization Agent initialized with {len(self.agent_tools)} memory tools")
    
    def create_modernization_agent(self) -> Agent:
        """Create the CrewAI agent specialized in modernization and cloud readiness with memory tools"""
        
        agent = Agent(
            role="Cloud Modernization and Architecture Specialist",
            goal="Assess modernization potential and cloud readiness using evidence-based analysis and learned migration patterns",
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
            memory=True,  # Use agent memory for modernization intelligence
            max_iter=3,
            max_execution_time=60
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
            "data_volume": asset_data.get("data_volume")
        }
        
        task = Task(
            description=f"""
            Conduct a comprehensive modernization assessment for this asset using your cloud architecture intelligence and memory tools:
            
            Asset Details:
            {json.dumps(asset_summary, indent=2)}
            
            Complete Modernization Assessment Process:
            
            1. SEARCH FOR MODERNIZATION PATTERNS:
               Use your pattern search tool to find relevant modernization patterns and successful migration strategies from previous projects.
               Search for: cloud migration strategies, containerization patterns, microservices transformation, database modernization.
               
            2. TECHNOLOGY STACK ANALYSIS:
               Use your asset query tool to examine similar technology stacks and identify:
               - Cloud compatibility and native support for the technology stack
               - Containerization readiness and Docker/Kubernetes potential
               - Microservices decomposition opportunities for monolithic applications
               - Database modernization options (managed services, cloud-native databases)
               - Compare with other successfully modernized systems
               
            3. CLOUD READINESS ASSESSMENT:
               Evaluate cloud readiness factors including:
               - Stateless vs. stateful architecture considerations
               - Configuration management and externalization readiness
               - Service discovery and load balancing requirements
               - Data persistence and storage optimization opportunities
               - Network and security architecture cloud compatibility
               
            4. MODERNIZATION STRATEGY ANALYSIS:
               Assess different modernization approaches:
               - Lift-and-shift: Minimal changes, quick migration, cost analysis
               - Re-platform: Cloud-optimized deployment with managed services
               - Refactor: Containerization, microservices, cloud-native patterns
               - Rebuild: Complete redesign using cloud-native architecture
               - Migration complexity and effort estimation for each approach
               
            5. CONTAINERIZATION POTENTIAL:
               Determine containerization readiness:
               - Application architecture suitability for containers
               - Dependency management and external service integration
               - Configuration and secret management requirements
               - Orchestration needs for Kubernetes deployment
               - CI/CD pipeline integration opportunities
               
            6. MODERNIZATION SCORING:
               Provide a comprehensive modernization assessment:
               - Cloud Readiness Score (0-100): Current readiness for cloud deployment
               - Modernization Potential (Low/Medium/High): Overall modernization opportunity
               - Effort Estimation (Low/Medium/High): Resources required for modernization
               - Business Impact (Low/Medium/High): Expected benefits from modernization
               
            7. PATTERN DISCOVERY:
               If you identify new modernization patterns or architectural insights, use your pattern recording tool
               to save them for future project intelligence.
               
            8. ASSET ENRICHMENT:
               Use your asset enrichment tool to update the asset with:
               - Cloud readiness score and modernization potential assessment
               - Recommended modernization strategy and migration approach
               - Technical requirements and architecture recommendations
               - Effort estimation and timeline considerations
               
            Provide your modernization assessment in this format:
            Cloud Readiness Score: [0-100]
            Modernization Potential: [Low/Medium/High]
            Recommended Strategy: [Lift-and-shift/Re-platform/Refactor/Rebuild]
            Migration Effort: [Low/Medium/High]
            Technical Confidence: [High/Medium/Low]
            Architecture Assessment: [Key architectural strengths and modernization opportunities]
            Technology Compatibility: [Cloud service compatibility and optimization opportunities]
            Containerization Readiness: [Container deployment feasibility and requirements]
            Modernization Patterns Applied: [Patterns used from memory]
            New Patterns Discovered: [New modernization patterns identified]
            Immediate Modernization Steps: [Quick wins and initial modernization actions]
            Long-term Migration Strategy: [Comprehensive modernization roadmap]
            Expected Benefits: [Business and technical benefits from modernization]
            """,
            
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
            max_execution_time=50
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
            memory=True,  # Enable crew-level memory for modernization intelligence
            max_execution_time=90
        )
        
        return crew
    
    async def analyze_modernization_potential(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to analyze modernization potential of an asset using agentic intelligence.
        
        This method:
        1. Creates a specialized modernization crew with architectural intelligence tools
        2. Executes comprehensive cloud readiness and modernization strategy analysis
        3. Returns structured results with modernization scores, strategies, and migration roadmaps
        """
        try:
            logger.info(f"☁️ Starting agentic modernization analysis for asset: {asset_data.get('name')}")
            
            # Create and execute the modernization crew
            crew = self.create_modernization_crew(asset_data)
            
            # Execute the crew (this will run the agent with all memory tools)
            result = crew.kickoff()
            
            # Parse the agent's output
            parsed_result = self._parse_modernization_output(result, asset_data)
            
            logger.info(f"✅ Modernization analysis completed - Cloud Readiness: {parsed_result.get('cloud_readiness_score')}/100")
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"❌ Modernization analysis failed: {e}")
            
            # Fallback to reasoning engine if crew fails
            try:
                logger.info("🔄 Falling back to reasoning engine analysis")
                reasoning_result = await self.reasoning_engine.analyze_modernization_potential(
                    asset_data, "Modernization Agent"
                )
                return self._convert_reasoning_to_dict(reasoning_result)
            except Exception as fallback_error:
                logger.error(f"❌ Fallback modernization analysis also failed: {fallback_error}")
                return self._create_default_modernization_assessment(asset_data)
    
    def _parse_modernization_output(self, agent_output: str, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the agent's modernization assessment output into structured data"""
        try:
            result = {
                "agent_analysis_type": "modernization_assessment",
                "asset_id": asset_data.get("id"),
                "asset_name": asset_data.get("name"),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "agent_name": "Modernization Agent"
            }
            
            output_lower = str(agent_output).lower()
            
            # Extract cloud readiness score
            import re
            readiness_score_match = re.search(r'cloud readiness score:?\s*(\d+)', output_lower)
            result["cloud_readiness_score"] = int(readiness_score_match.group(1)) if readiness_score_match else 50
            
            # Extract modernization potential
            if 'modernization potential: high' in output_lower:
                result["modernization_potential"] = "high"
            elif 'modernization potential: medium' in output_lower:
                result["modernization_potential"] = "medium"
            else:
                result["modernization_potential"] = "low"
            
            # Extract recommended strategy
            if 'recommended strategy: rebuild' in output_lower:
                result["recommended_strategy"] = "rebuild"
            elif 'recommended strategy: refactor' in output_lower:
                result["recommended_strategy"] = "refactor"
            elif 'recommended strategy: re-platform' in output_lower:
                result["recommended_strategy"] = "re-platform"
            else:
                result["recommended_strategy"] = "lift-and-shift"
            
            # Extract migration effort
            if 'migration effort: high' in output_lower:
                result["migration_effort"] = "high"
            elif 'migration effort: medium' in output_lower:
                result["migration_effort"] = "medium"
            else:
                result["migration_effort"] = "low"
            
            # Extract technical confidence
            if 'high' in output_lower and 'confidence' in output_lower:
                result["technical_confidence"] = "high"
            elif 'medium' in output_lower and 'confidence' in output_lower:
                result["technical_confidence"] = "medium"
            else:
                result["technical_confidence"] = "medium"
            
            # Extract architecture assessment
            arch_match = re.search(r'architecture assessment:(.+?)(?:technology compatibility|$)', output_lower, re.DOTALL)
            if arch_match:
                result["architecture_assessment"] = arch_match.group(1).strip()
            else:
                result["architecture_assessment"] = "Architecture evaluated for cloud modernization compatibility"
            
            # Extract technology compatibility
            tech_match = re.search(r'technology compatibility:(.+?)(?:containerization readiness|$)', output_lower, re.DOTALL)
            if tech_match:
                result["technology_compatibility"] = tech_match.group(1).strip()
            else:
                result["technology_compatibility"] = "Technology stack assessed for cloud services integration"
            
            # Extract containerization readiness
            container_match = re.search(r'containerization readiness:(.+?)(?:modernization patterns|$)', output_lower, re.DOTALL)
            if container_match:
                result["containerization_readiness"] = container_match.group(1).strip()
            else:
                result["containerization_readiness"] = "Containerization potential evaluated"
            
            # Extract immediate modernization steps
            immediate_match = re.search(r'immediate modernization steps:(.+?)(?:long-term migration|$)', output_lower, re.DOTALL)
            if immediate_match:
                immediate_text = immediate_match.group(1).strip()
                result["immediate_steps"] = [step.strip() for step in immediate_text.split('-') if step.strip()]
            else:
                result["immediate_steps"] = ["Assess current architecture", "Plan containerization approach"]
            
            # Extract long-term migration strategy
            longterm_match = re.search(r'long-term migration strategy:(.+?)(?:expected benefits|$)', output_lower, re.DOTALL)
            if longterm_match:
                longterm_text = longterm_match.group(1).strip()
                result["migration_strategy"] = longterm_text
            else:
                result["migration_strategy"] = "Develop comprehensive modernization roadmap with phased approach"
            
            # Extract expected benefits
            benefits_match = re.search(r'expected benefits:(.+?)$', output_lower, re.DOTALL)
            if benefits_match:
                benefits_text = benefits_match.group(1).strip()
                result["expected_benefits"] = [benefit.strip() for benefit in benefits_text.split('-') if benefit.strip()]
            else:
                result["expected_benefits"] = ["Improved scalability", "Enhanced operational efficiency", "Reduced infrastructure costs"]
            
            # Set enrichment status
            result["enrichment_status"] = "agent_analyzed"
            result["analysis_method"] = "agentic_intelligence"
            
            return result
            
        except Exception as e:
            logger.warning(f"Failed to parse modernization output: {e}")
            return self._create_default_modernization_assessment(asset_data)
    
    def _convert_reasoning_to_dict(self, reasoning: 'AgentReasoning') -> Dict[str, Any]:
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
            "recommended_strategy": "re-platform" if reasoning.score >= 70 else "lift-and-shift",
            "migration_effort": "medium",
            "technical_confidence": "high" if reasoning.confidence >= 0.7 else "medium" if reasoning.confidence >= 0.4 else "low",
            "architecture_assessment": reasoning.reasoning_summary,
            "evidence_count": len(reasoning.evidence_pieces),
            "patterns_applied": len(reasoning.applied_patterns),
            "patterns_discovered": len(reasoning.discovered_patterns),
            "immediate_steps": reasoning.recommendations[:3],  # First 3 as immediate
            "migration_strategy": reasoning.reasoning_summary,
            "expected_benefits": reasoning.recommendations[3:] if len(reasoning.recommendations) > 3 else ["Improved cloud efficiency"],
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "enrichment_status": "agent_analyzed",
            "analysis_method": "reasoning_engine"
        }
    
    def _create_default_modernization_assessment(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
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
            "immediate_steps": ["Assess current dependencies", "Plan migration approach"],
            "migration_strategy": "Standard lift-and-shift with gradual optimization",
            "expected_benefits": ["Cloud infrastructure benefits", "Operational efficiency improvements"],
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "enrichment_status": "basic",
            "analysis_method": "fallback"
        }


async def analyze_modernization_potential_agentic(
    asset_data: Dict[str, Any], 
    crewai_service, 
    client_account_id: uuid.UUID, 
    engagement_id: uuid.UUID,
    flow_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    """
    Main function to analyze modernization potential using agentic intelligence.
    
    This function creates a ModernizationAgent and executes comprehensive cloud readiness
    and modernization strategy analysis.
    """
    
    agent = ModernizationAgent(
        crewai_service=crewai_service,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_id=flow_id
    )
    
    return await agent.analyze_modernization_potential(asset_data)


# Example usage pattern for integration with discovery flow
async def enrich_assets_with_modernization_intelligence(
    assets: List[Dict[str, Any]], 
    crewai_service, 
    client_account_id: uuid.UUID, 
    engagement_id: uuid.UUID,
    flow_id: Optional[uuid.UUID] = None
) -> List[Dict[str, Any]]:
    """
    Enrich multiple assets with comprehensive modernization intelligence.
    
    This function processes assets in batches and enriches them with:
    - Cloud readiness scores (0-100)
    - Modernization potential and recommended strategies
    - Architecture assessment and containerization readiness
    - Migration effort estimation and timeline planning
    - Immediate modernization steps and long-term roadmaps
    """
    
    enriched_assets = []
    
    # Initialize the modernization agent once for batch processing
    agent = ModernizationAgent(
        crewai_service=crewai_service,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_id=flow_id
    )
    
    for i, asset in enumerate(assets):
        try:
            logger.info(f"☁️ Analyzing modernization potential for asset {i+1}/{len(assets)}: {asset.get('name')}")
            
            # Perform agentic modernization analysis
            analysis_result = await agent.analyze_modernization_potential(asset)
            
            # Merge analysis results with asset data
            enriched_asset = {**asset}
            enriched_asset.update({
                "cloud_readiness_score": analysis_result.get("cloud_readiness_score"),
                "modernization_potential": analysis_result.get("modernization_potential"),
                "recommended_migration_strategy": analysis_result.get("recommended_strategy"),
                "migration_effort_estimate": analysis_result.get("migration_effort"),
                "architecture_assessment": analysis_result.get("architecture_assessment"),
                "containerization_readiness": analysis_result.get("containerization_readiness"),
                "modernization_recommendations": analysis_result.get("immediate_steps"),
                "migration_roadmap": analysis_result.get("migration_strategy"),
                "expected_modernization_benefits": analysis_result.get("expected_benefits"),
                "enrichment_status": "agent_enriched",
                "last_enriched_at": datetime.utcnow(),
                "last_enriched_by_agent": "Modernization Agent"
            })
            
            enriched_assets.append(enriched_asset)
            
            logger.info(f"✅ Modernization analysis completed - Readiness: {analysis_result.get('cloud_readiness_score')}/100")
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze modernization for asset {asset.get('name')}: {e}")
            
            # Add asset with basic modernization assessment
            enriched_asset = {**asset}
            enriched_asset.update({
                "cloud_readiness_score": 50,  # Default medium readiness
                "modernization_potential": "medium",
                "recommended_migration_strategy": "lift-and-shift",
                "modernization_analysis_reasoning": "Modernization analysis failed - using default assessment",
                "enrichment_status": "basic",
                "last_enriched_at": datetime.utcnow()
            })
            enriched_assets.append(enriched_asset)
    
    logger.info(f"✅ Completed modernization analysis for {len(enriched_assets)} assets")
    return enriched_assets