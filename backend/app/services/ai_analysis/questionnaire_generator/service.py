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
    Process = object
    BaseDiscoveryCrew = object

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
            # Extract and parse results
            if isinstance(raw_results, str):
                try:
                    import re

                    json_match = re.search(r"\{.*\}", raw_results, re.DOTALL)
                    if json_match:
                        parsed_results = json.loads(json_match.group())
                    else:
                        parsed_results = parse_text_results(raw_results)
                except Exception as e:
                    logger.warning(
                        f"Could not parse JSON from questionnaire generation results: {e}"
                    )
                    parsed_results = parse_text_results(raw_results)
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
            critical_questions = 0
            for section in sections:
                for question in section.get("questions", []):
                    pr = question.get("priority")
                    if isinstance(pr, str) and pr.lower() == "critical":
                        critical_questions += 1

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

    def __init__(self, processor: QuestionnaireProcessor):
        self.processor = processor

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

            # Process results using mock data for now
            # In real implementation, this would call kickoff_async
            processed_results = self.processor.process_results(
                {
                    "questionnaire_metadata": {
                        "id": f"questionnaire-{collection_flow_id}",
                        "title": "Migration Data Collection Questionnaire",
                        "estimated_duration_minutes": 20,
                    },
                    "questionnaire_sections": [],
                    "adaptive_logic": {},
                    "completion_criteria": {},
                }
            )

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
