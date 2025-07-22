"""
Service utilities for agent service layer operations.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def validate_uuid(value: str) -> bool:
    """Validate if a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def sanitize_string(value: Any, max_length: int = 255) -> str:
    """Sanitize string input for safe processing."""
    if value is None:
        return ""
    
    str_value = str(value).strip()
    
    # Truncate if too long
    if len(str_value) > max_length:
        str_value = str_value[:max_length]
    
    return str_value


def normalize_asset_type(asset_type: str) -> str:
    """Normalize asset type to standard values."""
    if not asset_type:
        return "unknown"
    
    # Mapping of common variations to standard types
    type_mappings = {
        "db": "database",
        "srv": "server", 
        "svc": "service",
        "app": "application",
        "net": "network",
        "infra": "infrastructure",
        "sec": "security"
    }
    
    normalized = asset_type.lower().strip()
    return type_mappings.get(normalized, normalized)


def calculate_confidence_score(factors: Dict[str, float], weights: Optional[Dict[str, float]] = None) -> float:
    """Calculate confidence score from multiple factors."""
    if not factors:
        return 0.0
    
    # Default weights if not provided
    default_weights = {
        "data_completeness": 0.3,
        "validation_status": 0.3,
        "discovery_method": 0.2,
        "source_reliability": 0.2
    }
    
    if weights is None:
        weights = default_weights
    
    # Calculate weighted average
    total_weight = 0.0
    weighted_sum = 0.0
    
    for factor, value in factors.items():
        weight = weights.get(factor, 0.1)  # Default weight for unknown factors
        weighted_sum += value * weight
        total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    return min(1.0, max(0.0, weighted_sum / total_weight))


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}min"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def calculate_completion_percentage(completed_phases: List[str], total_phases: int = 6) -> float:
    """Calculate completion percentage based on completed phases."""
    if total_phases == 0:
        return 0.0
    
    return min(100.0, (len(completed_phases) / total_phases) * 100)


def extract_error_category(error_message: str) -> str:
    """Extract error category from error message."""
    if not error_message:
        return "unknown"
    
    error_lower = error_message.lower()
    
    if "timeout" in error_lower:
        return "timeout"
    elif "not found" in error_lower or "404" in error_lower:
        return "not_found"
    elif "permission" in error_lower or "access" in error_lower or "401" in error_lower or "403" in error_lower:
        return "permission"
    elif "validation" in error_lower or "invalid" in error_lower or "400" in error_lower:
        return "validation"
    elif "database" in error_lower or "connection" in error_lower or "sql" in error_lower:
        return "database"
    elif "500" in error_lower or "internal" in error_lower:
        return "internal_server"
    else:
        return "other"


def build_error_response(method_name: str, error: Exception, error_type: Optional[str] = None) -> Dict[str, Any]:
    """Build standardized error response."""
    error_msg = str(error)
    
    if error_type is None:
        error_type = extract_error_category(error_msg)
    
    guidance_map = {
        "not_found": "Resource not found. Please check the ID and try again.",
        "permission": "Access denied. Please verify your permissions.",
        "validation": "Invalid data provided. Please check your input.",
        "timeout": "Request timed out. Please try again or contact support.",
        "database": "Database error occurred. Please try again later.",
        "internal_server": "Internal server error. Please contact support.",
        "other": "An error occurred. Please try again or contact support."
    }
    
    return {
        "status": "error",
        "error": error_msg,
        "error_type": error_type,
        "method": method_name,
        "timestamp": datetime.utcnow().isoformat(),
        "guidance": guidance_map.get(error_type, guidance_map["other"])
    }


def validate_phase_order(from_phase: str, to_phase: str) -> Dict[str, Any]:
    """Validate phase transition order."""
    phase_order = [
        "data_import",
        "attribute_mapping",
        "data_cleansing",
        "inventory",
        "dependencies", 
        "tech_debt"
    ]
    
    try:
        from_index = phase_order.index(from_phase)
        to_index = phase_order.index(to_phase)
    except ValueError as e:
        return {
            "is_valid": False,
            "error": f"Invalid phase name: {e}",
            "valid_phases": phase_order
        }
    
    # Allow forward transitions and same phase
    is_valid = to_index >= from_index
    
    return {
        "is_valid": is_valid,
        "from_index": from_index,
        "to_index": to_index,
        "phase_order": phase_order,
        "message": "Valid transition" if is_valid else "Backward transitions not allowed"
    }


