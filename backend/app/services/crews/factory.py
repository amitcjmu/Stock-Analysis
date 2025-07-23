"""
Crew Factory for dynamic crew composition
"""

import logging
from typing import Any, Dict, List, Optional, Type

from app.services.crews.asset_inventory_crew import AssetInventoryCrew
from app.services.crews.base_crew import BaseDiscoveryCrew
from app.services.crews.data_cleansing_crew import DataCleansingCrew
from app.services.crews.field_mapping_crew import FieldMappingCrew

logger = logging.getLogger(__name__)


class CrewFactory:
    """
    Factory for creating and managing CrewAI crews.
    Provides:
    - Dynamic crew instantiation
    - Crew registry
    - Execution management
    """

    # Registry of available crews
    _crew_registry: Dict[str, Type[BaseDiscoveryCrew]] = {
        "field_mapping": FieldMappingCrew,
        "data_cleansing": DataCleansingCrew,
        "asset_inventory": AssetInventoryCrew,
    }

    @classmethod
    def register_crew(cls, name: str, crew_class: Type[BaseDiscoveryCrew]) -> None:
        """Register a new crew type"""
        cls._crew_registry[name] = crew_class
        logger.info(f"Registered crew: {name}")

    @classmethod
    def create_crew(cls, crew_type: str) -> Optional[BaseDiscoveryCrew]:
        """Create a crew instance by type"""
        crew_class = cls._crew_registry.get(crew_type)
        if not crew_class:
            logger.error(f"Unknown crew type: {crew_type}")
            return None

        try:
            crew = crew_class()
            logger.info(f"Created crew: {crew_type}")
            return crew
        except Exception as e:
            logger.error(f"Failed to create crew {crew_type}: {e}")
            return None

    @classmethod
    def execute_crew(cls, crew_type: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Create and execute a crew in one call"""
        crew = cls.create_crew(crew_type)
        if not crew:
            return {"status": "error", "error": f"Failed to create crew: {crew_type}"}

        try:
            return crew.execute(inputs)
        except Exception as e:
            logger.error(f"Crew execution failed: {e}")
            return {"status": "error", "error": str(e), "crew_type": crew_type}

    @classmethod
    def list_crews(cls) -> List[str]:
        """List all available crew types"""
        return list(cls._crew_registry.keys())

    @classmethod
    def get_crew_info(cls, crew_type: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific crew type"""
        crew_class = cls._crew_registry.get(crew_type)
        if not crew_class:
            return None

        try:
            # Create temporary instance to get info
            temp_crew = crew_class()
            return {
                "name": temp_crew.name,
                "description": temp_crew.description,
                "process": str(temp_crew.process),
                "crew_type": crew_type,
            }
        except Exception as e:
            logger.warning(f"Could not get info for crew {crew_type}: {e}")
            return {
                "name": crew_type,
                "description": "Information unavailable",
                "error": str(e),
            }

    @classmethod
    def validate_crew_inputs(
        cls, crew_type: str, inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate inputs for a specific crew type"""
        validation_result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "required_fields": [],
        }

        if crew_type == "field_mapping":
            # Validate field mapping inputs
            required_fields = ["raw_data"]

            validation_result["required_fields"] = required_fields

            # Check required fields
            for field in required_fields:
                if field not in inputs or not inputs[field]:
                    validation_result["errors"].append(
                        f"Missing required field: {field}"
                    )

            # Check data format
            if "raw_data" in inputs:
                raw_data = inputs["raw_data"]
                if not isinstance(raw_data, list):
                    validation_result["errors"].append("raw_data must be a list")
                elif len(raw_data) == 0:
                    validation_result["errors"].append("raw_data cannot be empty")
                elif not isinstance(raw_data[0], dict):
                    validation_result["errors"].append(
                        "raw_data must contain dictionary objects"
                    )

            # Check optional fields
            if "source_schema" in inputs and not isinstance(
                inputs["source_schema"], dict
            ):
                validation_result["warnings"].append(
                    "source_schema should be a dictionary"
                )

            if "target_fields" in inputs and not isinstance(
                inputs["target_fields"], list
            ):
                validation_result["warnings"].append("target_fields should be a list")

        elif crew_type == "data_cleansing":
            # Validate data cleansing inputs
            required_fields = ["raw_data"]

            validation_result["required_fields"] = required_fields

            # Check required fields
            for field in required_fields:
                if field not in inputs or not inputs[field]:
                    validation_result["errors"].append(
                        f"Missing required field: {field}"
                    )

            # Check data format
            if "raw_data" in inputs:
                raw_data = inputs["raw_data"]
                if not isinstance(raw_data, list):
                    validation_result["errors"].append("raw_data must be a list")
                elif len(raw_data) == 0:
                    validation_result["errors"].append("raw_data cannot be empty")

        elif crew_type == "asset_inventory":
            # Validate asset inventory inputs
            required_fields = ["raw_data"]

            validation_result["required_fields"] = required_fields

            # Check required fields
            for field in required_fields:
                if field not in inputs or not inputs[field]:
                    validation_result["errors"].append(
                        f"Missing required field: {field}"
                    )

            # Check data format
            if "raw_data" in inputs:
                raw_data = inputs["raw_data"]
                if not isinstance(raw_data, list):
                    validation_result["errors"].append("raw_data must be a list")
                elif len(raw_data) == 0:
                    validation_result["errors"].append("raw_data cannot be empty")

        else:
            validation_result["errors"].append(f"Unknown crew type: {crew_type}")

        validation_result["valid"] = len(validation_result["errors"]) == 0
        return validation_result


# Global crew factory instance
crew_factory = CrewFactory()
