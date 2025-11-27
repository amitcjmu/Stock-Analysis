"""6R Strategy Resource Estimation Module - estimates FTEs based on migration strategies."""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.schemas.planning.resource import (
    ResourceTeam,
    TeamAssignment,
    ResourceMetrics,
    ResourceRecommendation,
    UpcomingNeed,
)

logger = logging.getLogger(__name__)

# 6R Strategy effort multipliers (person-days per application)
# These represent TOTAL effort including:
# - Discovery, assessment, design phases
# - Build/configure, data migration, testing
# - Cutover coordination, rehearsals, actual cutover
# - PMO, stakeholder management, risk management
# - Cloud environment setup, security, networking
# - Training, documentation, hypercare support
STRATEGY_EFFORT = {
    "rehost": {
        "days_per_app": 25,  # Lift-and-shift still requires planning, testing, cutover
        "skills": [
            "Cloud Operations",
            "DevOps",
            "Data Migration",
            "PMO",
            "QA Engineering",
        ],
    },
    "replatform": {
        "days_per_app": 45,  # Platform changes require more testing and validation
        "skills": [
            "Cloud Operations",
            "Backend Development",
            "DevOps",
            "Data Migration",
            "QA Engineering",
            "PMO",
        ],
    },
    "refactor": {
        "days_per_app": 90,  # Significant code changes, extensive testing
        "skills": [
            "Backend Development",
            "Frontend Development",
            "Cloud Architecture",
            "DevOps",
            "QA Engineering",
            "Data Migration",
            "PMO",
        ],
    },
    "repurchase": {
        "days_per_app": 30,  # SaaS evaluation, data migration, training
        "skills": [
            "Business Analysis",
            "Procurement",
            "Change Management",
            "Data Migration",
            "Training",
            "PMO",
        ],
    },
    "retain": {
        "days_per_app": 5,  # Minimal effort - documentation and monitoring
        "skills": ["Operations", "PMO"],
    },
    "retire": {
        "days_per_app": 15,  # Data archival, dependency cleanup, decommission
        "skills": ["Operations", "Data Migration", "PMO"],
    },
    # Fallback for unknown strategies
    "default": {
        "days_per_app": 35,
        "skills": [
            "Cloud Operations",
            "Backend Development",
            "DevOps",
            "QA Engineering",
            "PMO",
        ],
    },
}

# Default project duration in working days (3 months)
DEFAULT_PROJECT_DURATION_DAYS = 60


def _aggregate_effort_by_skill(
    waves: List[Dict[str, Any]],
) -> tuple[Dict[str, float], Dict[str, int], int]:
    """
    Aggregate effort by skill across all waves.

    Args:
        waves: List of wave dictionaries with applications

    Returns:
        Tuple of (skill_effort_days, strategy_counts, total_apps)
    """
    skill_effort_days: Dict[str, float] = defaultdict(float)
    strategy_counts: Dict[str, int] = defaultdict(int)
    total_apps = 0

    for wave in waves:
        applications = wave.get("applications", [])
        total_apps += len(applications)

        for app in applications:
            strategy = (app.get("migration_strategy") or "default").lower()
            strategy_counts[strategy] += 1

            effort_config = STRATEGY_EFFORT.get(strategy, STRATEGY_EFFORT["default"])
            days_per_app = effort_config["days_per_app"]
            skills = effort_config["skills"]

            days_per_skill = days_per_app / len(skills) if skills else days_per_app
            for skill in skills:
                skill_effort_days[skill] += days_per_skill

    return skill_effort_days, strategy_counts, total_apps


def _extract_date_range(waves: List[Dict[str, Any]]) -> tuple[str, str]:
    """
    Extract date range from waves for assignment dates.

    Args:
        waves: List of wave dictionaries

    Returns:
        Tuple of (start_date, end_date) as ISO format strings
    """
    all_start_dates = []
    all_end_dates = []

    for wave in waves:
        if wave.get("start_date"):
            try:
                all_start_dates.append(wave["start_date"])
            except (ValueError, TypeError):
                pass
        if wave.get("end_date"):
            try:
                all_end_dates.append(wave["end_date"])
            except (ValueError, TypeError):
                pass

    if all_start_dates:
        assignment_start = min(all_start_dates)
    else:
        assignment_start = datetime.now().strftime("%Y-%m-%d")

    if all_end_dates:
        assignment_end = max(all_end_dates)
    else:
        assignment_end = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")

    return assignment_start, assignment_end


def _build_teams_from_effort(
    skill_effort_days: Dict[str, float],
    assignment_start: str,
    assignment_end: str,
    project_duration_days: int = DEFAULT_PROJECT_DURATION_DAYS,
) -> tuple[List[ResourceTeam], int]:
    """
    Build ResourceTeam objects from skill effort calculations.

    Args:
        skill_effort_days: Dict mapping skills to total effort days
        assignment_start: Start date for assignments
        assignment_end: End date for assignments
        project_duration_days: Project duration in working days

    Returns:
        Tuple of (teams list, total_ftes)
    """
    teams = []
    total_ftes = 0

    for skill, effort_days in skill_effort_days.items():
        ftes_needed = effort_days / project_duration_days
        ftes_rounded = max(1, round(ftes_needed))
        total_ftes += ftes_rounded

        utilization = min(
            100, (effort_days / (ftes_rounded * project_duration_days)) * 100
        )

        teams.append(
            ResourceTeam(
                id=skill.lower().replace(" ", "-"),
                name=f"{skill} Team",
                size=ftes_rounded,
                skills=[skill],
                availability=100 - utilization,
                utilization=round(utilization, 1),
                assignments=[
                    TeamAssignment(
                        project="Migration Waves",
                        allocation=round(utilization, 1),
                        start_date=assignment_start,
                        end_date=assignment_end,
                    )
                ],
            )
        )

    return teams, total_ftes


