"""
Discovery Flow Completion Service - Helper Functions
Contains utility functions for 6R strategy, risk assessment, and recommendations.
"""

from typing import Any, Dict, List

from app.models.asset import Asset as DiscoveryAsset


def determine_six_r_strategy(asset: DiscoveryAsset) -> str:
    """
    Determine 6R migration strategy for an asset.

    Args:
        asset: Discovery asset to analyze

    Returns:
        str: 6R strategy (rehost, replatform, refactor, etc.)
    """
    # Simple heuristic based on asset type and complexity
    asset_type = asset.asset_type or "unknown"
    complexity = asset.migration_complexity or "medium"

    if asset_type in ["database", "legacy_system"]:
        return "replatform" if complexity == "high" else "rehost"
    elif asset_type == "application":
        return "refactor" if complexity == "high" else "replatform"
    elif asset_type in ["server", "infrastructure"]:
        return "rehost"
    else:
        return "replatform"


def assess_asset_risk(asset: DiscoveryAsset) -> str:
    """
    Assess migration risk level for an asset.

    Args:
        asset: Discovery asset to analyze

    Returns:
        str: Risk level (low, medium, high)
    """
    complexity = asset.migration_complexity or "medium"
    confidence = asset.confidence_score or 0.5

    if complexity == "high" or confidence < 0.6:
        return "high"
    elif complexity == "medium" and confidence >= 0.8:
        return "medium"
    else:
        return "low"


def assess_modernization_potential(asset: DiscoveryAsset) -> str:
    """
    Assess modernization potential for an asset.

    Args:
        asset: Discovery asset to analyze

    Returns:
        str: Modernization potential (low, medium, high)
    """
    asset_type = asset.asset_type or "unknown"

    if asset_type == "application":
        return "high"
    elif asset_type in ["server", "infrastructure"]:
        return "medium"
    else:
        return "low"


def generate_migration_waves(assets: List[DiscoveryAsset]) -> List[Dict[str, Any]]:
    """
    Generate migration waves based on dependencies and complexity.

    Args:
        assets: List of discovery assets

    Returns:
        List of migration waves with asset assignments
    """
    # Simple wave generation - can be enhanced with dependency analysis
    waves = []

    # Wave 1: Low complexity, infrastructure
    wave1_assets = [
        a
        for a in assets
        if a.migration_complexity == "low"
        and a.asset_type in ["server", "infrastructure"]
    ]
    if wave1_assets:
        waves.append(
            {
                "wave": 1,
                "name": "Infrastructure Foundation",
                "assets": [
                    {"id": str(a.id), "name": a.asset_name} for a in wave1_assets
                ],
                "estimated_duration_weeks": max(2, len(wave1_assets)),
                "dependencies": [],
            }
        )

    # Wave 2: Medium complexity applications
    wave2_assets = [
        a
        for a in assets
        if a.migration_complexity == "medium" and a.asset_type == "application"
    ]
    if wave2_assets:
        waves.append(
            {
                "wave": 2,
                "name": "Core Applications",
                "assets": [
                    {"id": str(a.id), "name": a.asset_name} for a in wave2_assets
                ],
                "estimated_duration_weeks": max(4, len(wave2_assets) * 2),
                "dependencies": ["wave_1"] if waves else [],
            }
        )

    # Wave 3: High complexity and databases
    wave3_assets = [
        a
        for a in assets
        if a.migration_complexity == "high" or a.asset_type == "database"
    ]
    if wave3_assets:
        waves.append(
            {
                "wave": 3,
                "name": "Complex Systems",
                "assets": [
                    {"id": str(a.id), "name": a.asset_name} for a in wave3_assets
                ],
                "estimated_duration_weeks": max(6, len(wave3_assets) * 3),
                "dependencies": (
                    ["wave_1", "wave_2"]
                    if len(waves) >= 2
                    else (["wave_1"] if waves else [])
                ),
            }
        )

    return waves


def generate_risk_assessment(assets: List[DiscoveryAsset]) -> Dict[str, Any]:
    """
    Generate overall risk assessment for migration.

    Args:
        assets: List of discovery assets

    Returns:
        Dict containing risk assessment details
    """
    high_risk_count = sum(1 for a in assets if assess_asset_risk(a) == "high")
    total_assets = len(assets)

    if total_assets == 0:
        return {
            "overall_risk": "unknown",
            "risk_factors": ["No assets to assess"],
            "mitigation_recommendations": [],
        }

    if high_risk_count / total_assets > 0.3:
        overall_risk = "high"
    elif high_risk_count / total_assets > 0.1:
        overall_risk = "medium"
    else:
        overall_risk = "low"

    risk_factors = []
    if high_risk_count > 0:
        risk_factors.append(f"{high_risk_count} high-risk assets identified")

    complex_assets = sum(1 for a in assets if a.migration_complexity == "high")
    if complex_assets > 0:
        risk_factors.append(f"{complex_assets} highly complex assets")

    low_confidence = sum(1 for a in assets if (a.confidence_score or 0) < 0.7)
    if low_confidence > 0:
        risk_factors.append(f"{low_confidence} assets with low confidence scores")

    return {
        "overall_risk": overall_risk,
        "risk_factors": risk_factors,
        "mitigation_recommendations": [
            "Conduct detailed technical assessment for high-risk assets",
            "Plan additional discovery for low-confidence assets",
            "Consider proof-of-concept migrations for complex systems",
        ],
    }


def generate_recommendations(assets: List[DiscoveryAsset]) -> Dict[str, Any]:
    """
    Generate migration recommendations based on asset analysis.

    Args:
        assets: List of discovery assets

    Returns:
        Dict containing recommendations for migration approach
    """
    six_r_dist = {}
    quick_wins = []
    complex_migrations = []
    modernization_opportunities = []

    for asset in assets:
        strategy = determine_six_r_strategy(asset)
        six_r_dist[strategy] = six_r_dist.get(strategy, 0) + 1

        if asset.migration_complexity == "low" and asset.migration_ready:
            quick_wins.append(
                {
                    "id": str(asset.id),
                    "name": asset.asset_name,
                    "reason": "Low complexity, migration ready",
                }
            )

        if asset.migration_complexity == "high":
            complex_migrations.append(
                {
                    "id": str(asset.id),
                    "name": asset.asset_name,
                    "complexity_factors": ["High migration complexity"],
                }
            )

        if assess_modernization_potential(asset) == "high":
            modernization_opportunities.append(
                {
                    "id": str(asset.id),
                    "name": asset.asset_name,
                    "opportunity": "Application modernization candidate",
                }
            )

    return {
        "six_r_distribution": six_r_dist,
        "quick_wins": quick_wins,
        "complex_migrations": complex_migrations,
        "modernization_opportunities": modernization_opportunities,
    }
