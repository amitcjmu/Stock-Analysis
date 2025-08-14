"""
Flow Lookup Helpers

This module provides convenience methods for looking up flows across the two-table
architecture (master and child flows). It helps eliminate confusion between flow_id
and master_flow_id lookups.

The two-table pattern is INTENTIONAL:
- Master table (crewai_flow_state_extensions): Orchestration lifecycle
- Child table (discovery_flows): UI and operational data
"""

import logging
from typing import Optional, Tuple
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)


class FlowLookupHelper:
    """Helper class for flow lookups across master and child tables."""

    @staticmethod
    async def get_discovery_flow_by_any_id(
        db: AsyncSession, flow_id: str
    ) -> Optional[DiscoveryFlow]:
        """
        Get discovery flow by either flow_id or master_flow_id.

        This helper eliminates confusion when you have an ID but don't know
        if it's the flow_id or master_flow_id.

        Args:
            db: Database session
            flow_id: Either flow_id or master_flow_id

        Returns:
            DiscoveryFlow if found, None otherwise
        """
        try:
            # Try both flow_id and master_flow_id
            query = select(DiscoveryFlow).where(
                or_(
                    DiscoveryFlow.flow_id == flow_id,
                    DiscoveryFlow.master_flow_id == flow_id,
                )
            )

            result = await db.execute(query)
            flow = result.scalar_one_or_none()

            if flow:
                logger.debug(
                    f"Found discovery flow: flow_id={flow.flow_id}, master_flow_id={flow.master_flow_id}"
                )
            else:
                logger.debug(f"No discovery flow found for ID: {flow_id}")

            return flow

        except Exception as e:
            logger.error(f"Error looking up discovery flow: {e}")
            return None

    @staticmethod
    async def get_master_flow(
        db: AsyncSession, flow_id: str
    ) -> Optional[CrewAIFlowStateExtensions]:
        """
        Get master flow by flow_id.

        Args:
            db: Database session
            flow_id: Master flow ID

        Returns:
            CrewAIFlowStateExtensions if found, None otherwise
        """
        try:
            query = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == flow_id
            )

            result = await db.execute(query)
            flow = result.scalar_one_or_none()

            if flow:
                logger.debug(f"Found master flow: {flow.flow_id}")
            else:
                logger.debug(f"No master flow found for ID: {flow_id}")

            return flow

        except Exception as e:
            logger.error(f"Error looking up master flow: {e}")
            return None

    @staticmethod
    async def get_both_flows(
        db: AsyncSession, flow_id: str
    ) -> Tuple[Optional[CrewAIFlowStateExtensions], Optional[DiscoveryFlow]]:
        """
        Get both master and child flows by ID.

        This is useful when you need data from both tables.

        Args:
            db: Database session
            flow_id: Flow ID (will check both flow_id and master_flow_id)

        Returns:
            Tuple of (master_flow, child_flow), either can be None
        """
        # Get master flow
        master_flow = await FlowLookupHelper.get_master_flow(db, flow_id)

        # Get child flow (checking both IDs)
        child_flow = await FlowLookupHelper.get_discovery_flow_by_any_id(db, flow_id)

        # If we found child but not master, try getting master by child's master_flow_id
        if child_flow and not master_flow and child_flow.master_flow_id:
            master_flow = await FlowLookupHelper.get_master_flow(
                db, child_flow.master_flow_id
            )

        return master_flow, child_flow

    @staticmethod
    async def get_flow_status(db: AsyncSession, flow_id: str) -> Optional[dict]:
        """
        Get comprehensive flow status from both tables.

        Args:
            db: Database session
            flow_id: Flow ID

        Returns:
            Dictionary with status from both tables, or None if not found
        """
        master_flow, child_flow = await FlowLookupHelper.get_both_flows(db, flow_id)

        if not master_flow and not child_flow:
            return None

        status = {
            "flow_id": flow_id,
            "found_in": [],
            "master_flow": None,
            "child_flow": None,
        }

        if master_flow:
            status["found_in"].append("master")
            status["master_flow"] = {
                "flow_id": master_flow.flow_id,
                "flow_status": master_flow.flow_status,
                "current_phase": master_flow.current_phase,
                "created_at": (
                    master_flow.created_at.isoformat()
                    if master_flow.created_at
                    else None
                ),
                "updated_at": (
                    master_flow.updated_at.isoformat()
                    if master_flow.updated_at
                    else None
                ),
            }

        if child_flow:
            status["found_in"].append("child")
            status["child_flow"] = {
                "flow_id": child_flow.flow_id,
                "master_flow_id": child_flow.master_flow_id,
                "status": child_flow.status,
                "current_phase": child_flow.current_phase,
                "progress_percentage": child_flow.progress_percentage,
                "data_import_id": (
                    str(child_flow.data_import_id)
                    if child_flow.data_import_id
                    else None
                ),
            }

        return status

    @staticmethod
    async def resolve_master_flow_id(db: AsyncSession, flow_id: str) -> Optional[str]:
        """
        Resolve any flow ID to its master flow ID.

        This is useful when you need the master flow ID but might have
        either the flow_id or master_flow_id.

        Args:
            db: Database session
            flow_id: Any flow ID

        Returns:
            Master flow ID if found, None otherwise
        """
        # First check if this IS a master flow ID
        master_flow = await FlowLookupHelper.get_master_flow(db, flow_id)
        if master_flow:
            return master_flow.flow_id

        # Check if it's a child flow ID
        child_flow = await FlowLookupHelper.get_discovery_flow_by_any_id(db, flow_id)
        if child_flow and child_flow.master_flow_id:
            return child_flow.master_flow_id

        return None

    @staticmethod
    async def get_data_import_id(db: AsyncSession, flow_id: str) -> Optional[str]:
        """
        Get data_import_id from discovery flow.

        Args:
            db: Database session
            flow_id: Any flow ID

        Returns:
            data_import_id if found, None otherwise
        """
        child_flow = await FlowLookupHelper.get_discovery_flow_by_any_id(db, flow_id)

        if child_flow and child_flow.data_import_id:
            return str(child_flow.data_import_id)

        return None


