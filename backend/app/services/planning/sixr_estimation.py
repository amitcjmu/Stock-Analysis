"""6R Strategy Resource Estimation Module - wave-aware FTE estimation based on migration strategies."""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Tuple

from app.schemas.planning.resource import (
    ResourceTeam,
    TeamAssignment,
    ResourceMetrics,
    ResourceRecommendation,
    UpcomingNeed,
)

logger = logging.getLogger(__name__)

# 6R Strategy effort multipliers (person-days per application)
# These represent TOTAL effort including all migration phases
STRATEGY_EFFORT = {
    "rehost": {
        "days_per_app": 25,
        "skills": {
            "Cloud Operations": 0.25,
            "DevOps": 0.20,
            "Data Migration": 0.20,
            "PMO": 0.15,
            "QA Engineering": 0.20,
        },
    },
    "replatform": {
        "days_per_app": 45,
        "skills": {
            "Cloud Operations": 0.15,
            "Backend Development": 0.25,
            "DevOps": 0.15,
            "Data Migration": 0.15,
            "QA Engineering": 0.15,
            "PMO": 0.15,
        },
    },
    "refactor": {
        "days_per_app": 90,
        "skills": {
            "Backend Development": 0.25,
            "Frontend Development": 0.15,
            "Cloud Architecture": 0.10,
            "DevOps": 0.10,
            "QA Engineering": 0.20,
            "Data Migration": 0.10,
            "PMO": 0.10,
        },
    },
    "repurchase": {
        "days_per_app": 30,
        "skills": {
            "Business Analysis": 0.20,
            "Procurement": 0.15,
            "Change Management": 0.20,
            "Data Migration": 0.15,
            "Training": 0.15,
            "PMO": 0.15,
        },
    },
    "retain": {
        "days_per_app": 5,
        "skills": {"Operations": 0.60, "PMO": 0.40},
    },
    "retire": {
        "days_per_app": 15,
        "skills": {"Operations": 0.40, "Data Migration": 0.40, "PMO": 0.20},
    },
    "default": {
        "days_per_app": 35,
        "skills": {
            "Cloud Operations": 0.20,
            "Backend Development": 0.25,
            "DevOps": 0.20,
            "QA Engineering": 0.20,
            "PMO": 0.15,
        },
    },
}

# Minimum baseline FTEs per skill (always need at least this many)
BASELINE_FTES = {
    "Cloud Operations": 1,
    "Backend Development": 1,
    "Frontend Development": 1,
    "Cloud Architecture": 1,
    "DevOps": 1,
    "QA Engineering": 1,
    "Data Migration": 1,
    "PMO": 1,
    "Operations": 1,
    "Business Analysis": 1,
    "Procurement": 1,
    "Change Management": 1,
    "Training": 1,
}


def _parse_date(date_str: str) -> datetime:
    """Parse date string to datetime."""
    if not date_str:
        return datetime.now()
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return datetime.now()


def _calculate_working_days(start_date: datetime, end_date: datetime) -> int:
    """Calculate working days between two dates (excluding weekends)."""
    if end_date <= start_date:
        return 20  # Default to 1 month
    total_days = (end_date - start_date).days
    # Roughly 5/7 of days are working days
    working_days = int(total_days * 5 / 7)
    return max(working_days, 10)  # Minimum 2 weeks


def _get_wave_default_strategy(wave: Dict[str, Any]) -> str:
    """
    Extract default migration strategy from wave's groups array.

    Wave plan data structure stores migration_strategy at the GROUP level,
    not the individual application level. This function extracts it.
    """
    groups = wave.get("groups", [])
    if groups and len(groups) > 0:
        # Use first group's strategy as wave default
        group_strategy = groups[0].get("migration_strategy", "")
        if group_strategy:
            return group_strategy.lower()
    return "default"


def _calculate_wave_effort(wave: Dict[str, Any]) -> Dict[str, float]:
    """Calculate total effort days by skill for a single wave."""
    skill_effort: Dict[str, float] = defaultdict(float)
    applications = wave.get("applications", [])

    # Get wave-level default strategy from groups (wave_plan_data stores strategy at group level)
    wave_default_strategy = _get_wave_default_strategy(wave)

    for app in applications:
        # Priority: app.migration_strategy > app.six_r_strategy > wave default > "default"
        strategy = (
            app.get("migration_strategy")
            or app.get("six_r_strategy")
            or wave_default_strategy
            or "default"
        ).lower()
        effort_config = STRATEGY_EFFORT.get(strategy, STRATEGY_EFFORT["default"])
        total_days = effort_config["days_per_app"]
        skill_weights = effort_config["skills"]

        for skill, weight in skill_weights.items():
            skill_effort[skill] += total_days * weight

    return dict(skill_effort)


