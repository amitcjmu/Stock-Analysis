"""
Flow Commands - Core flow management operations
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import AssessmentFlow
from app.models.assessment_flow_state import AssessmentFlowStatus, AssessmentPhase

logger = logging.getLogger(__name__)


class FlowCommands:
    """Commands for core assessment flow operations"""

    def __init__(self, db: AsyncSession, client_account_id: int):
        self.db = db
        self.client_account_id = client_account_id

    async def create_assessment_flow(
        self,
        engagement_id: str,
        selected_application_ids: List[str],
        created_by: Optional[str] = None,
        collection_flow_id: Optional[str] = None,
    ) -> str:
        """
        Create new assessment flow with initial state and register with master flow system.

        ENHANCED (October 2025 - Phase 2 Days 8-9): Now populates application_asset_groups,
        enrichment_status, and readiness_summary during initialization using
        AssessmentApplicationResolver service.

        Collection → Assessment Handoff: When collection_flow_id is provided,
        automatically resolves assets to canonical applications via junction table.

        Args:
            engagement_id: Engagement UUID
            selected_application_ids: Asset IDs (DEPRECATED name, actually asset UUIDs)
            created_by: User ID who created the flow
            collection_flow_id: Optional collection flow ID for asset resolution

        Returns:
            Assessment flow ID (UUID as string)
        """
        from uuid import UUID
        from app.services.assessment.application_resolver import (
            AssessmentApplicationResolver,
        )

        # Convert string IDs to UUIDs for resolver
        try:
            asset_ids = [UUID(aid) for aid in selected_application_ids]
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid asset IDs provided: {e}")
            asset_ids = []

        # Convert collection_flow_id to UUID if provided
        collection_flow_uuid = None
        if collection_flow_id:
            try:
                collection_flow_uuid = UUID(collection_flow_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid collection_flow_id: {collection_flow_id}")

        # Step 1: Initialize AssessmentApplicationResolver
        resolver = AssessmentApplicationResolver(
            db=self.db,
            client_account_id=UUID(str(self.client_account_id)),
            engagement_id=UUID(str(engagement_id)),
        )

        # Step 2: Resolve assets to canonical applications (with grouping)
        application_groups = []
        canonical_app_ids = []
        if asset_ids:
            try:
                application_groups = await resolver.resolve_assets_to_applications(
                    asset_ids=asset_ids, collection_flow_id=collection_flow_uuid
                )

                # Extract canonical application IDs
                canonical_app_ids = [
                    str(group.canonical_application_id)
                    for group in application_groups
                    if group.canonical_application_id is not None
                ]
            except Exception as e:
                logger.error(f"Failed to resolve assets to applications: {e}")
                # Continue with flow creation even if resolution fails

        # Step 3: Calculate enrichment status
        enrichment_status = {}
        if asset_ids:
            try:
                enrichment_obj = await resolver.calculate_enrichment_status(asset_ids)
                enrichment_status = enrichment_obj.dict()
            except Exception as e:
                logger.error(f"Failed to calculate enrichment status: {e}")

        # Step 4: Calculate readiness summary
        readiness_summary = {}
        if asset_ids:
            try:
                readiness_obj = await resolver.calculate_readiness_summary(asset_ids)
                readiness_summary = readiness_obj.dict()
            except Exception as e:
                logger.error(f"Failed to calculate readiness summary: {e}")

        # Step 5: Convert application groups to dict for JSONB storage
        application_groups_dict = [group.dict() for group in application_groups]

        # Step 6: Log warnings for edge cases
        unmapped_count = sum(
            1 for group in application_groups if group.canonical_application_id is None
        )
        if unmapped_count > 0:
            logger.warning(
                f"Assessment flow has {unmapped_count} unmapped assets. "
                f"Consider running canonical deduplication."
            )

        total_enrichment = sum(enrichment_status.values()) if enrichment_status else 0
        if total_enrichment == 0 and asset_ids:
            logger.warning(
                f"Assessment flow has no enrichment data for {len(asset_ids)} assets. "
                f"Consider running enrichment pipeline."
            )

        avg_completeness = readiness_summary.get("avg_completeness_score", 0.0)
        if avg_completeness < 0.5 and asset_ids:
            logger.warning(
                f"Assessment flow has low readiness: {avg_completeness:.1%}. "
                f"Only {readiness_summary.get('ready', 0)}/{len(asset_ids)} assets ready."
            )

        # Convert string IDs to proper format for JSONB storage
        app_ids_jsonb = [str(app_id) for app_id in selected_application_ids]

        flow_record = AssessmentFlow(
            client_account_id=self.client_account_id,
            engagement_id=engagement_id,
            flow_name=f"Assessment Flow - {len(selected_application_ids)} Applications",
            configuration={
                "selected_application_ids": selected_application_ids,
            },
            # DEPRECATED: Keep for backward compatibility (semantic mismatch)
            selected_application_ids=app_ids_jsonb,
            # NEW: Proper semantic fields (October 2025)
            selected_asset_ids=app_ids_jsonb,
            selected_canonical_application_ids=canonical_app_ids,
            application_asset_groups=application_groups_dict,
            enrichment_status=enrichment_status,
            readiness_summary=readiness_summary,
            status=AssessmentFlowStatus.INITIALIZED.value,
            current_phase=AssessmentPhase.INITIALIZATION.value,
            progress=0.0,
            phase_progress={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(flow_record)
        await self.db.commit()
        await self.db.refresh(flow_record)

        # Log creation with metadata
        logger.info(
            f"Created assessment flow {flow_record.id} with "
            f"{len(application_groups)} application groups, "
            f"{len(asset_ids)} assets, "
            f"readiness: {readiness_summary.get('ready', 0)}/{len(asset_ids)} ready"
        )

        # Register with master flow system
        from app.repositories.crewai_flow_state_extensions_repository import (
            CrewAIFlowStateExtensionsRepository,
        )

        try:
            extensions_repo = CrewAIFlowStateExtensionsRepository(
                self.db,
                str(self.client_account_id),
                str(engagement_id),
                user_id=created_by,
            )

            await extensions_repo.create_master_flow(
                flow_id=str(flow_record.id),
                flow_type="assessment",  # Using 'assessment' for consistency
                user_id=created_by or "system",
                flow_name=f"Assessment Flow - {len(selected_application_ids)} Applications",
                flow_configuration={
                    "selected_applications": selected_application_ids,
                    "assessment_type": "sixr_analysis",
                    "created_by": created_by,
                    "engagement_id": str(engagement_id),
                },
                initial_state={
                    "phase": AssessmentPhase.INITIALIZATION.value,
                    "applications_count": len(selected_application_ids),
                },
            )

            logger.info(
                f"Registered assessment flow {flow_record.id} with master flow system"
            )

        except Exception as e:
            logger.error(
                f"Failed to register assessment flow {flow_record.id} with master flow: {e}"
            )
            # Don't fail the entire creation if master flow registration fails
            # The flow still exists and can function, just without master coordination

        logger.info(
            f"Created assessment flow {flow_record.id} for engagement {engagement_id}"
        )
        return str(flow_record.id)

    async def update_flow_phase(
        self,
        flow_id: str,
        current_phase: str,
        next_phase: Optional[str] = None,
        progress: Optional[int] = None,
        status: Optional[str] = None,
    ):
        """Update flow phase and progress, sync with master flow"""

        update_data = {"current_phase": current_phase, "updated_at": datetime.utcnow()}

        if next_phase:
            update_data["next_phase"] = next_phase
        if progress is not None:
            update_data["progress"] = progress
        if status:
            update_data["status"] = status

        await self.db.execute(
            update(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
            .values(**update_data)
        )
        await self.db.commit()

        logger.info(f"Updated flow {flow_id} phase to {current_phase}")

    async def save_user_input(
        self, flow_id: str, phase: str, user_input: Dict[str, Any]
    ):
        """Save user input for specific phase"""

        # Get current user_inputs
        from sqlalchemy import select

        result = await self.db.execute(
            select(AssessmentFlow.user_inputs).where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
        )
        current_inputs = result.scalar() or {}
        current_inputs[phase] = user_input

        await self.db.execute(
            update(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
            .values(
                user_inputs=current_inputs,
                last_user_interaction=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        await self.db.commit()

    async def save_agent_insights(
        self, flow_id: str, phase: str, insights: List[Dict[str, Any]]
    ):
        """Save agent insights for specific phase and log to master flow"""

        # Get current agent insights
        from sqlalchemy import select

        result = await self.db.execute(
            select(AssessmentFlow.agent_insights).where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
        )
        current_insights = result.scalar() or []

        # Add phase context to insights
        phase_insights = [
            {**insight, "phase": phase, "timestamp": datetime.utcnow().isoformat()}
            for insight in insights
        ]
        current_insights.extend(phase_insights)

        await self.db.execute(
            update(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
            .values(agent_insights=current_insights, updated_at=datetime.utcnow())
        )
        await self.db.commit()

    async def resume_flow(
        self, flow_id: str, user_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resume assessment flow from pause point, advance to next phase.
        Per ADR-027: Uses FlowTypeConfig as single source of truth for phase progression.
        Supports legacy phase names via phase alias normalization.
        """
        from sqlalchemy import select

        # Per ADR-027: Get flow configuration from registry
        from app.services.flow_type_registry import flow_type_registry
        from app.services.flow_configs.phase_aliases import normalize_phase_name

        flow_config = flow_type_registry.get_flow_config("assessment")

        # Get current flow state
        result = await self.db.execute(
            select(AssessmentFlow).where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
        )
        flow = result.scalar_one_or_none()

        if not flow:
            raise ValueError(f"Assessment flow {flow_id} not found")

        current_phase = flow.current_phase

        # Normalize legacy phase names to ADR-027 canonical names
        try:
            normalized_current_phase = normalize_phase_name("assessment", current_phase)
            logger.info(
                f"Normalized phase {current_phase} -> {normalized_current_phase}"
            )
        except ValueError as e:
            # Phase not recognized - log warning and keep original
            logger.warning(
                f"Could not normalize phase {current_phase}: {e}. Using as-is."
            )
            normalized_current_phase = current_phase

        # Per ADR-027: Use FlowTypeConfig.get_next_phase() instead of hardcoded array
        next_phase = flow_config.get_next_phase(normalized_current_phase)

        if not next_phase:
            # Already at final phase, stay at current
            next_phase = normalized_current_phase
            logger.info(
                f"Flow {flow_id} already at final phase: {normalized_current_phase}"
            )

        # Per ADR-027: Calculate progress using FlowTypeConfig.get_phase_index()
        total_phases = len(flow_config.phases)
        next_phase_index = flow_config.get_phase_index(next_phase)

        if next_phase_index >= 0:
            progress_percentage = int(((next_phase_index + 1) / total_phases) * 100)
        else:
            # Phase not found in config - use current progress
            progress_percentage = flow.progress or 0
            logger.warning(
                f"Phase {next_phase} not found in flow config, keeping current progress"
            )

        # Save user input for current phase
        current_inputs = flow.user_inputs or {}
        current_inputs[current_phase] = user_input

        # Update flow to next phase
        await self.db.execute(
            update(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
            .values(
                current_phase=next_phase,
                status=AssessmentFlowStatus.IN_PROGRESS.value,
                progress=progress_percentage,
                user_inputs=current_inputs,
                last_user_interaction=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        await self.db.commit()

        logger.info(
            f"Resumed flow {flow_id}: {current_phase} -> {next_phase} ({progress_percentage}%)"
        )

        return {
            "flow_id": flow_id,
            "current_phase": next_phase,
            "previous_phase": current_phase,
            "progress_percentage": progress_percentage,
            "status": AssessmentFlowStatus.IN_PROGRESS.value,
        }
