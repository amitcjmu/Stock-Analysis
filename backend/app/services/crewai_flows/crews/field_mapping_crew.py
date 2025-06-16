"""
Field Mapping Crew - Foundation Phase
Enhanced implementation with CrewAI best practices:
- Hierarchical management with manager agents
- Shared memory for cross-crew learning  
- Knowledge base integration
- Agent collaboration features
"""

import logging
import json
from typing import Dict, List, Any, Optional
from crewai import Agent, Task, Crew, Process

# Import advanced CrewAI features with fallbacks
try:
    from crewai.memory import LongTermMemory
    from crewai.knowledge import KnowledgeBase
    CREWAI_ADVANCED_AVAILABLE = True
except ImportError:
    CREWAI_ADVANCED_AVAILABLE = False
    # Fallback classes
    class LongTermMemory:
        def __init__(self, **kwargs):
            pass
    class KnowledgeBase:
        def __init__(self, **kwargs):
            pass

logger = logging.getLogger(__name__)

class FieldMappingCrew:
    """Enhanced Field Mapping Crew with CrewAI best practices"""
    
    def __init__(self, crewai_service, shared_memory=None, knowledge_base=None):
        self.crewai_service = crewai_service
        self.llm = getattr(crewai_service, 'llm', None)
        
        # Setup shared memory and knowledge base
        self.shared_memory = shared_memory or self._setup_shared_memory()
        self.knowledge_base = knowledge_base or self._setup_knowledge_base()
        
        logger.info("✅ Field Mapping Crew initialized with advanced features")
    
    def _setup_shared_memory(self) -> Optional[LongTermMemory]:
        """Setup shared memory for field mapping insights"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Shared memory not available - using fallback")
            return None
        
        try:
            return LongTermMemory(
                storage_type="vector",
                embedder_config={
                    "provider": "openai", 
                    "model": "text-embedding-3-small"
                }
            )
        except Exception as e:
            logger.warning(f"Failed to setup shared memory: {e}")
            return None
    
    def _setup_knowledge_base(self) -> Optional[KnowledgeBase]:
        """Setup knowledge base for field mapping patterns"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Knowledge base not available - using fallback")
            return None
        
        try:
            return KnowledgeBase(
                sources=[
                    "backend/app/knowledge_bases/field_mapping_patterns.json"
                ],
                embedder_config={
                    "provider": "openai",
                    "model": "text-embedding-3-small"
                }
            )
        except Exception as e:
            logger.warning(f"Failed to setup knowledge base: {e}")
            return None
    
    def create_agents(self):
        """Create agents with hierarchical management"""
        
        # Manager Agent for hierarchical coordination
        field_mapping_manager = Agent(
            role="Field Mapping Manager",
            goal="Coordinate field mapping analysis and ensure comprehensive coverage of all data fields",
            backstory="""You are a senior data architect with 15+ years of experience managing 
            enterprise data migration projects. You excel at coordinating complex field mapping 
            tasks across diverse data sources and ensuring quality outcomes.""",
            llm=self.llm,
            memory=self.shared_memory,
            knowledge=self.knowledge_base,
            verbose=True,
            allow_delegation=True,
            max_delegation=2,
            planning=True if CREWAI_ADVANCED_AVAILABLE else False
        )
        
        # Schema Analysis Expert - specialist agent
        schema_analyst = Agent(
            role="Schema Analysis Expert", 
            goal="Analyze data structure semantics and understand field relationships for migration mapping",
            backstory="""You are an expert data analyst specializing in schema analysis for enterprise 
            systems. You have deep knowledge of CMDB structures and can understand field meanings from 
            context, naming patterns, and data samples.""",
            llm=self.llm,
            memory=self.shared_memory,
            knowledge=self.knowledge_base,
            verbose=True,
            collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
            tools=self._create_schema_analysis_tools()
        )
        
        # Attribute Mapping Specialist - specialist agent  
        mapping_specialist = Agent(
            role="Attribute Mapping Specialist",
            goal="Create precise field mappings with confidence scores for migration standardization",
            backstory="""You are a specialist in field mapping with extensive experience in migration 
            data standardization. You excel at resolving ambiguous mappings and providing accurate 
            confidence scores for field relationships.""",
            llm=self.llm,
            memory=self.shared_memory, 
            knowledge=self.knowledge_base,
            verbose=True,
            collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
            tools=self._create_mapping_confidence_tools()
        )
        
        return [field_mapping_manager, schema_analyst, mapping_specialist]
    
    def create_tasks(self, agents, raw_data: List[Dict[str, Any]]):
        """Create hierarchical tasks with manager coordination"""
        manager, schema_analyst, mapping_specialist = agents
        
        headers = list(raw_data[0].keys()) if raw_data else []
        data_sample = raw_data[:5] if raw_data else []
        
        # Planning Task - Manager coordinates overall approach
        planning_task = Task(
            description=f"""Plan comprehensive field mapping strategy for dataset with {len(headers)} fields.
            
            Headers to analyze: {headers}
            Data sample size: {len(data_sample)} records
            
            Create an execution plan that:
            1. Assigns schema analysis priorities
            2. Defines mapping validation criteria  
            3. Establishes confidence thresholds
            4. Plans collaboration between specialists
            
            Use your planning capabilities to coordinate the field mapping crew effectively.""",
            expected_output="Comprehensive field mapping execution plan with agent assignments and success criteria",
            agent=manager,
            tools=[]
        )
        
        # Schema Analysis Task - Deep field understanding
        schema_analysis_task = Task(
            description=f"""Analyze data structure and field semantics for migration mapping.
            
            Headers: {headers}
            Sample data: {data_sample}
            
            Detailed Analysis Requirements:
            1. Identify field types and data patterns
            2. Understand business context of each field
            3. Detect relationships between fields
            4. Flag ambiguous or unclear field meanings
            5. Generate semantic understanding report
            6. Store insights in shared memory for mapping specialist
            
            Collaborate with the mapping specialist by sharing your analysis insights.""",
            expected_output="Comprehensive field analysis report with semantic understanding and relationship mapping",
            agent=schema_analyst,
            context=[planning_task],
            tools=self._create_schema_analysis_tools()
        )
        
        # Field Mapping Task - Precise mapping with confidence
        field_mapping_task = Task(
            description=f"""Create precise mappings from source fields to standard migration attributes.
            
            Source Headers: {headers}
            
            Standard Target Schema:
            - asset_name, asset_id, asset_type
            - environment, business_criticality, owner
            - operating_system, ip_address, cpu_cores, memory_gb
            - version, vendor, license
            
            Mapping Requirements:
            1. Map each source field to best-fit standard attribute
            2. Provide confidence scores (0.0-1.0) for each mapping
            3. Identify unmapped fields requiring human clarification
            4. Validate mappings against knowledge base patterns
            5. Generate mapping dictionary with metadata
            6. Use schema analyst insights from shared memory
            
            Collaborate with schema analyst to leverage field understanding.""",
            expected_output="Complete field mapping dictionary with confidence scores, validation results, and unmapped fields list",
            agent=mapping_specialist,
            context=[schema_analysis_task],
            tools=self._create_mapping_confidence_tools()
        )
        
        return [planning_task, schema_analysis_task, field_mapping_task]
    
    def create_crew(self, raw_data: List[Dict[str, Any]]):
        """Create hierarchical crew with manager coordination"""
        agents = self.create_agents()
        tasks = self.create_tasks(agents, raw_data)
        
        # Use hierarchical process if advanced features available
        process = Process.hierarchical if CREWAI_ADVANCED_AVAILABLE else Process.sequential
        
        crew_config = {
            "agents": agents,
            "tasks": tasks,
            "process": process,
            "verbose": True
        }
        
        # Add advanced features if available
        if CREWAI_ADVANCED_AVAILABLE:
            crew_config.update({
                "manager_llm": self.llm,
                "planning": True,
                "memory": True,
                "knowledge": self.knowledge_base,
                "share_crew": True
            })
        
        logger.info(f"Creating Field Mapping Crew with {process.name if hasattr(process, 'name') else 'sequential'} process")
        return Crew(**crew_config)
    
    def _create_schema_analysis_tools(self):
        """Create tools for schema analysis"""
        # For now, return empty list - tools will be implemented in Task 7
        return []
    
    def _create_mapping_confidence_tools(self):
        """Create tools for mapping confidence scoring"""
        # For now, return empty list - tools will be implemented in Task 7  
        return []

def create_field_mapping_crew(crewai_service, raw_data: List[Dict[str, Any]], 
                             shared_memory=None, knowledge_base=None) -> Crew:
    """Factory function to create enhanced Field Mapping Crew"""
    crew_instance = FieldMappingCrew(crewai_service, shared_memory, knowledge_base)
    return crew_instance.create_crew(raw_data) 