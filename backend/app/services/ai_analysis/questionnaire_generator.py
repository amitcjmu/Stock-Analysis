"""
Adaptive Questionnaire Generation Service - B2.2
ADCS AI Analysis & Intelligence Service

This service uses AI to generate adaptive, contextual questionnaires for filling
data gaps identified by the gap analysis agent.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

try:
    from crewai import Agent, Process, Task

    from app.services.crews.base_crew import BaseDiscoveryCrew

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Create dummy classes for type hints
    Agent = Task = Process = object
    BaseDiscoveryCrew = object

logger = logging.getLogger(__name__)


class QuestionType(str, Enum):
    """Question types supported by the adaptive questionnaire system"""

    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"
    TEXT_INPUT = "text_input"
    NUMERIC_INPUT = "numeric_input"
    BOOLEAN = "boolean"
    DATE_INPUT = "date_input"
    FILE_UPLOAD = "file_upload"
    RATING_SCALE = "rating_scale"
    DEPENDENCY_MAPPING = "dependency_mapping"
    TECHNOLOGY_SELECTION = "technology_selection"


class QuestionPriority(str, Enum):
    """Question priority levels for questionnaire sequencing"""

    CRITICAL = "critical"  # Must be answered to proceed
    HIGH = "high"  # Important for strategy confidence
    MEDIUM = "medium"  # Helpful for planning
    LOW = "low"  # Nice to have


class AdaptiveQuestionnaireGenerator(BaseDiscoveryCrew):
    """
    AI-powered adaptive questionnaire generator using CrewAI framework.

    Generates contextual questionnaires based on gap analysis results,
    business context, and learned patterns from previous collections.
    """

    def __init__(self):
        """Initialize questionnaire generation crew"""
        if CREWAI_AVAILABLE:
            super().__init__(
                name="questionnaire_generation_crew",
                description="AI-powered adaptive questionnaire generation for data gap resolution",
                process=Process.sequential,
                verbose=True,
                memory=True,
                cache=True,
            )
        else:
            # Fallback initialization when CrewAI is not available
            self.name = "questionnaire_generation_crew"
            self.description = (
                "AI-powered adaptive questionnaire generation for data gap resolution"
            )
            self.verbose = True
            self.agents = []
            self.tasks = []

    def create_agents(self) -> List[Any]:
        """Create specialized AI agents for questionnaire generation"""
        agents = []

        try:
            # Primary Questionnaire Designer
            questionnaire_designer = Agent(
                role="Intelligent Questionnaire Designer",
                goal="Generate adaptive questionnaires that efficiently collect missing critical migration data",
                backstory="""You are an expert AI agent specializing in intelligent questionnaire design
                for enterprise migration projects. Your expertise combines:

                - Deep understanding of the 22 critical attributes framework for migration planning
                - Knowledge of 6R migration strategies and their data requirements
                - Expertise in questionnaire design psychology and user experience
                - Understanding of business stakeholder roles and knowledge areas
                - Experience with progressive disclosure and adaptive questioning techniques

                Your questionnaires are designed to:
                - Minimize respondent fatigue while maximizing data quality
                - Use conditional logic to show only relevant questions
                - Provide context and help text for complex technical questions
                - Sequence questions logically from simple to complex
                - Adapt based on previous responses and stakeholder role
                - Include validation rules to ensure data quality

                You understand that different stakeholders have different knowledge areas:
                - Infrastructure teams know technical details but not business impact
                - Business owners know criticality but not technical architecture
                - Application teams know dependencies but not infrastructure details
                - Compliance teams know regulatory requirements but not technical implementation

                Your questionnaires bridge these knowledge gaps efficiently.""",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                tools=[],
            )
            agents.append(questionnaire_designer)

            # Business Context Specialist
            context_specialist = Agent(
                role="Business Context Analysis Specialist",
                goal="Ensure questionnaires are contextually relevant to the business environment and stakeholder roles",
                backstory="""You are a business analysis AI agent that ensures questionnaires
                are properly contextualized for the specific business environment and stakeholder roles.

                Your specializations include:
                - Analyzing business context to determine appropriate question complexity
                - Identifying the right stakeholders for specific types of questions
                - Understanding organizational structures and decision-making processes
                - Adapting questionnaire language and terminology for different audiences
                - Ensuring questions align with business objectives and migration goals
                - Balancing thoroughness with practical time constraints

                You work with the Questionnaire Designer to ensure questions are:
                - Appropriate for the target audience's knowledge level
                - Aligned with business priorities and migration objectives
                - Sensitive to organizational culture and change management needs
                - Realistic in terms of effort and expertise required to answer
                - Structured to support business decision-making processes""",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                tools=[],
            )
            agents.append(context_specialist)

            # Question Quality Validator
            quality_validator = Agent(
                role="Questionnaire Quality Assurance Expert",
                goal="Validate questionnaire quality, usability, and effectiveness for gap resolution",
                backstory="""You are a quality assurance AI agent specializing in questionnaire
                validation and optimization for enterprise data collection.

                Your validation expertise covers:
                - Question clarity and unambiguous wording
                - Logical flow and conditional branching validation
                - Response format consistency and data validation rules
                - User experience and accessibility considerations
                - Completeness of gap coverage for migration planning
                - Integration with existing systems and workflows

                You ensure questionnaires meet high standards for:
                - Data quality and reliability
                - User experience and completion rates
                - Business value and actionable insights
                - Technical integration and data processing
                - Compliance with data privacy and security requirements

                You provide the final quality check before questionnaires are deployed.""",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                tools=[],
            )
            agents.append(quality_validator)

        except Exception as e:
            logger.error(f"Failed to create questionnaire generation agents: {e}")
            # Create minimal fallback agent
            fallback_agent = Agent(
                role="Questionnaire Generator",
                goal="Generate questionnaires for data collection",
                backstory="You generate questionnaires to collect missing data.",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                tools=[],
            )
            agents.append(fallback_agent)

        return agents

    def create_tasks(self, inputs: Dict[str, Any]) -> List[Task]:
        """Create questionnaire generation tasks"""
        gap_analysis = inputs.get("gap_analysis", {})
        business_context = inputs.get("business_context", {})
        collection_flow_id = inputs.get("collection_flow_id")
        stakeholder_context = inputs.get("stakeholder_context", {})
        automation_tier = inputs.get("automation_tier", "tier_2")

        tasks = []

        # Task 1: Questionnaire Design
        questionnaire_design_task = Task(
            description=f"""
            ADAPTIVE QUESTIONNAIRE GENERATION

            Collection Flow ID: {collection_flow_id}
            Automation Tier: {automation_tier}

            GAP ANALYSIS INPUT:
            {json.dumps(gap_analysis, indent=2)}

            BUSINESS CONTEXT:
            {json.dumps(business_context, indent=2)}

            STAKEHOLDER CONTEXT:
            {json.dumps(stakeholder_context, indent=2)}

            QUESTIONNAIRE DESIGN OBJECTIVES:

            1. GAP-TARGETED QUESTION GENERATION:
               - Create specific questions for each prioritized gap from the gap analysis
               - Focus on Priority 1 (Critical) and Priority 2 (High) gaps first
               - Design questions that directly collect the missing critical attributes
               - Ensure questions support 6R strategy confidence improvement

            2. ADAPTIVE QUESTION LOGIC:
               - Implement conditional logic based on previous responses
               - Progressive disclosure: start simple, get more detailed as needed
               - Role-based question filtering (infrastructure, business, application teams)
               - Dynamic follow-up questions based on initial responses

            3. QUESTION TYPE OPTIMIZATION:
               Available Question Types:
               - single_select: Single choice from predefined options
               - multi_select: Multiple choices from predefined options
               - text_input: Free-form text input with validation
               - numeric_input: Numeric values with range validation
               - boolean: Yes/No or True/False questions
               - date_input: Date selection with validation
               - file_upload: Document or file attachment
               - rating_scale: 1-5 or 1-10 scale ratings
               - dependency_mapping: Visual dependency relationships
               - technology_selection: Technology stack components

            4. STAKEHOLDER-AWARE DESIGN:
               - Infrastructure Team: Technical configuration, performance, dependencies
               - Business Owner: Criticality, business impact, compliance requirements
               - Application Team: Architecture, integrations, data flows
               - Security Team: Security controls, compliance, data classification
               - Operations Team: Monitoring, backup, maintenance procedures

            5. USER EXPERIENCE OPTIMIZATION:
               - Maximum 15 questions per questionnaire section
               - Estimated completion time: 10-20 minutes per section
               - Clear help text and examples for complex questions
               - Progress indicators and section organization
               - Save and resume capability for longer questionnaires

            6. DATA QUALITY MEASURES:
               - Input validation rules for each question type
               - Required field identification based on gap priority
               - Consistency checks across related questions
               - Data format standardization rules

            OUTPUT FORMAT:
            Generate comprehensive questionnaire specification:
            {{
                "questionnaire_metadata": {{
                    "id": "questionnaire-{collection_flow_id}",
                    "title": "Migration Data Collection Questionnaire",
                    "description": "Targeted data collection for migration planning",
                    "version": "1.0",
                    "estimated_duration_minutes": <10-30>,
                    "total_questions": <count>,
                    "priority_distribution": {{
                        "critical": <count>,
                        "high": <count>,
                        "medium": <count>,
                        "low": <count>
                    }}
                }},
                "questionnaire_sections": [
                    {{
                        "section_id": "infrastructure",
                        "section_title": "Infrastructure Information",
                        "section_description": "Technical infrastructure details",
                        "target_stakeholders": ["infrastructure_team", "operations_team"],
                        "estimated_duration_minutes": <5-10>,
                        "questions": [
                            {{
                                "question_id": "q-infra-001",
                                "question_text": "What is the current operating system version?",
                                "question_type": "single_select",
                                "priority": "critical",
                                "required": true,
                                "help_text": "Select the specific OS version for migration compatibility assessment",
                                "validation_rules": {{
                                    "required": true,
                                    "format": "string"
                                }},
                                "options": [
                                    {{"value": "windows_server_2019", "label": "Windows Server 2019"}},
                                    {{"value": "windows_server_2016", "label": "Windows Server 2016"}},
                                    {{"value": "rhel_8", "label": "Red Hat Enterprise Linux 8"}},
                                    {{"value": "ubuntu_20_04", "label": "Ubuntu 20.04 LTS"}},
                                    {{"value": "other", "label": "Other (please specify)"}}
                                ],
                                "conditional_logic": {{
                                    "show_if": {{"previous_response": "has_infrastructure"}},
                                    "follow_up_if": {{"response": "other", "question": "q-infra-001-followup"}}
                                }},
                                "gap_resolution": {{
                                    "addresses_gap": "os_version",
                                    "gap_priority": 1,
                                    "confidence_improvement": 25
                                }}
                            }}
                        ]
                    }}
                ],
                "adaptive_logic": {{
                    "branching_rules": [
                        {{
                            "condition": "stakeholder_role == 'business_owner'",
                            "action": "skip_technical_sections",
                            "sections_affected": ["infrastructure", "technical_architecture"]
                        }}
                    ],
                    "dynamic_questions": [
                        {{
                            "trigger_condition": "application_type == 'web_application'",
                            "additional_questions": ["web_framework", "database_dependencies"]
                        }}
                    ]
                }},
                "completion_criteria": {{
                    "minimum_required_questions": <count>,
                    "critical_questions_required": true,
                    "estimated_confidence_improvement": <percentage>,
                    "success_metrics": [
                        "All Priority 1 gaps addressed",
                        "Minimum 80% of Priority 2 gaps addressed",
                        "Sufficient data for 6R strategy recommendation"
                    ]
                }}
            }}
            """,
            agent=self.agents[0],
            expected_output="Comprehensive adaptive questionnaire specification with conditional logic and stakeholder targeting",
        )
        tasks.append(questionnaire_design_task)

        # Task 2: Business Context Validation
        if len(self.agents) > 1:
            business_context_task = Task(
                description="""
                BUSINESS CONTEXT VALIDATION AND OPTIMIZATION

                Review the questionnaire design for business context alignment:

                1. STAKEHOLDER APPROPRIATENESS:
                   - Verify questions are appropriate for target stakeholders
                   - Check question complexity matches stakeholder expertise
                   - Ensure business terminology is used correctly
                   - Validate that questions align with stakeholder responsibilities

                2. BUSINESS OBJECTIVE ALIGNMENT:
                   - Confirm questions support migration business case development
                   - Verify alignment with enterprise architecture standards
                   - Check compliance and governance requirement coverage
                   - Ensure questions support ROI and cost analysis

                3. ORGANIZATIONAL CONTEXT:
                   - Adapt questions for organizational culture and change readiness
                   - Consider organizational structure and decision-making processes
                   - Account for resource constraints and competing priorities
                   - Ensure questions respect confidentiality and security concerns

                4. PRACTICAL CONSIDERATIONS:
                   - Validate realistic time estimates for completion
                   - Check if required information is actually available to respondents
                   - Ensure questions don't duplicate existing documentation
                   - Verify feasibility of data collection methods

                Provide business context optimization recommendations.
                """,
                agent=self.agents[1],
                expected_output="Business context validation with optimization recommendations",
                context=[questionnaire_design_task],
            )
            tasks.append(business_context_task)

        # Task 3: Quality Validation
        if len(self.agents) > 2:
            quality_validation_task = Task(
                description="""
                QUESTIONNAIRE QUALITY VALIDATION

                Perform comprehensive quality validation of the questionnaire:

                1. QUESTION QUALITY ASSESSMENT:
                   - Clear, unambiguous wording
                   - Appropriate question types for data being collected
                   - Logical flow and sequence
                   - Proper conditional logic implementation
                   - Complete validation rules and error handling

                2. USER EXPERIENCE VALIDATION:
                   - Optimal questionnaire length and pacing
                   - Clear instructions and help text
                   - Intuitive navigation and progress indicators
                   - Accessible design for different user capabilities
                   - Mobile-friendly design considerations

                3. DATA QUALITY ASSURANCE:
                   - Comprehensive validation rules
                   - Consistent data formats and standards
                   - Duplicate prevention mechanisms
                   - Data integration compatibility
                   - Error prevention and recovery

                4. TECHNICAL INTEGRATION:
                   - API compatibility for data submission
                   - Database schema alignment
                   - Security and privacy compliance
                   - Performance optimization for large-scale deployment
                   - Integration with existing workflow systems

                5. EFFECTIVENESS VALIDATION:
                   - Complete gap coverage analysis
                   - Confidence improvement projections
                   - Success metrics alignment
                   - ROI validation for questionnaire deployment

                Provide final quality assessment and recommendations.
                """,
                agent=self.agents[2],
                expected_output="Comprehensive quality validation report with final recommendations",
                context=(
                    [questionnaire_design_task, business_context_task]
                    if len(tasks) > 1
                    else [questionnaire_design_task]
                ),
            )
            tasks.append(quality_validation_task)

        return tasks

    def process_results(self, raw_results: Any) -> Dict[str, Any]:
        """Process questionnaire generation results"""
        try:
            # Extract and parse results
            if isinstance(raw_results, str):
                try:
                    import re

                    json_match = re.search(r"\{.*\}", raw_results, re.DOTALL)
                    if json_match:
                        parsed_results = json.loads(json_match.group())
                    else:
                        parsed_results = self._parse_text_results(raw_results)
                except Exception as e:
                    logger.warning(
                        f"Could not parse JSON from questionnaire generation results: {e}"
                    )
                    parsed_results = self._parse_text_results(raw_results)
            else:
                parsed_results = raw_results

            # Ensure required structure
            if not isinstance(parsed_results, dict):
                parsed_results = {"error": "Unexpected result format"}

            # Extract key components
            metadata = parsed_results.get("questionnaire_metadata", {})
            sections = parsed_results.get("questionnaire_sections", [])
            adaptive_logic = parsed_results.get("adaptive_logic", {})
            completion_criteria = parsed_results.get("completion_criteria", {})

            # Calculate questionnaire metrics
            total_questions = sum(
                len(section.get("questions", [])) for section in sections
            )
            critical_questions = sum(
                1
                for section in sections
                for question in section.get("questions", [])
                if question.get("priority") == "critical"
            )

            # Generate questionnaire deployment package
            deployment_package = self._create_deployment_package(
                metadata, sections, adaptive_logic, completion_criteria
            )

            return {
                "crew_name": self.name,
                "status": "completed",
                "questionnaire": {
                    "metadata": metadata,
                    "sections": sections,
                    "adaptive_logic": adaptive_logic,
                    "completion_criteria": completion_criteria,
                    "deployment_package": deployment_package,
                },
                "generation_metrics": {
                    "total_questions": total_questions,
                    "critical_questions": critical_questions,
                    "sections_count": len(sections),
                    "estimated_duration": metadata.get(
                        "estimated_duration_minutes", 20
                    ),
                    "adaptive_branches": len(adaptive_logic.get("branching_rules", [])),
                    "dynamic_questions": len(
                        adaptive_logic.get("dynamic_questions", [])
                    ),
                },
                "quality_assessment": {
                    "question_quality_score": self._assess_question_quality(sections),
                    "user_experience_score": self._assess_user_experience(
                        metadata, sections
                    ),
                    "data_quality_score": self._assess_data_quality(sections),
                    "business_alignment_score": self._assess_business_alignment(
                        sections
                    ),
                    "overall_quality_score": 0,  # Will be calculated
                },
                "recommendations": {
                    "deployment_readiness": self._assess_deployment_readiness(
                        metadata, sections
                    ),
                    "optimization_suggestions": self._generate_optimization_suggestions(
                        sections
                    ),
                    "integration_requirements": self._identify_integration_requirements(
                        sections
                    ),
                    "success_metrics": completion_criteria.get("success_metrics", []),
                },
                "metadata": {
                    "generation_timestamp": datetime.now(timezone.utc).isoformat(),
                    "agent_count": len(self.agents),
                    "task_count": len(self.tasks),
                    "questionnaire_version": metadata.get("version", "1.0"),
                },
            }

        except Exception as e:
            logger.error(f"Error processing questionnaire generation results: {e}")
            return {
                "crew_name": self.name,
                "status": "error",
                "error": str(e),
                "questionnaire": {"metadata": {"error": True}},
                "metadata": {
                    "generation_timestamp": datetime.now(timezone.utc).isoformat()
                },
            }

    def _parse_text_results(self, text_result: str) -> Dict[str, Any]:
        """Parse questionnaire from text when JSON parsing fails"""
        result = {
            "questionnaire_metadata": {"parsing_fallback": True},
            "questionnaire_sections": [],
            "adaptive_logic": {},
            "completion_criteria": {},
        }

        # Extract basic metrics from text
        lines = text_result.split("\n")
        question_count = 0

        for line in lines:
            line = line.strip().lower()
            if "question" in line and ("?" in line or "q-" in line):
                question_count += 1

        result["questionnaire_metadata"]["total_questions"] = question_count
        result["questionnaire_metadata"]["estimated_duration_minutes"] = max(
            10, question_count * 2
        )

        return result

    def _create_deployment_package(
        self,
        metadata: Dict,
        sections: List,
        adaptive_logic: Dict,
        completion_criteria: Dict,
    ) -> Dict[str, Any]:
        """Create deployment package for questionnaire"""
        return {
            "api_schema": {
                "questionnaire_id": metadata.get("id"),
                "version": metadata.get("version", "1.0"),
                "endpoints": {
                    "submit": "/api/v1/questionnaires/{id}/responses",
                    "validate": "/api/v1/questionnaires/{id}/validate",
                    "progress": "/api/v1/questionnaires/{id}/progress",
                },
            },
            "ui_configuration": {
                "theme": "migration_questionnaire",
                "layout": "progressive_disclosure",
                "features": ["save_progress", "validation_feedback", "help_tooltips"],
                "responsive_design": True,
            },
            "integration_points": {
                "database_tables": [
                    "collection_questionnaire_responses",
                    "collection_data_gaps",
                ],
                "workflow_triggers": ["gap_resolution", "confidence_update"],
                "notification_events": ["questionnaire_completed", "validation_failed"],
            },
            "deployment_checklist": [
                "Database schema validation",
                "API endpoint testing",
                "UI component integration",
                "Conditional logic validation",
                "User acceptance testing",
                "Performance optimization",
                "Security review",
                "Documentation completion",
            ],
        }

    def _assess_question_quality(self, sections: List[Dict]) -> float:
        """Assess question quality score"""
        if not sections:
            return 0.0

        total_questions = sum(len(section.get("questions", [])) for section in sections)
        if total_questions == 0:
            return 0.0

        quality_indicators = 0

        for section in sections:
            for question in section.get("questions", []):
                # Check for required quality indicators
                if question.get("help_text"):
                    quality_indicators += 1
                if question.get("validation_rules"):
                    quality_indicators += 1
                if question.get("question_type") in [
                    "single_select",
                    "multi_select",
                ] and question.get("options"):
                    quality_indicators += 1
                if question.get("gap_resolution"):
                    quality_indicators += 1

        max_possible_indicators = total_questions * 4
        return (
            (quality_indicators / max_possible_indicators) * 100
            if max_possible_indicators > 0
            else 0
        )

    def _assess_user_experience(self, metadata: Dict, sections: List[Dict]) -> float:
        """Assess user experience score"""
        score = 0
        max_score = 100

        # Duration appropriateness (20 points)
        duration = metadata.get("estimated_duration_minutes", 30)
        if duration <= 20:
            score += 20
        elif duration <= 30:
            score += 15
        elif duration <= 45:
            score += 10
        else:
            score += 5

        # Section organization (30 points)
        if len(sections) >= 2 and len(sections) <= 6:
            score += 30
        elif len(sections) == 1 or len(sections) > 6:
            score += 15

        # Question distribution (25 points)
        questions_per_section = [
            len(section.get("questions", [])) for section in sections
        ]
        if all(5 <= count <= 15 for count in questions_per_section):
            score += 25
        elif all(count <= 20 for count in questions_per_section):
            score += 15
        else:
            score += 5

        # Help and guidance (25 points)
        total_questions = sum(len(section.get("questions", [])) for section in sections)
        questions_with_help = sum(
            1
            for section in sections
            for question in section.get("questions", [])
            if question.get("help_text")
        )

        if total_questions > 0:
            help_percentage = (questions_with_help / total_questions) * 100
            if help_percentage >= 80:
                score += 25
            elif help_percentage >= 60:
                score += 20
            elif help_percentage >= 40:
                score += 15
            else:
                score += 10

        return min(score, max_score)

    def _assess_data_quality(self, sections: List[Dict]) -> float:
        """Assess data quality measures score"""
        if not sections:
            return 0.0

        total_questions = sum(len(section.get("questions", [])) for section in sections)
        if total_questions == 0:
            return 0.0

        validation_score = 0

        for section in sections:
            for question in section.get("questions", []):
                validation_rules = question.get("validation_rules", {})
                if validation_rules:
                    validation_score += 1
                    # Bonus for comprehensive validation
                    if len(validation_rules) >= 2:
                        validation_score += 0.5

        return min((validation_score / total_questions) * 100, 100)

    def _assess_business_alignment(self, sections: List[Dict]) -> float:
        """Assess business alignment score"""
        alignment_score = 0
        total_possible = 0

        for section in sections:
            total_possible += 1
            if section.get("target_stakeholders"):
                alignment_score += 0.5
            if section.get("section_description"):
                alignment_score += 0.5

            for question in section.get("questions", []):
                total_possible += 1
                gap_resolution = question.get("gap_resolution", {})
                if gap_resolution and gap_resolution.get("addresses_gap"):
                    alignment_score += 1

        return (alignment_score / total_possible) * 100 if total_possible > 0 else 0

    def _assess_deployment_readiness(self, metadata: Dict, sections: List[Dict]) -> str:
        """Assess questionnaire deployment readiness"""
        readiness_score = 0

        # Basic structure check
        if metadata and sections:
            readiness_score += 25

        # Question completeness
        total_questions = sum(len(section.get("questions", [])) for section in sections)
        if total_questions >= 5:
            readiness_score += 25

        # Validation rules
        questions_with_validation = sum(
            1
            for section in sections
            for question in section.get("questions", [])
            if question.get("validation_rules")
        )

        if total_questions > 0 and (questions_with_validation / total_questions) >= 0.7:
            readiness_score += 25

        # Help text coverage
        questions_with_help = sum(
            1
            for section in sections
            for question in section.get("questions", [])
            if question.get("help_text")
        )

        if total_questions > 0 and (questions_with_help / total_questions) >= 0.6:
            readiness_score += 25

        if readiness_score >= 80:
            return "ready"
        elif readiness_score >= 60:
            return "needs_minor_adjustments"
        elif readiness_score >= 40:
            return "needs_major_revisions"
        else:
            return "not_ready"

    def _generate_optimization_suggestions(self, sections: List[Dict]) -> List[str]:
        """Generate optimization suggestions"""
        suggestions = []

        total_questions = sum(len(section.get("questions", [])) for section in sections)

        if total_questions > 30:
            suggestions.append(
                "Consider reducing total question count to improve completion rates"
            )

        if len(sections) > 6:
            suggestions.append("Consider consolidating sections to improve navigation")

        questions_without_help = sum(
            1
            for section in sections
            for question in section.get("questions", [])
            if not question.get("help_text")
        )

        if questions_without_help > total_questions * 0.3:
            suggestions.append(
                "Add help text to more questions to improve user experience"
            )

        critical_questions = sum(
            1
            for section in sections
            for question in section.get("questions", [])
            if question.get("priority") == "critical"
        )

        if critical_questions < total_questions * 0.2:
            suggestions.append(
                "Consider marking more questions as critical to ensure essential data collection"
            )

        return suggestions

    def _identify_integration_requirements(self, sections: List[Dict]) -> List[str]:
        """Identify integration requirements"""
        requirements = []

        # Check for file upload questions
        has_file_upload = any(
            question.get("question_type") == "file_upload"
            for section in sections
            for question in section.get("questions", [])
        )

        if has_file_upload:
            requirements.append("File upload and storage capability")

        # Check for dependency mapping
        has_dependency_mapping = any(
            question.get("question_type") == "dependency_mapping"
            for section in sections
            for question in section.get("questions", [])
        )

        if has_dependency_mapping:
            requirements.append("Dependency visualization and mapping interface")

        # Check for technology selection
        has_tech_selection = any(
            question.get("question_type") == "technology_selection"
            for section in sections
            for question in section.get("questions", [])
        )

        if has_tech_selection:
            requirements.append("Technology stack selection interface")

        # Always required integrations
        requirements.extend(
            [
                "Database integration for response storage",
                "API endpoints for data submission and validation",
                "User authentication and authorization",
                "Progress tracking and session management",
            ]
        )

        return requirements

    async def generate_questionnaires(
        self,
        data_gaps: List[Dict[str, Any]],
        business_context: Optional[Dict[str, Any]] = None,
        automation_tier: str = "tier_2",
        collection_flow_id: Optional[str] = None,
        stakeholder_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate questionnaires based on identified data gaps.

        Args:
            data_gaps: List of identified data gaps from gap analysis
            business_context: Business environment context
            automation_tier: Current automation tier
            collection_flow_id: Optional collection flow ID
            stakeholder_context: Available stakeholder information

        Returns:
            List of generated questionnaires
        """
        try:
            logger.info(f"Starting questionnaire generation for {len(data_gaps)} gaps")

            # Prepare gap analysis structure
            gap_analysis = {
                "identified_gaps": data_gaps,
                "gaps_identified": len(data_gaps),
                "priority_gaps": [
                    gap for gap in data_gaps if gap.get("priority", 3) <= 2
                ],
                "gap_categories": list(
                    set(gap.get("category", "unknown") for gap in data_gaps)
                ),
            }

            # Prepare generation inputs
            generation_inputs = {
                "gap_analysis": gap_analysis,
                "collection_flow_id": collection_flow_id or "unknown",
                "business_context": business_context or {},
                "stakeholder_context": stakeholder_context or {},
                "automation_tier": automation_tier,
            }

            # Execute questionnaire generation using CrewAI
            logger.info(
                f"Executing questionnaire generation crew for automation tier: {automation_tier}"
            )
            results = await self.kickoff_async(generation_inputs)

            # Process results
            processed_results = self.process_results(results)

            # Extract questionnaires from processed results
            questionnaire_data = processed_results.get("questionnaire", {})
            sections = questionnaire_data.get("sections", [])

            # Convert sections to questionnaire format expected by the system
            questionnaires = []
            for section in sections:
                questionnaire = {
                    "id": section.get(
                        "section_id", f"questionnaire-{len(questionnaires)}"
                    ),
                    "title": section.get(
                        "section_title", "Data Collection Questionnaire"
                    ),
                    "description": section.get("section_description", ""),
                    "questions": section.get("questions", []),
                    "target_stakeholders": section.get("target_stakeholders", []),
                    "estimated_duration": section.get("estimated_duration_minutes", 15),
                    "metadata": {
                        "generation_timestamp": processed_results.get(
                            "metadata", {}
                        ).get("generation_timestamp"),
                        "automation_tier": automation_tier,
                        "gaps_addressed": len(
                            [
                                q
                                for q in section.get("questions", [])
                                if q.get("gap_resolution")
                            ]
                        ),
                    },
                }
                questionnaires.append(questionnaire)

            logger.info(f"Successfully generated {len(questionnaires)} questionnaires")
            return questionnaires

        except Exception as e:
            logger.error(f"Failed to generate questionnaires: {e}")
            # Return empty list on failure to prevent infinite loops
            return []


