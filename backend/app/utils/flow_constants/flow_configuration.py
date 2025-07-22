"""
Flow configuration definitions and management utilities.
Provides standardized flow configurations and validation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .flow_states import FlowPhase, FlowPriority, FlowType


class ConfigurationLevel(str, Enum):
    """Configuration inheritance levels."""
    GLOBAL = "global"
    FLOW_TYPE = "flow_type"
    PHASE = "phase"
    INSTANCE = "instance"

@dataclass
class PhaseConfiguration:
    """Configuration for a flow phase."""
    phase: FlowPhase
    enabled: bool = True
    required: bool = True
    timeout_seconds: int = 3600
    max_retries: int = 3
    parallel_execution: bool = False
    dependencies: List[FlowPhase] = field(default_factory=list)
    agent_config: Dict[str, Any] = field(default_factory=dict)
    validation_rules: List[str] = field(default_factory=list)
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    rollback_enabled: bool = True
    checkpoint_enabled: bool = True
    
    def validate(self) -> List[str]:
        """Validate phase configuration."""
        errors = []
        
        if self.timeout_seconds <= 0:
            errors.append("Timeout seconds must be positive")
        
        if self.max_retries < 0:
            errors.append("Max retries cannot be negative")
        
        # Validate dependencies don't create cycles
        if self.phase in self.dependencies:
            errors.append("Phase cannot depend on itself")
        
        return errors

@dataclass
class FlowConfiguration:
    """Configuration for a complete flow."""
    flow_type: FlowType
    name: str
    description: str
    priority: FlowPriority = FlowPriority.NORMAL
    phases: List[PhaseConfiguration] = field(default_factory=list)
    global_timeout_seconds: int = 14400  # 4 hours
    max_concurrent_phases: int = 1
    error_handling_strategy: str = "fail_fast"
    notification_settings: Dict[str, Any] = field(default_factory=dict)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """Validate flow configuration."""
        errors = []
        
        if not self.name:
            errors.append("Flow name is required")
        
        if self.global_timeout_seconds <= 0:
            errors.append("Global timeout must be positive")
        
        if self.max_concurrent_phases <= 0:
            errors.append("Max concurrent phases must be positive")
        
        # Validate phases
        if not self.phases:
            errors.append("At least one phase is required")
        
        for phase_config in self.phases:
            phase_errors = phase_config.validate()
            errors.extend([f"Phase {phase_config.phase.value}: {error}" for error in phase_errors])
        
        # Check for duplicate phases
        phase_names = [p.phase for p in self.phases]
        if len(phase_names) != len(set(phase_names)):
            errors.append("Duplicate phases found")
        
        # Validate dependencies
        phase_set = set(phase_names)
        for phase_config in self.phases:
            for dep in phase_config.dependencies:
                if dep not in phase_set:
                    errors.append(f"Phase {phase_config.phase.value} depends on non-existent phase {dep.value}")
        
        return errors
    
    def get_phase_config(self, phase: FlowPhase) -> Optional[PhaseConfiguration]:
        """Get configuration for a specific phase."""
        for phase_config in self.phases:
            if phase_config.phase == phase:
                return phase_config
        return None
    
    def get_enabled_phases(self) -> List[FlowPhase]:
        """Get list of enabled phases."""
        return [pc.phase for pc in self.phases if pc.enabled]
    
    def get_required_phases(self) -> List[FlowPhase]:
        """Get list of required phases."""
        return [pc.phase for pc in self.phases if pc.required and pc.enabled]

# Default configurations for different flow types
DEFAULT_FLOW_CONFIGS: Dict[FlowType, FlowConfiguration] = {
    FlowType.DISCOVERY: FlowConfiguration(
        flow_type=FlowType.DISCOVERY,
        name="Discovery Flow",
        description="Comprehensive application discovery and analysis",
        priority=FlowPriority.HIGH,
        phases=[
            PhaseConfiguration(
                phase=FlowPhase.INITIALIZATION,
                timeout_seconds=60,
                max_retries=2,
                agent_config={"type": "initialization_agent"},
                validation_rules=["context_validation", "permissions_check"]
            ),
            PhaseConfiguration(
                phase=FlowPhase.DATA_IMPORT,
                timeout_seconds=600,
                max_retries=3,
                agent_config={"type": "data_import_agent", "batch_size": 1000},
                validation_rules=["file_format_validation", "size_limits"]
            ),
            PhaseConfiguration(
                phase=FlowPhase.DATA_VALIDATION,
                timeout_seconds=300,
                max_retries=2,
                dependencies=[FlowPhase.DATA_IMPORT],
                agent_config={"type": "validation_agent"},
                validation_rules=["data_integrity", "schema_validation"]
            ),
            PhaseConfiguration(
                phase=FlowPhase.FIELD_MAPPING,
                timeout_seconds=600,
                max_retries=3,
                dependencies=[FlowPhase.DATA_VALIDATION],
                agent_config={"type": "field_mapping_agent", "confidence_threshold": 0.8},
                validation_rules=["mapping_completeness", "field_types"]
            ),
            PhaseConfiguration(
                phase=FlowPhase.DATA_CLEANSING,
                timeout_seconds=1800,
                max_retries=2,
                dependencies=[FlowPhase.FIELD_MAPPING],
                agent_config={"type": "cleansing_agent", "quality_threshold": 0.9},
                validation_rules=["data_quality", "cleansing_rules"]
            ),
            PhaseConfiguration(
                phase=FlowPhase.ASSET_INVENTORY,
                timeout_seconds=900,
                max_retries=3,
                dependencies=[FlowPhase.DATA_CLEANSING],
                agent_config={"type": "inventory_agent", "classification_enabled": True},
                validation_rules=["asset_completeness", "classification_accuracy"]
            ),
            PhaseConfiguration(
                phase=FlowPhase.DEPENDENCY_ANALYSIS,
                timeout_seconds=1800,
                max_retries=2,
                dependencies=[FlowPhase.ASSET_INVENTORY],
                agent_config={"type": "dependency_agent", "depth_limit": 5},
                validation_rules=["dependency_consistency", "circular_dependency_check"]
            ),
            PhaseConfiguration(
                phase=FlowPhase.TECH_DEBT_ANALYSIS,
                timeout_seconds=1200,
                max_retries=3,
                dependencies=[FlowPhase.DEPENDENCY_ANALYSIS],
                agent_config={"type": "tech_debt_agent", "scoring_model": "comprehensive"},
                validation_rules=["scoring_completeness", "risk_assessment"]
            ),
            PhaseConfiguration(
                phase=FlowPhase.FINALIZATION,
                timeout_seconds=300,
                max_retries=1,
                dependencies=[FlowPhase.TECH_DEBT_ANALYSIS],
                agent_config={"type": "finalization_agent"},
                validation_rules=["completion_check", "report_generation"]
            )
        ],
        global_timeout_seconds=14400,
        max_concurrent_phases=2,
        error_handling_strategy="retry_then_fail",
        notification_settings={
            "on_completion": True,
            "on_failure": True,
            "on_phase_completion": False,
            "channels": ["email", "system"]
        },
        resource_limits={
            "max_memory_mb": 2000,
            "max_cpu_percent": 80,
            "max_disk_mb": 5000
        }
    ),
    
    FlowType.ASSESSMENT: FlowConfiguration(
        flow_type=FlowType.ASSESSMENT,
        name="Assessment Flow",
        description="Application assessment and readiness evaluation",
        priority=FlowPriority.HIGH,
        phases=[
            PhaseConfiguration(
                phase=FlowPhase.INITIALIZATION,
                timeout_seconds=30,
                max_retries=2,
                agent_config={"type": "assessment_init_agent"},
                validation_rules=["inventory_check", "prerequisites"]
            ),
            PhaseConfiguration(
                phase=FlowPhase.ASSESSMENT,
                timeout_seconds=3600,
                max_retries=2,
                dependencies=[FlowPhase.INITIALIZATION],
                agent_config={"type": "assessment_agent", "assessment_depth": "comprehensive"},
                validation_rules=["assessment_completeness", "scoring_validation"]
            ),
            PhaseConfiguration(
                phase=FlowPhase.TECH_DEBT_ANALYSIS,
                timeout_seconds=1800,
                max_retries=2,
                dependencies=[FlowPhase.ASSESSMENT],
                agent_config={"type": "tech_debt_agent", "integration_mode": "assessment"},
                validation_rules=["tech_debt_scoring", "risk_analysis"]
            ),
            PhaseConfiguration(
                phase=FlowPhase.FINALIZATION,
                timeout_seconds=300,
                max_retries=1,
                dependencies=[FlowPhase.TECH_DEBT_ANALYSIS],
                agent_config={"type": "assessment_finalization_agent"},
                validation_rules=["report_generation", "recommendations"]
            )
        ],
        global_timeout_seconds=7200,
        max_concurrent_phases=1,
        error_handling_strategy="fail_fast",
        notification_settings={
            "on_completion": True,
            "on_failure": True,
            "on_phase_completion": True,
            "channels": ["email", "system", "webhook"]
        },
        resource_limits={
            "max_memory_mb": 1500,
            "max_cpu_percent": 70,
            "max_disk_mb": 3000
        }
    ),
    
    FlowType.PLANNING: FlowConfiguration(
        flow_type=FlowType.PLANNING,
        name="Planning Flow",
        description="Migration planning and strategy development",
        priority=FlowPriority.NORMAL,
        phases=[
            PhaseConfiguration(
                phase=FlowPhase.INITIALIZATION,
                timeout_seconds=30,
                max_retries=2,
                agent_config={"type": "planning_init_agent"},
                validation_rules=["assessment_availability", "strategy_requirements"]
            ),
            PhaseConfiguration(
                phase=FlowPhase.PLANNING,
                timeout_seconds=1800,
                max_retries=2,
                dependencies=[FlowPhase.INITIALIZATION],
                agent_config={"type": "planning_agent", "strategy_types": ["rehost", "replatform", "refactor"]},
                validation_rules=["plan_completeness", "strategy_validation"]
            ),
            PhaseConfiguration(
                phase=FlowPhase.FINALIZATION,
                timeout_seconds=300,
                max_retries=1,
                dependencies=[FlowPhase.PLANNING],
                agent_config={"type": "planning_finalization_agent"},
                validation_rules=["plan_approval", "timeline_validation"]
            )
        ],
        global_timeout_seconds=3600,
        max_concurrent_phases=1,
        error_handling_strategy="retry_then_fail",
        notification_settings={
            "on_completion": True,
            "on_failure": True,
            "on_phase_completion": False,
            "channels": ["email", "system"]
        },
        resource_limits={
            "max_memory_mb": 1000,
            "max_cpu_percent": 60,
            "max_disk_mb": 2000
        }
    )
}

# Helper functions
def get_flow_configuration(flow_type: FlowType) -> FlowConfiguration:
    """Get default configuration for a flow type."""
    return DEFAULT_FLOW_CONFIGS.get(flow_type, DEFAULT_FLOW_CONFIGS[FlowType.DISCOVERY])

def get_phase_configuration(flow_type: FlowType, phase: FlowPhase) -> Optional[PhaseConfiguration]:
    """Get configuration for a specific phase in a flow type."""
    flow_config = get_flow_configuration(flow_type)
    return flow_config.get_phase_config(phase)

def validate_flow_configuration(config: FlowConfiguration) -> List[str]:
    """Validate a flow configuration."""
    return config.validate()

def merge_flow_configurations(base_config: FlowConfiguration, 
                            override_config: Dict[str, Any]) -> FlowConfiguration:
    """Merge base configuration with overrides."""
    # Create a copy of base config
    merged_config = FlowConfiguration(
        flow_type=base_config.flow_type,
        name=override_config.get("name", base_config.name),
        description=override_config.get("description", base_config.description),
        priority=FlowPriority(override_config.get("priority", base_config.priority.value)),
        phases=base_config.phases.copy(),
        global_timeout_seconds=override_config.get("global_timeout_seconds", base_config.global_timeout_seconds),
        max_concurrent_phases=override_config.get("max_concurrent_phases", base_config.max_concurrent_phases),
        error_handling_strategy=override_config.get("error_handling_strategy", base_config.error_handling_strategy),
        notification_settings={**base_config.notification_settings, **override_config.get("notification_settings", {})},
        resource_limits={**base_config.resource_limits, **override_config.get("resource_limits", {})},
        metadata={**base_config.metadata, **override_config.get("metadata", {})}
    )
    
    # Merge phase configurations
    if "phases" in override_config:
        phase_overrides = override_config["phases"]
        for phase_override in phase_overrides:
            phase_name = phase_override.get("phase")
            if phase_name:
                phase_enum = FlowPhase(phase_name)
                existing_phase = merged_config.get_phase_config(phase_enum)
                
                if existing_phase:
                    # Update existing phase
                    for key, value in phase_override.items():
                        if key != "phase" and hasattr(existing_phase, key):
                            setattr(existing_phase, key, value)
                else:
                    # Add new phase
                    new_phase = PhaseConfiguration(
                        phase=phase_enum,
                        **{k: v for k, v in phase_override.items() if k != "phase"}
                    )
                    merged_config.phases.append(new_phase)
    
    return merged_config

def create_custom_flow_configuration(flow_type: FlowType, 
                                   name: str,
                                   phases: List[Dict[str, Any]],
                                   **kwargs) -> FlowConfiguration:
    """Create a custom flow configuration."""
    phase_configs = []
    for phase_data in phases:
        phase_config = PhaseConfiguration(
            phase=FlowPhase(phase_data["phase"]),
            **{k: v for k, v in phase_data.items() if k != "phase"}
        )
        phase_configs.append(phase_config)
    
    return FlowConfiguration(
        flow_type=flow_type,
        name=name,
        description=kwargs.get("description", f"Custom {flow_type.value} flow"),
        priority=FlowPriority(kwargs.get("priority", FlowPriority.NORMAL.value)),
        phases=phase_configs,
        global_timeout_seconds=kwargs.get("global_timeout_seconds", 14400),
        max_concurrent_phases=kwargs.get("max_concurrent_phases", 1),
        error_handling_strategy=kwargs.get("error_handling_strategy", "fail_fast"),
        notification_settings=kwargs.get("notification_settings", {}),
        resource_limits=kwargs.get("resource_limits", {}),
        metadata=kwargs.get("metadata", {})
    )

def get_phase_dependencies(flow_type: FlowType, phase: FlowPhase) -> List[FlowPhase]:
    """Get dependencies for a specific phase."""
    phase_config = get_phase_configuration(flow_type, phase)
    return phase_config.dependencies if phase_config else []

def is_phase_enabled(flow_type: FlowType, phase: FlowPhase) -> bool:
    """Check if a phase is enabled for a flow type."""
    phase_config = get_phase_configuration(flow_type, phase)
    return phase_config.enabled if phase_config else False

def get_phase_timeout(flow_type: FlowType, phase: FlowPhase) -> int:
    """Get timeout for a specific phase."""
    phase_config = get_phase_configuration(flow_type, phase)
    return phase_config.timeout_seconds if phase_config else 3600