def calculate_data_quality_score(data_sample: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate data quality score from data sample."""
    if not data_sample:
        return {
            "overall_score": 0.0,
            "completeness": 0.0,
            "consistency": 0.0,
            "validity": 0.0,
            "issues": ["No data available for analysis"]
        }
    
    # Analyze sample
    total_records = len(data_sample)
    all_fields = set()
    field_counts = {}
    type_consistency = {}
    
    for record in data_sample:
        if isinstance(record, dict):
            for field, value in record.items():
                all_fields.add(field)
                field_counts[field] = field_counts.get(field, 0) + 1
                
                # Track type consistency
                value_type = type(value).__name__
                if field not in type_consistency:
                    type_consistency[field] = {}
                type_consistency[field][value_type] = type_consistency[field].get(value_type, 0) + 1
    
    # Calculate completeness
    completeness_scores = {}
    for field in all_fields:
        completeness_scores[field] = field_counts.get(field, 0) / total_records
    
    avg_completeness = sum(completeness_scores.values()) / len(completeness_scores) if completeness_scores else 0
    
    # Calculate consistency (type consistency)
    consistency_scores = {}
    for field, types in type_consistency.items():
        # Field is consistent if it has predominantly one type
        max_type_count = max(types.values()) if types else 0
        consistency_scores[field] = max_type_count / field_counts.get(field, 1)
    
    avg_consistency = sum(consistency_scores.values()) / len(consistency_scores) if consistency_scores else 0
    
    # Calculate validity (simplified - no null/empty values)
    validity_scores = {}
    for field in all_fields:
        valid_count = 0
        for record in data_sample:
            if isinstance(record, dict) and field in record:
                value = record[field]
                if value is not None and str(value).strip():
                    valid_count += 1
        validity_scores[field] = valid_count / total_records
    
    avg_validity = sum(validity_scores.values()) / len(validity_scores) if validity_scores else 0
    
    # Overall score
    overall_score = (avg_completeness + avg_consistency + avg_validity) / 3
    
    # Identify issues
    issues = []
    if avg_completeness < 0.8:
        issues.append("Low data completeness detected")
    if avg_consistency < 0.9:
        issues.append("Data type inconsistencies found")
    if avg_validity < 0.8:
        issues.append("High percentage of null/empty values")
    
    return {
        "overall_score": round(overall_score, 3),
        "completeness": round(avg_completeness, 3),
        "consistency": round(avg_consistency, 3),
        "validity": round(avg_validity, 3),
        "field_scores": {
            "completeness": completeness_scores,
            "consistency": consistency_scores,
            "validity": validity_scores
        },
        "issues": issues,
        "total_records": total_records,
        "total_fields": len(all_fields)
    }


def generate_asset_summary(assets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics for a list of assets."""
    if not assets:
        return {
            "total_count": 0,
            "by_type": {},
            "by_status": {},
            "quality_metrics": {},
            "average_scores": {}
        }
    
    # Count by type
    type_counts = {}
    status_counts = {}
    quality_scores = []
    confidence_scores = []
    
    for asset in assets:
        # Asset type distribution
        asset_type = asset.get("asset_type", "unknown")
        type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
        
        # Status distribution
        status = asset.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # Quality metrics
        quality_score = asset.get("quality_score", 0.0)
        confidence_score = asset.get("confidence_score", 0.0)
        
        if isinstance(quality_score, (int, float)):
            quality_scores.append(quality_score)
        if isinstance(confidence_score, (int, float)):
            confidence_scores.append(confidence_score)
    
    # Calculate averages
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
    
    # Quality metrics
    high_quality_count = sum(1 for score in quality_scores if score >= 0.8)
    low_confidence_count = sum(1 for score in confidence_scores if score < 0.6)
    
    return {
        "total_count": len(assets),
        "by_type": type_counts,
        "by_status": status_counts,
        "quality_metrics": {
            "high_quality_assets": high_quality_count,
            "low_confidence_assets": low_confidence_count,
            "quality_rate": round(high_quality_count / len(assets) * 100, 1) if assets else 0
        },
        "average_scores": {
            "quality": round(avg_quality, 3),
            "confidence": round(avg_confidence, 3)
        }
    }


def create_success_response(data: Any, message: str = None) -> Dict[str, Any]:
    """Create standardized success response."""
    response = {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if message:
        response["message"] = message
    
    # Add data based on type
    if isinstance(data, dict):
        response.update(data)
    elif isinstance(data, list):
        response["data"] = data
    else:
        response["result"] = data
    
    return response


def parse_time_range(time_str: str) -> timedelta:
    """Parse time range string to timedelta."""
    if not time_str:
        return timedelta(hours=24)  # Default to 24 hours
    
    time_str = time_str.lower().strip()
    
    try:
        if time_str.endswith('h'):
            hours = int(time_str[:-1])
            return timedelta(hours=hours)
        elif time_str.endswith('d'):
            days = int(time_str[:-1])
            return timedelta(days=days)
        elif time_str.endswith('m'):
            minutes = int(time_str[:-1])
            return timedelta(minutes=minutes)
        elif time_str.endswith('s'):
            seconds = int(time_str[:-1])
            return timedelta(seconds=seconds)
        else:
            # Assume hours if no unit
            hours = int(time_str)
            return timedelta(hours=hours)
    except ValueError:
        logger.warning(f"Could not parse time range: {time_str}, using default 24h")
        return timedelta(hours=24)


def merge_performance_data(data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple performance data points."""
    if not data_points:
        return {
            "calls": 0,
            "errors": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "error_rate": 0.0
        }
    
    total_calls = sum(point.get("calls", 0) for point in data_points)
    total_errors = sum(point.get("errors", 0) for point in data_points) 
    total_time = sum(point.get("total_time", 0.0) for point in data_points)
    
    avg_time = total_time / total_calls if total_calls > 0 else 0.0
    error_rate = total_errors / total_calls if total_calls > 0 else 0.0
    
    return {
        "calls": total_calls,
        "errors": total_errors,
        "total_time": total_time,
        "avg_time": round(avg_time, 4),
        "error_rate": round(error_rate, 4)
    }