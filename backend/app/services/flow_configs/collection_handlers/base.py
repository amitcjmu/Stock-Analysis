"""
Base classes and utilities for Collection Flow Handlers
ADCS: Common imports, base classes, and utility functions used across all handlers

Provides shared functionality and common patterns for collection flow handlers.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CollectionHandlerBase:
    """Base class for collection flow handlers"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def _get_collection_flow_by_master_id(
        self, db: AsyncSession, master_flow_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get collection flow by master flow ID"""
        query = """
            SELECT id, flow_id, status, current_phase, automation_tier
            FROM collection_flows
            WHERE master_flow_id = :master_flow_id
        """

        result = await db.execute(query, {"master_flow_id": master_flow_id})
        row = result.fetchone()

        if row:
            return {
                "id": row.id,
                "flow_id": row.flow_id,
                "status": row.status,
                "current_phase": row.current_phase,
                "automation_tier": row.automation_tier,
            }
        return None


# Utility Functions
def normalize_platform_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize platform-specific data to common schema"""
    normalized = {"resources": [], "metadata": {}, "platform_specific": {}}

    # Extract resources
    if "resources" in raw_data:
        normalized["resources"] = raw_data["resources"]
    elif "assets" in raw_data:
        normalized["resources"] = raw_data["assets"]
    elif "items" in raw_data:
        normalized["resources"] = raw_data["items"]

    # Extract metadata
    for key in ["platform", "region", "account", "environment"]:
        if key in raw_data:
            normalized["metadata"][key] = raw_data[key]

    # Keep platform-specific data
    normalized["platform_specific"] = {
        k: v
        for k, v in raw_data.items()
        if k not in ["resources", "assets", "items"] and not k.startswith("_")
    }

    return normalized


def get_question_template(gap_type: str) -> str:
    """Get question template based on gap type"""
    templates = {
        "missing_data": "Please provide the missing {field_name} information. {description}",
        "incomplete_data": (
            "The {field_name} field is incomplete. {description}. "
            "Please provide the complete information."
        ),
        "quality_issues": (
            "There are quality issues with {field_name}. {description}. "
            "Please provide corrected information."
        ),
        "validation_errors": "The {field_name} failed validation. {description}. Please provide valid information.",
    }

    return templates.get(
        gap_type, "Please provide information for {field_name}. {description}"
    )


def build_field_updates_from_rows(rows) -> Dict[str, Any]:
    """Extract last-write-wins mapping of field_name -> value from resolved rows."""
    updates: Dict[str, Any] = {}
    for row in rows:
        val = getattr(row, "response_value", None)
        if isinstance(val, dict) and "value" in val:
            val = val["value"]
        field_name = getattr(row, "field_name", None)
        if field_name:
            updates[field_name] = val
    return updates


# Database Helper Functions
async def clear_collected_data(
    db: AsyncSession, collection_flow_id: uuid.UUID, preserve_platforms: bool = False
):
    """Clear collected data for rollback"""
    if not preserve_platforms:
        await db.execute(
            "DELETE FROM collected_data_inventory WHERE collection_flow_id = :flow_id",
            {"flow_id": collection_flow_id},
        )
    else:
        # Only clear automated collection data
        await db.execute(
            (
                "DELETE FROM collected_data_inventory "
                "WHERE collection_flow_id = :flow_id "
                "AND collection_method = 'automated'"
            ),
            {"flow_id": collection_flow_id},
        )


async def clear_gaps(db: AsyncSession, collection_flow_id: uuid.UUID):
    """Clear identified gaps"""
    await db.execute(
        "DELETE FROM collection_data_gaps WHERE collection_flow_id = :flow_id",
        {"flow_id": collection_flow_id},
    )


async def clear_questionnaire_responses(
    db: AsyncSession, collection_flow_id: uuid.UUID
):
    """Clear questionnaire responses"""
    await db.execute(
        "DELETE FROM collection_questionnaire_responses WHERE collection_flow_id = :flow_id",
        {"flow_id": collection_flow_id},
    )


async def get_adapter_by_name(
    db: AsyncSession, adapter_name: str
) -> Optional[Dict[str, Any]]:
    """Get adapter by name"""
    query = """
        SELECT id, adapter_name, status, capabilities
        FROM platform_adapters
        WHERE adapter_name = :adapter_name
        AND status = 'active'
    """

    result = await db.execute(query, {"adapter_name": adapter_name})
    row = result.fetchone()

    if row:
        return {
            "id": row.id,
            "adapter_name": row.adapter_name,
            "status": row.status,
            "capabilities": row.capabilities,
        }
    return None


async def initialize_adapter_registry(db: AsyncSession) -> List[Dict[str, Any]]:
    """Initialize and return available adapters"""
    query = """
        SELECT id, adapter_name, adapter_type, capabilities, supported_platforms
        FROM platform_adapters
        WHERE status = 'active'
    """

    result = await db.execute(query)
    adapters = []

    for row in result:
        adapters.append(
            {
                "id": str(row.id),
                "name": row.adapter_name,
                "type": row.adapter_type,
                "capabilities": row.capabilities,
                "platforms": row.supported_platforms,
            }
        )

    return adapters
