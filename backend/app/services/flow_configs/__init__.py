"""
Flow Configurations Module
MFO-056: Register all flows with registry

This module provides centralized access to all flow configurations and
handles registration of all flow types with the registry.
"""

import logging
from typing import Any, Dict, List

# Registry imports - removing unused imports
# These were previously imported but not used in this module
from .additional_flow_configs import (
    get_decommission_flow_config,
    get_execution_flow_config,
    get_finops_flow_config,
    get_modernize_flow_config,
    get_observability_flow_config,
    get_planning_flow_config,
)
from .additional_handlers import (  # Multiple handlers: Decommission, Execution, FinOps, etc.
    cost_data_collection,
    decommission_completion,
    decommission_error_handler,
    decommission_finalization,
    decommission_initialization,
    environment_preparation,
    execution_error_handler,
    execution_finalization,
    execution_initialization,
    final_backup,
    finops_completion,
    finops_error_handler,
    finops_finalization,
    finops_initialization,
    impact_analysis,
    migration_completion,
    modernization_completion,
    modernize_error_handler,
    modernize_finalization,
    modernize_initialization,
    monitoring_design,
    observability_completion,
    observability_error_handler,
    observability_finalization,
    observability_initialization,
    planning_completion,
    planning_error_handler,
    planning_finalization,
    planning_initialization,
    wave_analysis,
    wave_optimization,
)
from .additional_validators import (  # Multiple validators for various flow types
    alerting_validation,
    architecture_validation,
    budget_validation,
    capacity_validation,
    cost_validation,
    data_migration_validation,
    decommission_validation,
    dependency_validation,
    execution_validation,
    logging_validation,
    modernization_validation,
    monitoring_validation,
    optimization_validation,
    post_migration_validation,
    pre_migration_validation,
    resource_validation,
    shutdown_validation,
    timeline_validation,
    wave_validation,
)
from .assessment_flow_config import get_assessment_flow_config
from .assessment_handlers import (
    assessment_completion,
    assessment_error_handler,
    assessment_finalization,
    assessment_initialization,
    complexity_categorization,
    complexity_preparation,
    mitigation_planning,
    readiness_preparation,
    readiness_scoring,
    recommendation_analysis,
    risk_identification,
    roadmap_generation,
)
from .assessment_validators import (
    assessment_validation,
    complexity_validation,
    inventory_completeness,
    mitigation_validation,
    recommendation_validation,
    risk_validation,
    roadmap_validation,
    score_validation,
)
from .collection_flow_config import get_collection_flow_config
from .collection_handlers import (
    adapter_preparation,
    collection_checkpoint_handler,
    collection_data_normalization,
    collection_error_handler,
    collection_finalization,
    collection_initialization,
    collection_rollback_handler,
    gap_analysis_preparation,
    gap_prioritization,
    platform_inventory_creation,
    questionnaire_generation,
    response_processing,
    synthesis_preparation,
)
from .collection_validators import (
    collection_validation,
    completeness_validation,
    credential_validation,
    data_quality_validation,
    final_validation,
    gap_validation,
    platform_validation,
    response_validation,
    sixr_impact_validation,
    sixr_readiness_validation,
)

# Import flow configurations
from .discovery_flow_config import get_discovery_flow_config

# Import handlers
from .discovery_handlers import (
    asset_creation_completion,
    asset_inventory,
    data_import_preparation,
    discovery_error_handler,
    discovery_finalization,
    discovery_initialization,
)
from .discovery_handlers import data_import_validation as data_import_validation_handler

# Import validators
from .discovery_validators import (
    asset_validation,
    circular_dependency_check,
    cleansing_validation,
    field_mapping_validation,
    inventory_validation,
    mapping_completeness,
)
from .discovery_validators import (
    dependency_validation as discovery_dependency_validation,
)

logger = logging.getLogger(__name__)


