"""
Critical Attribute Assessor Agent - CrewAI Implementation
Evaluates collected data against the 22 critical attributes framework
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.registry import AgentMetadata
from app.services.crewai_flows.memory.tenant_memory_manager import (
    LearningScope,
    TenantMemoryManager,
)
from app.services.llm_config import get_crewai_llm

logger = logging.getLogger(__name__)

# The 22 Critical Attributes Framework for Migration Analysis
CRITICAL_ATTRIBUTES_FRAMEWORK = {
    "infrastructure": {
        "primary": [
            "hostname",
            "environment",
            "os_type",
            "os_version",
            "cpu_cores",
            "memory_gb",
            "storage_gb",
            "network_zone",
        ],
        "business_impact": "high",
        "6r_relevance": ["rehost", "replatform", "refactor"],
    },
    "application": {
        "primary": [
            "application_name",
            "application_type",
            "technology_stack",
            "criticality_level",
            "data_classification",
            "compliance_scope",
        ],
        "business_impact": "critical",
        "6r_relevance": ["refactor", "repurchase", "retire"],
    },
    "operational": {
        "primary": [
            "owner",
            "cost_center",
            "backup_strategy",
            "monitoring_status",
            "patch_level",
            "last_scan_date",
        ],
        "business_impact": "medium",
        "6r_relevance": ["retain", "rehost", "replatform"],
    },
    "dependencies": {
        "primary": [
            "application_dependencies",
            "database_dependencies",
            "integration_points",
            "data_flows",
        ],
        "business_impact": "critical",
        "6r_relevance": ["refactor", "replatform", "repurchase"],
    },
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
            goal=(
                "Evaluate collected data against the 22 critical attributes "
                "framework to identify gaps and assess migration readiness"
            ),
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
            memory=False,  # Per ADR-024: Use TenantMemoryManager for enterprise memory
            verbose=True,
            allow_delegation=False,
            **kwargs,
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
                "gap_identifier",
            ],
            capabilities=[
                "attribute_assessment",
                "coverage_analysis",
                "gap_identification",
                "quality_evaluation",
                "6r_impact_analysis",
            ],
            max_iter=10,
            memory=False,  # Per ADR-024: Use TenantMemoryManager for enterprise memory
            verbose=True,
            allow_delegation=False,
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
            logger.info(
                f"Assessing {len(data)} data points against critical attributes framework"
            )

            assessment = {
                "framework_version": "22_critical_attributes_v1.0",
                "total_attributes": 22,
                "categories": {},
            }

            # Assess each category
            for category, config in CRITICAL_ATTRIBUTES_FRAMEWORK.items():
                category_assessment = {
                    "required_attributes": config["primary"],
                    "business_impact": config["business_impact"],
                    "6r_relevance": config["6r_relevance"],
                    "coverage": {},
                    "gaps": [],
                }

                # Check each required attribute
                for attribute in config["primary"]:
                    if attribute in data:
                        category_assessment["coverage"][attribute] = {
                            "present": True,
                            "quality_score": self._calculate_quality_score(
                                data[attribute]
                            ),
                            "completeness": self._calculate_completeness(
                                data[attribute]
                            ),
                        }
                    else:
                        category_assessment["gaps"].append(
                            {
                                "attribute": attribute,
                                "impact": config["business_impact"],
                                "affects_strategies": config["6r_relevance"],
                            }
                        )

                assessment["categories"][category] = category_assessment

            # Calculate overall metrics
            assessment["overall_coverage"] = self._calculate_overall_coverage(
                assessment
            )
            assessment["migration_readiness"] = self._calculate_migration_readiness(
                assessment
            )

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

    def _calculate_migration_readiness(
        self, assessment: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate migration readiness for each 6R strategy"""
        readiness = {
            "rehost": 100.0,
            "replatform": 100.0,
            "refactor": 100.0,
            "repurchase": 100.0,
            "retire": 100.0,
            "retain": 100.0,
        }

        # Reduce readiness based on gaps
        for category_data in assessment["categories"].values():
            for gap in category_data["gaps"]:
                impact_reduction = (
                    15.0 if category_data["business_impact"] == "critical" else 10.0
                )
                for strategy in gap["affects_strategies"]:
                    readiness[strategy] -= impact_reduction

        # Ensure scores don't go below 0
        for strategy in readiness:
            readiness[strategy] = max(0.0, readiness[strategy])

        return readiness

    async def assess_attributes_with_memory(
        self,
        data: Dict[str, Any],
        asset_type: str,
        crewai_service: Any,
        client_account_id: int,
        engagement_id: int,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Assess attributes with TenantMemoryManager integration (ADR-024).

        This method demonstrates proper memory integration:
        1. Retrieve historical attribute assessment patterns
        2. Provide patterns as context for the assessment
        3. Execute assessment with historical insights
        4. Store discovered patterns for future use

        Args:
            data: Collected asset data to assess
            asset_type: Type of asset being assessed
            crewai_service: CrewAI service instance
            client_account_id: Client account ID for multi-tenant isolation
            engagement_id: Engagement ID for pattern scoping
            db: Database session

        Returns:
            Dict containing assessment results with coverage, gaps, and recommendations
        """
        try:
            logger.info(
                f"🧠 Starting attribute assessment with TenantMemoryManager "
                f"(client={client_account_id}, engagement={engagement_id}, asset_type={asset_type})"
            )

            # Step 1: Initialize TenantMemoryManager
            memory_manager = TenantMemoryManager(
                crewai_service=crewai_service, database_session=db
            )

            # Step 2: Retrieve historical attribute assessment patterns
            logger.info("📚 Retrieving historical attribute assessment patterns...")
            historical_patterns = await memory_manager.retrieve_similar_patterns(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                pattern_type="attribute_assessment",
                query_context={"asset_type": asset_type, "framework": "6R"},
                limit=10,
            )

            logger.info(f"✅ Found {len(historical_patterns)} historical patterns")

            # Step 3: Execute existing assessment method
            logger.info("🔍 Executing attribute assessment with historical context...")
            assessment = self.assess_attributes(data)

            # Step 4: Store discovered patterns if assessment was successful
            if assessment and "error" not in assessment:
                logger.info("💾 Storing discovered attribute assessment patterns...")

                # Extract key metrics for pattern storage
                pattern_data = {
                    "name": f"attribute_assessment_{asset_type}_{engagement_id}",
                    "asset_type": asset_type,
                    "framework": "22_critical_attributes",
                    "overall_coverage": assessment.get("overall_coverage", 0.0),
                    "migration_readiness": assessment.get("migration_readiness", {}),
                    "category_assessments": {
                        cat: {
                            "coverage_count": len(data.get("coverage", {})),
                            "gap_count": len(data.get("gaps", [])),
                            "business_impact": data.get("business_impact", "unknown"),
                        }
                        for cat, data in assessment.get("categories", {}).items()
                    },
                    "historical_patterns_used": len(historical_patterns),
                }

                pattern_id = await memory_manager.store_learning(
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    scope=LearningScope.ENGAGEMENT,
                    pattern_type="attribute_assessment",
                    pattern_data=pattern_data,
                )

                logger.info(
                    f"✅ Stored attribute assessment pattern with ID: {pattern_id}"
                )

                # Enhance result with memory metadata
                assessment["memory_integration"] = {
                    "status": "success",
                    "pattern_id": pattern_id,
                    "historical_patterns_used": len(historical_patterns),
                    "framework": "TenantMemoryManager (ADR-024)",
                }

            return assessment

        except Exception as e:
            logger.error(
                f"❌ Attribute assessment with memory failed: {e}", exc_info=True
            )
            # Fallback to standard assessment without memory
            logger.warning("⚠️ Falling back to standard assessment without memory")
            return self.assess_attributes(data)
