"""
TASK 3.4: Create Dependencies (Raw SQL Approach)
Creating realistic dependencies between assets using raw SQL to bypass enum casting issues.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone

from constants import DEMO_CLIENT_ID, DEMO_ENGAGEMENT_ID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal


async def get_assets_by_type_raw(session: AsyncSession, asset_type: str) -> list:
    """Get all assets of a specific type using raw SQL."""
    sql = """
    SELECT id, name, asset_type, dependencies, custom_attributes
    FROM assets 
    WHERE client_account_id = :client_account_id AND asset_type = :asset_type 
    ORDER BY name
    """
    result = await session.execute(text(sql), {
        "client_account_id": str(DEMO_CLIENT_ID),
        "asset_type": asset_type
    })
    return result.fetchall()

async def insert_dependency_raw_sql(session: AsyncSession, asset_id: str, depends_on_asset_id: str, dependency_type: str, description: str):
    """Insert dependency using raw SQL."""
    sql = """
    INSERT INTO asset_dependencies (id, asset_id, depends_on_asset_id, dependency_type, description, created_at)
    VALUES (:id, :asset_id, :depends_on_asset_id, :dependency_type, :description, :created_at)
    """
    await session.execute(text(sql), {
        "id": str(uuid.uuid4()),
        "asset_id": asset_id,
        "depends_on_asset_id": depends_on_asset_id,
        "dependency_type": dependency_type,
        "description": description,
        "created_at": datetime.now(timezone.utc)
    })

async def update_asset_dependencies_json(session: AsyncSession, asset_id: str, dependencies: list):
    """Update asset's dependencies JSON field using raw SQL."""
    sql = """
    UPDATE assets 
    SET dependencies = :dependencies
    WHERE id = :asset_id
    """
    await session.execute(text(sql), {
        "asset_id": asset_id,
        "dependencies": json.dumps(dependencies)
    })

