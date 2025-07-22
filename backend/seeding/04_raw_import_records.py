"""
TASK 3.1: Create Raw Import Records
Creating realistic asset inventory with raw import records for 3 data imports.
"""

import asyncio

from constants import DEMO_CLIENT_ID, DEMO_ENGAGEMENT_ID, IMPORT_IDS
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.data_import import DataImport
from app.models.data_import.core import RawImportRecord

# Asset distributions for raw records
ASSET_DISTRIBUTIONS = {
    "csv_servers": {
        "total_records": 60,  # Server inventory
        "valid_records": 55,
        "invalid_records": 5,
        "asset_types": ["server", "virtual_machine"]
    },
    "json_applications": {
        "total_records": 55,  # Application catalog
        "valid_records": 50,
        "invalid_records": 5,
        "asset_types": ["application"]
    },
    "excel_dependencies": {
        "total_records": 45,  # Mixed asset types with dependencies
        "valid_records": 40,
        "invalid_records": 5,
        "asset_types": ["server", "database", "network", "application"]
    }
}

def generate_server_record(row_num: int, is_valid: bool = True) -> dict:
    """Generate server asset raw data record."""
    if not is_valid:
        # Invalid records - missing required fields or bad data
        return {
            "hostname": f"INVALID-{row_num}",
            "bad_field": "this should not exist",
            "cpu_cores": "not-a-number",
            "memory_gb": -1,  # Invalid negative memory
        }
    
    # Valid server records
    os_options = ["RHEL 8.5", "Ubuntu 20.04", "Windows Server 2019", "Windows Server 2022", "CentOS 7.9"]
    env_options = ["Production", "Development", "Testing", "Staging"]
    dc_options = ["DC-EAST-01", "DC-WEST-02", "AWS-US-EAST-1", "AZURE-CENTRAL-US"]
    
    base_records = [
        {
            "hostname": f"web-server-{row_num:03d}",
            "ip_address": f"10.1.{(row_num // 254) + 1}.{(row_num % 254) + 1}",
            "operating_system": "RHEL 8.5",
            "cpu_cores": 8,
            "memory_gb": 32,
            "storage_gb": 500,
            "environment": "Production",
            "datacenter": "DC-EAST-01",
            "asset_type": "server",
            "business_owner": "Infrastructure Team",
            "technical_owner": "infra@democorp.com",
            "criticality": "High"
        },
        {
            "hostname": f"db-server-{row_num:03d}",
            "ip_address": f"10.2.{(row_num // 254) + 1}.{(row_num % 254) + 1}",
            "operating_system": "Windows Server 2019",
            "cpu_cores": 16,
            "memory_gb": 64,
            "storage_gb": 2000,
            "environment": "Production",
            "datacenter": "DC-WEST-02",
            "asset_type": "server",
            "business_owner": "Database Team",
            "technical_owner": "dba@democorp.com",
            "criticality": "Critical"
        },
        {
            "hostname": f"app-server-{row_num:03d}",
            "ip_address": f"10.3.{(row_num // 254) + 1}.{(row_num % 254) + 1}",
            "operating_system": "Ubuntu 20.04",
            "cpu_cores": 4,
            "memory_gb": 16,
            "storage_gb": 200,
            "environment": "Development",
            "datacenter": "AWS-US-EAST-1",
            "asset_type": "virtual_machine",
            "business_owner": "Development Team",
            "technical_owner": "dev@democorp.com",
            "criticality": "Medium"
        }
    ]
    
    # Use modulo to cycle through base patterns
    base_record = base_records[row_num % len(base_records)].copy()
    
    # Add some variation
    base_record["hostname"] = base_record["hostname"].replace(f"{row_num:03d}", f"{row_num:03d}")
    base_record["asset_name"] = base_record["hostname"]
    base_record["operating_system"] = os_options[row_num % len(os_options)]
    base_record["environment"] = env_options[row_num % len(env_options)]
    base_record["datacenter"] = dc_options[row_num % len(dc_options)]
    
    # Add performance metrics
    base_record.update({
        "cpu_utilization_percent": min(95, 20 + (row_num % 60)),
        "memory_utilization_percent": min(90, 30 + (row_num % 50)),
        "current_monthly_cost": 500 + (row_num % 1000),
        "discovery_method": "network_scan",
        "discovery_source": "Azure Migrate"
    })
    
    return base_record

