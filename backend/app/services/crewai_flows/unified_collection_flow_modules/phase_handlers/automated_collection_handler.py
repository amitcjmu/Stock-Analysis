"""
Automated Collection Phase Handler

Handles the automated data collection phase of the collection flow.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.models.collection_flow import (CollectionFlowError,
                                        CollectionFlowState, CollectionPhase,
                                        CollectionStatus)
from app.services.crewai_flows.handlers.enhanced_error_handler import \
    enhanced_error_handler
from app.services.crewai_flows.unified_collection_flow_modules.flow_utilities import \
    get_available_adapters
from app.services.crewai_flows.utils.retry_utils import retry_with_backoff

logger = logging.getLogger(__name__)


class AutomatedCollectionHandler:
    """Handles automated collection phase of collection flow"""

    def __init__(self, flow_context, state_manager, services, crewai_service):
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.services = services
        self.crewai_service = crewai_service

    async def automated_collection(
        self,
        state: CollectionFlowState,
        config: Dict[str, Any],
        platform_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Phase 2: Automated data collection"""
        try:
            logger.info("🤖 Starting automated collection phase")

            # Update state
            state.status = CollectionStatus.COLLECTING_DATA
            state.current_phase = CollectionPhase.AUTOMATED_COLLECTION
            state.updated_at = datetime.utcnow()

            # Get detected platforms
            detected_platforms = state.detected_platforms
            adapter_recommendations = state.collection_config.get(
                "adapter_recommendations", []
            )

            # Create automated collection crew
            from app.services.crewai_flows.crews.collection.automated_collection_crew import \
                create_automated_collection_crew

            crew = create_automated_collection_crew(
                crewai_service=self.crewai_service,
                platforms=detected_platforms,
                tier_assessments=state.phase_results.get("platform_detection", {}).get(
                    "tier_analysis", {}
                ),
                context={
                    "available_adapters": get_available_adapters(),
                    "collection_timeout_minutes": 60,
                    "quality_thresholds": {"minimum": 0.8},
                },
            )

            # Execute crew
            crew_result = await retry_with_backoff(
                crew.kickoff,
                inputs={
                    "platforms": detected_platforms,
                    "adapter_configs": adapter_recommendations,
                },
            )

            # Process collected data
            collected_data = crew_result.get("collected_data", [])
            collection_metrics = crew_result.get("collection_metrics", {})

            # Transform data
            transformed_data = (
                await self.services.data_transformation.transform_collected_data(
                    raw_data=collected_data,
                    platforms=detected_platforms,
                    normalization_rules=config.get("client_requirements", {}).get(
                        "normalization_rules", {}
                    ),
                )
            )

            # Store in state
            state.collected_data = transformed_data
            state.collection_results = {
                "raw_data": collected_data,
                "transformed_data": transformed_data,
                "metrics": collection_metrics,
            }
            state.phase_results["automated_collection"] = crew_result

            # Calculate quality score
            quality_scores = (
                await self.services.quality_assessment.assess_collection_quality(
                    collected_data=transformed_data,
                    expected_platforms=detected_platforms,
                    automation_tier=state.automation_tier.value,
                )
            )
            state.collection_quality_score = quality_scores.get("overall_quality", 0.0)

            # Update progress
            state.progress = 40.0
            state.next_phase = CollectionPhase.GAP_ANALYSIS

            # Persist state
            await self.state_manager.save_state(state.to_dict())

            return {
                "phase": "automated_collection",
                "status": "completed",
                "data_collected": len(transformed_data),
                "quality_score": state.collection_quality_score,
                "next_phase": "gap_analysis",
            }

        except Exception as e:
            logger.error(f"❌ Automated collection failed: {e}")
            state.add_error("automated_collection", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Automated collection failed: {e}")
