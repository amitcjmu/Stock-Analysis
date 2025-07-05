"""
Field Mapping Agent - Converted to proper CrewAI pattern
Enterprise Asset Schema Mapping Specialist
"""

from typing import List, Dict, Any
from crewai import Agent
from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.registry import AgentMetadata
from app.services.llm_config import get_crewai_llm

class FieldMappingAgent(BaseCrewAIAgent):
    """
    Maps source data fields to target schema using CrewAI patterns.
    
    Capabilities:
    - Intelligent field mapping
    - Schema analysis
    - Semantic matching
    - Confidence scoring
    - Mapping validation
    """
    
    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize with proper CrewAI configuration"""
        if llm is None:
            llm = get_crewai_llm()
        
        super().__init__(
            role="Field Mapping Specialist",
            goal="Map source data fields to target schema with high accuracy and confidence",
            backstory="""You are an expert data architect with deep experience in 
            enterprise data migration and schema mapping. You excel at:
            - Understanding semantic relationships between field names
            - Identifying field patterns across different systems
            - Creating accurate mappings that preserve data integrity
            - Validating mapping quality before implementation
            
            Your mappings enable seamless data transformation and migration success.""",
            tools=tools,
            llm=llm,
            **kwargs
        )
    
    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="field_mapping_agent",
            description="Maps source data fields to target schema with semantic analysis",
            agent_class=cls,
            required_tools=[
                "SemanticMatcherTool",
                "SchemaAnalyzerTool",
                "MappingValidatorTool",
                "FieldSimilarityTool"
            ],
            capabilities=[
                "field_mapping",
                "schema_mapping",
                "semantic_analysis",
                "mapping_validation"
            ],
            max_iter=15,
            memory=True,
            verbose=True,
            allow_delegation=False
        )