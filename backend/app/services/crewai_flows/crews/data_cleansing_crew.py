"""
Data Cleansing Crew - Quality Assurance Phase
Enhanced implementation with CrewAI best practices:
- Hierarchical management with Data Quality Manager
- Shared memory access to field mapping insights
- Knowledge base integration for data quality standards
- Agent collaboration for comprehensive cleansing
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

class DataCleansingCrew:
    """Enhanced Data Cleansing Crew with CrewAI best practices"""
    
    def __init__(self, crewai_service, shared_memory=None, knowledge_base=None):
        self.crewai_service = crewai_service
        self.llm = getattr(crewai_service, 'llm', None)
        
        # Setup shared memory and knowledge base
        self.shared_memory = shared_memory or self._setup_shared_memory()
        self.knowledge_base = knowledge_base or self._setup_knowledge_base()
        
        logger.info("✅ Data Cleansing Crew initialized with advanced features")
    
    def _setup_shared_memory(self) -> Optional[LongTermMemory]:
        """Setup shared memory to access field mapping insights"""
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
        """Setup knowledge base for data quality standards"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Knowledge base not available - using fallback")
            return None
        
        try:
            return KnowledgeBase(
                sources=[
                    "backend/app/knowledge_bases/data_quality_standards.yaml"
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
        data_quality_manager = Agent(
            role="Data Quality Manager",
            goal="Ensure comprehensive data cleansing and quality validation for migration readiness",
            backstory="""You are a data quality expert with 12+ years managing enterprise data 
            cleansing projects. You excel at coordinating validation and standardization efforts 
            while ensuring data integrity for migration projects.""",
            llm=self.llm,
            memory=self.shared_memory,
            knowledge=self.knowledge_base,
            verbose=True,
            allow_delegation=True,
            max_delegation=2,
            planning=True if CREWAI_ADVANCED_AVAILABLE else False
        )
        
        # Data Validation Expert - specialist agent
        validation_expert = Agent(
            role="Data Validation Expert", 
            goal="Validate data quality using established field mappings and enterprise standards",
            backstory="""You are an expert in data validation with deep knowledge of IT asset data 
            requirements. You excel at identifying data quality issues and implementing validation 
            rules based on field mappings and business requirements.""",
            llm=self.llm,
            memory=self.shared_memory,
            knowledge=self.knowledge_base,
            verbose=True,
            collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
            tools=self._create_validation_tools()
        )
        
        # Data Standardization Specialist - specialist agent  
        standardization_specialist = Agent(
            role="Data Standardization Specialist",
            goal="Standardize data formats and values for consistent migration processing",
            backstory="""You are a specialist in data standardization with extensive experience in 
            normalizing IT asset data. You excel at applying consistent formatting, value 
            standardization, and data transformation for migration projects.""",
            llm=self.llm,
            memory=self.shared_memory, 
            knowledge=self.knowledge_base,
            verbose=True,
            collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
            tools=self._create_standardization_tools()
        )
        
        return [data_quality_manager, validation_expert, standardization_specialist]
    
    def create_tasks(self, agents, cleaned_data: List[Dict[str, Any]], field_mappings: Dict[str, Any]):
        """Create hierarchical tasks with manager coordination"""
        manager, validation_expert, standardization_specialist = agents
        
        data_sample = cleaned_data[:5] if cleaned_data else []
        mapped_fields = field_mappings.get("mappings", {})
        
        # Planning Task - Manager coordinates data quality approach
        planning_task = Task(
            description=f"""Plan comprehensive data cleansing strategy based on field mappings.
            
            Data sample size: {len(cleaned_data)} records
            Mapped fields: {list(mapped_fields.keys())}
            Field mappings confidence: {field_mappings.get('confidence_scores', {})}
            
            Create a data quality plan that:
            1. Prioritizes validation based on field mapping confidence
            2. Defines standardization requirements for each field type
            3. Establishes quality metrics and success criteria
            4. Plans collaboration between validation and standardization specialists
            5. Leverages field mapping insights from shared memory
            
            Use your planning capabilities to coordinate the data cleansing crew effectively.""",
            expected_output="Comprehensive data quality execution plan with validation priorities and standardization requirements",
            agent=manager,
            tools=[]
        )
        
        # Data Validation Task - Quality assessment using field mappings
        validation_task = Task(
            description=f"""Validate data quality using established field mappings and standards.
            
            Data to validate: {len(cleaned_data)} records
            Sample data: {data_sample}
            Field mappings: {mapped_fields}
            Confidence scores: {field_mappings.get('confidence_scores', {})}
            
            Validation Requirements:
            1. Check data completeness for required fields
            2. Validate data formats (IP addresses, dates, etc.)
            3. Verify value ranges and constraints
            4. Identify data inconsistencies and outliers
            5. Assess data quality using field mapping confidence
            6. Generate detailed validation report with quality scores
            7. Store validation insights in shared memory
            
            Collaborate with standardization specialist to share validation findings.""",
            expected_output="Comprehensive data validation report with quality scores, issues identified, and recommendations",
            agent=validation_expert,
            context=[planning_task],
            tools=self._create_validation_tools()
        )
        
        # Data Standardization Task - Format and value normalization
        standardization_task = Task(
            description=f"""Standardize data formats and values for consistent migration processing.
            
            Data to standardize: {len(cleaned_data)} records
            Field mappings: {mapped_fields}
            Validation results: Use insights from validation expert
            
            Standardization Requirements:
            1. Normalize text values (trim, case consistency)
            2. Standardize date and time formats
            3. Format IP addresses consistently
            4. Normalize environment values (prod, staging, dev)
            5. Standardize criticality levels
            6. Apply field-specific transformations based on mappings
            7. Generate standardized dataset with transformation log
            8. Use validation expert insights from shared memory
            
            Collaborate with validation expert to ensure standardization quality.""",
            expected_output="Standardized dataset with transformation log and quality metrics",
            agent=standardization_specialist,
            context=[validation_task],
            tools=self._create_standardization_tools()
        )
        
        return [planning_task, validation_task, standardization_task]
    
    def create_crew(self, cleaned_data: List[Dict[str, Any]], field_mappings: Dict[str, Any]):
        """Create hierarchical crew with manager coordination"""
        agents = self.create_agents()
        tasks = self.create_tasks(agents, cleaned_data, field_mappings)
        
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
        
        logger.info(f"Creating Data Cleansing Crew with {process.name if hasattr(process, 'name') else 'sequential'} process")
        return Crew(**crew_config)
    
    def _create_validation_tools(self):
        """Create tools for data validation"""
        # For now, return empty list - tools will be implemented in Task 7
        return []
    
    def _create_standardization_tools(self):
        """Create tools for data standardization"""
        # For now, return empty list - tools will be implemented in Task 7  
        return []

def create_data_cleansing_crew(crewai_service, cleaned_data: List[Dict[str, Any]], 
                              field_mappings: Dict[str, Any], shared_memory=None, 
                              knowledge_base=None) -> Crew:
    """Factory function to create enhanced Data Cleansing Crew"""
    crew_instance = DataCleansingCrew(crewai_service, shared_memory, knowledge_base)
    return crew_instance.create_crew(cleaned_data, field_mappings)
