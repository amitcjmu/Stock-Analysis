"""
Gap Analysis Crew
ADCS: Crew for analyzing collected data gaps using intelligent agents
"""

import logging
from typing import Any, Dict, Optional

from crewai import Agent, Crew, Task

logger = logging.getLogger(__name__)


def create_gap_analysis_crew(
    crewai_service,
    collected_data: Dict[str, Any],
    quality_assessment: Dict[str, Any],
    context: Dict[str, Any],
    shared_memory: Optional[Any] = None,
):
    """
    Create a crew for gap analysis phase

    Args:
        crewai_service: CrewAI service instance
        collected_data: Data collected from automated collection phase
        quality_assessment: Quality assessment from collection phase
        context: Additional context (critical attributes, 6R requirements, etc.)
        shared_memory: Shared memory for agent learning

    Returns:
        CrewAI Crew for gap analysis
    """

    try:
        # Get LLM from service
        llm = crewai_service.get_llm()

        # Import optimized config
        from ..crew_config import DEFAULT_AGENT_CONFIG

        # Create gap analysis specialist agent
        gap_specialist = Agent(
            role="Data Gap Analysis Specialist",
            goal=(
                "Identify critical data gaps that impact 6R migration strategy accuracy "
                "and prioritize them for resolution"
            ),
            backstory="""You are an expert gap analysis specialist with deep understanding of:
            - The 22 critical attributes framework for migration
            - 6R strategy requirements (Rehost, Replatform, Refactor, Repurchase, Retire, Retain)
            - Data quality impact on migration decisions
            - Business criticality assessment

            You excel at:
            1. Analyzing collected data against critical attributes framework
            2. Identifying gaps that block or reduce confidence in 6R decisions
            3. Prioritizing gaps based on business impact and migration strategy
            4. Assessing data completeness and quality
            5. Recommending targeted collection strategies

            Your analysis ensures migration strategies are based on complete, accurate data.""",
            llm=llm,
            memory=shared_memory,
            **DEFAULT_AGENT_CONFIG,
        )

        # Create 6R impact assessor agent
        sixr_impact_assessor = Agent(
            role="6R Strategy Impact Assessment Expert",
            goal="Evaluate how identified gaps affect each 6R strategy option and calculate confidence impacts",
            backstory="""You are a 6R strategy expert who understands how data gaps affect migration decisions.

            You specialize in:
            - Assessing data requirements for each 6R strategy
            - Calculating confidence impacts from missing data
            - Identifying which gaps block specific strategies
            - Determining minimum data requirements for decisions
            - Evaluating risk levels for proceeding with gaps

            Your assessments ensure stakeholders understand the impact of data gaps on migration options.""",
            llm=llm,
            memory=shared_memory,
            **DEFAULT_AGENT_CONFIG,
        )

        # Create gap prioritization agent
        gap_prioritizer = Agent(
            role="Gap Prioritization and Resolution Expert",
            goal="Prioritize identified gaps and recommend optimal resolution strategies for each",
            backstory="""You are a gap resolution expert who prioritizes and plans gap remediation.

            Your expertise includes:
            - Prioritizing gaps by business impact and effort
            - Recommending collection methods (automated vs manual)
            - Estimating effort and timeline for gap resolution
            - Identifying quick wins vs complex gaps
            - Planning efficient gap resolution workflows

            You ensure gap resolution efforts are focused on highest-value activities.""",
            llm=llm,
            memory=shared_memory,
            **DEFAULT_AGENT_CONFIG,
        )

        # Extract context information
        context.get("critical_attributes_framework", {})
        context.get("sixr_requirements", {})
        business_priorities = context.get("business_priorities", {})

        # Calculate collection statistics
        total_records = sum(
            len(v.get("resources", []))
            for v in collected_data.values()
            if isinstance(v, dict)
        )
        platforms_collected = len(collected_data)
        avg_quality_score = quality_assessment.get("quality_assessment", {}).get(
            "overall_quality_score", 0
        )

        # Create gap analysis task
        gap_analysis_task = Task(
            description=f"""Analyze collected data to identify critical gaps:

            COLLECTION SUMMARY:
            - Platforms collected: {platforms_collected}
            - Total records: {total_records}
            - Average quality score: {avg_quality_score}

            CRITICAL ATTRIBUTES FRAMEWORK:
            Infrastructure: hostname, environment, os_type, cpu_cores, memory_gb, storage_gb
            Application: app_name, technology_stack, criticality, dependencies
            Operational: owner, cost_center, backup_strategy, monitoring_status
            Dependencies: app_dependencies, database_dependencies, integration_points

            ANALYSIS OBJECTIVES:
            1. ATTRIBUTE COVERAGE:
               - Map collected fields to critical attributes
               - Calculate coverage percentage per category
               - Identify missing critical attributes
               - Assess data quality for present attributes

            2. GAP IDENTIFICATION:
               - List all missing critical attributes
               - Identify incomplete or low-quality data
               - Find platform-specific gaps
               - Detect relationship/dependency gaps

            3. BUSINESS IMPACT:
               - Assess impact on migration planning
               - Identify decision-blocking gaps
               - Calculate risk of proceeding with gaps
               - Determine confidence reduction

            OUTPUT FORMAT:
            {{
                "gap_summary": {{
                    "total_critical_attributes": 22,
                    "attributes_collected": 16,
                    "coverage_percentage": 72.7,
                    "critical_gaps_count": 6,
                    "high_priority_gaps": 3
                }},
                "category_analysis": {{
                    "infrastructure": {{
                        "coverage": 85,
                        "missing": ["network_zone", "patch_level"],
                        "quality_issues": ["cpu_cores incomplete for 15% of assets"]
                    }},
                    "application": {{
                        "coverage": 65,
                        "missing": ["technology_stack", "criticality_level"],
                        "quality_issues": ["dependencies not mapped for 40% of apps"]
                    }}
                }},
                "identified_gaps": [
                    {{
                        "gap_id": "gap-001",
                        "attribute": "technology_stack",
                        "category": "application",
                        "platforms_affected": ["aws-prod", "azure-dev"],
                        "records_affected": 234,
                        "business_impact": "Cannot determine refactor vs replatform",
                        "data_availability": "manual_collection_required"
                    }}
                ]
            }}""",
            agent=gap_specialist,
            expected_output="JSON object with comprehensive gap analysis",
        )

        # Create 6R impact assessment task
        sixr_impact_task = Task(
            description="""Assess how identified gaps impact 6R strategy decisions:

            6R STRATEGY REQUIREMENTS:
            - Rehost: Infrastructure details, dependencies, performance metrics
            - Replatform: Technology stack, architecture, platform features
            - Refactor: Application complexity, code quality, APIs
            - Repurchase: Business functions, integration points, costs
            - Retire: Business value, usage metrics, dependencies
            - Retain: Operational costs, compliance, technical debt

            IMPACT ASSESSMENT:
            1. STRATEGY CONFIDENCE:
               - Calculate confidence score for each 6R option
               - Identify gaps that block specific strategies
               - Assess risk of wrong strategy selection
               - Determine minimum viable data for decisions

            2. DECISION IMPACTS:
               - Which strategies become non-viable due to gaps
               - Confidence reduction per strategy
               - Risk of migration failure per strategy
               - Cost impact of proceeding with gaps

            3. REMEDIATION PRIORITY:
               - Which gaps most impact preferred strategies
               - Quick wins that significantly boost confidence
               - Critical gaps that block all strategies
               - Gaps that can be deferred

            OUTPUT FORMAT:
            {
                "sixr_impact_analysis": {
                    "rehost": {
                        "confidence_score": 0.82,
                        "blocking_gaps": [],
                        "confidence_impact": "Medium - missing performance baselines",
                        "risk_level": "low"
                    },
                    "replatform": {
                        "confidence_score": 0.45,
                        "blocking_gaps": ["technology_stack", "platform_features"],
                        "confidence_impact": "High - cannot assess platform compatibility",
                        "risk_level": "high"
                    }
                },
                "strategy_recommendations": {
                    "viable_strategies": ["rehost", "retire"],
                    "blocked_strategies": ["refactor", "repurchase"],
                    "confidence_threshold_met": ["rehost"],
                    "remediation_required_for": ["replatform", "refactor"]
                },
                "critical_gaps_for_6r": [
                    {
                        "gap_id": "gap-001",
                        "strategies_affected": ["replatform", "refactor"],
                        "confidence_impact": -35,
                        "priority": "critical"
                    }
                ]
            }""",
            agent=sixr_impact_assessor,
            expected_output="JSON object with 6R strategy impact analysis",
            context=[gap_analysis_task],
        )

        # Create gap prioritization task
        gap_prioritization_task = Task(
            description=f"""Prioritize gaps and recommend resolution strategies:

            BUSINESS PRIORITIES:
            {business_priorities}

            PRIORITIZATION CRITERIA:
            1. Business impact (critical/high/medium/low)
            2. Number of assets affected
            3. 6R strategy impact
            4. Collection effort required
            5. Data availability

            RESOLUTION PLANNING:
            1. PRIORITY ASSIGNMENT:
               - P1: Critical gaps blocking decisions
               - P2: High-impact gaps reducing confidence
               - P3: Medium gaps affecting optimization
               - P4: Nice-to-have for completeness

            2. COLLECTION METHODS:
               - Automated: Additional API calls, database queries
               - Semi-automated: Bulk uploads, spreadsheet templates
               - Manual: Questionnaires, interviews, documentation review
               - Hybrid: Combination of methods

            3. EFFORT ESTIMATION:
               - Hours required per gap
               - Resources needed (SMEs, tools, access)
               - Dependencies and prerequisites
               - Optimal sequence for efficiency

            OUTPUT FORMAT:
            {{
                "prioritized_gaps": [
                    {{
                        "gap_id": "gap-001",
                        "priority": 1,
                        "attribute": "technology_stack",
                        "business_justification": "Blocks replatform/refactor decision for 234 critical apps",
                        "resolution_method": "questionnaire",
                        "estimated_effort_hours": 8,
                        "requires_sme": true,
                        "quick_win": false,
                        "dependencies": []
                    }}
                ],
                "resolution_plan": {{
                    "immediate_actions": [
                        "Deploy technology stack questionnaire",
                        "Schedule SME interviews for critical apps"
                    ],
                    "total_effort_hours": 24,
                    "recommended_sequence": ["gap-001", "gap-003", "gap-002"],
                    "parallel_activities": ["gap-004", "gap-005"],
                    "expected_coverage_improvement": 15
                }},
                "quick_wins": [
                    {{
                        "gap_id": "gap-006",
                        "improvement": "5% coverage increase",
                        "effort_hours": 1,
                        "method": "bulk_api_call"
                    }}
                ]
            }}""",
            agent=gap_prioritizer,
            expected_output="JSON object with prioritized gaps and resolution plan",
            context=[gap_analysis_task, sixr_impact_task],
        )

        # Import crew config
        from ..crew_config import get_optimized_crew_config

        # Create crew with optimized settings
        crew_config = get_optimized_crew_config()
        crew = Crew(
            agents=[gap_specialist, sixr_impact_assessor, gap_prioritizer],
            tasks=[gap_analysis_task, sixr_impact_task, gap_prioritization_task],
            process="sequential",
            **crew_config,  # Apply optimized config
        )

        logger.info("✅ Gap Analysis Crew created successfully")
        return crew

    except Exception as e:
        logger.error(f"❌ Failed to create gap analysis crew: {e}")
        raise e
