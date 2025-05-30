"""
Task Coordinator Handler
Handles task creation, crew orchestration, and workflow execution.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskCoordinatorHandler:
    """Handles task coordination and crew orchestration with graceful fallbacks."""
    
    def __init__(self, agent_manager):
        self.agent_manager = agent_manager
        self.service_available = False
        self._initialize_dependencies()
    
    def _initialize_dependencies(self):
        """Initialize dependencies with graceful fallbacks."""
        try:
            from crewai import Task, Crew
            self.Task = Task
            self.Crew = Crew
            self.service_available = True
            logger.info("Task coordinator handler initialized successfully")
            
        except ImportError as e:
            logger.warning(f"CrewAI not available: {e}")
            self._initialize_fallback_components()
            self.service_available = False
    
    def _initialize_fallback_components(self):
        """Initialize fallback components when dependencies unavailable."""
        class FallbackTask:
            def __init__(self, **kwargs):
                self.description = kwargs.get('description', 'Fallback task')
                self.agent = kwargs.get('agent')
                
        class FallbackCrew:
            def __init__(self, **kwargs):
                self.agents = kwargs.get('agents', [])
                self.tasks = kwargs.get('tasks', [])
                
            def kickoff(self):
                return "Fallback crew execution completed"
        
        self.Task = FallbackTask
        self.Crew = FallbackCrew
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks
    
    def create_discovery_task(self, cmdb_data: Dict[str, Any]) -> Any:
        """Create discovery analysis task."""
        try:
            return self.Task(
                description=f"""
                Analyze the provided CMDB data for application discovery and 6R preparation:
                
                CMDB Data: {cmdb_data}
                
                Your task is to:
                1. Extract key application characteristics from the CMDB data
                2. Identify technology stack, dependencies, and infrastructure details
                3. Assess business criticality indicators
                4. Identify any compliance or regulatory requirements
                5. Note any data quality issues or missing information
                6. Provide a summary of findings relevant to 6R migration strategy analysis
                
                Return your analysis in a structured format highlighting:
                - Application type and characteristics
                - Technical complexity indicators
                - Business value indicators
                - Risk factors
                - Information gaps that need clarification
                """,
                agent=self.agent_manager.get_agent("discovery"),
                expected_output="Structured analysis of CMDB data with key insights for 6R strategy planning"
            )
        except Exception as e:
            logger.error(f"Error creating discovery task: {e}")
            return self._fallback_task("discovery", cmdb_data)
    
    def create_initial_analysis_task(self, parameters: Any, application_context: Dict[str, Any]) -> Any:
        """Create initial 6R analysis task."""
        try:
            return self.Task(
                description=f"""
                Perform initial 6R migration strategy analysis based on:
                
                Parameters: {parameters}
                Application Context: {application_context}
                
                Your task is to:
                1. Evaluate the application against all 6R strategies (Rehost, Replatform, Refactor, Rearchitect, Rewrite, Retire)
                2. Consider business value, technical complexity, urgency, and constraints
                3. Assess migration risks and challenges for each strategy
                4. Recommend the most suitable strategy with detailed justification
                5. Identify key success factors and potential blockers
                6. Suggest next steps for detailed planning
                
                Provide a comprehensive analysis including:
                - Strategy recommendation with confidence score
                - Pros and cons of recommended approach
                - Alternative strategies considered
                - Risk assessment and mitigation suggestions
                - Resource and timeline estimates
                """,
                agent=self.agent_manager.get_agent("initial_analysis"),
                expected_output="Detailed 6R strategy recommendation with supporting analysis"
            )
        except Exception as e:
            logger.error(f"Error creating initial analysis task: {e}")
            return self._fallback_task("initial_analysis", {"parameters": parameters, "context": application_context})
    
    def create_question_generation_task(self, analysis_gaps: List[str], application_context: Dict[str, Any]) -> Any:
        """Create question generation task."""
        try:
            return self.Task(
                description=f"""
                Generate targeted qualifying questions to address information gaps in 6R analysis:
                
                Information Gaps: {analysis_gaps}
                Application Context: {application_context}
                
                Your task is to:
                1. Review the identified information gaps
                2. Consider the application context and existing information
                3. Generate specific, actionable questions that will fill these gaps
                4. Prioritize questions by their impact on strategy decisions
                5. Provide different question types (multiple choice, scale, text) as appropriate
                6. Include helpful context or examples for each question
                
                Create questions that are:
                - Clear and unambiguous
                - Relevant to 6R strategy decisions
                - Appropriate for business stakeholders
                - Prioritized by importance
                - Include suggested answer formats
                """,
                agent=self.agent_manager.get_agent("question_generator"),
                expected_output="List of prioritized qualifying questions with answer formats"
            )
        except Exception as e:
            logger.error(f"Error creating question generation task: {e}")
            return self._fallback_task("question_generation", {"gaps": analysis_gaps, "context": application_context})
    
    def create_input_processing_task(self, responses: List[Dict[str, Any]], current_parameters: Any) -> Any:
        """Create input processing task."""
        try:
            return self.Task(
                description=f"""
                Process stakeholder responses and update 6R analysis parameters:
                
                Stakeholder Responses: {responses}
                Current Parameters: {current_parameters}
                
                Your task is to:
                1. Analyze each stakeholder response for relevance to 6R parameters
                2. Extract quantitative insights from qualitative answers
                3. Update analysis parameters based on new information
                4. Identify any conflicting information that needs resolution
                5. Calculate confidence levels for parameter updates
                6. Document the reasoning for each parameter change
                
                For each response:
                - Map to relevant 6R analysis parameters
                - Determine appropriate parameter values (1-5 scale)
                - Provide confidence score for the mapping
                - Note any assumptions made
                - Identify follow-up questions if needed
                """,
                agent=self.agent_manager.get_agent("input_processing"),
                expected_output="Updated parameters with confidence scores and reasoning"
            )
        except Exception as e:
            logger.error(f"Error creating input processing task: {e}")
            return self._fallback_task("input_processing", {"responses": responses, "parameters": current_parameters})
    
    def run_discovery_workflow(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run discovery analysis workflow."""
        try:
            if not self.service_available:
                return self._fallback_workflow_execution("discovery", cmdb_data)
            
            discovery_task = self.create_discovery_task(cmdb_data)
            
            crew = self.Crew(
                agents=[self.agent_manager.get_agent("discovery")],
                tasks=[discovery_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            return {
                "status": "completed",
                "discovery_insights": result,
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "discovery"
            }
            
        except Exception as e:
            logger.error(f"Discovery workflow failed: {e}")
            return self._fallback_workflow_execution("discovery", cmdb_data)
    
    def run_initial_analysis_workflow(self, parameters: Any, application_context: Dict[str, Any]) -> Dict[str, Any]:
        """Run initial 6R analysis workflow."""
        try:
            if not self.service_available:
                return self._fallback_initial_analysis(parameters, application_context)
            
            # Use decision engine for core analysis
            engine_result = self.agent_manager.get_decision_engine().analyze_parameters(parameters, application_context)
            
            # Create task for agent to review and enhance the analysis
            analysis_task = self.create_initial_analysis_task(parameters, application_context)
            
            crew = self.Crew(
                agents=[self.agent_manager.get_agent("initial_analysis")],
                tasks=[analysis_task],
                verbose=True
            )
            
            agent_result = crew.kickoff()
            
            # Combine engine and agent results
            return {
                "status": "completed",
                "engine_analysis": engine_result,
                "agent_insights": agent_result,
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "initial_analysis"
            }
            
        except Exception as e:
            logger.error(f"Initial analysis failed: {e}")
            return self._fallback_initial_analysis(parameters, application_context)
    
    def run_question_generation_workflow(self, analysis_gaps: List[str], application_context: Dict[str, Any]) -> Dict[str, Any]:
        """Run question generation workflow."""
        try:
            if not self.service_available:
                return self._fallback_question_generation(analysis_gaps, application_context)
            
            question_task = self.create_question_generation_task(analysis_gaps, application_context)
            
            crew = self.Crew(
                agents=[self.agent_manager.get_agent("question_generator")],
                tasks=[question_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            return {
                "status": "completed",
                "questions": result,
                "raw_result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "question_generator"
            }
            
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return self._fallback_question_generation(analysis_gaps, application_context)
    
    def run_input_processing_workflow(self, responses: List[Dict[str, Any]], current_parameters: Any) -> Dict[str, Any]:
        """Run input processing workflow."""
        try:
            if not self.service_available:
                return self._fallback_input_processing(responses, current_parameters)
            
            processing_task = self.create_input_processing_task(responses, current_parameters)
            
            crew = self.Crew(
                agents=[self.agent_manager.get_agent("input_processing")],
                tasks=[processing_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            return {
                "status": "completed",
                "parameter_updates": result,
                "raw_result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "input_processing"
            }
            
        except Exception as e:
            logger.error(f"Input processing failed: {e}")
            return self._fallback_input_processing(responses, current_parameters)
    
    # Fallback methods
    def _fallback_task(self, task_type: str, data: Any) -> Any:
        """Create fallback task when CrewAI unavailable."""
        return self.Task(
            description=f"Fallback {task_type} task",
            agent=None,
            data=data
        )
    
    def _fallback_workflow_execution(self, workflow_type: str, data: Any) -> Dict[str, Any]:
        """Fallback workflow execution."""
        return {
            "status": "completed_fallback",
            "workflow_type": workflow_type,
            "result": f"Fallback {workflow_type} analysis completed",
            "data_processed": bool(data),
            "timestamp": datetime.utcnow().isoformat(),
            "fallback_mode": True
        }
    
    def _fallback_initial_analysis(self, parameters: Any, application_context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback initial analysis when services unavailable."""
        engine_result = self.agent_manager.get_decision_engine().analyze_parameters(parameters, application_context)
        
        return {
            "status": "completed_fallback",
            "engine_analysis": engine_result,
            "agent_insights": "Fallback analysis mode - using decision engine only",
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "initial_analysis",
            "fallback_mode": True
        }
    
    def _fallback_question_generation(self, analysis_gaps: List[str], application_context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback question generation."""
        from app.schemas.sixr_analysis import QualifyingQuestion, QuestionType, QuestionOption
        
        # Generate basic fallback questions
        fallback_questions = [
            {
                "id": "tech_complexity",
                "question": "How would you rate the technical complexity of this application?",
                "type": "scale",
                "category": "Technical",
                "priority": 1
            },
            {
                "id": "business_criticality", 
                "question": "How critical is this application to your business operations?",
                "type": "scale",
                "category": "Business",
                "priority": 1
            }
        ]
        
        return {
            "status": "completed_fallback",
            "questions": fallback_questions,
            "raw_result": "Fallback question generation",
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "question_generator",
            "fallback_mode": True
        }
    
    def _fallback_input_processing(self, responses: List[Dict[str, Any]], current_parameters: Any) -> Dict[str, Any]:
        """Fallback input processing."""
        return {
            "status": "completed_fallback",
            "parameter_updates": {
                "updates": {},
                "confidence": 0.6,
                "reasoning": "Fallback processing mode"
            },
            "raw_result": "Fallback input processing",
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "input_processing",
            "fallback_mode": True
        } 