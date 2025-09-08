"""
Questionnaire Generator Tasks Module
"""

import json
from typing import Any, Dict, List

try:
    from crewai import Task

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Task = object


class QuestionnaireTaskManager:
    """Manager for questionnaire generation tasks"""

    def __init__(self, agents: List[Any]):
        self.agents = agents

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
               - CRITICAL: For each gap in the identified_gaps list, use the EXACT gap.field_name as the question_id
               - Example gap structure: {{"field_name": "business_owner", "priority": 1, "description": "..."}}
               - The question_id MUST be identical to gap.field_name
                 (e.g., "business_owner", "technology_stack", "environment")
               - This ensures questionnaire responses can be mapped back to resolve specific gaps
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

            7. CRITICAL REQUIREMENT - FIELD NAME PRESERVATION:
               - ALWAYS use the EXACT gap field_name as the question_id
               - This ensures gap resolution can match responses back to specific gaps
               - Do NOT generate custom IDs like "q-infra-001" - use gap.field_name directly
               - Processing pattern: For each gap in identified_gaps list:
                 * Extract gap["field_name"] (e.g., "business_owner", "technology_stack")
                 * Set question_id = gap["field_name"]
                 * Set addresses_gap = gap["field_name"]
               - The question_id MUST be identical to the gap's field_name for proper resolution

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
                                "question_id": "business_owner",
                                "question_text": "Who is the business owner or primary stakeholder "
                                                "for this application?",
                                "question_type": "text_input",
                                "priority": "critical",
                                "required": true,
                                "help_text": "Identify the business owner to understand "
                                            "accountability and decision-making authority",
                                "validation_rules": {{
                                    "required": true,
                                    "format": "string"
                                }},
                                "gap_resolution": {{
                                    "addresses_gap": "business_owner",
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
            expected_output=(
                "Comprehensive adaptive questionnaire specification with "
                "conditional logic and stakeholder targeting"
            ),
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
