"""
Collection Child Flow Service - Main Implementation
Modularized per pre-commit file length requirements
"""

import logging
from typing import Any, Dict, Optional

from .base import CollectionChildFlowServiceBase
from .phase_handlers.data_validation import execute_data_validation_phase
from .phase_handlers.finalization import execute_finalization_phase
from .phase_handlers.manual_collection import execute_manual_collection_phase
from app.services.collection_flow.state_management import CollectionPhase

logger = logging.getLogger(__name__)


class CollectionChildFlowService(CollectionChildFlowServiceBase):
    """Service for collection flow child operations with phase routing"""

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
            return await self._execute_auto_enrichment_phase(
                child_flow, phase_name, phase_input
            )

        elif phase_name == "gap_analysis":
            return await self._execute_gap_analysis_phase(
                child_flow, phase_name, phase_input
            )

        elif phase_name == "questionnaire_generation":
            return await self._execute_questionnaire_generation(child_flow, phase_name)

        elif phase_name == "manual_collection":
            # Bug #1056-A Fix: Check responses before allowing completion
            return await execute_manual_collection_phase(
                self.db, self.state_service, child_flow, phase_name
            )

        elif phase_name == "data_validation":
            # Bug #1056-B Fix: Validate gap closure
            return await execute_data_validation_phase(
                self.db, self.state_service, child_flow, phase_name
            )

        elif phase_name == "finalization":
            # Bug #1056-C Fix: Final readiness gate
            return await execute_finalization_phase(self.db, child_flow, phase_name)

        else:
            # Unknown phase - return noop success
            logger.info(f"Unknown phase '{phase_name}' - executing as noop")
            return {
                "status": "success",
                "phase": phase_name,
                "execution_type": "noop",
                "message": f"Phase '{phase_name}' not yet implemented",
            }

    async def _execute_auto_enrichment_phase(
        self, child_flow, phase_name: str, phase_input: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute auto-enrichment BEFORE gap analysis (Phase 2 fix)"""
        from app.core.config import settings
        from app.services.enrichment.auto_enrichment_pipeline import (
            AutoEnrichmentPipeline,
        )

        logger.info("Executing auto_enrichment via AutoEnrichmentPipeline")

        # Check feature flag (respecting environment configuration)
        if not getattr(settings, "AUTO_ENRICHMENT_ENABLED", True):
            logger.warning("AUTO_ENRICHMENT_ENABLED=False - skipping enrichment phase")
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
        await self.state_service.transition_phase(
            flow_id=child_flow.id, new_phase=CollectionPhase.GAP_ANALYSIS
        )

        return {
            "status": "success",
            "phase": phase_name,
            "enrichment_results": result,
        }

    async def _execute_gap_analysis_phase(
        self, child_flow, phase_name: str, phase_input: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute gap analysis using GapAnalysisService with persistent agents"""
        from app.services.collection.gap_analysis import GapAnalysisService

        logger.info("Executing gap_analysis via GapAnalysisService")

        gap_service = GapAnalysisService(
            client_account_id=str(self.context.client_account_id),
            engagement_id=str(self.context.engagement_id),
            collection_flow_id=str(child_flow.id),
        )

        # Call analyze_and_generate_questionnaire
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
            logger.info(
                f"Transitioning to questionnaire_generation for persisted gaps "
                f"(gaps_persisted={gaps_persisted})"
            )
            await self.state_service.transition_phase(
                flow_id=child_flow.id,
                new_phase=CollectionPhase.QUESTIONNAIRE_GENERATION,
            )
        elif not has_pending_gaps:
            logger.info("No pending gaps - transitioning to finalization")
            await self.state_service.transition_phase(
                flow_id=child_flow.id, new_phase=CollectionPhase.FINALIZATION
            )
        else:
            logger.info("Gaps exist but not persisted - remaining in gap_analysis")

        return result

    async def _execute_questionnaire_generation(
        self, child_flow, phase_name: str
    ) -> Dict[str, Any]:
        """
        Execute questionnaire generation phase.

        Extracted to reduce complexity of execute_phase method (Flake8 C901).
        """
        logger.info(f"Phase '{phase_name}' - questionnaire generation requested")

        from app.models.collection_data_gap import CollectionDataGap
        from sqlalchemy import select

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
                generate_questionnaires,
                persist_questionnaires,
                prepare_gap_data,
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
