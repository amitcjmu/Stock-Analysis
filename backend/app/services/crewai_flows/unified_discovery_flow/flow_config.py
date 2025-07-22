"""
Flow Configuration and Constants

Contains all configuration, constants, and phase definitions
for the Unified Discovery Flow.
"""

from enum import Enum
from typing import Any, Dict, List


class PhaseNames(str, Enum):
    """Phase names enumeration for type safety"""
    DATA_IMPORT_VALIDATION = "data_import_validation"
    FIELD_MAPPING = "field_mapping"
    DATA_CLEANSING = "data_cleansing"
    ASSET_INVENTORY = "asset_inventory"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    TECH_DEBT_ASSESSMENT = "tech_debt_assessment"


class FlowConfig:
    """Configuration constants for the Unified Discovery Flow"""
    
    # Flow metadata
    FLOW_NAME = "unified_discovery_flow"
    FLOW_VERSION = "1.0.0"
    
    # Phase order
    PHASE_ORDER = [
        PhaseNames.DATA_IMPORT_VALIDATION,
        PhaseNames.FIELD_MAPPING,
        PhaseNames.DATA_CLEANSING,
        PhaseNames.ASSET_INVENTORY,
        PhaseNames.DEPENDENCY_ANALYSIS,
        PhaseNames.TECH_DEBT_ASSESSMENT
    ]
    
    # Parallel analysis phases
    PARALLEL_ANALYSIS_PHASES = [
        PhaseNames.DEPENDENCY_ANALYSIS,
        PhaseNames.TECH_DEBT_ASSESSMENT
    ]
    
    # User approval configuration
    USER_APPROVAL_REQUIRED_FIELDS = [
        "field_mappings",
        "data_quality_threshold",
        "asset_classification_confidence"
    ]
    
    # Asset type mappings
    ASSET_TYPE_KEYWORDS = {
        'server': ['server', 'host', 'node', 'machine', 'vm', 'virtual', 'physical'],
        'database': ['database', 'db', 'sql', 'oracle', 'mysql', 'postgres', 'mongodb'],
        'application': ['app', 'application', 'service', 'api', 'web', 'software'],
        'network': ['network', 'router', 'switch', 'firewall', 'load balancer', 'lb'],
        'storage': ['storage', 'san', 'nas', 'disk', 'volume', 'backup'],
        'middleware': ['middleware', 'mq', 'queue', 'broker', 'esb'],
        'container': ['container', 'docker', 'kubernetes', 'k8s', 'pod'],
        'cloud': ['cloud', 'aws', 'azure', 'gcp', 'saas', 'paas', 'iaas']
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
                "validation_threshold": 0.95
            },
            PhaseNames.FIELD_MAPPING: {
                "timeout": None,  # No timeout for agentic activities
                "retries": 3,
                "user_approval_required": True,
                "confidence_threshold": cls.DEFAULT_CONFIDENCE_THRESHOLD
            },
            PhaseNames.DATA_CLEANSING: {
                "timeout": None,  # No timeout for agentic activities
                "retries": 2,
                "quality_threshold": cls.DEFAULT_DATA_QUALITY_THRESHOLD
            },
            PhaseNames.ASSET_INVENTORY: {
                "timeout": None,  # No timeout for agentic activities
                "retries": 2,
                "batch_size": cls.DEFAULT_BATCH_SIZE
            },
            PhaseNames.DEPENDENCY_ANALYSIS: {
                "timeout": None,  # No timeout for agentic activities
                "retries": 2,
                "parallel": True
            },
            PhaseNames.TECH_DEBT_ASSESSMENT: {
                "timeout": None,  # No timeout for agentic activities
                "retries": 2,
                "parallel": True
            }
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
            "retry_on_failure": True
        }