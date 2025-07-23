"""
Platform Detection Phase Handler

Handles the platform detection phase of the collection flow.
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
    requires_user_approval
from app.services.crewai_flows.utils.retry_utils import retry_with_backoff

logger = logging.getLogger(__name__)


class PlatformDetectionHandler:
    """Handles platform detection phase of collection flow"""

    def __init__(
        self,
        flow_context,
        state_manager,
        services,
        unified_flow_management,
        crewai_service,
    ):
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.services = services
        self.unified_flow_management = unified_flow_management
        self.crewai_service = crewai_service

    async def detect_platforms(
        self,
        state: CollectionFlowState,
        config: Dict[str, Any],
        initialization_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Phase 1: Detect platforms in the environment"""
        try:
            logger.info("🔍 Starting platform detection phase")

            # Update state
            state.status = CollectionStatus.DETECTING_PLATFORMS
            state.current_phase = CollectionPhase.PLATFORM_DETECTION
            state.updated_at = datetime.utcnow()

            # Perform tier analysis
            tier_analysis = await self.services.tier_detection.analyze_environment_tier(
                environment_config=config.get("environment_config", {}),
                automation_tier=state.automation_tier.value,
            )

            # Create platform detection crew
            from app.services.crewai_flows.crews.collection.platform_detection_crew import \
                create_platform_detection_crew

            crew = create_platform_detection_crew(
                crewai_service=self.crewai_service,
                environment_config=config.get("environment_config", {}),
                tier_assessment=tier_analysis,
                context={
                    "client_requirements": config.get("client_requirements", {}),
                    "automation_tier": state.automation_tier.value,
                },
            )

            # Execute crew
            crew_result = await retry_with_backoff(
                crew.kickoff,
                inputs={
                    "environment_config": config.get("environment_config", {}),
                    "tier_analysis": tier_analysis,
                },
            )

            # Process results
            detected_platforms = crew_result.get("platforms", [])
            adapter_recommendations = crew_result.get("recommended_adapters", [])

            # Store in state
            state.detected_platforms = detected_platforms
            state.collection_config["adapter_recommendations"] = adapter_recommendations
            state.phase_results["platform_detection"] = {
                "platforms": detected_platforms,
                "tier_analysis": tier_analysis,
                "adapter_recommendations": adapter_recommendations,
            }

            # Calculate quality score
            quality_score = await self.services.quality_assessment.assess_platform_detection_quality(
                detected_platforms=detected_platforms, tier_analysis=tier_analysis
            )

            # Update progress
            state.progress = 15.0
            state.next_phase = CollectionPhase.AUTOMATED_COLLECTION

            # Persist state
            await self.state_manager.save_state(state.to_dict())

            # Check if pause required
            if requires_user_approval(
                "platform_detection", config.get("client_requirements", {})
            ):
                state.pause_points.append("platform_detection_approval")
                await self.unified_flow_management.pause_flow(
                    reason="Platform detection completed - user approval required",
                    phase="platform_detection",
                )

            return {
                "phase": "platform_detection",
                "status": "completed",
                "platforms_detected": len(detected_platforms),
                "quality_score": quality_score,
                "next_phase": "automated_collection",
            }

        except Exception as e:
            logger.error(f"❌ Platform detection failed: {e}")
            state.add_error("platform_detection", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Platform detection failed: {e}")
