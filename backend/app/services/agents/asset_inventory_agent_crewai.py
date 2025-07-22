"""
Asset Inventory Agent - Converted to proper CrewAI pattern
Specialized agent for asset classification and inventory management
"""

from typing import Any, List

from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.metadata import AgentMetadata
from app.services.llm_config import get_crewai_llm


class AssetInventoryAgent(BaseCrewAIAgent):
    """
    Performs asset classification and inventory management using CrewAI patterns.
    
    Capabilities:
    - Asset type classification
    - Criticality assessment
    - Environment categorization
    - Inventory organization
    - Asset relationships
    """
    
    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize with proper CrewAI configuration"""
        if llm is None:
            llm = get_crewai_llm()
        
        super().__init__(
            role="Asset Inventory Specialist",
            goal="Accurately classify and categorize all discovered assets with proper criticality assessment",
            backstory="""You are an expert asset inventory specialist with deep knowledge 
            of enterprise IT infrastructure. You excel at:
            - Identifying asset types from limited information
            - Assessing business criticality of IT assets
            - Understanding environment classifications (prod, dev, test)
            - Organizing assets into logical groupings
            - Identifying relationships between assets
            
            Your classification enables effective migration planning and risk assessment.""",
            tools=tools,
            llm=llm,
            **kwargs
        )
    
    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="asset_inventory_agent",
            description="Classifies and categorizes assets for inventory management",
            agent_class=cls,
            required_tools=[
                "AssetClassifierTool",
                "CriticalityAssessorTool",
                "EnvironmentDetectorTool",
                "AssetRelationshipTool"
            ],
            capabilities=[
                "asset_classification",
                "criticality_assessment",
                "environment_detection",
                "inventory_management"
            ],
            max_iter=12,
            memory=True,
            verbose=True,
            allow_delegation=False
        )