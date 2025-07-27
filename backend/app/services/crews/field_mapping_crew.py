"""
Field Mapping Crew - Proper CrewAI implementation
"""

import json
import logging
import re
from typing import Any, Dict, List

from crewai import Process, Task

from app.services.crews.base_crew import BaseDiscoveryCrew

logger = logging.getLogger(__name__)


class FieldMappingCrew(BaseDiscoveryCrew):
    """
    Crew for intelligent field mapping using multiple specialized agents.

    Process:
    1. Schema analysis
    2. Semantic matching
    3. Confidence scoring
    4. Validation
    """

    def __init__(self):
        """Initialize field mapping crew"""
        super().__init__(
            name="field_mapping_crew",
            description="Intelligent field mapping with semantic understanding",
            process=Process.sequential,
            verbose=True,
            memory=True,
            cache=True,
        )

    def create_agents(self) -> List[Any]:
        """Create specialized agents for field mapping"""
        agents = []

        # Try to create agents through factory, fallback to available agents
        try:
            # Import agent factory locally to avoid circular imports
            from app.services.agents.factory import agent_factory

            # Primary field mapping agent
            field_mapper = agent_factory.create_agent("field_mapping_agent")
            if field_mapper:
                agents.append(field_mapper)

            # Data validation agent for validation tasks
            validator = agent_factory.create_agent("data_validation_agent")
            if validator:
                agents.append(validator)

        except Exception as e:
            logger.warning(f"Agent factory creation failed: {e}")

        # If no agents were created via factory, create a basic field mapping agent
        if not agents:
            logger.info("Creating basic field mapping agent as fallback")
            from crewai import Agent

            basic_mapper = Agent(
                role="CMDB Field Mapping Specialist",
                goal="Map source data fields to standard CMDB attributes with confidence scores",
                backstory="""You are an expert field mapping specialist with deep knowledge of CMDB schemas.

                STANDARD TARGET ATTRIBUTES:
                - asset_name (hostname, server_name, name, asset_name)
                - asset_type (type, category, class, asset_type)
                - asset_id (id, asset_id, ci_id, configuration_item_id)
                - environment (env, environment, stage, tier)
                - business_criticality (criticality, priority, importance)
                - operating_system (os, operating_system, platform)
                - ip_address (ip, ip_address, primary_ip)
                - owner (owner, responsible_person, contact)
                - location (location, site, datacenter)
                - status (status, state, operational_status)

                You provide accurate mappings with confidence scores based on semantic similarity and field patterns.""",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                tools=[],
            )
            agents.append(basic_mapper)

        return agents

    def create_tasks(self, inputs: Dict[str, Any]) -> List[Task]:
        """Create field mapping tasks"""
        source_schema = inputs.get("source_schema", {})
        target_fields = inputs.get("target_fields", self._get_default_target_fields())
        sample_data = inputs.get("sample_data", [])
        raw_data = inputs.get("raw_data", [])

        # Extract headers from raw_data if source_schema is empty
        if not source_schema and raw_data:
            headers = list(raw_data[0].keys()) if raw_data else []
            source_schema = {field: "string" for field in headers}

        tasks = []

        # Task 1: Analyze source schema and create mappings
        mapping_task = Task(
            description=f"""
            FIELD MAPPING TASK:

            Source Schema: {json.dumps(source_schema, indent=2)}
            Sample Data: {json.dumps(sample_data[:5], indent=2) if sample_data else json.dumps(raw_data[:3], indent=2) if raw_data else "No sample data"}
            Target Fields Available: {json.dumps(target_fields, indent=2)}

            Your task is to create accurate field mappings:

            1. ANALYZE each source field:
               - Data type and format
               - Value patterns from sample data
               - Potential field purpose

            2. CREATE MAPPINGS:
               - Map each source field to the best matching target field
               - Consider field names, data types, and content patterns
               - Assign confidence score (0.0-1.0) based on match quality

            3. CONFIDENCE SCORING:
               - 0.9+: Exact name match (hostname → asset_name)
               - 0.7+: Semantic match (server_name → asset_name)
               - 0.5+: Possible match based on content (name → asset_name)
               - 0.3+: Weak match requiring review
               - 0.0: No suitable match found

            4. OUTPUT FORMAT:
            Return a JSON object with this structure:
            {{
                "mappings": [
                    {{
                        "source_field": "field_name",
                        "target_field": "target_name",
                        "confidence": 0.85,
                        "reasoning": "explanation of mapping logic",
                        "data_type_compatible": true,
                        "requires_transformation": false
                    }}
                ],
                "unmapped_fields": ["field1", "field2"],
                "summary": {{
                    "total_source_fields": 10,
                    "mapped_fields": 8,
                    "high_confidence_mappings": 6,
                    "requires_review": 2
                }}
            }}
            """,
            agent=self.agents[0],  # Primary mapping agent
            expected_output="JSON field mapping result with mappings, confidence scores, and summary",
        )
        tasks.append(mapping_task)

        # Task 2: Validation (if we have a validation agent)
        if len(self.agents) > 1:
            validation_task = Task(
                description="""
                VALIDATION TASK:

                Review the field mappings for:
                1. Data type compatibility between source and target
                2. Potential data loss during mapping
                3. Missing critical fields that should be mapped
                4. Overly confident mappings that need review
                5. Duplicate target field assignments

                Provide validation results and recommendations for improvement.
                """,
                agent=self.agents[1],  # Validation agent
                expected_output="Validation report with issues found and recommendations",
                context=[mapping_task],
            )
            tasks.append(validation_task)

        return tasks

    def _get_default_target_fields(self) -> List[str]:
        """Get default CMDB target fields"""
        return [
            "asset_name",
            "asset_type",
            "asset_id",
            "environment",
            "business_criticality",
            "operating_system",
            "ip_address",
            "owner",
            "location",
            "status",
            "manufacturer",
            "model",
            "serial_number",
            "cpu_count",
            "memory_gb",
            "disk_space_gb",
            "application_name",
            "application_version",
            "database_type",
            "database_version",
            "port",
            "protocol",
            "description",
            "notes",
            "last_discovered",
            "discovery_source",
        ]

    def process_results(self, raw_results: Any) -> Dict[str, Any]:
        """Process field mapping results"""
        try:
            # Extract final result from the last task
            final_result = raw_results

            # Handle different result formats
            if isinstance(final_result, str):
                try:
                    import re

                    # Try to extract JSON from string result
                    json_match = re.search(r"\{.*\}", final_result, re.DOTALL)
                    if json_match:
                        final_result = json.loads(json_match.group())
                    else:
                        # Fallback: parse basic field mappings from text
                        final_result = self._parse_text_mappings(final_result)
                except Exception as e:
                    logger.warning(f"Could not parse JSON from results: {e}")
                    final_result = {"mappings": [], "error": "Failed to parse results"}

            # Ensure we have the expected structure
            if not isinstance(final_result, dict):
                final_result = {"mappings": [], "error": "Unexpected result format"}

            mappings = final_result.get("mappings", [])

            # Calculate summary statistics
            total_mappings = len(mappings)
            high_confidence = sum(1 for m in mappings if m.get("confidence", 0) >= 0.7)
            medium_confidence = sum(
                1 for m in mappings if 0.5 <= m.get("confidence", 0) < 0.7
            )
            low_confidence = sum(1 for m in mappings if m.get("confidence", 0) < 0.5)

            return {
                "crew_name": self.name,
                "status": "completed",
                "mappings": mappings,
                "unmapped_fields": final_result.get("unmapped_fields", []),
                "summary": {
                    "total_mappings": total_mappings,
                    "high_confidence": high_confidence,
                    "medium_confidence": medium_confidence,
                    "low_confidence": low_confidence,
                    "requires_review": low_confidence,
                    "mapping_rate": (
                        (
                            total_mappings
                            / (
                                total_mappings
                                + len(final_result.get("unmapped_fields", []))
                            )
                        )
                        * 100
                        if total_mappings > 0
                        else 0
                    ),
                },
                "context": {
                    "client_account_id": (
                        self.context.client_account_id if self.context else None
                    ),
                    "engagement_id": (
                        self.context.engagement_id if self.context else None
                    ),
                },
                "metadata": {
                    "processing_time": final_result.get("processing_time"),
                    "agent_count": len(self.agents),
                    "task_count": len(self.tasks),
                },
            }

        except Exception as e:
            logger.error(f"Error processing field mapping results: {e}")
            return {
                "crew_name": self.name,
                "status": "error",
                "error": str(e),
                "mappings": [],
                "summary": {"total_mappings": 0, "error": True},
                "context": {
                    "client_account_id": (
                        self.context.client_account_id if self.context else None
                    ),
                    "engagement_id": (
                        self.context.engagement_id if self.context else None
                    ),
                },
            }

    def _parse_text_mappings(self, text_result: str) -> Dict[str, Any]:
        """Parse field mappings from text when JSON parsing fails"""
        mappings = []

        # Simple pattern matching for basic mapping extraction
        lines = text_result.split("\n")
        for line in lines:
            if "->" in line or "→" in line:
                try:
                    # Extract source and target fields
                    parts = line.split("->" if "->" in line else "→")
                    if len(parts) == 2:
                        source = parts[0].strip()
                        target = parts[1].strip()

                        # Extract confidence if present
                        confidence = 0.5  # Default
                        if "(" in target and ")" in target:
                            conf_match = re.search(r"\((\d+\.?\d*)\)", target)
                            if conf_match:
                                confidence = float(conf_match.group(1))
                                target = re.sub(r"\s*\([^)]*\)", "", target).strip()

                        mappings.append(
                            {
                                "source_field": source,
                                "target_field": target,
                                "confidence": confidence,
                                "reasoning": "Parsed from text output",
                                "data_type_compatible": True,
                                "requires_transformation": False,
                            }
                        )
                except Exception:
                    continue

        return {
            "mappings": mappings,
            "unmapped_fields": [],
            "summary": {
                "total_source_fields": len(mappings),
                "mapped_fields": len(mappings),
                "parsing_fallback": True,
            },
        }
