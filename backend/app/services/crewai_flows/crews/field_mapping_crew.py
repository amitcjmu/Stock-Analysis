"""
Field Mapping Crew - Simplified Fast Version
Optimized for speed and reliability:
- No knowledge base dependencies to eliminate search failures
- Minimal delegation to reduce processing time
- No human input to avoid EOF errors
- Direct field mapping with confidence scoring
"""

import logging
import json
from typing import Dict, List, Any, Optional
from crewai import Agent, Task, Crew, Process

logger = logging.getLogger(__name__)

class FieldMappingCrew:
    """Simplified Field Mapping Crew optimized for speed and reliability"""
    
    def __init__(self, crewai_service, shared_memory=None, knowledge_base=None):
        self.crewai_service = crewai_service
        
        # Get proper LLM configuration from our LLM config service
        try:
            from app.services.llm_config import get_crewai_llm
            self.llm = get_crewai_llm()
            logger.info("✅ Field Mapping Crew using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM, using fallback: {e}")
            self.llm = getattr(crewai_service, 'llm', None)
        
        logger.info("✅ Field Mapping Crew initialized in FAST mode (no knowledge base, minimal delegation)")
    
    def create_agents(self):
        """Create simplified agents optimized for speed"""
        
        # Single Field Mapping Agent - handles everything directly
        field_mapper_config = {
            "role": "CMDB Field Mapping Specialist",
            "goal": "Quickly map source data fields to standard CMDB attributes with confidence scores",
            "backstory": """You are an expert field mapping specialist. You work FAST and DIRECTLY.
            
            YOUR MISSION: Map source fields to standard CMDB attributes quickly and confidently.
            
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
            
            WORK STYLE:
            - Work DIRECTLY without delegation
            - Make decisions QUICKLY based on field names
            - Provide confidence scores: 0.9+ for exact matches, 0.7+ for semantic matches, 0.5+ for possible matches
            - Complete mapping in under 60 seconds
            - Focus on SPEED over perfection
            """,
            "llm": self.llm,
            "verbose": True,
            "allow_delegation": False,  # NO DELEGATION for speed
            "max_execution_time": 60,  # 1 minute timeout
            "max_retry": 1,
            "memory": None,  # No memory for speed
            "collaboration": False,  # No collaboration for speed
            "tools": []  # No tools for speed
        }
        
        field_mapper = Agent(**field_mapper_config)
        
        return [field_mapper]
    
    def create_tasks(self, agents, raw_data: List[Dict[str, Any]]):
        """Create simplified fast mapping task"""
        field_mapper = agents[0]
        
        headers = list(raw_data[0].keys()) if raw_data else []
        data_sample = raw_data[:3] if raw_data else []  # Only 3 samples for speed
        
        # Single fast mapping task
        mapping_task = Task(
            description=f"""
            FAST FIELD MAPPING TASK:
            
            Source Headers: {headers}
            Sample Data: {data_sample}
            
            YOUR TASK: Create field mappings in under 60 seconds.
            
            MAPPING RULES:
            1. Map each source field to the best standard CMDB attribute
            2. Assign confidence score (0.0-1.0) based on match quality
            3. Use these standard targets: asset_name, asset_type, asset_id, environment, business_criticality, operating_system, ip_address, owner, location, status
            4. Work DIRECTLY - no delegation, no collaboration
            5. Make quick decisions based on field names and patterns
            
            CONFIDENCE SCORING:
            - 0.9+: Exact name match (hostname → asset_name)
            - 0.7+: Semantic match (server_name → asset_name)
            - 0.5+: Possible match (name → asset_name)
            - 0.3+: Weak match (description → notes)
            - 0.0: No match found
            
            OUTPUT FORMAT:
            Return JSON with field mappings and confidence scores.
            """,
            agent=field_mapper,
            expected_output="""
            JSON field mapping result with:
            - source_field → target_attribute mappings
            - confidence scores for each mapping
            - total mapped fields count
            - unmapped fields list
            """,
            tools=[],  # No tools for speed
            context=[],  # No dependencies
            max_execution_time=60,  # 1 minute max
            max_retry=1,
            human_input=False  # NO HUMAN INPUT to avoid EOF errors
        )
        
        return [mapping_task]
    
    def create_crew(self, raw_data: List[Dict[str, Any]]):
        """Create simplified fast crew"""
        agents = self.create_agents()
        tasks = self.create_tasks(agents, raw_data)
        
        crew_config = {
            "agents": agents,
            "tasks": tasks,
            "process": Process.sequential,  # Simple sequential for speed
            "verbose": True,
            "memory": False,  # No memory for speed
            "planning": False,  # No planning for speed
            "collaboration": False,  # No collaboration for speed
            "share_crew": False,  # No sharing for speed
            "manager_llm": None,  # No manager for speed
            "planning_llm": None,  # No planning LLM
            "knowledge": None  # NO KNOWLEDGE BASE to avoid search failures
        }
        
        logger.info("Creating FAST Field Mapping Crew (no knowledge base, no delegation, no human input)")
        return Crew(**crew_config)
    
    def _create_schema_analysis_tools(self):
        """No tools for speed"""
        return []
    
    def _create_mapping_confidence_tools(self):
        """No tools for speed"""
        return []
    
    def _create_field_mapping_tools(self):
        """No tools for speed"""
        return []

def create_field_mapping_crew(crewai_service, raw_data: List[Dict[str, Any]], 
                             shared_memory=None, knowledge_base=None) -> Crew:
    """Factory function to create fast Field Mapping Crew"""
    crew_instance = FieldMappingCrew(crewai_service, shared_memory, knowledge_base)
    return crew_instance.create_crew(raw_data)