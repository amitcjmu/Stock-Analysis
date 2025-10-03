"""
Modernization Agent - Core Analysis Module
Contains the main analysis method and TenantMemoryManager integration.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.services.crewai_flows.memory.tenant_memory_manager import (
    TenantMemoryManager,
    LearningScope,
)
from app.services.crewai_flows.memory.pattern_sanitizer import (
    sanitize_pattern_data,
    safe_int_conversion,
)
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CoreAnalysisMixin:
    """Mixin for core analysis methods"""

    async def analyze_modernization_potential(
        self, asset_data: Dict[str, Any], db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Main method to analyze modernization potential of an asset using agentic intelligence.

        This method:
        1. Retrieves historical modernization patterns from TenantMemoryManager
        2. Creates a specialized modernization crew with architectural intelligence tools
        3. Executes comprehensive cloud readiness and modernization strategy analysis
        4. Stores discovered patterns back to TenantMemoryManager
        5. Returns structured results with modernization scores, strategies, and migration roadmaps

        Args:
            asset_data: Asset data to analyze
            db: Database session for TenantMemoryManager

        Returns:
            Modernization assessment with scores and recommendations
        """
        try:
            logger.info(
                f"☁️ Starting agentic modernization analysis for asset: {asset_data.get('name')}"
            )

            # Step 1: Initialize TenantMemoryManager
            memory_manager = TenantMemoryManager(
                crewai_service=self.crewai_service, database_session=db
            )

            # Step 2: Retrieve historical modernization patterns
            logger.info("📚 Retrieving historical modernization patterns...")
            query_context = {
                "asset_type": asset_data.get("asset_type"),
                "technology_stack": asset_data.get("technology_stack"),
                "architecture_style": asset_data.get("architecture_style"),
            }

            historical_patterns = await memory_manager.retrieve_similar_patterns(
                client_account_id=safe_int_conversion(self.client_account_id),
                engagement_id=safe_int_conversion(self.engagement_id),
                pattern_type="modernization_strategy",
                query_context=query_context,
                limit=10,
            )

            logger.info(f"✅ Found {len(historical_patterns)} historical patterns")

            # Step 3: Create and execute the modernization crew with historical context
            crew = self.create_modernization_crew(asset_data, historical_patterns)

            # Execute the crew (this will run the agent with all memory tools)
            result = crew.kickoff()

            # Parse the agent's output
            parsed_result = self._parse_modernization_output(result, asset_data)

            # Step 4: Store discovered patterns if analysis was successful
            if parsed_result.get("cloud_readiness_score", 0) > 0:
                logger.info("💾 Storing discovered modernization patterns...")
                pattern_data = {
                    "name": f"modernization_analysis_{asset_data.get('name')}_{datetime.utcnow().isoformat()}",
                    "cloud_readiness_score": parsed_result.get("cloud_readiness_score"),
                    "modernization_potential": parsed_result.get(
                        "modernization_potential"
                    ),
                    "recommended_strategy": parsed_result.get("recommended_strategy"),
                    "asset_type": asset_data.get("asset_type"),
                    "technology_stack": asset_data.get("technology_stack"),
                    "historical_patterns_used": len(historical_patterns),
                    "confidence": parsed_result.get("technical_confidence", "medium"),
                }

                # Sanitize pattern data before storage to remove PII/secrets
                sanitized_pattern_data = sanitize_pattern_data(pattern_data)

                pattern_id = await memory_manager.store_learning(
                    client_account_id=safe_int_conversion(self.client_account_id),
                    engagement_id=safe_int_conversion(self.engagement_id),
                    scope=LearningScope.ENGAGEMENT,
                    pattern_type="modernization_strategy",
                    pattern_data=sanitized_pattern_data,
                )

                logger.info(f"✅ Stored pattern with ID: {pattern_id}")
                parsed_result["pattern_id"] = pattern_id
                parsed_result["historical_patterns_used"] = len(historical_patterns)

            logger.info(
                f"✅ Modernization analysis completed - Cloud Readiness: "
                f"{parsed_result.get('cloud_readiness_score')}/100"
            )

            return parsed_result

        except Exception as e:
            logger.error(f"❌ Modernization analysis failed: {e}")

            # Fallback to reasoning engine if crew fails
            try:
                logger.info("🔄 Falling back to reasoning engine analysis")
                reasoning_result = (
                    await self.reasoning_engine.analyze_modernization_potential(
                        asset_data, "Modernization Agent"
                    )
                )
                return self._convert_reasoning_to_dict(reasoning_result)
            except Exception as fallback_error:
                logger.error(
                    f"❌ Fallback modernization analysis also failed: {fallback_error}"
                )
                return self._create_default_modernization_assessment(asset_data)
