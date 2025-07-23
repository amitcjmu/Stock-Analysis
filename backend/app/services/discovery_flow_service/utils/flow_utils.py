"""
Utility functions for discovery flow operations.
"""

import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


class FlowPhase(Enum):
    """Enumeration of discovery flow phases."""

    DATA_IMPORT = "data_import"
    ATTRIBUTE_MAPPING = "attribute_mapping"
    DATA_CLEANSING = "data_cleansing"
    INVENTORY = "inventory"
    DEPENDENCIES = "dependencies"
    TECH_DEBT = "tech_debt"


class ValidationStatus(Enum):
    """Enumeration of asset validation statuses."""

    PENDING = "pending"
    VALIDATED = "validated"
    FAILED = "failed"
    MANUAL_REVIEW = "manual_review"


class FlowStatus(Enum):
    """Enumeration of flow statuses."""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


def validate_flow_id(flow_id: str) -> bool:
    """
    Validate CrewAI flow ID format.

    Args:
        flow_id: Flow identifier to validate

    Returns:
        True if valid format, False otherwise
    """
    if not flow_id or not isinstance(flow_id, str):
        return False

    # CrewAI flow IDs should be non-empty strings with reasonable length
    if len(flow_id.strip()) == 0 or len(flow_id) > 255:
        return False

    # Basic format validation - alphanumeric, hyphens, underscores
    pattern = r"^[a-zA-Z0-9_-]+$"
    return bool(re.match(pattern, flow_id))


def validate_phase_name(phase: str) -> bool:
    """
    Validate discovery flow phase name.

    Args:
        phase: Phase name to validate

    Returns:
        True if valid phase, False otherwise
    """
    try:
        FlowPhase(phase)
        return True
    except ValueError:
        return False


def get_next_phase(current_phase_completion: Dict[str, bool]) -> Optional[str]:
    """
    Determine the next phase based on current completion status.

    Args:
        current_phase_completion: Dictionary of phase completion status

    Returns:
        Next phase name or None if all phases complete
    """
    phase_order = [
        FlowPhase.DATA_IMPORT,
        FlowPhase.ATTRIBUTE_MAPPING,
        FlowPhase.DATA_CLEANSING,
        FlowPhase.INVENTORY,
        FlowPhase.DEPENDENCIES,
        FlowPhase.TECH_DEBT,
    ]

    for phase in phase_order:
        if not current_phase_completion.get(phase.value, False):
            return phase.value

    return None  # All phases completed


def calculate_progress_percentage(phase_completion: Dict[str, bool]) -> float:
    """
    Calculate overall progress percentage based on phase completion.

    Args:
        phase_completion: Dictionary of phase completion status

    Returns:
        Progress percentage (0.0 to 100.0)
    """
    if not phase_completion:
        return 0.0

    total_phases = len(FlowPhase)
    completed_phases = sum(1 for completed in phase_completion.values() if completed)

    return round((completed_phases / total_phases) * 100, 1)


def format_duration(start_time: datetime, end_time: Optional[datetime] = None) -> str:
    """
    Format duration between timestamps in human-readable format.

    Args:
        start_time: Start timestamp
        end_time: End timestamp (defaults to current time)

    Returns:
        Human-readable duration string
    """
    if end_time is None:
        end_time = datetime.utcnow()

    duration = end_time - start_time

    if duration.days > 0:
        return f"{duration.days} day{'s' if duration.days > 1 else ''}"
    elif duration.seconds >= 3600:
        hours = duration.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''}"
    elif duration.seconds >= 60:
        minutes = duration.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''}"
    else:
        return "less than a minute"


