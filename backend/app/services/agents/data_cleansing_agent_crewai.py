"""
Data Cleansing Agent - Converted to proper CrewAI pattern
Enterprise Data Standardization and Bulk Processing Specialist
"""

from typing import List, Dict, Any
from crewai import Agent
from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.registry import AgentMetadata
from app.services.llm_config import get_crewai_llm

class DataCleansingAgent(BaseCrewAIAgent):
    """
    Performs intelligent data cleansing and standardization using CrewAI patterns.
    
    Capabilities:
    - Data standardization
    - Format normalization
    - Value cleansing
    - Missing data handling
    - Bulk operations
    """
    
    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize with proper CrewAI configuration"""
        if llm is None:
            llm = get_crewai_llm()
        
        super().__init__(
            role="Data Cleansing Specialist",
            goal="Clean and standardize data to ensure quality and consistency",
            backstory="""You are an expert data engineer specializing in data quality 
            and standardization. You excel at:
            - Identifying and correcting data inconsistencies
            - Applying standardization rules across large datasets
            - Handling missing and invalid data intelligently
            - Performing bulk operations efficiently
            - Maintaining data integrity during cleansing
            
            Your work ensures high-quality, consistent data for migration success.""",
            tools=tools,
            llm=llm,
            **kwargs
        )
    
    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="data_cleansing_agent",
            description="Cleans and standardizes data for quality and consistency",
            agent_class=cls,
            required_tools=[
                "DataStandardizerTool",
                "FormatNormalizerTool",
                "ValueValidatorTool",
                "BulkOperationTool"
            ],
            capabilities=[
                "data_cleansing",
                "data_standardization", 
                "format_normalization",
                "bulk_operations"
            ],
            max_iter=12,
            memory=True,
            verbose=True,
            allow_delegation=False
        )