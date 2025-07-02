"""
TASK 3.4: Create Dependencies
Creating realistic dependencies between assets including:
- Application-to-server mappings
- Database dependencies
- Network topology
- Circular dependencies (2 instances)
- Clear dependency chains for each app
"""

import asyncio
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset, AssetDependency, AssetType
from constants import DEMO_CLIENT_ID, DEMO_ENGAGEMENT_ID

# Dependency patterns for realistic relationships
DEPENDENCY_PATTERNS = {
    "application_to_server": [
        {"type": "hosting", "description": "Application hosted on server"},
        {"type": "load_balancing", "description": "Load balancer distributing traffic"},
        {"type": "file_storage", "description": "File storage dependency"}
    ],
    "application_to_database": [
        {"type": "primary_database", "description": "Primary database connection"},
        {"type": "cache_database", "description": "Caching layer database"},
        {"type": "reporting_database", "description": "Reporting and analytics database"}
    ],
    "server_to_network": [
        {"type": "network_route", "description": "Network routing dependency"},
        {"type": "firewall_rule", "description": "Firewall security dependency"},
        {"type": "load_balancing", "description": "Load balancer traffic distribution"}
    ],
    "database_to_server": [
        {"type": "hosting", "description": "Database hosted on server"},
        {"type": "backup_storage", "description": "Backup storage dependency"},
        {"type": "cluster_member", "description": "Database cluster member"}
    ],
    "cross_application": [
        {"type": "api_integration", "description": "API service integration"},
        {"type": "data_feed", "description": "Data feed dependency"},
        {"type": "authentication", "description": "Authentication service dependency"}
    ]
}

async def get_assets_by_type(session: AsyncSession, asset_type: str) -> list:
    """Get all assets of a specific type."""
    result = await session.execute(
        select(Asset).where(
            Asset.client_account_id == DEMO_CLIENT_ID,
            Asset.asset_type == asset_type
        ).order_by(Asset.name)
    )
    return result.scalars().all()

