"""
TASK 3.5: Create Migration Planning
Creating migration waves and updating 6R strategies for comprehensive migration planning.
"""

import asyncio
from datetime import datetime, timezone

from constants import DEMO_CLIENT_ID, DEMO_ENGAGEMENT_ID, USER_IDS
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset, MigrationWave, SixRStrategy

# Migration wave definitions
MIGRATION_WAVES = [
    {
        "wave_number": 1,
        "name": "Infrastructure Foundation",
        "description": "Critical network infrastructure and core services",
        "status": "completed",
        "planned_start_date": datetime(2024, 1, 15, tzinfo=timezone.utc),
        "planned_end_date": datetime(2024, 2, 28, tzinfo=timezone.utc),
        "actual_start_date": datetime(2024, 1, 15, tzinfo=timezone.utc),
        "actual_end_date": datetime(2024, 2, 25, tzinfo=timezone.utc),
        "estimated_cost": 150000,
        "actual_cost": 142000,
        "estimated_effort_hours": 1200,
        "actual_effort_hours": 1150,
    },
    {
        "wave_number": 2,
        "name": "Database Migration",
        "description": "Core databases and data services",
        "status": "in_progress",
        "planned_start_date": datetime(2024, 3, 1, tzinfo=timezone.utc),
        "planned_end_date": datetime(2024, 4, 15, tzinfo=timezone.utc),
        "actual_start_date": datetime(2024, 3, 1, tzinfo=timezone.utc),
        "actual_end_date": None,
        "estimated_cost": 250000,
        "actual_cost": 180000,  # Partial cost
        "estimated_effort_hours": 2000,
        "actual_effort_hours": 1400,  # Partial effort
    },
    {
        "wave_number": 3,
        "name": "Application Services",
        "description": "Business applications and middleware",
        "status": "planned",
        "planned_start_date": datetime(2024, 4, 16, tzinfo=timezone.utc),
        "planned_end_date": datetime(2024, 6, 30, tzinfo=timezone.utc),
        "actual_start_date": None,
        "actual_end_date": None,
        "estimated_cost": 400000,
        "actual_cost": None,
        "estimated_effort_hours": 3200,
        "actual_effort_hours": None,
    },
    {
        "wave_number": 4,
        "name": "Legacy Systems",
        "description": "Legacy applications and specialized systems",
        "status": "planned",
        "planned_start_date": datetime(2024, 7, 1, tzinfo=timezone.utc),
        "planned_end_date": datetime(2024, 9, 15, tzinfo=timezone.utc),
        "actual_start_date": None,
        "actual_end_date": None,
        "estimated_cost": 200000,
        "actual_cost": None,
        "estimated_effort_hours": 1800,
        "actual_effort_hours": None,
    },
]

# 6R Strategy distributions and rules
STRATEGY_RULES = {
    "network": {
        "primary_strategy": SixRStrategy.REPLACE,
        "rationale": "Network devices typically need cloud-native replacements",
    },
    "load_balancer": {
        "primary_strategy": SixRStrategy.REPLACE,
        "rationale": "Replace with cloud load balancers",
    },
    "database": {
        "strategies": [
            SixRStrategy.REPLATFORM,
            SixRStrategy.REHOST,
            SixRStrategy.REFACTOR,
        ],
        "rationale": "Database migration strategy depends on version and complexity",
    },
    "application": {
        "strategies": [
            SixRStrategy.REPLATFORM,
            SixRStrategy.REFACTOR,
            SixRStrategy.REHOST,
            SixRStrategy.REPLACE,
        ],
        "rationale": "Application strategy varies by technology stack and business criticality",
    },
    "server": {
        "strategies": [
            SixRStrategy.REHOST,
            SixRStrategy.REPLATFORM,
            SixRStrategy.RETIRE,
        ],
        "rationale": "Server strategy depends on workload and dependencies",
    },
}

# Migration readiness indicators
READINESS_INDICATORS = {
    "Ready": "Asset has been assessed and is ready for migration",
    "Needs Analysis": "Asset requires additional technical analysis",
    "Dependency Blocked": "Asset migration blocked by dependencies",
    "Business Review": "Asset requires business stakeholder review",
    "Not Applicable": "Asset not suitable for current migration scope",
}


async def create_migration_waves(session: AsyncSession):
    """Create migration wave definitions."""
    print("  🌊 Creating migration waves...")

    waves = []
    for wave_data in MIGRATION_WAVES:
        wave = MigrationWave(
            client_account_id=DEMO_CLIENT_ID,
            engagement_id=DEMO_ENGAGEMENT_ID,
            created_by=USER_IDS["engagement_manager"],
            **wave_data,
        )
        waves.append(wave)

    session.add_all(waves)
    return waves


def _determine_strategy_for_network_asset(asset):
    """Determine strategy for network and load balancer assets."""
    return {
        "strategy": "replace",
        "wave": 1,
        "readiness": "Ready",
        "complexity": "High",
        "priority": 9,
    }