class FlowConfigurationManager:
    """
    Manages registration and initialization of all flow types
    """

    def __init__(self):
        # [ECHO] Use global singleton instances instead of creating new ones
        from app.services.flow_type_registry import flow_type_registry
        from app.services.handler_registry import handler_registry
        from app.services.validator_registry import validator_registry

        self.flow_registry = flow_type_registry  # Use global singleton
        self.validator_registry = validator_registry  # Use global singleton
        self.handler_registry = handler_registry  # Use global singleton
        self._initialized = False

    def initialize_all_flows(self) -> Dict[str, Any]:
        """
        Initialize and register all flow types
        MFO-056: Register all flows with registry
        """
        if self._initialized:
            logger.info("Flow configurations already initialized")
            return {"status": "already_initialized"}

        results = {
            "flows_registered": [],
            "validators_registered": [],
            "handlers_registered": [],
            "errors": [],
        }

        try:
            # Register all validators first
            self._register_all_validators(results)

            # Register all handlers
            self._register_all_handlers(results)

            # Register all flow types
            self._register_all_flows(results)

            self._initialized = True
            logger.info(
                f"✅ Flow configuration complete: {len(results['flows_registered'])} flows registered"
            )

            return results

        except Exception as e:
            logger.error(f"❌ Flow configuration initialization failed: {e}")
            results["errors"].append(str(e))
            return results

    def _register_all_validators(self, results: Dict[str, Any]) -> None:
        """Register all validators with the validator registry"""
        validators = {
            # Discovery validators
            "field_mapping_validation": field_mapping_validation,
            "asset_validation": asset_validation,
            "inventory_validation": inventory_validation,
            "discovery_dependency_validation": discovery_dependency_validation,
            "mapping_completeness": mapping_completeness,
            "cleansing_validation": cleansing_validation,
            "circular_dependency_check": circular_dependency_check,
            # Assessment validators
            "assessment_validation": assessment_validation,
            "complexity_validation": complexity_validation,
            "risk_validation": risk_validation,
            "recommendation_validation": recommendation_validation,
            "inventory_completeness": inventory_completeness,
            "score_validation": score_validation,
            "mitigation_validation": mitigation_validation,
            "roadmap_validation": roadmap_validation,
            # Collection validators
            "platform_validation": platform_validation,
            "credential_validation": credential_validation,
            "collection_validation": collection_validation,
            "data_quality_validation": data_quality_validation,
            "gap_validation": gap_validation,
            "sixr_impact_validation": sixr_impact_validation,
            "response_validation": response_validation,
            "completeness_validation": completeness_validation,
            "final_validation": final_validation,
            "sixr_readiness_validation": sixr_readiness_validation,
            # Planning validators
            "wave_validation": wave_validation,
            "resource_validation": resource_validation,
            # Execution validators
            "pre_migration_validation": pre_migration_validation,
            "execution_validation": execution_validation,
            "post_migration_validation": post_migration_validation,
            # Modernize validators
            "modernization_validation": modernization_validation,
            "architecture_validation": architecture_validation,
            # FinOps validators
            "cost_validation": cost_validation,
            "optimization_validation": optimization_validation,
            "budget_validation": budget_validation,
            # Observability validators
            "monitoring_validation": monitoring_validation,
            "logging_validation": logging_validation,
            "alerting_validation": alerting_validation,
            # Decommission validators
            "decommission_validation": decommission_validation,
            "data_migration_validation": data_migration_validation,
            "shutdown_validation": shutdown_validation,
            # Common validators
            "dependency_validation": dependency_validation,
            "timeline_validation": timeline_validation,
            "capacity_validation": capacity_validation,
        }

        for name, validator in validators.items():
            try:
                self.validator_registry.register_validator(name, validator)
                results["validators_registered"].append(name)
            except Exception as e:
                logger.error(f"Failed to register validator {name}: {e}")
                results["errors"].append(f"Validator {name}: {str(e)}")

    def _register_all_handlers(self, results: Dict[str, Any]) -> None:
        """Register all handlers with the handler registry"""
        handlers = {
            # Discovery handlers
            "discovery_initialization": discovery_initialization,
            "discovery_finalization": discovery_finalization,
            "discovery_error_handler": discovery_error_handler,
            "asset_creation_completion": asset_creation_completion,
            "asset_inventory": asset_inventory,
            "data_import_preparation": data_import_preparation,
            "data_import_validation": data_import_validation_handler,
            # Assessment handlers
            "assessment_initialization": assessment_initialization,
            "assessment_finalization": assessment_finalization,
            "assessment_error_handler": assessment_error_handler,
            "assessment_completion": assessment_completion,
            "readiness_preparation": readiness_preparation,
            "readiness_scoring": readiness_scoring,
            "complexity_preparation": complexity_preparation,
            "complexity_categorization": complexity_categorization,
            "risk_identification": risk_identification,
            "mitigation_planning": mitigation_planning,
            "recommendation_analysis": recommendation_analysis,
            "roadmap_generation": roadmap_generation,
            # Collection handlers
            "collection_initialization": collection_initialization,
            "collection_finalization": collection_finalization,
            "collection_error_handler": collection_error_handler,
            "collection_rollback_handler": collection_rollback_handler,
            "collection_checkpoint_handler": collection_checkpoint_handler,
            "platform_inventory_creation": platform_inventory_creation,
            "adapter_preparation": adapter_preparation,
            "collection_data_normalization": collection_data_normalization,
            "gap_analysis_preparation": gap_analysis_preparation,
            "gap_prioritization": gap_prioritization,
            "questionnaire_generation": questionnaire_generation,
            "response_processing": response_processing,
            "synthesis_preparation": synthesis_preparation,
            # Planning handlers
            "planning_initialization": planning_initialization,
            "planning_finalization": planning_finalization,
            "planning_error_handler": planning_error_handler,
            "planning_completion": planning_completion,
            "wave_analysis": wave_analysis,
            "wave_optimization": wave_optimization,
            # Execution handlers
            "execution_initialization": execution_initialization,
            "execution_finalization": execution_finalization,
            "execution_error_handler": execution_error_handler,
            "migration_completion": migration_completion,
            "environment_preparation": environment_preparation,
            # Modernize handlers
            "modernize_initialization": modernize_initialization,
            "modernize_finalization": modernize_finalization,
            "modernize_error_handler": modernize_error_handler,
            "modernization_completion": modernization_completion,
            # FinOps handlers
            "finops_initialization": finops_initialization,
            "finops_finalization": finops_finalization,
            "finops_error_handler": finops_error_handler,
            "finops_completion": finops_completion,
            "cost_data_collection": cost_data_collection,
            # Observability handlers
            "observability_initialization": observability_initialization,
            "observability_finalization": observability_finalization,
            "observability_error_handler": observability_error_handler,
            "observability_completion": observability_completion,
            "monitoring_design": monitoring_design,
            # Decommission handlers
            "decommission_initialization": decommission_initialization,
            "decommission_finalization": decommission_finalization,
            "decommission_error_handler": decommission_error_handler,
            "decommission_completion": decommission_completion,
            "impact_analysis": impact_analysis,
            "final_backup": final_backup,
        }

        for name, handler in handlers.items():
            try:
                self.handler_registry.register_handler(name, handler)
                results["handlers_registered"].append(name)
            except Exception as e:
                logger.error(f"Failed to register handler {name}: {e}")
                results["errors"].append(f"Handler {name}: {str(e)}")

    def _register_all_flows(self, results: Dict[str, Any]) -> None:
        """Register all flow types with the flow registry"""
        flow_configs = [
            ("discovery", get_discovery_flow_config),
            ("assessment", get_assessment_flow_config),
            ("collection", get_collection_flow_config),
            ("planning", get_planning_flow_config),
            ("execution", get_execution_flow_config),
            ("modernize", get_modernize_flow_config),
            ("finops", get_finops_flow_config),
            ("observability", get_observability_flow_config),
            ("decommission", get_decommission_flow_config),
        ]

        for flow_name, config_getter in flow_configs:
            try:
                config = config_getter()
                self.flow_registry.register(config)
                results["flows_registered"].append(flow_name)
                logger.info(f"✅ Registered {flow_name} flow")
            except Exception as e:
                logger.error(f"Failed to register {flow_name} flow: {e}")
                results["errors"].append(f"Flow {flow_name}: {str(e)}")

    def verify_all_flows(self) -> Dict[str, Any]:
        """
        Verify all flow configurations
        MFO-058: Verify configuration consistency
        """
        verification_results = {
            "total_flows": len(self.flow_registry.list_flow_types()),
            "flow_details": {},
            "consistency_check": True,
            "issues": [],
        }

        expected_flows = [
            "discovery",
            "assessment",
            "collection",
            "planning",
            "execution",
            "modernize",
            "finops",
            "observability",
            "decommission",
        ]

        # Check all expected flows are registered
        registered_flows = self.flow_registry.list_flow_types()
        missing_flows = [f for f in expected_flows if f not in registered_flows]

        if missing_flows:
            verification_results["consistency_check"] = False
            verification_results["issues"].append(f"Missing flows: {missing_flows}")

        # Verify each flow configuration
        for flow_name in registered_flows:
            try:
                config = self.flow_registry.get_flow_config(flow_name)
                flow_info = {
                    "phases": len(config.phases),
                    "has_validators": any(phase.validators for phase in config.phases),
                    "has_handlers": bool(config.initialization_handler),
                    "capabilities": {
                        "pause_resume": config.capabilities.supports_pause_resume,
                        "rollback": config.capabilities.supports_rollback,
                        "checkpointing": config.capabilities.supports_checkpointing,
                    },
                }
                verification_results["flow_details"][flow_name] = flow_info

                # Check for configuration issues
                if len(config.phases) == 0:
                    verification_results["issues"].append(
                        f"{flow_name}: No phases defined"
                    )

                if not config.initialization_handler:
                    verification_results["issues"].append(
                        f"{flow_name}: No initialization handler"
                    )

            except Exception as e:
                verification_results["issues"].append(f"{flow_name}: {str(e)}")
                verification_results["consistency_check"] = False

        return verification_results

    def get_flow_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all registered flows"""
        summary = []

        for flow_name in self.flow_registry.list_flow_types():
            try:
                config = self.flow_registry.get_flow_config(flow_name)
                summary.append(
                    {
                        "name": flow_name,
                        "display_name": config.display_name,
                        "description": config.description,
                        "version": config.version,
                        "phase_count": len(config.phases),
                        "tags": config.tags,
                    }
                )
            except Exception as e:
                logger.error(f"Error getting summary for {flow_name}: {e}")

        return summary


# Global instance
flow_configuration_manager = FlowConfigurationManager()


# Convenience functions
def initialize_all_flows() -> Dict[str, Any]:
    """Initialize all flow configurations"""
    return flow_configuration_manager.initialize_all_flows()


def verify_flow_configurations() -> Dict[str, Any]:
    """Verify all flow configurations"""
    return flow_configuration_manager.verify_all_flows()


def get_flow_summary() -> List[Dict[str, Any]]:
    """Get summary of all registered flows"""
    return flow_configuration_manager.get_flow_summary()


# Export key items
__all__ = [
    "flow_configuration_manager",
    "initialize_all_flows",
    "verify_flow_configurations",
    "get_flow_summary",
    "get_discovery_flow_config",
    "get_assessment_flow_config",
    "get_collection_flow_config",
    "get_planning_flow_config",
    "get_execution_flow_config",
    "get_modernize_flow_config",
    "get_finops_flow_config",
    "get_observability_flow_config",
    "get_decommission_flow_config",
]