def _build_metrics(
    teams: List[ResourceTeam],
    skill_effort_days: Dict[str, float],
    total_ftes: int,
) -> ResourceMetrics:
    """
    Build ResourceMetrics from teams and skill data.

    Args:
        teams: List of ResourceTeam objects
        skill_effort_days: Dict mapping skills to effort days
        total_ftes: Total FTE count

    Returns:
        ResourceMetrics object
    """
    skill_coverage = {skill: 100.0 for skill in skill_effort_days.keys()}
    avg_utilization = sum(t.utilization for t in teams) / len(teams) if teams else 0

    return ResourceMetrics(
        total_teams=len(teams),
        total_resources=total_ftes,
        average_utilization=round(avg_utilization, 1),
        skill_coverage=skill_coverage,
    )


def _identify_upcoming_needs(teams: List[ResourceTeam]) -> List[UpcomingNeed]:
    """
    Identify skill gaps from teams with high utilization.

    Args:
        teams: List of ResourceTeam objects

    Returns:
        List of UpcomingNeed objects
    """
    upcoming_needs = []
    for team in teams:
        if team.utilization > 80:
            upcoming_needs.append(
                UpcomingNeed(
                    skill=team.skills[0] if team.skills else team.name,
                    demand=team.size + 1,
                    timeline="Next 30 days",
                )
            )
    return upcoming_needs


def generate_6r_recommendations(
    teams: List[ResourceTeam],
    strategy_counts: Dict[str, int],
    total_apps: int,
) -> List[ResourceRecommendation]:
    """
    Generate recommendations based on 6R strategy analysis.

    Args:
        teams: Estimated teams from 6R analysis
        strategy_counts: Count of apps by strategy
        total_apps: Total applications being migrated

    Returns:
        List of ResourceRecommendation schemas
    """
    recommendations = []

    # High utilization warnings
    high_util_teams = [t for t in teams if t.utilization > 80]
    if high_util_teams:
        team_names = ", ".join(t.name for t in high_util_teams[:3])
        recommendations.append(
            ResourceRecommendation(
                type="capacity",
                description=f"{team_names} will be at high utilization. "
                f"Consider adding capacity or extending timeline.",
                impact="High",
            )
        )

    # Strategy mix insights
    refactor_count = strategy_counts.get("refactor", 0)
    if refactor_count > 0 and total_apps > 0:
        refactor_pct = (refactor_count / total_apps) * 100
        if refactor_pct > 30:
            recommendations.append(
                ResourceRecommendation(
                    type="planning",
                    description=f"{refactor_pct:.0f}% of applications require Refactoring. "
                    f"This is resource-intensive - ensure adequate dev resources.",
                    impact="High",
                )
            )

    # Rehost opportunity
    rehost_count = strategy_counts.get("rehost", 0)
    if rehost_count > 0:
        recommendations.append(
            ResourceRecommendation(
                type="optimization",
                description=f"{rehost_count} applications can be Rehosted quickly. "
                f"Consider parallelizing these for quick wins.",
                impact="Medium",
            )
        )

    # General recommendation
    if teams:
        recommendations.append(
            ResourceRecommendation(
                type="planning",
                description=f"Estimated {sum(t.size for t in teams)} FTEs needed across "
                f"{len(teams)} skill areas for {total_apps} applications.",
                impact="Medium",
            )
        )

    return recommendations


def estimate_resources_from_6r(wave_plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Estimate resource requirements based on 6R strategies in wave applications.

    Analyzes each application's migration_strategy and calculates:
    - Total effort days by skill
    - FTE requirements
    - Team composition recommendations

    Args:
        wave_plan_data: Wave plan data with waves and applications

    Returns:
        Dict with teams, metrics, recommendations, upcoming_needs
    """
    waves = wave_plan_data.get("waves", [])

    if not waves:
        return {
            "teams": [],
            "metrics": {
                "total_teams": 0,
                "total_resources": 0,
                "average_utilization": 0,
                "skill_coverage": {},
            },
            "recommendations": [],
            "upcoming_needs": [],
        }

    # Step 1: Aggregate effort by skill
    skill_effort_days, strategy_counts, total_apps = _aggregate_effort_by_skill(waves)

    # Step 2: Extract date range
    assignment_start, assignment_end = _extract_date_range(waves)

    # Step 3: Build teams from effort
    teams, total_ftes = _build_teams_from_effort(
        skill_effort_days, assignment_start, assignment_end
    )

    # Step 4: Build metrics
    metrics = _build_metrics(teams, skill_effort_days, total_ftes)

    # Step 5: Generate recommendations
    recommendations = generate_6r_recommendations(teams, strategy_counts, total_apps)

    # Step 6: Identify upcoming needs
    upcoming_needs = _identify_upcoming_needs(teams)

    return {
        "teams": teams,
        "metrics": metrics,
        "recommendations": recommendations,
        "upcoming_needs": upcoming_needs,
    }
