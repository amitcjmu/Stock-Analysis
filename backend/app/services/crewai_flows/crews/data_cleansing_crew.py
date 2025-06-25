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

# Import state model for type hints
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

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
        
        # 🚀 PERFORMANCE FIX: Single agent, no delegation, memory disabled
        data_quality_manager = Agent(
            role="Data Quality Specialist",
            goal="Process and validate data quality efficiently without delegation",
            backstory="""You are a data quality expert who processes data directly and efficiently. 
            You provide comprehensive data cleansing results without requiring additional agents or conversations.""",
            llm=self.llm,
            memory=False,  # DISABLE MEMORY - Prevents APIStatusError
            verbose=True,
            allow_delegation=False,  # DISABLE DELEGATION - Prevents agent conversations
            max_iter=1,  # LIMIT ITERATIONS - Prevents infinite loops
            max_execution_time=30  # 30 SECOND TIMEOUT
        )
        
        return [data_quality_manager]  # SINGLE AGENT PATTERN
    
    def create_tasks(self, agents, cleaned_data: List[Dict[str, Any]], field_mappings: Dict[str, Any]):
        """Create single task for direct processing"""
        manager = agents[0]  # SINGLE AGENT PATTERN
        
        data_sample = cleaned_data[:5] if cleaned_data else []
        mapped_fields = field_mappings.get("mappings", {})
        
        # 🚀 SINGLE TASK - Direct data processing without delegation
        data_processing_task = Task(
            description=f"""Process and validate data quality directly for {len(cleaned_data)} records.
            
            Data sample: {data_sample}
            Field mappings: {mapped_fields}
            Confidence scores: {field_mappings.get('confidence_scores', {})}
            
            Complete the following in a single response:
            1. Validate data completeness and format consistency
            2. Standardize field values and formats
            3. Generate quality metrics and scores
            4. Provide final cleansed dataset
            
            Provide results in JSON format with:
            - validation_results: quality scores and issues
            - standardized_data: processed records
            - quality_metrics: completion, consistency, accuracy scores""",
            expected_output="JSON with validation results, standardized data, and quality metrics",
            agent=manager
        )
        
        return [data_processing_task]  # SINGLE TASK PATTERN
    
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
