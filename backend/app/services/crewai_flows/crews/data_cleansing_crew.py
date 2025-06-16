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

def create_data_cleansing_crew(crewai_service, raw_data: List[Dict[str, Any]], 
                              field_mappings: Dict[str, Any], shared_memory=None) -> Crew:
    """
    Create enhanced Data Cleansing Crew with shared memory integration
    Uses field mapping insights from shared memory to improve data quality validation
    """
    
    # Enhanced with shared memory from field mapping crew
    if shared_memory:
        logger.info("🧠 Data Cleansing Crew accessing field mapping insights from shared memory")
    
    try:
        # Data Quality Manager - Enhanced with field mapping context
        data_quality_manager = Agent(
            role="Data Quality Manager", 
            goal="Orchestrate comprehensive data cleansing using field mapping insights from shared memory",
            backstory="""Senior data quality architect with 12+ years managing enterprise data cleansing projects. 
            Expert in leveraging field mapping intelligence to optimize data validation and standardization processes.
            Capable of coordinating multiple specialists to achieve exceptional data quality standards.""",
            llm=crewai_service.llm,
            manager=True,
            delegation=True,
            max_delegation=2,
            memory=shared_memory,  # Access field mapping insights
            planning=True,
            verbose=True,
            step_callback=lambda step: logger.info(f"Data Quality Manager: {step}")
        )
        
        # Data Validation Expert - Enhanced with field mapping intelligence
        validation_expert = Agent(
            role="Data Validation Expert",
            goal="Validate data quality using field mapping insights and established standards",
            backstory="""Expert in data validation with deep knowledge of IT asset data requirements. 
            Specializes in using field mapping intelligence to create targeted validation rules and identify quality issues.
            Skilled in cross-referencing field semantics to ensure data integrity.""",
            llm=crewai_service.llm,
            memory=shared_memory,  # Access shared insights
            collaboration=True,
            verbose=True,
            tools=[
                _create_field_aware_validation_tool(field_mappings),
                _create_quality_metrics_tool(),
                _create_data_profiling_tool()
            ]
        )
        
        # Data Standardization Specialist - Enhanced with field context
        standardization_specialist = Agent(
            role="Data Standardization Specialist",
            goal="Standardize data formats using field mapping context for consistent processing",
            backstory="""Specialist in data standardization with expertise in normalizing IT asset data. 
            Expert in applying field-specific standardization rules based on semantic understanding from field mappings.
            Capable of transforming diverse data formats into consistent, analysis-ready structures.""",
            llm=crewai_service.llm,
            memory=shared_memory,  # Access field context
            collaboration=True,
            verbose=True,
            tools=[
                _create_field_aware_standardization_tool(field_mappings),
                _create_format_normalization_tool(),
                _create_data_transformation_tool()
            ]
        )
        
        # Enhanced planning task that leverages field mapping insights
        planning_task = Task(
            description=f"""
            Plan comprehensive data cleansing strategy leveraging field mapping insights.
            
            SHARED MEMORY CONTEXT:
            - Access field mapping results from previous crew execution
            - Use field semantic understanding for targeted validation
            - Apply field-specific cleansing rules based on data types and meanings
            
            PLANNING REQUIREMENTS:
            1. Review field mappings: {list(field_mappings.get('mappings', {}).keys())}
            2. Identify high-confidence mappings for priority cleansing
            3. Plan validation approach for unmapped fields
            4. Coordinate validation and standardization specialists
            5. Set quality targets based on field criticality
            
            DELIVERABLE: Comprehensive cleansing execution plan with specialist assignments
            """,
            expected_output="Data cleansing execution plan with field-aware validation strategy and specialist task assignments",
            agent=data_quality_manager,
            context=[],
            tools=[]
        )
        
        # Field-aware validation task
        validation_task = Task(
            description=f"""
            Execute comprehensive data validation using field mapping intelligence.
            
            FIELD MAPPING INSIGHTS:
            - Mapped fields: {field_mappings.get('mappings', {})}
            - Confidence scores: {field_mappings.get('confidence_scores', {})}
            - Unmapped fields: {field_mappings.get('unmapped_fields', [])}
            
            VALIDATION REQUIREMENTS:
            1. Validate mapped fields according to their semantic meaning
            2. Apply field-specific validation rules (e.g., IP addresses, dates, criticality levels)
            3. Flag data quality issues in high-confidence mappings
            4. Generate quality metrics for each mapped field
            5. Assess data completeness and consistency
            6. Store validation insights in shared memory for inventory building crew
            
            COLLABORATION: Work with standardization specialist to ensure validation aligns with transformation needs.
            """,
            expected_output="Comprehensive validation report with field-specific quality metrics and data issue identification",
            agent=validation_expert,
            context=[planning_task],
            collaboration=[standardization_specialist],
            tools=[
                _create_field_aware_validation_tool(field_mappings),
                _create_quality_metrics_tool()
            ]
        )
        
        # Field-aware standardization task
        standardization_task = Task(
            description=f"""
            Execute data standardization using field mapping context for optimal transformation.
            
            FIELD CONTEXT USAGE:
            - Apply standardization rules based on field semantic meaning
            - Transform data according to mapped field requirements
            - Standardize formats for critical asset attributes
            - Preserve data relationships identified in field mappings
            
            STANDARDIZATION TARGETS:
            1. Asset names: Clean and standardize naming conventions
            2. Asset types: Normalize classification values
            3. Environments: Standardize environment designations
            4. Criticality levels: Normalize business criticality scales
            5. Technical attributes: Format CPU, memory, storage values consistently
            6. Network attributes: Standardize IP addresses and network identifiers
            
            MEMORY STORAGE: Store standardization patterns in shared memory for asset classification crew.
            """,
            expected_output="Standardized dataset with consistent formats and field-aware transformations",
            agent=standardization_specialist,
            context=[validation_task],
            collaboration=[validation_expert],
            tools=[
                _create_field_aware_standardization_tool(field_mappings),
                _create_format_normalization_tool()
            ]
        )
        
        # Create crew with hierarchical process and shared memory
        crew = Crew(
            agents=[data_quality_manager, validation_expert, standardization_specialist],
            tasks=[planning_task, validation_task, standardization_task],
            process=Process.hierarchical,
            manager_llm=crewai_service.llm,
            planning=True,
            memory=True,
            verbose=True,
            share_crew=True  # Enable cross-crew collaboration
        )
        
        logger.info("✅ Enhanced Data Cleansing Crew created with field mapping intelligence")
        return crew
        
    except Exception as e:
        logger.error(f"Failed to create enhanced Data Cleansing Crew: {e}")
        # Fallback to basic crew
        return _create_fallback_data_cleansing_crew(crewai_service, raw_data)

