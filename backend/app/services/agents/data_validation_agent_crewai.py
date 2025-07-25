"""
Data Import Validation Agent - Converted to proper CrewAI pattern
"""

from typing import Any, List

from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.metadata import AgentMetadata
from app.services.llm_config import get_crewai_llm


class DataImportValidationAgent(BaseCrewAIAgent):
    """
    Validates imported data quality and structure using CrewAI patterns.

    Capabilities:
    - Schema validation
    - Data quality assessment
    - Missing value detection
    - Format consistency checking
    - PII detection
    """

    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize with proper CrewAI configuration"""
        if llm is None:
            llm = get_crewai_llm()

        super().__init__(
            role="Data Import Validation Specialist",
            goal="Ensure imported data meets quality standards and is ready for processing",
            backstory="""You are an expert data validator with years of experience
            in enterprise data migration. You excel at:
            - Identifying data quality issues before they cause problems
            - Detecting patterns and anomalies in large datasets
            - Ensuring data meets schema requirements
            - Protecting sensitive information through PII detection

            Your validation prevents downstream failures and ensures smooth migrations.""",
            tools=tools,
            llm=llm,
            **kwargs
        )

    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="data_validation_agent",
            description="Validates data quality and structure for migration readiness",
            agent_class=cls,
            required_tools=[
                "schema_analyzer",
                "data_quality_analyzer",
                "pii_scanner",
                "format_validator",
            ],
            capabilities=[
                "data_validation",
                "schema_validation",
                "quality_assessment",
                "pii_detection",
            ],
            max_iter=10,
            memory=True,
            verbose=True,
            allow_delegation=False,
        )
