"""
Flow Execution Engine Validators
Validation utilities for flow phase execution including pre and post validation.
"""

from typing import Any, Dict

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.services.validator_registry import ValidatorRegistry

logger = get_logger(__name__)


class ExecutionEngineValidators:
    """Validation handlers for flow execution engine."""

    def __init__(self, validator_registry: ValidatorRegistry, context: RequestContext):
        self.validator_registry = validator_registry
        self.context = context

    async def run_phase_validators(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_data: Dict[str, Any],
        validation_type: str,
    ) -> Dict[str, Any]:
        """Run validators for a specific phase"""
        validation_results = {"valid": True, "errors": [], "warnings": []}

        # Get validators for this phase and type
        validators = getattr(phase_config, f"{validation_type}_validators", [])

        for validator_name in validators:
            validator = self.validator_registry.get_validator(validator_name)
            if validator:
                try:
                    result = await validator(
                        flow_id=master_flow.flow_id,
                        phase_data=phase_data,
                        context=self.context,
                    )

                    # Handle ValidationResult dataclass or dict response
                    if hasattr(result, "valid"):
                        # ValidationResult dataclass - use attribute access
                        if not result.valid:
                            validation_results["valid"] = False
                            validation_results["errors"].extend(result.errors or [])

                        validation_results["warnings"].extend(result.warnings or [])
                    else:
                        # Legacy dict response - use dictionary access
                        if not result.get("valid", True):
                            validation_results["valid"] = False
                            validation_results["errors"].extend(
                                result.get("errors", [])
                            )

                        validation_results["warnings"].extend(
                            result.get("warnings", [])
                        )

                except Exception as e:
                    logger.warning(f"⚠️ Validator {validator_name} failed: {e}")
                    validation_results["warnings"].append(
                        f"Validator {validator_name} failed: {str(e)}"
                    )

        return validation_results
