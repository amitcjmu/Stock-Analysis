"""
Collection Child Flow Service
Service for managing collection flow child operations following ADR-025
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.collection_flow_repository import CollectionFlowRepository
from app.services.child_flow_services.base import BaseChildFlowService
from app.services.collection_flow.state_management import (
    CollectionFlowStateService,
    CollectionPhase,
)

logger = logging.getLogger(__name__)


class CollectionChildFlowService(BaseChildFlowService):
    """Service for collection flow child operations"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        super().__init__(db, context)
        # Initialize repository with explicit tenant scoping (per ADR-025)
        self.repository = CollectionFlowRepository(
            db=self.db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
        )
        self.state_service = CollectionFlowStateService(db, context)

    async def get_child_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get collection flow child status

        Args:
            flow_id: Master flow identifier

        Returns:
            Child flow status dictionary or None
        """
        try:
            child_flow = await self.repository.get_by_master_flow_id(UUID(flow_id))
            if not child_flow:
                logger.warning(f"Collection flow not found for master flow {flow_id}")
                return None

            return {
                "status": child_flow.status,
                "current_phase": child_flow.current_phase,
                "progress_percentage": child_flow.progress_percentage,
                "automation_tier": child_flow.automation_tier,
                "collection_config": child_flow.collection_config,
                # Per ADR-028: phase_state field removed from collection_flow
            }
        except Exception as e:
            logger.warning(f"Failed to get collection child flow status: {e}")
            return None

    async def get_by_master_flow_id(self, flow_id: str):
        """
        Get collection flow by master flow ID

        Args:
            flow_id: Master flow identifier (UUID string)

        Returns:
            Collection flow entity or None
        """
        try:
            return await self.repository.get_by_master_flow_id(UUID(flow_id))
        except Exception as e:
            logger.warning(f"Failed to get collection flow by master ID: {e}")
            return None

    async def execute_phase(
        self,
        flow_id: str,
        phase_name: str,
        phase_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute phase using persistent agents

        Args:
            flow_id: Master flow identifier
            phase_name: Phase to execute
            phase_input: Optional input data for the phase

        Returns:
            Phase execution result dictionary

        Raises:
            ValueError: If collection flow not found for master flow ID
        """
        child_flow = await self.get_by_master_flow_id(flow_id)
        if not child_flow:
            raise ValueError(f"Collection flow not found for master flow {flow_id}")

        logger.info(
            f"Executing collection phase '{phase_name}' for flow {flow_id} "
            f"(child_flow.id={child_flow.id})"
        )

        # Route to phase handler based on phase name
        if phase_name == "asset_selection":
            # User must select assets - return awaiting input
            logger.info(f"Phase '{phase_name}' - awaiting user asset selection")
            return {"status": "awaiting_user_input", "phase": phase_name}

        elif phase_name == "auto_enrichment":
            # Execute auto-enrichment BEFORE gap analysis (Phase 2 fix)
            # Per BULK_UPLOAD_ENRICHMENT_ARCHITECTURE_ANALYSIS.md Part 6.1
            from app.services.enrichment.auto_enrichment_pipeline import (
                AutoEnrichmentPipeline,
            )
            from app.core.config import settings

            logger.info("Executing auto_enrichment via AutoEnrichmentPipeline")

            # Check feature flag (respecting environment configuration)
            if not getattr(settings, "AUTO_ENRICHMENT_ENABLED", True):
                logger.warning(
                    "AUTO_ENRICHMENT_ENABLED=False - skipping enrichment phase"
                )
                # Auto-transition to gap_analysis
                await self.state_service.transition_phase(
                    flow_id=child_flow.id, new_phase=CollectionPhase.GAP_ANALYSIS
                )
                return {
                    "status": "skipped",
                    "phase": phase_name,
                    "reason": "AUTO_ENRICHMENT_ENABLED feature flag disabled",
                }

            # Get asset_ids from phase_input (selected in asset_selection phase)
            asset_ids = (phase_input or {}).get("selected_asset_ids", [])
            if not asset_ids:
                logger.warning("No asset_ids provided for enrichment - skipping")
                # Auto-transition to gap_analysis even if no assets
                await self.state_service.transition_phase(
                    flow_id=child_flow.id, new_phase=CollectionPhase.GAP_ANALYSIS
                )
                return {
                    "status": "skipped",
                    "phase": phase_name,
                    "reason": "No assets selected for enrichment",
                }

            # Initialize AutoEnrichmentPipeline with tenant scoping
            enrichment_pipeline = AutoEnrichmentPipeline(
                db=self.db,
                client_account_id=self.context.client_account_id,
                engagement_id=self.context.engagement_id,
            )

            # Execute enrichment with Phase 2.3 backpressure controls
            result = await enrichment_pipeline.trigger_auto_enrichment(asset_ids)

            logger.info(
                f"Auto-enrichment completed: {result.get('total_assets', 0)} assets, "
                f"{result.get('elapsed_time_seconds', 0):.1f}s"
            )

            # Auto-transition to gap_analysis after enrichment completes
            # CRITICAL: Gap analysis now sees enriched data
            await self.state_service.transition_phase(
                flow_id=child_flow.id, new_phase=CollectionPhase.GAP_ANALYSIS
            )

            return {
                "status": "success",
                "phase": phase_name,
                "enrichment_results": result,
            }

        elif phase_name == "gap_analysis":
            # Execute gap analysis using GapAnalysisService with persistent agents
            from app.services.collection.gap_analysis import GapAnalysisService

            logger.info("Executing gap_analysis via GapAnalysisService")

            # CRITICAL: GapAnalysisService uses different constructor
            # (client_account_id, engagement_id, collection_flow_id)
            # Use child_flow.id (UUID PK) for collection_flow_id
            gap_service = GapAnalysisService(
                client_account_id=str(self.context.client_account_id),
                engagement_id=str(self.context.engagement_id),
                collection_flow_id=str(child_flow.id),  # ✅ UUID PK
            )

            # Call analyze_and_generate_questionnaire (actual method name)
            # Pass selected_asset_ids from phase_input if available
            selected_asset_ids = (phase_input or {}).get("selected_asset_ids", [])
            automation_tier = (phase_input or {}).get("automation_tier", "tier_2")

            result = await gap_service.analyze_and_generate_questionnaire(
                selected_asset_ids=selected_asset_ids,
                db=self.db,
                automation_tier=automation_tier,
            )

            # Auto-progression logic based on gap analysis results
            summary = result.get("summary", {})
            gaps_persisted = summary.get("gaps_persisted", 0)
            has_pending_gaps = summary.get("has_pending_gaps", False)

            logger.info(
                f"Gap analysis complete: gaps_persisted={gaps_persisted}, "
                f"has_pending_gaps={has_pending_gaps}"
            )

            if gaps_persisted > 0:
                # Gaps persisted → transition to questionnaire_generation
                # Per Qodo review: Use QUESTIONNAIRE_GENERATION phase when gaps are identified
                logger.info(
                    f"Transitioning to questionnaire_generation for persisted gaps "
                    f"(gaps_persisted={gaps_persisted})"
                )
                await self.state_service.transition_phase(
                    flow_id=child_flow.id,
                    new_phase=CollectionPhase.QUESTIONNAIRE_GENERATION,
                )
            elif not has_pending_gaps:
                # No pending gaps → transition to finalization
                logger.info("No pending gaps - transitioning to finalization")
                await self.state_service.transition_phase(
                    flow_id=child_flow.id, new_phase=CollectionPhase.FINALIZATION
                )
            else:
                # Job persisted but gaps still exist → stay in gap_analysis
                logger.info("Gaps exist but not persisted - remaining in gap_analysis")
                # No phase transition needed - stay in current phase

            return result

        elif phase_name == "questionnaire_generation":
            # Generate questionnaires from persisted gaps using QuestionnaireGenerationTool
            return await self._execute_questionnaire_generation(child_flow, phase_name)

        elif phase_name == "manual_collection":
            # User must manually provide responses - return awaiting input
            logger.info(f"Phase '{phase_name}' - awaiting user responses")
            return {"status": "awaiting_user_responses", "phase": phase_name}

        elif phase_name == "data_validation":
            # Validate collected data using ValidationService
            # NOTE: This service may not exist yet - implementing stub per plan
            logger.info(f"Phase '{phase_name}' - data validation requested")

            # For now, return success with placeholder
            # TODO: Implement actual ValidationService when ready
            logger.warning(
                "ValidationService not yet implemented - returning placeholder"
            )
            return {
                "status": "success",
                "phase": phase_name,
                "execution_type": "stub",
                "message": "Validation service pending implementation",
            }

        else:
            # Unknown phase - return noop success
            logger.info(f"Unknown phase '{phase_name}' - executing as noop")
            return {
                "status": "success",
                "phase": phase_name,
                "execution_type": "noop",
                "message": f"Phase '{phase_name}' not yet implemented",
            }

    async def _execute_questionnaire_generation(
        self, child_flow, phase_name: str
    ) -> Dict[str, Any]:
        """
        Execute questionnaire generation phase.

        Extracted to reduce complexity of execute_phase method (Flake8 C901).

        Args:
            child_flow: Collection flow entity
            phase_name: Phase name ("questionnaire_generation")

        Returns:
            Phase execution result dictionary
        """
        logger.info(f"Phase '{phase_name}' - questionnaire generation requested")

        # Import required services
        from sqlalchemy import select
        from app.models.collection_data_gap import CollectionDataGap

        try:
            # Get persisted gaps from database
            gaps_result = await self.db.execute(
                select(CollectionDataGap).where(
                    CollectionDataGap.collection_flow_id == child_flow.id,
                    CollectionDataGap.resolution_status == "pending",
                )
            )
            persisted_gaps = gaps_result.scalars().all()

            if not persisted_gaps:
                logger.info(
                    "No pending gaps found - transitioning to manual_collection"
                )
                await self.state_service.transition_phase(
                    flow_id=child_flow.id,
                    new_phase=CollectionPhase.MANUAL_COLLECTION,
                )
                return {
                    "status": "success",
                    "phase": phase_name,
                    "message": "No gaps to generate questionnaires for",
                    "questionnaires_generated": 0,
                }

            logger.info(
                f"Found {len(persisted_gaps)} pending gaps for questionnaire generation"
            )

            # Import helper functions
            from app.services.child_flow_services.questionnaire_helpers import (
                prepare_gap_data,
                generate_questionnaires,
                persist_questionnaires,
            )

            # Transform gaps and generate questionnaires using helper functions
            data_gaps, business_context = await prepare_gap_data(
                self.db, self.context, persisted_gaps, child_flow
            )

            generation_result = await generate_questionnaires(
                data_gaps, business_context
            )

            if generation_result.get("status") != "success":
                logger.error(
                    f"Questionnaire generation failed: {generation_result.get('error')}"
                )
                return {
                    "status": "failed",
                    "phase": phase_name,
                    "error": generation_result.get("error", "Unknown error"),
                }

            # Persist and transition using helper function
            return await persist_questionnaires(
                self.db,
                self.context,
                self.state_service,
                generation_result,
                persisted_gaps,
                child_flow,
                phase_name,
            )

        except Exception as e:
            logger.error(
                f"Error in questionnaire_generation phase: {e}",
                exc_info=True,
            )
            return {
                "status": "failed",
                "phase": phase_name,
                "error": str(e),
                "error_type": type(e).__name__,
            }
