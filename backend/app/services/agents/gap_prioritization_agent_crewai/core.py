"""
Gap Prioritization Agent - Core Prioritization Module
Contains main prioritization methods.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.services.crewai_flows.memory.tenant_memory_manager import (
    TenantMemoryManager,
    LearningScope,
)
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CorePrioritizationMixin:
    """Mixin for core prioritization methods"""

    async def prioritize_gaps_with_memory(
        self,
        gaps: List[Dict[str, Any]],
        context: Dict[str, Any],
        crewai_service: Any,
        client_account_id: int,
        engagement_id: int,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Prioritize identified gaps with TenantMemoryManager integration.
        """
        try:
            logger.info(f"📊 Prioritizing {len(gaps)} identified gaps with memory")

            # Initialize TenantMemoryManager
            memory_manager = TenantMemoryManager(
                crewai_service=crewai_service, database_session=db
            )

            # Retrieve historical gap prioritization patterns
            logger.info("📚 Retrieving historical gap prioritization patterns...")
            query_context = {
                "asset_type": context.get("asset_type"),
                "gap_count": len(gaps),
                "primary_migration_strategy": context.get("primary_migration_strategy"),
            }

            historical_patterns = await memory_manager.retrieve_similar_patterns(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                pattern_type="gap_prioritization",
                query_context=query_context,
                limit=10,
            )

            logger.info(f"✅ Found {len(historical_patterns)} historical patterns")

            # Perform gap prioritization
            prioritization_result = self.prioritize_gaps(gaps, context)

            # Store discovered patterns if prioritization was successful
            if prioritization_result.get("prioritized_gaps"):
                logger.info("💾 Storing discovered gap prioritization patterns...")
                pattern_data = {
                    "name": f"gap_prioritization_{engagement_id}_{datetime.now(timezone.utc).isoformat()}",
                    "total_gaps": prioritization_result.get("total_gaps"),
                    "priority_distribution": prioritization_result.get(
                        "priority_distribution"
                    ),
                    "collection_strategy": prioritization_result.get(
                        "collection_strategy"
                    ),
                    "asset_type": context.get("asset_type"),
                    "primary_migration_strategy": context.get(
                        "primary_migration_strategy"
                    ),
                    "top_priority_gaps": [
                        g["attribute"]
                        for g in prioritization_result.get("prioritized_gaps", [])[:5]
                    ],
                    "historical_patterns_used": len(historical_patterns),
                }

                pattern_id = await memory_manager.store_learning(
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    scope=LearningScope.ENGAGEMENT,
                    pattern_type="gap_prioritization",
                    pattern_data=pattern_data,
                )

                logger.info(f"✅ Stored pattern with ID: {pattern_id}")
                prioritization_result["pattern_id"] = pattern_id
                prioritization_result["historical_patterns_used"] = len(
                    historical_patterns
                )

            logger.info(
                f"✅ Gap prioritization completed - {prioritization_result.get('total_gaps')} gaps processed"
            )

            return prioritization_result

        except Exception as e:
            logger.error(f"❌ Gap prioritization with memory failed: {e}")
            # Fallback to basic prioritization without memory
            return self.prioritize_gaps(gaps, context)

    def prioritize_gaps(
        self, gaps: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prioritize identified gaps based on business impact and collection feasibility
        """
        try:
            logger.info(f"Prioritizing {len(gaps)} identified gaps")

            prioritization_result = {
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "total_gaps": len(gaps),
                "prioritized_gaps": [],
                "priority_distribution": {
                    "priority_1_critical": 0,
                    "priority_2_high": 0,
                    "priority_3_medium": 0,
                    "priority_4_low": 0,
                },
                "collection_strategy": {},
                "resource_requirements": {},
            }

            # Score and prioritize each gap
            scored_gaps = []
            for gap in gaps:
                score, priority = self._calculate_gap_priority(gap, context)
                prioritized_gap = {
                    **gap,
                    "priority_score": score,
                    "priority_level": priority,
                    "collection_recommendation": self._recommend_collection_method(
                        gap, context
                    ),
                    "estimated_effort": self._estimate_collection_effort(gap),
                    "business_justification": self._generate_justification(
                        gap, priority
                    ),
                }
                scored_gaps.append(prioritized_gap)

            # Sort by priority score (descending)
            scored_gaps.sort(key=lambda x: x["priority_score"], reverse=True)
            prioritization_result["prioritized_gaps"] = scored_gaps

            # Update priority distribution
            for gap in scored_gaps:
                priority_key = (
                    f"priority_{gap['priority_level']}_"
                    + {1: "critical", 2: "high", 3: "medium", 4: "low"}[
                        gap["priority_level"]
                    ]
                )
                prioritization_result["priority_distribution"][priority_key] += 1

            # Generate collection strategy
            prioritization_result["collection_strategy"] = (
                self._generate_collection_strategy(scored_gaps, context)
            )

            # Calculate resource requirements
            prioritization_result["resource_requirements"] = (
                self._calculate_resource_requirements(scored_gaps)
            )

            return prioritization_result

        except Exception as e:
            logger.error(f"Error in gap prioritization: {e}")
            return {"error": str(e)}
