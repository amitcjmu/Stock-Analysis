"""
Inventory Building Tools - Tool Creation Functions

This module contains tool creation functions for the Inventory Building Crew.
These tools support server, application, and device classification.

The tools are created as functions that return tool instances, allowing them
to be configured per-crew-instance as needed.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _create_server_classification_tools() -> List[Any]:
    """
    Create tools for server classification.

    When implemented, these tools should:
    - Identify server types (physical, virtual, cloud)
    - Analyze OS and hardware specifications
    - Determine hosting relationships
    - Map server dependencies

    Returns:
        List of server classification tool instances
    """
    logger.debug("Server classification tools not yet implemented")
    return []


def _create_app_classification_tools() -> List[Any]:
    """
    Create tools for application classification.

    When implemented, these tools should:
    - Identify application types and versions
    - Analyze business criticality
    - Map application dependencies
    - Detect hosting relationships

    Returns:
        List of application classification tool instances
    """
    logger.debug("Application classification tools not yet implemented")
    return []


def _create_device_classification_tools() -> List[Any]:
    """
    Create tools for device classification.

    When implemented, these tools should:
    - Identify network device types
    - Analyze device roles in topology
    - Map device dependencies
    - Classify security appliances

    Returns:
        List of device classification tool instances
    """
    logger.debug("Device classification tools not yet implemented")
    return []


def _identify_asset_type_indicators(data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Identify potential asset type indicators in the data.

    This utility function analyzes a sample of the data to determine
    what types of assets are present based on keyword matching.

    Args:
        data: List of asset records to analyze

    Returns:
        Dictionary with counts of different asset type indicators
    """
    if not data:
        return {}

    indicators = {"servers": 0, "applications": 0, "devices": 0, "unknown": 0}
    server_keywords = ["server", "host", "vm", "virtual", "linux", "windows"]
    app_keywords = ["app", "application", "service", "software", "web"]
    device_keywords = ["router", "switch", "firewall", "network", "device"]

    for record in data[:10]:  # Sample analysis
        record_str = str(record).lower()
        if any(keyword in record_str for keyword in server_keywords):
            indicators["servers"] += 1
        elif any(keyword in record_str for keyword in app_keywords):
            indicators["applications"] += 1
        elif any(keyword in record_str for keyword in device_keywords):
            indicators["devices"] += 1
        else:
            indicators["unknown"] += 1

    return indicators


def _filter_infrastructure_mappings(mappings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter field mappings relevant to infrastructure assets.

    Args:
        mappings: Complete field mappings dictionary

    Returns:
        Filtered mappings containing only infrastructure-related fields
    """
    infra_fields = [
        "operating_system",
        "ip_address",
        "cpu_cores",
        "memory_gb",
        "storage_gb",
    ]
    return {
        k: v
        for k, v in mappings.items()
        if any(field in str(v).lower() for field in infra_fields)
    }


def _filter_application_mappings(mappings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter field mappings relevant to applications.

    Args:
        mappings: Complete field mappings dictionary

    Returns:
        Filtered mappings containing only application-related fields
    """
    app_fields = [
        "application",
        "service",
        "version",
        "environment",
        "business_criticality",
    ]
    return {
        k: v
        for k, v in mappings.items()
        if any(field in str(v).lower() for field in app_fields)
    }


def _filter_device_mappings(mappings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter field mappings relevant to devices.

    Args:
        mappings: Complete field mappings dictionary

    Returns:
        Filtered mappings containing only device-related fields
    """
    device_fields = ["device", "network", "router", "switch", "firewall"]
    return {
        k: v
        for k, v in mappings.items()
        if any(field in str(v).lower() for field in device_fields)
    }


__all__ = [
    "_create_server_classification_tools",
    "_create_app_classification_tools",
    "_create_device_classification_tools",
    "_identify_asset_type_indicators",
    "_filter_infrastructure_mappings",
    "_filter_application_mappings",
    "_filter_device_mappings",
]
