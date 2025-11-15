"""
Data Validation Phase Handler
Bug #1056-B Fix: Validates gap closure before finalization
"""

import logging
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_data_gap import CollectionDataGap
from app.services.collection_flow.state_management import (
    CollectionFlowStateService,
    CollectionPhase,
)

logger = logging.getLogger(__name__)


async def execute_data_validation_phase(
    db: AsyncSession,
    state_service: CollectionFlowStateService,
    child_flow: Any,
    phase_name: str,
) -> Dict[str, Any]:
    """
    Data Validation Phase Handler

    Purpose: Validate that collected responses have closed the identified data gaps
    before allowing the flow to proceed to finalization.

    Validation Steps:
    1. Re-query gaps from database to check resolution status
    2. Categorize gaps by priority and impact_on_sixr
    3. Calculate gap closure percentage
    4. Decide whether to proceed or pause for user review

    Completion Criteria:
    - All critical gaps (impact_on_sixr='critical' OR priority >= 80) must be closed
    - High-priority gaps (impact_on_sixr='high' OR priority >= 60) should be closed
    - Medium/low priority gaps can remain (acceptable for assessment)

    Auto-Progression:
    - If all critical gaps closed → transition to finalization
    - If critical gaps remain → pause for user review/additional data
    """
    logger.info(f"📋 Phase '{phase_name}' - validating gap closure")

    try:
        # Query current gaps from database
        gaps_result = await db.execute(
            select(CollectionDataGap).where(
                CollectionDataGap.collection_flow_id == child_flow.id
            )
        )
        all_gaps = list(gaps_result.scalars().all())

        if not all_gaps:
            # No gaps were identified in the first place - proceed to finalization
            logger.info("✅ No gaps were identified - proceeding to finalization")
            await state_service.transition_phase(
                flow_id=child_flow.id,
                new_phase=CollectionPhase.FINALIZATION,
            )
            return {
                "status": "completed",
                "phase": phase_name,
                "validation_result": {
                    "total_gaps": 0,
                    "critical_gaps_remaining": 0,
                    "gap_closure_percentage": 100.0,
                    "all_critical_gaps_closed": True,
                },
                "message": "No gaps to validate - proceeding to finalization",
                "next_phase": "finalization",
            }

        # Categorize gaps by resolution status
        # Resolution status values: pending, resolved, skipped, auto_resolved
        pending_gaps = [g for g in all_gaps if g.resolution_status == "pending"]
        resolved_gaps = [
            g
            for g in all_gaps
            if g.resolution_status in ["resolved", "skipped", "auto_resolved"]
        ]

        # Further categorize pending gaps by priority and impact
        # CRITICAL: impact_on_sixr='critical' OR priority >= 80
        critical_pending = [
            g
            for g in pending_gaps
            if g.impact_on_sixr == "critical" or g.priority >= 80
        ]

        # HIGH: impact_on_sixr='high' OR priority >= 60 (and not already critical)
        high_pending = [
            g
            for g in pending_gaps
            if (g.impact_on_sixr == "high" or g.priority >= 60)
            and g not in critical_pending
        ]

        # MEDIUM: impact_on_sixr='medium' OR priority >= 40
        medium_pending = [
            g
            for g in pending_gaps
            if (g.impact_on_sixr == "medium" or (40 <= g.priority < 60))
            and g not in critical_pending
            and g not in high_pending
        ]

        # LOW: everything else
        low_pending = [
            g
            for g in pending_gaps
            if g not in critical_pending
            and g not in high_pending
            and g not in medium_pending
        ]

        total_gaps = len(all_gaps)
        total_resolved = len(resolved_gaps)
        total_pending = len(pending_gaps)
        critical_pending_count = len(critical_pending)

        # Calculate gap closure percentage
        gap_closure_percentage = (
            (total_resolved / total_gaps * 100) if total_gaps > 0 else 100.0
        )

        logger.info(
            f"📊 Gap validation results: "
            f"{total_resolved}/{total_gaps} closed ({gap_closure_percentage:.1f}%), "
            f"{critical_pending_count} critical gaps remain"
        )

        # Determine if validation passes
        # CRITICAL REQUIREMENT: All critical gaps must be closed
        validation_passes = critical_pending_count == 0

        if not validation_passes:
            # Critical gaps remain - pause for user review
            logger.warning(
                f"⚠️ Data validation incomplete: {critical_pending_count} critical gaps remain - "
                "pausing for user review"
            )

            # Prepare details about remaining critical gaps
            critical_gap_details = [
                {
                    "field_name": g.field_name,
                    "priority": g.priority,
                    "gap_category": g.gap_category,
                    "impact_on_sixr": g.impact_on_sixr,
                    "gap_id": str(g.id),
                }
                for g in critical_pending[:10]  # Limit to first 10 for response size
            ]

            return {
                "status": "paused",
                "phase": phase_name,
                "validation_result": {
                    "total_gaps": total_gaps,
                    "resolved_gaps": total_resolved,
                    "pending_gaps": total_pending,
                    "critical_gaps_remaining": critical_pending_count,
                    "high_gaps_remaining": len(high_pending),
                    "medium_gaps_remaining": len(medium_pending),
                    "low_gaps_remaining": len(low_pending),
                    "gap_closure_percentage": round(gap_closure_percentage, 1),
                    "all_critical_gaps_closed": False,
                    "critical_gap_details": critical_gap_details,
                },
                "reason": "critical_gaps_remaining",
                "message": f"{critical_pending_count} critical gap(s) remain unresolved",
                "user_action_required": "review_and_provide_missing_data",
                "suggested_actions": [
                    "Review critical gap details",
                    "Provide missing data via questionnaire responses",
                    "Update asset data directly if applicable",
                    "Contact support if data is unavailable",
                ],
            }

        # Validation passes - all critical gaps closed
        # Check high-priority gaps as optional quality gate
        high_priority_threshold = 0.7  # Allow up to 30% high gaps to remain
        high_gap_ratio = len(high_pending) / total_gaps if total_gaps > 0 else 0

        validation_warning = None
        if high_gap_ratio > (1 - high_priority_threshold):
            # Too many high gaps remain - recommend review but allow proceed
            logger.warning(
                f"⚠️ {len(high_pending)} high-priority gaps remain ({high_gap_ratio*100:.1f}% of total) - "
                "recommending user review but allowing progression"
            )
            validation_warning = (
                f"{len(high_pending)} high-priority gaps remain. "
                "Consider reviewing before assessment."
            )

        # All critical gaps closed - proceed to finalization
        logger.info(
            f"✅ Data validation passed - all critical gaps closed "
            f"({gap_closure_percentage:.1f}% overall closure) - "
            "transitioning to finalization"
        )

        await state_service.transition_phase(
            flow_id=child_flow.id, new_phase=CollectionPhase.FINALIZATION
        )

        result = {
            "status": "completed",
            "phase": phase_name,
            "validation_result": {
                "total_gaps": total_gaps,
                "resolved_gaps": total_resolved,
                "pending_gaps": total_pending,
                "critical_gaps_remaining": 0,
                "high_gaps_remaining": len(high_pending),
                "medium_gaps_remaining": len(medium_pending),
                "low_gaps_remaining": len(low_pending),
                "gap_closure_percentage": round(gap_closure_percentage, 1),
                "all_critical_gaps_closed": True,
            },
            "message": (
                f"Data validation passed - {gap_closure_percentage:.1f}% gaps closed, "
                "all critical gaps resolved"
            ),
            "next_phase": "finalization",
        }

        if validation_warning:
            result["validation_warning"] = validation_warning

        return result

    except Exception as e:
        logger.error(
            f"❌ Error during data validation for flow {child_flow.id}: {e}",
            exc_info=True,
        )

        # Return error status but don't crash the phase
        return {
            "status": "error",
            "phase": phase_name,
            "error": str(e),
            "error_type": type(e).__name__,
            "message": "Data validation failed due to internal error",
            "user_action_required": "retry_or_contact_support",
        }