def _analyze_waves(
    waves: List[Dict[str, Any]],
) -> Tuple[List[Dict], Dict[str, int], int]:
    """
    Analyze all waves and calculate per-wave resource requirements.

    Returns: (wave_analysis, strategy_counts, total_apps)
    """
    wave_analysis = []
    strategy_counts: Dict[str, int] = defaultdict(int)
    total_apps = 0

    for wave in waves:
        wave_name = (
            wave.get("wave_name")
            or wave.get("name")
            or f"Wave {len(wave_analysis) + 1}"
        )
        start_date = _parse_date(wave.get("start_date", ""))
        end_date = _parse_date(wave.get("end_date", ""))
        applications = wave.get("applications", [])

        # Get wave-level default strategy from groups
        wave_default_strategy = _get_wave_default_strategy(wave)

        # Count strategies (using same resolution logic as effort calculation)
        wave_strategies: Dict[str, int] = defaultdict(int)
        for app in applications:
            strategy = (
                app.get("migration_strategy")
                or app.get("six_r_strategy")
                or wave_default_strategy
                or "default"
            ).lower()
            strategy_counts[strategy] += 1
            wave_strategies[strategy] += 1

        total_apps += len(applications)

        # Calculate effort by skill for this wave
        skill_effort = _calculate_wave_effort(wave)
        working_days = _calculate_working_days(start_date, end_date)

        # Calculate FTEs needed for this wave (effort / duration)
        skill_ftes: Dict[str, float] = {}
        for skill, effort_days in skill_effort.items():
            ftes_needed = effort_days / working_days
            skill_ftes[skill] = round(ftes_needed, 1)

        wave_analysis.append(
            {
                "name": wave_name,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "app_count": len(applications),
                "working_days": working_days,
                "skill_effort": skill_effort,
                "skill_ftes": skill_ftes,
                "strategies": dict(wave_strategies),
            }
        )

    return wave_analysis, dict(strategy_counts), total_apps


def _build_teams_from_waves(
    wave_analysis: List[Dict],
) -> Tuple[List[ResourceTeam], int]:
    """Build teams with per-wave assignments showing actual demand."""
    # Aggregate all skills across waves
    all_skills: set = set()
    for wave in wave_analysis:
        all_skills.update(wave["skill_ftes"].keys())

    teams = []
    total_ftes = 0

    for skill in sorted(all_skills):
        # Find peak demand and calculate assignments per wave
        assignments = []
        peak_ftes = 0.0
        total_effort_days = 0.0
        total_working_days = 0

        for wave in wave_analysis:
            ftes_needed = wave["skill_ftes"].get(skill, 0)
            effort_days = wave["skill_effort"].get(skill, 0)

            if ftes_needed > 0:
                peak_ftes = max(peak_ftes, ftes_needed)
                total_effort_days += effort_days
                total_working_days += wave["working_days"]

                # Create assignment for this wave
                assignments.append(
                    TeamAssignment(
                        project=wave["name"],
                        allocation=round(
                            min(100, ftes_needed * 100 / max(1, peak_ftes)), 1
                        ),
                        start_date=wave["start_date"],
                        end_date=wave["end_date"],
                    )
                )

        if not assignments:
            continue

        # Team size = peak FTEs rounded up, minimum from baseline
        baseline = BASELINE_FTES.get(skill, 1)
        team_size = max(baseline, int(peak_ftes + 0.5))  # Round to nearest
        total_ftes += team_size

        # Calculate actual utilization based on total effort vs capacity
        total_capacity_days = (
            team_size * total_working_days if total_working_days > 0 else 1
        )
        utilization = min(100, (total_effort_days / total_capacity_days) * 100)

        teams.append(
            ResourceTeam(
                id=skill.lower().replace(" ", "-"),
                name=f"{skill} Team",
                size=team_size,
                skills=[skill],
                availability=round(100 - utilization, 1),
                utilization=round(utilization, 1),
                assignments=assignments,
            )
        )

    # Sort teams by utilization (highest first)
    teams.sort(key=lambda t: t.utilization, reverse=True)

    return teams, total_ftes


def _build_metrics(
    teams: List[ResourceTeam], total_ftes: int, wave_analysis: List[Dict]
) -> ResourceMetrics:
    """Build metrics from wave-aware analysis."""
    # Calculate skill coverage based on demand vs capacity
    skill_coverage = {}
    for team in teams:
        skill = team.skills[0] if team.skills else team.name
        # Coverage = (team_size / peak_demand) * 100, capped at 100
        total_demand = sum(w["skill_ftes"].get(skill, 0) for w in wave_analysis)
        avg_demand = total_demand / len(wave_analysis) if wave_analysis else 0
        if avg_demand > 0:
            coverage = min(100, (team.size / avg_demand) * 100)
        else:
            coverage = 100
        skill_coverage[skill] = round(coverage, 1)

    avg_utilization = sum(t.utilization for t in teams) / len(teams) if teams else 0

    return ResourceMetrics(
        total_teams=len(teams),
        total_resources=total_ftes,
        average_utilization=round(avg_utilization, 1),
        skill_coverage=skill_coverage,
    )


