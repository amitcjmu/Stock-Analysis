"""
Field Mapping Crew - Full Agentic Version
Provides intelligent field mapping with full agent capabilities:
- Complete Asset model schema awareness
- Data pattern analysis
- Multi-field synthesis capabilities
- Intelligent reasoning and decision making
- Full audit trail
"""

import json
import logging
from typing import Any, Dict, List

from crewai import Crew, Process

from app.services.crewai_flows.config.crew_factory import (
    create_agent,
    create_crew,
    create_task,
)
from crewai.tools import BaseTool
from pydantic import Field

logger = logging.getLogger(__name__)


class AssetSchemaAnalysisTool(BaseTool):
    """Tool to analyze the Asset model schema"""

    name: str = "asset_schema_analyzer"
    description: str = (
        "Analyzes the complete Asset model schema to understand all available fields and their types"
    )

    def _run(self) -> str:
        """Return complete Asset model schema"""
        from sqlalchemy import inspect

        from app.models.asset import Asset

        mapper = inspect(Asset)
        schema_info = []

        for column in mapper.columns:
            col_info = {
                "name": column.name,
                "type": str(column.type),
                "nullable": column.nullable,
                "primary_key": column.primary_key,
                "foreign_key": bool(column.foreign_keys),
                "description": column.comment or "",
            }
            schema_info.append(col_info)

        # Asset field categories for better understanding
        field_categories = {
            "Identity": ["id", "name", "asset_name", "hostname", "asset_id", "fqdn"],
            "Classification": ["asset_type", "description", "technology_stack"],
            "Network": ["ip_address", "mac_address"],
            "Location": [
                "environment",
                "location",
                "datacenter",
                "rack_location",
                "availability_zone",
            ],
            "Hardware": [
                "operating_system",
                "os_version",
                "cpu_cores",
                "memory_gb",
                "storage_gb",
            ],
            "Business": [
                "business_owner",
                "technical_owner",
                "department",
                "application_name",
                "criticality",
                "business_criticality",
            ],
            "Migration": [
                "six_r_strategy",
                "migration_priority",
                "migration_complexity",
                "migration_wave",
                "migration_status",
            ],
            "Status": ["status", "mapping_status"],
            "Dependencies": ["dependencies", "related_assets"],
            "Performance": [
                "cpu_utilization_percent",
                "memory_utilization_percent",
                "disk_iops",
                "network_throughput_mbps",
            ],
            "Cost": ["current_monthly_cost", "estimated_cloud_cost"],
            "Quality": ["completeness_score", "quality_score"],
            "Discovery": [
                "discovery_method",
                "discovery_source",
                "discovery_timestamp",
            ],
            "Import": ["source_filename", "raw_data", "field_mappings_used"],
            "Metadata": ["created_at", "updated_at", "created_by", "updated_by"],
            "Multi-tenant": ["client_account_id", "engagement_id", "flow_id"],
            "Custom": ["custom_attributes"],
        }

        return json.dumps(
            {
                "schema": schema_info,
                "field_categories": field_categories,
                "total_fields": len(schema_info),
            },
            indent=2,
        )

    async def _arun(self) -> str:
        """Async version"""
        return self._run()


class DataPatternAnalysisTool(BaseTool):
    """Tool to analyze data patterns in source fields"""

    name: str = "data_pattern_analyzer"
    description: str = (
        "Analyzes data patterns and values to understand the nature of the data"
    )

    sample_data: List[Dict[str, Any]] = Field(default_factory=list)

    def _run(self, field_name: str) -> str:
        """Analyze patterns in a specific field"""
        if not self.sample_data:
            return "No sample data available"

        values = []
        for record in self.sample_data[:10]:  # Analyze up to 10 samples
            if field_name in record:
                values.append(record[field_name])

        if not values:
            return f"Field '{field_name}' not found in sample data"

        # Analyze patterns
        analysis = {
            "field": field_name,
            "sample_values": values[:5],
            "value_count": len(values),
            "unique_values": len(set(str(v) for v in values if v is not None)),
            "has_nulls": any(v is None or v == "" for v in values),
            "all_numeric": all(
                isinstance(v, (int, float)) for v in values if v is not None
            ),
            "all_strings": all(isinstance(v, str) for v in values if v is not None),
            "patterns": self._detect_patterns(values),
        }

        return json.dumps(analysis, indent=2, default=str)

    def _detect_patterns(self, values: List[Any]) -> Dict[str, Any]:
        """Detect common patterns in values"""
        patterns = {
            "looks_like_ip": False,
            "looks_like_hostname": False,
            "looks_like_email": False,
            "looks_like_date": False,
            "looks_like_version": False,
            "looks_like_path": False,
        }

        import re

        for value in values:
            if value and isinstance(value, str):
                # IP pattern
                if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", value):
                    patterns["looks_like_ip"] = True
                # Hostname pattern
                if re.match(
                    r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$",
                    value,
                ):
                    patterns["looks_like_hostname"] = True
                # Email pattern
                if "@" in value and "." in value:
                    patterns["looks_like_email"] = True
                # Date patterns
                if re.match(r"^\d{4}-\d{2}-\d{2}", value) or re.match(
                    r"^\d{2}/\d{2}/\d{4}", value
                ):
                    patterns["looks_like_date"] = True
                # Version pattern
                if re.match(r"^\d+\.\d+", value):
                    patterns["looks_like_version"] = True
                # Path pattern
                if "/" in value or "\\" in value:
                    patterns["looks_like_path"] = True

        return patterns

    async def _arun(self, field_name: str) -> str:
        """Async version"""
        return self._run(field_name)