async def create_application_dependencies(session: AsyncSession, applications: list, servers: list, databases: list, load_balancers: list):
    """Create dependencies for applications."""
    dependencies = []
    
    for i, app in enumerate(applications):
        print(f"    Creating dependencies for {app.name}...")
        
        app_dependencies = []
        
        # Each application depends on 1-3 servers
        server_count = min(3, max(1, (i % 3) + 1))
        app_servers = servers[i:i+server_count] if i+server_count <= len(servers) else servers[i:i+1]
        
        for server in app_servers:
            await insert_dependency_raw_sql(
                session, app.id, server.id, "hosting",
                f"{app.name} application hosted on {server.name}"
            )
            dependencies.append((app.id, server.id, "hosting"))
            
            app_dependencies.append({
                "asset_id": str(server.id),
                "asset_name": server.name,
                "dependency_type": "hosting",
                "criticality": "high"
            })
        
        # Each application depends on 1-2 databases
        db_count = min(2, max(1, (i % 2) + 1))
        app_databases = databases[i:i+db_count] if i+db_count <= len(databases) else databases[i:i+1]
        
        for j, database in enumerate(app_databases):
            dep_type = "primary_database" if j == 0 else "cache_database"
            await insert_dependency_raw_sql(
                session, app.id, database.id, dep_type,
                f"{app.name} uses {database.name} as {dep_type.replace('_', ' ')}"
            )
            dependencies.append((app.id, database.id, dep_type))
            
            app_dependencies.append({
                "asset_id": str(database.id),
                "asset_name": database.name,
                "dependency_type": dep_type,
                "criticality": "critical"
            })
        
        # Some applications depend on load balancers
        if i < len(load_balancers) and i % 2 == 0:  # Every other app uses load balancer
            lb = load_balancers[i // 2]
            await insert_dependency_raw_sql(
                session, app.id, lb.id, "load_balancing",
                f"{app.name} traffic distributed via {lb.name}"
            )
            dependencies.append((app.id, lb.id, "load_balancing"))
            
            app_dependencies.append({
                "asset_id": str(lb.id),
                "asset_name": lb.name,
                "dependency_type": "load_balancing",
                "criticality": "high"
            })
        
        # Update asset's dependencies JSON
        await update_asset_dependencies_json(session, app.id, app_dependencies)
    
    return dependencies

async def create_cross_application_dependencies(session: AsyncSession, applications: list):
    """Create dependencies between applications (including circular)."""
    dependencies = []
    
    if len(applications) >= 4:
        # Create a circular dependency: App1 -> App2 -> App3 -> App1
        app1, app2, app3 = applications[0], applications[1], applications[2]
        
        # App1 depends on App2 (API integration)
        await insert_dependency_raw_sql(
            session, app1.id, app2.id, "api_integration",
            f"{app1.name} integrates with {app2.name} API services"
        )
        dependencies.append((app1.id, app2.id, "api_integration"))
        
        # App2 depends on App3 (data feed)
        await insert_dependency_raw_sql(
            session, app2.id, app3.id, "data_feed",
            f"{app2.name} receives data feeds from {app3.name}"
        )
        dependencies.append((app2.id, app3.id, "data_feed"))
        
        # App3 depends on App1 (authentication) - Creates circular dependency
        await insert_dependency_raw_sql(
            session, app3.id, app1.id, "authentication",
            f"{app3.name} uses {app1.name} for authentication services"
        )
        dependencies.append((app3.id, app1.id, "authentication"))
        
        # Update JSON dependencies for circular relationships
        for app, target, dep_type in [(app1, app2, "api_integration"), (app2, app3, "data_feed"), (app3, app1, "authentication")]:
            # Get existing dependencies
            existing_sql = "SELECT dependencies FROM assets WHERE id = :asset_id"
            result = await session.execute(text(existing_sql), {"asset_id": app.id})
            existing_deps = result.fetchone()
            
            if existing_deps and existing_deps[0]:
                if isinstance(existing_deps[0], str):
                    current_deps = json.loads(existing_deps[0])
                else:
                    current_deps = existing_deps[0]  # Already a list
            else:
                current_deps = []
            current_deps.append({
                "asset_id": str(target.id),
                "asset_name": target.name,
                "dependency_type": dep_type,
                "criticality": "medium",
                "circular_risk": True
            })
            
            await update_asset_dependencies_json(session, app.id, current_deps)
        
        print(f"    ⚠️ Created circular dependency: {app1.name} -> {app2.name} -> {app3.name} -> {app1.name}")
    
    if len(applications) >= 6:
        # Create another circular dependency: App4 -> App5 -> App4
        app4, app5 = applications[3], applications[4]
        
        # App4 depends on App5
        await insert_dependency_raw_sql(
            session, app4.id, app5.id, "data_feed",
            f"{app4.name} receives real-time data from {app5.name}"
        )
        dependencies.append((app4.id, app5.id, "data_feed"))
        
        # App5 depends on App4 - Creates circular dependency
        await insert_dependency_raw_sql(
            session, app5.id, app4.id, "api_integration",
            f"{app5.name} calls {app4.name} for processing services"
        )
        dependencies.append((app5.id, app4.id, "api_integration"))
        
        # Update JSON dependencies for circular relationships
        for app, target, dep_type in [(app4, app5, "data_feed"), (app5, app4, "api_integration")]:
            existing_sql = "SELECT dependencies FROM assets WHERE id = :asset_id"
            result = await session.execute(text(existing_sql), {"asset_id": app.id})
            existing_deps = result.fetchone()
            
            if existing_deps and existing_deps[0]:
                if isinstance(existing_deps[0], str):
                    current_deps = json.loads(existing_deps[0])
                else:
                    current_deps = existing_deps[0]  # Already a list
            else:
                current_deps = []
            current_deps.append({
                "asset_id": str(target.id),
                "asset_name": target.name,
                "dependency_type": dep_type,
                "criticality": "medium",
                "circular_risk": True
            })
            
            await update_asset_dependencies_json(session, app.id, current_deps)
        
        print(f"    ⚠️ Created circular dependency: {app4.name} -> {app5.name} -> {app4.name}")
    
    return dependencies

async def create_infrastructure_dependencies(session: AsyncSession, servers: list, databases: list, network_devices: list):
    """Create infrastructure dependencies."""
    dependencies = []
    
    # Databases depend on servers for hosting
    for i, database in enumerate(databases):
        if i < len(servers):
            server = servers[i]
            await insert_dependency_raw_sql(
                session, database.id, server.id, "hosting",
                f"{database.name} database hosted on {server.name}"
            )
            dependencies.append((database.id, server.id, "hosting"))
            
            # Update database dependencies
            await update_asset_dependencies_json(session, database.id, [{
                "asset_id": str(server.id),
                "asset_name": server.name,
                "dependency_type": "hosting",
                "criticality": "critical"
            }])
    
    # Servers depend on network devices
    for i, server in enumerate(servers):
        # Every 3rd server depends on a network device
        if i % 3 == 0 and i // 3 < len(network_devices):
            network_device = network_devices[i // 3]
            dep_type = "firewall_rule" if "firewall" in network_device.name.lower() else "load_balancing"
            
            await insert_dependency_raw_sql(
                session, server.id, network_device.id, dep_type,
                f"{server.name} protected/routed by {network_device.name}"
            )
            dependencies.append((server.id, network_device.id, dep_type))
            
            # Update server dependencies
            await update_asset_dependencies_json(session, server.id, [{
                "asset_id": str(network_device.id),
                "asset_name": network_device.name,
                "dependency_type": dep_type,
                "criticality": "high"
            }])
    
    return dependencies

async def create_dependencies_raw_sql():
    """Create all asset dependencies using raw SQL."""
    print("🔗 Creating asset dependencies...")
    
    async with AsyncSessionLocal() as session:
        # Get all assets by type using raw SQL
        applications = await get_assets_by_type_raw(session, "application")
        servers = await get_assets_by_type_raw(session, "server")
        databases = await get_assets_by_type_raw(session, "database")
        
        # Get network devices (load balancers and network devices)
        network_sql = """
        SELECT id, name, asset_type, dependencies, custom_attributes
        FROM assets 
        WHERE client_account_id = :client_account_id AND asset_type IN ('load_balancer', 'network')
        ORDER BY name
        """
        result = await session.execute(text(network_sql), {"client_account_id": str(DEMO_CLIENT_ID)})
        network_devices = result.fetchall()
        
        # Get load balancers specifically
        load_balancers = [asset for asset in network_devices if asset.asset_type == "load_balancer"]
        
        print(f"  📊 Found assets: {len(applications)} apps, {len(servers)} servers, {len(databases)} databases, {len(network_devices)} network devices")
        
        all_dependencies = []
        
        # Create application dependencies
        print("  🖥️ Creating application dependencies...")
        app_deps = await create_application_dependencies(session, applications, servers, databases, load_balancers)
        all_dependencies.extend(app_deps)
        print(f"    ✅ Created {len(app_deps)} application dependencies")
        
        # Create cross-application dependencies (including circular)
        print("  🔄 Creating cross-application dependencies...")
        cross_deps = await create_cross_application_dependencies(session, applications)
        all_dependencies.extend(cross_deps)
        print(f"    ✅ Created {len(cross_deps)} cross-application dependencies")
        
        # Create infrastructure dependencies
        print("  🏗️ Creating infrastructure dependencies...")
        infra_deps = await create_infrastructure_dependencies(session, servers, databases, network_devices)
        all_dependencies.extend(infra_deps)
        print(f"    ✅ Created {len(infra_deps)} infrastructure dependencies")
        
        # Commit all changes
        await session.commit()
        
        # Calculate dependency statistics
        total_dependencies = len(all_dependencies)
        circular_dependencies = 2  # We created 2 circular dependency chains
        
        # Count dependencies by type
        dep_types = {}
        for asset_id, depends_on_id, dep_type in all_dependencies:
            dep_types[dep_type] = dep_types.get(dep_type, 0) + 1
        
        print("\n✅ Dependencies created successfully!")
        print(f"   📊 Total Dependencies: {total_dependencies}")
        print(f"   ⚠️ Circular Dependencies: {circular_dependencies} chains")
        print("   📈 Dependency Types:")
        for dep_type, count in sorted(dep_types.items()):
            print(f"     {dep_type}: {count}")
        
        # Sample dependency chains for first few applications
        print("\n   📋 Sample Dependency Chains:")
        for i, app in enumerate(applications[:3]):
            deps_sql = "SELECT dependencies FROM assets WHERE id = :asset_id"
            result = await session.execute(text(deps_sql), {"asset_id": app.id})
            deps_data = result.fetchone()
            
            if deps_data and deps_data[0]:
                if isinstance(deps_data[0], str):
                    deps = json.loads(deps_data[0])
                else:
                    deps = deps_data[0]  # Already a list
                    
                dep_names = [f"{dep['asset_name']} ({dep['dependency_type']})" for dep in deps]
                circular_note = " [CIRCULAR]" if any(dep.get('circular_risk') for dep in deps) else ""
                print(f"     {app.name}: {' -> '.join(dep_names)}{circular_note}")

if __name__ == "__main__":
    asyncio.run(create_dependencies_raw_sql())