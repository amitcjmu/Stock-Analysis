"""
Credential Validation Agent - Credential scope and access validation
Validates credentials and permissions for migration operations
"""

from typing import Any, List

from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.metadata import AgentMetadata
from app.services.llm_config import get_crewai_llm


class CredentialValidationAgent(BaseCrewAIAgent):
    """
    Validates credential scope and access permissions using CrewAI patterns.
    
    Capabilities:
    - Credential format validation
    - Permission scope verification
    - Access level assessment
    - Service account validation
    - Role and policy analysis
    """
    
    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize with proper CrewAI configuration"""
        if llm is None:
            llm = get_crewai_llm()
        
        super().__init__(
            role="Credential Validation Specialist",
            goal="Ensure all credentials have appropriate permissions and access levels for migration operations",
            backstory="""You are a security-focused credential validation expert with 
            deep knowledge of cloud IAM systems and access control. You excel at:
            - Validating credential formats and authenticity
            - Verifying permission scopes match migration requirements
            - Identifying missing or excessive permissions
            - Assessing service account configurations
            - Understanding role hierarchies and policy attachments
            - Detecting credential rotation requirements
            
            Your validation ensures migrations proceed securely with appropriate 
            access levels while maintaining least-privilege principles.""",
            tools=tools,
            llm=llm,
            **kwargs
        )
    
    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="credential_validation_agent",
            description="Validates credentials and permissions for secure migration operations",
            agent_class=cls,
            required_tools=[
                "CredentialFormatValidator",
                "PermissionScopeChecker",
                "AccessLevelAnalyzer",
                "ServiceAccountValidator",
                "RolePolicyAnalyzer"
            ],
            capabilities=[
                "credential_validation",
                "permission_verification",
                "access_level_assessment",
                "service_account_validation",
                "role_policy_analysis"
            ],
            max_iter=10,
            memory=True,
            verbose=True,
            allow_delegation=False
        )