"""
Tier Recommendation Agent - Automation tier recommendation
Recommends optimal automation tier based on platform capabilities and requirements
"""

from typing import Any, List


from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.metadata import AgentMetadata
from app.services.llm_config import get_crewai_llm


class TierRecommendationAgent(BaseCrewAIAgent):
    """
    Recommends appropriate automation tier using CrewAI patterns.
    
    Capabilities:
    - Complexity assessment
    - Automation feasibility analysis
    - Risk evaluation
    - Tier matching
    - Recommendation justification
    """
    
    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize with proper CrewAI configuration"""
        if llm is None:
            llm = get_crewai_llm()
        
        super().__init__(
            role="Automation Tier Recommendation Specialist",
            goal="Recommend the optimal automation tier that balances efficiency, risk, and complexity",
            backstory="""You are an expert in migration automation strategy with 
            comprehensive understanding of different automation approaches. You excel at:
            - Assessing migration complexity and requirements
            - Evaluating automation feasibility and risks
            - Understanding platform-specific automation capabilities
            - Balancing speed with safety in migrations
            - Recommending appropriate human oversight levels
            - Justifying tier selections with clear rationale
            
            Your recommendations ensure migrations use the right level of automation 
            for optimal outcomes while managing risk appropriately. You understand 
            the three tiers:
            - Tier 1: Full automation with minimal oversight
            - Tier 2: Semi-automated with checkpoint validations
            - Tier 3: Guided manual with automation assistance""",
            tools=tools,
            llm=llm,
            **kwargs
        )
    
    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="tier_recommendation_agent",
            description="Recommends optimal automation tier for migration execution",
            agent_class=cls,
            required_tools=[
                "ComplexityAnalyzer",
                "AutomationFeasibilityChecker",
                "RiskAssessmentTool",
                "TierMatchingEngine",
                "RecommendationJustifier"
            ],
            capabilities=[
                "complexity_assessment",
                "automation_feasibility",
                "risk_evaluation",
                "tier_recommendation",
                "justification_generation"
            ],
            max_iter=8,
            memory=True,
            verbose=True,
            allow_delegation=False
        )