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


def _get_database_strategy(database_type, business_criticality):
    """Get database migration strategy based on type and criticality."""
    if "Oracle" in database_type:
        return "replatform" if business_criticality == "Critical" else "rehost"
    elif "PostgreSQL" in database_type:
        return "rehost"
    else:
        return "replatform"


def _get_readiness_for_strategy(strategy):
    """Get readiness status based on migration strategy."""
    return "Ready" if strategy == "rehost" else "Needs Analysis"


def _get_complexity_for_strategy(strategy):
    """Get complexity level based on migration strategy."""
    return "High" if strategy == "replatform" else "Medium"


def _determine_strategy_for_database_asset(asset):
    """Determine strategy for database assets."""
    database_type = str(asset.custom_attributes.get("database_type", ""))
    strategy = _get_database_strategy(database_type, asset.business_criticality)

    return {
        "strategy": strategy,
        "wave": 2,
        "readiness": _get_readiness_for_strategy(strategy),
        "complexity": _get_complexity_for_strategy(strategy),
        "priority": 8,
    }


def _get_application_strategy_details(tech_stack):
    """Get application strategy, readiness, and complexity based on tech stack."""
    if "Java" in tech_stack or ".NET Core" in tech_stack:
        return "replatform", "Ready", "Medium"
    elif "Legacy" in tech_stack or ".NET Framework" in tech_stack:
        return "refactor", "Business Review", "High"
    elif "Python" in tech_stack or "Node.js" in tech_stack:
        return "rehost", "Ready", "Low"
    else:
        return "replace", "Needs Analysis", "Medium"


def _get_application_priority(business_criticality):
    """Get application migration priority based on business criticality."""
    return 7 if business_criticality == "Critical" else 5


def _determine_strategy_for_application_asset(asset):
    """Determine strategy for application assets."""
    tech_stack = asset.technology_stack or ""
    strategy, readiness, complexity = _get_application_strategy_details(tech_stack)

    return {
        "strategy": strategy,
        "wave": 3,
        "readiness": readiness,
        "complexity": complexity,
        "priority": _get_application_priority(asset.business_criticality),
    }


def _is_legacy_os(operating_system):
    """Check if the operating system is legacy and should be retired."""
    return "Windows Server 2016" in operating_system or "CentOS 7" in operating_system


def _get_server_strategy_for_legacy():
    """Get strategy details for legacy servers."""
    return {
        "strategy": "retire",
        "wave": 4,
        "readiness": "Business Review",
        "complexity": "Low",
        "priority": 3,
    }


def _get_server_strategy_with_dependencies():
    """Get strategy details for servers with dependencies."""
    return {
        "strategy": "replatform",
        "wave": 3,
        "readiness": "Dependency Blocked",
        "complexity": "Medium",
        "priority": 6,
    }


def _get_server_strategy_standard():
    """Get strategy details for standard servers."""
    return {
        "strategy": "rehost",
        "wave": 2,
        "readiness": "Ready",
        "complexity": "Low",
        "priority": 4,
    }


def _determine_strategy_for_server_asset(asset):
    """Determine strategy for server assets."""
    os = asset.operating_system or ""

    if _is_legacy_os(os):
        return _get_server_strategy_for_legacy()
    elif asset.has_dependencies:
        return _get_server_strategy_with_dependencies()
    else:
        return _get_server_strategy_standard()


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


def _update_asset_basic_properties(asset, planning_details, readiness):
    """Update basic asset migration properties."""
    asset.six_r_strategy = planning_details["strategy"]
    asset.migration_wave = planning_details["wave"]
    asset.migration_complexity = planning_details["complexity"]
    asset.migration_priority = planning_details["priority"]
    asset.sixr_ready = readiness


def _get_migration_status_for_wave(wave_status):
    """Get migration status based on wave status."""
    if wave_status == "completed":
        return "migrated"
    elif wave_status == "in_progress":
        return "migrating"
    else:
        return "planned"


def _get_migration_duration_for_complexity(complexity):
    """Get estimated migration duration based on complexity."""
    duration_map = {"Low": 5, "Medium": 15, "High": 30}
    return duration_map.get(complexity, 10)


def _build_custom_attributes_update(asset, planning_details, readiness):
    """Build custom attributes update dictionary."""
    strategy_rationale = STRATEGY_RULES.get(asset.asset_type, {}).get(
        "rationale", "Standard migration approach"
    )

    wave = planning_details["wave"]
    complexity = planning_details["complexity"]

    return {
        "migration_strategy_rationale": strategy_rationale,
        "readiness_indicator": readiness,
        "wave_assignment_reason": f"Asset assigned to wave {wave} based on type and dependencies",
        "estimated_migration_duration_days": _get_migration_duration_for_complexity(
            complexity
        ),
        "risk_factors": _build_risk_factors(asset),
    }


