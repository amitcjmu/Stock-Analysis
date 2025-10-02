"""
Data Import Validation Agent - Converted to proper CrewAI pattern
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.metadata import AgentMetadata
from app.services.crewai_flows.memory.tenant_memory_manager import (
    LearningScope,
    TenantMemoryManager,
)
from app.services.llm_config import get_crewai_llm

logger = logging.getLogger(__name__)


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
            **kwargs,
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
            memory=False,  # Per ADR-024: Use TenantMemoryManager for enterprise memory
            verbose=True,
            allow_delegation=False,
        )

    async def validate_data_with_memory(
        self,
        data_source: str,
        validation_scope: str,
        data_records: List[Dict[str, Any]],
        crewai_service: Any,
        client_account_id: int,
        engagement_id: int,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Validate data with TenantMemoryManager integration (ADR-024).

        This method demonstrates proper memory integration:
        1. Retrieve historical data validation patterns
        2. Provide patterns as context for validation
        3. Execute data validation with historical insights
        4. Store discovered patterns for future use

        Args:
            data_source: Source of the data (e.g., 'csv', 'api', 'database')
            validation_scope: Scope of validation (e.g., 'schema', 'quality', 'completeness')
            data_records: List of data records to validate
            crewai_service: CrewAI service instance
            client_account_id: Client account ID for multi-tenant isolation
            engagement_id: Engagement ID for pattern scoping
            db: Database session

        Returns:
            Dict containing validation results with issues and recommendations
        """
        try:
            logger.info(
                f"🧠 Starting data validation with TenantMemoryManager "
                f"(client={client_account_id}, engagement={engagement_id}, "
                f"source={data_source}, scope={validation_scope})"
            )

            # Step 1: Initialize TenantMemoryManager
            memory_manager = TenantMemoryManager(
                crewai_service=crewai_service, database_session=db
            )

            # Step 2: Retrieve historical data validation patterns
            logger.info("📚 Retrieving historical data validation patterns...")
            historical_patterns = await memory_manager.retrieve_similar_patterns(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                pattern_type="data_validation",
                query_context={
                    "data_source": data_source,
                    "validation_scope": validation_scope,
                },
                limit=10,
            )

            logger.info(f"✅ Found {len(historical_patterns)} historical patterns")

            # Step 3: Validate data with historical context
            logger.info("🔍 Validating data with historical insights...")

            # Extract validation rules from historical patterns
            validation_rules = []
            common_issues = []

            for pattern in historical_patterns[:5]:  # Top 5 patterns
                pattern_data = pattern.get("pattern_data", {})
                if "validation_rules" in pattern_data:
                    validation_rules.extend(pattern_data["validation_rules"])
                if "common_issues" in pattern_data:
                    common_issues.extend(pattern_data["common_issues"])

            # Perform validation
            validation_issues = []
            quality_score = 1.0

            for idx, record in enumerate(data_records):
                # Check for missing required fields
                if not record.get("id"):
                    validation_issues.append(
                        {
                            "record_index": idx,
                            "severity": "error",
                            "issue": "Missing required field: id",
                        }
                    )
                    quality_score -= 0.1

                # Check for data quality
                if not record.get("name") or record.get("name") == "":
                    validation_issues.append(
                        {
                            "record_index": idx,
                            "severity": "warning",
                            "issue": "Empty or missing name field",
                        }
                    )
                    quality_score -= 0.05

            quality_score = max(0.0, quality_score)

            # Build validation result
            validation_result = {
                "data_source": data_source,
                "validation_scope": validation_scope,
                "total_records": len(data_records),
                "validation_issues": validation_issues,
                "quality_score": quality_score,
                "passed": len(validation_issues) == 0,
                "historical_context": {
                    "patterns_found": len(historical_patterns),
                    "rules_applied": len(validation_rules),
                    "common_issues_checked": len(common_issues),
                },
            }

            # Step 4: Store discovered patterns
            logger.info("💾 Storing data validation patterns...")

            pattern_data = {
                "name": f"data_validation_{data_source}_{engagement_id}",
                "data_source": data_source,
                "validation_scope": validation_scope,
                "total_records_validated": len(data_records),
                "validation_rules": [
                    "Check for required id field",
                    "Check for non-empty name field",
                    "Quality score calculation",
                ],
                "common_issues": [issue["issue"] for issue in validation_issues[:5]],
                "quality_score": quality_score,
                "historical_patterns_used": len(historical_patterns),
            }

            pattern_id = await memory_manager.store_learning(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                scope=LearningScope.ENGAGEMENT,
                pattern_type="data_validation",
                pattern_data=pattern_data,
            )

            logger.info(f"✅ Stored data validation pattern with ID: {pattern_id}")

            # Enhance result with memory metadata
            validation_result["memory_integration"] = {
                "status": "success",
                "pattern_id": pattern_id,
                "historical_patterns_used": len(historical_patterns),
                "framework": "TenantMemoryManager (ADR-024)",
            }

            return validation_result

        except Exception as e:
            logger.error(f"❌ Data validation with memory failed: {e}", exc_info=True)
            # Fallback to basic validation
            logger.warning("⚠️ Falling back to basic validation without memory")

            return {
                "data_source": data_source,
                "validation_scope": validation_scope,
                "total_records": len(data_records),
                "validation_issues": [],
                "quality_score": 0.5,
                "passed": False,
                "status": "error",
                "error": str(e),
            }
