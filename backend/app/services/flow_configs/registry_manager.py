"""
Flow Configuration Registry Manager
Manages registration and initialization of all flow types
"""

import logging
from typing import Any, Dict, List

from .registry_handlers import register_all_handlers
from .registry_validators import register_all_validators

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
            register_all_validators(self.validator_registry, results)

            # Register all handlers
            register_all_handlers(self.handler_registry, results)

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

    def _register_all_flows(self, results: Dict[str, Any]) -> None:
        """Register all flow types with the flow registry"""
        from .assessment_flow_config import get_assessment_flow_config
        from .collection_flow_config import get_collection_flow_config
        from .decommission_flow_config import get_decommission_flow_config
        from .discovery_flow_config import get_discovery_flow_config
        from .execution_flow_config import get_execution_flow_config
        from .finops_flow_config import get_finops_flow_config
        from .modernize_flow_config import get_modernize_flow_config
        from .observability_flow_config import get_observability_flow_config
        from .planning_flow_config import get_planning_flow_config

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
        ]  # 9 total flows

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
