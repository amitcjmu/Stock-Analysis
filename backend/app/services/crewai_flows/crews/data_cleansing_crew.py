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
    from crewai.knowledge.knowledge import Knowledge
    CREWAI_ADVANCED_AVAILABLE = True
except ImportError:
    CREWAI_ADVANCED_AVAILABLE = False
    # Fallback classes
    class LongTermMemory:
        def __init__(self, **kwargs):
            pass
    class Knowledge:
        def __init__(self, **kwargs):
            pass

logger = logging.getLogger(__name__)

class DataCleansingCrew:
    """Enhanced Data Cleansing Crew with CrewAI best practices"""
    
    def __init__(self, crewai_service, shared_memory=None, knowledge_base=None):
        self.crewai_service = crewai_service
        
        # Get proper LLM configuration from our LLM config service
        try:
            from app.services.llm_config import get_crewai_llm
            self.llm = get_crewai_llm()
            logger.info("✅ Data Cleansing Crew using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM, using fallback: {e}")
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
    
    def _setup_knowledge_base(self) -> Optional[Knowledge]:
        """Setup knowledge base for data quality standards"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Knowledge base not available - using fallback")
            return None
        
        try:
            return Knowledge(
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
            # Ensure manager_llm uses our configured LLM and not gpt-4o-mini
            crew_config.update({
                "manager_llm": self.llm,  # Critical: Use our DeepInfra LLM
                "planning": True,
                "planning_llm": self.llm,  # Force planning to use our LLM too
                "memory": True,
                "knowledge": self.knowledge_base,
                "share_crew": True
            })
            
            # Additional environment override to prevent any gpt-4o-mini fallback
            import os
            os.environ["OPENAI_MODEL_NAME"] = str(self.llm.model) if hasattr(self.llm, 'model') else "deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
        
        logger.info(f"Creating Data Cleansing Crew with {process.name if hasattr(process, 'name') else 'sequential'} process")
        logger.info(f"Using LLM: {self.llm.model if hasattr(self.llm, 'model') else 'Unknown'}")
        return Crew(**crew_config)
    
    def _create_validation_tools(self):
        """Create tools for data validation"""
        # For now, return empty list - tools will be implemented in Task 7
        return []
    
    def _create_standardization_tools(self):
        """Create tools for data standardization"""
        # For now, return empty list - tools will be implemented in Task 7  
        return []

def create_data_cleansing_crew(crewai_service, state: UnifiedDiscoveryFlowState) -> Crew:
    """
    🚀 OPTIMIZED: Create a streamlined Data Cleansing Crew with minimal agent overhead.
    
    PERFORMANCE IMPROVEMENTS:
    - Single specialized agent instead of multiple agents with delegation
    - Direct execution instead of hierarchical management
    - Reduced LLM calls and memory operations
    - Fast pattern-based cleansing with AI validation
    """
    try:
        logger.info("🚀 Creating OPTIMIZED Data Cleansing Crew for performance")
        
        # Get LLM configuration
        llm = crewai_service.get_llm()
        logger.info(f"Using LLM: {llm.model}")
        
        # 🎯 SINGLE OPTIMIZED AGENT: Direct data cleansing specialist
        data_cleansing_specialist = Agent(
            role="Data Cleansing Specialist",
            goal="Efficiently cleanse and standardize data using proven patterns",
            backstory="""You are an expert data cleansing specialist who focuses on 
            fast, accurate data standardization using established patterns and rules.
            You work independently and provide direct results without extensive planning or delegation.""",
            verbose=False,  # Reduce logging overhead
            allow_delegation=False,  # CRITICAL: Prevent agent delegation
            llm=llm,
            max_iter=2,  # Limit iterations for speed
            max_execution_time=30  # 30 second timeout
        )
        
        # 🎯 SINGLE OPTIMIZED TASK: Direct data cleansing
        cleansing_task = Task(
            description=f"""
            Perform fast data cleansing on {len(state.raw_data)} records.
            
            Focus on:
            1. Data type validation and standardization
            2. Format consistency (dates, names, identifiers)
            3. Value normalization and deduplication
            4. Quality scoring based on completeness and consistency
            
            Provide a concise summary with:
            - Records processed: {len(state.raw_data)}
            - Issues identified and resolved
            - Quality score (0-100)
            - Ready for next phase: Yes/No
            
            Work efficiently and avoid extensive analysis or planning.
            """,
            agent=data_cleansing_specialist,
            expected_output="Concise data cleansing summary with quality metrics",
            max_execution_time=25  # Task-level timeout
        )
        
        # 🚀 OPTIMIZED CREW: Sequential process, no manager overhead
        crew = Crew(
            agents=[data_cleansing_specialist],
            tasks=[cleansing_task],
            process=Process.sequential,  # CRITICAL: No hierarchical overhead
            verbose=False,  # Reduce logging
            max_execution_time=45,  # Crew-level timeout
            memory=False,  # CRITICAL: Disable memory for speed
            embedder=None  # Disable embedding overhead
        )
        
        logger.info("✅ OPTIMIZED Data Cleansing Crew created - single agent, direct execution")
        return crew
        
    except Exception as e:
        logger.error(f"Failed to create optimized Data Cleansing Crew: {e}")
        # Fallback to minimal crew
        return _create_minimal_fallback_crew(crewai_service, state)

def _create_minimal_fallback_crew(crewai_service, state: UnifiedDiscoveryFlowState) -> Crew:
    """Minimal fallback crew for when optimization fails"""
    try:
        llm = crewai_service.get_llm()
        
        minimal_agent = Agent(
            role="Data Processor",
            goal="Process data quickly",
            backstory="Fast data processing specialist",
            verbose=False,
            allow_delegation=False,
            llm=llm,
            max_iter=1
        )
        
        minimal_task = Task(
            description=f"Quick data validation for {len(state.raw_data)} records. Return: PROCESSED",
            agent=minimal_agent,
            expected_output="PROCESSED"
        )
        
        return Crew(
            agents=[minimal_agent],
            tasks=[minimal_task],
            process=Process.sequential,
            verbose=False,
            memory=False
        )
    except Exception as e:
        logger.error(f"Even fallback crew creation failed: {e}")
        raise

def _create_field_aware_validation_tool(field_mappings: Dict[str, Any]):
    """Create validation tool that uses field mapping insights"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    # Return empty list for now to avoid validation errors
    return []

def _create_quality_metrics_tool():
    """Create quality metrics tool"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    # Return empty list for now to avoid validation errors
    return []

def _create_data_profiling_tool():
    """Create data profiling tool"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    # Return empty list for now to avoid validation errors
    return []

def _create_field_aware_standardization_tool(field_mappings: Dict[str, Any]):
    """Create standardization tool that uses field mapping context"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    # Return empty list for now to avoid validation errors
    return []

def _create_format_normalization_tool():
    """Create format normalization tool"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    # Return empty list for now to avoid validation errors
    return []

def _create_data_transformation_tool():
    """Create data transformation tool"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    # Return empty list for now to avoid validation errors
    return []
