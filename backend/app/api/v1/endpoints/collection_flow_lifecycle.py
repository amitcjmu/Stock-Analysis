"""
Collection Flow Lifecycle Management
Utilities for managing collection flow lifecycle states, completion detection,
and stale flow handling to resolve 409 conflicts.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import (
    CollectionFlow,
    CollectionFlowStatus,
)
from app.services.collection_flow_rate_limiter import CollectionFlowRateLimitingService
from app.services.collection_flow_analyzer import CollectionFlowAnalyzer

logger = logging.getLogger(__name__)


class CollectionFlowLifecycleManager:
    """Manager for collection flow lifecycle operations and state transitions."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        # Initialize rate limiting service and analyzer
        self.rate_limiter = CollectionFlowRateLimitingService(
            min_operation_interval_minutes=5
        )
        self.analyzer = CollectionFlowAnalyzer()

    async def analyze_existing_flows(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze existing flows for the current engagement to provide options
        when a 409 conflict occurs.

        Returns:
            Dictionary with flow analysis and recommended actions
        """
        try:
            # Get all active flows for the engagement
            # Per ADR-012: Use lifecycle states instead of phase values
            active_statuses = [
                CollectionFlowStatus.INITIALIZED.value,
                CollectionFlowStatus.RUNNING.value,
                CollectionFlowStatus.PAUSED.value,
            ]

            query = (
                select(CollectionFlow)
                .where(
                    CollectionFlow.engagement_id == self.context.engagement_id,
                    CollectionFlow.status.in_(active_statuses),
                )
                .order_by(CollectionFlow.updated_at.desc())
            )

            result = await self.db.execute(query)
            active_flows = result.scalars().all()

            if not active_flows:
                return {
                    "has_active_flows": False,
                    "can_create_new": True,
                    "recommended_action": "create_new",
                    "message": "No active flows found. Safe to create new flow.",
                }

            # Analyze each flow
            flow_analysis = []
            now = datetime.now(timezone.utc)
            resumable_flows = []
            stale_flows = []
            recently_active_flows = []

            for flow in active_flows:
                analysis = await self.analyzer.analyze_single_flow(flow, now)
                flow_analysis.append(analysis)

                if analysis["is_stale"]:
                    stale_flows.append(flow)
                elif analysis["is_resumable"]:
                    resumable_flows.append(flow)
                elif analysis["recently_active"]:
                    recently_active_flows.append(flow)

            # Determine recommended action
            recommended_action, message = self.analyzer.determine_recommended_action(
                recently_active_flows, resumable_flows, stale_flows
            )

            return {
                "has_active_flows": True,
                "active_flow_count": len(active_flows),
                "flow_analysis": flow_analysis,
                "resumable_flows": len(resumable_flows),
                "stale_flows": len(stale_flows),
                "recently_active_flows": len(recently_active_flows),
                "recommended_action": recommended_action,
                "message": message,
                "can_create_new": recommended_action == "create_new",
                "options": self.analyzer.generate_user_options(
                    recently_active_flows, resumable_flows, stale_flows
                ),
            }

        except Exception as e:
            logger.error(f"Error analyzing existing flows: {e}")
            raise

    async def auto_complete_eligible_flows(self) -> Dict[str, Any]:
        """
        Auto-complete flows that have completion indicators but aren't marked complete.
        Includes rate limiting to prevent frequent status flips.

        Returns:
            Summary of flows that were auto-completed
        """
        try:
            # Find flows that should be completed
            # Per ADR-012: Use lifecycle states instead of phase values
            active_statuses = [
                CollectionFlowStatus.INITIALIZED.value,
                CollectionFlowStatus.RUNNING.value,
                CollectionFlowStatus.PAUSED.value,
            ]

            query = select(CollectionFlow).where(
                CollectionFlow.engagement_id == self.context.engagement_id,
                CollectionFlow.status.in_(active_statuses),
            )

            result = await self.db.execute(query)
            active_flows = result.scalars().all()

            completed_flows = []
            rate_limited_flows = []

            for flow in active_flows:
                completion_indicators = await self.analyzer.check_completion_indicators(
                    flow
                )

                if completion_indicators["should_be_complete"]:
                    # Check rate limiting before proceeding
                    can_proceed, rate_limit_reason = self.rate_limiter.check_rate_limit(
                        flow, "auto_complete"
                    )

                    if not can_proceed:
                        rate_limited_flows.append(
                            {
                                "flow_id": str(flow.flow_id),
                                "flow_name": flow.flow_name,
                                "reason": rate_limit_reason,
                            }
                        )
                        logger.info(
                            f"Rate limited auto-completion for flow {flow.flow_id}: {rate_limit_reason}"
                        )
                        continue

                    # Auto-complete the flow
                    flow.status = CollectionFlowStatus.COMPLETED.value
                    flow.completed_at = datetime.now(timezone.utc)
                    flow.progress_percentage = 100.0

                    # Add completion metadata
                    if not flow.flow_metadata:
                        flow.flow_metadata = {}
                    flow.flow_metadata["auto_completed"] = True
                    flow.flow_metadata["auto_completed_at"] = datetime.now(
                        timezone.utc
                    ).isoformat()
                    flow.flow_metadata["completion_reasons"] = completion_indicators[
                        "reasons"
                    ]
                    flow.flow_metadata["completion_confidence"] = completion_indicators[
                        "confidence"
                    ]

                    # Update operation timestamp for rate limiting
                    self.rate_limiter.update_operation_timestamp(flow, "auto_complete")

                    completed_flows.append(
                        {
                            "flow_id": str(flow.flow_id),
                            "flow_name": flow.flow_name,
                            "reasons": completion_indicators["reasons"],
                            "confidence": completion_indicators["confidence"],
                        }
                    )

            if completed_flows:
                await self.db.commit()
                logger.info(f"Auto-completed {len(completed_flows)} collection flows")

            return {
                "flows_completed": len(completed_flows),
                "completed_flows": completed_flows,
                "rate_limited_flows": len(rate_limited_flows),
                "rate_limited_details": rate_limited_flows,
                "rate_limit_config": self.rate_limiter.get_rate_limit_config(),
            }

        except Exception as e:
            logger.error(f"Error auto-completing flows: {e}")
            await self.db.rollback()
            raise

    async def complete_single_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        Mark a specific flow as complete.
        Includes rate limiting and proper metadata tracking.

        Args:
            flow_id: The specific flow ID to complete

        Returns:
            Result of the completion operation

        Raises:
            HTTPException: If flow is not found or completion fails
        """
        from fastapi import HTTPException
        from uuid import UUID

        try:
            # Convert flow_id to UUID for query
            try:
                flow_uuid = UUID(flow_id)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=400, detail=f"Invalid flow ID format: {flow_id}"
                )

            # Find the specific flow
            query = select(CollectionFlow).where(
                CollectionFlow.flow_id == flow_uuid,
                CollectionFlow.engagement_id == self.context.engagement_id,
            )

            result = await self.db.execute(query)
            flow = result.scalar_one_or_none()

            if not flow:
                raise HTTPException(
                    status_code=404, detail=f"Collection flow not found: {flow_id}"
                )

            # Check if already completed
            if flow.status == CollectionFlowStatus.COMPLETED.value:
                return {
                    "success": True,
                    "message": "Flow was already completed",
                    "flow_id": flow_id,
                    "flow_name": flow.flow_name,
                    "already_completed": True,
                    "completed_at": (
                        flow.completed_at.isoformat() if flow.completed_at else None
                    ),
                }

            # Check if flow is in a state that can be completed
            # Per ADR-012: Use lifecycle states instead of phase values
            completable_statuses = [
                CollectionFlowStatus.INITIALIZED.value,
                CollectionFlowStatus.RUNNING.value,
                CollectionFlowStatus.PAUSED.value,
            ]

            if flow.status not in completable_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Flow cannot be completed from current status '{flow.status}'. "
                        f"Completable statuses: {', '.join(completable_statuses)}"
                    ),
                )

            # Check rate limiting before proceeding
            can_proceed, rate_limit_reason = self.rate_limiter.check_rate_limit(
                flow, "manual_complete"
            )

            if not can_proceed:
                return {
                    "success": False,
                    "flow_id": flow_id,
                    "flow_name": flow.flow_name,
                    "rate_limited": True,
                    "reason": rate_limit_reason,
                    "message": f"Rate limited: {rate_limit_reason}",
                }

            # Complete the flow
            flow.status = CollectionFlowStatus.COMPLETED.value
            flow.completed_at = datetime.now(timezone.utc)
            flow.progress_percentage = 100.0

            # Add completion metadata
            if not flow.flow_metadata:
                flow.flow_metadata = {}
            flow.flow_metadata["manually_completed"] = True
            flow.flow_metadata["manually_completed_at"] = datetime.now(
                timezone.utc
            ).isoformat()
            flow.flow_metadata["completion_method"] = "manual_complete_flow_action"

            # Update operation timestamp for rate limiting
            self.rate_limiter.update_operation_timestamp(flow, "manual_complete")

            # Commit the changes
            await self.db.commit()

            logger.info(
                f"Manually completed collection flow {flow.flow_id} ({flow.flow_name})"
            )

            return {
                "success": True,
                "message": "Flow completed successfully",
                "flow_id": flow_id,
                "flow_name": flow.flow_name,
                "completed_at": flow.completed_at.isoformat(),
                "progress_percentage": flow.progress_percentage,
                "completion_method": "manual",
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error completing single flow {flow_id}: {e}")
            await self.db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to complete flow: {str(e)}"
            )

    async def cancel_stale_flows(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Cancel flows that have been stale for more than the specified time.
        Includes rate limiting to prevent frequent status flips.

        Args:
            max_age_hours: Maximum age in hours before a flow is considered stale

        Returns:
            Summary of cancelled flows
        """
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

            # Find stale flows
            # Per ADR-012: Use lifecycle states instead of phase values
            active_statuses = [
                CollectionFlowStatus.INITIALIZED.value,
                CollectionFlowStatus.RUNNING.value,
                CollectionFlowStatus.PAUSED.value,
            ]

            query = select(CollectionFlow).where(
                CollectionFlow.engagement_id == self.context.engagement_id,
                CollectionFlow.status.in_(active_statuses),
                CollectionFlow.updated_at < cutoff_time,
            )

            result = await self.db.execute(query)
            stale_flows = result.scalars().all()

            cancelled_flows = []
            rate_limited_flows = []

            for flow in stale_flows:
                age_hours = (
                    datetime.now(timezone.utc) - flow.updated_at
                ).total_seconds() / 3600

                # Check rate limiting before proceeding
                can_proceed, rate_limit_reason = self.rate_limiter.check_rate_limit(
                    flow, "auto_cancel"
                )

                if not can_proceed:
                    rate_limited_flows.append(
                        {
                            "flow_id": str(flow.flow_id),
                            "flow_name": flow.flow_name,
                            "age_hours": round(age_hours, 2),
                            "reason": rate_limit_reason,
                        }
                    )
                    logger.info(
                        f"Rate limited auto-cancellation for flow {flow.flow_id}: {rate_limit_reason}"
                    )
                    continue

                # Cancel the stale flow
                flow.status = CollectionFlowStatus.CANCELLED.value
                flow.completed_at = datetime.now(timezone.utc)
                flow.error_message = f"Flow cancelled due to inactivity (stale for {age_hours:.1f} hours)"

                if not flow.flow_metadata:
                    flow.flow_metadata = {}
                flow.flow_metadata["auto_cancelled"] = True
                flow.flow_metadata["auto_cancelled_at"] = datetime.now(
                    timezone.utc
                ).isoformat()
                flow.flow_metadata["stale_hours"] = age_hours

                # Update operation timestamp for rate limiting
                self.rate_limiter.update_operation_timestamp(flow, "auto_cancel")

                cancelled_flows.append(
                    {
                        "flow_id": str(flow.flow_id),
                        "flow_name": flow.flow_name,
                        "age_hours": round(age_hours, 2),
                        "status": flow.status,
                    }
                )

            if cancelled_flows:
                await self.db.commit()
                logger.info(
                    f"Auto-cancelled {len(cancelled_flows)} stale collection flows"
                )

            return {
                "flows_cancelled": len(cancelled_flows),
                "cancelled_flows": cancelled_flows,
                "rate_limited_flows": len(rate_limited_flows),
                "rate_limited_details": rate_limited_flows,
                "rate_limit_config": self.rate_limiter.get_rate_limit_config(),
            }

        except Exception as e:
            logger.error(f"Error cancelling stale flows: {e}")
            await self.db.rollback()
            raise
