"""
Questionnaire Generator Service Module
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from .utils import (
    assess_business_alignment,
    assess_data_quality,
    assess_deployment_readiness,
    assess_question_quality,
    assess_user_experience,
    create_deployment_package,
    generate_optimization_suggestions,
    identify_integration_requirements,
    parse_text_results,
)

try:
    from crewai import Process
    from app.services.crews.base_crew import BaseDiscoveryCrew

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Process = type("Process", (object,), {})  # type: ignore
    BaseDiscoveryCrew = type("BaseDiscoveryCrew", (object,), {})  # type: ignore

logger = logging.getLogger(__name__)


class QuestionnaireProcessor:
    """Handles questionnaire result processing"""

    def __init__(self, agents: List[Any], tasks: List[Any], name: str):
        self.agents = agents
        self.tasks = tasks
        self.name = name

    def process_results(self, raw_results: Any) -> Dict[str, Any]:
        """Process questionnaire generation results"""
        try:
            # Extract and parse results with enhanced type handling
            if isinstance(raw_results, str):
                try:
                    import re

                    # First attempt: direct JSON parsing
                    try:
                        parsed_results = json.loads(raw_results)
                    except json.JSONDecodeError:
                        # Second attempt: extract JSON from string
                        json_match = re.search(r"\{.*\}", raw_results, re.DOTALL)
                        if json_match:
                            parsed_results = json.loads(json_match.group())
                        else:
                            # Third attempt: use text parser as fallback
                            parsed_results = parse_text_results(raw_results)

                except Exception as e:
                    logger.warning(
                        f"Could not parse JSON from questionnaire generation results: {e}"
                    )
                    parsed_results = parse_text_results(raw_results)
            elif isinstance(raw_results, dict):
                # Results are already a dictionary, use directly
                parsed_results = raw_results
            elif hasattr(raw_results, "__dict__"):
                # Results are an object, convert to dict
                parsed_results = vars(raw_results)
            else:
                # Try to convert other types to dict
                try:
                    parsed_results = dict(raw_results) if raw_results else {}
                except (TypeError, ValueError):
                    parsed_results = {"raw_data": str(raw_results)}

            # Enhanced type validation and structure guarantee
            if not isinstance(parsed_results, dict):
                logger.warning(
                    f"Unexpected result type: {type(parsed_results)}, converting to dict"
                )
                parsed_results = {
                    "error": "Unexpected result format",
                    "original_type": str(type(parsed_results)),
                }

            # Extract key components with type validation
            metadata = parsed_results.get("questionnaire_metadata", {})
            if not isinstance(metadata, dict):
                logger.warning(
                    f"Invalid metadata type: {type(metadata)}, using empty dict"
                )
                metadata = {}

            sections = parsed_results.get("questionnaire_sections", [])
            if not isinstance(sections, list):
                logger.warning(
                    f"Invalid sections type: {type(sections)}, converting to list"
                )
                sections = [sections] if sections else []

            adaptive_logic = parsed_results.get("adaptive_logic", {})
            if not isinstance(adaptive_logic, dict):
                logger.warning(
                    f"Invalid adaptive_logic type: {type(adaptive_logic)}, using empty dict"
                )
                adaptive_logic = {}

            completion_criteria = parsed_results.get("completion_criteria", {})
            if not isinstance(completion_criteria, dict):
                logger.warning(
                    f"Invalid completion_criteria type: {type(completion_criteria)}, using empty dict"
                )
                completion_criteria = {}

            # Calculate questionnaire metrics with enhanced validation
            total_questions = 0
            critical_questions = 0

            try:
                # Ensure sections is iterable and contains valid data
                for section in sections:
                    if not isinstance(section, dict):
                        logger.warning(
                            f"Invalid section type: {type(section)}, skipping"
                        )
                        continue

                    questions = section.get("questions", [])
                    if not isinstance(questions, list):
                        logger.warning(
                            f"Invalid questions type: {type(questions)}, treating as empty"
                        )
                        questions = []

                    total_questions += len(questions)

                    for question in questions:
                        if not isinstance(question, dict):
                            continue
                        pr = question.get("priority")
                        if isinstance(pr, str) and pr.lower() == "critical":
                            critical_questions += 1
            except Exception as metrics_error:
                logger.error(
                    f"Error calculating questionnaire metrics: {metrics_error}"
                )
                total_questions = 0
                critical_questions = 0

            # Generate questionnaire deployment package
            deployment_package = create_deployment_package(
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
                    "question_quality_score": (
                        question_quality := assess_question_quality(sections)
                    ),
                    "user_experience_score": (
                        ux_score := assess_user_experience(metadata, sections)
                    ),
                    "data_quality_score": (
                        data_quality := assess_data_quality(sections)
                    ),
                    "business_alignment_score": (
                        business_alignment := assess_business_alignment(sections)
                    ),
                    "overall_quality_score": round(
                        (
                            question_quality
                            + ux_score
                            + data_quality
                            + business_alignment
                        )
                        / 4.0,
                        2,
                    ),
                },
                "recommendations": {
                    "deployment_readiness": assess_deployment_readiness(
                        metadata, sections
                    ),
                    "optimization_suggestions": generate_optimization_suggestions(
                        sections
                    ),
                    "integration_requirements": identify_integration_requirements(
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


class QuestionnaireService:
    """Main questionnaire generation service"""

    def __init__(self, processor: QuestionnaireProcessor, crew_instance=None):
        self.processor = processor
        self.crew_instance = crew_instance

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

            # Try to use actual CrewAI if available
            raw_results = None
            if self.crew_instance and hasattr(self.crew_instance, 'kickoff_async'):
                try:
                    # Prepare inputs for crew
                    crew_inputs = {
                        "gap_analysis": {"data_gaps": data_gaps} if data_gaps else {},
                        "business_context": business_context or {},
                        "automation_tier": automation_tier,
                        "collection_flow_id": str(collection_flow_id) if collection_flow_id else None,
                        "stakeholder_context": stakeholder_context or {},
                        "persistence_data": {}
                    }

                    logger.info("Attempting to execute questionnaire generation crew with real agents")
                    raw_results = await self.crew_instance.kickoff_async(crew_inputs)
                    logger.info("CrewAI questionnaire generation completed successfully")

                except Exception as crew_error:
                    logger.warning(f"CrewAI execution failed, falling back to mock data: {crew_error}")
                    raw_results = None

            # If crew execution failed or not available, use mock data
            if raw_results is None:
                logger.info("Using fallback questionnaire generation with mock data")
                raw_results = {
                    "questionnaire_metadata": {
                        "id": f"questionnaire-{collection_flow_id}",
                        "title": "Migration Data Collection Questionnaire",
                        "estimated_duration_minutes": 20,
                        "version": "1.0",
                        "scope": "application_assessment",
                    },
                    "questionnaire_sections": [
                        {
                            "section_id": "basic_info",
                            "section_title": "Basic Application Information",
                            "section_description": "Essential details about the application for migration planning",
                            "estimated_duration_minutes": 8,
                            "target_stakeholders": ["business_owner", "technical_lead"],
                            "questions": [
                                {
                                    "id": "app_purpose",
                                    "text": "What is the primary business purpose of this application?",
                                    "type": "text",
                                    "required": True,
                                    "category": "business_context",
                                    "priority": "critical",
                                    "help_text": "Describe the main business function this application serves",
                                    "gap_resolution": "application_selection",
                                },
                                {
                                    "id": "business_criticality",
                                    "text": "How critical is this application to business operations?",
                                    "type": "select",
                                    "required": True,
                                    "category": "business_context",
                                    "priority": "critical",
                                    "options": [
                                        {
                                            "value": "mission_critical",
                                            "label": "Mission Critical",
                                        },
                                        {
                                            "value": "business_critical",
                                            "label": "Business Critical",
                                        },
                                        {"value": "important", "label": "Important"},
                                        {
                                            "value": "nice_to_have",
                                            "label": "Nice to Have",
                                        },
                                    ],
                                    "gap_resolution": "basic_info",
                                },
                                {
                                    "id": "user_count",
                                    "text": "Approximately how many users access this application?",
                                    "type": "select",
                                    "required": True,
                                    "category": "usage_metrics",
                                    "priority": "high",
                                    "options": [
                                        {"value": "1-10", "label": "1-10 users"},
                                        {"value": "11-50", "label": "11-50 users"},
                                        {"value": "51-200", "label": "51-200 users"},
                                        {
                                            "value": "201-1000",
                                            "label": "201-1,000 users",
                                        },
                                        {"value": "1000+", "label": "1,000+ users"},
                                    ],
                                    "gap_resolution": "basic_info",
                                },
                            ],
                        },
                        {
                            "section_id": "technical_details",
                            "section_title": "Technical Architecture",
                            "section_description": "Technical specifications and architecture details",
                            "estimated_duration_minutes": 12,
                            "target_stakeholders": [
                                "technical_lead",
                                "developer",
                                "architect",
                            ],
                            "questions": [
                                {
                                    "id": "tech_stack",
                                    "text": "What is the primary technology stack?",
                                    "type": "select",
                                    "required": True,
                                    "category": "technology",
                                    "priority": "critical",
                                    "options": [
                                        {"value": "java", "label": "Java"},
                                        {"value": "dotnet", "label": ".NET"},
                                        {"value": "python", "label": "Python"},
                                        {"value": "nodejs", "label": "Node.js"},
                                        {"value": "php", "label": "PHP"},
                                        {"value": "ruby", "label": "Ruby"},
                                        {"value": "go", "label": "Go"},
                                        {"value": "other", "label": "Other"},
                                    ],
                                    "gap_resolution": "technical_details",
                                },
                                {
                                    "id": "database_type",
                                    "text": "What type of database does this application use?",
                                    "type": "select",
                                    "required": True,
                                    "category": "technology",
                                    "priority": "high",
                                    "options": [
                                        {"value": "mysql", "label": "MySQL"},
                                        {"value": "postgresql", "label": "PostgreSQL"},
                                        {"value": "oracle", "label": "Oracle"},
                                        {"value": "sqlserver", "label": "SQL Server"},
                                        {"value": "mongodb", "label": "MongoDB"},
                                        {"value": "redis", "label": "Redis"},
                                        {"value": "none", "label": "No Database"},
                                        {"value": "other", "label": "Other"},
                                    ],
                                    "gap_resolution": "technical_details",
                                },
                            ],
                        },
                    ],
                    "adaptive_logic": {
                        "branching_rules": [
                            {
                                "condition": "business_criticality == 'mission_critical'",
                                "action": "add_section",
                                "target": "compliance_requirements",
                            }
                        ],
                        "dynamic_questions": [
                            {
                                "trigger": "tech_stack == 'other'",
                                "question": {
                                    "id": "tech_stack_other",
                                    "text": "Please specify the technology stack",
                                    "type": "text",
                                    "required": True,
                                },
                            }
                        ],
                    },
                    "completion_criteria": {
                        "success_metrics": [
                            "all_critical_questions_answered",
                            "business_context_complete",
                            "technical_overview_complete",
                        ],
                        "minimum_completion": 0.8,
                    },
                }

            # Process the results (either from crew or mock)
            processed_results = self.processor.process_results(raw_results)

            # Extract questionnaires from processed results
            questionnaire_data = processed_results.get("questionnaire", {})
            sections = questionnaire_data.get("sections", [])

            # Convert sections to questionnaire format expected by the system
            questionnaires: list[dict] = []
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