def generate_application_record(row_num: int, is_valid: bool = True) -> dict:
    """Generate application asset raw data record."""
    if not is_valid:
        return {
            "application_name": "",  # Missing required field
            "invalid_json": "this is not valid json: {broken",
            "port": "not-a-port-number"
        }
    
    app_types = ["Web Application", "Database Service", "API Service", "Batch Process", "Monitoring Tool"]
    tech_stacks = ["Java Spring", ".NET Core", "Python Django", "Node.js", "PHP Laravel", "Go"]
    criticality_levels = ["Low", "Medium", "High", "Critical"]
    
    return {
        "application_name": f"App-{row_num:03d}-{app_types[row_num % len(app_types)].replace(' ', '')}",
        "asset_name": f"App-{row_num:03d}",
        "application_type": app_types[row_num % len(app_types)],
        "technology_stack": tech_stacks[row_num % len(tech_stacks)],
        "version": f"{(row_num % 5) + 1}.{(row_num % 10) + 1}.{(row_num % 20) + 1}",
        "environment": ["Production", "Development", "Testing"][row_num % 3],
        "business_owner": f"team-{(row_num % 5) + 1}@democorp.com",
        "technical_owner": f"dev-{(row_num % 8) + 1}@democorp.com",
        "criticality": criticality_levels[row_num % len(criticality_levels)],
        "asset_type": "application",
        "port": 8000 + (row_num % 1000),
        "url": f"https://app-{row_num:03d}.democorp.com",
        "database_connections": row_num % 3 + 1,
        "estimated_users": (row_num % 10 + 1) * 100,
        "uptime_sla": f"{95 + (row_num % 5)}.{row_num % 10}%",
        "discovery_method": "application_scan",
        "discovery_source": "Application Discovery Service"
    }

def generate_dependency_record(row_num: int, is_valid: bool = True) -> dict:
    """Generate mixed asset types with dependency information."""
    if not is_valid:
        return {
            "source_asset": "",
            "target_asset": "",
            "dependency_type": "unknown_type"
        }
    
    asset_types = ["database", "network", "load_balancer", "application", "server"]
    dependency_types = ["database_connection", "network_route", "load_balance", "api_call", "file_share"]
    
    asset_type = asset_types[row_num % len(asset_types)]
    
    base_record = {
        "asset_name": f"{asset_type}-{row_num:03d}",
        "asset_type": asset_type,
        "environment": ["Production", "Development", "Testing"][row_num % 3],
        "criticality": ["Low", "Medium", "High", "Critical"][row_num % 4],
        "discovery_method": "dependency_scan",
        "discovery_source": "Network Dependency Tool"
    }
    
    # Asset-type specific fields
    if asset_type == "database":
        base_record.update({
            "database_type": ["Oracle", "SQL Server", "PostgreSQL", "MySQL"][row_num % 4],
            "database_version": f"{(row_num % 3) + 10}.{row_num % 5}",
            "storage_gb": 100 + (row_num % 1000),
            "max_connections": 50 + (row_num % 200),
            "backup_schedule": "Daily",
            "cpu_cores": 4 + (row_num % 8),
            "memory_gb": 16 + (row_num % 48)
        })
    elif asset_type == "network":
        base_record.update({
            "device_type": ["Router", "Switch", "Firewall"][row_num % 3],
            "model": f"Cisco-{1000 + (row_num % 9999)}",
            "ports": 24 + (row_num % 24),
            "management_ip": f"192.168.{(row_num % 254) + 1}.1",
            "firmware_version": f"15.{row_num % 10}.{row_num % 20}"
        })
    elif asset_type == "load_balancer":
        base_record.update({
            "load_balancer_type": ["Application", "Network", "Global"][row_num % 3],
            "throughput_mbps": 1000 + (row_num % 9000),
            "ssl_termination": row_num % 2 == 0,
            "backend_servers": row_num % 5 + 2,
            "health_check_url": f"/health-{row_num}"
        })
    
    # Add dependency information
    if row_num > 1:  # Ensure we have targets for dependencies
        base_record.update({
            "depends_on_asset": f"server-{(row_num - 1):03d}",
            "dependency_type": dependency_types[row_num % len(dependency_types)],
            "dependency_description": f"Service dependency for {base_record['asset_name']}"
        })
    
    return base_record

