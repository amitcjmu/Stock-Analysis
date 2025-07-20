"""
Critical Attribute Assessor Agent - CrewAI Implementation
Evaluates collected data against the 22 critical attributes framework
"""

from typing import List, Dict, Any, Optional
from crewai import Agent
from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.registry import AgentMetadata
from app.services.llm_config import get_crewai_llm
import logging

logger = logging.getLogger(__name__)

# The 22 Critical Attributes Framework for Migration Analysis
CRITICAL_ATTRIBUTES_FRAMEWORK = {
    "infrastructure": {
        "primary": [
            "hostname", "environment", "os_type", "os_version", 
            "cpu_cores", "memory_gb", "storage_gb", "network_zone"
        ],
        "business_impact": "high",
        "6r_relevance": ["rehost", "replatform", "refactor"]
    },
    "application": {
        "primary": [
            "application_name", "application_type", "technology_stack",
            "criticality_level", "data_classification", "compliance_scope"
        ],
        "business_impact": "critical", 
        "6r_relevance": ["refactor", "repurchase", "retire"]
    },
    "operational": {
        "primary": [
            "owner", "cost_center", "backup_strategy", "monitoring_status",
            "patch_level", "last_scan_date"
        ],
        "business_impact": "medium",
        "6r_relevance": ["retain", "rehost", "replatform"]
    },
    "dependencies": {
        "primary": [
            "application_dependencies", "database_dependencies", 
            "integration_points", "data_flows"
        ],
        "business_impact": "critical",
        "6r_relevance": ["refactor", "replatform", "repurchase"]
    }
}


class CriticalAttributeAssessorAgent(BaseCrewAIAgent):
    """
    Evaluates collected data against the 22 critical attributes framework.
    
    This agent specializes in:
    - Mapping collected data fields to critical attributes
    - Calculating attribute coverage and completeness
    - Assessing data quality for each attribute
    - Identifying gaps in critical migration data
    - Evaluating impact on 6R migration strategies
    """
    
    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize the Critical Attribute Assessor agent"""
        if llm is None:
            llm = get_crewai_llm()
        
        super().__init__(
            role="Critical Attribute Assessment Specialist",
            goal="Evaluate collected data against the 22 critical attributes framework to identify gaps and assess migration readiness",
            backstory="""You are an expert in migration data assessment with deep knowledge 
            of the 22 critical attributes framework. Your expertise includes:
            
            - Understanding which attributes are essential for each 6R migration strategy
            - Mapping raw data fields to standardized critical attributes
            - Calculating attribute coverage and data quality scores
            - Identifying gaps that impact migration decision confidence
            - Assessing business impact of missing attributes
            
            You know that different migration strategies require different attributes:
            - Rehost needs infrastructure details (OS, dependencies, performance)
            - Replatform requires technology stack and architecture information
            - Refactor demands application complexity and code quality metrics
            - Repurchase needs business function and cost analysis
            - Retire requires business value and dependency assessment
            - Retain needs operational metrics and cost justification
            
            Your assessments directly impact migration strategy recommendations and project success.""",
            tools=tools,
            llm=llm,
            max_iter=10,
            memory=True,
            verbose=True,
            allow_delegation=False,
            **kwargs
        )
    
    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="critical_attribute_assessor",
            description="Evaluates data against 22 critical attributes framework for migration readiness",
            agent_class=cls,
            required_tools=[
                "attribute_mapper",
                "completeness_analyzer",
                "quality_scorer",
                "gap_identifier"
            ],
            capabilities=[
                "attribute_assessment",
                "coverage_analysis",
                "gap_identification",
                "quality_evaluation",
                "6r_impact_analysis"
            ],
            max_iter=10,
            memory=True,
            verbose=True,
            allow_delegation=False
        )
    
    def assess_attributes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess collected data against critical attributes framework
        
        Args:
            data: Collected asset data to assess
            
        Returns:
            Assessment results including coverage, gaps, and recommendations
        """
        try:
            # This method would be called by the agent's tools
            logger.info(f"Assessing {len(data)} data points against critical attributes framework")
            
            assessment = {
                "framework_version": "22_critical_attributes_v1.0",
                "total_attributes": 22,
                "categories": {}
            }
            
            # Assess each category
            for category, config in CRITICAL_ATTRIBUTES_FRAMEWORK.items():
                category_assessment = {
                    "required_attributes": config["primary"],
                    "business_impact": config["business_impact"],
                    "6r_relevance": config["6r_relevance"],
                    "coverage": {},
                    "gaps": []
                }
                
                # Check each required attribute
                for attribute in config["primary"]:
                    if attribute in data:
                        category_assessment["coverage"][attribute] = {
                            "present": True,
                            "quality_score": self._calculate_quality_score(data[attribute]),
                            "completeness": self._calculate_completeness(data[attribute])
                        }
                    else:
                        category_assessment["gaps"].append({
                            "attribute": attribute,
                            "impact": config["business_impact"],
                            "affects_strategies": config["6r_relevance"]
                        })
                
                assessment["categories"][category] = category_assessment
            
            # Calculate overall metrics
            assessment["overall_coverage"] = self._calculate_overall_coverage(assessment)
            assessment["migration_readiness"] = self._calculate_migration_readiness(assessment)
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error in attribute assessment: {e}")
            return {"error": str(e)}
    
    def _calculate_quality_score(self, value: Any) -> float:
        """Calculate quality score for an attribute value"""
        if value is None or value == "":
            return 0.0
        
        # Basic quality scoring logic
        score = 0.5  # Base score for having a value
        
        # Additional quality checks
        if isinstance(value, str):
            if len(value) > 3:
                score += 0.2
            if not value.isspace():
                score += 0.2
            if value.lower() not in ["unknown", "n/a", "null", "none"]:
                score += 0.1
        else:
            score += 0.5  # Non-string values assumed to be more structured
        
        return min(score, 1.0)
    
    def _calculate_completeness(self, value: Any) -> float:
        """Calculate completeness score for an attribute value"""
        if value is None or value == "":
            return 0.0
        
        if isinstance(value, str):
            if value.lower() in ["unknown", "n/a", "null", "none", "tbd"]:
                return 0.2
            elif len(value.strip()) < 2:
                return 0.3
            else:
                return 1.0
        elif isinstance(value, (list, dict)):
            if len(value) == 0:
                return 0.2
            else:
                return 1.0
        else:
            return 1.0
    
    def _calculate_overall_coverage(self, assessment: Dict[str, Any]) -> float:
        """Calculate overall attribute coverage percentage"""
        total_attributes = 0
        covered_attributes = 0
        
        for category_data in assessment["categories"].values():
            total_attributes += len(category_data["required_attributes"])
            covered_attributes += len(category_data["coverage"])
        
        if total_attributes == 0:
            return 0.0
        
        return (covered_attributes / total_attributes) * 100
    
    def _calculate_migration_readiness(self, assessment: Dict[str, Any]) -> Dict[str, float]:
        """Calculate migration readiness for each 6R strategy"""
        readiness = {
            "rehost": 100.0,
            "replatform": 100.0,
            "refactor": 100.0,
            "repurchase": 100.0,
            "retire": 100.0,
            "retain": 100.0
        }
        
        # Reduce readiness based on gaps
        for category_data in assessment["categories"].values():
            for gap in category_data["gaps"]:
                impact_reduction = 15.0 if category_data["business_impact"] == "critical" else 10.0
                for strategy in gap["affects_strategies"]:
                    readiness[strategy] -= impact_reduction
        
        # Ensure scores don't go below 0
        for strategy in readiness:
            readiness[strategy] = max(0.0, readiness[strategy])
        
        return readiness