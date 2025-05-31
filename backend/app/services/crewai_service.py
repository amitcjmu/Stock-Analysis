"""
CrewAI service integration for AI-powered migration analysis.
Provides truly agentic AI agents with memory, learning, and adaptive capabilities.
"""

import json
import logging
import asyncio
import concurrent.futures
import uuid
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from crewai import Task, LLM
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logging.warning("CrewAI not available. AI features will use placeholder logic.")

from app.core.config import settings
from app.services.memory import AgentMemory
from app.services.agents import AgentManager
from app.services.analysis import IntelligentAnalyzer, PlaceholderAnalyzer
from app.services.feedback import FeedbackProcessor
from app.services.agent_monitor import agent_monitor, TaskStatus
from app.services.tools.sixr_tools import get_sixr_tools

logger = logging.getLogger(__name__)

# Set up proper environment for CrewAI with local embeddings
def configure_crewai_environment():
    """Configure environment variables for CrewAI to work with DeepInfra and local embeddings."""
    
    # Set CHROMA_OPENAI_API_KEY to a placeholder if not set
    # CrewAI checks for this but we'll use local embeddings instead
    if not os.getenv('CHROMA_OPENAI_API_KEY'):
        os.environ['CHROMA_OPENAI_API_KEY'] = 'not_needed_using_local_embeddings'
        logging.info("Set CHROMA_OPENAI_API_KEY placeholder for local embeddings")
    
    # Configure Chroma to use local embeddings instead of OpenAI
    os.environ['CHROMA_CLIENT_TYPE'] = 'local'
    os.environ['CHROMA_PERSIST_DIRECTORY'] = './data/chroma_db'
    
    # Ensure we're using DeepInfra for the main LLM
    deepinfra_key = os.getenv('DEEPINFRA_API_KEY')
    if deepinfra_key:
        os.environ['LITELLM_API_KEY'] = deepinfra_key
        logging.info("Configured LiteLLM to use DeepInfra API key")
    
    # Set embedding model to use local sentence transformers instead of OpenAI
    os.environ['EMBEDDING_MODEL'] = 'sentence-transformers/all-MiniLM-L6-v2'
    os.environ['EMBEDDING_PROVIDER'] = 'local'
    
    logging.info("CrewAI environment configured for DeepInfra + local embeddings")

# Configure environment before importing CrewAI
configure_crewai_environment()

