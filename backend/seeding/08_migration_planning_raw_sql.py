"""
TASK 3.5: Create Migration Planning (Raw SQL Approach)
Creating migration waves and updating 6R strategies using raw SQL.
"""

import asyncio
from datetime import datetime, timezone

from constants import DEMO_CLIENT_ID, DEMO_ENGAGEMENT_ID, USER_IDS
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal

# Migration wave definitions
MIGRATION_WAVES = [
    {
        "id": "11111111-2222-3333-4444-555555555551",
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
        "actual_effort_hours": 1150
    },
    {
        "id": "11111111-2222-3333-4444-555555555552",
        "wave_number": 2,
        "name": "Database Migration",
        "description": "Core databases and data services",
        "status": "in_progress",
        "planned_start_date": datetime(2024, 3, 1, tzinfo=timezone.utc),
        "planned_end_date": datetime(2024, 4, 15, tzinfo=timezone.utc),
        "actual_start_date": datetime(2024, 3, 1, tzinfo=timezone.utc),
        "actual_end_date": None,
        "estimated_cost": 250000,
        "actual_cost": 180000,
        "estimated_effort_hours": 2000,
        "actual_effort_hours": 1400
    },
    {
        "id": "11111111-2222-3333-4444-555555555553",
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
        "actual_effort_hours": None
    },
    {
        "id": "11111111-2222-3333-4444-555555555554",
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
        "actual_effort_hours": None
    }
]

async def create_migration_waves_raw_sql(session: AsyncSession):
    """Create migration wave definitions using raw SQL."""
    print("  🌊 Creating migration waves...")
    
    for wave_data in MIGRATION_WAVES:
        sql = """
        INSERT INTO migration_waves (
            id, client_account_id, engagement_id, wave_number, name, description, status,
            planned_start_date, planned_end_date, actual_start_date, actual_end_date,
            total_assets, completed_assets, failed_assets, estimated_cost, actual_cost,
            estimated_effort_hours, actual_effort_hours, created_by, created_at
        ) VALUES (
            :id, :client_account_id, :engagement_id, :wave_number, :name, :description, :status,
            :planned_start_date, :planned_end_date, :actual_start_date, :actual_end_date,
            :total_assets, :completed_assets, :failed_assets, :estimated_cost, :actual_cost,
            :estimated_effort_hours, :actual_effort_hours, :created_by, :created_at
        )
        """
        
        await session.execute(text(sql), {
            "id": wave_data["id"],
            "client_account_id": str(DEMO_CLIENT_ID),
            "engagement_id": str(DEMO_ENGAGEMENT_ID),
            "wave_number": wave_data["wave_number"],
            "name": wave_data["name"],
            "description": wave_data["description"],
            "status": wave_data["status"],
            "planned_start_date": wave_data["planned_start_date"],
            "planned_end_date": wave_data["planned_end_date"],
            "actual_start_date": wave_data["actual_start_date"],
            "actual_end_date": wave_data["actual_end_date"],
            "total_assets": 0,  # Will be updated later
            "completed_assets": 0,
            "failed_assets": 0,
            "estimated_cost": wave_data["estimated_cost"],
            "actual_cost": wave_data["actual_cost"],
            "estimated_effort_hours": wave_data["estimated_effort_hours"],
            "actual_effort_hours": wave_data["actual_effort_hours"],
            "created_by": str(USER_IDS["engagement_manager"]),
            "created_at": datetime.now(timezone.utc)
        })
    
    return len(MIGRATION_WAVES)

