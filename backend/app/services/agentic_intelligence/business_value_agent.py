"""
Business Value Agent - Agentic Intelligence Implementation

This agent analyzes assets to determine their business value using:
1. Real CrewAI agent reasoning instead of hard-coded rules
2. Pattern discovery and learning from previous analyses
3. Evidence-based scoring with confidence levels
4. Integration with three-tier memory system for continuous learning

The agent uses the agentic memory tools to:
- Search for existing business value patterns
- Record new patterns it discovers during analysis
- Enrich assets with its reasoning and scores
- Learn from user feedback to improve future analysis
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# CrewAI imports
from crewai import Agent, Crew, Process, Task
from crewai.tools import tool

# Internal imports
from app.services.agentic_intelligence.agent_reasoning_patterns import (
    AgentReasoningEngine,
    AssetReasoningPatterns,
    ReasoningDimension,
)
from app.services.agentic_memory import ThreeTierMemoryManager
from app.services.agentic_memory.agent_tools_functional import create_functional_agent_tools

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
            logger.info("✅ Business Value Agent using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM: {e}")
            self.llm = getattr(crewai_service, 'llm', None)
        
        # Create agent tools for memory access
        self.agent_tools = create_functional_agent_tools(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            agent_name="Business Value Agent",
            flow_id=flow_id
        )
        
        logger.info(f"✅ Business Value Agent initialized with {len(self.agent_tools)} memory tools")
    
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
            memory=True,  # Use agent memory for learning
            max_iter=3,
            max_execution_time=60
        )
        
        return agent
    
    def create_business_value_analysis_task(self, asset_data: Dict[str, Any]) -> Task:
        """Create a task for analyzing business value of a specific asset"""
        
        asset_summary = {
            "name": asset_data.get("name"),
            "asset_type": asset_data.get("asset_type"),
            "technology_stack": asset_data.get("technology_stack"),
            "environment": asset_data.get("environment"),
            "cpu_utilization_percent": asset_data.get("cpu_utilization_percent"),
            "business_criticality": asset_data.get("business_criticality")
        }
        
        task = Task(
            description=f"""
            Analyze the business value of this asset using your agentic intelligence and memory tools:
            
            Asset Details:
            {json.dumps(asset_summary, indent=2)}
            
            Complete Analysis Process:
            
            1. SEARCH FOR PATTERNS:
               Use your pattern search tool to find relevant business value patterns from previous analyses.
               Search for patterns related to: database business value, production systems, technology stack analysis.
               
            2. GATHER EVIDENCE:
               Use your asset query tool to examine similar assets and gather comparative evidence.
               Look for assets with similar characteristics to understand value patterns.
               
            3. ANALYZE BUSINESS VALUE:
               Based on the evidence and patterns, analyze:
               - Business criticality indicators (production environment, high usage, etc.)
               - Technology value indicators (enterprise systems, databases, etc.)
               - Usage patterns that suggest business importance
               - Integration complexity that adds business value
               
            4. CALCULATE SCORE:
               Provide a business value score from 1-10 where:
               - 1-3: Low business value (test systems, non-critical applications)
               - 4-6: Medium business value (important but replaceable systems)
               - 7-8: High business value (critical business operations)
               - 9-10: Very high business value (core business systems, revenue-generating)
               
            5. DISCOVER NEW PATTERNS:
               If you identify a new business value pattern during your analysis, use your 
               pattern recording tool to save it for future analyses.
               
            6. ENRICH THE ASSET:
               Use your asset enrichment tool to update the asset with:
               - Your business value score
               - Your detailed reasoning
               - Confidence level in your analysis
               
            Provide your final analysis in this format:
            Business Value Score: [1-10]
            Confidence Level: [High/Medium/Low]
            Primary Reasoning: [Your main reasoning for the score]
            Evidence Found: [Key evidence that supported your decision]
            Patterns Applied: [Any patterns you used from memory]
            New Patterns Discovered: [Any new patterns you identified]
            Recommendations: [Specific recommendations based on the business value]
            """,
            
            expected_output="""
            Business Value Analysis Report with:
            - Business Value Score (1-10)
            - Confidence Level assessment
            - Detailed reasoning explaining the score
            - Evidence summary from pattern search and asset analysis
            - New patterns discovered and recorded
            - Asset enrichment confirmation
            - Specific recommendations for this asset
            """,
            
            agent=self.create_business_value_agent(),  # Fix: Assign agent to task
            max_execution_time=50
        )
        
        return task
    
    def create_business_value_crew(self, asset_data: Dict[str, Any]) -> Crew:
        """Create a crew for business value analysis"""
        
        agent = self.create_business_value_agent()
        task = self.create_business_value_analysis_task(asset_data)
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
            memory=True,  # Enable crew-level memory
            max_execution_time=90
        )
        
        return crew
    
    async def analyze_asset_business_value(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to analyze business value of an asset using agentic intelligence.
        
        This method:
        1. Creates a specialized CrewAI crew with memory tools
        2. Executes the agent reasoning process
        3. Returns structured results with business value score and reasoning
        """
        try:
            logger.info(f"🧠 Starting agentic business value analysis for asset: {asset_data.get('name')}")
            
            # Create and execute the business value crew
            crew = self.create_business_value_crew(asset_data)
            
            # Execute the crew (this will run the agent with all memory tools)
            result = crew.kickoff()
            
            # Parse the agent's output
            parsed_result = self._parse_agent_output(result, asset_data)
            
            logger.info(f"✅ Business value analysis completed - Score: {parsed_result.get('business_value_score')}")
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"❌ Business value analysis failed: {e}")
            
            # Fallback to reasoning engine if crew fails
            try:
                logger.info("🔄 Falling back to reasoning engine analysis")
                reasoning_result = await self.reasoning_engine.analyze_asset_business_value(
                    asset_data, "Business Value Agent"
                )
                return self._convert_reasoning_to_dict(reasoning_result)
            except Exception as fallback_error:
                logger.error(f"❌ Fallback analysis also failed: {fallback_error}")
                return self._create_default_analysis(asset_data)
    
    def _parse_agent_output(self, agent_output: str, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the agent's natural language output into structured data"""
        try:
            result = {
                "agent_analysis_type": "business_value",
                "asset_id": asset_data.get("id"),
                "asset_name": asset_data.get("name"),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "agent_name": "Business Value Agent"
            }
            
            output_lower = str(agent_output).lower()
            
            # Extract business value score
            import re
            score_match = re.search(r'business value score:?\s*(\d+)', output_lower)
            if score_match:
                result["business_value_score"] = int(score_match.group(1))
            else:
                # Try to extract score from other patterns
                score_match = re.search(r'score:?\s*(\d+)', output_lower)
                result["business_value_score"] = int(score_match.group(1)) if score_match else 5
            
            # Extract confidence level
            if 'high' in output_lower and 'confidence' in output_lower:
                result["confidence_level"] = "high"
            elif 'medium' in output_lower and 'confidence' in output_lower:
                result["confidence_level"] = "medium"
            else:
                result["confidence_level"] = "medium"
            
            # Extract reasoning
            reasoning_match = re.search(r'(?:primary reasoning|reasoning):(.+?)(?:evidence found|$)', output_lower, re.DOTALL)
            if reasoning_match:
                result["reasoning"] = reasoning_match.group(1).strip()
            else:
                result["reasoning"] = "Business value determined through agentic analysis"
            
            # Extract recommendations
            recommendations_match = re.search(r'recommendations:(.+?)$', output_lower, re.DOTALL)
            if recommendations_match:
                result["recommendations"] = [rec.strip() for rec in recommendations_match.group(1).split('-') if rec.strip()]
            else:
                result["recommendations"] = ["Standard migration approach recommended"]
            
            # Set enrichment status
            result["enrichment_status"] = "agent_analyzed"
            result["analysis_method"] = "agentic_intelligence"
            
            return result
            
        except Exception as e:
            logger.warning(f"Failed to parse agent output: {e}")
            return self._create_default_analysis(asset_data)
    
    def _convert_reasoning_to_dict(self, reasoning: 'AgentReasoning') -> Dict[str, Any]:
        """Convert AgentReasoning object to dictionary format"""
        return {
            "agent_analysis_type": "business_value",
            "business_value_score": reasoning.score,
            "confidence_level": "high" if reasoning.confidence >= 0.7 else "medium" if reasoning.confidence >= 0.4 else "low",
            "reasoning": reasoning.reasoning_summary,
            "evidence_count": len(reasoning.evidence_pieces),
            "patterns_applied": len(reasoning.applied_patterns),
            "patterns_discovered": len(reasoning.discovered_patterns),
            "recommendations": reasoning.recommendations,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "enrichment_status": "agent_analyzed",
            "analysis_method": "reasoning_engine"
        }
    
    def _create_default_analysis(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a default analysis when both agent and reasoning engine fail"""
        return {
            "agent_analysis_type": "business_value",
            "business_value_score": 5,  # Default medium value
            "confidence_level": "low",
            "reasoning": "Default analysis - agent reasoning unavailable",
            "recommendations": ["Standard migration approach"],
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "enrichment_status": "basic",
            "analysis_method": "fallback"
        }


async def analyze_asset_business_value_agentic(
    asset_data: Dict[str, Any], 
    crewai_service, 
    client_account_id: uuid.UUID, 
    engagement_id: uuid.UUID,
    flow_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    """
    Main function to analyze asset business value using agentic intelligence.
    
    This function creates a BusinessValueAgent and executes the full agentic analysis
    including pattern search, evidence gathering, and memory-based learning.
    """
    
    agent = BusinessValueAgent(
        crewai_service=crewai_service,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_id=flow_id
    )
    
    return await agent.analyze_asset_business_value(asset_data)


# Example usage pattern for integration with discovery flow
async def enrich_assets_with_business_value_intelligence(
    assets: List[Dict[str, Any]], 
    crewai_service, 
    client_account_id: uuid.UUID, 
    engagement_id: uuid.UUID,
    flow_id: Optional[uuid.UUID] = None
) -> List[Dict[str, Any]]:
    """
    Enrich multiple assets with business value intelligence.
    
    This function processes assets in batches and enriches them with:
    - Business value scores (1-10)
    - Confidence levels
    - Detailed reasoning
    - Pattern-based insights
    - Recommendations
    """
    
    enriched_assets = []
    
    # Initialize the business value agent once for batch processing
    agent = BusinessValueAgent(
        crewai_service=crewai_service,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_id=flow_id
    )
    
    for i, asset in enumerate(assets):
        try:
            logger.info(f"🧠 Analyzing asset {i+1}/{len(assets)}: {asset.get('name')}")
            
            # Perform agentic business value analysis
            analysis_result = await agent.analyze_asset_business_value(asset)
            
            # Merge analysis results with asset data
            enriched_asset = {**asset}
            enriched_asset.update({
                "business_value_score": analysis_result.get("business_value_score"),
                "business_value_reasoning": analysis_result.get("reasoning"),
                "business_value_confidence": analysis_result.get("confidence_level"),
                "business_value_recommendations": analysis_result.get("recommendations"),
                "enrichment_status": "agent_enriched",
                "last_enriched_at": datetime.utcnow(),
                "last_enriched_by_agent": "Business Value Agent"
            })
            
            enriched_assets.append(enriched_asset)
            
            logger.info(f"✅ Asset enriched - Business Value: {analysis_result.get('business_value_score')}/10")
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze asset {asset.get('name')}: {e}")
            
            # Add asset with basic enrichment
            enriched_asset = {**asset}
            enriched_asset.update({
                "business_value_score": 5,  # Default medium value
                "business_value_reasoning": "Analysis failed - using default value",
                "business_value_confidence": "low",
                "enrichment_status": "basic",
                "last_enriched_at": datetime.utcnow()
            })
            enriched_assets.append(enriched_asset)
    
    logger.info(f"✅ Completed business value analysis for {len(enriched_assets)} assets")
    return enriched_assets