def _determine_strategy_for_database_asset(asset):
    """Determine strategy for database assets."""
    database_type = str(asset.custom_attributes.get("database_type", ""))

    if "Oracle" in database_type:
        strategy = (
            "replatform" if asset.business_criticality == "Critical" else "rehost"
        )
    elif "PostgreSQL" in database_type:
        strategy = "rehost"
    else:
        strategy = "replatform"

    return {
        "strategy": strategy,
        "wave": 2,
        "readiness": "Ready" if strategy == SixRStrategy.REHOST else "Needs Analysis",
        "complexity": "High" if strategy == SixRStrategy.REPLATFORM else "Medium",
        "priority": 8,
    }


def _determine_strategy_for_application_asset(asset):
    """Determine strategy for application assets."""
    tech_stack = asset.technology_stack or ""

    if "Java" in tech_stack or ".NET Core" in tech_stack:
        strategy, readiness, complexity = "replatform", "Ready", "Medium"
    elif "Legacy" in tech_stack or ".NET Framework" in tech_stack:
        strategy, readiness, complexity = "refactor", "Business Review", "High"
    elif "Python" in tech_stack or "Node.js" in tech_stack:
        strategy, readiness, complexity = "rehost", "Ready", "Low"
    else:
        strategy, readiness, complexity = "replace", "Needs Analysis", "Medium"

    return {
        "strategy": strategy,
        "wave": 3,
        "readiness": readiness,
        "complexity": complexity,
        "priority": 7 if asset.business_criticality == "Critical" else 5,
    }


def _determine_strategy_for_server_asset(asset):
    """Determine strategy for server assets."""
    os = asset.operating_system or ""

    if "Windows Server 2016" in os or "CentOS 7" in os:
        return {
            "strategy": "retire",
            "wave": 4,
            "readiness": "Business Review",
            "complexity": "Low",
            "priority": 3,
        }
    elif asset.has_dependencies:
        return {
            "strategy": "replatform",
            "wave": 3,
            "readiness": "Dependency Blocked",
            "complexity": "Medium",
            "priority": 6,
        }
    else:
        return {
            "strategy": "rehost",
            "wave": 2,
            "readiness": "Ready",
            "complexity": "Low",
            "priority": 4,
        }


def _get_migration_planning_for_asset(asset):
    """Get migration planning details for an asset based on its type."""
    if asset.asset_type in ["network", "load_balancer"]:
        return _determine_strategy_for_network_asset(asset)
    elif asset.asset_type == "database":
        return _determine_strategy_for_database_asset(asset)
    elif asset.asset_type == "application":
        return _determine_strategy_for_application_asset(asset)
    else:  # servers
        return _determine_strategy_for_server_asset(asset)


def _adjust_readiness_for_flow_state(asset, readiness, priority):
    """Adjust readiness based on discovery flow state."""
    if hasattr(asset, "discovery_flow") and asset.discovery_flow:
        flow_state = getattr(asset.discovery_flow, "state", "unknown")
        if flow_state == "failed":
            return "Needs Analysis"
        elif flow_state == "in_progress" and priority > 5:
            return "Dependency Blocked"
    return readiness


def _build_risk_factors(asset):
    """Build risk factors list for an asset."""
    risk_factors = [
        "Dependency complexity" if asset.has_dependencies else None,
        "Legacy technology" if "Legacy" in (asset.technology_stack or "") else None,
        (
            "High availability requirements"
            if asset.business_criticality == "Critical"
            else None
        ),
        (
            "Compliance requirements"
            if asset.custom_attributes.get("compliance_scope", "None") != "None"
            else None
        ),
    ]
    return [rf for rf in risk_factors if rf is not None]


def _update_asset_with_migration_plan(asset, planning_details, wave_status):
    """Update asset with migration planning details."""
    strategy = planning_details["strategy"]
    wave = planning_details["wave"]
    complexity = planning_details["complexity"]
    readiness = planning_details["readiness"]
    priority = planning_details["priority"]

    # Adjust readiness for flow state
    readiness = _adjust_readiness_for_flow_state(asset, readiness, priority)

    # Update asset properties
    asset.six_r_strategy = strategy
    asset.migration_wave = wave
    asset.migration_complexity = complexity
    asset.migration_priority = priority
    asset.sixr_ready = readiness

    # Update migration status based on wave status
    if wave_status == "completed":
        asset.migration_status = "migrated"
    elif wave_status == "in_progress":
        asset.migration_status = "migrating"
    else:
        asset.migration_status = "planned"

    # Update custom attributes
    if not asset.custom_attributes:
        asset.custom_attributes = {}

    asset.custom_attributes.update(
        {
            "migration_strategy_rationale": STRATEGY_RULES.get(
                asset.asset_type, {}
            ).get("rationale", "Standard migration approach"),
            "readiness_indicator": readiness,
            "wave_assignment_reason": f"Asset assigned to wave {wave} based on type and dependencies",
            "estimated_migration_duration_days": {
                "Low": 5,
                "Medium": 15,
                "High": 30,
            }.get(complexity, 10),
            "risk_factors": _build_risk_factors(asset),
        }
    )