async def update_assets_with_migration_planning(session: AsyncSession):
    """Update all assets with 6R strategies and migration planning using raw SQL."""
    print("  🎯 Updating assets with migration planning...")
    
    # Get all assets
    assets_sql = """
    SELECT id, name, asset_type, business_criticality, technology_stack, operating_system, 
           custom_attributes, dependencies
    FROM assets 
    WHERE client_account_id = :client_account_id
    ORDER BY asset_type, name
    """
    
    result = await session.execute(text(assets_sql), {"client_account_id": str(DEMO_CLIENT_ID)})
    assets = result.fetchall()
    
    strategy_counts = {}
    wave_assignments = {1: 0, 2: 0, 3: 0, 4: 0}
    readiness_counts = {}
    
    for asset in assets:
        # Assign 6R strategy based on asset type and characteristics
        if asset.asset_type in ["network", "load_balancer"]:
            strategy = "replace"
            wave = 1  # Network infrastructure first
            readiness = "Ready"
            complexity = "High"
            priority = 9
            migration_status = "migrated"  # Wave 1 completed
        elif asset.asset_type == "database":
            # Database strategy based on technology and criticality
            custom_attrs = asset.custom_attributes or {}
            if isinstance(custom_attrs, str):
                import json
                custom_attrs = json.loads(custom_attrs)
            
            if custom_attrs.get("database_type") == "Oracle":
                strategy = "replatform" if asset.business_criticality == "Critical" else "rehost"
            elif custom_attrs.get("database_type") == "PostgreSQL":
                strategy = "rehost"  # Simpler migration for PostgreSQL
            else:
                strategy = "replatform"
            
            wave = 2  # Databases in wave 2
            readiness = "Ready" if strategy == "rehost" else "Needs Analysis"
            complexity = "High" if strategy == "replatform" else "Medium"
            priority = 8
            migration_status = "migrating"  # Wave 2 in progress
        elif asset.asset_type == "application":
            # Application strategy based on technology stack and criticality
            tech_stack = asset.technology_stack or ""
            if "Java" in tech_stack or ".NET Core" in tech_stack:
                strategy = "replatform"
                readiness = "Ready"
                complexity = "Medium"
            elif "Legacy" in tech_stack or ".NET Framework" in tech_stack:
                strategy = "refactor"
                readiness = "Business Review"
                complexity = "High"
            elif "Python" in tech_stack or "Node.js" in tech_stack:
                strategy = "rehost"
                readiness = "Ready"
                complexity = "Low"
            else:
                strategy = "replace"
                readiness = "Needs Analysis"
                complexity = "Medium"
            
            wave = 3  # Applications in wave 3
            priority = 7 if asset.business_criticality == "Critical" else 5
            migration_status = "planned"  # Wave 3 planned
        else:  # servers
            # Server strategy based on OS and dependencies
            os = asset.operating_system or ""
            has_dependencies = bool(asset.dependencies)
            
            if "Windows Server 2016" in os or "CentOS 7" in os:
                strategy = "retire"  # Old OS versions
                readiness = "Business Review"
                complexity = "Low"
                wave = 4
                priority = 3
                migration_status = "planned"
            elif has_dependencies:
                strategy = "replatform"
                readiness = "Dependency Blocked"
                complexity = "Medium"
                wave = 3
                priority = 6
                migration_status = "planned"
            else:
                strategy = "rehost"
                readiness = "Ready"
                complexity = "Low"
                wave = 2
                priority = 4
                migration_status = "migrating"
        
        # Update asset with migration planning data using raw SQL
        update_sql = """
        UPDATE assets SET
            six_r_strategy = :six_r_strategy,
            migration_wave = :migration_wave,
            migration_complexity = :migration_complexity,
            migration_priority = :migration_priority,
            sixr_ready = :sixr_ready,
            migration_status = :migration_status
        WHERE id = :asset_id
        """
        
        await session.execute(text(update_sql), {
            "asset_id": asset.id,
            "six_r_strategy": strategy,
            "migration_wave": wave,
            "migration_complexity": complexity,
            "migration_priority": priority,
            "sixr_ready": readiness,
            "migration_status": migration_status
        })
        
        # Count statistics
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        wave_assignments[wave] += 1
        readiness_counts[readiness] = readiness_counts.get(readiness, 0) + 1
    
    return len(assets), strategy_counts, wave_assignments, readiness_counts

