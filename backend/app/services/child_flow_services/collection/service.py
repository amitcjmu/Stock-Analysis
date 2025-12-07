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
            return await self._execute_questionnaire_generation(
                child_flow, phase_name, phase_input
            )

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

        # CRITICAL: Persist selected_asset_ids to flow_metadata for future phases
        # This ensures questionnaire_generation can access asset IDs even without phase_input
        if selected_asset_ids:
            current_metadata = child_flow.flow_metadata or {}
            current_metadata["selected_asset_ids"] = selected_asset_ids
            child_flow.flow_metadata = current_metadata
            await self.db.commit()
            await self.db.refresh(child_flow)
            logger.info(
                f"Persisted {len(selected_asset_ids)} selected_asset_ids to flow_metadata"
            )

        result = await gap_service.analyze_and_generate_questionnaire(
            selected_asset_ids=selected_asset_ids,
            db=self.db,
            automation_tier=automation_tier,
        )

        # CRITICAL FIX (Issue #1066 + Issue #TBD): Query database as source of truth
        # The summary metadata from gap analysis service can be incorrect/stale
        # Database is the authoritative source for gap count and resolution status
        #
        # CRITICAL FIX: Query by ASSET IDs, not collection_flow_id
        # Gaps are per-asset, not per-flow. Multiple collection flows for the same assets
        # share the same underlying gaps. The unique constraint uq_gaps_dedup includes
        # collection_flow_id, so new flows create new gap records. We must check for
        # pending gaps across ALL gaps for the selected assets.
        from sqlalchemy import select, func
        from app.models.collection_data_gap import CollectionDataGap
        from uuid import UUID as PythonUUID

        # Convert selected_asset_ids to UUIDs for query
        asset_uuids = []
        for aid in selected_asset_ids:
            try:
                if isinstance(aid, str):
                    asset_uuids.append(PythonUUID(aid))
                elif isinstance(aid, PythonUUID):
                    asset_uuids.append(aid)
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid asset ID: {aid}, error: {e}")

        # Query actual pending gaps from database BY ASSET IDs (not by collection_flow_id)
        # This ensures we find gaps regardless of which collection flow created them
        if asset_uuids:
            pending_gaps_result = await self.db.execute(
                select(func.count(CollectionDataGap.id)).where(
                    CollectionDataGap.asset_id.in_(asset_uuids),
                    CollectionDataGap.resolution_status == "pending",
                )
            )
            actual_pending_gaps = pending_gaps_result.scalar() or 0

            logger.info(
                f"Gap query by asset IDs: {len(asset_uuids)} assets → "
                f"{actual_pending_gaps} pending gaps found"
            )
        else:
            # Fallback: If no selected_asset_ids provided, use collection_flow_id
            logger.warning(
                "No selected_asset_ids provided, falling back to collection_flow_id query"
            )
            pending_gaps_result = await self.db.execute(
                select(func.count(CollectionDataGap.id)).where(
                    CollectionDataGap.collection_flow_id == child_flow.id,
                    CollectionDataGap.resolution_status == "pending",
                )
            )
            actual_pending_gaps = pending_gaps_result.scalar() or 0

        # Also get summary metadata for comparison/debugging
        summary = result.get("summary", {})
        gaps_persisted = summary.get("gaps_persisted", 0)
        has_pending_gaps = summary.get("has_pending_gaps", False)

        # Log both values to track discrepancies
        logger.info(
            f"Gap analysis complete - "
            f"Database: {actual_pending_gaps} pending gaps, "
            f"Summary metadata: gaps_persisted={gaps_persisted}, has_pending_gaps={has_pending_gaps}"
        )

        # IMPORTANT: Use database count for auto-progression decision
        if actual_pending_gaps > 0:
            logger.info(
                f"✅ Auto-progression: {actual_pending_gaps} pending gaps found in database → "
                f"transitioning to questionnaire_generation"
            )
            await self.state_service.transition_phase(
                flow_id=child_flow.id,
                new_phase=CollectionPhase.QUESTIONNAIRE_GENERATION,
            )
        else:
            logger.info(
                "✅ Auto-progression: 0 pending gaps in database → "
                "transitioning to finalization (no questionnaires needed)"
            )
            await self.state_service.transition_phase(
                flow_id=child_flow.id, new_phase=CollectionPhase.FINALIZATION
            )

        return result

    async def _execute_questionnaire_generation(
        self, child_flow, phase_name: str, phase_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute questionnaire generation phase.

        Extracted to reduce complexity of execute_phase method (Flake8 C901).
        """
        logger.info(f"Phase '{phase_name}' - questionnaire generation requested")

        from app.models.collection_data_gap import CollectionDataGap
        from sqlalchemy import select
        from uuid import UUID as PythonUUID

        try:
            # CRITICAL FIX: Query gaps by ASSET IDs, not collection_flow_id
            # Get selected_asset_ids from phase_input or flow_metadata
            selected_asset_ids = (phase_input or {}).get("selected_asset_ids", [])

            # If not in phase_input, try to get from flow_metadata
            if not selected_asset_ids and child_flow.flow_metadata:
                selected_asset_ids = child_flow.flow_metadata.get(
                    "selected_asset_ids", []
                )

            # Convert to UUIDs
            asset_uuids = []
            for aid in selected_asset_ids:
                try:
                    if isinstance(aid, str):
                        asset_uuids.append(PythonUUID(aid))
                    elif isinstance(aid, PythonUUID):
                        asset_uuids.append(aid)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid asset ID: {aid}, error: {e}")

            # Get persisted gaps from database BY ASSET IDs
            if asset_uuids:
                logger.info(
                    f"Querying gaps by {len(asset_uuids)} asset IDs for questionnaire generation"
                )
                gaps_result = await self.db.execute(
                    select(CollectionDataGap).where(
                        CollectionDataGap.asset_id.in_(asset_uuids),
                        CollectionDataGap.resolution_status == "pending",
                    )
                )
            else:
                # Fallback: use collection_flow_id (may return 0 results if new flow)
                logger.warning(
                    "No selected_asset_ids available, falling back to collection_flow_id query"
                )
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
