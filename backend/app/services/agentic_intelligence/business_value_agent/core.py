"""
Business Value Agent - Core Analysis Module
Contains the main analysis method and TenantMemoryManager integration.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.services.crewai_flows.memory.tenant_memory_manager import (
    TenantMemoryManager,
    LearningScope,
)
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CoreAnalysisMixin:
    """Mixin for core analysis methods"""

    async def analyze_asset_business_value(
        self, asset_data: Dict[str, Any], db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Main method to analyze business value of an asset using agentic intelligence.

        This method:
        1. Retrieves historical business value patterns from TenantMemoryManager
        2. Creates a specialized CrewAI crew with memory tools
        3. Executes the agent reasoning process
        4. Stores discovered patterns back to TenantMemoryManager
        5. Returns structured results with business value score and reasoning

        Args:
            asset_data: Asset data to analyze
            db: Database session for TenantMemoryManager

        Returns:
            Business value assessment with score and reasoning
        """
        try:
            logger.info(
                f"🧠 Starting agentic business value analysis for asset: {asset_data.get('name')}"
            )

            # Step 1: Initialize TenantMemoryManager
            memory_manager = TenantMemoryManager(
                crewai_service=self.crewai_service, database_session=db
            )

            # Step 2: Retrieve historical business value patterns
            logger.info("📚 Retrieving historical business value patterns...")
            query_context = {
                "environment": asset_data.get("environment"),
                "criticality": asset_data.get("business_criticality"),
                "asset_type": asset_data.get("asset_type"),
            }

            historical_patterns = await memory_manager.retrieve_similar_patterns(
                client_account_id=int(self.client_account_id),
                engagement_id=int(self.engagement_id),
                pattern_type="business_value_assessment",
                query_context=query_context,
                limit=10,
            )

            logger.info(f"✅ Found {len(historical_patterns)} historical patterns")

            # Step 3: Create and execute the business value crew
            # TODO: Pass historical_patterns to crew context
            crew = self.create_business_value_crew(asset_data)

            # Execute the crew (this will run the agent with all memory tools)
            result = crew.kickoff()

            # Parse the agent's output
            parsed_result = self._parse_agent_output(result, asset_data)

            # Step 4: Store discovered patterns if analysis was successful
            if parsed_result.get("business_value_score", 0) > 0:
                logger.info("💾 Storing discovered business value patterns...")
                pattern_data = {
                    "name": f"business_value_analysis_{asset_data.get('name')}_{datetime.utcnow().isoformat()}",
                    "business_value_score": parsed_result.get("business_value_score"),
                    "confidence_level": parsed_result.get("confidence_level"),
                    "reasoning": parsed_result.get("reasoning"),
                    "environment": asset_data.get("environment"),
                    "asset_type": asset_data.get("asset_type"),
                    "business_criticality": asset_data.get("business_criticality"),
                    "recommendations": parsed_result.get("recommendations", []),
                    "historical_patterns_used": len(historical_patterns),
                }

                pattern_id = await memory_manager.store_learning(
                    client_account_id=int(self.client_account_id),
                    engagement_id=int(self.engagement_id),
                    scope=LearningScope.ENGAGEMENT,
                    pattern_type="business_value_assessment",
                    pattern_data=pattern_data,
                )

                logger.info(f"✅ Stored pattern with ID: {pattern_id}")
                parsed_result["pattern_id"] = pattern_id
                parsed_result["historical_patterns_used"] = len(historical_patterns)

            logger.info(
                f"✅ Business value analysis completed - Score: {parsed_result.get('business_value_score')}"
            )

            return parsed_result

        except Exception as e:
            logger.error(f"❌ Business value analysis failed: {e}")

            # Fallback to reasoning engine if crew fails
            try:
                logger.info("🔄 Falling back to reasoning engine analysis")
                reasoning_result = (
                    await self.reasoning_engine.analyze_asset_business_value(
                        asset_data, "Business Value Agent"
                    )
                )
                return self._convert_reasoning_to_dict(reasoning_result)
            except Exception as fallback_error:
                logger.error(f"❌ Fallback analysis also failed: {fallback_error}")
                return self._create_default_analysis(asset_data)