async def update_wave_statistics(session: AsyncSession, wave_assignments: dict):
    """Update migration wave statistics based on asset assignments."""
    print("  📊 Updating wave statistics...")
    
    for wave_num, asset_count in wave_assignments.items():
        wave_data = MIGRATION_WAVES[wave_num - 1]
        
        # Set completed/failed assets based on wave status
        if wave_data["status"] == "completed":
            completed_assets = asset_count
            failed_assets = 0
        elif wave_data["status"] == "in_progress":
            completed_assets = asset_count // 2  # 50% complete
            failed_assets = max(1, asset_count // 10)  # 10% failed
        else:
            completed_assets = 0
            failed_assets = 0
        
        update_sql = """
        UPDATE migration_waves SET
            total_assets = :total_assets,
            completed_assets = :completed_assets,
            failed_assets = :failed_assets
        WHERE wave_number = :wave_number AND client_account_id = :client_account_id
        """
        
        await session.execute(text(update_sql), {
            "wave_number": wave_num,
            "client_account_id": str(DEMO_CLIENT_ID),
            "total_assets": asset_count,
            "completed_assets": completed_assets,
            "failed_assets": failed_assets
        })

async def create_migration_planning_raw_sql():
    """Create comprehensive migration planning data using raw SQL."""
    print("🎯 Creating migration planning...")
    
    async with AsyncSessionLocal() as session:
        # Create migration waves
        waves_created = await create_migration_waves_raw_sql(session)
        print(f"    ✅ Created {waves_created} migration waves")
        
        # Update assets with 6R strategies and waves
        total_assets, strategy_counts, wave_assignments, readiness_counts = await update_assets_with_migration_planning(session)
        print(f"    ✅ Updated {total_assets} assets with migration planning")
        
        # Update wave statistics
        await update_wave_statistics(session, wave_assignments)
        print("    ✅ Updated wave statistics")
        
        # Commit all changes
        await session.commit()
        
        print("\n✅ Migration planning created successfully!")
        print(f"   📊 Total Assets: {total_assets}")
        print(f"   🌊 Migration Waves: {waves_created}")
        
        print("\n   🎯 6R Strategy Distribution:")
        for strategy, count in sorted(strategy_counts.items()):
            percentage = (count / total_assets) * 100
            print(f"     {strategy.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        print("\n   🌊 Wave Assignment:")
        for wave_num, count in sorted(wave_assignments.items()):
            wave_name = MIGRATION_WAVES[wave_num - 1]["name"]
            wave_status = MIGRATION_WAVES[wave_num - 1]["status"]
            percentage = (count / total_assets) * 100
            print(f"     Wave {wave_num} ({wave_name}): {count} assets ({percentage:.1f}%) - {wave_status.upper()}")
        
        print("\n   🚦 Readiness Status:")
        for readiness, count in sorted(readiness_counts.items()):
            percentage = (count / total_assets) * 100
            print(f"     {readiness}: {count} ({percentage:.1f}%)")
        
        print("\n   💰 Migration Cost Estimates:")
        total_estimated = sum(wave["estimated_cost"] for wave in MIGRATION_WAVES)
        total_actual = sum(wave.get("actual_cost", 0) for wave in MIGRATION_WAVES if wave.get("actual_cost"))
        print(f"     Total Estimated: ${total_estimated:,}")
        print(f"     Spent to Date: ${total_actual:,}")
        print(f"     Remaining Budget: ${total_estimated - total_actual:,}")
        
        print("\n   ⏱️ Effort Estimates:")
        total_effort = sum(wave["estimated_effort_hours"] for wave in MIGRATION_WAVES)
        actual_effort = sum(wave.get("actual_effort_hours", 0) for wave in MIGRATION_WAVES if wave.get("actual_effort_hours"))
        print(f"     Total Estimated: {total_effort:,} hours")
        print(f"     Effort to Date: {actual_effort:,} hours")
        print(f"     Remaining Effort: {total_effort - actual_effort:,} hours")

if __name__ == "__main__":
    asyncio.run(create_migration_planning_raw_sql())