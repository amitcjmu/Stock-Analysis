"""
Field Mapping Crew - Full Agentic Version
Provides intelligent field mapping with full agent capabilities:
- Complete Asset model schema awareness
- Data pattern analysis
- Multi-field synthesis capabilities
- Intelligent reasoning and decision making
- Full audit trail
"""

import logging
import json
from typing import Dict, List, Any, Optional
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AssetSchemaAnalysisTool(BaseTool):
    """Tool to analyze the Asset model schema"""
    name: str = "asset_schema_analyzer"
    description: str = "Analyzes the complete Asset model schema to understand all available fields and their types"
    
    def _run(self) -> str:
        """Return complete Asset model schema"""
        from app.models.asset import Asset
        from sqlalchemy import inspect
        
        mapper = inspect(Asset)
        schema_info = []
        
        for column in mapper.columns:
            col_info = {
                "name": column.name,
                "type": str(column.type),
                "nullable": column.nullable,
                "primary_key": column.primary_key,
                "foreign_key": bool(column.foreign_keys),
                "description": column.comment or ""
            }
            schema_info.append(col_info)
        
        # Asset field categories for better understanding
        field_categories = {
            "Identity": ["id", "name", "asset_name", "hostname", "asset_id", "fqdn"],
            "Classification": ["asset_type", "description", "technology_stack"],
            "Network": ["ip_address", "mac_address"],
            "Location": ["environment", "location", "datacenter", "rack_location", "availability_zone"],
            "Hardware": ["operating_system", "os_version", "cpu_cores", "memory_gb", "storage_gb"],
            "Business": ["business_owner", "technical_owner", "department", "application_name", 
                        "criticality", "business_criticality"],
            "Migration": ["six_r_strategy", "migration_priority", "migration_complexity", 
                         "migration_wave", "migration_status"],
            "Status": ["status", "mapping_status"],
            "Dependencies": ["dependencies", "related_assets"],
            "Performance": ["cpu_utilization_percent", "memory_utilization_percent", 
                           "disk_iops", "network_throughput_mbps"],
            "Cost": ["current_monthly_cost", "estimated_cloud_cost"],
            "Quality": ["completeness_score", "quality_score"],
            "Discovery": ["discovery_method", "discovery_source", "discovery_timestamp"],
            "Import": ["source_filename", "raw_data", "field_mappings_used"],
            "Metadata": ["created_at", "updated_at", "created_by", "updated_by"],
            "Multi-tenant": ["client_account_id", "engagement_id", "flow_id"],
            "Custom": ["custom_attributes"]
        }
        
        return json.dumps({
            "schema": schema_info,
            "field_categories": field_categories,
            "total_fields": len(schema_info)
        }, indent=2)
    
    async def _arun(self) -> str:
        """Async version"""
        return self._run()