async def assign_6r_strategies_and_waves(session: AsyncSession):
    """Assign 6R strategies and migration waves to assets based on rules."""
    print("  🎯 Assigning 6R strategies and migration waves...")

    # Get all assets
    result = await session.execute(
        select(Asset)
        .where(Asset.client_account_id == DEMO_CLIENT_ID)
        .order_by(Asset.asset_type, Asset.name)
    )
    assets = result.scalars().all()

    strategy_counts = {}
    wave_assignments = {1: 0, 2: 0, 3: 0, 4: 0}
    readiness_counts = {}

    for asset in assets:
        # Get migration planning details
        planning_details = _get_migration_planning_for_asset(asset)

        # Get wave status
        wave_status = MIGRATION_WAVES[planning_details["wave"] - 1]["status"]

        # Update asset with migration planning
        _update_asset_with_migration_plan(asset, planning_details, wave_status)

        # Update statistics
        strategy_counts[planning_details["strategy"]] = (
            strategy_counts.get(planning_details["strategy"], 0) + 1
        )
        wave_assignments[planning_details["wave"]] += 1
        readiness_counts[asset.sixr_ready] = (
            readiness_counts.get(asset.sixr_ready, 0) + 1
        )

    return assets, strategy_counts, wave_assignments, readiness_counts


async def update_wave_statistics(
    session: AsyncSession, waves: list, wave_assignments: dict
):
    """Update migration wave statistics based on asset assignments."""
    print("  📊 Updating wave statistics...")

    for wave in waves:
        wave_num = wave.wave_number
        asset_count = wave_assignments.get(wave_num, 0)

        wave.total_assets = asset_count

        # Set completed/failed assets based on wave status
        if wave.status == "completed":
            wave.completed_assets = asset_count
            wave.failed_assets = 0
        elif wave.status == "in_progress":
            wave.completed_assets = asset_count // 2  # 50% complete
            wave.failed_assets = max(1, asset_count // 10)  # 10% failed
        else:
            wave.completed_assets = 0
            wave.failed_assets = 0


async def create_migration_planning():
    """Create comprehensive migration planning data."""
    print("🎯 Creating migration planning...")

    async with AsyncSessionLocal() as session:
        # Create migration waves
        waves = await create_migration_waves(session)
        print(f"    ✅ Created {len(waves)} migration waves")

        # Assign 6R strategies and waves to assets
        (
            assets,
            strategy_counts,
            wave_assignments,
            readiness_counts,
        ) = await assign_6r_strategies_and_waves(session)
        print(f"    ✅ Updated {len(assets)} assets with migration planning")

        # Update wave statistics
        await update_wave_statistics(session, waves, wave_assignments)
        print("    ✅ Updated wave statistics")

        # Commit all changes
        await session.commit()

        # Summary statistics
        total_assets = len(assets)

        print("\n✅ Migration planning created successfully!")
        print(f"   📊 Total Assets: {total_assets}")
        print(f"   🌊 Migration Waves: {len(waves)}")

        print("\n   🎯 6R Strategy Distribution:")
        for strategy, count in sorted(strategy_counts.items()):
            percentage = (count / total_assets) * 100
            print(
                f"     {strategy.replace('_', ' ').title()}: {count} ({percentage:.1f}%)"
            )

        print("\n   🌊 Wave Assignment:")
        for wave_num, count in sorted(wave_assignments.items()):
            wave_name = MIGRATION_WAVES[wave_num - 1]["name"]
            wave_status = MIGRATION_WAVES[wave_num - 1]["status"]
            percentage = (count / total_assets) * 100
            print(
                f"     Wave {wave_num} ({wave_name}): {count} assets ({percentage:.1f}%) - {wave_status.upper()}"
            )

        print("\n   🚦 Readiness Status:")
        for readiness, count in sorted(readiness_counts.items()):
            percentage = (count / total_assets) * 100
            print(f"     {readiness}: {count} ({percentage:.1f}%)")

        print("\n   💰 Migration Cost Estimates:")
        total_estimated = sum(wave["estimated_cost"] for wave in MIGRATION_WAVES)
        total_actual = sum(
            wave.get("actual_cost", 0)
            for wave in MIGRATION_WAVES
            if wave.get("actual_cost")
        )
        print(f"     Total Estimated: ${total_estimated:,}")
        print(f"     Spent to Date: ${total_actual:,}")
        print(f"     Remaining Budget: ${total_estimated - total_actual:,}")

        print("\n   ⏱️ Effort Estimates:")
        total_effort = sum(wave["estimated_effort_hours"] for wave in MIGRATION_WAVES)
        actual_effort = sum(
            wave.get("actual_effort_hours", 0)
            for wave in MIGRATION_WAVES
            if wave.get("actual_effort_hours")
        )
        print(f"     Total Estimated: {total_effort:,} hours")
        print(f"     Effort to Date: {actual_effort:,} hours")
        print(f"     Remaining Effort: {total_effort - actual_effort:,} hours")


if __name__ == "__main__":
    asyncio.run(create_migration_planning())
