"""
TASK 3.3: Create Assets (Raw SQL Approach)
Creating 60 assets using raw SQL to bypass enum casting issues.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone

from constants import DEMO_CLIENT_ID, DEMO_ENGAGEMENT_ID, FLOW_IDS, USER_IDS
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal


# Asset data generators (same as before)
def generate_application_asset(index: int, flow_info: dict) -> dict:
    """Generate application asset data."""
    app_names = [
        "CustomerPortal",
        "FinanceSystem",
        "HRManagement",
        "InventoryERP",
        "SalesForce",
        "MarketingPortal",
        "DataWarehouse",
        "ReportingEngine",
        "DocumentManagement",
        "CommunicationPlatform",
    ]

    tech_stacks = [
        "Java Spring Boot",
        ".NET Core",
        "Python Django",
        "Node.js Express",
        "React + REST API",
        "Angular + .NET",
        "Vue.js + Laravel",
        "Legacy .NET Framework",
    ]

    app_name = app_names[index % len(app_names)]

    return {
        "id": str(uuid.uuid4()),
        "name": f"{app_name}-{index:02d}",
        "asset_name": f"{app_name}-{index:02d}",
        "hostname": f"{app_name.lower()}-{index:02d}.democorp.com",
        "asset_type": "application",
        "description": f"Business application: {app_name}",
        "application_name": app_name,
        "technology_stack": tech_stacks[index % len(tech_stacks)],
        "environment": ["Production", "Development", "Testing"][index % 3],
        "business_owner": f"business-team-{(index % 3) + 1}@democorp.com",
        "technical_owner": f"dev-team-{(index % 4) + 1}@democorp.com",
        "department": ["Finance", "HR", "Sales", "Marketing", "IT"][index % 5],
        "business_criticality": ["Critical", "High", "Medium", "Low"][index % 4],
        "criticality": ["Critical", "High", "Medium", "Low"][index % 4],
        "six_r_strategy": ["replatform", "refactor", "rehost", "replace"][index % 4],
        "migration_complexity": ["High", "Medium", "Low"][index % 3],
        "migration_priority": (index % 10) + 1,
        "migration_wave": ((index % 4) + 1),
        "status": "active",
        "migration_status": (
            "assessed" if flow_info.get("state") == "complete" else "discovered"
        ),
        "custom_attributes": json.dumps(
            {
                "user_count": (index + 1) * 150,
                "uptime_sla": f"{95 + (index % 5)}.{index % 10}%",
                "compliance_required": index % 2 == 0,
                "data_classification": [
                    "Public",
                    "Internal",
                    "Confidential",
                    "Restricted",
                ][index % 4],
            }
        ),
        "current_monthly_cost": 2000 + (index * 500),
        "estimated_cloud_cost": 1500 + (index * 400),
        "discovery_method": "application_scan",
        "discovery_source": "Application Discovery Service",
    }


def generate_server_asset(index: int, flow_info: dict, is_linux: bool = True) -> dict:
    """Generate server asset data."""
    os_family = "Linux" if is_linux else "Windows"

    linux_os = ["RHEL 8.5", "Ubuntu 20.04 LTS", "CentOS 7.9", "SUSE Enterprise 15"]
    windows_os = ["Windows Server 2019", "Windows Server 2022", "Windows Server 2016"]

    server_roles = [
        "Web Server",
        "Application Server",
        "File Server",
        "Print Server",
        "Domain Controller",
        "Mail Server",
        "Proxy Server",
        "Backup Server",
    ]

    return {
        "id": str(uuid.uuid4()),
        "name": f"{'lnx' if is_linux else 'win'}-srv-{index:03d}",
        "asset_name": f"{'lnx' if is_linux else 'win'}-srv-{index:03d}",
        "hostname": f"{'lnx' if is_linux else 'win'}-srv-{index:03d}.democorp.com",
        "asset_type": "server",
        "description": f"{os_family} {server_roles[index % len(server_roles)]}",
        "ip_address": f"10.{1 if is_linux else 2}.{(index // 254) + 1}.{(index % 254) + 1}",
        "fqdn": f"{'lnx' if is_linux else 'win'}-srv-{index:03d}.democorp.com",
        "operating_system": (
            linux_os[index % len(linux_os)]
            if is_linux
            else windows_os[index % len(windows_os)]
        ),
        "os_version": (
            f"{(index % 3) + 8}.{index % 10}"
            if is_linux
            else f"10.0.{17763 + (index % 1000)}"
        ),
        "cpu_cores": [4, 8, 16, 32][index % 4],
        "memory_gb": [16, 32, 64, 128][index % 4],
        "storage_gb": [500, 1000, 2000, 4000][index % 4],
        "environment": ["Production", "Development", "Testing", "Staging"][index % 4],
        "location": [
            "Data Center East",
            "Data Center West",
            "AWS US-East-1",
            "Azure Central US",
        ][index % 4],
        "datacenter": ["DC-EAST-01", "DC-WEST-02", "AWS-US-EAST-1", "AZURE-CENTRAL-US"][
            index % 4
        ],
        "rack_location": f"Rack-{(index % 20) + 1}-U{(index % 40) + 1}",
        "business_owner": "Infrastructure Team",
        "technical_owner": f"infra-team-{(index % 3) + 1}@democorp.com",
        "department": "IT",
        "business_criticality": ["Critical", "High", "Medium", "Low"][index % 4],
        "criticality": ["Critical", "High", "Medium", "Low"][index % 4],
        "six_r_strategy": ["rehost", "replatform", "retire"][index % 3],
        "migration_complexity": ["Low", "Medium", "High"][index % 3],
        "migration_priority": (index % 10) + 1,
        "migration_wave": ((index % 4) + 1),
        "status": "active",
        "migration_status": (
            "assessed" if flow_info.get("state") == "complete" else "discovered"
        ),
        "cpu_utilization_percent": min(95, 20 + (index % 60)),
        "memory_utilization_percent": min(90, 30 + (index % 50)),
        "current_monthly_cost": 300 + (index * 100),
        "estimated_cloud_cost": 250 + (index * 80),
        "custom_attributes": json.dumps(
            {
                "virtualization_platform": ["VMware", "Hyper-V", "KVM", "Physical"][
                    index % 4
                ],
                "backup_schedule": ["Daily", "Weekly", "Monthly"][index % 3],
                "patch_group": f"Group-{(index % 5) + 1}",
                "compliance_scope": ["SOX", "PCI", "HIPAA", "None"][index % 4],
            }
        ),
        "discovery_method": "network_scan",
        "discovery_source": "Azure Migrate",
    }


def generate_database_asset(index: int, flow_info: dict, db_type: str) -> dict:
    """Generate database asset data."""
    db_versions = {
        "Oracle": ["19c", "18c", "12c", "11g"],
        "SQL Server": ["2019", "2017", "2016", "2014"],
        "PostgreSQL": ["13.7", "12.11", "11.16", "10.21"],
    }

    return {
        "id": str(uuid.uuid4()),
        "name": f"db-{db_type.lower().replace(' ', '')}-{index:02d}",
        "asset_name": f"db-{db_type.lower().replace(' ', '')}-{index:02d}",
        "hostname": f"db-{db_type.lower().replace(' ', '')}-{index:02d}.democorp.com",
        "asset_type": "database",
        "description": f"{db_type} Database Server",
        "ip_address": f"10.3.{(index // 254) + 1}.{(index % 254) + 1}",
        "fqdn": f"db-{db_type.lower().replace(' ', '')}-{index:02d}.democorp.com",
        "operating_system": (
            "RHEL 8.5" if db_type == "PostgreSQL" else "Windows Server 2019"
        ),
        "cpu_cores": [8, 16, 32][index % 3],
        "memory_gb": [32, 64, 128][index % 3],
        "storage_gb": [1000, 2000, 5000][index % 3],
        "environment": ["Production", "Development", "Testing"][index % 3],
        "location": ["Data Center East", "Data Center West"][index % 2],
        "datacenter": ["DC-EAST-01", "DC-WEST-02"][index % 2],
        "business_owner": "Database Team",
        "technical_owner": f"dba-{(index % 2) + 1}@democorp.com",
        "department": "IT",
        "business_criticality": ["Critical", "High"][index % 2],
        "criticality": ["Critical", "High"][index % 2],
        "six_r_strategy": ["replatform", "rehost", "refactor"][index % 3],
        "migration_complexity": ["High", "Medium"][index % 2],
        "migration_priority": (index % 5) + 6,
        "migration_wave": ((index % 3) + 1),
        "status": "active",
        "migration_status": (
            "assessed" if flow_info.get("state") == "complete" else "discovered"
        ),
        "current_monthly_cost": 1500 + (index * 500),
        "estimated_cloud_cost": 1200 + (index * 400),
        "custom_attributes": json.dumps(
            {
                "database_type": db_type,
                "database_version": db_versions[db_type][
                    index % len(db_versions[db_type])
                ],
                "backup_strategy": ["Full Daily", "Incremental", "Log Shipping"][
                    index % 3
                ],
                "replication": ["Active-Passive", "Active-Active", "None"][index % 3],
                "max_connections": 100 + (index * 50),
                "storage_type": ["SAN", "Local SSD", "NAS"][index % 3],
                "clustering": index % 2 == 0,
            }
        ),
        "discovery_method": "database_scan",
        "discovery_source": "Database Discovery Tool",
    }


def generate_network_asset(index: int, flow_info: dict, device_type: str) -> dict:
    """Generate network device asset data."""
    device_models = {
        "load_balancer": [
            "F5 Big-IP 4000",
            "HAProxy Enterprise",
            "Citrix ADC",
            "AWS ALB",
        ],
        "firewall": [
            "Cisco ASA 5516",
            "Palo Alto PA-850",
            "Fortinet FortiGate",
            "pfSense",
        ],
    }

    return {
        "id": str(uuid.uuid4()),
        "name": f"net-{device_type.replace('_', '')}-{index:02d}",
        "asset_name": f"net-{device_type.replace('_', '')}-{index:02d}",
        "hostname": f"net-{device_type.replace('_', '')}-{index:02d}.democorp.com",
        "asset_type": "load_balancer" if device_type == "load_balancer" else "network",
        "description": f"Network {device_type.replace('_', ' ').title()} Device",
        "ip_address": f"192.168.{index + 1}.1",
        "fqdn": f"net-{device_type.replace('_', '')}-{index:02d}.democorp.com",
        "environment": ["Production", "Development"][index % 2],
        "location": ["Data Center East", "Data Center West"][index % 2],
        "datacenter": ["DC-EAST-01", "DC-WEST-02"][index % 2],
        "business_owner": "Network Team",
        "technical_owner": f"network-{(index % 2) + 1}@democorp.com",
        "department": "IT",
        "business_criticality": "Critical",
        "criticality": "Critical",
        "six_r_strategy": ["replace", "rehost"][index % 2],
        "migration_complexity": "High",
        "migration_priority": 9,
        "migration_wave": 1,
        "status": "active",
        "migration_status": (
            "assessed" if flow_info.get("state") == "complete" else "discovered"
        ),
        "current_monthly_cost": 800 + (index * 200),
        "estimated_cloud_cost": 600 + (index * 150),
        "custom_attributes": json.dumps(
            {
                "device_type": device_type.replace("_", " ").title(),
                "model": device_models[device_type][
                    index % len(device_models[device_type])
                ],
                "firmware_version": f"15.{index}.{(index * 2) % 10}",
                "throughput_gbps": [1, 10, 40][index % 3],
                "port_count": [24, 48, 96][index % 3],
                "redundancy": "Active-Passive",
                "vlan_count": 10 + (index * 5),
            }
        ),
        "discovery_method": "network_scan",
        "discovery_source": "Network Discovery Tool",
    }


async def insert_asset_raw_sql(session: AsyncSession, asset_data: dict, flow_id: str):
    """Insert asset using raw SQL to bypass enum casting."""
    sql = """
    INSERT INTO assets (
        id, client_account_id, engagement_id, flow_id, name, asset_name, hostname,
        asset_type, description, ip_address, fqdn, environment, location, datacenter,
        rack_location, operating_system, os_version, cpu_cores, memory_gb, storage_gb,
        business_owner, technical_owner, department, application_name, technology_stack,
        criticality, business_criticality, custom_attributes, six_r_strategy,
        migration_complexity, migration_priority, migration_wave, status, migration_status,
        cpu_utilization_percent, memory_utilization_percent, current_monthly_cost,
        estimated_cloud_cost, discovery_method, discovery_source, created_by, imported_by,
        imported_at, created_at, source_phase, current_phase, phase_context
    ) VALUES (
        :id, :client_account_id, :engagement_id, :flow_id, :name, :asset_name, :hostname,
        :asset_type, :description, :ip_address, :fqdn, :environment, :location, :datacenter,
        :rack_location, :operating_system, :os_version, :cpu_cores, :memory_gb, :storage_gb,
        :business_owner, :technical_owner, :department, :application_name, :technology_stack,
        :criticality, :business_criticality, :custom_attributes, :six_r_strategy,
        :migration_complexity, :migration_priority, :migration_wave, :status, :migration_status,
        :cpu_utilization_percent, :memory_utilization_percent, :current_monthly_cost,
        :estimated_cloud_cost, :discovery_method, :discovery_source, :created_by, :imported_by,
        :imported_at, :created_at, :source_phase, :current_phase, :phase_context
    )
    """

    params = {
        "id": asset_data["id"],
        "client_account_id": str(DEMO_CLIENT_ID),
        "engagement_id": str(DEMO_ENGAGEMENT_ID),
        "flow_id": flow_id,
        "name": asset_data["name"],
        "asset_name": asset_data.get("asset_name"),
        "hostname": asset_data.get("hostname"),
        "asset_type": asset_data["asset_type"],
        "description": asset_data.get("description"),
        "ip_address": asset_data.get("ip_address"),
        "fqdn": asset_data.get("fqdn"),
        "environment": asset_data.get("environment"),
        "location": asset_data.get("location"),
        "datacenter": asset_data.get("datacenter"),
        "rack_location": asset_data.get("rack_location"),
        "operating_system": asset_data.get("operating_system"),
        "os_version": asset_data.get("os_version"),
        "cpu_cores": asset_data.get("cpu_cores"),
        "memory_gb": asset_data.get("memory_gb"),
        "storage_gb": asset_data.get("storage_gb"),
        "business_owner": asset_data.get("business_owner"),
        "technical_owner": asset_data.get("technical_owner"),
        "department": asset_data.get("department"),
        "application_name": asset_data.get("application_name"),
        "technology_stack": asset_data.get("technology_stack"),
        "criticality": asset_data.get("criticality"),
        "business_criticality": asset_data.get("business_criticality"),
        "custom_attributes": asset_data.get("custom_attributes"),
        "six_r_strategy": asset_data.get("six_r_strategy"),
        "migration_complexity": asset_data.get("migration_complexity"),
        "migration_priority": asset_data.get("migration_priority"),
        "migration_wave": asset_data.get("migration_wave"),
        "status": asset_data.get("status", "active"),
        "migration_status": asset_data.get("migration_status"),
        "cpu_utilization_percent": asset_data.get("cpu_utilization_percent"),
        "memory_utilization_percent": asset_data.get("memory_utilization_percent"),
        "current_monthly_cost": asset_data.get("current_monthly_cost"),
        "estimated_cloud_cost": asset_data.get("estimated_cloud_cost"),
        "discovery_method": asset_data.get("discovery_method"),
        "discovery_source": asset_data.get("discovery_source"),
        "created_by": str(USER_IDS["analyst"]),
        "imported_by": str(USER_IDS["analyst"]),
        "imported_at": datetime.now(timezone.utc) - timedelta(days=1),
        "created_at": datetime.now(timezone.utc),
        "source_phase": "discovery",
        "current_phase": "discovery",
        "phase_context": "{}",
    }

    await session.execute(text(sql), params)


async def create_assets_raw_sql():
    """Create 60 assets using raw SQL."""
    print("🏗️ Creating assets using raw SQL...")

    # Asset distribution across flows
    FLOW_ASSET_DISTRIBUTION = {
        "complete": {
            "flow_id": str(FLOW_IDS["complete"]),
            "applications": 3,
            "servers": 12,
            "databases": 3,
            "network": 2,
            "state": "complete",
        },
        "field_mapping": {
            "flow_id": str(FLOW_IDS["field_mapping"]),
            "applications": 2,
            "servers": 8,
            "databases": 2,
            "network": 1,
            "state": "in_progress",
        },
        "asset_inventory": {
            "flow_id": str(FLOW_IDS["asset_inventory"]),
            "applications": 3,
            "servers": 10,
            "databases": 3,
            "network": 2,
            "state": "in_progress",
        },
        "failed_import": {
            "flow_id": str(FLOW_IDS["failed_import"]),
            "applications": 1,
            "servers": 3,
            "databases": 1,
            "network": 0,
            "state": "failed",
        },
        "just_started": {
            "flow_id": str(FLOW_IDS["just_started"]),
            "applications": 1,
            "servers": 2,
            "databases": 1,
            "network": 0,
            "state": "in_progress",
        },
    }

    async with AsyncSessionLocal() as session:
        asset_counter = 1
        linux_server_count = 0
        windows_server_count = 0
        oracle_count = 0
        sqlserver_count = 0
        postgres_count = 0
        load_balancer_count = 0
        firewall_count = 0

        for flow_name, distribution in FLOW_ASSET_DISTRIBUTION.items():
            flow_id = distribution["flow_id"]
            flow_info = {"state": distribution["state"]}

            print(f"  📁 Creating assets for {flow_name} flow...")

            # Create applications
            for i in range(distribution["applications"]):
                asset_data = generate_application_asset(asset_counter, flow_info)
                await insert_asset_raw_sql(session, asset_data, flow_id)
                asset_counter += 1

            # Create servers
            for i in range(distribution["servers"]):
                target_linux = 20 * distribution["servers"] // 35
                is_linux = linux_server_count < target_linux

                asset_data = generate_server_asset(asset_counter, flow_info, is_linux)
                await insert_asset_raw_sql(session, asset_data, flow_id)

                if is_linux:
                    linux_server_count += 1
                else:
                    windows_server_count += 1

                asset_counter += 1

            # Create databases
            for i in range(distribution["databases"]):
                if oracle_count < 4:
                    db_type = "Oracle"
                    oracle_count += 1
                elif sqlserver_count < 3:
                    db_type = "SQL Server"
                    sqlserver_count += 1
                else:
                    db_type = "PostgreSQL"
                    postgres_count += 1

                asset_data = generate_database_asset(asset_counter, flow_info, db_type)
                await insert_asset_raw_sql(session, asset_data, flow_id)
                asset_counter += 1

            # Create network devices
            for i in range(distribution["network"]):
                if load_balancer_count < 2:
                    device_type = "load_balancer"
                    load_balancer_count += 1
                else:
                    device_type = "firewall"
                    firewall_count += 1

                asset_data = generate_network_asset(
                    asset_counter, flow_info, device_type
                )
                await insert_asset_raw_sql(session, asset_data, flow_id)
                asset_counter += 1

            flow_total = (
                distribution["applications"]
                + distribution["servers"]
                + distribution["databases"]
                + distribution["network"]
            )
            print(f"    ✅ Created {flow_total} assets for {flow_name}")

        # Commit all changes
        await session.commit()

        # Summary
        total_assets = asset_counter - 1
        applications = sum(d["applications"] for d in FLOW_ASSET_DISTRIBUTION.values())
        servers = sum(d["servers"] for d in FLOW_ASSET_DISTRIBUTION.values())
        databases = sum(d["databases"] for d in FLOW_ASSET_DISTRIBUTION.values())
        network = sum(d["network"] for d in FLOW_ASSET_DISTRIBUTION.values())

        print("\n✅ Assets created successfully using raw SQL!")
        print(f"   📊 Total Assets: {total_assets}")
        print(f"   🖥️ Applications: {applications}")
        print(
            f"   🖥️ Servers: {servers} ({linux_server_count} Linux, {windows_server_count} Windows)"
        )
        print(
            f"   🗄️ Databases: {databases} ({oracle_count} Oracle, {sqlserver_count} SQL Server, {postgres_count} PostgreSQL)"
        )
        print(
            f"   🌐 Network Devices: {network} ({load_balancer_count} Load Balancers, {firewall_count} Firewalls)"
        )


if __name__ == "__main__":
    asyncio.run(create_assets_raw_sql())
