"""
Audit Logger Utilities

Helper functions for serialization, conversion, and event formatting.
"""

import json
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, Optional

from ..models import AuditEvent, AuditLevel
from app.core.logging import get_logger

logger = get_logger(__name__)


def convert_to_serializable(obj: Any, visited: Optional[set] = None) -> Any:
    """
    Recursively convert UUIDs and other non-serializable objects to strings.

    Includes circular reference detection to prevent infinite recursion.

    Args:
        obj: Object to convert
        visited: Set of visited object IDs (for circular reference detection)

    Returns:
        Serializable version of the object
    """
    # Initialize visited set on first call
    if visited is None:
        visited = set()

    # Detect circular references by tracking object IDs
    obj_id = id(obj)
    if obj_id in visited:
        return "<Circular Reference>"

    # For complex types, add to visited set
    if isinstance(obj, (dict, list)) or hasattr(obj, "__dict__"):
        visited.add(obj_id)

    # Convert based on type
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v, visited) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item, visited) for item in obj]
    elif hasattr(obj, "__dict__"):
        return convert_to_serializable(obj.__dict__, visited)
    else:
        return obj


def event_to_dict(event: AuditEvent) -> Dict[str, Any]:
    """
    Convert AuditEvent to dictionary with proper serialization.

    Args:
        event: AuditEvent to convert

    Returns:
        Dictionary representation with serialized fields
    """
    event_dict = asdict(event)
    # Convert any nested UUIDs or non-serializable objects
    return convert_to_serializable(event_dict)


def log_event_to_system(event: AuditEvent):
    """
    Log audit event to system logger with appropriate log level.

    Args:
        event: AuditEvent to log
    """
    log_data = {
        "event_id": event.event_id,
        "timestamp": event.timestamp.isoformat(),
        "category": event.category.value,
        "level": event.level.value,
        "flow_id": str(event.flow_id) if event.flow_id else None,
        "operation": event.operation,
        "user_id": str(event.user_id) if event.user_id else None,
        "client_account_id": (
            str(event.client_account_id) if event.client_account_id else None
        ),
        "engagement_id": str(event.engagement_id) if event.engagement_id else None,
        "success": event.success,
        "error_message": event.error_message,
        "details": convert_to_serializable(event.details),
        "metadata": convert_to_serializable(event.metadata),
    }

    # Log based on audit level
    log_msg = f"AUDIT: {json.dumps(log_data, default=str)}"
    if event.level == AuditLevel.CRITICAL:
        logger.critical(log_msg)
    elif event.level == AuditLevel.ERROR:
        logger.error(log_msg)
    elif event.level == AuditLevel.WARNING:
        logger.warning(log_msg)
    elif event.level == AuditLevel.DEBUG:
        logger.debug(log_msg)
    else:
        logger.info(log_msg)


def export_events_to_json(events: list) -> str:
    """
    Export events to JSON format.

    Args:
        events: List of AuditEvents

    Returns:
        JSON string representation
    """
    return json.dumps([event_to_dict(event) for event in events], indent=2, default=str)


def export_events_to_csv(events: list) -> str:
    """
    Export events to CSV format.

    Args:
        events: List of AuditEvents

    Returns:
        CSV string representation
    """
    csv_lines = [
        "timestamp,category,level,flow_id,operation,user_id,success,error_message"
    ]
    for event in events:
        csv_lines.append(
            f"{event.timestamp},{event.category.value},{event.level.value},"
            f"{event.flow_id},{event.operation},{event.user_id},{event.success},{event.error_message or ''}"
        )
    return "\n".join(csv_lines)
