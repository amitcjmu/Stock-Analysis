"""
Planning Tasks - CrewAI Task Definitions for Planning Flow

This module contains task creation functions for planning-related CrewAI agents.

Task Definitions:
1. Wave Planning Task - Organize applications into optimal migration waves

Each task includes:
- Detailed description with analysis requirements
- Expected output format and structure
- Agent assignment and context dependencies

References:
- Pattern source: architecture_standards_crew/tasks.py
- ADR-024: TenantMemoryManager (CrewAI memory disabled)
- ADR-029: LLM JSON sanitization required
- ADR-031: CallbackHandlerIntegration for observability
"""

import logging
from typing import Any, Dict, List

# CrewAI imports with fallback
try:
    from crewai import Task

    CREWAI_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ CrewAI Task imports successful for PlanningTasks")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"CrewAI not available: {e}")
    CREWAI_AVAILABLE = False

    # Fallback class
    class Task:
        """Fallback Task class when CrewAI is not available"""

        def __init__(self, **kwargs):
            self.description = kwargs.get("description", "")
            self.expected_output = kwargs.get("expected_output", "")
            self.agent = kwargs.get("agent")
            self.context = kwargs.get("context", [])


def create_wave_planning_task(
    agent: Any,
    applications: List[Dict[str, Any]],
    dependencies: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Task:
    """
    Create a wave planning task for the wave planning specialist agent.

    This task analyzes application dependencies and creates an optimal wave plan
    that minimizes risk while maximizing migration efficiency.

    Args:
        agent: Wave planning specialist agent instance
        applications: List of applications to migrate with metadata
        dependencies: List of application dependencies
        config: Wave planning configuration parameters

    Returns:
        Task instance configured for wave planning

    Example:
        >>> from app.services.agent_registry import agent_registry
        >>> agent = agent_registry.get_agent("wave_planning_specialist")
        >>> applications = [
        ...     {"id": "app1", "name": "Web App", "complexity": "medium"},
        ...     {"id": "app2", "name": "API Gateway", "complexity": "high"}
        ... ]
        >>> dependencies = [
        ...     {"source": "app1", "target": "app2", "type": "api_call"}
        ... ]
        >>> config = {"max_apps_per_wave": 50, "wave_duration_days": 90}
        >>> task = create_wave_planning_task(agent, applications, dependencies, config)
    """
    logger.info(
        f"Creating wave planning task for {len(applications)} applications "
        f"with {len(dependencies)} dependencies"
    )

    # Extract configuration parameters
    max_apps_per_wave = config.get("max_apps_per_wave", 50)
    wave_duration_days = config.get("wave_duration_days", 90)
    prioritize_parallel = config.get("prioritize_parallel_migration", True)
    business_criticality = config.get("consider_business_criticality", True)

    # Build application context summary
    app_summary = {
        "total_applications": len(applications),
        "total_dependencies": len(dependencies),
        "complexity_distribution": _calculate_complexity_distribution(applications),
        "criticality_levels": _calculate_criticality_levels(applications),
        "sixr_strategy_distribution": _calculate_sixr_distribution(applications),
    }

    # Build application list for agent (CRITICAL: agent needs actual IDs and names)
    # Format concisely to stay within token limits
    app_list_for_agent = _format_applications_for_agent(applications)

    task = Task(
        description=f"""Analyze {len(applications)} applications and their {len(dependencies)}
        dependencies to create an optimal migration wave plan.

        OBJECTIVES:
        1. Dependency Analysis:
           - Build dependency graph from provided relationships
           - Identify critical path and sequential migration requirements
           - Detect circular dependencies and resolve them
           - Calculate dependency depth for each application
           - Identify independent applications for parallel migration

        2. Wave Sequencing:
           - Group independent applications for parallel migration
           - Sequence dependent applications in correct execution order
           - Balance wave sizes (target: {max_apps_per_wave} apps/wave, duration: {wave_duration_days} days)
           - Minimize cross-wave dependencies for reduced migration risk
           - Ensure prerequisite applications migrate before dependents

        3. Optimization Criteria:
           {'- Prioritize parallel migration opportunities' if prioritize_parallel else ''}
           {'- Consider business criticality and compliance requirements' if business_criticality else ''}
           - Minimize total migration timeline
           - Balance resource utilization across waves
           - Account for rollback complexity and risk mitigation
           - Optimize for minimum downtime windows
           - IMPORTANT: Balance 6R strategies across waves for resource team specialization
             (e.g., Rehost teams, Replatform teams have finite capacity per wave)

        4. Risk Mitigation:
           - Identify high-risk dependencies and plan safeguards
           - Ensure pilot wave contains manageable complexity
           - Plan for rollback scenarios in each wave
           - Flag applications requiring special handling

        APPLICATION CONTEXT:
        {app_summary}

        APPLICATIONS LIST (use these EXACT IDs and names in your output):
        {app_list_for_agent}

        CONFIGURATION:
        - Max applications per wave: {max_apps_per_wave}
        - Wave duration limit: {wave_duration_days} days
        - Prioritize parallel migration: {prioritize_parallel}
        - Consider business criticality: {business_criticality}

        Provide a comprehensive wave plan with clear rationale for sequencing decisions.
        """,
        expected_output="""A structured wave plan in JSON format containing:

        {{
          "waves": [
            {{
              "wave_id": "wave_1",
              "wave_number": 1,
              "wave_name": "Wave 1 - Pilot",
              "application_count": <int>,
              "applications": [
                {{
                  "application_id": "<uuid>",
                  "application_name": "<string>",
                  "dependency_depth": <int>,
                  "criticality": "<string>",
                  "complexity": "<string>",
                  "rationale": "<string explaining why in this wave>"
                }}
              ],
              "start_date": "<ISO 8601 date>",
              "end_date": "<ISO 8601 date>",
              "duration_days": <int>,
              "status": "planned",
              "description": "<string describing wave focus>",
              "dependencies_on_previous_waves": <int>,
              "parallel_migration_opportunities": <int>,
              "risk_level": "<low|medium|high>",
              "groups": [
                {{
                  "group_id": "wave_1_group_1",
                  "group_name": "<string>",
                  "application_count": <int>,
                  "migration_strategy": "<6R strategy>",
                  "parallel_execution": <boolean>
                }}
              ]
            }}
          ],
          "summary": {{
            "total_waves": <int>,
            "total_apps": <int>,
            "total_groups": <int>,
            "estimated_duration_days": <int>,
            "optimization_rationale": "<string explaining key decisions>",
            "critical_path_length": <int>,
            "parallel_migration_percentage": <float 0-100>
          }},
          "dependency_analysis": {{
            "total_dependencies": <int>,
            "cross_wave_dependencies": <int>,
            "circular_dependencies_resolved": <int>,
            "independent_applications": <int>,
            "max_dependency_depth": <int>
          }},
          "risk_assessment": {{
            "overall_risk_level": "<low|medium|high>",
            "high_risk_applications": [<application_ids>],
            "mitigation_strategies": [
              {{
                "risk": "<string>",
                "mitigation": "<string>",
                "wave_affected": <int>
              }}
            ]
          }},
          "recommendations": [
            "<string: actionable recommendations for successful migration>"
          ]
        }}

        CRITICAL REQUIREMENTS:
        1. All applications must be assigned to exactly one wave
        2. Dependencies must be respected (no app migrates before its dependencies)
        3. Wave sizes should be balanced (variance < 20% of target size)
        4. Provide clear rationale for sequencing decisions
        5. Include risk mitigation strategies for each wave
        6. Return ONLY valid JSON (no markdown wrappers, no trailing commas)
        7. USE THE EXACT application_id AND application_name FROM THE APPLICATIONS LIST PROVIDED
           DO NOT make up generic names like "Application 1" - use the real names!
        8. Balance 6R strategies across waves to optimize resource team capacity
        """,
        agent=(agent._agent if hasattr(agent, "_agent") else agent),
        context=[],  # No dependent tasks for initial wave planning
    )

    logger.info("Created wave planning task successfully")
    return task


def _calculate_complexity_distribution(
    applications: List[Dict[str, Any]],
) -> Dict[str, int]:
    """Calculate distribution of applications by complexity level."""
    distribution = {"low": 0, "medium": 0, "high": 0, "unknown": 0}

    for app in applications:
        complexity = app.get("complexity", "unknown").lower()
        if complexity in distribution:
            distribution[complexity] += 1
        else:
            distribution["unknown"] += 1

    return distribution


def _calculate_criticality_levels(applications: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate distribution of applications by business criticality."""
    levels = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}

    for app in applications:
        criticality = app.get("business_criticality", "unknown").lower()
        if criticality in levels:
            levels[criticality] += 1
        else:
            levels["unknown"] += 1

    return levels


def _calculate_sixr_distribution(applications: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate distribution of applications by 6R migration strategy."""
    # Standard 6R strategies
    strategies = {
        "rehost": 0,
        "replatform": 0,
        "refactor": 0,
        "repurchase": 0,
        "retire": 0,
        "retain": 0,
        "unknown": 0,
    }

    for app in applications:
        strategy = (
            (
                app.get("migration_strategy", "")
                or app.get("six_r_strategy", "")
                or "unknown"
            )
            .lower()
            .replace("-", "")
            .replace(" ", "")
        )
        # Normalize strategy name (handles "re-host", "re host", etc.)
        if strategy in strategies:
            strategies[strategy] += 1
        else:
            strategies["unknown"] += 1

    return strategies


def _format_applications_for_agent(applications: List[Dict[str, Any]]) -> str:
    """
    Format applications list for agent prompt.

    Creates a VERY concise representation to minimize token usage.
    Uses short format: id|name|strategy|complexity|criticality

    For large app lists (>20), only show first 8 chars of UUID to save tokens.
    """
    lines = []
    use_short_id = len(applications) > 20

    for app in applications:
        app_id = app.get("id")
        if not app_id:
            logger.warning(
                f"Skipping application with missing ID: {app.get('name', 'N/A')}"
            )
            continue

        # Shorten UUID for large lists
        display_id = app_id[:8] if use_short_id else app_id
        name = app.get("name", f"App_{app_id[:8]}")
        # Truncate long names
        if len(name) > 30:
            name = name[:27] + "..."
        strategy = (
            app.get("migration_strategy", "")
            or app.get("six_r_strategy", "")
            or "rehost"
        )[
            :10
        ]  # Truncate strategy name
        complexity = app.get("complexity", "medium")[:3]  # low/med/hig
        criticality = app.get("business_criticality", "medium")[:3]

        # Ultra-compact format
        line = f"{display_id}|{name}|{strategy}|{complexity}|{criticality}"
        lines.append(line)

    header = "Format: id|name|strategy|complexity|criticality"
    return header + "\n        " + "\n        ".join(lines)


# Export factory function
__all__ = ["create_wave_planning_task"]
