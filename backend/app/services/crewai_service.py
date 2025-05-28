"""
CrewAI service integration for AI-powered migration analysis.
Provides truly agentic AI agents with memory, learning, and adaptive capabilities.
"""

import json
import logging
import asyncio
import concurrent.futures
import uuid
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
from app.services.tools.field_mapping_tool import field_mapping_tool

logger = logging.getLogger(__name__)





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
    
    def _initialize_llm(self):
        """Initialize the LiteLLM configuration for DeepInfra."""
        try:
            if not settings.DEEPINFRA_API_KEY:
                logger.error("DeepInfra API key is required but not provided")
                self.llm = None
                return
            
            # Initialize LiteLLM for DeepInfra with optimized settings
            self.llm = LLM(
                model="deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                api_key=settings.DEEPINFRA_API_KEY,
                temperature=0.1,  # Lower temperature for consistent responses
                max_tokens=1000   # Increased token limit for complete responses
            )
            
            logger.info(f"Initialized LiteLLM for DeepInfra: {self.llm.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LiteLLM: {e}")
            self.llm = None
    
    def reinitialize_with_fresh_llm(self) -> None:
        """Reinitialize the service with a fresh LLM instance to avoid any caching issues."""
        if not CREWAI_AVAILABLE or not settings.DEEPINFRA_API_KEY:
            logger.warning("Cannot reinitialize - CrewAI not available or API key missing")
            return
        
        logger.info("Reinitializing CrewAI service with fresh LiteLLM instance")
        
        # Create a fresh LiteLLM instance
        fresh_llm = LLM(
            model="deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            api_key=settings.DEEPINFRA_API_KEY,
            temperature=0.1,  # Lower temperature for consistent responses
            max_tokens=1000   # Increased token limit for complete responses
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
            field_analysis = field_mapping_tool.analyze_data_columns(available_columns, "server")
            mapping_context = field_mapping_tool.get_mapping_context()
            
            # Enhanced pattern analysis using data content
            pattern_analysis = {}
            if cmdb_data.get('sample_data'):
                try:
                    # Convert sample data to list format for pattern analysis
                    sample_rows = []
                    for record in cmdb_data['sample_data'][:10]:  # Analyze first 10 rows
                        row = [record.get(col, '') for col in available_columns]
                        sample_rows.append(row)
                    
                    pattern_analysis = field_mapping_tool.field_mapper.analyze_data_patterns(
                        available_columns, sample_rows, "server"
                    )
                except Exception as e:
                    logger.warning(f"Pattern analysis failed: {e}")
                    pattern_analysis = {"column_analysis": {}, "confidence_scores": {}}
            
            # Create agentic task with enhanced field mapping intelligence
            task = Task(
                description=f"""
                As a Senior CMDB Data Analyst with access to advanced field mapping intelligence, analyze this CMDB export data.
                
                CURRENT ANALYSIS:
                File: {cmdb_data.get('filename')}
                Data Structure: {cmdb_data.get('structure')}
                Sample Records: {cmdb_data.get('sample_data', [])}
                Available Columns: {available_columns}
                
                FIELD MAPPING INTELLIGENCE:
                Field Analysis: {field_analysis}
                Mapping Context: {mapping_context}
                Pattern Analysis: {pattern_analysis}
                
                CRITICAL FIELD MAPPING INSTRUCTIONS:
                1. Use the pattern analysis results to understand what each column contains
                2. The pattern_analysis shows suggested field mappings with confidence scores
                3. Column suggestions like:
                   - 'HOSTNAME' → 'Asset Name' (confidence: 0.75)
                   - 'RAM (GB)' → 'Memory (GB)' (confidence: 0.85)
                   - 'APPLICATION_MAPPED' → 'Dependencies' (confidence: 0.70)
                4. DO NOT report fields as missing if they are available under different column names
                5. Learn new field mappings using the field_mapping_tool when patterns are discovered
                6. Use actual data content patterns, not just column names, for field identification
                
                ANALYSIS REQUIREMENTS:
                1. Determine the PRIMARY asset type based on data patterns and content
                2. Assess data quality considering the actual field mappings found
                3. Identify truly missing fields AFTER applying pattern-based field mappings
                4. Learn and store new field mappings discovered through pattern analysis
                5. Provide migration-specific recommendations based on discovered asset types
                
                FIELD MAPPING WORKFLOW:
                For each column in the data:
                1. Check pattern_analysis["column_analysis"] for suggested mappings
                2. If a mapping is suggested with confidence > 0.7, consider it valid
                3. Use field_mapping_tool.learn_field_mapping() to store discovered patterns
                4. Only report fields as missing if no suitable column mapping is found
                
                ASSET TYPE DETECTION:
                - Look for CI_TYPE, Asset_Type, or similar classification columns
                - If pattern analysis suggests these columns exist, use them for classification
                - Consider the actual data content, not just column names
                - Applications: Look for business services, versions, no hardware specs
                - Servers: Look for hostnames, IP addresses, hardware specifications
                - Databases: Look for database-specific fields like ports, instances
                
                DATA QUALITY ASSESSMENT:
                - Base quality on completeness AFTER field mapping
                - Higher quality if more fields are successfully mapped
                - Consider data pattern consistency (e.g., IP addresses in IP columns)
                - Reduce quality for truly missing essential fields
                
                LEARNING INSTRUCTIONS:
                - If you discover reliable field mappings (confidence > 0.7), learn them
                - Example: field_mapping_tool.learn_field_mapping("HOSTNAME", "Asset Name", "pattern_analysis")
                - Store patterns that could help with future similar datasets
                
                CRITICAL OUTPUT FORMAT REQUIREMENTS:
                You MUST return ONLY a valid JSON object. No additional text, explanations, or thoughts.
                
                EXACTLY this format (with actual values):
                {{
                    "asset_type_detected": "application",
                    "confidence_level": 0.9,
                    "data_quality_score": 85,
                    "issues": ["Missing IP addresses"],
                    "recommendations": ["Add network configuration data"],
                    "missing_fields_relevant": ["Business Owner"],
                    "migration_readiness": "ready",
                    "field_mappings_discovered": ["HOSTNAME → Asset Name"],
                    "pattern_analysis_applied": true,
                    "columns_successfully_mapped": 8,
                    "total_columns": 10
                }}
                
                Return only the JSON object above with your analysis results. No other text.
                """,
                agent=self.agents['cmdb_analyst'],
                expected_output="Valid JSON analysis with enhanced field mapping intelligence"
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
            field_learning_result = field_mapping_tool.learn_from_feedback_text(feedback_text, f"feedback_{filename}")
            current_mapping_context = field_mapping_tool.get_mapping_context()
            
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
                try:
                    from app.services.field_mapper import field_mapper
                    field_mapper.process_feedback_patterns(learning_result['patterns_identified'])
                except ImportError:
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
            
            # Remove common prefixes that agents might add
            prefixes_to_remove = [
                "Thought:", "Analysis:", "Response:", "Result:", "Output:",
                "Here is the analysis:", "The analysis is:", "Based on the data:",
                "I need to", "Let me", "First", "After analyzing"
            ]
            
            for prefix in prefixes_to_remove:
                if response.startswith(prefix):
                    response = response[len(prefix):].strip()
            
            # Try multiple JSON extraction methods
            import re
            
            # Method 1: Find the first complete JSON object
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            json_matches = re.findall(json_pattern, response, re.DOTALL)
            
            for json_match in json_matches:
                try:
                    parsed_json = json.loads(json_match)
                    if isinstance(parsed_json, dict) and len(parsed_json) > 3:  # Ensure it's a substantial object
                        logger.info("Successfully parsed AI response using pattern matching")
                        return self._validate_and_enhance_response(parsed_json)
                except json.JSONDecodeError:
                    continue
            
            # Method 2: Find the outermost braces
            first_brace = response.find('{')
            last_brace = response.rfind('}')
            
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_str = response[first_brace:last_brace + 1]
                try:
                    parsed_json = json.loads(json_str)
                    logger.info("Successfully parsed AI response using brace extraction")
                    return self._validate_and_enhance_response(parsed_json)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse extracted JSON: {e}")
            
            # Method 3: Try parsing the entire response
            try:
                parsed_json = json.loads(response)
                logger.info("Successfully parsed entire response as JSON")
                return self._validate_and_enhance_response(parsed_json)
            except json.JSONDecodeError:
                pass
            
            # Method 4: Try to clean and fix common JSON issues
            cleaned_response = self._clean_malformed_json(response)
            if cleaned_response:
                try:
                    parsed_json = json.loads(cleaned_response)
                    logger.info("Successfully parsed cleaned JSON response")
                    return self._validate_and_enhance_response(parsed_json)
                except json.JSONDecodeError:
                    pass
            
            logger.warning(f"All JSON parsing methods failed. Response length: {len(original_response)}")
            logger.warning(f"Response preview: {original_response[:200]}...")
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
        
        # Return intelligent fallback based on context
        return self._create_intelligent_fallback(original_response)
    
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






# Global service instance
crewai_service = CrewAIService() 