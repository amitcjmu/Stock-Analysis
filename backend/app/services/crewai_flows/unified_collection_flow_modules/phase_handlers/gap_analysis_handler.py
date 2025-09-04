"""
Gap Analysis Phase Handler

Handles the gap analysis phase of the collection flow.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.models.collection_flow import (
    AutomationTier,
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


class GapAnalysisHandler:
    """Handles gap analysis phase of collection flow"""

    def __init__(self, flow_context, state_manager, services, crewai_service):
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.services = services
        self.crewai_service = crewai_service

    async def analyze_gaps(
        self,
        state: CollectionFlowState,
        config: Dict[str, Any],
        collection_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Phase 3: Gap analysis"""
        try:
            logger.info("🔎 Starting gap analysis phase")

            # Update state
            state.status = CollectionStatus.ANALYZING_GAPS
            state.current_phase = CollectionPhase.GAP_ANALYSIS
            state.updated_at = datetime.utcnow()

            # Get collected data
            collected_data = state.collected_data
            collection_gaps = state.phase_results.get("automated_collection", {}).get(
                "identified_gaps", []
            )

            # Perform AI gap analysis
            gap_analysis_result = (
                await self.services.gap_analysis_agent.analyze_data_gaps(
                    collected_data=collected_data,
                    existing_gaps=collection_gaps,
                    sixr_requirements=config.get("client_requirements", {}).get(
                        "sixr_requirements", {}
                    ),
                    automation_tier=state.automation_tier.value,
                )
            )

            # Create gap analysis crew
            from app.services.crewai_flows.crews.collection.gap_analysis_crew import (
                create_gap_analysis_crew,
            )

            crew = create_gap_analysis_crew(
                crewai_service=self.crewai_service,
                collected_data=collected_data,
                sixr_requirements=config.get("client_requirements", {}).get(
                    "sixr_requirements", {}
                ),
                context={
                    "automation_tier": state.automation_tier.value,
                    "existing_gaps": collection_gaps,
                },
            )

            # Execute crew
            crew_result = await retry_with_backoff(
                crew.kickoff,
                inputs={
                    "collected_data": collected_data,
                    "ai_analysis": gap_analysis_result,
                },
            )

            # Process results
            identified_gaps = crew_result.get("data_gaps", [])
            gap_categories = crew_result.get("gap_categories", {})
            sixr_impact = crew_result.get("sixr_impact_analysis", {})

            # Store in state
            state.gap_analysis_results = {
                "identified_gaps": identified_gaps,
                "gap_categories": gap_categories,
                "sixr_impact": sixr_impact,
                "recommendations": crew_result.get("recommendations", []),
            }
            state.phase_results["gap_analysis"] = crew_result

            # Update progress
            state.progress = 55.0

            # Determine next phase based on gaps
            if not identified_gaps or state.automation_tier == AutomationTier.TIER_1:
                state.next_phase = CollectionPhase.DATA_VALIDATION
            else:
                state.next_phase = CollectionPhase.QUESTIONNAIRE_GENERATION

            # Persist state
            await self.state_manager.save_state(state.to_dict())

            # NEW: Populate gap analysis summary table
            try:
                from app.services.gap_analysis_summary_service import (
                    GapAnalysisSummaryService,
                )

                # Get database session from state manager
                if hasattr(self.state_manager, "db"):
                    db = self.state_manager.db
                else:
                    # Fallback - get from flow context if available
                    db = getattr(self.flow_context, "db", None)

                if db:
                    summary_service = GapAnalysisSummaryService(db)

                    # Create request context from flow_context
                    from app.core.context import RequestContext

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
                    if collection_flow_id:
                        await summary_service.populate_gap_analysis_summary(
                            collection_flow_id=collection_flow_id,
                            gap_results=state.gap_analysis_results,
                            context=context,
                        )
                        # Commit the summary - use flush pattern for atomicity
                        await db.flush()
                        logger.info(
                            f"✅ Gap analysis summary populated for collection flow {collection_flow_id}"
                        )
                    else:
                        logger.warning(
                            "Collection flow ID not found in flow context - skipping summary population"
                        )
                else:
                    logger.warning(
                        "Database session not available - skipping gap analysis summary population"
                    )

            except Exception as summary_error:
                # Don't fail the entire gap analysis if summary population fails
                logger.error(
                    f"Failed to populate gap analysis summary: {str(summary_error)}"
                )
                # Continue with normal flow execution

            result = {
                "phase": "gap_analysis",
                "status": "completed",
                "gaps_identified": len(identified_gaps),
                "sixr_impact_score": sixr_impact.get("overall_impact_score", 0.0),
                "next_phase": state.next_phase.value,
            }

            # NEW: Automatic phase transition - trigger next phase if gaps require questionnaires
            if (
                state.next_phase == CollectionPhase.QUESTIONNAIRE_GENERATION
                and identified_gaps
            ):
                logger.info(
                    f"🚀 Gap analysis found {len(identified_gaps)} gaps - automatically triggering questionnaire generation"
                )

                try:
                    # Try to get master flow ID from flow context or state
                    master_flow_id = getattr(self.flow_context, "master_flow_id", None)
                    if not master_flow_id and hasattr(self.flow_context, "flow_id"):
                        # If flow_context.flow_id is the master flow ID
                        master_flow_id = self.flow_context.flow_id

                    if master_flow_id and hasattr(
                        self.flow_context, "client_account_id"
                    ):
                        from app.services.master_flow_orchestrator import (
                            MasterFlowOrchestrator,
                        )
                        from app.core.context import RequestContext

                        # Get database session
                        db = getattr(self.flow_context, "db", None)
                        if hasattr(self.state_manager, "db") and not db:
                            db = self.state_manager.db

                        if db:
                            # Create request context
                            context = RequestContext(
                                client_account_id=self.flow_context.client_account_id,
                                engagement_id=self.flow_context.engagement_id,
                                user_id=getattr(self.flow_context, "user_id", None),
                                tenant_id=getattr(self.flow_context, "tenant_id", None),
                            )

                            # Initialize orchestrator and trigger next phase
                            orchestrator = MasterFlowOrchestrator(db, context)
                            next_result = await orchestrator.execute_phase(
                                flow_id=str(master_flow_id),
                                phase_name="QUESTIONNAIRE_GENERATION",
                            )

                            result["auto_transition"] = {
                                "triggered": True,
                                "next_phase_result": next_result,
                                "message": f"Automatically triggered questionnaire generation for {len(identified_gaps)} gaps",
                            }
                            logger.info(
                                "✅ Automatically triggered questionnaire generation phase"
                            )
                        else:
                            logger.warning(
                                "Database session not available for automatic phase transition"
                            )
                            result["auto_transition"] = {
                                "triggered": False,
                                "reason": "no_db_session",
                            }
                    else:
                        logger.warning(
                            "Master flow ID or context not available for automatic phase transition"
                        )
                        result["auto_transition"] = {
                            "triggered": False,
                            "reason": "missing_context",
                        }

                except Exception as transition_error:
                    logger.error(
                        f"Failed to automatically trigger next phase: {str(transition_error)}"
                    )
                    result["auto_transition"] = {
                        "triggered": False,
                        "error": str(transition_error),
                        "reason": "execution_error",
                    }
                    # Don't fail the gap analysis - just log the transition failure
            else:
                result["auto_transition"] = {
                    "triggered": False,
                    "reason": (
                        "no_gaps_or_validation_phase"
                        if not identified_gaps
                        else "tier1_automation"
                    ),
                }

            return result

        except Exception as e:
            logger.error(f"❌ Gap analysis failed: {e}")
            state.add_error("gap_analysis", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Gap analysis failed: {e}")
