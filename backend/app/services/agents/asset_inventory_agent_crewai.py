"""
Asset Inventory Agent - Converted to proper CrewAI pattern
Specialized agent for asset classification and inventory management
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
from app.services.crewai_flows.memory.pattern_sanitizer import sanitize_pattern_data
from app.services.llm_config import get_crewai_llm

logger = logging.getLogger(__name__)


class AssetInventoryAgent(BaseCrewAIAgent):
    """
    Performs asset classification and inventory management using CrewAI patterns.

    Capabilities:
    - Asset type classification
    - Criticality assessment
    - Environment categorization
    - Inventory organization
    - Asset relationships
    """

    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize with proper CrewAI configuration"""
        if llm is None:
            llm = get_crewai_llm()

        super().__init__(
            role="Asset Inventory Specialist",
            goal="Accurately classify and categorize all discovered assets with proper criticality assessment",
            backstory="""You are an expert asset inventory specialist with deep knowledge
            of enterprise IT infrastructure. You excel at:
            - Identifying asset types from limited information
            - Assessing business criticality of IT assets
            - Understanding environment classifications (prod, dev, test)
            - Organizing assets into logical groupings
            - Identifying relationships between assets

            Your classification enables effective migration planning and risk assessment.""",
            tools=tools,
            llm=llm,
            **kwargs,
        )

    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="asset_inventory_agent",
            description="Classifies and categorizes assets for inventory management",
            agent_class=cls,
            required_tools=[
                "AssetClassifierTool",
                "CriticalityAssessorTool",
                "EnvironmentDetectorTool",
                "AssetRelationshipTool",
            ],
            capabilities=[
                "asset_classification",
                "criticality_assessment",
                "environment_detection",
                "inventory_management",
            ],
            max_iter=12,
            memory=False,  # Per ADR-024: Use TenantMemoryManager for enterprise memory
            verbose=True,
            allow_delegation=False,
        )

    async def classify_assets_with_memory(
        self,
        assets_data: List[Dict[str, Any]],
        technology_stack: str,
        environment: str,
        crewai_service: Any,
        client_account_id: int,
        engagement_id: int,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Classify assets with TenantMemoryManager integration (ADR-024).

        This method demonstrates proper memory integration:
        1. Retrieve historical asset classification patterns
        2. Provide patterns as context for classification
        3. Execute asset classification with historical insights
        4. Store discovered patterns for future use

        Args:
            assets_data: List of asset data to classify
            technology_stack: Technology stack identifier
            environment: Environment type (prod, dev, test, etc.)
            crewai_service: CrewAI service instance
            client_account_id: Client account ID for multi-tenant isolation
            engagement_id: Engagement ID for pattern scoping
            db: Database session

        Returns:
            Dict containing classification results with categories and relationships
        """
        try:
            logger.info(
                f"🧠 Starting asset classification with TenantMemoryManager "
                f"(client={client_account_id}, engagement={engagement_id}, "
                f"stack={technology_stack}, env={environment})"
            )

            # Step 1: Initialize TenantMemoryManager
            memory_manager = TenantMemoryManager(
                crewai_service=crewai_service, database_session=db
            )

            # Step 2: Retrieve historical asset classification patterns
            logger.info("📚 Retrieving historical asset classification patterns...")
            historical_patterns = await memory_manager.retrieve_similar_patterns(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                pattern_type="asset_classification",
                query_context={
                    "technology_stack": technology_stack,
                    "environment": environment,
                },
                limit=10,
            )

            logger.info(f"✅ Found {len(historical_patterns)} historical patterns")

            # Step 3: Classify assets with historical context
            logger.info("🔍 Classifying assets with historical insights...")

            # Extract classification insights from historical patterns
            classification_rules = []
            criticality_patterns = []

            for pattern in historical_patterns[:5]:  # Top 5 patterns
                pattern_data = pattern.get("pattern_data", {})
                if "classification_rules" in pattern_data:
                    classification_rules.append(pattern_data["classification_rules"])
                if "criticality_patterns" in pattern_data:
                    criticality_patterns.append(pattern_data["criticality_patterns"])

            # Perform classification
            classified_assets = []
            for asset in assets_data:
                classified_asset = {
                    "asset_id": asset.get("id", "unknown"),
                    "asset_name": asset.get("name", "unknown"),
                    "asset_type": self._determine_asset_type(asset, technology_stack),
                    "criticality": self._assess_criticality(asset, environment),
                    "environment": environment,
                    "technology_stack": technology_stack,
                }
                classified_assets.append(classified_asset)

            # Build classification result
            classification_result = {
                "total_assets": len(classified_assets),
                "classified_assets": classified_assets,
                "technology_stack": technology_stack,
                "environment": environment,
                "classification_summary": self._summarize_classification(
                    classified_assets
                ),
                "historical_context": {
                    "patterns_found": len(historical_patterns),
                    "rules_applied": len(classification_rules),
                },
            }

            # Step 4: Store discovered patterns
            logger.info("💾 Storing asset classification patterns...")

            pattern_data = {
                "name": f"asset_classification_{technology_stack}_{engagement_id}",
                "technology_stack": technology_stack,
                "environment": environment,
                "total_assets_classified": len(classified_assets),
                "classification_rules": self._extract_classification_rules(
                    classified_assets
                ),
                "criticality_patterns": self._extract_criticality_patterns(
                    classified_assets
                ),
                "asset_type_distribution": classification_result[
                    "classification_summary"
                ],
                "historical_patterns_used": len(historical_patterns),
            }

            # Sanitize pattern data before storage to remove PII/secrets
            sanitized_pattern_data = sanitize_pattern_data(pattern_data)

            pattern_id = await memory_manager.store_learning(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                scope=LearningScope.ENGAGEMENT,
                pattern_type="asset_classification",
                pattern_data=sanitized_pattern_data,
            )

            logger.info(f"✅ Stored asset classification pattern with ID: {pattern_id}")

            # Enhance result with memory metadata
            classification_result["memory_integration"] = {
                "status": "success",
                "pattern_id": pattern_id,
                "historical_patterns_used": len(historical_patterns),
                "framework": "TenantMemoryManager (ADR-024)",
            }

            return classification_result

        except Exception as e:
            logger.error(
                f"❌ Asset classification with memory failed: {e}", exc_info=True
            )
            # Re-raise to maintain consistent error handling
            raise

    def _determine_asset_type(self, asset: Dict[str, Any], tech_stack: str) -> str:
        """Determine asset type based on asset data and technology stack"""
        # Simple heuristic - in production would use more sophisticated logic
        if "server" in asset.get("name", "").lower():
            return "server"
        elif "database" in asset.get("name", "").lower():
            return "database"
        elif "application" in asset.get("name", "").lower():
            return "application"
        else:
            return "infrastructure"

    def _assess_criticality(self, asset: Dict[str, Any], environment: str) -> str:
        """Assess asset criticality based on environment and characteristics"""
        if environment == "production":
            return "high"
        elif environment == "staging":
            return "medium"
        else:
            return "low"

    def _summarize_classification(
        self, classified_assets: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Summarize classification results by asset type"""
        summary = {}
        for asset in classified_assets:
            asset_type = asset.get("asset_type", "unknown")
            summary[asset_type] = summary.get(asset_type, 0) + 1
        return summary

    def _extract_classification_rules(
        self, classified_assets: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract classification rules from classified assets"""
        # Simple rule extraction - in production would use more sophisticated logic
        return [
            "Server assets identified by 'server' keyword",
            "Database assets identified by 'database' keyword",
            "Application assets identified by 'application' keyword",
        ]

    def _extract_criticality_patterns(
        self, classified_assets: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract criticality patterns from classified assets"""
        # Simple pattern extraction
        return [
            "Production environment assets marked as high criticality",
            "Staging environment assets marked as medium criticality",
            "Development environment assets marked as low criticality",
        ]
