"""
Platform Detection Agent - Main platform capability assessment
Analyzes target platform capabilities and features for migration planning
"""

from typing import Any, List


from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.metadata import AgentMetadata
from app.services.llm_config import get_crewai_llm


class PlatformDetectionAgent(BaseCrewAIAgent):
    """
    Performs comprehensive platform capability assessment using CrewAI patterns.
    
    Capabilities:
    - Platform feature detection
    - Service availability assessment
    - API compatibility analysis
    - Resource limit identification
    - Migration path validation
    """
    
    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize with proper CrewAI configuration"""
        if llm is None:
            llm = get_crewai_llm()
        
        super().__init__(
            role="Platform Detection Specialist",
            goal="Comprehensively assess target platform capabilities and identify optimal migration paths",
            backstory="""You are an expert platform analyst with extensive experience 
            in cloud platform assessment and migration planning. You excel at:
            - Identifying platform-specific features and capabilities
            - Detecting service availability and regional constraints
            - Analyzing API compatibility and versioning
            - Understanding resource quotas and limits
            - Mapping source to target platform capabilities
            - Identifying migration blockers and constraints
            
            Your assessments ensure migrations leverage platform capabilities optimally 
            while avoiding incompatibilities and limitations.""",
            tools=tools,
            llm=llm,
            **kwargs
        )
    
    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="platform_detection_agent",
            description="Assesses target platform capabilities and features for migration planning",
            agent_class=cls,
            required_tools=[
                "PlatformCapabilityScanner",
                "ServiceAvailabilityChecker",
                "APICompatibilityAnalyzer",
                "ResourceQuotaInspector",
                "FeatureCompatibilityMapper"
            ],
            capabilities=[
                "platform_capability_detection",
                "service_availability_check",
                "api_compatibility_analysis",
                "resource_limit_assessment",
                "migration_path_validation"
            ],
            max_iter=15,
            memory=True,
            verbose=True,
            allow_delegation=False
        )