class DataPatternAnalysisTool(BaseTool):
    """Tool to analyze data patterns in source fields"""
    name: str = "data_pattern_analyzer"
    description: str = "Analyzes data patterns and values to understand the nature of the data"
    
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
            "all_numeric": all(isinstance(v, (int, float)) for v in values if v is not None),
            "all_strings": all(isinstance(v, str) for v in values if v is not None),
            "patterns": self._detect_patterns(values)
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
            "looks_like_path": False
        }
        
        import re
        
        for value in values:
            if value and isinstance(value, str):
                # IP pattern
                if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', value):
                    patterns["looks_like_ip"] = True
                # Hostname pattern
                if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$', value):
                    patterns["looks_like_hostname"] = True
                # Email pattern
                if '@' in value and '.' in value:
                    patterns["looks_like_email"] = True
                # Date patterns
                if re.match(r'^\d{4}-\d{2}-\d{2}', value) or re.match(r'^\d{2}/\d{2}/\d{4}', value):
                    patterns["looks_like_date"] = True
                # Version pattern
                if re.match(r'^\d+\.\d+', value):
                    patterns["looks_like_version"] = True
                # Path pattern
                if '/' in value or '\\' in value:
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
            self.llm = get_crewai_llm()
            logger.info("✅ Field Mapping Crew using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM, using fallback: {e}")
            self.llm = getattr(crewai_service, 'llm', None)
        
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
            "llm": self.llm,
            "verbose": True,
            "allow_delegation": True,
            "tools": [pattern_tool],
            "memory": True
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
            "llm": self.llm,
            "verbose": True,
            "allow_delegation": True,
            "tools": [schema_tool, pattern_tool],
            "memory": True
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
            "llm": self.llm,
            "verbose": True,
            "allow_delegation": False,
            "tools": [pattern_tool],
            "memory": True
        }
        
        data_analyst = Agent(**data_analyst_config)
        schema_expert = Agent(**schema_expert_config)
        synthesis_specialist = Agent(**synthesis_specialist_config)
        
        return [data_analyst, schema_expert, synthesis_specialist]
    
    def create_tasks(self, agents, raw_data: List[Dict[str, Any]]):
        """Create comprehensive mapping tasks"""
        data_analyst, schema_expert, synthesis_specialist = agents
        
        headers = list(raw_data[0].keys()) if raw_data else []
        # Provide more samples for better analysis
        data_sample = raw_data[:10] if len(raw_data) >= 10 else raw_data
        
        # Task 1: Analyze Data Patterns
        data_analysis_task = Task(
            description=f"""
            Analyze the source data to understand patterns and semantic meaning.
            
            Source Headers: {headers}
            Sample Data: {json.dumps(data_sample, indent=2, default=str)}
            
            For each field:
            1. Analyze the data patterns (use the data_pattern_analyzer tool)
            2. Understand what the data represents semantically
            3. Identify fields that might contain composite information
            4. Note any fields that seem to be metadata (like row numbers) vs actual data
            5. Identify relationships between fields
            
            Provide a comprehensive analysis of what each field contains and represents.
            """,
            agent=data_analyst,
            expected_output="""
            Detailed analysis of each source field including:
            - Field name and data patterns found
            - Semantic meaning of the data
            - Whether it's metadata or actual asset data
            - Relationships to other fields
            - Any composite information detected
            """
        )
        
        # Task 2: Create Intelligent Mappings
        mapping_task = Task(
            description=f"""
            Create intelligent field mappings based on the data analysis.
            
            Use the asset_schema_analyzer tool to understand ALL available Asset model fields.
            
            IMPORTANT INSTRUCTIONS:
            1. Map based on semantic meaning, not just field names
            2. Skip pure metadata fields (row numbers, indices, etc.)
            3. For composite data, design how to synthesize multiple fields
            4. Consider ALL Asset model fields, not just common ones
            5. Provide detailed reasoning for each mapping
            6. Assign accurate confidence scores based on:
               - 0.9+: Perfect semantic match with clear data patterns
               - 0.7-0.89: Good match with some uncertainty
               - 0.5-0.69: Possible match but needs review
               - Below 0.5: Weak match, likely needs human input
            
            OUTPUT FORMAT:
            {{
                "mappings": {{
                    "source_field": {{
                        "target_field": "asset_field_name",
                        "confidence": 0.85,
                        "reasoning": "Detailed explanation",
                        "requires_transformation": false
                    }}
                }},
                "skipped_fields": ["metadata_field1", "metadata_field2"],
                "synthesis_required": []
            }}
            """,
            agent=schema_expert,
            context=[data_analysis_task],
            expected_output="""
            Complete JSON mapping specification with all source fields mapped or explicitly skipped,
            including confidence scores and detailed reasoning.
            """
        )
        
        # Task 3: Design Complex Transformations
        synthesis_task = Task(
            description=f"""
            Design transformation rules for any complex mappings identified.
            
            Based on the mapping analysis, create specific transformation rules for:
            1. Multi-field synthesis (combining multiple source fields)
            2. Field extraction (extracting part of a field)
            3. Data transformation (format changes, calculations, etc.)
            
            Ensure that when multiple fields map to the same target, they enhance rather than overwrite.
            
            For each transformation, specify:
            - Source fields involved
            - Target field
            - Transformation logic
            - Order of operations (if multiple sources)
            - Conflict resolution strategy
            
            OUTPUT FORMAT:
            {{
                "transformations": [
                    {{
                        "source_fields": ["field1", "field2"],
                        "target_field": "asset_field",
                        "transformation_type": "synthesis",
                        "logic": "Detailed transformation logic",
                        "conflict_resolution": "How to handle conflicts"
                    }}
                ]
            }}
            """,
            agent=synthesis_specialist,
            context=[data_analysis_task, mapping_task],
            expected_output="""
            Complete transformation specifications for any complex mappings,
            ensuring no data loss and proper synthesis of information.
            """
        )
        
        return [data_analysis_task, mapping_task, synthesis_task]
    
    def create_crew(self, raw_data: List[Dict[str, Any]]):
        """Create full agentic crew with collaboration"""
        agents = self.create_agents(raw_data)
        tasks = self.create_tasks(agents, raw_data)
        
        crew_config = {
            "agents": agents,
            "tasks": tasks,
            "process": Process.sequential,
            "verbose": True,
            "memory": True,  # Enable memory for better decisions
            "planning": True,  # Enable planning for complex mappings
            "collaboration": True,  # Enable agent collaboration
            "share_crew": True,  # Share insights between agents
            "manager_llm": self.llm,  # Manager for coordination
            "planning_llm": self.llm,  # Planning LLM
            "knowledge": self.knowledge_base  # Use knowledge base if available
        }
        
        logger.info("Creating FULL Agentic Field Mapping Crew with complete capabilities")
        return Crew(**crew_config)
    
    def get_audit_metadata(self) -> Dict[str, Any]:
        """Get metadata for audit trail"""
        return {
            "crew_type": "field_mapping",
            "version": "2.0",
            "capabilities": [
                "full_schema_analysis",
                "data_pattern_recognition",
                "multi_field_synthesis",
                "intelligent_reasoning"
            ],
            "agents": [
                "Senior Data Pattern Analyst",
                "CMDB Schema Mapping Expert",
                "Data Synthesis Specialist"
            ]
        }


def create_field_mapping_crew(crewai_service, raw_data: List[Dict[str, Any]], 
                             shared_memory=None, knowledge_base=None) -> Crew:
    """Factory function to create Full Agentic Field Mapping Crew"""
    crew_instance = FieldMappingCrew(crewai_service, shared_memory, knowledge_base)
    return crew_instance.create_crew(raw_data)