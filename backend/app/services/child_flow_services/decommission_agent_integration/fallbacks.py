"""
Decommission Agent Integration - Fallback Results Module

Generates fallback results when agents are unavailable.
"""

from typing import Any, Dict, List


def _generate_fallback_planning_result(system_ids: List[str]) -> Dict[str, Any]:
    """Generate fallback planning result when agents unavailable."""
    return {
        "dependency_map": [],
        "impact_zones": [],
        "risk_assessment": {
            "risk_level": "unknown",
            "factors": ["Agent unavailable - manual review required"],
        },
        "system_count": len(system_ids),
        "fallback_mode": True,
    }


def _generate_fallback_migration_result(system_ids: List[str]) -> Dict[str, Any]:
    """Generate fallback migration result when agents unavailable."""
    return {
        "retention_policies": {},
        "archival_plan": {},
        "compliance_status": "pending_review",
        "system_count": len(system_ids),
        "fallback_mode": True,
    }


def _generate_fallback_shutdown_result(system_ids: List[str]) -> Dict[str, Any]:
    """Generate fallback shutdown result when agents unavailable."""
    return {
        "shutdown_sequence": [],
        "rollback_checkpoints": [],
        "validation_results": {},
        "system_count": len(system_ids),
        "fallback_mode": True,
    }
