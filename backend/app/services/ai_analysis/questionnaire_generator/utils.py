"""
Questionnaire Generator Utility Functions
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def parse_text_results(text_result: str) -> Dict[str, Any]:
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


def create_deployment_package(
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
                "submit": "/api/v1/collection/questionnaires/submit",
                "validate": "/api/v1/collection/questionnaires/validate",
                "progress": "/api/v1/collection/questionnaires/progress",
            },
        },
        "ui_configuration": {
            "theme": "migration_assessment",
            "progress_indicators": True,
            "save_resume": True,
            "validation_timing": "on_blur",
        },
        "integration_points": [
            "collection_flow_persistence",
            "gap_resolution_service",
            "6r_strategy_analysis",
        ],
        "deployment_checklist": [
            "API endpoints configured",
            "Database schema updated",
            "UI components tested",
            "Validation rules verified",
            "Integration tests passed",
        ],
    }


def assess_question_quality(sections: List[Dict]) -> float:
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


def assess_user_experience(metadata: Dict, sections: List[Dict]) -> float:
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
    questions_per_section = [len(section.get("questions", [])) for section in sections]
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


def assess_data_quality(sections: List[Dict]) -> float:
    """Assess data quality measures score"""
    if not sections:
        return 0.0

    total_questions = sum(len(section.get("questions", [])) for section in sections)
    if total_questions == 0:
        return 0.0

    validation_score = 0

    for section in sections:
        for question in section.get("questions", []):
            # Check validation completeness
            validation_rules = question.get("validation_rules", {})
            if validation_rules:
                validation_score += 1

                # Additional points for comprehensive validation
                if validation_rules.get("required"):
                    validation_score += 0.5
                if validation_rules.get("format") or validation_rules.get("pattern"):
                    validation_score += 0.5
                if validation_rules.get("min_length") or validation_rules.get(
                    "max_length"
                ):
                    validation_score += 0.5

    max_possible_score = total_questions * 2.5
    return (
        (validation_score / max_possible_score) * 100 if max_possible_score > 0 else 0
    )


def assess_business_alignment(sections: List[Dict]) -> float:
    """Assess business alignment score"""
    if not sections:
        return 0.0

    total_questions = sum(len(section.get("questions", [])) for section in sections)
    if total_questions == 0:
        return 0.0

    alignment_score = 0

    for section in sections:
        for question in section.get("questions", []):
            # Check gap resolution alignment
            gap_resolution = question.get("gap_resolution", {})
            if gap_resolution:
                alignment_score += 1

                # Additional points for priority alignment
                if gap_resolution.get("gap_priority", 3) <= 2:
                    alignment_score += 1
                if gap_resolution.get("confidence_improvement", 0) > 0:
                    alignment_score += 0.5

    max_possible_score = total_questions * 2.5
    return (alignment_score / max_possible_score) * 100 if max_possible_score > 0 else 0


def assess_deployment_readiness(metadata: Dict, sections: List[Dict]) -> str:
    """Assess deployment readiness level"""
    quality_score = assess_question_quality(sections)
    ux_score = assess_user_experience(metadata, sections)
    data_score = assess_data_quality(sections)
    business_score = assess_business_alignment(sections)

    overall_score = (quality_score + ux_score + data_score + business_score) / 4

    if overall_score >= 85:
        return "ready"
    elif overall_score >= 70:
        return "minor_adjustments"
    elif overall_score >= 50:
        return "major_improvements"
    else:
        return "requires_redesign"


def generate_optimization_suggestions(sections: List[Dict]) -> List[str]:
    """Generate optimization suggestions for questionnaire"""
    suggestions = []

    if not sections:
        return ["No sections found - questionnaire needs complete restructuring"]

    total_questions = sum(len(section.get("questions", [])) for section in sections)

    # Check question count
    if total_questions > 50:
        suggestions.append(
            "Consider reducing total question count for better completion rates"
        )
    elif total_questions < 10:
        suggestions.append("Consider adding more questions to improve gap coverage")

    # Check section distribution
    questions_per_section = [len(section.get("questions", [])) for section in sections]
    if any(count > 20 for count in questions_per_section):
        suggestions.append(
            "Some sections have too many questions - consider splitting into subsections"
        )

    # Check help text coverage
    questions_with_help = sum(
        1
        for section in sections
        for question in section.get("questions", [])
        if question.get("help_text")
    )

    if total_questions > 0:
        help_percentage = (questions_with_help / total_questions) * 100
        if help_percentage < 60:
            suggestions.append(
                "Add more help text to questions for better user guidance"
            )

    # Check validation coverage
    questions_with_validation = sum(
        1
        for section in sections
        for question in section.get("questions", [])
        if question.get("validation_rules")
    )

    if total_questions > 0:
        validation_percentage = (questions_with_validation / total_questions) * 100
        if validation_percentage < 70:
            suggestions.append(
                "Add validation rules to more questions for better data quality"
            )

    # Check gap resolution coverage
    questions_with_gaps = sum(
        1
        for section in sections
        for question in section.get("questions", [])
        if question.get("gap_resolution")
    )

    if total_questions > 0:
        gap_percentage = (questions_with_gaps / total_questions) * 100
        if gap_percentage < 80:
            suggestions.append("Ensure more questions are mapped to specific data gaps")

    if not suggestions:
        suggestions.append("Questionnaire appears well-optimized")

    return suggestions


def identify_integration_requirements(sections: List[Dict]) -> List[str]:
    """Identify integration requirements for questionnaire"""
    requirements = []

    if not sections:
        return ["Basic questionnaire framework integration required"]

    question_types = set()
    for section in sections:
        for question in section.get("questions", []):
            question_types.add(question.get("question_type", "unknown"))

    # Check for special question type requirements
    if "file_upload" in question_types:
        requirements.append("File upload and storage integration required")

    if "dependency_mapping" in question_types:
        requirements.append("Interactive dependency visualization component required")

    if "technology_selection" in question_types:
        requirements.append("Technology stack database integration required")

    # Check for adaptive logic requirements
    total_adaptive_rules = 0
    for section in sections:
        if isinstance(section, dict):
            adaptive_logic = section.get("adaptive_logic", {})
            total_adaptive_rules += len(adaptive_logic.get("branching_rules", []))
            total_adaptive_rules += len(adaptive_logic.get("dynamic_questions", []))

    if total_adaptive_rules > 0:
        requirements.append("Conditional logic engine integration required")

    # Check for stakeholder-specific features
    stakeholder_types = set()
    for section in sections:
        stakeholders = section.get("target_stakeholders", [])
        stakeholder_types.update(stakeholders)

    if len(stakeholder_types) > 1:
        requirements.append("Role-based access control integration required")

    # Standard requirements
    requirements.extend(
        [
            "Form validation framework integration",
            "Progress tracking and persistence",
            "Data export and reporting capabilities",
        ]
    )

    return requirements
