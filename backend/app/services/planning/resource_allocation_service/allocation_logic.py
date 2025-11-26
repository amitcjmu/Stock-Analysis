"""
Resource allocation logic and data manipulation.

Handles allocation parsing, persistence, overrides, and nested value operations.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select, update

from app.models.planning.planning_flow import PlanningFlow

from .base import BaseResourceAllocationService

logger = logging.getLogger(__name__)


class AllocationLogic(BaseResourceAllocationService):
    """
    Handles allocation logic including parsing, persistence, and overrides.

    This class manages resource allocation data manipulation and storage.
    """

    async def apply_manual_override(
        self,
        planning_flow_id: uuid.UUID,
        wave_id: str,
        overrides: Dict[str, Any],
        user_id: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Apply manual overrides to AI-generated resource allocations.

        This method:
        1. Retrieves current allocations from JSONB
        2. Applies manual overrides with audit trail
        3. Stores learning via TenantMemoryManager (ADR-024)
        4. Updates planning_flows.resource_allocation_data JSONB

        Args:
            planning_flow_id: UUID of the planning flow
            wave_id: ID of the wave to override
            overrides: Dict of field overrides {field_path: new_value}
            user_id: User making the override
            reason: Optional reason for override

        Returns:
            Updated resource allocation data

        Example:
            overrides = {
                "resources.cloud_architect.count": 3,
                "resources.developer.effort_hours": 200
            }
        """
        logger.info(
            f"Applying manual overrides for wave {wave_id} in planning flow {planning_flow_id}"
        )

        # Get current allocations
        stmt = select(PlanningFlow).where(
            PlanningFlow.id == planning_flow_id,
            PlanningFlow.client_account_id == self.client_account_uuid,
            PlanningFlow.engagement_id == self.engagement_uuid,
        )
        result = await self.db.execute(stmt)
        planning_flow = result.scalar_one_or_none()

        if not planning_flow:
            raise ValueError(f"Planning flow not found: {planning_flow_id}")

        # Get current allocation data
        allocation_data = planning_flow.resource_allocation_data or {
            "allocations": [],
            "metadata": {},
        }

        # Find wave allocation
        wave_allocation = None
        for alloc in allocation_data.get("allocations", []):
            if alloc.get("wave_id") == wave_id:
                wave_allocation = alloc
                break

        if not wave_allocation:
            raise ValueError(f"Wave allocation not found for wave_id: {wave_id}")

        # Track overrides for learning
        override_records = []

        # Apply overrides
        for field_path, new_value in overrides.items():
            old_value = self._get_nested_value(wave_allocation, field_path)

            # Update value
            self._set_nested_value(wave_allocation, field_path, new_value)

            # Record override
            override_record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "field": field_path,
                "old_value": old_value,
                "new_value": new_value,
                "reason": reason,
            }
            override_records.append(override_record)

        # Add override records to wave allocation
        if "overrides" not in wave_allocation:
            wave_allocation["overrides"] = []
        wave_allocation["overrides"].extend(override_records)

        # Update planning flow
        stmt = (
            update(PlanningFlow)
            .where(
                PlanningFlow.id == planning_flow_id,
                PlanningFlow.client_account_id == self.client_account_uuid,
                PlanningFlow.engagement_id == self.engagement_uuid,
            )
            .values(resource_allocation_data=allocation_data)
        )
        await self.db.execute(stmt)
        await self.db.commit()

        # TODO: Store learning via TenantMemoryManager (ADR-024)
        # This will be implemented when TenantMemoryManager is integrated
        # await self._store_override_learning(override_records, wave_allocation)

        logger.info(f"✅ Applied {len(override_records)} overrides for wave {wave_id}")
        return allocation_data

    def _parse_allocation_result(self, result: Any) -> Dict[str, Any]:
        """
        Parse and validate LLM result.

        Uses defensive parsing to handle various LLM output formats.
        """
        if isinstance(result, dict):
            return result
        elif isinstance(result, str):
            # Try to parse as JSON
            try:
                # Remove markdown wrappers if present
                cleaned = result.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]

                return json.loads(cleaned.strip())
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM result as JSON: {e}")
                # Return error structure
                return {
                    "allocations": [],
                    "metadata": {
                        "error": "Failed to parse LLM output",
                        "raw_output": result[:500],
                    },
                }
        else:
            # Unknown type - return error
            return {
                "allocations": [],
                "metadata": {"error": f"Unexpected result type: {type(result)}"},
            }

    async def _persist_allocations(
        self, planning_flow_id: uuid.UUID, allocations: Dict[str, Any]
    ) -> None:
        """Persist resource allocations to JSONB column."""
        # Add metadata timestamp
        if "metadata" not in allocations:
            allocations["metadata"] = {}
        allocations["metadata"]["generated_at"] = datetime.now(timezone.utc).isoformat()

        stmt = (
            update(PlanningFlow)
            .where(
                PlanningFlow.id == planning_flow_id,
                PlanningFlow.client_account_id == self.client_account_uuid,
                PlanningFlow.engagement_id == self.engagement_uuid,
            )
            .values(resource_allocation_data=allocations)
        )
        await self.db.execute(stmt)
        await self.db.commit()

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dict using dot notation (e.g., 'resources.cloud_architect.count')."""
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list):
                try:
                    idx = int(key)
                    value = value[idx]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return value

    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        """Set value in nested dict using dot notation."""
        keys = path.split(".")
        current = data
        for i, key in enumerate(keys[:-1]):
            if isinstance(current, dict):
                if key not in current:
                    current[key] = {}
                current = current[key]
            elif isinstance(current, list):
                try:
                    idx = int(key)
                    current = current[idx]
                except (ValueError, IndexError):
                    return
        # Set final value
        final_key = keys[-1]
        if isinstance(current, dict):
            current[final_key] = value
        elif isinstance(current, list):
            try:
                idx = int(final_key)
                current[idx] = value
            except (ValueError, IndexError):
                pass
