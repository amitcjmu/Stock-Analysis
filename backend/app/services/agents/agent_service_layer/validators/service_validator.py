"""
Service validator for agent service layer validation operations.
"""

import logging
from typing import Any, Dict

from app.core.context import RequestContext

logger = logging.getLogger(__name__)


class ServiceValidator:
    """Handles validation operations for the agent service layer."""

    def __init__(self, context: RequestContext):
        self.context = context

    def validate_flow_id(self, flow_id: str) -> Dict[str, Any]:
        """Validate flow ID format and structure"""
        validation_result = {"is_valid": True, "issues": [], "recommendations": []}

        if not flow_id:
            validation_result["is_valid"] = False
            validation_result["issues"].append("Flow ID is empty or None")
            validation_result["recommendations"].append("Provide a valid flow ID")
            return validation_result

        if not isinstance(flow_id, str):
            validation_result["is_valid"] = False
            validation_result["issues"].append("Flow ID must be a string")
            validation_result["recommendations"].append(
                "Convert flow ID to string format"
            )
            return validation_result

        if len(flow_id.strip()) == 0:
            validation_result["is_valid"] = False
            validation_result["issues"].append("Flow ID cannot be whitespace only")
            validation_result["recommendations"].append("Provide a non-empty flow ID")
            return validation_result

        if len(flow_id) > 255:
            validation_result["is_valid"] = False
            validation_result["issues"].append(
                "Flow ID exceeds maximum length of 255 characters"
            )
            validation_result["recommendations"].append("Use a shorter flow ID")

        return validation_result

    def validate_asset_id(self, asset_id: str) -> Dict[str, Any]:
        """Validate asset ID format and structure"""
        validation_result = {"is_valid": True, "issues": [], "recommendations": []}

        if not asset_id:
            validation_result["is_valid"] = False
            validation_result["issues"].append("Asset ID is empty or None")
            validation_result["recommendations"].append("Provide a valid asset ID")
            return validation_result

        if not isinstance(asset_id, str):
            validation_result["is_valid"] = False
            validation_result["issues"].append("Asset ID must be a string")
            validation_result["recommendations"].append(
                "Convert asset ID to string format"
            )
            return validation_result

        # Try to validate as UUID format
        try:
            import uuid

            uuid.UUID(asset_id)
        except ValueError:
            validation_result["is_valid"] = False
            validation_result["issues"].append("Asset ID is not a valid UUID format")
            validation_result["recommendations"].append(
                "Ensure asset ID is in UUID format"
            )

        return validation_result

    def validate_phase_name(self, phase: str) -> Dict[str, Any]:
        """Validate discovery phase name"""
        validation_result = {"is_valid": True, "issues": [], "recommendations": []}

        valid_phases = [
            "data_import",
            "attribute_mapping",
            "data_cleansing",
            "inventory",
            "dependencies",
            "tech_debt",
        ]

        if not phase:
            validation_result["is_valid"] = False
            validation_result["issues"].append("Phase name is empty or None")
            validation_result["recommendations"].append("Provide a valid phase name")
            return validation_result

        if phase not in valid_phases:
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"Invalid phase name: {phase}")
            validation_result["recommendations"].append(
                f"Use one of: {', '.join(valid_phases)}"
            )

        return validation_result

    def validate_asset_type(self, asset_type: str) -> Dict[str, Any]:
        """Validate asset type"""
        validation_result = {"is_valid": True, "issues": [], "recommendations": []}

        valid_asset_types = [
            "server",
            "database",
            "application",
            "network",
            "storage",
            "middleware",
            "service",
            "infrastructure",
            "security",
            "unknown",
        ]

        if not asset_type:
            validation_result["is_valid"] = False
            validation_result["issues"].append("Asset type is empty or None")
            validation_result["recommendations"].append("Provide a valid asset type")
            return validation_result

        if asset_type.lower() not in [t.lower() for t in valid_asset_types]:
            # Allow unknown types but issue a warning
            validation_result["issues"].append(f"Uncommon asset type: {asset_type}")
            validation_result["recommendations"].append(
                f"Consider using standard types: {', '.join(valid_asset_types)}"
            )

        return validation_result

    def validate_mappings_structure(self, mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate field mappings structure"""
        validation_result = {
            "is_valid": True,
            "issues": [],
            "recommendations": [],
            "field_validations": {},
        }

        if not isinstance(mappings, dict):
            validation_result["is_valid"] = False
            validation_result["issues"].append("Mappings must be a dictionary")
            validation_result["recommendations"].append(
                "Provide mappings as a dictionary"
            )
            return validation_result

        if len(mappings) == 0:
            validation_result["is_valid"] = False
            validation_result["issues"].append("Mappings dictionary is empty")
            validation_result["recommendations"].append(
                "Provide at least one field mapping"
            )
            return validation_result

        # Validate each mapping
        for source_field, mapping_config in mappings.items():
            field_validation = self._validate_single_mapping(
                source_field, mapping_config
            )
            validation_result["field_validations"][source_field] = field_validation

            if not field_validation["is_valid"]:
                validation_result["is_valid"] = False
                validation_result["issues"].extend(
                    [f"{source_field}: {issue}" for issue in field_validation["issues"]]
                )
                validation_result["recommendations"].extend(
                    [
                        f"{source_field}: {rec}"
                        for rec in field_validation["recommendations"]
                    ]
                )

        return validation_result

    def validate_context(self) -> Dict[str, Any]:
        """Validate request context"""
        validation_result = {"is_valid": True, "issues": [], "recommendations": []}

        # Validate client account ID
        if not self.context.client_account_id:
            validation_result["is_valid"] = False
            validation_result["issues"].append("Client account ID is missing")
            validation_result["recommendations"].append(
                "Provide a valid client account ID"
            )

        # Validate engagement ID
        if not self.context.engagement_id:
            validation_result["is_valid"] = False
            validation_result["issues"].append("Engagement ID is missing")
            validation_result["recommendations"].append("Provide a valid engagement ID")

        # Validate user ID (optional but recommended)
        if not self.context.user_id:
            validation_result["issues"].append("User ID is missing (optional)")
            validation_result["recommendations"].append(
                "Consider providing user ID for audit trail"
            )

        return validation_result

    def validate_service_call_params(
        self, method_name: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate parameters for a service call"""
        validation_result = {
            "is_valid": True,
            "issues": [],
            "recommendations": [],
            "param_validations": {},
        }

        # Method-specific parameter validation
        if method_name == "get_flow_status":
            if "flow_id" not in params:
                validation_result["is_valid"] = False
                validation_result["issues"].append(
                    "Missing required parameter: flow_id"
                )
            else:
                flow_validation = self.validate_flow_id(params["flow_id"])
                validation_result["param_validations"]["flow_id"] = flow_validation
                if not flow_validation["is_valid"]:
                    validation_result["is_valid"] = False
                    validation_result["issues"].extend(flow_validation["issues"])

        elif method_name == "validate_asset_data":
            if "asset_id" not in params:
                validation_result["is_valid"] = False
                validation_result["issues"].append(
                    "Missing required parameter: asset_id"
                )
            else:
                asset_validation = self.validate_asset_id(params["asset_id"])
                validation_result["param_validations"]["asset_id"] = asset_validation
                if not asset_validation["is_valid"]:
                    validation_result["is_valid"] = False
                    validation_result["issues"].extend(asset_validation["issues"])

        elif method_name == "validate_phase_completion":
            required_params = ["flow_id", "phase"]
            for param in required_params:
                if param not in params:
                    validation_result["is_valid"] = False
                    validation_result["issues"].append(
                        f"Missing required parameter: {param}"
                    )

            if "flow_id" in params:
                flow_validation = self.validate_flow_id(params["flow_id"])
                validation_result["param_validations"]["flow_id"] = flow_validation
                if not flow_validation["is_valid"]:
                    validation_result["is_valid"] = False
                    validation_result["issues"].extend(flow_validation["issues"])

            if "phase" in params:
                phase_validation = self.validate_phase_name(params["phase"])
                validation_result["param_validations"]["phase"] = phase_validation
                if not phase_validation["is_valid"]:
                    validation_result["is_valid"] = False
                    validation_result["issues"].extend(phase_validation["issues"])

        return validation_result

    def validate_response_data(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate response data structure"""
        validation_result = {"is_valid": True, "issues": [], "recommendations": []}

        # Check for required response structure
        if not isinstance(response, dict):
            validation_result["is_valid"] = False
            validation_result["issues"].append("Response must be a dictionary")
            return validation_result

        # Check for status field
        if "status" not in response:
            validation_result["issues"].append("Response missing status field")
            validation_result["recommendations"].append(
                "Include status field in response"
            )

        # Validate status values
        valid_statuses = ["success", "error", "not_found", "invalid"]
        if "status" in response and response["status"] not in valid_statuses:
            validation_result["issues"].append(
                f"Invalid status value: {response['status']}"
            )
            validation_result["recommendations"].append(
                f"Use one of: {', '.join(valid_statuses)}"
            )

        # Check error responses
        if response.get("status") == "error":
            if "error" not in response:
                validation_result["issues"].append("Error response missing error field")
                validation_result["recommendations"].append(
                    "Include error field in error responses"
                )

        return validation_result

    def _validate_single_mapping(
        self, source_field: str, mapping_config: Any
    ) -> Dict[str, Any]:
        """Validate a single field mapping"""
        validation_result = {"is_valid": True, "issues": [], "recommendations": []}

        if not isinstance(mapping_config, dict):
            validation_result["is_valid"] = False
            validation_result["issues"].append(
                "Mapping configuration must be a dictionary"
            )
            validation_result["recommendations"].append(
                "Provide mapping as dictionary with target_field and data_type"
            )
            return validation_result

        # Check required fields
        required_fields = ["target_field", "data_type"]
        for field in required_fields:
            if field not in mapping_config:
                validation_result["is_valid"] = False
                validation_result["issues"].append(f"Missing required field: {field}")
                validation_result["recommendations"].append(
                    f"Add {field} to mapping configuration"
                )

        # Validate data types
        if "data_type" in mapping_config:
            valid_data_types = [
                "string",
                "integer",
                "float",
                "boolean",
                "date",
                "datetime",
                "json",
            ]
            data_type = mapping_config["data_type"]
            if data_type not in valid_data_types:
                validation_result["issues"].append(f"Unknown data type: {data_type}")
                validation_result["recommendations"].append(
                    f"Use one of: {', '.join(valid_data_types)}"
                )

        # Validate target field name
        if "target_field" in mapping_config:
            target_field = mapping_config["target_field"]
            if not target_field or not isinstance(target_field, str):
                validation_result["is_valid"] = False
                validation_result["issues"].append(
                    "Target field must be a non-empty string"
                )
                validation_result["recommendations"].append(
                    "Provide a valid target field name"
                )

        return validation_result