def _update_asset_with_migration_plan(asset, planning_details, wave_status):
    """Update asset with migration planning details."""
    readiness = _adjust_readiness_for_flow_state(
        asset, planning_details["readiness"], planning_details["priority"]
    )

    # Update asset properties
    _update_asset_basic_properties(asset, planning_details, readiness)

    # Update migration status
    asset.migration_status = _get_migration_status_for_wave(wave_status)

    # Update custom attributes
    if not asset.custom_attributes:
        asset.custom_attributes = {}

    custom_attributes_update = _build_custom_attributes_update(
        asset, planning_details, readiness
    )
    asset.custom_attributes.update(custom_attributes_update)


def _initialize_statistics_counters():
    """Initialize statistics counters for tracking assignment results."""
    return {}, {1: 0, 2: 0, 3: 0, 4: 0}, {}


def _update_assignment_statistics(
    planning_details, asset, strategy_counts, wave_assignments, readiness_counts
):
    """Update assignment statistics for an asset."""
    strategy = planning_details["strategy"]
    wave = planning_details["wave"]
    readiness = asset.sixr_ready

    strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
    wave_assignments[wave] += 1
    readiness_counts[readiness] = readiness_counts.get(readiness, 0) + 1


def _process_single_asset(asset, strategy_counts, wave_assignments, readiness_counts):
    """Process a single asset for migration planning."""
    planning_details = _get_migration_planning_for_asset(asset)
    wave_status = MIGRATION_WAVES[planning_details["wave"] - 1]["status"]

    _update_asset_with_migration_plan(asset, planning_details, wave_status)
    _update_assignment_statistics(
        planning_details, asset, strategy_counts, wave_assignments, readiness_counts
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

    # Initialize statistics counters
    strategy_counts, wave_assignments, readiness_counts = (
        _initialize_statistics_counters()
    )

    # Process each asset
    for asset in assets:
        _process_single_asset(
            asset, strategy_counts, wave_assignments, readiness_counts
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


def _print_strategy_distribution(strategy_counts, total_assets):
    """Print 6R strategy distribution statistics."""
    print("\n   🎯 6R Strategy Distribution:")
    for strategy, count in sorted(strategy_counts.items()):
        percentage = (count / total_assets) * 100
        print(f"     {strategy.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")


def _print_wave_assignments(wave_assignments, total_assets):
    """Print wave assignment statistics."""
    print("\n   🌊 Wave Assignment:")
    for wave_num, count in sorted(wave_assignments.items()):
        wave_name = MIGRATION_WAVES[wave_num - 1]["name"]
        wave_status = MIGRATION_WAVES[wave_num - 1]["status"]
        percentage = (count / total_assets) * 100
        print(
            f"     Wave {wave_num} ({wave_name}): {count} assets ({percentage:.1f}%) - {wave_status.upper()}"
        )


def _print_readiness_status(readiness_counts, total_assets):
    """Print readiness status statistics."""
    print("\n   🚦 Readiness Status:")
    for readiness, count in sorted(readiness_counts.items()):
        percentage = (count / total_assets) * 100
        print(f"     {readiness}: {count} ({percentage:.1f}%)")


def _calculate_cost_totals():
    """Calculate total estimated and actual costs."""
    total_estimated = sum(wave["estimated_cost"] for wave in MIGRATION_WAVES)
    total_actual = sum(
        wave.get("actual_cost", 0)
        for wave in MIGRATION_WAVES
        if wave.get("actual_cost")
    )
    return total_estimated, total_actual


def _calculate_effort_totals():
    """Calculate total estimated and actual effort."""
    total_effort = sum(wave["estimated_effort_hours"] for wave in MIGRATION_WAVES)
    actual_effort = sum(
        wave.get("actual_effort_hours", 0)
        for wave in MIGRATION_WAVES
        if wave.get("actual_effort_hours")
    )
    return total_effort, actual_effort


def _print_cost_estimates():
    """Print migration cost estimates."""
    print("\n   💰 Migration Cost Estimates:")
    total_estimated, total_actual = _calculate_cost_totals()
    print(f"     Total Estimated: ${total_estimated:,}")
    print(f"     Spent to Date: ${total_actual:,}")
    print(f"     Remaining Budget: ${total_estimated - total_actual:,}")


def _print_effort_estimates():
    """Print effort estimates."""
    print("\n   ⏱️ Effort Estimates:")
    total_effort, actual_effort = _calculate_effort_totals()
    print(f"     Total Estimated: {total_effort:,} hours")
    print(f"     Effort to Date: {actual_effort:,} hours")
    print(f"     Remaining Effort: {total_effort - actual_effort:,} hours")


def _print_summary_statistics(
    assets, waves, strategy_counts, wave_assignments, readiness_counts
):
    """Print comprehensive summary statistics."""
    total_assets = len(assets)

    print("\n✅ Migration planning created successfully!")
    print(f"   📊 Total Assets: {total_assets}")
    print(f"   🌊 Migration Waves: {len(waves)}")

    _print_strategy_distribution(strategy_counts, total_assets)
    _print_wave_assignments(wave_assignments, total_assets)
    _print_readiness_status(readiness_counts, total_assets)
    _print_cost_estimates()
    _print_effort_estimates()


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

        # Print summary statistics
        _print_summary_statistics(
            assets, waves, strategy_counts, wave_assignments, readiness_counts
        )


if __name__ == "__main__":
    asyncio.run(create_migration_planning())
