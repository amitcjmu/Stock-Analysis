"""
Utilities for normalizing topology/dependency import records.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any


@dataclass
class NormalizationResult:
    """Container for normalization output."""

    normalized_records: List[Dict[str, Any]]
    warnings: List[str]
    errors: List[str]
    detected_fields: List[str]


# Map common column aliases to canonical names
COLUMN_ALIASES = {
    "application": "application_name",
    "applicationname": "application_name",
    "application_id": "application_name",
    "app_name": "application_name",
    "service": "component_name",
    "service_name": "component_name",
    "tier": "component_name",
    "tier_name": "component_name",
    "component": "component_name",
    "node": "host_name",
    "node_name": "host_name",
    "host": "host_name",
    "hostname": "host_name",
    "server": "host_name",
    "environment": "environment",
    "env": "environment",
    "called_component": "dependency_target",
    "downstream_component": "dependency_target",
    "target_service": "dependency_target",
    "dependency_target": "dependency_target",
    "dependencytype": "dependency_type",
    "dependency_type": "dependency_type",
    "protocol_name": "protocol",
    "avg_response_time_ms": "avg_latency_ms",
    "latency_ms": "avg_latency_ms",
    "response_time": "avg_latency_ms",
    "call_count": "call_count",
    "calls": "call_count",
    "error_rate_percent": "error_rate_percent",
    "error_rate": "error_rate_percent",
    "port": "port",
    "protocol": "protocol",
    "language": "language",
    "component_type": "component_type",
    "target_component_type": "dependency_target_type",
    "status": "status",
    "source_system": "source_system",
    # Bug #1172 Fix: Add connection count aliases for network discovery imports
    "connection_count": "conn_count",
    "connections": "conn_count",
    "num_connections": "conn_count",
    "connectioncount": "conn_count",
    "numconnections": "conn_count",
    # Bytes total aliases
    "bytes": "bytes_total",
    "total_bytes": "bytes_total",
    "bytestotal": "bytes_total",
    "totalbytes": "bytes_total",
}

REQUIRED_FIELDS = {"application_name", "component_name", "dependency_target"}


def normalize_topology_records(
    raw_records: List[Dict[str, Any]], source_system: str | None = None
) -> NormalizationResult:
    """
    Normalize raw topology records into a consistent structure.
    """

    normalized: List[Dict[str, Any]] = []
    warnings: List[str] = []
    errors: List[str] = []
    detected_fields: set[str] = set()

    for idx, record in enumerate(raw_records):
        if not isinstance(record, dict):
            warnings.append(f"Record {idx + 1} is not an object and was skipped.")
            continue

        lowered = {str(key).lower(): value for key, value in record.items()}
        canonical: Dict[str, Any] = {}

        for key, value in lowered.items():
            canonical_name = COLUMN_ALIASES.get(key, key)
            canonical[canonical_name] = value
            detected_fields.add(canonical_name)

        normalized_record, record_errors = _normalize_single_record(
            canonical, idx, source_system
        )
        if record_errors:
            errors.extend(record_errors)
            continue

        if normalized_record.get("application_dependency") is not None:
            detected_fields.add("application_dependency")
        normalized.append(normalized_record)

    return NormalizationResult(
        normalized_records=normalized,
        warnings=warnings,
        errors=errors,
        detected_fields=sorted(detected_fields),
    )


def _normalize_single_record(
    record: Dict[str, Any], idx: int, source_system: str | None
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Normalize an individual record and return (record, errors).
    """

    errors: List[str] = []

    missing = [field for field in REQUIRED_FIELDS if not record.get(field)]
    if missing:
        errors.append(
            f"Record {idx + 1} missing required fields: {', '.join(sorted(missing))}"
        )
        return {}, errors

    normalized = {
        "record_index": idx,
        "application_name": _safe_str(record.get("application_name")),
        "component_name": _safe_str(record.get("component_name")),
        "component_type": _safe_str(
            record.get("component_type") or record.get("service_type")
        ),
        "language": _safe_str(record.get("language")),
        "host_name": _safe_str(record.get("host_name")),
        "environment": _safe_str(record.get("environment")),
        "status": _safe_str(record.get("status")),
        "dependency_target": _safe_str(record.get("dependency_target")),
        "dependency_target_type": _safe_str(
            record.get("dependency_target_type") or record.get("target_type")
        ),
        "dependency_type": _safe_str(
            record.get("dependency_type") or "application_dependency"
        ),
        "avg_latency_ms": _safe_float(record.get("avg_latency_ms")),
        "call_count": _safe_int(record.get("call_count")),
        "error_rate_percent": _safe_float(record.get("error_rate_percent")),
        "port": record.get(
            "port"
        ),  # Keep as original value, parse in processor (Issue #833: handle comma-separated numbers)
        "protocol": _safe_str(record.get("protocol")),
        "confidence_score": _safe_float(record.get("confidence_score"), default=0.7),
        "source_system": _safe_str(record.get("source_system") or source_system),
        # Network Discovery Fields (Issue #833) - Preserve raw values, parse in processor
        "conn_count": record.get("conn_count") or record.get("connection_count"),
        "bytes_total": record.get("bytes_total") or record.get("bytes"),
        "first_seen": record.get("first_seen"),  # Keep as string/date
        "last_seen": record.get("last_seen"),  # Keep as string/date
        "protocol_name": _safe_str(
            record.get("protocol_name") or record.get("protocol")
        ),
        "raw_record": record,
    }
    normalized["application_dependency"] = normalized.get("dependency_target")
    if normalized.get("dependency_target") is not None:
        # Ensure application_dependency is recognized as a detected field downstream
        record.setdefault("application_dependency", normalized["dependency_target"])

    return normalized, errors


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    value_str = str(value).strip()
    return value_str or None


def _safe_float(value: Any, *, default: float | None = None) -> float | None:
    if value in (None, "", "null", "None"):
        return default
    try:
        result = float(value)
        if result != result or result in (float("inf"), float("-inf")):
            return default
        return result
    except (ValueError, TypeError):
        return default


def _safe_int(value: Any) -> int | None:
    if value in (None, "", "null", "None"):
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None
