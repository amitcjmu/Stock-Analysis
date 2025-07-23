"""
Validation Workflow Agent - Creates validation workflows for manual data collection
"""

from typing import Any, List

from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.metadata import AgentMetadata
from app.services.llm_config import get_crewai_llm


class ValidationWorkflowAgent(BaseCrewAIAgent):
    """
    Creates and manages validation workflows for manually collected data.

    Capabilities:
    - Multi-level validation workflow design
    - Approval chain configuration
    - Cross-field validation rules
    - Data consistency checks
    - Error handling and correction workflows
    """

    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize with proper CrewAI configuration"""
        if llm is None:
            llm = get_crewai_llm()

        super().__init__(
            role="Validation Workflow Architect",
            goal="Design comprehensive validation workflows that ensure manually collected data meets quality standards before migration",
            backstory="""You are an expert in data validation and workflow orchestration. 
            You specialize in:
            - Building multi-tiered validation processes that catch errors early
            - Creating approval workflows that involve the right stakeholders
            - Implementing cross-field and cross-system validation rules
            - Designing error correction workflows that guide users to resolution
            - Ensuring data consistency across all manual inputs
            
            Your validation workflows prevent bad data from entering the migration pipeline,
            saving time and preventing costly errors downstream.""",
            tools=tools,
            llm=llm,
            **kwargs
        )

    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="validation_workflow_agent",
            description="Creates validation workflows for ensuring manual data quality",
            agent_class=cls,
            required_tools=[
                "workflow_designer",
                "validation_rule_engine",
                "approval_chain_builder",
                "error_handler",
                "consistency_checker",
            ],
            capabilities=[
                "workflow_design",
                "validation_orchestration",
                "approval_management",
                "error_handling",
                "data_consistency",
            ],
            max_iter=10,
            memory=True,
            verbose=True,
            allow_delegation=False,
        )
