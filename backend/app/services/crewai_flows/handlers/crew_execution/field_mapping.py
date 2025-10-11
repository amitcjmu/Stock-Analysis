"""
Field Mapping Crew Execution Handler
"""

import logging
import os
from typing import Any, Dict, List

from .base import CrewExecutionBase
from .fallbacks import CrewFallbackHandler
from .parsers import CrewResultParser

logger = logging.getLogger(__name__)


class FieldMappingExecutor(CrewExecutionBase):
    """Handles execution of Field Mapping Crew"""

    def __init__(self, crewai_service):
        super().__init__(crewai_service)
        self.parser = CrewResultParser()
        self.fallback_handler = CrewFallbackHandler()

    def execute_field_mapping_crew(self, state, crewai_service) -> Dict[str, Any]:
        """Execute Field Mapping Crew with enhanced CrewAI features"""
        try:
            # TEMPORARY: Check if we should bypass crew execution to avoid rate limits
            bypass_crew = (
                os.getenv("BYPASS_CREWAI_FOR_FIELD_MAPPING", "false").lower() == "true"
            )

            if bypass_crew:
                logger.warning(
                    "⚠️ BYPASS_CREWAI_FOR_FIELD_MAPPING is enabled, using simple field mapper"
                )
                from app.services.crewai_flows.crews.simple_field_mapper import (
                    get_simple_field_mappings,
                )

                field_mapping_result = get_simple_field_mappings(state.raw_data)
                field_mappings = field_mapping_result.get("mappings", {})

                crew_status = self.create_crew_status(
                    status="completed",
                    manager="Simple Field Mapper (No LLM)",
                    agents=["Rule-based mapper"],
                    success_criteria_met=True,
                    additional_fields={
                        "validation_results": {
                            "phase": "field_mapping",
                            "criteria_checked": True,
                        },
                        "process_type": "rule-based",
                        "collaboration_enabled": False,
                    },
                )

                return {"field_mappings": field_mappings, "crew_status": crew_status}

            # Execute field mapping using PERSISTENT agent wrapper (Phase B1 - Nov 2025)
            try:
                from app.services.persistent_agents.field_mapping_persistent import (
                    execute_field_mapping,
                )

                # Pass shared memory and knowledge base if available
                shared_memory = getattr(state, "shared_memory_reference", None)

                # Execute via persistent wrapper (no crew creation needed)
                crew_result = await execute_field_mapping(
                    context=None,  # Will be extracted from state
                    service_registry=None,  # Will use crewai_service
                    data={"raw_data": state.raw_data, "shared_memory": shared_memory},
                )

                # Parse crew results and extract field mappings
                field_mappings = self.parser.parse_field_mapping_results(
                    crew_result, state.raw_data
                )

                logger.info(
                    "✅ Enhanced Field Mapping Crew executed successfully with CrewAI features"
                )

            except Exception as crew_error:
                error_info = self.handle_crew_error(crew_error, "Field Mapping")

                if error_info["is_rate_limit"]:
                    logger.warning(
                        "⚠️ Rate limit detected, using simple field mapper instead"
                    )

                    # Use simple field mapper that doesn't use LLMs
                    from app.services.crewai_flows.crews.simple_field_mapper import (
                        get_simple_field_mappings,
                    )

                    field_mapping_result = get_simple_field_mappings(state.raw_data)
                    field_mappings = field_mapping_result.get("mappings", {})

                    logger.info(
                        f"✅ Simple field mapping completed: {len(field_mappings)} fields mapped"
                    )
                else:
                    # Not a rate limit error, re-raise
                    raise crew_error

            # Validate success criteria
            success_criteria_met = self._validate_field_mapping_success(
                field_mappings, state.raw_data
            )

            crew_status = self.create_crew_status(
                status="completed",
                manager="Field Mapping Manager",
                agents=["Schema Analysis Expert", "Attribute Mapping Specialist"],
                success_criteria_met=success_criteria_met,
                additional_fields={
                    "validation_results": {
                        "phase": "field_mapping",
                        "criteria_checked": True,
                    }
                },
            )

            return {"field_mappings": field_mappings, "crew_status": crew_status}

        except Exception as e:
            logger.error(f"Field Mapping Crew execution failed: {e}")
            raise

    def _validate_field_mapping_success(
        self, field_mappings: Dict[str, Any], raw_data: List[Dict[str, Any]]
    ) -> bool:
        """Validate if field mapping was successful"""
        if not field_mappings or not raw_data:
            return False

        mapped_count = len(field_mappings.get("mappings", {}))

        # Calculate total fields from multiple records for robustness
        total_fields = 0
        if raw_data:
            field_set = set()
            sample_size = min(5, len(raw_data))

            for i in range(sample_size):
                if isinstance(raw_data[i], dict):
                    for key in raw_data[i].keys():
                        if key is not None and str(key).strip():
                            field_set.add(str(key).strip())

            total_fields = len(field_set)

        # Consider successful if at least 50% of fields are mapped
        success_threshold = 0.5
        mapping_ratio = mapped_count / total_fields if total_fields > 0 else 0

        return mapping_ratio >= success_threshold
