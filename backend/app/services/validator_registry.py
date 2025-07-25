"""
Validator Registry

Registry for phase-specific validators across all flow types.
Provides a centralized system for registering and executing validation logic.
"""

import inspect
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels"""

    ERROR = "error"  # Blocks execution
    WARNING = "warning"  # Allows execution but logs warning
    INFO = "info"  # Informational only


@dataclass
class ValidationResult:
    """Result of a validation check"""

    valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    info: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        self.errors = self.errors or []
        self.warnings = self.warnings or []
        self.info = self.info or []
        self.metadata = self.metadata or {}


# Type alias for validator functions
ValidatorFunc = Callable[
    [Dict[str, Any], Dict[str, Any], Optional[Dict[str, Any]]],
    Awaitable[ValidationResult],
]


class ValidatorRegistry:
    """
    Registry for phase-specific validators.
    Validators can be registered globally or for specific flow types and phases.
    """

    def __init__(self):
        # Global validators (apply to all flows)
        self._global_validators: Dict[str, ValidatorFunc] = {}

        # Flow-type specific validators
        self._flow_validators: Dict[str, Dict[str, ValidatorFunc]] = {}

        # Phase-specific validators
        self._phase_validators: Dict[str, Dict[str, Dict[str, ValidatorFunc]]] = {}

        # Built-in validators
        self._register_builtin_validators()

        logger.info("✅ Validator Registry initialized")

    def register_validator(
        self,
        name: str,
        validator: ValidatorFunc,
        flow_type: Optional[str] = None,
        phase: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        Register a validator function

        Args:
            name: Unique name for the validator
            validator: Async function that performs validation
            flow_type: Optional flow type to restrict validator to
            phase: Optional phase to restrict validator to (requires flow_type)
            description: Optional description of what the validator checks

        Raises:
            ValueError: If validator is invalid or name already exists
        """
        # Validate the validator function
        if not callable(validator):
            raise ValueError("Validator must be callable")

        if not inspect.iscoroutinefunction(validator):
            raise ValueError("Validator must be async function")

        # Register based on scope
        if flow_type and phase:
            # Phase-specific validator
            if flow_type not in self._phase_validators:
                self._phase_validators[flow_type] = {}
            if phase not in self._phase_validators[flow_type]:
                self._phase_validators[flow_type][phase] = {}

            if name in self._phase_validators[flow_type][phase]:
                raise ValueError(
                    f"Phase validator '{name}' already exists for {flow_type}.{phase}"
                )

            self._phase_validators[flow_type][phase][name] = validator
            logger.info(f"✅ Registered phase validator: {name} for {flow_type}.{phase}")

        elif flow_type:
            # Flow-type specific validator
            if flow_type not in self._flow_validators:
                self._flow_validators[flow_type] = {}

            if name in self._flow_validators[flow_type]:
                raise ValueError(
                    f"Flow validator '{name}' already exists for {flow_type}"
                )

            self._flow_validators[flow_type][name] = validator
            logger.info(f"✅ Registered flow validator: {name} for {flow_type}")

        else:
            # Global validator
            if name in self._global_validators:
                raise ValueError(f"Global validator '{name}' already exists")

            self._global_validators[name] = validator
            logger.info(f"✅ Registered global validator: {name}")

    def get_validator(
        self, name: str, flow_type: Optional[str] = None, phase: Optional[str] = None
    ) -> Optional[ValidatorFunc]:
        """
        Get a validator by name

        Args:
            name: Validator name
            flow_type: Optional flow type for scoped lookup
            phase: Optional phase for scoped lookup

        Returns:
            Validator function if found, None otherwise
        """
        # Check phase-specific first (most specific)
        if flow_type and phase:
            phase_validators = self._phase_validators.get(flow_type, {}).get(phase, {})
            if name in phase_validators:
                return phase_validators[name]

        # Check flow-type specific
        if flow_type:
            flow_validators = self._flow_validators.get(flow_type, {})
            if name in flow_validators:
                return flow_validators[name]

        # Check global validators
        return self._global_validators.get(name)

    async def validate(
        self,
        validator_names: List[str],
        phase_input: Dict[str, Any],
        flow_state: Dict[str, Any],
        overrides: Optional[Dict[str, Any]] = None,
        flow_type: Optional[str] = None,
        phase: Optional[str] = None,
    ) -> ValidationResult:
        """
        Run multiple validators and aggregate results

        Args:
            validator_names: List of validator names to run
            phase_input: Input data for the phase
            flow_state: Current flow state
            overrides: Optional validation overrides
            flow_type: Optional flow type for scoped validators
            phase: Optional phase for scoped validators

        Returns:
            Aggregated validation result
        """
        all_errors = []
        all_warnings = []
        all_info = []
        metadata = {}

        for validator_name in validator_names:
            validator = self.get_validator(validator_name, flow_type, phase)

            if not validator:
                logger.warning(f"Validator '{validator_name}' not found")
                all_warnings.append(f"Validator '{validator_name}' not found")
                continue

            try:
                result = await validator(phase_input, flow_state, overrides)

                all_errors.extend(result.errors)
                all_warnings.extend(result.warnings)
                all_info.extend(result.info)

                if result.metadata:
                    metadata.update(result.metadata)

            except Exception as e:
                logger.error(f"Validator '{validator_name}' failed: {e}")
                all_errors.append(f"Validator '{validator_name}' failed: {str(e)}")

        return ValidationResult(
            valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            info=all_info,
            metadata=metadata,
        )

    def list_validators(
        self, flow_type: Optional[str] = None, phase: Optional[str] = None
    ) -> List[str]:
        """
        List available validators

        Args:
            flow_type: Optional flow type filter
            phase: Optional phase filter

        Returns:
            List of validator names
        """
        validators = set()

        # Add global validators
        validators.update(self._global_validators.keys())

        # Add flow-type validators if specified
        if flow_type:
            validators.update(self._flow_validators.get(flow_type, {}).keys())

            # Add phase validators if specified
            if phase:
                validators.update(
                    self._phase_validators.get(flow_type, {}).get(phase, {}).keys()
                )

        return sorted(list(validators))

    def _register_builtin_validators(self):
        """Register built-in validators"""

        # Required fields validator
        async def required_fields_validator(
            phase_input: Dict[str, Any],
            flow_state: Dict[str, Any],
            overrides: Optional[Dict[str, Any]],
        ) -> ValidationResult:
            """Validate that required fields are present"""
            errors = []

            # This is a generic implementation
            # Specific flows would override with their requirements
            if not phase_input:
                errors.append("Phase input cannot be empty")

            return ValidationResult(valid=len(errors) == 0, errors=errors)

        self.register_validator(
            "required_fields",
            required_fields_validator,
            description="Validates required fields are present",
        )

        # File exists validator
        async def file_exists_validator(
            phase_input: Dict[str, Any],
            flow_state: Dict[str, Any],
            overrides: Optional[Dict[str, Any]],
        ) -> ValidationResult:
            """Validate that referenced files exist"""
            errors = []
            warnings = []

            file_fields = ["import_file_id", "file_path", "data_file"]

            for field in file_fields:
                if field in phase_input:
                    file_ref = phase_input[field]
                    # In real implementation, check if file exists
                    # For now, just validate it's not empty
                    if not file_ref:
                        errors.append(f"{field} cannot be empty")

            return ValidationResult(
                valid=len(errors) == 0, errors=errors, warnings=warnings
            )

        self.register_validator(
            "file_exists",
            file_exists_validator,
            description="Validates that referenced files exist",
        )

        # Data format validator
        async def file_format_valid_validator(
            phase_input: Dict[str, Any],
            flow_state: Dict[str, Any],
            overrides: Optional[Dict[str, Any]],
        ) -> ValidationResult:
            """Validate file format is supported"""
            errors = []
            info = []

            supported_formats = [".csv", ".json", ".xml", ".xlsx", ".parquet"]

            if "file_path" in phase_input:
                file_path = phase_input["file_path"]
                if file_path:
                    ext = file_path.lower().split(".")[-1] if "." in file_path else ""
                    if f".{ext}" not in supported_formats:
                        errors.append(
                            f"Unsupported file format: .{ext}. "
                            f"Supported formats: {', '.join(supported_formats)}"
                        )
                    else:
                        info.append(f"File format validated: .{ext}")

            return ValidationResult(valid=len(errors) == 0, errors=errors, info=info)

        self.register_validator(
            "file_format_valid",
            file_format_valid_validator,
            description="Validates file format is supported",
        )

        # Mappings complete validator
        async def mappings_complete_validator(
            phase_input: Dict[str, Any],
            flow_state: Dict[str, Any],
            overrides: Optional[Dict[str, Any]],
        ) -> ValidationResult:
            """Validate that field mappings are complete"""
            errors = []
            warnings = []

            if "mappings" not in phase_input:
                errors.append("Field mappings are required")
            else:
                mappings = phase_input["mappings"]
                if not isinstance(mappings, dict):
                    errors.append("Mappings must be a dictionary")
                elif len(mappings) == 0:
                    errors.append("At least one field mapping is required")
                else:
                    # Check for empty mappings
                    empty_mappings = [k for k, v in mappings.items() if not v]
                    if empty_mappings:
                        warnings.append(
                            f"Empty mappings found for fields: {', '.join(empty_mappings)}"
                        )

            return ValidationResult(
                valid=len(errors) == 0, errors=errors, warnings=warnings
            )

        self.register_validator(
            "mappings_complete",
            mappings_complete_validator,
            description="Validates field mappings are complete",
        )

        # Applications exist validator
        async def applications_exist_validator(
            phase_input: Dict[str, Any],
            flow_state: Dict[str, Any],
            overrides: Optional[Dict[str, Any]],
        ) -> ValidationResult:
            """Validate that referenced applications exist"""
            errors = []

            if "application_ids" not in phase_input:
                errors.append("Application IDs are required")
            else:
                app_ids = phase_input["application_ids"]
                if not isinstance(app_ids, list):
                    errors.append("Application IDs must be a list")
                elif len(app_ids) == 0:
                    errors.append("At least one application ID is required")
                else:
                    # In real implementation, verify apps exist in database
                    # For now, just validate format
                    for app_id in app_ids:
                        if not app_id or not isinstance(app_id, str):
                            errors.append(f"Invalid application ID: {app_id}")

            return ValidationResult(valid=len(errors) == 0, errors=errors)

        self.register_validator(
            "applications_exist",
            applications_exist_validator,
            description="Validates referenced applications exist",
        )

        # Size limit validator
        async def size_limit_validator(
            phase_input: Dict[str, Any],
            flow_state: Dict[str, Any],
            overrides: Optional[Dict[str, Any]],
        ) -> ValidationResult:
            """Validate data size limits"""
            warnings = []
            info = []

            # Check various size limits
            max_records = (
                overrides.get("max_records", 1000000) if overrides else 1000000
            )

            if "record_count" in phase_input:
                count = phase_input["record_count"]
                if count > max_records:
                    warnings.append(
                        f"Record count ({count}) exceeds recommended limit ({max_records})"
                    )
                else:
                    info.append(f"Record count validated: {count}")

            return ValidationResult(
                valid=True,  # Size limits are warnings, not errors
                warnings=warnings,
                info=info,
            )

        self.register_validator(
            "size_limit", size_limit_validator, description="Validates data size limits"
        )

        logger.info("✅ Registered 6 built-in validators")


# Global validator registry instance
validator_registry = ValidatorRegistry()
