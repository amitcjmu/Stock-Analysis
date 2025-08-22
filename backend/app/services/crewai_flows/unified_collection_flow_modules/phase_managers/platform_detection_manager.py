"""
Platform Detection Phase Manager

Handles the orchestration of platform detection in the collection flow.
This manager creates and executes the platform detection crew, manages state updates,
and handles pause/resume functionality.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.collection_flow import CollectionPhase, CollectionStatus
from app.services.collection_flow import QualityAssessmentService, TierDetectionService
from app.services.crewai_flows.handlers.enhanced_error_handler import (
    enhanced_error_handler,
)
from app.services.crewai_flows.utils.retry_utils import retry_with_backoff

logger = logging.getLogger(__name__)


class PlatformDetectionManager:
    """
    Manages the platform detection phase of the collection flow.

    This manager handles:
    - Environment tier analysis
    - Platform detection crew creation and execution
    - Quality assessment of detected platforms
    - State persistence and updates
    - Pause/resume support for user approval
    """

    def __init__(self, flow_context, state_manager, audit_service):
        """
        Initialize the platform detection manager.

        Args:
            flow_context: Flow context containing flow ID, client, and engagement info
            state_manager: State manager for persisting flow state
            audit_service: Audit logging service
        """
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.audit_service = audit_service

        # Initialize services
        self.tier_detection = TierDetectionService(
            flow_context.db_session, flow_context.context
        )
        self.quality_assessment = QualityAssessmentService(
            flow_context.db_session, flow_context.context
        )

    async def execute(
        self,
        flow_state,
        crewai_service,
        environment_config,
        client_requirements,
        automation_tier,
    ) -> Dict[str, Any]:
        """
        Execute the platform detection phase.

        Args:
            flow_state: Current collection flow state
            crewai_service: CrewAI service for creating crews
            environment_config: Environment configuration
            client_requirements: Client-specific requirements
            automation_tier: Automation tier (tier_1, tier_2, tier_3)

        Returns:
            Dict containing phase execution results
        """
        try:
            logger.info(
                f"🔍 Starting platform detection for flow {self.flow_context.flow_id}"
            )

            # Update state to indicate phase start
            flow_state.status = CollectionStatus.DETECTING_PLATFORMS
            flow_state.current_phase = CollectionPhase.PLATFORM_DETECTION
            flow_state.updated_at = datetime.utcnow()

            # Perform tier analysis
            tier_analysis = await self._perform_tier_analysis(
                environment_config, automation_tier
            )

            # Create and execute platform detection crew
            detection_results = await self._execute_detection_crew(
                crewai_service,
                environment_config,
                tier_analysis,
                client_requirements,
                automation_tier,
            )

            # Process and validate results
            processed_results = await self._process_detection_results(
                detection_results, tier_analysis, flow_state
            )

            # Update flow state with results
            await self._update_flow_state(flow_state, processed_results)

            # Log phase completion
            await self.audit_service.log_flow_event(
                flow_id=self.flow_context.flow_id,
                event_type="platform_detection_completed",
                event_data={
                    "platforms_detected": len(processed_results["detected_platforms"]),
                    "quality_score": processed_results["quality_score"],
                    "tier_analysis": tier_analysis,
                },
            )

            return {
                "phase": "platform_detection",
                "status": "completed",
                "platforms_detected": len(processed_results["detected_platforms"]),
                "quality_score": processed_results["quality_score"],
                "next_phase": "automated_collection",
                "requires_approval": self._requires_approval(
                    processed_results, client_requirements
                ),
            }

        except Exception as e:
            logger.error(f"❌ Platform detection failed: {e}")
            flow_state.add_error("platform_detection", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise

    async def resume(
        self, flow_state, user_inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resume platform detection after pause.

        Args:
            flow_state: Current collection flow state
            user_inputs: Optional user inputs/approvals

        Returns:
            Dict containing resume results
        """
        logger.info(
            f"🔄 Resuming platform detection for flow {self.flow_context.flow_id}"
        )

        if user_inputs and user_inputs.get("approved"):
            # User approved platform detection results
            flow_state.user_inputs["platform_approval"] = user_inputs
            flow_state.last_user_interaction = datetime.utcnow()

            # Update state
            flow_state.progress = 15.0
            flow_state.next_phase = CollectionPhase.AUTOMATED_COLLECTION
            await self.state_manager.save_state(flow_state.to_dict())

            return {
                "phase": "platform_detection",
                "status": "approved",
                "next_phase": "automated_collection",
                "can_proceed": True,
            }
        else:
            # User requested changes
            return {
                "phase": "platform_detection",
                "status": "changes_requested",
                "requires_rerun": True,
            }

    async def _perform_tier_analysis(
        self, environment_config: Dict[str, Any], automation_tier: str
    ) -> Dict[str, Any]:
        """Perform environment tier analysis"""
        logger.info("📊 Performing environment tier analysis")

        tier_analysis = await self.tier_detection.analyze_environment_tier(
            environment_config=environment_config, automation_tier=automation_tier
        )

        logger.info(
            f"✅ Tier analysis complete: {tier_analysis.get('tier_recommendation')}"
        )
        return tier_analysis

    async def _execute_detection_crew(
        self,
        crewai_service,
        environment_config,
        tier_analysis,
        client_requirements,
        automation_tier,
    ) -> Dict[str, Any]:
        """Create and execute the platform detection crew"""
        logger.info("🤖 Creating platform detection crew")

        # Import crew creation function
        from app.services.crewai_flows.crews.collection.platform_detection_crew import (
            create_platform_detection_crew,
        )

        # Create crew with context
        crew = create_platform_detection_crew(
            crewai_service=crewai_service,
            environment_config=environment_config,
            tier_assessment=tier_analysis,
            context={
                "client_requirements": client_requirements,
                "automation_tier": automation_tier,
                "flow_id": self.flow_context.flow_id,
            },
        )

        # Execute with retry
        logger.info("🚀 Executing platform detection crew")
        crew_result = await retry_with_backoff(
            crew.kickoff,
            inputs={
                "environment_config": environment_config,
                "tier_analysis": tier_analysis,
            },
        )

        return crew_result

    async def _process_detection_results(
        self,
        detection_results: Dict[str, Any],
        tier_analysis: Dict[str, Any],
        flow_state,
    ) -> Dict[str, Any]:
        """Process and validate detection results"""
        logger.info("🔧 Processing platform detection results")

        # Extract detected platforms
        detected_platforms = detection_results.get("platforms", [])
        adapter_recommendations = detection_results.get("recommended_adapters", [])

        # Perform quality assessment
        quality_score = await self.quality_assessment.assess_platform_detection_quality(
            detected_platforms=detected_platforms, tier_analysis=tier_analysis
        )

        # Categorize platforms by type
        platform_categories = self._categorize_platforms(detected_platforms)

        return {
            "detected_platforms": detected_platforms,
            "adapter_recommendations": adapter_recommendations,
            "platform_categories": platform_categories,
            "quality_score": quality_score,
            "tier_analysis": tier_analysis,
            "crew_output": detection_results,
        }

    async def _update_flow_state(self, flow_state, processed_results: Dict[str, Any]):
        """Update flow state with detection results"""
        logger.info("💾 Updating flow state with detection results")

        # Update state attributes
        flow_state.detected_platforms = processed_results["detected_platforms"]
        flow_state.collection_config["adapter_recommendations"] = processed_results[
            "adapter_recommendations"
        ]
        flow_state.phase_results["platform_detection"] = {
            "platforms": processed_results["detected_platforms"],
            "tier_analysis": processed_results["tier_analysis"],
            "adapter_recommendations": processed_results["adapter_recommendations"],
            "platform_categories": processed_results["platform_categories"],
            "quality_score": processed_results["quality_score"],
        }

        # Update progress
        flow_state.progress = 15.0
        flow_state.next_phase = CollectionPhase.AUTOMATED_COLLECTION

        # Persist state
        await self.state_manager.save_state(flow_state.to_dict())

    def _categorize_platforms(
        self, platforms: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict]]:
        """Categorize detected platforms by type"""
        categories = {
            "cloud": [],
            "on_premises": [],
            "hybrid": [],
            "saas": [],
            "containerized": [],
        }

        for platform in platforms:
            platform_type = platform.get("type", "").lower()
            if platform_type in categories:
                categories[platform_type].append(platform)
            else:
                # Default to on_premises if unknown
                categories["on_premises"].append(platform)

        return categories

    def _requires_approval(
        self, processed_results: Dict[str, Any], client_requirements: Dict[str, Any]
    ) -> bool:
        """Check if platform detection requires user approval"""
        approval_phases = client_requirements.get("approval_required_phases", [])

        # Check if platform_detection is in approval phases
        if "platform_detection" in approval_phases:
            return True

        # Check quality score threshold
        quality_threshold = client_requirements.get("quality_threshold", 0.8)
        if processed_results["quality_score"] < quality_threshold:
            logger.warning(
                f"Quality score {processed_results['quality_score']} below threshold {quality_threshold}"
            )
            return True

        # Check for critical platforms
        critical_platforms = client_requirements.get("critical_platforms", [])
        detected_names = [
            p.get("name", "").lower() for p in processed_results["detected_platforms"]
        ]

        for critical in critical_platforms:
            if critical.lower() not in detected_names:
                logger.warning(f"Critical platform '{critical}' not detected")
                return True

        return False
