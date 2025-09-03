"""
Gap Analysis Task Templates

This module contains task templates and prompts for gap analysis agents.
Extracted from gap_analysis_agent.py to maintain the 400-line file limit.
"""

import json
from typing import Any, Dict

try:
    from crewai import Task

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Task = object

from .gap_analysis_constants import CRITICAL_ATTRIBUTES_FRAMEWORK


def create_gap_analysis_task(
    inputs: Dict[str, Any],
    agent: Any,
    collection_flow_id: str = None,
    automation_tier: str = "tier_2",
) -> Task:
    """Create primary gap analysis task.

    Args:
        inputs: Task inputs containing collected data
        agent: CrewAI agent to execute the task
        collection_flow_id: Collection flow ID
        automation_tier: Automation tier level

    Returns:
        Gap analysis Task instance
    """
    if not CREWAI_AVAILABLE:
        raise RuntimeError("CrewAI is required but not available")

    collected_data = inputs.get("collected_data", [])

    description = f"""
    CRITICAL ATTRIBUTES GAP ANALYSIS

    Collection Flow ID: {collection_flow_id}
    Automation Tier: {automation_tier}
    Assets Analyzed: {len(collected_data)}

    CRITICAL ATTRIBUTES FRAMEWORK (22 Core Attributes):
    {json.dumps(CRITICAL_ATTRIBUTES_FRAMEWORK, indent=2)}

    COLLECTED DATA SAMPLE:
    {json.dumps(collected_data[:5], indent=2) if collected_data else "No data collected"}

    ANALYSIS OBJECTIVES:

    1. ATTRIBUTE COVERAGE ANALYSIS:
       - Map collected data fields to the 22 critical attributes framework
       - Identify missing primary attributes in each category
       - Calculate coverage percentage per category and overall
       - Assess data quality for available attributes

    2. 6R STRATEGY IMPACT ASSESSMENT:
       - Evaluate how missing attributes affect each 6R strategy confidence
       - Assign impact scores (critical, high, medium, low) per 6R strategy

    3. GAP PRIORITIZATION:
       - Priority 1 (Critical): Gaps blocking 6R strategy selection
       - Priority 2 (High): Gaps reducing confidence in recommendations
       - Priority 3 (Medium): Gaps affecting migration planning details
       - Priority 4 (Low): Nice-to-have attributes for optimization

    OUTPUT FORMAT:
    Return detailed JSON analysis with gap_analysis_summary, category_analysis,
    sixr_strategy_impact, prioritized_gaps, and automation_recommendations.
    """

    return Task(
        description=description,
        agent=agent,
        expected_output="Comprehensive JSON gap analysis report",
    )


def create_business_impact_task(
    inputs: Dict[str, Any], agent: Any, business_context: Dict[str, Any] = None
) -> Task:
    """Create business impact assessment task.

    Args:
        inputs: Task inputs
        agent: CrewAI agent to execute the task
        business_context: Additional business context

    Returns:
        Business impact assessment Task instance
    """
    if not CREWAI_AVAILABLE:
        raise RuntimeError("CrewAI is required but not available")

    description = f"""
    BUSINESS IMPACT ASSESSMENT FOR GAP ANALYSIS

    Business Context: {json.dumps(business_context or {}, indent=2)}

    ASSESSMENT OBJECTIVES:

    1. BUSINESS CRITICALITY EVALUATION:
       - Assess business impact of missing critical attributes
       - Evaluate risk to migration timeline and budget
       - Determine stakeholder impact levels

    2. MIGRATION READINESS SCORING:
       - Calculate readiness score based on attribute coverage
       - Identify readiness blockers and risks
       - Recommend readiness improvement actions

    3. COST-BENEFIT ANALYSIS:
       - Estimate effort required for gap resolution
       - Assess automation potential for missing data
       - Prioritize gaps by business value vs. collection effort

    OUTPUT FORMAT:
    Return business impact assessment with readiness scores, risk analysis,
    and prioritized recommendations.
    """

    return Task(
        description=description,
        agent=agent,
        expected_output="Business impact and readiness assessment JSON report",
    )


def create_quality_validation_task(inputs: Dict[str, Any], agent: Any) -> Task:
    """Create quality validation task.

    Args:
        inputs: Task inputs
        agent: CrewAI agent to execute the task

    Returns:
        Quality validation Task instance
    """
    if not CREWAI_AVAILABLE:
        raise RuntimeError("CrewAI is required but not available")

    description = """
    QUALITY VALIDATION AND CONSISTENCY CHECK

    VALIDATION OBJECTIVES:

    1. ANALYSIS COMPLETENESS:
       - Verify all critical attribute categories are addressed
       - Check for logical consistency in gap identification
       - Validate 6R strategy impact assessments

    2. RECOMMENDATION QUALITY:
       - Ensure recommendations are actionable and specific
       - Validate priority assignments are logical
       - Check automation feasibility assessments

    3. OUTPUT CONSISTENCY:
       - Verify JSON structure completeness
       - Check data type consistency
       - Validate numerical scores and percentages

    OUTPUT FORMAT:
    Return quality validation report with validation results,
    consistency checks, and any corrections needed.
    """

    return Task(
        description=description,
        agent=agent,
        expected_output="Quality validation and consistency report",
    )


def get_expected_output_format() -> Dict[str, Any]:
    """Get the expected output format for gap analysis.

    Returns:
        Dictionary describing expected output structure
    """
    return {
        "gap_analysis_summary": {
            "total_attributes_framework": "int",
            "attributes_collected": "int",
            "overall_coverage_percentage": "float",
            "critical_gaps_count": "int",
            "automation_feasibility": "string",
        },
        "category_analysis": {
            "infrastructure": {
                "coverage_percentage": "float",
                "missing_attributes": "list[string]",
                "available_attributes": "list[string]",
                "data_quality_score": "float",
                "business_impact": "string",
            }
            # Similar structure for application, operational, dependencies
        },
        "sixr_strategy_impact": {
            "rehost": {
                "confidence_impact": "float",
                "blocking_gaps": "list[string]",
                "impact_severity": "string",
            }
            # Similar structure for other 6R strategies
        },
        "prioritized_gaps": {
            "critical": "list[dict]",
            "high": "list[dict]",
            "medium": "list[dict]",
            "low": "list[dict]",
        },
        "automation_recommendations": {
            "api_collectable": "list[string]",
            "manual_collection": "list[string]",
            "questionnaire_required": "list[string]",
        },
    }


def validate_gap_analysis_output(output: Dict[str, Any]) -> bool:
    """Validate gap analysis output structure.

    Args:
        output: Gap analysis output to validate

    Returns:
        True if valid, False otherwise
    """
    required_sections = [
        "gap_analysis_summary",
        "category_analysis",
        "sixr_strategy_impact",
        "prioritized_gaps",
    ]

    return all(section in output for section in required_sections)
