"""
Data Processing Helper Functions for Discovery Flow Status Operations

This module contains data processing, transformation, and response building
functions for discovery flow status operations.
"""

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_flow import DiscoveryFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.services.discovery.data_extraction_service import extract_raw_data

logger = logging.getLogger(__name__)


async def build_phase_state(
    discovery_flow: DiscoveryFlow, master_flow: Optional[CrewAIFlowStateExtensions]
) -> Dict[str, Any]:
    """Build combined phase state from discovery and master flows"""
    phase_state = discovery_flow.phase_state or {}
    if master_flow and master_flow.flow_persistence_data:
        master_phase_state = master_flow.flow_persistence_data.get(
            "current_phase_state", {}
        )
        if master_phase_state:
            phase_state.update(master_phase_state)
    return phase_state


def safe_serialize(data: Any, data_type: str) -> Dict[str, Any]:
    """Safely serialize data to avoid recursion errors"""
    if not data:
        return {}

    try:
        import json

        return json.loads(json.dumps(data))
    except (TypeError, ValueError, RecursionError):
        return {"error": f"{data_type}_serialization_failed"}


async def load_raw_data(
    discovery_flow: DiscoveryFlow, db: AsyncSession, flow_id: str
) -> List[Dict[str, Any]]:
    """Load raw data from import records"""
    raw_data = []
    if discovery_flow.data_import_id:
        from app.models import RawImportRecord

        stmt = (
            select(RawImportRecord)
            .where(RawImportRecord.data_import_id == discovery_flow.data_import_id)
            .limit(1000)
        )
        result = await db.execute(stmt)
        import_records = result.scalars().all()

        for record in import_records:
            raw_data.append(
                {
                    "id": str(record.id) if hasattr(record, "id") else None,
                    "source": "data_import",
                    "data": record.raw_data if hasattr(record, "raw_data") else {},
                    "timestamp": (
                        record.created_at.isoformat()
                        if hasattr(record, "created_at")
                        else None
                    ),
                    "validation_status": "valid",
                }
            )

        logger.info(f"✅ Loaded {len(raw_data)} raw records for flow {flow_id}")

    return raw_data


def load_field_mappings(discovery_flow: DiscoveryFlow, flow_id: str) -> Dict[str, Any]:
    """Load and parse field mappings from discovery flow"""
    field_mappings = {}
    if not discovery_flow.field_mappings:
        return field_mappings

    try:
        import json

        if isinstance(discovery_flow.field_mappings, str):
            field_mappings = json.loads(discovery_flow.field_mappings)
        elif isinstance(discovery_flow.field_mappings, dict):
            field_mappings = discovery_flow.field_mappings
        elif isinstance(discovery_flow.field_mappings, list):
            field_mappings = convert_list_mappings_to_dict(
                discovery_flow.field_mappings
            )

        logger.info(
            f"✅ Loaded {len(field_mappings)} field mappings for flow {flow_id}"
        )
    except Exception as e:
        logger.error(f"Failed to parse field mappings: {e}")
        field_mappings = {}

    return field_mappings


def convert_list_mappings_to_dict(
    mappings_list: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Convert list format mappings to dict format"""
    field_mappings = {}
    for mapping in mappings_list:
        if isinstance(mapping, dict) and "source_field" in mapping:
            field_mappings[mapping["source_field"]] = {
                "source_field": mapping.get("source_field"),
                "target_field": mapping.get("target_field"),
                "mapping_type": mapping.get("mapping_type", "direct"),
                "confidence": mapping.get("confidence", 1.0),
            }
    return field_mappings


def build_summary(
    raw_data: List[Dict[str, Any]],
    discovery_flow: DiscoveryFlow,
    field_mappings: Dict[str, Any],
    safe_phases_completed: Dict[str, Any],
) -> Dict[str, Any]:
    """Build summary data for frontend compatibility"""
    return {
        "total_records": len(raw_data),
        "data_import_completed": bool(discovery_flow.data_import_id and raw_data),
        "field_mapping_completed": bool(field_mappings),
        "attribute_mapping_completed": bool(field_mappings),  # Alias for compatibility
        "data_cleansing_completed": (
            safe_phases_completed.get("data_cleansing", False)
            if safe_phases_completed
            else False
        ),
        "record_count": len(raw_data),
        "quality_score": 0,  # Would need to be calculated based on data quality metrics
    }


def extract_master_flow_data(
    master_flow: CrewAIFlowStateExtensions,
    raw_data: List[Dict[str, Any]],
    summary: Dict[str, Any],
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Extract additional data from master flow persistence data"""
    if not master_flow.flow_persistence_data:
        return raw_data, summary

    persistence_data = master_flow.flow_persistence_data
    if "crewai_state_data" in persistence_data:
        crewai_data = persistence_data["crewai_state_data"]
        extracted_raw = extract_raw_data(crewai_data)
        if extracted_raw and not raw_data:
            raw_data = extracted_raw
            summary["total_records"] = len(raw_data)
            logger.info(f"📦 Extracted {len(raw_data)} records from CrewAI state data")

    return raw_data, summary


def build_flow_status_response(
    flow_id: str,
    discovery_flow: DiscoveryFlow,
    safe_phase_state: Dict[str, Any],
    safe_metadata: Dict[str, Any],
    safe_phases_completed: Dict[str, Any],
    raw_data: List[Dict[str, Any]],
    field_mappings: Dict[str, Any],
    summary: Dict[str, Any],
) -> Dict[str, Any]:
    """Build the final flow status response"""
    return {
        "flow_id": flow_id,
        "status": discovery_flow.status,
        "current_phase": discovery_flow.current_phase,
        "progress": discovery_flow.progress_percentage or 0,
        "progress_percentage": discovery_flow.progress_percentage or 0,  # Alias
        "phase_state": safe_phase_state,
        "metadata": safe_metadata,
        "last_activity": (
            discovery_flow.updated_at.isoformat() if discovery_flow.updated_at else None
        ),
        "error_message": discovery_flow.error_message,
        "phase_completion": safe_phases_completed,
        "raw_data": raw_data,
        "field_mappings": field_mappings,
        "summary": summary,
        "data_import_id": discovery_flow.data_import_id,
        "import_metadata": {
            "record_count": len(raw_data),
            "import_id": discovery_flow.data_import_id,
        },
    }
