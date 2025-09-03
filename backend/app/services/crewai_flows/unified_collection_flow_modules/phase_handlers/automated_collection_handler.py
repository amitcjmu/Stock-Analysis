"""
Automated Collection Phase Handler

Handles the automated data collection phase of the collection flow.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.models.collection_flow import (
    CollectionFlowError,
    CollectionFlowState,
    CollectionPhase,
    CollectionStatus,
)
from app.services.crewai_flows.handlers.enhanced_error_handler import (
    enhanced_error_handler,
)
from app.services.crewai_flows.unified_collection_flow_modules.flow_utilities import (
    get_available_adapters,
)
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
            from app.services.crewai_flows.crews.collection.automated_collection_crew import (
                create_automated_collection_crew,
            )

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

            # NEW: Populate collected_data_inventory table
            try:
                from app.services.collected_data_inventory_service import (
                    CollectedDataInventoryService,
                )

                # Get database session from state manager
                if hasattr(self.state_manager, "db"):
                    db = self.state_manager.db
                else:
                    # Fallback - get from flow context if available
                    db = getattr(self.flow_context, "db", None)

                if db:
                    inventory_service = CollectedDataInventoryService(db)

                    # Create request context from flow_context
                    from app.api.dependencies import RequestContext

                    context = RequestContext(
                        client_account_id=self.flow_context.client_account_id,
                        engagement_id=self.flow_context.engagement_id,
                        user_id=getattr(self.flow_context, "user_id", None),
                        tenant_id=getattr(self.flow_context, "tenant_id", None),
                    )

                    # Get collection flow ID from flow context
                    collection_flow_id = getattr(
                        self.flow_context, "collection_flow_id", None
                    )

                    if collection_flow_id and transformed_data:
                        # Transform collected data into inventory format
                        inventory_data = []
                        for item in transformed_data:
                            inventory_item = {
                                "platform": item.get("platform", "unknown"),
                                "data_type": item.get("data_type", "unknown"),
                                "raw_data": item.get("raw_data", item),
                                "normalized_data": item.get("normalized_data"),
                                "quality_score": item.get("quality_score"),
                                "validation_status": "pending",
                                "metadata": {
                                    "automation_tier": state.automation_tier.value,
                                    "collection_metrics": collection_metrics,
                                },
                            }
                            inventory_data.append(inventory_item)

                        # Populate inventory table
                        await inventory_service.populate_collected_data(
                            collection_flow_id=collection_flow_id,
                            collected_data=inventory_data,
                            collection_method="automated",
                            context=context,
                            adapter_id=None,  # TODO: Get from adapter recommendations
                        )
                        # Commit the inventory data - use flush pattern for atomicity
                        await db.flush()
                        logger.info(
                            f"✅ Populated collected data inventory with {len(inventory_data)} items for collection flow {collection_flow_id}"
                        )
                    else:
                        logger.warning(
                            f"Collection flow ID not found or no data collected - skipping inventory population"
                        )
                else:
                    logger.warning(
                        "Database session not available - skipping collected data inventory population"
                    )

            except Exception as inventory_error:
                # Don't fail the entire collection if inventory population fails
                logger.error(
                    f"Failed to populate collected data inventory: {str(inventory_error)}"
                )
                # Continue with normal flow execution

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