class FieldMappingCrew:
    """Full Agentic Field Mapping Crew with complete capabilities"""

    def __init__(self, crewai_service, shared_memory=None, knowledge_base=None):
        self.crewai_service = crewai_service
        self.shared_memory = shared_memory
        self.knowledge_base = knowledge_base

        # Get proper LLM configuration from our LLM config service
        try:
            from app.services.llm_config import get_crewai_llm

            self.llm_model = get_crewai_llm()
            logger.info("✅ Field Mapping Crew using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM, using fallback: {e}")
            self.llm_model = getattr(crewai_service, "llm", None)

        logger.info("✅ Field Mapping Crew initialized with FULL agentic capabilities")

    def create_agents(self, raw_data: List[Dict[str, Any]]):
        """Create intelligent agents with full capabilities"""

        # Create tools with sample data
        schema_tool = AssetSchemaAnalysisTool()
        pattern_tool = DataPatternAnalysisTool(sample_data=raw_data)

        # Data Analysis Agent
        data_analyst_config = {
            "role": "Senior Data Pattern Analyst",
            "goal": "Analyze source data patterns and understand the semantic meaning of each field",
            "backstory": """You are an expert data analyst with 15+ years of experience in data migration
            and schema mapping. You have deep expertise in:

            - Recognizing data patterns (IPs, hostnames, dates, versions, etc.)
            - Understanding business context from data values
            - Identifying relationships between fields
            - Detecting composite information that needs synthesis

            Your strength is looking beyond field names to understand what the data actually represents.""",
            "llm": self.llm_model,
            "verbose": False,
            "allow_delegation": True,
            "tools": [pattern_tool],
            "memory": False,  # Per ADR-024: Use TenantMemoryManager
        }

        # Schema Mapping Expert
        schema_expert_config = {
            "role": "CMDB Schema Mapping Expert",
            "goal": "Map source fields to the most appropriate Asset model fields using intelligent analysis",
            "backstory": """You are a CMDB expert who deeply understands asset management schemas.
            You excel at:

            - Understanding the complete Asset model schema and its nuances
            - Mapping fields based on semantic meaning, not just names
            - Identifying when multiple source fields should map to one target
            - Recognizing when source data needs transformation or synthesis
            - Determining appropriate confidence scores based on mapping quality

            You NEVER make assumptions. You analyze the actual data patterns and the complete
            Asset schema to make intelligent mapping decisions.""",
            "llm": self.llm_model,
            "verbose": False,
            "allow_delegation": True,
            "tools": [schema_tool, pattern_tool],
            "memory": False,  # Per ADR-024: Use TenantMemoryManager
        }

        # Synthesis Specialist
        synthesis_specialist_config = {
            "role": "Data Synthesis and Transformation Specialist",
            "goal": "Identify and design complex field mappings that require data synthesis or transformation",
            "backstory": """You specialize in complex data transformations where simple 1:1 mappings
            don't suffice. Your expertise includes:

            - Combining multiple fields into single target fields
            - Extracting partial information from complex fields
            - Designing transformation rules for data synthesis
            - Ensuring no data loss during multi-field mappings
            - Creating clear transformation specifications

            You ensure that when multiple source fields contain related information, they are
            properly synthesized without overwriting each other.""",
            "llm": self.llm_model,
            "verbose": False,
            "allow_delegation": False,
            "tools": [pattern_tool],
            "memory": False,  # Per ADR-024: Use TenantMemoryManager
        }

        data_analyst = create_agent(**data_analyst_config)
        schema_expert = create_agent(**schema_expert_config)
        synthesis_specialist = create_agent(**synthesis_specialist_config)

        return [data_analyst, schema_expert, synthesis_specialist]

    def create_tasks(self, agents, raw_data: List[Dict[str, Any]]):
        """Create comprehensive mapping tasks"""
        data_analyst, schema_expert, synthesis_specialist = agents

        headers = list(raw_data[0].keys()) if raw_data else []
        logger.info(
            f"🔍 DEBUG: Standard crew received {len(raw_data)} records with headers: {headers}"
        )
        # Use minimal data sample to avoid rate limits - just headers and one sample value per field
        sample_values = {}
        if raw_data:
            # Only show first 10 fields to reduce token usage
            limited_headers = headers[:10]
            for header in limited_headers:
                sample_values[header] = str(raw_data[0].get(header, ""))[
                    :30
                ]  # Limit to 30 chars per field

            if len(headers) > 10:
                logger.info(
                    f"⚠️ Limiting field mapping to first 10 fields out of {len(headers)} to prevent rate limits"
                )
                sample_values["...more_fields"] = (
                    f"({len(headers) - 10} additional fields not shown)"
                )

        # Task 1: Analyze Data Patterns (OPTIMIZED for rate limits)
        data_analysis_task = create_task(
            description=f"""
            Analyze the source data headers to understand patterns and semantic meaning.

            Source Headers (Limited): {list(sample_values.keys())}
            Sample Values: {json.dumps(sample_values, indent=2, default=str)}

            IMPORTANT: Be concise to avoid rate limits. For each field:
            1. Identify the semantic meaning based on the field name and sample value
            2. Note if it's metadata (row numbers, IDs) vs actual asset data
            3. Keep analysis brief but accurate

            Return a concise analysis focusing on field purpose and meaning.
            """,
            agent=data_analyst,
            expected_output="""
            Detailed analysis of each source field including:
            - Field name and data patterns found
            - Semantic meaning of the data
            - Whether it's metadata or actual asset data
            - Relationships to other fields
            - Any composite information detected
            """,
        )

        # Task 2: Create Intelligent Mappings (OPTIMIZED for rate limits)
        mapping_task = create_task(
            description=f"""
            Create field mappings from source headers to Asset model fields.

            Source Headers (Limited): {list(sample_values.keys())}

            CRITICAL INSTRUCTIONS:
            1. Use the EXACT CSV field names as source fields in your mappings
            2. DO NOT normalize or change the CSV field names (e.g., keep "Device_ID" not "device_id")
            3. Map each header to the most appropriate Asset model field
            4. Skip obvious metadata fields (row_index, etc.)
            5. Focus on standard mappings first
            6. Assign accurate confidence scores based on:
               - 0.9+: Perfect semantic match with clear data patterns
               - 0.7-0.89: Good match with some uncertainty
               - 0.5-0.69: Possible match but needs review
               - Below 0.5: Weak match, likely needs human input

            EXAMPLE OUTPUT (preserving exact field names):
            {{
                "mappings": {{
                    "Device_ID": {{
                        "target_field": "asset_id",
                        "confidence": 0.95,
                        "reasoning": "Clear identifier field",
                        "requires_transformation": false
                    }},
                    "Device_Name": {{
                        "target_field": "asset_name",
                        "confidence": 0.95,
                        "reasoning": "Name field for assets",
                        "requires_transformation": false
                    }}
                }},
                "skipped_fields": [],
                "synthesis_required": []
            }}
            """,
            agent=schema_expert,
            context=[data_analysis_task],
            expected_output="""
            Complete JSON mapping specification with all source fields mapped or explicitly skipped,
            including confidence scores and detailed reasoning.
            """,
        )

        # Task 3: Design Complex Transformations (commented out to reduce LLM calls)
        # synthesis_task = create_task(...)
        # Synthesis task was removed to reduce LLM calls and prevent output override

        # Return only mapping task - synthesis task output was overriding the actual mappings
        return [data_analysis_task, mapping_task]

    def create_crew(self, raw_data: List[Dict[str, Any]]):
        """Create full agentic crew with collaboration"""
        agents = self.create_agents(raw_data)
        tasks = self.create_tasks(agents, raw_data)

        crew_config = {
            "agents": agents,
            "tasks": tasks,
            "process": Process.sequential,
            "verbose": False,  # Reduce verbosity to minimize LLM calls
            "memory": False,  # Disable memory temporarily to reduce calls
            "planning": False,  # Disable planning to reduce LLM calls
            "collaboration": False,  # Disable collaboration to reduce inter-agent communication
            "share_crew": False,  # Disable crew sharing to reduce calls
            # Don't include manager_llm or planning_llm to avoid extra coordination calls
            # "manager_llm": self.llm,
            # "planning_llm": self.llm,
            # "knowledge": self.knowledge_base
        }

        logger.info(
            "Creating FULL Agentic Field Mapping Crew with complete capabilities"
        )
        return create_crew(**crew_config)

    def get_audit_metadata(self) -> Dict[str, Any]:
        """Get metadata for audit trail"""
        return {
            "crew_type": "field_mapping",
            "version": "2.0",
            "capabilities": [
                "full_schema_analysis",
                "data_pattern_recognition",
                "multi_field_synthesis",
                "intelligent_reasoning",
            ],
            "agents": [
                "Senior Data Pattern Analyst",
                "CMDB Schema Mapping Expert",
                "Data Synthesis Specialist",
            ],
        }


def create_field_mapping_crew(
    crewai_service,
    raw_data: List[Dict[str, Any]],
    shared_memory=None,
    knowledge_base=None,
) -> Crew:
    """Factory function to create Full Agentic Field Mapping Crew"""
    crew_instance = FieldMappingCrew(crewai_service, shared_memory, knowledge_base)
    return crew_instance.create_crew(raw_data)