def sanitize_flow_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize flow data by removing sensitive information and normalizing values.

    Args:
        data: Raw flow data

    Returns:
        Sanitized flow data
    """
    if not isinstance(data, dict):
        return {}

    sanitized = {}
    sensitive_fields = {"password", "token", "secret", "key", "credential"}

    for key, value in data.items():
        # Skip sensitive fields
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            sanitized[key] = "[REDACTED]"
            continue

        # Recursively sanitize nested dictionaries
        if isinstance(value, dict):
            sanitized[key] = sanitize_flow_data(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_flow_data(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


def extract_asset_type_from_data(asset_data: Dict[str, Any]) -> str:
    """
    Extract or infer asset type from asset data.

    Args:
        asset_data: Asset data dictionary

    Returns:
        Asset type string
    """
    # Direct type specification
    if "asset_type" in asset_data:
        return asset_data["asset_type"]

    if "type" in asset_data:
        return asset_data["type"]

    # Infer from other fields
    inferrable_fields = {
        "database": ["db_name", "database_name", "schema", "table_count"],
        "server": ["hostname", "server_name", "ip_address", "cpu_count"],
        "application": ["app_name", "application_name", "version", "framework"],
        "network": ["network_name", "subnet", "vlan", "switch"],
        "storage": ["storage_name", "capacity", "volume", "disk"],
    }

    for asset_type, indicators in inferrable_fields.items():
        if any(indicator in asset_data for indicator in indicators):
            return asset_type

    return "unknown"


def normalize_confidence_score(score: Union[str, int, float]) -> float:
    """
    Normalize confidence score to 0.0-1.0 range.

    Args:
        score: Confidence score in various formats

    Returns:
        Normalized confidence score (0.0-1.0)
    """
    try:
        if isinstance(score, str):
            # Handle percentage strings
            if score.endswith("%"):
                numeric_score = float(score[:-1]) / 100
            else:
                numeric_score = float(score)
        else:
            numeric_score = float(score)

        # Normalize different ranges to 0.0-1.0
        if numeric_score > 1.0:
            if numeric_score <= 100.0:
                return numeric_score / 100.0  # Assume 0-100 scale
            else:
                return 1.0  # Cap at maximum
        elif numeric_score < 0.0:
            return 0.0  # Floor at minimum
        else:
            return numeric_score

    except (ValueError, TypeError):
        logger.warning(f"Failed to normalize confidence score: {score}")
        return 0.5  # Default neutral confidence


def validate_asset_data_quality(asset_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate asset data quality and return quality assessment.

    Args:
        asset_data: Asset data to validate

    Returns:
        Quality assessment with score and issues
    """
    issues = []
    quality_factors = {"completeness": 0.0, "consistency": 0.0, "validity": 0.0}

    # Check completeness
    required_fields = ["asset_name", "asset_type"]

    present_required = sum(1 for field in required_fields if asset_data.get(field))
    quality_factors["completeness"] = present_required / len(required_fields)

    if present_required < len(required_fields):
        missing = [field for field in required_fields if not asset_data.get(field)]
        issues.append(f"Missing required fields: {', '.join(missing)}")

    # Check consistency
    consistency_score = 1.0
    if "asset_name" in asset_data and asset_data["asset_name"]:
        name = asset_data["asset_name"]
        if len(name.strip()) == 0:
            issues.append("Asset name is empty or whitespace only")
            consistency_score -= 0.3
        elif len(name) > 255:
            issues.append("Asset name is too long (>255 characters)")
            consistency_score -= 0.2

    quality_factors["consistency"] = max(0.0, consistency_score)

    # Check validity
    validity_score = 1.0
    if "asset_type" in asset_data:
        valid_types = [
            "server",
            "database",
            "application",
            "network",
            "storage",
            "unknown",
        ]
        if asset_data["asset_type"] not in valid_types:
            issues.append(f"Invalid asset type: {asset_data['asset_type']}")
            validity_score -= 0.4

    quality_factors["validity"] = max(0.0, validity_score)

    # Calculate overall quality score
    overall_quality = sum(quality_factors.values()) / len(quality_factors)

    return {
        "quality_score": round(overall_quality, 3),
        "quality_factors": quality_factors,
        "issues": issues,
        "is_valid": overall_quality >= 0.7 and len(issues) == 0,
    }