class CrewAIService:
    """Service for managing truly agentic CrewAI agents with memory and learning."""
    
    def __init__(self):
        self.llm = None
        self.memory = AgentMemory()
        self.agent_manager = None
        self.analyzer = IntelligentAnalyzer(self.memory)
        self.feedback_processor = FeedbackProcessor(self.memory)
        
        # Start agent monitoring
        agent_monitor.start_monitoring()
        
        if CREWAI_AVAILABLE and settings.DEEPINFRA_API_KEY and settings.CREWAI_ENABLED:
            self._initialize_llm()
            self.agent_manager = AgentManager(self.llm)
        else:
            if not settings.CREWAI_ENABLED:
                logger.info("CrewAI service disabled by configuration - using placeholder mode")
            else:
                logger.warning("CrewAI service initialized in placeholder mode - DeepInfra API key required")
        
        # Initialize field mapping tool for agents
        try:
            from app.services.field_mapper_modular import field_mapper
            self.field_mapping_tool = field_mapper
            logger.info("Field mapping tool initialized for agents")
        except ImportError as e:
            logger.warning(f"Field mapping tool not available: {e}")
            self.field_mapping_tool = None

    def is_available(self) -> bool:
        """Check if the CrewAI service is available and properly initialized."""
        return CREWAI_AVAILABLE and self.llm is not None and self.agent_manager is not None
    
    def _initialize_llm(self):
        """Initialize the LiteLLM configuration for DeepInfra."""
        try:
            if not settings.DEEPINFRA_API_KEY:
                logger.error("DeepInfra API key is required but not provided")
                self.llm = None
                return
            
            # Initialize LiteLLM for DeepInfra with optimized settings for JSON output
            self.llm = LLM(
                model="deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                api_key=settings.DEEPINFRA_API_KEY,
                temperature=0.0,  # Zero temperature for deterministic, structured output
                max_tokens=1500,  # Adequate tokens for complete JSON responses
                top_p=0.1,        # Low top_p for more focused output
                frequency_penalty=0.0,  # No penalty to avoid incomplete responses
                presence_penalty=0.0    # No penalty to avoid incomplete responses
            )
            
            logger.info(f"Initialized LiteLLM for DeepInfra with JSON-optimized settings: {self.llm.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LiteLLM: {e}")
            self.llm = None
    
    def reinitialize_with_fresh_llm(self) -> None:
        """Reinitialize the service with a fresh LLM instance to avoid any caching issues."""
        if not CREWAI_AVAILABLE or not settings.DEEPINFRA_API_KEY:
            logger.warning("Cannot reinitialize - CrewAI not available or API key missing")
            return
        
        logger.info("Reinitializing CrewAI service with fresh LiteLLM instance")
        
        # Create a fresh LiteLLM instance with JSON-optimized settings
        fresh_llm = LLM(
            model="deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            api_key=settings.DEEPINFRA_API_KEY,
            temperature=0.0,  # Zero temperature for deterministic, structured output
            max_tokens=1500,  # Adequate tokens for complete JSON responses
            top_p=0.1,        # Low top_p for more focused output
            frequency_penalty=0.0,  # No penalty to avoid incomplete responses
            presence_penalty=0.0    # No penalty to avoid incomplete responses
        )
        
        # Update the LLM
        self.llm = fresh_llm
        
        # Reinitialize agent manager with fresh LLM
        if self.agent_manager:
            self.agent_manager.reinitialize_with_fresh_llm(fresh_llm)
        else:
            self.agent_manager = AgentManager(fresh_llm)
        
        logger.info("Successfully reinitialized CrewAI service with fresh LiteLLM")
    
    @property
    def agents(self):
        """Get agents from agent manager."""
        return self.agent_manager.agents if self.agent_manager else {}
    
    @property
    def crews(self):
        """Get crews from agent manager."""
        return self.agent_manager.crews if self.agent_manager else {}
    
    async def analyze_asset_6r_strategy(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze an asset and recommend 6R migration strategy."""
        if not CREWAI_AVAILABLE or not self.agents.get('migration_strategist'):
            return PlaceholderAnalyzer.placeholder_6r_analysis(asset_data)
        
        try:
            task = Task(
                description=f"""
                Analyze the following infrastructure asset and recommend the optimal 6R migration strategy:
                
                Asset Details:
                - Name: {asset_data.get('name')}
                - Type: {asset_data.get('asset_type')}
                - OS: {asset_data.get('operating_system')} {asset_data.get('os_version')}
                - CPU Cores: {asset_data.get('cpu_cores')}
                - Memory: {asset_data.get('memory_gb')} GB
                - Storage: {asset_data.get('storage_gb')} GB
                - Environment: {asset_data.get('environment')}
                - Business Criticality: {asset_data.get('business_criticality')}
                - Dependencies: {len(asset_data.get('dependencies', []))} dependencies
                
                Provide a detailed analysis including:
                1. Recommended 6R strategy with rationale
                2. Alternative strategies with pros/cons
                3. Risk assessment (low/medium/high/critical)
                4. Estimated complexity (low/medium/high)
                5. Migration priority (1-10)
                6. Key considerations and recommendations
                
                Return the analysis in JSON format.
                """,
                agent=self.agents['migration_strategist'],
                expected_output="JSON analysis with 6R strategy recommendation, risk assessment, and migration planning details"
            )
            
            result = await self._execute_task_async(task)
            return self._parse_ai_response(result)
            
        except Exception as e:
            logger.error(f"Error in 6R analysis: {e}")
            return PlaceholderAnalyzer.placeholder_6r_analysis(asset_data)
    
    async def assess_migration_risks(self, migration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risks for a migration project."""
        if not CREWAI_AVAILABLE or not self.agents.get('risk_assessor'):
            return PlaceholderAnalyzer.placeholder_risk_assessment(migration_data)
        
        try:
            task = Task(
                description=f"""
                Perform a comprehensive risk assessment for this migration project:
                
                Migration Details:
                - Total Assets: {migration_data.get('total_assets', 0)}
                - Source Environment: {migration_data.get('source_environment')}
                - Target Environment: {migration_data.get('target_environment')}
                - Timeline: {migration_data.get('timeline_days', 90)} days
                - Business Criticality: {migration_data.get('business_criticality')}
                
                Identify and assess:
                1. Technical risks and mitigation strategies
                2. Business continuity risks
                3. Security and compliance risks
                4. Resource and timeline risks
                5. Dependency-related risks
                6. Overall risk level and recommendations
                
                Return the assessment in JSON format.
                """,
                agent=self.agents['risk_assessor'],
                expected_output="JSON risk assessment with identified risks, mitigation strategies, and overall risk level"
            )
            
            result = await self._execute_task_async(task)
            return self._parse_ai_response(result)
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            return PlaceholderAnalyzer.placeholder_risk_assessment(migration_data)
    
    async def optimize_wave_plan(self, assets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize migration wave planning based on assets and dependencies."""
        if not CREWAI_AVAILABLE or not self.agents.get('wave_planner'):
            return PlaceholderAnalyzer.placeholder_wave_plan(assets_data)
        
        try:
            task = Task(
                description=f"""
                Create an optimized migration wave plan for {len(assets_data)} assets:
                
                Consider:
                1. Asset dependencies and relationships
                2. Business criticality and priorities
                3. Technical complexity and risk levels
                4. Resource constraints and parallel execution
                5. Minimize business disruption
                
                Create 3-5 migration waves with:
                - Wave sequencing rationale
                - Asset assignments per wave
                - Timeline recommendations
                - Risk mitigation strategies
                - Success criteria
                
                Return the wave plan in JSON format.
                """,
                agent=self.agents['wave_planner'],
                expected_output="JSON wave plan with 3-5 migration waves, asset assignments, and timeline recommendations"
            )
            
            result = await self._execute_task_async(task)
            return self._parse_ai_response(result)
            
        except Exception as e:
            logger.error(f"Error in wave planning: {e}")
            return PlaceholderAnalyzer.placeholder_wave_plan(assets_data)

    async def analyze_cmdb_data(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Truly agentic CMDB data analysis with memory and learning."""
        if not CREWAI_AVAILABLE or not self.agents.get('cmdb_analyst'):
            logger.info("CrewAI not available, using intelligent placeholder analysis")
            return self.analyzer.intelligent_placeholder_analysis(cmdb_data)
        
        try:
            logger.info(f"Starting CrewAI analysis for {cmdb_data.get('filename', 'unknown')}")
            
            # Add timeout for CrewAI execution
            async def run_crewai_analysis():
                return await self._run_crewai_analysis_internal(cmdb_data)
            
            # Run with timeout
            try:
                analysis = await asyncio.wait_for(run_crewai_analysis(), timeout=30.0)
                logger.info("CrewAI analysis completed successfully")
                return analysis
            except asyncio.TimeoutError:
                logger.warning("CrewAI analysis timed out after 30 seconds, falling back to placeholder")
                return self.analyzer.intelligent_placeholder_analysis(cmdb_data)
                
        except Exception as e:
            logger.error(f"Error in agentic CMDB analysis: {e}")
            # Fallback to enhanced placeholder with memory
            return self.analyzer.intelligent_placeholder_analysis(cmdb_data)
    
    async def _run_crewai_analysis_internal(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to run CrewAI analysis."""
        try:
            # Get relevant past experiences
            filename = cmdb_data.get('filename', '')
            relevant_experiences = self.memory.get_relevant_experiences(filename)
            
            # Record this analysis attempt
            self.memory.add_experience("analysis_attempt", {
                "filename": filename,
                "timestamp": datetime.utcnow().isoformat(),
                "data_structure": cmdb_data.get('structure', {})
            })
            
            # Get available columns for field mapping analysis
            available_columns = []
            if cmdb_data.get('structure', {}).get('columns'):
                available_columns = cmdb_data['structure']['columns']
            elif cmdb_data.get('sample_data') and len(cmdb_data['sample_data']) > 0:
                available_columns = list(cmdb_data['sample_data'][0].keys())
            
            # Use field mapping tool to analyze columns
            field_analysis = self.field_mapping_tool.agent_analyze_columns(available_columns, "server")
            mapping_context = self.field_mapping_tool.agent_get_mapping_context()
            
            # Enhanced pattern analysis using data content
            pattern_analysis = {}
            if cmdb_data.get('sample_data') and len(cmdb_data['sample_data']) > 0:
                # Analyze column patterns from sample data
                sample_rows = []
                for record in cmdb_data['sample_data'][:10]:  # Analyze first 10 rows
                    row = [record.get(col, '') for col in available_columns]
                    sample_rows.append(row)
                
                pattern_analysis = self.field_mapping_tool.analyze_columns(
                    available_columns, "server"
                )
            
            # Create agentic task with enhanced field mapping intelligence
            task = Task(
                description=f"""
                As a Senior Data Quality Analyst, analyze this CMDB export data for DATA CLEANSING purposes.
                Focus on providing CATEGORIZED, BULK-ACTIONABLE data quality issues.

                CURRENT ANALYSIS:
                File: {cmdb_data.get('filename')}
                Data Structure: {cmdb_data.get('structure')}
                Sample Records: {cmdb_data.get('sample_data', [])}
                Available Columns: {available_columns}
                
                FIELD MAPPING INTELLIGENCE:
                Field Analysis: {field_analysis}
                Mapping Context: {mapping_context}
                Pattern Analysis: {pattern_analysis}
                
                DATA CLEANSING FOCUS AREAS (PRIORITIZE THESE):
                
                1. MISSING DATA ISSUES:
                   - Identify fields with null/empty values that are critical for migration
                   - Focus on: environment, department, asset_type, hostname
                   - Suggest bulk values based on naming patterns and context
                   - Example issue: "50 assets missing environment classification"
                
                2. DUPLICATE RECORDS:
                   - Find assets with identical hostnames, IPs, or names
                   - Suggest consolidation or unique identifier addition
                   - Example issue: "15 duplicate hostnames requiring deduplication"
                
                3. FORMAT STANDARDIZATION:
                   - Abbreviated values that need expansion (DB → Database, SRV → Server)
                   - Inconsistent capitalization (production vs Production vs PRODUCTION)
                   - Non-standard asset types that need normalization
                   - Example issue: "25 assets with abbreviated asset types"
                
                4. INCORRECT FIELD MAPPINGS:
                   - Values in wrong fields or inconsistent formats
                   - IP addresses in wrong format, invalid environment names
                   - Example issue: "12 assets with non-standard environment values"
                
                BULK OPERATION REQUIREMENTS:
                - Group similar issues together (all missing environment issues)
                - Provide specific counts of affected assets
                - Suggest standardized values for bulk application
                - Focus on migration-critical fields only
                
                ANALYSIS WORKFLOW:
                1. Use pattern_analysis results to understand actual field mappings
                2. Only report fields as missing if NO suitable mapping exists
                3. Count actual occurrences of each issue type
                4. Provide bulk-applicable suggestions
                5. Categorize issues for efficient UI grouping
                
                CRITICAL OUTPUT FORMAT REQUIREMENTS:
                Return ONLY a valid JSON object with these specific fields for data cleansing:
                
                {{
                    "asset_type_detected": "server|application|database|mixed",
                    "confidence_level": 0.85,
                    "data_quality_score": 75,
                    "issues": [
                        "Missing environment data for 23 assets",
                        "Found 8 duplicate hostnames requiring deduplication", 
                        "15 assets have abbreviated asset types (DB, SRV)",
                        "Inconsistent capitalization in 12 department fields"
                    ],
                    "recommendations": [
                        "Bulk assign Production environment to assets with 'prod' in hostname",
                        "Expand abbreviated asset types: DB→Database, SRV→Server", 
                        "Standardize department capitalization to title case",
                        "Add instance numbers to duplicate hostnames"
                    ],
                    "missing_fields_relevant": ["Business_Owner", "Criticality"],
                    "migration_readiness": "requires_cleansing|ready|needs_major_work",
                    "bulk_suggestions": {{
                        "missing_environment": "Production",
                        "missing_department": "Information Technology",
                        "abbreviation_expansions": {{"DB": "Database", "SRV": "Server"}},
                        "capitalization_standard": "title_case"
                    }},
                    "issue_categories": {{
                        "missing_data": 23,
                        "duplicates": 8, 
                        "format_standardization": 15,
                        "incorrect_mappings": 12
                    }}
                }}
                
                Return only the JSON object above with your analysis results. No other text.
                """,
                agent=self.agents['cmdb_analyst'],
                expected_output="Valid JSON analysis focused on categorized data quality issues for bulk operations"
            )
            
            # Execute with simplified crew (no memory to avoid OpenAI issues)
            from crewai import Crew, Process
            
            # Create a simple crew without memory
            simple_crew = Crew(
                agents=[self.agents['cmdb_analyst']],
                tasks=[task],
                process=Process.sequential,
                verbose=False,  # Disable verbose to reduce overhead
                memory=False    # CRITICAL: Disable memory to avoid OpenAI API calls
            )
            
            # Run crew execution in thread pool to avoid blocking
            def run_crew():
                return simple_crew.kickoff()
            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, run_crew)
            
            # Parse and enhance the result
            analysis = self._parse_ai_response(str(result))
            
            # Record successful analysis
            self.memory.add_experience("successful_analysis", {
                "filename": filename,
                "result": analysis,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Update learning metrics
            self.memory.update_learning_metrics("total_analyses", 1)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in internal CrewAI analysis: {e}")
            # Fallback to enhanced placeholder with memory
            return self.analyzer.intelligent_placeholder_analysis(cmdb_data)

    async def process_cmdb_data(self, processing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and enhance CMDB data based on AI recommendations."""
        if not CREWAI_AVAILABLE or not self.agents.get('migration_strategist'):
            return PlaceholderAnalyzer.placeholder_cmdb_processing(processing_data)
        
        try:
            task = Task(
                description=f"""
                Process and enhance the following CMDB data:
                
                File: {processing_data.get('filename')}
                Original Data: {len(processing_data.get('original_data', []))} records
                Processed Data: {len(processing_data.get('processed_data', []))} records
                
                Provide recommendations for:
                1. Data standardization and normalization
                2. Missing field population strategies
                3. Asset categorization improvements
                4. Dependency mapping enhancements
                5. Business context enrichment
                6. Migration-specific data preparation
                
                Suggest specific transformations and enrichments that would:
                - Improve migration planning accuracy
                - Enable better 6R strategy recommendations
                - Support dependency analysis
                - Facilitate wave planning
                
                Return processing recommendations in JSON format.
                """,
                agent=self.agents['migration_strategist'],
                expected_output="JSON recommendations for CMDB data processing, standardization, and migration preparation"
            )
            
            result = await self._execute_task_async(task)
            return self._parse_ai_response(result)
            
        except Exception as e:
            logger.error(f"Error in CMDB processing: {e}")
            return PlaceholderAnalyzer.placeholder_cmdb_processing(processing_data)
    
    async def process_user_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Truly agentic feedback processing with persistent learning."""
        if not CREWAI_AVAILABLE or not self.agents.get('learning_agent'):
            return self.feedback_processor.intelligent_feedback_processing(feedback_data)
        
        try:
            filename = feedback_data.get('filename', '')
            user_corrections = feedback_data.get('user_corrections', {})
            asset_type_override = feedback_data.get('asset_type_override')
            
            # Record the user feedback for learning
            self.memory.add_experience("user_feedback", {
                "filename": filename,
                "corrections": user_corrections,
                "asset_type_override": asset_type_override,
                "timestamp": datetime.utcnow().isoformat(),
                "original_analysis": feedback_data.get('original_analysis', {})
            })
            
            # Get all past feedback for pattern recognition
            past_feedback = self.memory.experiences.get("user_feedback", [])
            
            # Use field mapping tool to learn from feedback
            feedback_text = str(user_corrections)
            field_learning_result = self.field_mapping_tool.learn_from_feedback_text(feedback_text, f"feedback_{filename}")
            current_mapping_context = self.field_mapping_tool.agent_get_mapping_context()
            
            # Create learning task with field mapping intelligence
            learning_task = Task(
                description=f"""
                As an AI Learning Specialist with access to field mapping tools, process this user feedback to improve future CMDB analysis accuracy.
                
                CURRENT FEEDBACK:
                File: {filename}
                User Corrections: {user_corrections}
                Asset Type Override: {asset_type_override}
                Original Analysis Issues: {feedback_data.get('original_analysis', {}).get('issues', [])}
                
                FIELD MAPPING LEARNING:
                Field Learning Result: {field_learning_result}
                Current Mapping Context: {current_mapping_context}
                
                LEARNING CONTEXT:
                Total Past Feedback: {len(past_feedback)} instances
                Recent Patterns: {past_feedback[-5:] if past_feedback else "None"}
                
                CRITICAL FIELD MAPPING INSTRUCTIONS:
                1. Use field_mapping_tool to extract and learn field mappings from user feedback
                2. If user mentions fields are "available" or "present" under different names, learn these mappings
                3. Look for patterns like "RAM_GB should map to Memory (GB)" in feedback text
                4. Use the tool to learn mappings like "APPLICATION_OWNER → Business Owner"
                5. Update the persistent field mapping knowledge base
                
                LEARNING OBJECTIVES:
                1. Identify why the original analysis was incorrect
                2. Extract and learn field mapping patterns from user corrections
                3. Update asset type detection rules
                4. Improve field relevance mapping using learned mappings
                5. Enhance future analysis accuracy through persistent learning
                
                SPECIFIC ANALYSIS:
                - If user corrected asset type, understand what indicators were missed
                - If user corrected missing fields, learn the actual field mappings
                - Extract field equivalencies from feedback text (e.g., "RAM_GB is available for memory")
                - Use field_mapping_tool to persist these learnings for future use
                - Identify recurring correction patterns across all feedback
                
                Return detailed learning insights in JSON format:
                {{
                    "learning_applied": true,
                    "patterns_identified": ["specific patterns found"],
                    "field_mappings_learned": ["field mappings extracted and learned"],
                    "knowledge_updates": ["what was learned"],
                    "accuracy_improvements": ["how future analysis will improve"],
                    "confidence_boost": 0.0-1.0,
                    "corrected_analysis": {{
                        "asset_type": "corrected type",
                        "relevant_missing_fields": ["truly missing fields after applying learned mappings"],
                        "updated_recommendations": ["improved recommendations"]
                    }}
                }}
                """,
                agent=self.agents['learning_agent'],
                expected_output="Detailed learning insights and corrected analysis based on user feedback"
            )
            
            # Execute learning with the crew
            crew = self.crews['learning']
            crew.tasks = [learning_task]
            
            # Run crew execution in thread pool to avoid blocking
            def run_learning_crew():
                return crew.kickoff()
            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, run_learning_crew)
            
            # Parse the learning result
            learning_result = self._parse_ai_response(str(result))
            
            # Update learning metrics
            self.memory.update_learning_metrics("user_corrections", 1)
            self.memory.update_learning_metrics("accuracy_improvements", 
                                               learning_result.get('confidence_boost', 0))
            
            # Store the learning patterns for future use
            if learning_result.get('patterns_identified'):
                self.memory.add_experience("learned_patterns", {
                    "patterns": learning_result['patterns_identified'],
                    "source_feedback": filename,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Update dynamic field mappings based on learned patterns
                if self.field_mapping_tool:
                    self.field_mapping_tool.process_feedback_patterns(learning_result['patterns_identified'])
                else:
                    logger.warning("Field mapper not available for pattern processing")
            
            logger.info(f"Processed user feedback and learned new patterns for {filename}")
            return learning_result
            
        except Exception as e:
            logger.error(f"Error in agentic feedback processing: {e}")
            return self.feedback_processor.intelligent_feedback_processing(feedback_data)
    
    async def _execute_task_async(self, task: Any) -> str:
        """Execute a CrewAI task asynchronously with enhanced monitoring."""
        task_id = str(uuid.uuid4())[:8]
        agent_name = getattr(task.agent, 'role', 'unknown_agent')
        description = getattr(task, 'description', 'No description')[:100]
        
        # Start monitoring
        task_exec = agent_monitor.start_task(task_id, agent_name, description)
        
        try:
            # Update status to running
            agent_monitor.update_task_status(task_id, TaskStatus.RUNNING)
            
            # Record thinking phase
            agent_monitor.record_thinking_phase(task_id, "Initializing CrewAI task execution")
            
            # CrewAI doesn't have native async support, so we run it in a thread
            def run_task():
                try:
                    # Record thinking phase
                    agent_monitor.record_thinking_phase(task_id, "Creating temporary crew")
                    
                    # Create a simple crew with just this task - NO MEMORY
                    from crewai import Crew, Process
                    temp_crew = Crew(
                        agents=[task.agent],
                        tasks=[task],
                        process=Process.sequential,
                        verbose=False,  # Disable verbose for debugging
                        memory=False    # CRITICAL: Disable memory to avoid OpenAI API calls
                    )
                    
                    # Record that we're about to call the LLM
                    agent_monitor.record_thinking_phase(task_id, "Starting crew kickoff")
                    call_id = agent_monitor.start_llm_call(
                        task_id, 
                        "crew_kickoff", 
                        len(str(task.description))
                    )
                    
                    # Execute the crew
                    try:
                        result = temp_crew.kickoff()
                        
                        # Complete the LLM call successfully
                        agent_monitor.complete_llm_call(task_id, len(str(result)))
                        
                        # Record final processing phase
                        agent_monitor.record_thinking_phase(task_id, "Processing crew result")
                        
                        return result
                        
                    except Exception as llm_error:
                        # Complete the LLM call with error
                        agent_monitor.complete_llm_call(task_id, 0, str(llm_error))
                        raise llm_error
                    
                except Exception as e:
                    agent_monitor.fail_task(task_id, str(e))
                    raise
            
            # Run the task in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Add timeout to the executor call
                future = loop.run_in_executor(executor, run_task)
                
                # Wait with timeout
                try:
                    result = await asyncio.wait_for(future, timeout=45.0)
                except asyncio.TimeoutError:
                    agent_monitor.fail_task(task_id, "Task execution timed out after 45 seconds")
                    raise asyncio.TimeoutError("CrewAI task execution timed out")
            
            # Complete the task
            result_str = str(result)
            agent_monitor.complete_task(task_id, result_str)
            
            return result_str
            
        except Exception as e:
            logger.error(f"Error executing CrewAI task: {e}")
            if task_id in agent_monitor.active_tasks:
                agent_monitor.fail_task(task_id, str(e))
            return f"Error: {str(e)}"
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response and return structured data with improved JSON extraction and intelligent fallbacks."""
        original_response = response
        
        try:
            # Clean the response string
            response = response.strip()
            
            # Remove common prefixes that agents might add including "Thought:" patterns
            prefixes_to_remove = [
                "Thought:", "Analysis:", "Response:", "Result:", "Output:",
                "Here is the analysis:", "The analysis is:", "Based on the data:",
                "I need to", "Let me", "First", "After analyzing", "I will start by"
            ]
            
            for prefix in prefixes_to_remove:
                if response.startswith(prefix):
                    response = response[len(prefix):].strip()
            
            # ENHANCED: Remove entire thinking/reasoning blocks that some models include
            import re
            
            # Remove "Thought: ... \n\n{JSON}" patterns - common with reasoning models
            thought_pattern = r'Thought:.*?(?=\{)'
            response = re.sub(thought_pattern, '', response, flags=re.DOTALL)
            response = response.strip()
            
            # Remove any text before the first JSON object
            first_brace = response.find('{')
            if first_brace > 0:
                # Check if there's significant text before the JSON (likely reasoning)
                prefix_text = response[:first_brace].strip()
                if len(prefix_text) > 50:  # More than a simple label, likely reasoning
                    response = response[first_brace:]
            
            # Try multiple JSON extraction methods with enhanced patterns
            
            # Method 1: Find the most complete JSON object using balanced braces
            def extract_balanced_json(text):
                """Extract the first balanced JSON object from text."""
                brace_count = 0
                start_idx = -1
                
                for i, char in enumerate(text):
                    if char == '{':
                        if start_idx == -1:
                            start_idx = i
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0 and start_idx != -1:
                            return text[start_idx:i + 1]
                return None
            
            balanced_json = extract_balanced_json(response)
            if balanced_json:
                try:
                    parsed_json = json.loads(balanced_json)
                    if isinstance(parsed_json, dict) and len(parsed_json) > 3:
                        logger.info("Successfully parsed AI response using balanced brace extraction")
                        return self._validate_and_enhance_response(parsed_json)
                except json.JSONDecodeError:
                    pass
            
            # Method 2: Enhanced regex pattern for complete JSON objects
            json_pattern = r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}'
            json_matches = re.findall(json_pattern, response, re.DOTALL)
            
            # Try larger JSON objects first (more likely to be complete)
            json_matches.sort(key=len, reverse=True)
            
            for json_match in json_matches:
                try:
                    parsed_json = json.loads(json_match)
                    if isinstance(parsed_json, dict) and len(parsed_json) > 3:
                        logger.info("Successfully parsed AI response using enhanced regex pattern")
                        return self._validate_and_enhance_response(parsed_json)
                except json.JSONDecodeError:
                    continue
            
            # Method 3: Try parsing the entire cleaned response
            try:
                parsed_json = json.loads(response)
                logger.info("Successfully parsed entire cleaned response as JSON")
                return self._validate_and_enhance_response(parsed_json)
            except json.JSONDecodeError:
                pass
            
            # Method 4: Enhanced JSON cleaning and fixing
            cleaned_response = self._clean_malformed_json(response)
            if cleaned_response:
                try:
                    parsed_json = json.loads(cleaned_response)
                    logger.info("Successfully parsed cleaned JSON response")
                    return self._validate_and_enhance_response(parsed_json)
                except json.JSONDecodeError:
                    pass
            
            # Method 5: Last resort - try to extract key-value pairs manually
            extracted_json = self._extract_json_from_text(response)
            if extracted_json:
                logger.info("Successfully extracted JSON from unstructured text")
                return self._validate_and_enhance_response(extracted_json)
            
            logger.warning(f"All JSON parsing methods failed. Response length: {len(original_response)}")
            logger.warning(f"Cleaned response preview: {response[:300]}...")
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
        
        # Return intelligent fallback based on context
        return self._create_intelligent_fallback(original_response)

    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Last resort: extract JSON-like data from unstructured text."""
        try:
            import re
            
            extracted = {}
            
            # Extract common fields using regex patterns
            patterns = {
                'asset_type_detected': r'asset_type[_\s]*detected["\s]*:[\s]*["\']?([^",\n]+)["\']?',
                'confidence_level': r'confidence[_\s]*level["\s]*:[\s]*([0-9.]+)',
                'data_quality_score': r'data[_\s]*quality[_\s]*score["\s]*:[\s]*([0-9]+)',
                'migration_readiness': r'migration[_\s]*readiness["\s]*:[\s]*["\']?([^",\n]+)["\']?'
            }
            
            for field, pattern in patterns.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    if field in ['confidence_level', 'data_quality_score']:
                        try:
                            extracted[field] = float(value)
                        except ValueError:
                            continue
                    else:
                        extracted[field] = value
            
            # Extract lists (issues, recommendations)
            list_patterns = {
                'issues': r'issues["\s]*:[\s]*\[(.*?)\]',
                'recommendations': r'recommendations["\s]*:[\s]*\[(.*?)\]',
                'missing_fields_relevant': r'missing[_\s]*fields[_\s]*relevant["\s]*:[\s]*\[(.*?)\]'
            }
            
            for field, pattern in list_patterns.items():
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    list_content = match.group(1)
                    # Simple list extraction
                    items = re.findall(r'["\']([^"\']+)["\']', list_content)
                    if items:
                        extracted[field] = items
                    else:
                        extracted[field] = []
                else:
                    extracted[field] = []
            
            # Only return if we extracted substantial data
            if len(extracted) >= 3:
                return extracted
            
        except Exception as e:
            logger.warning(f"Text extraction failed: {e}")
        
        return None
    
    def _clean_malformed_json(self, response: str) -> str:
        """Attempt to clean and fix common JSON formatting issues."""
        try:
            import re
            
            # Remove trailing commas
            response = re.sub(r',\s*}', '}', response)
            response = re.sub(r',\s*]', ']', response)
            
            # Fix missing quotes around keys
            response = re.sub(r'(\w+):', r'"\1":', response)
            
            # Fix single quotes to double quotes
            response = response.replace("'", '"')
            
            # Remove comments
            response = re.sub(r'//.*?\n', '\n', response)
            response = re.sub(r'/\*.*?\*/', '', response, flags=re.DOTALL)
            
            # Find the JSON object bounds more carefully
            brace_count = 0
            start_idx = -1
            end_idx = -1
            
            for i, char in enumerate(response):
                if char == '{':
                    if start_idx == -1:
                        start_idx = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start_idx != -1:
                        end_idx = i + 1
                        break
            
            if start_idx != -1 and end_idx != -1:
                return response[start_idx:end_idx]
                
        except Exception as e:
            logger.warning(f"Error cleaning JSON: {e}")
        
        return None
    
    def _validate_and_enhance_response(self, parsed_json: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance a successfully parsed JSON response."""
        
        # Ensure required fields exist with defaults
        required_fields = {
            "asset_type_detected": "server",
            "confidence_level": 0.8,
            "data_quality_score": 75,
            "issues": [],
            "recommendations": [],
            "missing_fields_relevant": [],
            "migration_readiness": "needs_work"
        }
        
        for field, default_value in required_fields.items():
            if field not in parsed_json:
                parsed_json[field] = default_value
        
        # Validate data types
        if not isinstance(parsed_json.get("confidence_level"), (int, float)):
            parsed_json["confidence_level"] = 0.8
        
        if not isinstance(parsed_json.get("data_quality_score"), (int, float)):
            parsed_json["data_quality_score"] = 75
        
        # Ensure lists are actually lists
        list_fields = ["issues", "recommendations", "missing_fields_relevant"]
        for field in list_fields:
            if not isinstance(parsed_json.get(field), list):
                parsed_json[field] = []
        
        # Add metadata
        parsed_json["parsed"] = True
        parsed_json["timestamp"] = datetime.utcnow().isoformat()
        
        return parsed_json
    
    def _create_intelligent_fallback(self, original_response: str) -> Dict[str, Any]:
        """Create an intelligent fallback response when AI parsing fails."""
        logger.info("Creating intelligent fallback response due to JSON parsing failure")
        
        # Try to extract some information from the raw response
        response_lower = original_response.lower()
        
        # Detect asset type mentions
        asset_type = "server"
        if "application" in response_lower:
            asset_type = "application"
        elif "database" in response_lower:
            asset_type = "database"
        elif "mixed" in response_lower:
            asset_type = "mixed"
        
        # Extract quality indicators
        quality_score = 60  # Default moderate score
        if "high quality" in response_lower or "good quality" in response_lower:
            quality_score = 80
        elif "low quality" in response_lower or "poor quality" in response_lower:
            quality_score = 40
        elif "excellent" in response_lower:
            quality_score = 90
        
        # Extract readiness indicators
        migration_readiness = "needs_work"
        if "ready" in response_lower:
            migration_readiness = "ready"
        elif "insufficient" in response_lower:
            migration_readiness = "insufficient_data"
        
        # INTELLIGENT MISSING FIELDS: Use dynamic field analysis instead of hardcoded values
        missing_fields_relevant = []
        try:
            # Get context from agent memory to understand what fields were analyzed
            from app.services.memory import agent_memory
            recent_experiences = agent_memory.get_recent_experiences(limit=3)
            
            # Look for pattern analysis context
            for exp in recent_experiences:
                if ("pattern_analysis" in exp.get("action", "") or 
                    "field_mapping" in exp.get("action", "")):
                    # Extract missing fields from memory context
                    context = exp.get("context", {})
                    missing_from_analysis = context.get("missing_fields", [])
                    if missing_from_analysis:
                        missing_fields_relevant = missing_from_analysis[:3]  # Limit to 3 most important
                        break
            
            # If no pattern analysis in memory, use intelligent defaults based on asset type
            if not missing_fields_relevant:
                if asset_type == "application":
                    missing_fields_relevant = ["Business Owner", "Criticality"]
                elif asset_type == "server":
                    missing_fields_relevant = ["Business Owner", "Criticality"]  
                elif asset_type == "database":
                    missing_fields_relevant = ["Business Owner", "Criticality", "Database Version"]
                else:
                    missing_fields_relevant = ["Business Owner", "Criticality"]
                    
        except Exception as e:
            logger.warning(f"Could not get intelligent missing fields: {e}")
            # Safe fallback
            missing_fields_relevant = ["Business Owner", "Criticality"]
        
        # Create intelligent fallback
        fallback_response = {
            "asset_type_detected": asset_type,
            "confidence_level": 0.6,  # Lower confidence for fallback
            "data_quality_score": quality_score,
            "issues": ["AI response parsing failed - using fallback analysis"],
            "recommendations": [
                "Review data format and field mappings",
                "Consider providing feedback to improve AI response quality"
            ],
            "missing_fields_relevant": missing_fields_relevant,  # Now using intelligent analysis
            "migration_readiness": migration_readiness,
            "fallback_used": True,
            "parsing_error": "Failed to parse AI response as JSON",
            "ai_response_preview": original_response[:300] if original_response else "No response",
            "parsed": False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Created fallback response with {quality_score}% quality score and {asset_type} asset type")
        logger.info(f"Intelligent missing fields: {missing_fields_relevant}")
        return fallback_response

    def test_json_parsing_improvements(self) -> Dict[str, Any]:
        """Test method to validate improved JSON parsing logic."""
        test_cases = [
            # Case 1: Response with "Thought:" prefix
            'Thought: I will analyze the data carefully and provide a structured response.\n\n{"asset_type_detected": "server", "confidence_level": 0.9, "data_quality_score": 85, "issues": ["Missing data"], "recommendations": ["Clean data"], "missing_fields_relevant": ["Environment"], "migration_readiness": "ready"}',
            
            # Case 2: Response with reasoning before JSON
            'I need to analyze this CMDB data to determine the asset type and quality. After examining the data patterns, I can see that this contains server information.\n\n{"asset_type_detected": "application", "confidence_level": 0.8, "data_quality_score": 75, "issues": [], "recommendations": ["Review mappings"], "missing_fields_relevant": [], "migration_readiness": "needs_work"}',
            
            # Case 3: Malformed JSON
            '{"asset_type_detected": "database", "confidence_level": 0.7, "data_quality_score": 90, "issues": ["Some issue",], "recommendations": ["Fix this"], "missing_fields_relevant": ["Owner"], "migration_readiness": "ready"}',
            
            # Case 4: Clean JSON
            '{"asset_type_detected": "mixed", "confidence_level": 0.95, "data_quality_score": 88, "issues": [], "recommendations": [], "missing_fields_relevant": [], "migration_readiness": "ready"}'
        ]
        
        results = []
        for i, test_response in enumerate(test_cases, 1):
            try:
                parsed = self._parse_ai_response(test_response)
                results.append({
                    f"test_case_{i}": {
                        "success": parsed.get("parsed", False),
                        "asset_type": parsed.get("asset_type_detected", "unknown"),
                        "fallback_used": parsed.get("fallback_used", False)
                    }
                })
            except Exception as e:
                results.append({
                    f"test_case_{i}": {
                        "success": False,
                        "error": str(e),
                        "fallback_used": True
                    }
                })
        
        return {
            "test_results": results,
            "total_tests": len(test_cases),
            "successful_parses": len([r for r in results if list(r.values())[0].get("success", False)]),
            "test_timestamp": datetime.utcnow().isoformat()
        }

    # Enhanced asset inventory management methods
    async def analyze_asset_inventory(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agentic asset inventory analysis using Asset Intelligence Agent.
        Leverages learned field mappings and intelligent pattern recognition.
        """
        if not CREWAI_AVAILABLE or not self.agents.get('asset_intelligence'):
            logger.info("Asset Intelligence Agent not available, using enhanced fallback analysis")
            return self._fallback_asset_analysis(inventory_data)
        
        try:
            logger.info(f"Starting Asset Intelligence analysis for {inventory_data.get('operation', 'general_analysis')}")
            
            # Get field mapping context for intelligent analysis
            field_context = {}
            if self.field_mapping_tool:
                field_context = self.field_mapping_tool.get_mapping_context()
            
            # Create agentic task with asset intelligence
            task = Task(
                description=f"""
                As an Asset Inventory Intelligence Specialist, analyze the following asset inventory data:
                
                Asset Context: {inventory_data}
                Operation: {inventory_data.get('operation', 'general_analysis')}
                Assets Count: {len(inventory_data.get('assets', []))}
                
                Using your advanced AI intelligence and learned field mapping patterns:
                
                1. PATTERN ANALYSIS: Identify intelligent patterns in asset data using content analysis, not hard-coded rules
                   - Analyze field usage patterns across assets using learned mappings: {field_context}
                   - Identify natural asset groupings based on content characteristics
                   - Detect quality consistency patterns for targeted improvements
                
                2. INTELLIGENT CLASSIFICATION: Provide AI-powered classification suggestions
                   - Use learned field mapping intelligence to understand asset characteristics
                   - Base suggestions on content patterns and historical learning
                   - Provide confidence scores for each classification suggestion
                
                3. DATA QUALITY ASSESSMENT: Intelligent quality analysis using field mapping intelligence
                   - Identify quality issues using learned field mapping context
                   - Generate actionable recommendations for bulk quality improvements
                   - Focus on categorized issues suitable for bulk operations
                
                4. BULK OPERATIONS OPTIMIZATION: Plan intelligent bulk operations
                   - Suggest bulk update opportunities based on identified patterns
                   - Optimize operations using learned asset management patterns
                   - Recommend validation strategies for safe bulk operations
                
                5. ACTIONABLE INSIGHTS: Generate prioritized, actionable insights
                   - Focus on insights that leverage learned patterns and field mappings
                   - Provide specific actions users can take to improve inventory management
                   - Include confidence scores and reasoning for each insight
                
                CRITICAL: Base all analysis on AI intelligence and learned patterns, NOT hard-coded heuristics.
                Use the field mapping context to understand data relationships intelligently.
                
                Return structured JSON with intelligent asset inventory insights.
                """,
                agent=self.agents['asset_intelligence'],
                expected_output="JSON analysis with intelligent asset inventory insights, pattern recognition, and actionable recommendations"
            )
            
            # Execute with timeout for reliability
            try:
                result = await asyncio.wait_for(self._execute_task_async(task), timeout=45.0)
                logger.info("Asset Intelligence analysis completed successfully")
                
                # Record successful analysis for learning
                self.memory.add_experience("asset_inventory_analysis", {
                    "operation": inventory_data.get('operation'),
                    "asset_count": len(inventory_data.get('assets', [])),
                    "result_summary": result[:200] if isinstance(result, str) else str(result)[:200],
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return self._parse_ai_response(result)
                
            except asyncio.TimeoutError:
                logger.warning("Asset Intelligence analysis timed out, falling back to enhanced analysis")
                return self._fallback_asset_analysis(inventory_data)
                
        except Exception as e:
            logger.error(f"Asset inventory analysis failed: {e}")
            return self._fallback_asset_analysis(inventory_data)
    
    async def plan_asset_bulk_operation(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered bulk operation planning using Asset Intelligence Agent.
        """
        if not CREWAI_AVAILABLE or not self.agents.get('asset_intelligence'):
            return self._fallback_bulk_operation_planning(operation_data)
        
        try:
            # Get field mapping context for intelligent planning
            field_context = {}
            if self.field_mapping_tool:
                field_context = self.field_mapping_tool.get_mapping_context()
            
            task = Task(
                description=f"""
                As an Asset Inventory Intelligence Specialist, plan the following bulk operation:
                
                Operation Data: {operation_data}
                Asset IDs: {len(operation_data.get('asset_ids', []))} assets
                Proposed Updates: {operation_data.get('proposed_updates', {})}
                
                Using your AI intelligence and field mapping knowledge:
                
                1. INTELLIGENT VALIDATION: Validate the bulk operation using learned patterns
                   - Use field mapping intelligence: {field_context}
                   - Identify potential validation issues based on learned data patterns
                   - Suggest field-level validations using mapping context
                
                2. OPTIMAL STRATEGY: Determine the best execution strategy
                   - Analyze operation complexity and scale
                   - Recommend batch sizes and execution approach
                   - Consider parallel vs sequential execution based on AI analysis
                
                3. RISK ASSESSMENT: AI-powered risk assessment
                   - Identify risks based on operation scope and learned patterns
                   - Suggest mitigation strategies using historical operation insights
                   - Provide confidence levels for risk assessments
                
                4. EXECUTION PLAN: Create detailed execution plan
                   - Optimize execution order using AI intelligence
                   - Plan rollback strategies for safe operation
                   - Include monitoring and validation checkpoints
                
                Base all recommendations on AI analysis and learned patterns, not hard-coded rules.
                
                Return structured JSON with comprehensive bulk operation plan.
                """,
                agent=self.agents['asset_intelligence'],
                expected_output="JSON bulk operation plan with AI-optimized strategy, validation, and execution details"
            )
            
            result = await self._execute_task_async(task)
            return self._parse_ai_response(result)
            
        except Exception as e:
            logger.error(f"Bulk operation planning failed: {e}")
            return self._fallback_bulk_operation_planning(operation_data)
    
    async def classify_assets(self, classification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered asset classification using learned patterns and field mapping intelligence.
        """
        if not CREWAI_AVAILABLE or not self.agents.get('asset_intelligence'):
            return self._fallback_asset_classification(classification_data)
        
        try:
            # Get field mapping context for intelligent classification
            field_context = {}
            if self.field_mapping_tool:
                field_context = self.field_mapping_tool.get_mapping_context()
            
            task = Task(
                description=f"""
                As an Asset Inventory Intelligence Specialist, classify the following assets:
                
                Classification Data: {classification_data}
                Asset IDs: {len(classification_data.get('asset_ids', []))} assets
                Use Learned Patterns: {classification_data.get('use_learned_patterns', True)}
                Confidence Threshold: {classification_data.get('confidence_threshold', 0.8)}
                
                Using your AI intelligence and field mapping knowledge:
                
                1. CONTENT-BASED CLASSIFICATION: Analyze asset content using learned field mappings
                   - Use field mapping intelligence: {field_context}
                   - Analyze asset characteristics based on canonical field mappings
                   - Consider content patterns, not just field names
                
                2. PATTERN-BASED SUGGESTIONS: Use learned patterns for classification
                   - Apply historical classification patterns from similar assets
                   - Use AI pattern recognition to identify asset types
                   - Provide confidence scores based on pattern matching
                
                3. INTELLIGENT GROUPING: Identify natural asset groupings
                   - Group assets with similar characteristics using AI analysis
                   - Suggest bulk classification opportunities
                   - Consider business context and asset relationships
                
                4. CLASSIFICATION VALIDATION: Validate classifications using AI intelligence
                   - Check classification consistency across similar assets
                   - Identify potential classification conflicts or issues
                   - Suggest manual review for low-confidence classifications
                
                Base all classifications on AI analysis and learned patterns, not hard-coded categorization rules.
                
                Return structured JSON with asset classifications, confidence scores, and validation results.
                """,
                agent=self.agents['asset_intelligence'],
                expected_output="JSON asset classification results with AI-generated suggestions, confidence scores, and validation insights"
            )
            
            result = await self._execute_task_async(task)
            return self._parse_ai_response(result)
            
        except Exception as e:
            logger.error(f"Asset classification failed: {e}")
            return self._fallback_asset_classification(classification_data)
    
    async def process_asset_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user feedback from asset management operations to improve AI intelligence.
        """
        if not CREWAI_AVAILABLE or not self.agents.get('learning_agent'):
            return self._fallback_feedback_processing(feedback_data)
        
        try:
            # Get current field mapping context
            field_context = {}
            if self.field_mapping_tool:
                field_context = self.field_mapping_tool.get_mapping_context()
            
            task = Task(
                description=f"""
                As an AI Learning Specialist, process this asset management feedback to improve system intelligence:
                
                Feedback Data: {feedback_data}
                Context: Asset inventory management
                Operation Type: {feedback_data.get('operation_type', 'general')}
                
                Extract learning patterns for system improvement:
                
                1. FIELD MAPPING LEARNING: Extract field mapping insights
                   - Current field mapping context: {field_context}
                   - Identify new field variations mentioned in feedback
                   - Learn field mapping corrections from user input
                   - Update field mapping intelligence based on user corrections
                
                2. ASSET CLASSIFICATION LEARNING: Improve classification intelligence
                   - Extract asset classification corrections from feedback
                   - Learn new classification patterns from user input
                   - Update asset type recognition based on user corrections
                
                3. DATA QUALITY LEARNING: Enhance quality assessment
                   - Learn from data quality feedback and corrections
                   - Identify new quality patterns from user observations
                   - Update quality assessment criteria based on feedback
                
                4. BULK OPERATIONS LEARNING: Optimize bulk operation strategies
                   - Learn from bulk operation outcomes and user feedback
                   - Identify successful operation patterns
                   - Update bulk operation planning based on user experiences
                
                5. USER WORKFLOW LEARNING: Understand user preferences
                   - Identify user workflow patterns from feedback
                   - Learn user preferences for asset management operations
                   - Update recommendations based on user behavior patterns
                
                Use the field mapping tool to learn and persist new mappings discovered in feedback.
                Apply learned insights to improve future asset management operations.
                
                Return structured JSON with learning insights and applied improvements.
                """,
                agent=self.agents['learning_agent'],
                expected_output="JSON learning patterns for asset management enhancement with applied improvements"
            )
            
            result = await self._execute_task_async(task)
            
            # Apply learned insights to improve future operations
            await self._apply_asset_learning_insights(result)
            
            # Record learning activity
            self.memory.add_experience("asset_feedback_processing", {
                "feedback_type": feedback_data.get('operation_type'),
                "learning_summary": str(result)[:200] if isinstance(result, str) else str(result)[:200],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return self._parse_ai_response(result)
            
        except Exception as e:
            logger.error(f"Asset feedback processing failed: {e}")
            return self._fallback_feedback_processing(feedback_data)
    
    # Enhanced fallback methods for asset management
    def _fallback_asset_analysis(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced fallback asset analysis when AI agents are not available."""
        assets = inventory_data.get('assets', [])
        operation = inventory_data.get('operation', 'general_analysis')
        
        # Basic intelligent analysis using available data
        analysis = {
            "status": "completed_fallback",
            "operation": operation,
            "asset_count": len(assets),
            "patterns": self._basic_pattern_analysis(assets),
            "insights": self._basic_asset_insights(assets, operation),
            "recommendations": self._basic_asset_recommendations(assets),
            "quality_assessment": self._basic_quality_assessment(assets),
            "fallback_mode": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return analysis
    
    def _fallback_bulk_operation_planning(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback bulk operation planning."""
        asset_ids = operation_data.get('asset_ids', [])
        updates = operation_data.get('proposed_updates', {})
        
        return {
            "status": "planned_fallback",
            "asset_count": len(asset_ids),
            "updates": updates,
            "strategy": {
                "approach": "batch_update",
                "batch_size": min(50, len(asset_ids)),
                "validation_required": True
            },
            "risk_assessment": {
                "overall_risk": "medium",
                "mitigation": "Use staged execution with validation"
            },
            "fallback_mode": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _fallback_asset_classification(self, classification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback asset classification."""
        asset_ids = classification_data.get('asset_ids', [])
        
        return {
            "status": "classified_fallback",
            "asset_count": len(asset_ids),
            "classifications": [],
            "confidence": 0.5,
            "method": "fallback_classification",
            "recommendation": "Use AI classification when available for better results",
            "fallback_mode": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _apply_asset_learning_insights(self, learning_result: Any) -> None:
        """Apply learned insights to improve asset management capabilities."""
        try:
            if isinstance(learning_result, str):
                # Try to parse if it's a JSON string
                import json
                try:
                    learning_data = json.loads(learning_result)
                except:
                    learning_data = {"insights": "Parsing failed"}
            else:
                learning_data = learning_result
            
            # Apply field mapping learning if available
            if self.field_mapping_tool and learning_data.get('field_mappings'):
                for mapping in learning_data['field_mappings']:
                    source_field = mapping.get('source_field')
                    target_field = mapping.get('target_field')
                    if source_field and target_field:
                        self.field_mapping_tool.learn_field_mapping(
                            source_field, target_field, "agent_learning"
                        )
            
            # Update learning metrics
            self.memory.update_learning_metrics("asset_learning_applications", 1)
            
        except Exception as e:
            logger.warning(f"Failed to apply asset learning insights: {e}")
    
    def _basic_pattern_analysis(self, assets: List[Dict]) -> List[Dict]:
        """Basic pattern analysis for fallback mode."""
        patterns = []
        
        if assets:
            # Simple field usage analysis
            field_usage = {}
            for asset in assets:
                for field in asset.keys():
                    field_usage[field] = field_usage.get(field, 0) + 1
            
            patterns.append({
                "type": "field_usage",
                "pattern": field_usage,
                "confidence": 0.6,
                "source": "basic_analysis"
            })
        
        return patterns
    
    def _basic_asset_insights(self, assets: List[Dict], operation: str) -> List[Dict]:
        """Basic asset insights for fallback mode."""
        insights = []
        
        if assets:
            insights.append({
                "type": "basic_insight",
                "insight": f"Analyzed {len(assets)} assets for {operation}",
                "action": "Consider using AI analysis for enhanced insights",
                "priority": "medium",
                "confidence": 0.5
            })
        
        return insights
    
    def _basic_asset_recommendations(self, assets: List[Dict]) -> List[Dict]:
        """Basic asset recommendations for fallback mode."""
        recommendations = []
        
        if assets:
            recommendations.append({
                "type": "enhancement",
                "recommendation": "Enable AI asset intelligence for advanced analysis",
                "action": "Configure CrewAI and DeepInfra API for intelligent asset management",
                "priority": "high"
            })
        
        return recommendations
    
    def _basic_quality_assessment(self, assets: List[Dict]) -> Dict[str, Any]:
        """Basic quality assessment for fallback mode."""
        if not assets:
            return {"quality_score": 0, "issues": [], "recommendations": []}
        
        # Simple completeness check
        total_fields = sum(len(asset) for asset in assets)
        populated_fields = sum(
            sum(1 for value in asset.values() if value and str(value).strip())
            for asset in assets
        )
        
        quality_score = (populated_fields / total_fields * 100) if total_fields > 0 else 0
        
        return {
            "quality_score": round(quality_score, 2),
            "issues": [],
            "recommendations": ["Use AI quality assessment for detailed analysis"],
            "method": "basic_completeness_check"
        }

# Global service instance
crewai_service = CrewAIService() 