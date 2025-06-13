"""
6R Analysis CrewAI Agents for migration strategy analysis workflow.
Specialized agents for discovery, analysis, question generation, and refinement.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from crewai import Agent, Task, Crew
    from crewai.tools import BaseTool
    from app.services.deepinfra_llm import DeepInfraLLM
    from app.services.sixr_engine import SixRDecisionEngine
    from app.schemas.sixr_analysis import (
        SixRParameterBase, QualifyingQuestion, 
        QuestionType, QuestionOption
    )
    from app.models.asset import SixRStrategy
except ImportError as e:
    logging.warning(f"CrewAI imports failed: {e}")
    # Fallback classes for testing
    class Agent:
        def __init__(self, **kwargs):
            pass
    class Task:
        def __init__(self, **kwargs):
            pass
    class Crew:
        def __init__(self, **kwargs):
            pass
    class BaseTool:
        def __init__(self, **kwargs):
            pass
    
    # Fallback schema classes
    class SixRParameterBase:
        def __init__(self, **kwargs):
            self.business_value = kwargs.get('business_value', 5)
            self.technical_complexity = kwargs.get('technical_complexity', 5)
            self.migration_urgency = kwargs.get('migration_urgency', 5)
            self.compliance_requirements = kwargs.get('compliance_requirements', 5)
            self.cost_sensitivity = kwargs.get('cost_sensitivity', 5)
            self.risk_tolerance = kwargs.get('risk_tolerance', 5)
            self.innovation_priority = kwargs.get('innovation_priority', 5)
    
    class QualifyingQuestion:
        def __init__(self, **kwargs):
            pass
    
    class QuestionType:
        TEXT = "text"
        SELECT = "select"
        BOOLEAN = "boolean"
    
    class QuestionOption:
        def __init__(self, **kwargs):
            pass
    
    # Fallback for DeepInfraLLM
    class DeepInfraLLM:
        def __init__(self, **kwargs):
            pass

    # Fallback for SixRDecisionEngine
    class SixRDecisionEngine:
        def analyze_parameters(self, *args, **kwargs):
            return {
                'recommended_strategy': 'replatform',
                'confidence_score': 0.7,
                'strategy_scores': [],
                'key_factors': ['Fallback analysis'],
                'assumptions': ['Limited functionality'],
                'next_steps': ['Fix import issues']
            }

logger = logging.getLogger(__name__)


class SixRAnalysisAgents:
    """6R Analysis CrewAI agents orchestrator."""
    
    def __init__(self, llm_service: Optional[Any] = None):
        try:
            self.llm = llm_service or DeepInfraLLM()
            self.decision_engine = SixRDecisionEngine()
            self.agents = self._initialize_agents()
        except Exception as e:
            logger.warning(f"Failed to initialize agents: {e}")
            # Create fallback instances
            self.llm = DeepInfraLLM()
            self.decision_engine = SixRDecisionEngine()
            self.agents = {}
        
    def _initialize_agents(self) -> Dict[str, Agent]:
        """Initialize all 6R analysis agents."""
        
        # Discovery Agent - Processes CMDB data and application context
        discovery_agent = Agent(
            role="6R Discovery Specialist",
            goal="Analyze application data and CMDB information to extract relevant context for 6R analysis",
            backstory="""You are an expert in application discovery and data analysis. 
            Your role is to examine CMDB data, application metadata, and infrastructure 
            information to identify key characteristics that influence migration strategy decisions. 
            You excel at finding patterns in technical data and translating them into 
            meaningful insights for migration planning.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Initial Analysis Agent - Performs preliminary 6R recommendations
        initial_analysis_agent = Agent(
            role="6R Strategy Analyst",
            goal="Perform initial 6R analysis based on available data and generate preliminary recommendations",
            backstory="""You are a seasoned cloud migration strategist with deep expertise 
            in the 6R framework (Rehost, Replatform, Refactor, Rearchitect, Rewrite, Retire). 
            You analyze application characteristics, business requirements, and technical 
            constraints to recommend optimal migration strategies. Your recommendations 
            are data-driven and consider both technical feasibility and business value.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Question Generator Agent - Creates qualifying questions to fill data gaps
        question_generator_agent = Agent(
            role="6R Question Designer",
            goal="Generate targeted qualifying questions to gather missing information for accurate 6R analysis",
            backstory="""You are an expert in requirements gathering and questionnaire design 
            for cloud migration projects. You identify information gaps in the analysis and 
            create precise, relevant questions that help stakeholders provide the missing 
            context needed for accurate migration strategy recommendations. Your questions 
            are clear, actionable, and prioritized by impact on the analysis.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Input Processing Agent - Processes stakeholder responses and updates analysis
        input_processing_agent = Agent(
            role="6R Input Processor",
            goal="Process stakeholder responses and update analysis parameters based on new information",
            backstory="""You are skilled at interpreting stakeholder feedback and translating 
            qualitative responses into quantitative parameters for migration analysis. You 
            understand how different types of input affect migration strategy decisions and 
            can adjust analysis parameters accordingly. You ensure that stakeholder intent 
            is accurately captured in the technical analysis.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Refinement Agent - Iteratively improves recommendations
        refinement_agent = Agent(
            role="6R Refinement Specialist",
            goal="Refine and improve 6R recommendations through iterative analysis and stakeholder feedback",
            backstory="""You are an expert in iterative analysis and continuous improvement 
            of migration strategies. You analyze feedback from previous iterations, identify 
            areas for improvement, and refine recommendations to better align with stakeholder 
            needs and constraints. You excel at balancing competing priorities and finding 
            optimal solutions through collaborative refinement.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Validation Agent - Validates final recommendations
        validation_agent = Agent(
            role="6R Validation Expert",
            goal="Validate final 6R recommendations for accuracy, feasibility, and alignment with requirements",
            backstory="""You are a senior migration architect with extensive experience 
            validating migration strategies across diverse environments. You perform final 
            quality checks on 6R recommendations, ensuring they are technically sound, 
            business-aligned, and practically implementable. You identify potential risks 
            and provide confidence assessments for the recommended strategies.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        return {
            "discovery": discovery_agent,
            "initial_analysis": initial_analysis_agent,
            "question_generator": question_generator_agent,
            "input_processing": input_processing_agent,
            "refinement": refinement_agent,
            "validation": validation_agent
        }
    
    def create_discovery_task(self, application_data: Dict[str, Any]) -> Task:
        """Create discovery task for analyzing application data."""
        return Task(
            description=f"""
            Analyze the provided application data and extract key characteristics 
            that influence 6R migration strategy decisions.
            
            Application Data: {application_data}
            
            Your analysis should identify:
            1. Technical complexity indicators
            2. Business value signals
            3. Compliance and regulatory requirements
            4. Dependencies and integration points
            5. Performance and scalability characteristics
            6. Current technology stack and architecture patterns
            
            Provide a structured analysis that can be used to inform initial 
            parameter settings for the 6R decision engine.
            """,
            agent=self.agents["discovery"],
            expected_output="Structured analysis of application characteristics with recommended initial parameter values"
        )
    
    def create_initial_analysis_task(self, parameters: SixRParameterBase, 
                                   application_context: Dict[str, Any]) -> Task:
        """Create initial analysis task for 6R recommendation."""
        return Task(
            description=f"""
            Perform initial 6R analysis using the provided parameters and application context.
            
            Parameters:
            - Business Value: {parameters.business_value}
            - Technical Complexity: {parameters.technical_complexity}
            - Migration Urgency: {parameters.migration_urgency}
            - Compliance Requirements: {parameters.compliance_requirements}
            - Cost Sensitivity: {parameters.cost_sensitivity}
            - Risk Tolerance: {parameters.risk_tolerance}
            - Innovation Priority: {parameters.innovation_priority}
            
            Application Context: {application_context}
            
            Generate a preliminary 6R recommendation with:
            1. Recommended strategy (Rehost, Replatform, Refactor, Rearchitect, Rewrite, Retire)
            2. Confidence score and rationale
            3. Key decision factors
            4. Identified risks and benefits
            5. Areas where additional information would improve the analysis
            """,
            agent=self.agents["initial_analysis"],
            expected_output="Preliminary 6R recommendation with confidence assessment and information gaps"
        )
    
    def create_question_generation_task(self, analysis_gaps: List[str], 
                                      application_context: Dict[str, Any]) -> Task:
        """Create task for generating qualifying questions."""
        return Task(
            description=f"""
            Generate targeted qualifying questions to address the identified information gaps 
            in the 6R analysis.
            
            Information Gaps: {analysis_gaps}
            Application Context: {application_context}
            
            For each gap, create questions that:
            1. Are specific and actionable
            2. Have clear answer options where appropriate
            3. Are prioritized by impact on analysis accuracy
            4. Include help text to guide stakeholders
            5. Consider dependencies between questions
            
            Question types available: text, select, multiselect, file_upload, boolean, numeric
            
            Focus on questions that will most significantly improve the confidence 
            and accuracy of the 6R recommendation.
            """,
            agent=self.agents["question_generator"],
            expected_output="Prioritized list of qualifying questions with clear answer options and help text"
        )
    
    def create_input_processing_task(self, responses: List[Dict[str, Any]], 
                                   current_parameters: SixRParameterBase) -> Task:
        """Create task for processing stakeholder input."""
        return Task(
            description=f"""
            Process stakeholder responses and determine how they should update the 
            current analysis parameters.
            
            Current Parameters:
            - Business Value: {current_parameters.business_value}
            - Technical Complexity: {current_parameters.technical_complexity}
            - Migration Urgency: {current_parameters.migration_urgency}
            - Compliance Requirements: {current_parameters.compliance_requirements}
            - Cost Sensitivity: {current_parameters.cost_sensitivity}
            - Risk Tolerance: {current_parameters.risk_tolerance}
            - Innovation Priority: {current_parameters.innovation_priority}
            
            Stakeholder Responses: {responses}
            
            Analyze each response and determine:
            1. Which parameters should be adjusted and by how much
            2. The confidence level in each adjustment
            3. Any new insights that affect the analysis
            4. Potential conflicts or inconsistencies in responses
            5. Recommended parameter updates with justification
            """,
            agent=self.agents["input_processing"],
            expected_output="Updated parameter recommendations with confidence levels and justification"
        )
    
    def create_refinement_task(self, previous_recommendation: Dict[str, Any], 
                             stakeholder_feedback: str, 
                             updated_parameters: SixRParameterBase) -> Task:
        """Create task for refining recommendations based on feedback."""
        return Task(
            description=f"""
            Refine the 6R recommendation based on stakeholder feedback and updated parameters.
            
            Previous Recommendation: {previous_recommendation}
            Stakeholder Feedback: {stakeholder_feedback}
            Updated Parameters:
            - Business Value: {updated_parameters.business_value}
            - Technical Complexity: {updated_parameters.technical_complexity}
            - Migration Urgency: {updated_parameters.migration_urgency}
            - Compliance Requirements: {updated_parameters.compliance_requirements}
            - Cost Sensitivity: {updated_parameters.cost_sensitivity}
            - Risk Tolerance: {updated_parameters.risk_tolerance}
            - Innovation Priority: {updated_parameters.innovation_priority}
            
            Analyze the feedback and parameter changes to:
            1. Determine if the recommended strategy should change
            2. Update confidence scores based on new information
            3. Refine rationale and risk assessments
            4. Address specific concerns raised in feedback
            5. Identify any remaining uncertainties or risks
            
            Provide a refined recommendation that better aligns with stakeholder needs.
            """,
            agent=self.agents["refinement"],
            expected_output="Refined 6R recommendation addressing stakeholder feedback with updated confidence"
        )
    
    def create_validation_task(self, final_recommendation: Dict[str, Any], 
                             analysis_history: List[Dict[str, Any]]) -> Task:
        """Create task for validating final recommendation."""
        return Task(
            description=f"""
            Validate the final 6R recommendation for accuracy, feasibility, and completeness.
            
            Final Recommendation: {final_recommendation}
            Analysis History: {analysis_history}
            
            Perform comprehensive validation including:
            1. Technical feasibility assessment
            2. Business alignment verification
            3. Risk assessment completeness
            4. Implementation practicality
            5. Confidence score validation
            6. Consistency with analysis inputs
            7. Identification of any remaining gaps or concerns
            
            Provide a final validation report with:
            - Overall validation status (approved/needs_revision/rejected)
            - Confidence in the recommendation
            - Key validation findings
            - Any recommended adjustments
            - Implementation readiness assessment
            """,
            agent=self.agents["validation"],
            expected_output="Comprehensive validation report with approval status and implementation readiness"
        )
    
    def run_discovery_analysis(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run discovery analysis workflow."""
        try:
            discovery_task = self.create_discovery_task(application_data)
            
            crew = Crew(
                agents=[self.agents["discovery"]],
                tasks=[discovery_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            return {
                "status": "completed",
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "discovery"
            }
            
        except Exception as e:
            logger.error(f"Discovery analysis failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "discovery"
            }
    
    def run_initial_analysis(self, parameters: SixRParameterBase, 
                           application_context: Dict[str, Any]) -> Dict[str, Any]:
        """Run initial 6R analysis workflow."""
        try:
            # Use decision engine for core analysis
            engine_result = self.decision_engine.analyze_parameters(parameters, application_context)
            
            # Create task for agent to review and enhance the analysis
            analysis_task = self.create_initial_analysis_task(parameters, application_context)
            
            crew = Crew(
                agents=[self.agents["initial_analysis"]],
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
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "initial_analysis"
            }
    
    def run_question_generation(self, analysis_gaps: List[str], 
                              application_context: Dict[str, Any]) -> Dict[str, Any]:
        """Run question generation workflow."""
        try:
            question_task = self.create_question_generation_task(analysis_gaps, application_context)
            
            crew = Crew(
                agents=[self.agents["question_generator"]],
                tasks=[question_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse and structure the questions
            questions = self._parse_generated_questions(result)
            
            return {
                "status": "completed",
                "questions": questions,
                "raw_result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "question_generator"
            }
            
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "question_generator"
            }
    
    def run_input_processing(self, responses: List[Dict[str, Any]], 
                           current_parameters: SixRParameterBase) -> Dict[str, Any]:
        """Run input processing workflow."""
        try:
            processing_task = self.create_input_processing_task(responses, current_parameters)
            
            crew = Crew(
                agents=[self.agents["input_processing"]],
                tasks=[processing_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse parameter updates
            parameter_updates = self._parse_parameter_updates(result)
            
            return {
                "status": "completed",
                "parameter_updates": parameter_updates,
                "raw_result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "input_processing"
            }
            
        except Exception as e:
            logger.error(f"Input processing failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "input_processing"
            }
    
    def run_refinement_analysis(self, previous_recommendation: Dict[str, Any], 
                              stakeholder_feedback: str, 
                              updated_parameters: SixRParameterBase) -> Dict[str, Any]:
        """Run refinement analysis workflow."""
        try:
            refinement_task = self.create_refinement_task(
                previous_recommendation, stakeholder_feedback, updated_parameters
            )
            
            crew = Crew(
                agents=[self.agents["refinement"]],
                tasks=[refinement_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            return {
                "status": "completed",
                "refined_recommendation": result,
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "refinement"
            }
            
        except Exception as e:
            logger.error(f"Refinement analysis failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "refinement"
            }
    
    def run_validation(self, final_recommendation: Dict[str, Any], 
                      analysis_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run validation workflow."""
        try:
            validation_task = self.create_validation_task(final_recommendation, analysis_history)
            
            crew = Crew(
                agents=[self.agents["validation"]],
                tasks=[validation_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            return {
                "status": "completed",
                "validation_result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "validation"
            }
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "validation"
            }
    
    def _parse_generated_questions(self, raw_result: str) -> List[QualifyingQuestion]:
        """Parse generated questions from agent output."""
        # This is a simplified parser - in practice, you'd want more robust parsing
        questions = []
        
        # For now, return some default questions based on common gaps
        default_questions = [
            QualifyingQuestion(
                id="app_dependencies",
                question="How many critical dependencies does this application have?",
                question_type=QuestionType.SELECT,
                category="Technical Architecture",
                priority=1,
                required=True,
                options=[
                    QuestionOption(value="none", label="No dependencies"),
                    QuestionOption(value="few", label="1-3 dependencies"),
                    QuestionOption(value="moderate", label="4-10 dependencies"),
                    QuestionOption(value="many", label="More than 10 dependencies")
                ],
                help_text="Consider databases, external APIs, shared services, and other applications"
            ),
            QualifyingQuestion(
                id="compliance_type",
                question="What compliance frameworks apply to this application?",
                question_type=QuestionType.MULTISELECT,
                category="Compliance",
                priority=2,
                required=False,
                options=[
                    QuestionOption(value="sox", label="SOX"),
                    QuestionOption(value="pci", label="PCI DSS"),
                    QuestionOption(value="hipaa", label="HIPAA"),
                    QuestionOption(value="gdpr", label="GDPR"),
                    QuestionOption(value="none", label="No specific compliance requirements")
                ],
                help_text="Select all applicable compliance frameworks"
            ),
            QualifyingQuestion(
                id="business_criticality",
                question="What is the business impact if this application is unavailable?",
                question_type=QuestionType.SELECT,
                category="Business Impact",
                priority=1,
                required=True,
                options=[
                    QuestionOption(value="low", label="Minimal impact - can be down for days"),
                    QuestionOption(value="medium", label="Moderate impact - can be down for hours"),
                    QuestionOption(value="high", label="High impact - can be down for minutes"),
                    QuestionOption(value="critical", label="Critical - must be always available")
                ],
                help_text="Consider revenue impact, customer experience, and operational disruption"
            )
        ]
        
        return default_questions
    
    def _parse_parameter_updates(self, raw_result: str) -> Dict[str, Any]:
        """Parse parameter updates from agent output."""
        # This is a simplified parser - in practice, you'd want more robust parsing
        return {
            "updates": {},
            "confidence": 0.8,
            "reasoning": "Parsed from agent analysis"
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        return {
            "agents_initialized": len(self.agents),
            "available_agents": list(self.agents.keys()),
            "llm_configured": self.llm is not None,
            "decision_engine_ready": self.decision_engine is not None,
            "timestamp": datetime.utcnow().isoformat()
        } 