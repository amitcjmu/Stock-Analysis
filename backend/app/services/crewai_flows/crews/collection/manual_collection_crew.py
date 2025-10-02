"""
Manual Collection Crew
ADCS: Crew for manual data collection through intelligent questionnaire generation and validation
"""

import logging
from typing import Any, Dict, List, Optional

from crewai import Crew, Process

from app.services.crewai_flows.config.crew_factory import (
    create_agent,
    create_crew,
    create_task,
)

logger = logging.getLogger(__name__)


def create_manual_collection_crew(
    crewai_service,
    prioritized_gaps: List[Dict[str, Any]],
    resolution_plan: Dict[str, Any],
    context: Dict[str, Any],
    shared_memory: Optional[Any] = None,
):
    """
    Create a crew for manual collection phase

    Args:
        crewai_service: CrewAI service instance
        prioritized_gaps: Prioritized gaps from gap analysis phase
        resolution_plan: Resolution plan from gap analysis
        context: Additional context (user responses, validation rules, etc.)
        shared_memory: Shared memory for agent learning

    Returns:
        CrewAI Crew for manual collection
    """

    try:
        # Get LLM from service
        llm = crewai_service.get_llm()

        # Import optimized config
        from ..crew_config import DEFAULT_AGENT_CONFIG

        # Create questionnaire generation agent
        questionnaire_generator = create_agent(
            role="Dynamic Questionnaire Generation Expert",
            goal="Generate targeted, user-friendly questionnaires that efficiently collect missing critical data",
            backstory="""You are a questionnaire design expert specializing in technical data collection.

            You excel at:
            - Creating clear, unambiguous questions for technical and non-technical users
            - Grouping related questions for logical flow
            - Providing helpful context and examples
            - Minimizing user effort while maximizing data quality
            - Adapting questions based on user responses

            Your questionnaires balance completeness with user experience, ensuring high response rates
            and quality data collection.""",
            llm=llm,
            memory=shared_memory,
            **DEFAULT_AGENT_CONFIG,
        )

        # Create response validation agent
        response_validator = create_agent(
            role="Data Validation and Quality Assurance Specialist",
            goal="Validate user responses for completeness, accuracy, and consistency with existing data",
            backstory="""You are a data validation expert who ensures collected data meets quality standards.

            Your expertise includes:
            - Validating data formats and types
            - Cross-referencing responses with existing data
            - Detecting inconsistencies and anomalies
            - Ensuring business rule compliance
            - Identifying incomplete or ambiguous responses

            You ensure all manually collected data is accurate and ready for migration planning.""",
            llm=llm,
            memory=shared_memory,
            **DEFAULT_AGENT_CONFIG,
        )

        # Create collection progress agent
        collection_coordinator = create_agent(
            role="Manual Collection Coordination Expert",
            goal="Coordinate manual collection efforts, track progress, and optimize the collection process",
            backstory="""You are a collection coordination expert who manages manual data gathering.

            You specialize in:
            - Tracking questionnaire completion rates
            - Identifying collection bottlenecks
            - Prioritizing follow-up actions
            - Coordinating with stakeholders
            - Optimizing collection workflows

            Your coordination ensures manual collection is completed efficiently and on schedule.""",
            llm=llm,
            memory=shared_memory,
            **DEFAULT_AGENT_CONFIG,
        )

        # Extract context information
        existing_responses = context.get("existing_responses", {})
        validation_rules = context.get("validation_rules", {})
        user_preferences = context.get("user_preferences", {})

        # Create questionnaire generation task
        # Prepare gaps summary for description
        gaps_summary = []
        for g in prioritized_gaps[:5]:
            gaps_summary.append(
                {
                    "gap_id": g.get("gap_id"),
                    "attribute": g.get("attribute"),
                    "priority": g.get("priority"),
                    "affected_assets": g.get("records_affected", 0),
                }
            )

        questionnaire_task = create_task(
            description=f"""Generate targeted questionnaires for gap resolution:

            PRIORITIZED GAPS TO ADDRESS:
            {gaps_summary}

            RESOLUTION PLAN:
            - Immediate actions: {resolution_plan.get('immediate_actions', [])}
            - Total effort: {resolution_plan.get('total_effort_hours', 0)} hours
            - Recommended sequence: {resolution_plan.get('recommended_sequence', [])}

            USER PREFERENCES:
            - Question format: {user_preferences.get('format', 'form')}
            - Batch size: {user_preferences.get('batch_size', 10)}
            - Technical level: {user_preferences.get('technical_level', 'medium')}

            QUESTIONNAIRE REQUIREMENTS:
            1. QUESTION DESIGN:
               - Clear, specific questions for each gap
               - Appropriate input types (text, select, multi-select)
               - Helpful descriptions and examples
               - Validation rules for each field
               - Conditional logic where applicable

            2. USER EXPERIENCE:
               - Logical grouping of related questions
               - Progress indicators
               - Save and resume capability
               - Bulk input options where possible
               - Clear instructions and help text

            3. EFFICIENCY OPTIMIZATION:
               - Pre-populate known values
               - Smart defaults based on patterns
               - Skip logic to avoid irrelevant questions
               - Batch similar questions together
               - Quick-fill templates for common scenarios

            OUTPUT FORMAT:
            {{
                "questionnaires": [
                    {{
                        "questionnaire_id": "q-001",
                        "target_gap": "gap-001",
                        "title": "Application Technology Stack Assessment",
                        "description": "Help us understand the technology stack for your applications",
                        "estimated_time_minutes": 15,
                        "questions": [
                            {{
                                "question_id": "q1",
                                "field_name": "technology_stack",
                                "question_text": "What is the primary technology stack?",
                                "help_text": "e.g., Java/Spring Boot, .NET Core, Python/Django",
                                "input_type": "select",
                                "options": ["Java", ".NET", "Python", "Node.js", "Other"],
                                "required": true,
                                "validation_rule": "not_empty",
                                "affects_assets": ["app-123", "app-456"]
                            }}
                        ],
                        "completion_logic": {{
                            "save_progress": true,
                            "allow_partial": true,
                            "review_before_submit": true
                        }}
                    }}
                ],
                "collection_strategy": {{
                    "total_questions": 15,
                    "grouped_by": ["platform", "asset_type"],
                    "estimated_total_time": 45,
                    "bulk_options_available": true,
                    "template_suggestions": ["web_app_template", "database_template"]
                }}
            }}""",
            agent=questionnaire_generator,
            expected_output="JSON object with generated questionnaires and collection strategy",
        )

        # Create response validation task
        # This is not SQL, it's a task description for an AI agent
        validation_task = create_task(  # nosec B608
            description=f"""
            Validate responses as they are submitted:

            VALIDATION REQUIREMENTS:
            - Format validation (data types, patterns)
            - Business rule compliance
            - Consistency with existing data
            - Completeness checks
            - Logical validation

            EXISTING DATA CONTEXT:
            - Previous responses: {len(existing_responses)} entries
            - Known patterns: Infrastructure naming conventions, valid technology stacks
            - Business rules: {validation_rules}

            VALIDATION OBJECTIVES:
            1. FORMAT VALIDATION:
               - Check data types and formats
               - Validate against regex patterns
               - Ensure required fields are complete
               - Check value ranges and constraints

            2. CONSISTENCY CHECKS:
               - Cross-reference with existing asset data
               - Verify relationships are valid
               - Check for duplicate entries
               - Ensure naming conventions are followed

            3. BUSINESS LOGIC:
               - Validate against business rules
               - Check dependencies are satisfied
               - Ensure data makes business sense
               - Flag suspicious or unusual values

            4. QUALITY SCORING:
               - Calculate completeness score
               - Assess data confidence level
               - Identify areas needing clarification
               - Recommend follow-up questions

            OUTPUT FORMAT:
            {{
                "validation_results": {{
                    "total_responses": 25,
                    "valid_responses": 22,
                    "validation_errors": [
                        {{
                            "response_id": "r-001",
                            "field": "technology_stack",
                            "error_type": "invalid_value",
                            "message": "Unknown technology stack: 'Custom Framework'",
                            "suggestion": "Please select from standard options or provide more details"
                        }}
                    ],
                    "warnings": [
                        {{
                            "response_id": "r-003",
                            "field": "memory_gb",
                            "warning_type": "unusual_value",
                            "message": "Memory value (512GB) is unusually high for application server"
                        }}
                    ]
                }},
                "quality_metrics": {{
                    "overall_quality_score": 0.88,
                    "completeness": 0.92,
                    "consistency": 0.85,
                    "confidence_level": "high"
                }},
                "follow_up_needed": [
                    {{
                        "response_id": "r-001",
                        "clarification_needed": "technology_stack_details",
                        "suggested_question": "Please provide more details about your custom framework"
                    }}
                ]
            }}""",
            agent=response_validator,
            expected_output="JSON object with validation results and quality metrics",
            context=[questionnaire_task],
        )

        # Create collection coordination task
        coordination_task = create_task(
            description=f"""Coordinate and optimize the manual collection process:

            COLLECTION TARGETS:
            - Gaps to resolve: {len(prioritized_gaps)}
            - Priority 1 gaps: {len([g for g in prioritized_gaps if g.get('priority') == 1])}
            - Target completion: {resolution_plan.get('total_effort_hours', 24)} hours

            COORDINATION OBJECTIVES:
            1. PROGRESS TRACKING:
               - Monitor questionnaire completion rates
               - Track response quality scores
               - Identify slow-moving collections
               - Calculate time to completion

            2. STAKEHOLDER MANAGEMENT:
               - Identify responsible parties for each gap
               - Send reminders and follow-ups
               - Escalate blocked items
               - Coordinate SME availability

            3. OPTIMIZATION:
               - Identify patterns in responses
               - Suggest bulk update opportunities
               - Recommend process improvements
               - Prioritize high-impact collections

            4. COMPLETION ASSURANCE:
               - Verify all critical gaps addressed
               - Ensure quality thresholds met
               - Confirm 6R strategy requirements satisfied
               - Generate completion summary

            OUTPUT FORMAT:
            {{
                "collection_status": {{
                    "overall_progress": 0.75,
                    "gaps_resolved": 12,
                    "gaps_in_progress": 5,
                    "gaps_pending": 3,
                    "estimated_completion": "2024-01-16T18:00:00Z"
                }},
                "stakeholder_actions": [
                    {{
                        "action_type": "reminder",
                        "recipient": "app-owner@company.com",
                        "regarding": "Technology stack for critical apps",
                        "due_date": "2024-01-15T17:00:00Z",
                        "priority": "high"
                    }}
                ],
                "optimization_insights": {{
                    "patterns_detected": [
                        "80% of Java apps use Spring Boot framework",
                        "All Azure VMs have standard naming convention"
                    ],
                    "bulk_update_opportunities": [
                        {{
                            "pattern": "Java apps framework",
                            "affected_assets": 45,
                            "suggested_value": "Spring Boot",
                            "confidence": 0.8
                        }}
                    ],
                    "process_improvements": [
                        "Add Spring Boot as default for Java apps",
                        "Pre-populate owner based on cost center"
                    ]
                }},
                "completion_summary": {{
                    "critical_gaps_resolved": 10,
                    "data_quality_achieved": 0.89,
                    "sixr_confidence_improvement": "+25%",
                    "ready_for_migration_planning": true
                }}
            }}""",
            agent=collection_coordinator,
            expected_output="JSON object with coordination status and optimization insights",
            context=[questionnaire_task, validation_task],
        )

        # Import crew config
        from ..crew_config import get_optimized_crew_config

        # Create crew with optimized settings
        crew_config = get_optimized_crew_config()
        crew = create_crew(
            agents=[
                questionnaire_generator,
                response_validator,
                collection_coordinator,
            ],
            tasks=[questionnaire_task, validation_task, coordination_task],
            process="sequential",
            **crew_config,  # Apply optimized config
        )

        logger.info("✅ Manual Collection Crew created successfully")
        return crew

    except Exception as e:
        logger.error(f"❌ Failed to create manual collection crew: {e}")
        raise e