def _create_fallback_data_cleansing_crew(crewai_service, raw_data: List[Dict[str, Any]]) -> Crew:
    """Create fallback data cleansing crew with basic functionality"""
    try:
        crew_instance = DataCleansingCrew(crewai_service)
        return crew_instance.create_crew(raw_data, {})
    except Exception as e:
        logger.error(f"Failed to create fallback crew: {e}")
        # Create minimal crew
        agent = Agent(
            role="Data Cleansing Agent",
            goal="Clean and standardize data",
            backstory="Basic data cleansing agent",
            llm=crewai_service.llm
        )
        task = Task(
            description="Clean and standardize the provided data",
            expected_output="Cleaned data",
            agent=agent
        )
        return Crew(agents=[agent], tasks=[task])

def _create_field_aware_validation_tool(field_mappings: Dict[str, Any]):
    """Create validation tool that uses field mapping insights"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    return None

def _create_quality_metrics_tool():
    """Create quality metrics tool"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    return None

def _create_data_profiling_tool():
    """Create data profiling tool"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    return None

def _create_field_aware_standardization_tool(field_mappings: Dict[str, Any]):
    """Create standardization tool that uses field mapping context"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    return None

def _create_format_normalization_tool():
    """Create format normalization tool"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    return None

def _create_data_transformation_tool():
    """Create data transformation tool"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    return None