def generate_flow_summary_key_metrics(
    phase_completion: Dict[str, bool],
    asset_count: int,
    avg_quality_score: float,
    avg_confidence_score: float,
) -> Dict[str, Any]:
    """
    Generate key metrics for flow summary.

    Args:
        phase_completion: Phase completion status
        asset_count: Number of assets
        avg_quality_score: Average asset quality score
        avg_confidence_score: Average asset confidence score

    Returns:
        Key metrics dictionary
    """
    completed_phases = sum(1 for completed in phase_completion.values() if completed)
    progress_percentage = calculate_progress_percentage(phase_completion)

    # Determine flow health
    health_factors = [
        progress_percentage / 100,  # Progress factor
        min(1.0, asset_count / 10),  # Asset count factor (10+ assets is good)
        avg_quality_score,  # Quality factor
        avg_confidence_score,  # Confidence factor
    ]

    overall_health = sum(health_factors) / len(health_factors)

    health_status = (
        "excellent"
        if overall_health >= 0.9
        else (
            "good"
            if overall_health >= 0.7
            else ("fair" if overall_health >= 0.5 else "poor")
        )
    )

    return {
        "progress_percentage": progress_percentage,
        "completed_phases": completed_phases,
        "total_phases": len(FlowPhase),
        "asset_count": asset_count,
        "avg_quality_score": round(avg_quality_score, 3),
        "avg_confidence_score": round(avg_confidence_score, 3),
        "health_score": round(overall_health, 3),
        "health_status": health_status,
        "next_phase": get_next_phase(phase_completion),
        "is_assessment_ready": completed_phases == len(FlowPhase)
        and overall_health >= 0.7,
    }


def estimate_remaining_effort(
    current_phase_completion: Dict[str, bool], asset_count: int
) -> Dict[str, Any]:
    """
    Estimate remaining effort to complete the discovery flow.

    Args:
        current_phase_completion: Current phase completion status
        asset_count: Number of assets in flow

    Returns:
        Effort estimation details
    """
    remaining_phases = [
        phase.value
        for phase in FlowPhase
        if not current_phase_completion.get(phase.value, False)
    ]

    # Base effort estimates per phase (in hours)
    phase_efforts = {
        FlowPhase.DATA_IMPORT.value: 2,
        FlowPhase.ATTRIBUTE_MAPPING.value: 4,
        FlowPhase.DATA_CLEANSING.value: 6,
        FlowPhase.INVENTORY.value: 8,
        FlowPhase.DEPENDENCIES.value: 10,
        FlowPhase.TECH_DEBT.value: 6,
    }

    # Scale effort based on asset count
    asset_multiplier = max(
        1.0, min(3.0, asset_count / 50)
    )  # 1x to 3x based on asset count

    total_effort_hours = 0
    phase_efforts_detail = {}

    for phase in remaining_phases:
        base_effort = phase_efforts.get(phase, 4)
        scaled_effort = base_effort * asset_multiplier
        phase_efforts_detail[phase] = {
            "base_hours": base_effort,
            "scaled_hours": round(scaled_effort, 1),
            "complexity_factor": round(asset_multiplier, 2),
        }
        total_effort_hours += scaled_effort

    # Convert to business days (assuming 8-hour days)
    total_days = total_effort_hours / 8

    if total_days <= 1:
        duration_estimate = "Less than 1 day"
    elif total_days <= 5:
        duration_estimate = f"{int(total_days)} day{'s' if int(total_days) > 1 else ''}"
    elif total_days <= 20:
        weeks = total_days / 5
        duration_estimate = f"{int(weeks)} week{'s' if int(weeks) > 1 else ''}"
    else:
        months = total_days / 20  # ~1 month = 4 weeks
        duration_estimate = f"{int(months)} month{'s' if int(months) > 1 else ''}"

    return {
        "remaining_phases": remaining_phases,
        "total_effort_hours": round(total_effort_hours, 1),
        "estimated_duration": duration_estimate,
        "phase_efforts": phase_efforts_detail,
        "complexity_factors": {
            "asset_count": asset_count,
            "asset_multiplier": round(asset_multiplier, 2),
        },
    }
