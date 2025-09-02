"""
Manual Collection Phase Handler

Handles the manual data collection phase of the collection flow.
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
from app.services.crewai_flows.utils.retry_utils import retry_with_backoff

logger = logging.getLogger(__name__)


class ManualCollectionHandler:
    """Handles manual collection phase of collection flow"""

    def __init__(self, flow_context, state_manager, services, crewai_service):
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.services = services
        self.crewai_service = crewai_service

    async def manual_collection(
        self,
        state: CollectionFlowState,
        config: Dict[str, Any],
        questionnaire_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Phase 5: Manual data collection"""
        try:
            logger.info("👤 Starting manual collection phase")

            # Update state
            state.status = CollectionStatus.MANUAL_COLLECTION
            state.current_phase = CollectionPhase.MANUAL_COLLECTION
            state.updated_at = datetime.utcnow()

            # Get questionnaires and gaps
            questionnaires = state.questionnaires
            identified_gaps = state.gap_analysis_results.get("identified_gaps", [])

            # Create manual collection crew
            from app.services.crewai_flows.crews.collection.manual_collection_crew import (
                create_manual_collection_crew,
            )

            crew = create_manual_collection_crew(
                crewai_service=self.crewai_service,
                questionnaires=questionnaires,
                data_gaps=identified_gaps,
                context={
                    "existing_data": state.collected_data,
                    "user_inputs": state.user_inputs,
                },
            )

            # Execute crew
            crew_result = await retry_with_backoff(
                crew.kickoff,
                inputs={
                    "questionnaires": questionnaires,
                    "user_responses": state.user_inputs.get("manual_responses", {}),
                },
            )

            # Process responses
            responses = crew_result.get("responses", [])
            validation_results = crew_result.get("validation", {})

            # Validate responses
            validated_responses = (
                await self.services.validation_service.validate_questionnaire_responses(
                    responses=responses,
                    validation_rules=config.get("client_requirements", {}).get(
                        "validation_rules", {}
                    ),
                    gap_context=identified_gaps,
                )
            )

            # Store in state
            state.manual_responses = validated_responses
            state.phase_results["manual_collection"] = {
                "responses": validated_responses,
                "validation_results": validation_results,
                "remaining_gaps": crew_result.get("unresolved_gaps", []),
            }

            # Update progress
            state.progress = 85.0
            state.next_phase = CollectionPhase.DATA_VALIDATION

            # Persist state
            await self.state_manager.save_state(state.to_dict())

            # NEW: Populate collected_data_inventory table for manual responses
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

                    if collection_flow_id and validated_responses:
                        # Transform manual responses into inventory format
                        inventory_data = []
                        for response in validated_responses:
                            inventory_item = {
                                "platform": "manual_input",
                                "data_type": response.get(
                                    "question_type", "questionnaire_response"
                                ),
                                "raw_data": response,
                                "normalized_data": response.get("normalized_data"),
                                "quality_score": response.get("validation_score"),
                                "validation_status": (
                                    "valid"
                                    if response.get("is_valid", True)
                                    else "invalid"
                                ),
                                "validation_errors": response.get("validation_errors"),
                                "metadata": {
                                    "questionnaire_id": response.get(
                                        "questionnaire_id"
                                    ),
                                    "question_id": response.get("question_id"),
                                    "gap_context": identified_gaps,
                                },
                            }
                            inventory_data.append(inventory_item)

                        # Populate inventory table
                        await inventory_service.populate_collected_data(
                            collection_flow_id=collection_flow_id,
                            collected_data=inventory_data,
                            collection_method="manual",
                            context=context,
                            adapter_id=None,  # Manual collection doesn't use adapters
                        )
                        # Commit the inventory data - use flush pattern for atomicity
                        await db.flush()
                        logger.info(
                            f"✅ Populated collected data inventory with {len(inventory_data)} manual responses for collection flow {collection_flow_id}"
                        )
                    else:
                        logger.warning(
                            f"Collection flow ID not found or no responses collected - skipping manual inventory population"
                        )
                else:
                    logger.warning(
                        "Database session not available - skipping manual collected data inventory population"
                    )

            except Exception as inventory_error:
                # Don't fail the entire collection if inventory population fails
                logger.error(
                    f"Failed to populate manual collected data inventory: {str(inventory_error)}"
                )
                # Continue with normal flow execution

            return {
                "phase": "manual_collection",
                "status": "completed",
                "responses_collected": len(validated_responses),
                "validation_pass_rate": validation_results.get("pass_rate", 0.0),
                "next_phase": "data_validation",
            }

        except Exception as e:
            logger.error(f"❌ Manual collection failed: {e}")
            state.add_error("manual_collection", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Manual collection failed: {e}")