async def create_raw_import_records():
    """Create raw import records for all three data imports."""
    print("🔄 Creating raw import records...")
    
    async with AsyncSessionLocal() as session:
        # Get data import IDs
        csv_import_id = IMPORT_IDS["csv_servers"]
        json_import_id = IMPORT_IDS["json_applications"]
        excel_import_id = IMPORT_IDS["excel_dependencies"]
        
        # Verify imports exist
        imports_query = await session.execute(
            select(DataImport).where(DataImport.id.in_([csv_import_id, json_import_id, excel_import_id]))
        )
        imports = imports_query.scalars().all()
        
        if len(imports) != 3:
            print(f"❌ Expected 3 data imports, found {len(imports)}")
            return
        
        # Create records for CSV server import
        print("  📄 Creating CSV server records...")
        csv_dist = ASSET_DISTRIBUTIONS["csv_servers"]
        csv_records = []
        
        for i in range(csv_dist["total_records"]):
            is_valid = i < csv_dist["valid_records"]
            raw_data = generate_server_record(i + 1, is_valid)
            
            record = RawImportRecord(
                data_import_id=csv_import_id,
                client_account_id=DEMO_CLIENT_ID,
                engagement_id=DEMO_ENGAGEMENT_ID,
                row_number=i + 1,
                raw_data=raw_data,
                cleansed_data=None,  # Let agentic data cleansing handle this properly
                is_valid=is_valid,
                is_processed=is_valid,
                validation_errors=None if is_valid else ["Missing required fields", "Invalid data types"],
                processing_notes=f"Row {i + 1} - {'Valid' if is_valid else 'Invalid'} server record"
            )
            csv_records.append(record)
        
        session.add_all(csv_records)
        print(f"    ✅ Created {len(csv_records)} CSV server records")
        
        # Create records for JSON application import
        print("  📄 Creating JSON application records...")
        json_dist = ASSET_DISTRIBUTIONS["json_applications"]
        json_records = []
        
        for i in range(json_dist["total_records"]):
            is_valid = i < json_dist["valid_records"]
            raw_data = generate_application_record(i + 1, is_valid)
            
            record = RawImportRecord(
                data_import_id=json_import_id,
                client_account_id=DEMO_CLIENT_ID,
                engagement_id=DEMO_ENGAGEMENT_ID,
                row_number=i + 1,
                raw_data=raw_data,
                cleansed_data=None,  # Let agentic data cleansing handle this properly
                is_valid=is_valid,
                is_processed=False,  # This import is still "processing"
                validation_errors=None if is_valid else ["Invalid JSON structure", "Missing application name"],
                processing_notes=f"Row {i + 1} - {'Valid' if is_valid else 'Invalid'} application record"
            )
            json_records.append(record)
        
        session.add_all(json_records)
        print(f"    ✅ Created {len(json_records)} JSON application records")
        
        # Create records for Excel dependency import
        print("  📄 Creating Excel dependency records...")
        excel_dist = ASSET_DISTRIBUTIONS["excel_dependencies"]
        excel_records = []
        
        for i in range(excel_dist["total_records"]):
            is_valid = i < excel_dist["valid_records"]
            raw_data = generate_dependency_record(i + 1, is_valid)
            
            record = RawImportRecord(
                data_import_id=excel_import_id,
                client_account_id=DEMO_CLIENT_ID,
                engagement_id=DEMO_ENGAGEMENT_ID,
                row_number=i + 1,
                raw_data=raw_data,
                cleansed_data=None,  # Let agentic data cleansing handle this properly
                is_valid=is_valid,
                is_processed=is_valid,
                validation_errors=None if is_valid else ["Missing dependency information", "Invalid asset type"],
                processing_notes=f"Row {i + 1} - {'Valid' if is_valid else 'Invalid'} dependency record"
            )
            excel_records.append(record)
        
        session.add_all(excel_records)
        print(f"    ✅ Created {len(excel_records)} Excel dependency records")
        
        # Commit all records
        await session.commit()
        
        # Summary
        total_records = csv_dist["total_records"] + json_dist["total_records"] + excel_dist["total_records"]
        total_valid = csv_dist["valid_records"] + json_dist["valid_records"] + excel_dist["valid_records"]
        total_invalid = csv_dist["invalid_records"] + json_dist["invalid_records"] + excel_dist["invalid_records"]
        
        print("\n✅ Raw import records created successfully!")
        print(f"   📊 Total Records: {total_records}")
        print(f"   ✅ Valid Records: {total_valid}")
        print(f"   ❌ Invalid Records: {total_invalid}")
        print(f"   📄 CSV Server Records: {csv_dist['total_records']}")
        print(f"   📄 JSON Application Records: {json_dist['total_records']}")
        print(f"   📄 Excel Dependency Records: {excel_dist['total_records']}")

if __name__ == "__main__":
    asyncio.run(create_raw_import_records())