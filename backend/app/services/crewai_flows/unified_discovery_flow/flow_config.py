"""
Flow Configuration and Constants

Contains all configuration, constants, and phase definitions
for the Unified Discovery Flow.

Per ADR-027: Phase sequences now read from FlowTypeConfig.
"""

import logging
from enum import Enum
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class PhaseNames(str, Enum):
    """
    Phase names enumeration for type safety

    NOTE: Some legacy phase names retained for backward compatibility.
    See get_phase_order() for mapping to FlowTypeConfig phases.
    """

    DATA_IMPORT_VALIDATION = "data_import_validation"
    FIELD_MAPPING = "field_mapping"
    DATA_CLEANSING = "data_cleansing"
    ASSET_INVENTORY = "asset_inventory"
    # Legacy phases (moved to Assessment flow per ADR-027 v3.0.0)
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    TECH_DEBT_ASSESSMENT = "tech_debt_assessment"


class FlowConfig:
    """Configuration constants for the Unified Discovery Flow"""

    # Flow metadata
    FLOW_NAME = "unified_discovery_flow"
    FLOW_VERSION = "3.0.0"  # Per ADR-027: Aligned with FlowTypeConfig

    @classmethod
    def get_phase_order(cls) -> List[str]:
        """
        Get Discovery phase order from FlowTypeConfig (Per ADR-027).

        Returns phase names as strings for backward compatibility.

        Fallback: If FlowTypeConfig unavailable, returns legacy phases.
        """
        try:
            from app.services.flow_type_registry_helpers import get_flow_config

            config = get_flow_config("discovery")
            phase_names = [p.name for p in config.phases]
            logger.debug(f"Phase order from FlowTypeConfig: {phase_names}")
            return phase_names
        except (ValueError, ImportError) as e:
            logger.warning(f"FlowTypeConfig not found, using legacy phase order: {e}")
            # Legacy fallback (5 phases post-ADR-027 v3.0.0)
            return [
                "data_import",
                "data_validation",
                "field_mapping",
                "data_cleansing",
                "asset_inventory",
            ]

    # DEPRECATED: Use get_phase_order() instead (ADR-027)
    # Retained for backward compatibility with existing code
    PHASE_ORDER = None  # Will be populated dynamically

    # Parallel analysis phases (DEPRECATED - moved to Assessment flow)
    # Retained for backward compatibility
    PARALLEL_ANALYSIS_PHASES = []

    # User approval configuration
    USER_APPROVAL_REQUIRED_FIELDS = [
        "field_mappings",
        "data_quality_threshold",
        "asset_classification_confidence",
    ]

    # Asset type mappings
    ASSET_TYPE_KEYWORDS = {
        "server": ["server", "host", "node", "machine", "vm", "virtual", "physical"],
        "database": ["database", "db", "sql", "oracle", "mysql", "postgres", "mongodb"],
        "application": ["app", "application", "service", "api", "web", "software"],
        "network": ["network", "router", "switch", "firewall", "load balancer", "lb"],
        "storage": ["storage", "san", "nas", "disk", "volume", "backup"],
        "middleware": ["middleware", "mq", "queue", "broker", "esb"],
        "container": ["container", "docker", "kubernetes", "k8s", "pod"],
        "cloud": ["cloud", "aws", "azure", "gcp", "saas", "paas", "iaas"],
    }

    # Default values
    DEFAULT_CONFIDENCE_THRESHOLD = 0.85
    DEFAULT_DATA_QUALITY_THRESHOLD = 0.90
    DEFAULT_BATCH_SIZE = 100

    # Timeouts (in seconds) - None means no timeout for agentic activities
    PHASE_TIMEOUT = None  # No timeout per phase for agentic activities
    AGENT_TIMEOUT = None  # No timeout per agent for agentic activities

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds

    @classmethod
    def get_phase_config(cls, phase_name: PhaseNames) -> Dict[str, Any]:
        """Get configuration for a specific phase"""
        phase_configs = {
            PhaseNames.DATA_IMPORT_VALIDATION: {
                "timeout": None,  # No timeout for agentic activities
                "retries": 2,
                "validation_threshold": 0.95,
            },
            PhaseNames.FIELD_MAPPING: {
                "timeout": None,  # No timeout for agentic activities
                "retries": 3,
                "user_approval_required": True,
                "confidence_threshold": cls.DEFAULT_CONFIDENCE_THRESHOLD,
            },
            PhaseNames.DATA_CLEANSING: {
                "timeout": None,  # No timeout for agentic activities
                "retries": 2,
                "quality_threshold": cls.DEFAULT_DATA_QUALITY_THRESHOLD,
            },
            PhaseNames.ASSET_INVENTORY: {
                "timeout": None,  # No timeout for agentic activities
                "retries": 2,
                "batch_size": cls.DEFAULT_BATCH_SIZE,
            },
            PhaseNames.DEPENDENCY_ANALYSIS: {
                "timeout": None,  # No timeout for agentic activities
                "retries": 2,
                "parallel": True,
            },
            PhaseNames.TECH_DEBT_ASSESSMENT: {
                "timeout": None,  # No timeout for agentic activities
                "retries": 2,
                "parallel": True,
            },
        }
        return phase_configs.get(phase_name, {})

    @classmethod
    def get_agent_config(cls) -> Dict[str, Any]:
        """Get agent configuration"""
        return {
            "max_iterations": 10,
            "temperature": 0.7,
            "model": "gpt-4",
            "timeout": cls.AGENT_TIMEOUT,  # None for agentic activities
            "retry_on_failure": True,
        }
