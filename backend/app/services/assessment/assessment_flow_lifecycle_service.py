"""
Assessment Flow Lifecycle Service

Business logic layer for assessment flow creation, resumption, and state management.
Coordinates between repository, application resolver, MFO, and enrichment pipeline.

Per 7-layer architecture: This is the SERVICE layer that orchestrates operations.
Repository layer (below) handles only data persistence.
API layer (above) handles HTTP concerns and delegates to this service.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.context import RequestContext
from app.models.assessment_flow import AssessmentFlow
from app.models.assessment_flow_state import AssessmentFlowStatus, AssessmentPhase
from app.repositories.assessment_flow_repository import AssessmentFlowRepository
from app.services.assessment.application_resolver import (
    AssessmentApplicationResolver,
)
from app.services.enrichment.auto_enrichment_pipeline import (
    trigger_auto_enrichment_background,
)
from app.services.flow_configs.phase_aliases import normalize_phase_name
from app.services.flow_type_registry import flow_type_registry
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

logger = logging.getLogger(__name__)


class AssessmentFlowLifecycleService:
    """
    Service layer for assessment flow lifecycle operations.

    Responsibilities:
    - Orchestrate flow creation with asset resolution, MFO registration, enrichment
    - Handle flow resumption with phase validation and progression
    - Coordinate between multiple services and repository layer
    - Enforce business rules (unmapped asset thresholds, enrichment warnings)

    Does NOT:
    - Directly access database (uses repository)
    - Handle HTTP concerns (API layer responsibility)
    - Contain data validation logic (Pydantic models handle that)
    """

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        repository: Optional[AssessmentFlowRepository] = None,
    ):
        """
        Initialize service with dependencies.

        Args:
            db: Database session for repository and sub-services
            context: Request context with tenant scoping (client_account_id, engagement_id)
            repository: Optional pre-initialized repository (for testing)
        """
        self.db = db
        self.context = context

        # Initialize repository if not provided
        self.repository = repository or AssessmentFlowRepository(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
            user_id=context.user_id,
        )

        # Initialize sub-services
        self.application_resolver = AssessmentApplicationResolver(
            db=db,
            client_account_id=UUID(str(context.client_account_id)),
            engagement_id=UUID(str(context.engagement_id)),
        )

        self.orchestrator = MasterFlowOrchestrator(db, context)

    async def create_assessment_flow(  # noqa: C901
        self,
        engagement_id: str,
        selected_application_ids: List[str],
        created_by: Optional[str] = None,
        collection_flow_id: Optional[str] = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> str:
        """
        Create new assessment flow with full orchestration.

        Business Logic:
        1. Resolve assets to canonical applications (with grouping)
        2. Calculate enrichment status and readiness summary
        3. Validate unmapped asset thresholds (strict/block/banner modes)
        4. Create master flow via MFO (ADR-012 two-table pattern)
        5. Create child flow record via repository
        6. Trigger auto-enrichment pipeline if enabled
        7. Single atomic commit for master + child flows

        Args:
            engagement_id: Engagement UUID
            selected_application_ids: Asset IDs (DEPRECATED name, actually asset UUIDs)
            created_by: User ID who created the flow
            collection_flow_id: Optional collection flow ID for asset resolution
            background_tasks: FastAPI BackgroundTasks for enrichment

        Returns:
            Master flow ID (UUID as string) - used for all subsequent operations

        Raises:
            ValueError: If unmapped assets exceed threshold in strict/block mode
        """
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

        # STEP 1: Resolve assets to canonical applications (with grouping)
        application_groups = []
        canonical_app_ids = []
        if asset_ids:
            try:
                application_groups = (
                    await self.application_resolver.resolve_assets_to_applications(
                        asset_ids=asset_ids, collection_flow_id=collection_flow_uuid
                    )
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

        # STEP 2: Calculate enrichment status
        enrichment_status = {}
        if asset_ids:
            try:
                enrichment_obj = (
                    await self.application_resolver.calculate_enrichment_status(
                        asset_ids
                    )
                )
                enrichment_status = enrichment_obj.dict()
            except Exception as e:
                logger.error(f"Failed to calculate enrichment status: {e}")

        # STEP 3: Calculate readiness summary
        readiness_summary = {}
        if asset_ids:
            try:
                readiness_obj = (
                    await self.application_resolver.calculate_readiness_summary(
                        asset_ids
                    )
                )
                readiness_summary = readiness_obj.dict()
            except Exception as e:
                logger.error(f"Failed to calculate readiness summary: {e}")

        # Convert application groups to dict for JSONB storage
        application_groups_dict = [
            group.model_dump(mode="json") for group in application_groups
        ]

        # STEP 4: Feature-flagged unmapped asset handling (Phase 1.2 - October 2025)
        unmapped_count = sum(
            1 for group in application_groups if group.canonical_application_id is None
        )
        unmapped_percentage = (
            unmapped_count / len(application_groups) if application_groups else 0
        )

        # Collect unmapped asset names for error/warning messages
        unmapped_names = [
            group.canonical_application_name
            for group in application_groups
            if group.canonical_application_id is None
        ]

        # Log tenant-scoped metrics for monitoring
        if unmapped_count > 0:
            logger.info(
                f"Assessment flow unmapped asset metrics: "
                f"total={len(application_groups)}, "
                f"unmapped={unmapped_count}, "
                f"percentage={unmapped_percentage:.1%}, "
                f"client_account_id={self.context.client_account_id}, "
                f"engagement_id={engagement_id}"
            )

            # Feature-flagged handling based on environment configuration
            if settings.UNMAPPED_ASSET_HANDLING == "strict":
                # Always reject unmapped assets
                # SECURITY: Log full details but sanitize user-facing error message
                logger.warning(
                    f"Strict mode rejection: {unmapped_count} unmapped assets: "
                    f"{', '.join(unmapped_names[:10])}{'...' if len(unmapped_names) > 10 else ''}"
                )
                raise ValueError(
                    f"Assessment initialization blocked: {unmapped_count} "
                    f"unmapped assets detected. "
                    f"Strict mode requires all assets mapped to canonical "
                    f"applications. Use Asset Resolution workflow in "
                    f"collection flow."
                )
            elif settings.UNMAPPED_ASSET_HANDLING == "block":
                # Reject if exceeds threshold
                threshold = settings.UNMAPPED_ASSET_THRESHOLD
                if unmapped_percentage > threshold:
                    # SECURITY: Log full details but sanitize user-facing error message
                    logger.warning(
                        f"Threshold exceeded: {unmapped_count} unmapped assets "
                        f"({unmapped_percentage:.1%}): "
                        f"{', '.join(unmapped_names[:10])}{'...' if len(unmapped_names) > 10 else ''}"
                    )

                    raise ValueError(
                        f"Assessment initialization blocked: "
                        f"{unmapped_percentage:.1%} unmapped assets "
                        f"exceeds threshold of {threshold:.1%}. "
                        f"Found {unmapped_count} unmapped assets. "
                        f"Please complete canonical application mapping to "
                        f"proceed."
                    )
                else:
                    logger.warning(
                        f"Assessment flow has {unmapped_count} unmapped assets "
                        f"({unmapped_percentage:.1%}) but within threshold "
                        f"({threshold:.1%}). Proceeding with banner."
                    )
            else:  # "banner" mode (default)
                logger.warning(
                    f"Assessment flow has {unmapped_count} unmapped assets. "
                    f"Asset Resolution banner will be shown in UI."
                )

        # Warn about missing enrichment data
        total_enrichment = sum(enrichment_status.values()) if enrichment_status else 0
        if total_enrichment == 0 and asset_ids:
            logger.warning(
                f"Assessment flow has no enrichment data for {len(asset_ids)} assets. "
                f"Consider running enrichment pipeline."
            )

        # Warn about low readiness
        avg_completeness = readiness_summary.get("avg_completeness_score", 0.0)
        if avg_completeness < 0.5 and asset_ids:
            logger.warning(
                f"Assessment flow has low readiness: {avg_completeness:.1%}. "
                f"Only {readiness_summary.get('ready', 0)}/{len(asset_ids)} assets ready."
            )

        # Convert string IDs to proper format for JSONB storage
        app_ids_jsonb = [str(app_id) for app_id in selected_application_ids]

        # STEP 5: Create master flow using MasterFlowOrchestrator (ADR-012)
        master_flow_id, _ = await self.orchestrator.create_flow(
            flow_type="assessment",
            flow_name=f"Assessment Flow - {len(selected_application_ids)} Applications",
            configuration={
                "selected_applications": selected_application_ids,
                "assessment_type": "sixr_analysis",
                "created_by": created_by,
                "engagement_id": str(engagement_id),
                "collection_flow_id": collection_flow_id,
            },
            initial_state={
                "phase": AssessmentPhase.INITIALIZATION.value,
                "applications_count": len(selected_application_ids),
            },
            atomic=True,  # Don't commit yet, we're in a transaction
        )

        # Flush to get master_flow_id in DB for FK availability (but don't commit)
        await self.db.flush()

        logger.info(
            f"✅ Created assessment master flow: {master_flow_id}"
            + (
                f" (linked to collection flow {collection_flow_id})"
                if collection_flow_id
                else ""
            )
        )

        # STEP 6: Create child flow with correct master_flow_id FK reference
        flow_record = AssessmentFlow(
            client_account_id=self.context.client_account_id,
            engagement_id=engagement_id,
            master_flow_id=UUID(master_flow_id),
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
            phase_results={},  # Initialize empty to prevent validation failures
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(flow_record)

        # STEP 7: Single atomic commit for both master and child flows (ADR-012)
        await self.db.commit()
        await self.db.refresh(flow_record)

        logger.info(
            f"✅ Created assessment child flow {flow_record.id} with "
            f"{len(application_groups)} application groups, "
            f"{len(asset_ids)} assets, "
            f"readiness: {readiness_summary.get('ready', 0)}/{len(asset_ids)} ready, "
            f"linked to master flow {master_flow_id}"
        )

        # STEP 8: Feature-flagged auto-enrichment (Phase 3.1 - October 2025)
        if settings.AUTO_ENRICHMENT_ENABLED and asset_ids and background_tasks:
            # Trigger background enrichment (non-blocking)
            background_tasks.add_task(
                trigger_auto_enrichment_background,
                db=self.db,
                flow_id=str(flow_record.id),
                client_account_id=self.context.client_account_id,
                engagement_id=engagement_id,
                asset_ids=asset_ids,
            )

            logger.info(
                f"Auto-enrichment triggered for flow {flow_record.id} "
                f"({len(asset_ids)} assets) - background task queued"
            )
        elif settings.AUTO_ENRICHMENT_ENABLED and asset_ids and not background_tasks:
            logger.warning(
                f"Auto-enrichment enabled but no BackgroundTasks provided "
                f"for flow {flow_record.id}"
            )

        logger.info(
            f"✅ Created assessment flow {master_flow_id} for engagement {engagement_id} "
            f"(master flow and child flow linked atomically per ADR-012)"
        )
        return str(master_flow_id)

    async def resume_flow(
        self, flow_id: str, user_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resume assessment flow from pause point, advance to next phase.

        Business Logic:
        1. Fetch current flow state from repository
        2. Validate user's expected phase matches database (phase mismatch detection)
        3. Normalize phase name using ADR-027 phase aliases
        4. Calculate next phase using FlowTypeConfig
        5. Update flow phase and progress via repository
        6. Return transition details for API response

        Args:
            flow_id: Master or child flow ID (supports both per Bug #999)
            user_input: User-provided input including expected phase

        Returns:
            Dict with flow_id, current_phase, previous_phase, progress_percentage, status

        Raises:
            ValueError: If flow not found
        """
        # Get flow configuration from registry (ADR-027)
        flow_config = flow_type_registry.get_flow_config("assessment")

        # Get current flow state via repository
        flow = await self.repository.get_by_flow_id(flow_id)

        if not flow:
            raise ValueError(f"Assessment flow {flow_id} not found")

        current_phase = flow.current_phase
        user_expected_phase = user_input.get("phase")

        logger.info(
            f"[RESUME] flow_id={flow_id}, "
            f"current_phase='{current_phase}', "
            f"user_expected_phase='{user_expected_phase}', "
            f"status={flow.status}, "
            f"progress={flow.progress}"
        )

        # CRITICAL FIX: Validate that user's expected phase matches database
        # This prevents the flow from auto-progressing ahead of user interaction
        if user_expected_phase and user_expected_phase != current_phase:
            logger.warning(
                f"[PHASE-MISMATCH] User expected phase '{user_expected_phase}' "
                f"but database shows '{current_phase}'. Resetting flow to user's phase."
            )
            # Reset via repository
            await self.repository.update_flow_phase(
                flow_id=flow_id,
                current_phase=user_expected_phase,
                progress=flow.progress,
                status=flow.status,
            )
            current_phase = user_expected_phase
            logger.info(
                f"[PHASE-MISMATCH] Reset flow {flow_id} to phase '{current_phase}'"
            )

        # Normalize legacy phase names to ADR-027 canonical names
        try:
            normalized_current_phase = normalize_phase_name("assessment", current_phase)
            logger.info(
                f"Phase normalization: '{current_phase}' -> '{normalized_current_phase}'"
            )
        except ValueError as e:
            logger.warning(
                f"Phase normalization failed for '{current_phase}': {e}. "
                f"Using original phase name as-is."
            )
            normalized_current_phase = current_phase

        # Calculate next phase using FlowTypeConfig (ADR-027)
        next_phase = flow_config.get_next_phase(normalized_current_phase)

        if not next_phase:
            # Already at final phase, stay at current
            next_phase = normalized_current_phase
            logger.warning(
                f"get_next_phase returned None for '{normalized_current_phase}'. "
                f"Flow {flow_id} staying at current phase."
            )

        # Calculate progress percentage
        total_phases = len(flow_config.phases)
        next_phase_index = flow_config.get_phase_index(next_phase)

        if next_phase_index >= 0:
            progress_percentage = int(((next_phase_index + 1) / total_phases) * 100)
        else:
            # Phase not found in config - keep current progress
            progress_percentage = flow.progress or 0
            logger.warning(
                f"Phase {next_phase} not found in flow config, keeping current progress"
            )

        # Save user input for current phase
        current_inputs = flow.user_inputs or {}
        current_inputs[current_phase] = user_input

        # Update flow to next phase via repository
        await self.repository.update_flow_phase(
            flow_id=flow_id,
            current_phase=next_phase,
            progress=progress_percentage,
            status=AssessmentFlowStatus.IN_PROGRESS.value,
        )

        # Update user inputs separately (repository should have this method)
        await self.repository.save_user_input(flow_id, current_phase, user_input)

        logger.info(
            f"[RESUME] COMPLETE - flow_id={flow_id}, "
            f"transition: '{current_phase}' -> '{next_phase}', "
            f"progress: {progress_percentage}%, "
            f"phase_index: {next_phase_index}/{total_phases}"
        )

        return {
            "flow_id": flow_id,
            "current_phase": next_phase,
            "previous_phase": current_phase,
            "progress_percentage": progress_percentage,
            "status": AssessmentFlowStatus.IN_PROGRESS.value,
        }