async def create_application_dependencies(session: AsyncSession, applications: list, servers: list, databases: list, load_balancers: list):
    """Create dependencies for applications."""
    dependencies = []
    
    for i, app in enumerate(applications):
        print(f"    Creating dependencies for {app.name}...")
        
        # Each application depends on 1-3 servers
        server_count = min(3, max(1, (i % 3) + 1))
        app_servers = servers[i:i+server_count] if i+server_count <= len(servers) else servers[i:i+1]
        
        for server in app_servers:
            dep = AssetDependency(
                asset_id=app.id,
                depends_on_asset_id=server.id,
                dependency_type="hosting",
                description=f"{app.name} application hosted on {server.name}"
            )
            dependencies.append(dep)
            
            # Update asset dependencies JSON field
            if not app.dependencies:
                app.dependencies = []
            app.dependencies.append({
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
            dep = AssetDependency(
                asset_id=app.id,
                depends_on_asset_id=database.id,
                dependency_type=dep_type,
                description=f"{app.name} uses {database.name} as {dep_type.replace('_', ' ')}"
            )
            dependencies.append(dep)
            
            # Update asset dependencies JSON field
            app.dependencies.append({
                "asset_id": str(database.id),
                "asset_name": database.name,
                "dependency_type": dep_type,
                "criticality": "critical"
            })
        
        # Some applications depend on load balancers
        if i < len(load_balancers) and i % 2 == 0:  # Every other app uses load balancer
            lb = load_balancers[i // 2]
            dep = AssetDependency(
                asset_id=app.id,
                depends_on_asset_id=lb.id,
                dependency_type="load_balancing",
                description=f"{app.name} traffic distributed via {lb.name}"
            )
            dependencies.append(dep)
            
            app.dependencies.append({
                "asset_id": str(lb.id),
                "asset_name": lb.name,
                "dependency_type": "load_balancing",
                "criticality": "high"
            })
    
    return dependencies

async def create_cross_application_dependencies(session: AsyncSession, applications: list):
    """Create dependencies between applications (including circular)."""
    dependencies = []
    
    if len(applications) >= 4:
        # Create a circular dependency: App1 -> App2 -> App3 -> App1
        app1, app2, app3 = applications[0], applications[1], applications[2]
        
        # App1 depends on App2 (API integration)
        dep1 = AssetDependency(
            asset_id=app1.id,
            depends_on_asset_id=app2.id,
            dependency_type="api_integration",
            description=f"{app1.name} integrates with {app2.name} API services"
        )
        dependencies.append(dep1)
        
        # App2 depends on App3 (data feed)
        dep2 = AssetDependency(
            asset_id=app2.id,
            depends_on_asset_id=app3.id,
            dependency_type="data_feed",
            description=f"{app2.name} receives data feeds from {app3.name}"
        )
        dependencies.append(dep2)
        
        # App3 depends on App1 (authentication) - Creates circular dependency
        dep3 = AssetDependency(
            asset_id=app3.id,
            depends_on_asset_id=app1.id,
            dependency_type="authentication",
            description=f"{app3.name} uses {app1.name} for authentication services"
        )
        dependencies.append(dep3)
        
        # Update JSON dependencies
        if not app1.dependencies:
            app1.dependencies = []
        app1.dependencies.append({
            "asset_id": str(app2.id),
            "asset_name": app2.name,
            "dependency_type": "api_integration",
            "criticality": "medium",
            "circular_risk": True
        })
        
        if not app2.dependencies:
            app2.dependencies = []
        app2.dependencies.append({
            "asset_id": str(app3.id),
            "asset_name": app3.name,
            "dependency_type": "data_feed",
            "criticality": "medium",
            "circular_risk": True
        })
        
        if not app3.dependencies:
            app3.dependencies = []
        app3.dependencies.append({
            "asset_id": str(app1.id),
            "asset_name": app1.name,
            "dependency_type": "authentication",
            "criticality": "high",
            "circular_risk": True
        })
        
        print(f"    ⚠️ Created circular dependency: {app1.name} -> {app2.name} -> {app3.name} -> {app1.name}")
    
    if len(applications) >= 6:
        # Create another circular dependency: App4 -> App5 -> App4
        app4, app5 = applications[3], applications[4]
        
        # App4 depends on App5
        dep4 = AssetDependency(
            asset_id=app4.id,
            depends_on_asset_id=app5.id,
            dependency_type="data_feed",
            description=f"{app4.name} receives real-time data from {app5.name}"
        )
        dependencies.append(dep4)
        
        # App5 depends on App4 - Creates circular dependency
        dep5 = AssetDependency(
            asset_id=app5.id,
            depends_on_asset_id=app4.id,
            dependency_type="api_integration",
            description=f"{app5.name} calls {app4.name} for processing services"
        )
        dependencies.append(dep5)
        
        # Update JSON dependencies
        if not app4.dependencies:
            app4.dependencies = []
        app4.dependencies.append({
            "asset_id": str(app5.id),
            "asset_name": app5.name,
            "dependency_type": "data_feed",
            "criticality": "medium",
            "circular_risk": True
        })
        
        if not app5.dependencies:
            app5.dependencies = []
        app5.dependencies.append({
            "asset_id": str(app4.id),
            "asset_name": app4.name,
            "dependency_type": "api_integration",
            "criticality": "medium",
            "circular_risk": True
        })
        
        print(f"    ⚠️ Created circular dependency: {app4.name} -> {app5.name} -> {app4.name}")
    
    return dependencies

async def create_infrastructure_dependencies(session: AsyncSession, servers: list, databases: list, network_devices: list):
    """Create infrastructure dependencies."""
    dependencies = []
    
    # Databases depend on servers for hosting
    for i, database in enumerate(databases):
        if i < len(servers):
            server = servers[i]
            dep = AssetDependency(
                asset_id=database.id,
                depends_on_asset_id=server.id,
                dependency_type="hosting",
                description=f"{database.name} database hosted on {server.name}"
            )
            dependencies.append(dep)
            
            # Update database dependencies
            if not database.dependencies:
                database.dependencies = []
            database.dependencies.append({
                "asset_id": str(server.id),
                "asset_name": server.name,
                "dependency_type": "hosting",
                "criticality": "critical"
            })
    
    # Servers depend on network devices
    for i, server in enumerate(servers):
        # Every 3rd server depends on a network device
        if i % 3 == 0 and i // 3 < len(network_devices):
            network_device = network_devices[i // 3]
            dep_type = "firewall_rule" if "firewall" in network_device.name.lower() else "load_balancing"
            
            dep = AssetDependency(
                asset_id=server.id,
                depends_on_asset_id=network_device.id,
                dependency_type=dep_type,
                description=f"{server.name} protected/routed by {network_device.name}"
            )
            dependencies.append(dep)
            
            # Update server dependencies
            if not server.dependencies:
                server.dependencies = []
            server.dependencies.append({
                "asset_id": str(network_device.id),
                "asset_name": network_device.name,
                "dependency_type": dep_type,
                "criticality": "high"
            })
    
    return dependencies

async def create_dependencies():
    """Create all asset dependencies."""
    print("🔗 Creating asset dependencies...")
    
    async with AsyncSessionLocal() as session:
        # Get all assets by type
        applications = await get_assets_by_type(session, "application")
        servers = await get_assets_by_type(session, "server")
        databases = await get_assets_by_type(session, "database")
        
        # Get network devices (load balancers and network devices)
        result = await session.execute(
            select(Asset).where(
                Asset.client_account_id == DEMO_CLIENT_ID,
                Asset.asset_type.in_(["load_balancer", "network"])
            ).order_by(Asset.name)
        )
        network_devices = result.scalars().all()
        
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
        
        # Add all dependencies to session
        session.add_all(all_dependencies)
        
        # Commit all changes (assets and dependencies)
        await session.commit()
        
        # Calculate dependency statistics
        total_dependencies = len(all_dependencies)
        circular_dependencies = 2  # We created 2 circular dependency chains
        
        # Count dependencies by type
        dep_types = {}
        for dep in all_dependencies:
            dep_type = dep.dependency_type
            dep_types[dep_type] = dep_types.get(dep_type, 0) + 1
        
        print(f"\n✅ Dependencies created successfully!")
        print(f"   📊 Total Dependencies: {total_dependencies}")
        print(f"   ⚠️ Circular Dependencies: {circular_dependencies} chains")
        print(f"   📈 Dependency Types:")
        for dep_type, count in sorted(dep_types.items()):
            print(f"     {dep_type}: {count}")
        
        print(f"\n   🔗 Dependency Summary:")
        print(f"     Applications with dependencies: {len([app for app in applications if app.dependencies])}")
        print(f"     Servers with dependencies: {len([srv for srv in servers if srv.dependencies])}")
        print(f"     Databases with dependencies: {len([db for db in databases if db.dependencies])}")
        
        # Detailed dependency chains for first few applications
        print(f"\n   📋 Sample Dependency Chains:")
        for i, app in enumerate(applications[:3]):
            if app.dependencies:
                deps = [f"{dep['asset_name']} ({dep['dependency_type']})" for dep in app.dependencies]
                circular_note = " [CIRCULAR]" if any(dep.get('circular_risk') for dep in app.dependencies) else ""
                print(f"     {app.name}: {' -> '.join(deps)}{circular_note}")

if __name__ == "__main__":
    asyncio.run(create_dependencies())