def _identify_upcoming_needs(
    teams: List[ResourceTeam], wave_analysis: List[Dict]
) -> List[UpcomingNeed]:
    """Identify resource gaps based on wave demands."""
    upcoming_needs = []

    for team in teams:
        skill = team.skills[0] if team.skills else team.name

        # Find waves where demand exceeds team size
        for wave in wave_analysis:
            ftes_needed = wave["skill_ftes"].get(skill, 0)
            if ftes_needed > team.size:
                gap = int(ftes_needed - team.size + 0.5)
                upcoming_needs.append(
                    UpcomingNeed(
                        skill=skill,
                        demand=team.size + gap,
                        timeline=f"{wave['name']} ({wave['start_date']})",
                    )
                )
                break  # Only report first gap per skill

        # Also flag high utilization teams
        if team.utilization > 85 and skill not in [n.skill for n in upcoming_needs]:
            upcoming_needs.append(
                UpcomingNeed(
                    skill=skill,
                    demand=team.size + 1,
                    timeline="High utilization - add capacity",
                )
            )

    return upcoming_needs[:6]  # Limit to top 6 needs


def generate_6r_recommendations(
    teams: List[ResourceTeam],
    strategy_counts: Dict[str, int],
    total_apps: int,
    wave_analysis: List[Dict],
) -> List[ResourceRecommendation]:
    """Generate actionable recommendations based on wave analysis."""
    recommendations = []

    # Find overloaded teams
    overloaded = [t for t in teams if t.utilization > 90]
    if overloaded:
        names = ", ".join(t.name for t in overloaded[:3])
        recommendations.append(
            ResourceRecommendation(
                type="capacity",
                description=f"{names} at >90% utilization. Add FTEs or extend wave timelines to reduce risk.",
                impact="High",
            )
        )

    # Identify waves with highest demand
    if wave_analysis:
        heaviest_wave = max(wave_analysis, key=lambda w: w["app_count"])
        if heaviest_wave["app_count"] > 5:
            wave_name = heaviest_wave["name"]
            app_count = heaviest_wave["app_count"]
            recommendations.append(
                ResourceRecommendation(
                    type="planning",
                    description=f"{wave_name} has {app_count} apps. Consider splitting "
                    f"into smaller waves for better resource distribution.",
                    impact="Medium",
                )
            )

    # Strategy-specific recommendations
    refactor_count = strategy_counts.get("refactor", 0)
    if refactor_count > 0 and total_apps > 0:
        refactor_pct = (refactor_count / total_apps) * 100
        if refactor_pct > 20:
            recommendations.append(
                ResourceRecommendation(
                    type="planning",
                    description=f"{refactor_pct:.0f}% of apps require Refactoring "
                    f"({refactor_count} apps × 90 days). Ensure Backend/Frontend dev capacity.",
                    impact="High",
                )
            )

    # Quick wins recommendation
    rehost_count = strategy_counts.get("rehost", 0)
    if rehost_count >= 3:
        recommendations.append(
            ResourceRecommendation(
                type="optimization",
                description=f"{rehost_count} Rehost apps can be parallelized for quick wins. "
                f"Group them in early waves to build momentum.",
                impact="Medium",
            )
        )

    # Summary recommendation
    if teams:
        total_ftes = sum(t.size for t in teams)
        high_util = len([t for t in teams if t.utilization > 75])
        num_teams = len(teams)
        num_waves = len(wave_analysis)
        recommendations.append(
            ResourceRecommendation(
                type="planning",
                description=f"Total: {total_ftes} FTEs across {num_teams} teams "
                f"for {total_apps} apps in {num_waves} waves. {high_util} teams at high utilization.",
                impact="Medium",
            )
        )

    return recommendations


def estimate_resources_from_6r(wave_plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wave-aware resource estimation based on 6R strategies.

    Analyzes each wave independently to calculate:
    - Per-wave effort by skill based on app strategies
    - Peak demand per skill across waves
    - Per-wave team assignments showing when skills are needed
    - Resource gaps where demand exceeds capacity
    """
    waves = wave_plan_data.get("waves", [])

    if not waves:
        return {
            "teams": [],
            "metrics": ResourceMetrics(
                total_teams=0,
                total_resources=0,
                average_utilization=0,
                skill_coverage={},
            ),
            "recommendations": [],
            "upcoming_needs": [],
        }

    # Analyze all waves
    wave_analysis, strategy_counts, total_apps = _analyze_waves(waves)

    # Build teams with per-wave assignments
    teams, total_ftes = _build_teams_from_waves(wave_analysis)

    # Build metrics
    metrics = _build_metrics(teams, total_ftes, wave_analysis)

    # Generate recommendations
    recommendations = generate_6r_recommendations(
        teams, strategy_counts, total_apps, wave_analysis
    )

    # Identify resource gaps
    upcoming_needs = _identify_upcoming_needs(teams, wave_analysis)

    return {
        "teams": teams,
        "metrics": metrics,
        "recommendations": recommendations,
        "upcoming_needs": upcoming_needs,
    }