class FlowConsistencyChecker:
    """Helper class for checking flow consistency between tables."""

    @staticmethod
    async def check_flow_consistency(db: AsyncSession, flow_id: str) -> dict:
        """
        Check consistency between master and child flow records.

        Args:
            db: Database session
            flow_id: Flow ID to check

        Returns:
            Dictionary with consistency check results
        """
        master_flow, child_flow = await FlowLookupHelper.get_both_flows(db, flow_id)

        issues = []
        warnings = []

        # Check if both exist
        if master_flow and not child_flow:
            issues.append("Master flow exists but child flow missing")
        elif child_flow and not master_flow:
            issues.append("Child flow exists but master flow missing")

        # Check ID consistency
        if master_flow and child_flow:
            if child_flow.master_flow_id != master_flow.flow_id:
                issues.append(
                    f"ID mismatch: child.master_flow_id={child_flow.master_flow_id} "
                    f"!= master.flow_id={master_flow.flow_id}"
                )

            # Check phase consistency
            if master_flow.current_phase != child_flow.current_phase:
                warnings.append(
                    f"Phase mismatch: master={master_flow.current_phase}, "
                    f"child={child_flow.current_phase}"
                )

            # Check status mapping
            status_map = {
                "running": ["running", "processing"],
                "waiting_for_approval": ["waiting_for_approval", "paused"],
                "completed": ["completed", "success"],
                "failed": ["failed", "error"],
            }

            master_status = master_flow.flow_status
            child_status = child_flow.status

            if master_status in status_map:
                if child_status not in status_map[master_status]:
                    warnings.append(
                        f"Status inconsistency: master={master_status}, "
                        f"child={child_status}"
                    )

        return {
            "flow_id": flow_id,
            "is_consistent": len(issues) == 0,
            "has_warnings": len(warnings) > 0,
            "issues": issues,
            "warnings": warnings,
            "master_exists": master_flow is not None,
            "child_exists": child_flow is not None,
        }


# Usage Examples:
"""
from app.repositories.flow_lookup_helpers import FlowLookupHelper

# When you have a flow ID but don't know if it's master or child
flow = await FlowLookupHelper.get_discovery_flow_by_any_id(db, flow_id)

# Get comprehensive status from both tables
status = await FlowLookupHelper.get_flow_status(db, flow_id)

# Resolve any ID to master flow ID
master_id = await FlowLookupHelper.resolve_master_flow_id(db, some_id)

# Get data_import_id regardless of which ID you have
import_id = await FlowLookupHelper.get_data_import_id(db, flow_id)

# Check consistency between tables
consistency = await FlowConsistencyChecker.check_flow_consistency(db, flow_id)
if not consistency["is_consistent"]:
    logger.error(f"Flow inconsistency: {consistency['issues']}")
"""
