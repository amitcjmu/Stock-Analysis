"""
Mapping Strategies for Field Mapping Generator

Contains different strategies for generating field mappings.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from typing import Any, Dict

from .base import FieldMappingGeneratorBase

# Import persistent field mapping to use actual AI agent
# Per ADR-015, ADR-024: Use new persistent agent wrapper
try:
    from app.services.persistent_agents.field_mapping_persistent import (
        execute_field_mapping,
    )

    PERSISTENT_FIELD_MAPPING_AVAILABLE = True
except ImportError:
    PERSISTENT_FIELD_MAPPING_AVAILABLE = False

logger = logging.getLogger(__name__)


class FieldMappingStrategies(FieldMappingGeneratorBase):
    """Implements different strategies for field mapping generation"""

    async def try_direct_crew_execution(
        self, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Try direct crew execution for field mapping using actual persistent AI agent"""
        try:
            self.logger.info(
                "🚀 Attempting direct crew execution for field mapping using persistent agent"
            )

            # Debug logging
            self.logger.info(
                f"📊 PERSISTENT_FIELD_MAPPING_AVAILABLE: {PERSISTENT_FIELD_MAPPING_AVAILABLE}"
            )
            self.logger.info(f"📊 Flow has context: {hasattr(self.flow, 'context')}")
            if hasattr(self.flow, "context"):
                context = self.flow.context
                self.logger.info(f"📊 Context type: {type(context)}")
                self.logger.info(
                    f"📊 Context has client_account_id: {hasattr(context, 'client_account_id')}"
                )
                self.logger.info(
                    f"📊 Context client_account_id: {getattr(context, 'client_account_id', 'None')}"
                )
                self.logger.info(
                    f"📊 Context has engagement_id: {hasattr(context, 'engagement_id')}"
                )
                self.logger.info(
                    f"📊 Context engagement_id: {getattr(context, 'engagement_id', 'None')}"
                )

            # Use actual persistent AI agent if available
            if PERSISTENT_FIELD_MAPPING_AVAILABLE and hasattr(self.flow, "context"):
                try:
                    self.logger.info("✅ Conditions met for persistent agent execution")
                    return await self._use_persistent_field_mapping_agent(input_data)
                except Exception as e:
                    self.logger.error(
                        f"❌ Persistent agent execution failed: {e}", exc_info=True
                    )
                    # Fall through to fallback logic
            else:
                self.logger.warning(
                    f"⚠️ Conditions not met for persistent agent - "
                    f"PERSISTENT_FIELD_MAPPING_AVAILABLE={PERSISTENT_FIELD_MAPPING_AVAILABLE}, "
                    f"has context={hasattr(self.flow, 'context')}"
                )

            # Fallback: Use basic field mapping logic
            field_mappings = []

            # Extract field information from input data
            field_analysis = input_data.get("field_analysis", {})

            # BUG FIX: If field_analysis is empty, try to generate from validated_data
            if not field_analysis:
                field_mappings = self._generate_mappings_from_validated_data(
                    input_data, "crew_generated_from_validated_data"
                )
                if not field_mappings:
                    self.logger.warning(
                        "⚠️ No field analysis or validated_data available for crew execution"
                    )
                    return {}
            else:
                # Standard processing with field_analysis
                for field_name, analysis in field_analysis.items():
                    # Create basic mapping based on field analysis
                    mapping = {
                        "source_field": field_name,
                        "target_field": self._suggest_target_field(
                            field_name, analysis
                        ),
                        "confidence": 0.7,
                        "mapping_type": "crew_generated_fallback",
                        "status": "suggested",
                    }
                    field_mappings.append(mapping)

            if field_mappings:
                result = {
                    "field_mappings": field_mappings,
                    "suggestions": [],
                    "execution_method": "direct_crew_execution_fallback",
                    "status": "success",
                }

                self.logger.info(
                    f"✅ Direct crew execution fallback generated {len(field_mappings)} mappings"
                )
                return result

        except Exception as e:
            self.logger.error(f"❌ Direct crew execution failed: {e}")

        return {}

    async def try_basic_field_extraction(
        self, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Try basic field extraction as fallback"""
        try:
            self.logger.info("📊 Attempting basic field extraction")

            field_analysis = input_data.get("field_analysis", {})
            basic_mappings = []

            # BUG FIX: If field_analysis is empty, try to generate from validated_data
            if not field_analysis:
                basic_mappings = self._generate_mappings_from_validated_data(
                    input_data, "basic_extraction_from_validated_data", confidence=0.5
                )
                if not basic_mappings:
                    self.logger.warning(
                        "⚠️ No field analysis or validated_data available for basic extraction"
                    )
                    return {}
            else:
                # Standard processing with field_analysis
                for field_name, analysis in field_analysis.items():
                    # Create basic mapping
                    mapping = {
                        "source_field": field_name,
                        "target_field": self._map_common_field_names(field_name),
                        "confidence": 0.5,
                        "mapping_type": "basic_extraction",
                        "status": "suggested",
                    }
                    basic_mappings.append(mapping)

            if basic_mappings:
                result = {
                    "field_mappings": basic_mappings,
                    "suggestions": [],
                    "execution_method": "basic_field_extraction",
                    "status": "success",
                }

                self.logger.info(
                    f"Basic field extraction completed with {len(basic_mappings)} fields"
                )
                return result

        except Exception as e:
            self.logger.error(f"❌ Basic field extraction failed: {e}")

        return {}

    async def try_minimal_fallback(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide minimal fallback when all else fails"""
        try:
            self.logger.info("🔄 Using minimal fallback approach")

            return {
                "field_mappings": [],
                "suggestions": [],
                "status": "fallback",
                "message": "Minimal fallback - proceeding with empty field mappings",
                "execution_method": "minimal_fallback",
            }

        except Exception as e:
            self.logger.error(f"❌ Minimal fallback failed: {e}")
            return {}

    def _generate_mappings_from_validated_data(
        self, input_data: Dict[str, Any], mapping_type: str, confidence: float = 0.7
    ) -> list:
        """Generate field mappings from validated_data when field_analysis is empty"""
        mappings = []

        try:
            validated_data = input_data.get("validated_data", [])
            if (
                validated_data
                and isinstance(validated_data, list)
                and len(validated_data) > 0
            ):
                sample_record = validated_data[0]
                if isinstance(sample_record, dict):
                    self.logger.info(
                        f"🔄 Generating {mapping_type} mappings from validated_data"
                    )
                    for field_name, field_value in sample_record.items():
                        if mapping_type.startswith("crew_generated"):
                            target_field = self._suggest_target_field(
                                field_name, {"sample_value": field_value}
                            )
                        else:
                            target_field = self._map_common_field_names(field_name)

                        mapping = {
                            "source_field": field_name,
                            "target_field": target_field,
                            "confidence": confidence,
                            "mapping_type": mapping_type,
                            "status": "suggested",
                        }
                        mappings.append(mapping)
        except Exception as e:
            self.logger.error(
                f"❌ Failed to generate mappings from validated_data: {e}"
            )

        return mappings

    async def _use_persistent_field_mapping_agent(
        self, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use the actual persistent field_mapper agent for intelligent field mapping"""
        try:
            self.logger.info(
                "🤖 Using persistent field_mapper agent for intelligent mapping"
            )

            # Get raw data from input_data for agent processing
            validated_data = input_data.get("validated_data", [])

            if not validated_data:
                self.logger.warning(
                    "⚠️ No validated_data available for persistent agent"
                )
                self.logger.warning(f"📊 Input data keys: {list(input_data.keys())}")
                return {}

            self.logger.info(f"📊 Validated data has {len(validated_data)} records")

            # Log context details before executing field mapping
            context = self.flow.context
            client_id = getattr(context, "client_account_id", "None")
            engagement_id = getattr(context, "engagement_id", "None")
            self.logger.info(
                f"📊 Executing field mapping with persistent agent - "
                f"client_id: {client_id}, engagement_id: {engagement_id}"
            )

            # Get service registry from flow
            service_registry = getattr(self.flow, "service_registry", None)
            if not service_registry:
                self.logger.warning("No service_registry found in flow")
                from app.services.service_registry import ServiceRegistry

                service_registry = ServiceRegistry()

            # Execute field mapping using persistent agent wrapper
            agent_result = await execute_field_mapping(
                context=context,
                service_registry=service_registry,
                raw_data=validated_data,
            )

            self.logger.info("✅ Persistent field mapping execution completed")

            if not agent_result or "mappings" not in agent_result:
                self.logger.warning("⚠️ Persistent agent returned invalid result")
                return {}

            # Convert persistent mapping result to expected format
            field_mappings = []
            agent_mappings = agent_result.get("mappings", {})

            for source_field, mapping_info in agent_mappings.items():
                mapping = {
                    "source_field": source_field,
                    "target_field": mapping_info.get("target_field", "UNMAPPED"),
                    "confidence": mapping_info.get("confidence", 0.7),
                    "mapping_type": "persistent_agent_generated",
                    "status": "suggested",
                    "reasoning": mapping_info.get("reasoning", "AI agent analysis"),
                }
                field_mappings.append(mapping)

            result = {
                "field_mappings": field_mappings,
                "suggestions": [],
                "execution_method": "persistent_agent_execution",
                "status": "success",
                "critical_attributes_assessment": agent_result.get(
                    "critical_attributes_assessment", {}
                ),
            }

            self.logger.info(
                f"✅ Persistent agent generated {len(field_mappings)} intelligent mappings"
            )
            return result

        except Exception as e:
            self.logger.error(f"❌ Persistent field mapping agent failed: {e}")
            raise