async def generate_adaptive_questionnaire(
    gap_analysis: Dict[str, Any],
    collection_flow_id: UUID,
    business_context: Optional[Dict[str, Any]] = None,
    stakeholder_context: Optional[Dict[str, Any]] = None,
    automation_tier: str = "tier_2",
) -> Dict[str, Any]:
    """
    High-level function to generate adaptive questionnaire using AI agents.

    Args:
        gap_analysis: Results from gap analysis agent
        collection_flow_id: UUID of the collection flow
        business_context: Business environment context
        stakeholder_context: Available stakeholder information
        automation_tier: Current automation tier

    Returns:
        Generated questionnaire with deployment package
    """
    try:
        # Initialize questionnaire generator
        questionnaire_generator = AdaptiveQuestionnaireGenerator()

        # Prepare generation inputs
        generation_inputs = {
            "gap_analysis": gap_analysis,
            "collection_flow_id": str(collection_flow_id),
            "business_context": business_context or {},
            "stakeholder_context": stakeholder_context or {},
            "automation_tier": automation_tier,
        }

        # Execute questionnaire generation
        logger.info(
            f"Starting questionnaire generation for collection flow: {collection_flow_id}"
        )
        results = await questionnaire_generator.kickoff_async(generation_inputs)

        logger.info(
            f"Questionnaire generation completed for collection flow: {collection_flow_id}"
        )
        return questionnaire_generator.process_results(results)

    except Exception as e:
        logger.error(f"Failed to generate adaptive questionnaire: {e}")
        return {
            "crew_name": "questionnaire_generation_crew",
            "status": "error",
            "error": str(e),
            "questionnaire": {"metadata": {"error": True}},
            "metadata": {
                "generation_timestamp": datetime.now(timezone.utc).isoformat()
            },
        }
