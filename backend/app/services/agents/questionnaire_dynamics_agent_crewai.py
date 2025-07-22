"""
Questionnaire Dynamics Agent - Generates adaptive questionnaires for manual data collection
"""

from typing import Any, List


from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.metadata import AgentMetadata
from app.services.llm_config import get_crewai_llm


class QuestionnaireDynamicsAgent(BaseCrewAIAgent):
    """
    Generates intelligent, adaptive questionnaires for manual data collection.
    
    Capabilities:
    - Dynamic question generation based on gaps
    - Conditional logic for follow-up questions
    - Answer validation rules
    - Context-aware question sequencing
    - Multi-format support (text, dropdown, checkbox, etc.)
    """
    
    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize with proper CrewAI configuration"""
        if llm is None:
            llm = get_crewai_llm()
        
        super().__init__(
            role="Questionnaire Dynamics Specialist",
            goal="Create intelligent adaptive questionnaires that efficiently collect missing critical data through user-friendly forms",
            backstory="""You are an expert in form design and user experience for data collection. 
            You excel at:
            - Creating intuitive questionnaires that minimize user effort
            - Implementing smart conditional logic to show relevant questions
            - Designing validation rules that ensure data quality
            - Structuring questions in logical, easy-to-follow sequences
            - Adapting question types to the nature of data being collected
            
            Your questionnaires achieve high completion rates while gathering accurate, 
            comprehensive data needed for successful migrations.""",
            tools=tools,
            llm=llm,
            **kwargs
        )
    
    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="questionnaire_dynamics_agent",
            description="Generates adaptive questionnaires for efficient manual data collection",
            agent_class=cls,
            required_tools=[
                "gap_analyzer",
                "question_generator",
                "validation_rule_builder",
                "form_template_selector",
                "conditional_logic_builder"
            ],
            capabilities=[
                "questionnaire_generation",
                "conditional_logic",
                "validation_rules",
                "adaptive_forms",
                "user_experience_optimization"
            ],
            max_iter=12,
            memory=True,
            verbose=True,
            allow_delegation=False
        )