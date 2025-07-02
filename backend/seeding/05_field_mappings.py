"""
TASK 3.2: Create Field Mappings
Creating AI-suggested field mappings with varied confidence scores for all imports.
"""

import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.data_import.mapping import ImportFieldMapping
from constants import DEMO_CLIENT_ID, IMPORT_IDS

# Field mappings for each import type
CSV_SERVER_MAPPINGS = [
    {
        "source_field": "hostname",
        "target_field": "name",
        "match_type": "direct",
        "confidence_score": 0.95,
        "status": "approved",
        "transformation_rules": {"type": "direct_copy"}
    },
    {
        "source_field": "hostname",
        "target_field": "hostname",
        "match_type": "direct",
        "confidence_score": 0.98,
        "status": "approved",
        "transformation_rules": {"type": "direct_copy"}
    },
    {
        "source_field": "ip_address",
        "target_field": "ip_address",
        "match_type": "direct",
        "confidence_score": 0.97,
        "status": "approved",
        "transformation_rules": {"type": "direct_copy", "validation": "ipv4"}
    },
    {
        "source_field": "operating_system",
        "target_field": "operating_system",
        "match_type": "direct",
        "confidence_score": 0.92,
        "status": "approved",
        "transformation_rules": {"type": "normalize_os_name"}
    },
    {
        "source_field": "cpu_cores",
        "target_field": "cpu_cores",
        "match_type": "direct",
        "confidence_score": 0.94,
        "status": "approved",
        "transformation_rules": {"type": "integer_conversion"}
    },
    {
        "source_field": "memory_gb",
        "target_field": "memory_gb",
        "match_type": "direct",
        "confidence_score": 0.91,
        "status": "approved",
        "transformation_rules": {"type": "float_conversion"}
    },
    {
        "source_field": "storage_gb",
        "target_field": "storage_gb",
        "match_type": "direct",
        "confidence_score": 0.89,
        "status": "approved",
        "transformation_rules": {"type": "float_conversion"}
    },
    {
        "source_field": "environment",
        "target_field": "environment",
        "match_type": "direct",
        "confidence_score": 0.96,
        "status": "approved",
        "transformation_rules": {"type": "enum_validation", "valid_values": ["Production", "Development", "Testing", "Staging"]}
    },
    {
        "source_field": "datacenter",
        "target_field": "datacenter",
        "match_type": "direct",
        "confidence_score": 0.93,
        "status": "approved",
        "transformation_rules": {"type": "direct_copy"}
    },
    {
        "source_field": "asset_type",
        "target_field": "asset_type",
        "match_type": "direct",
        "confidence_score": 0.90,
        "status": "approved",
        "transformation_rules": {"type": "enum_validation", "valid_values": ["server", "virtual_machine"]}
    },
    {
        "source_field": "business_owner",
        "target_field": "business_owner",
        "match_type": "direct",
        "confidence_score": 0.88,
        "status": "pending",
        "transformation_rules": {"type": "direct_copy"}
    },
    {
        "source_field": "technical_owner",
        "target_field": "technical_owner",
        "match_type": "direct",
        "confidence_score": 0.87,
        "status": "pending",
        "transformation_rules": {"type": "email_validation"}
    },
    {
        "source_field": "criticality",
        "target_field": "business_criticality",
        "match_type": "semantic",
        "confidence_score": 0.85,
        "status": "suggested",
        "transformation_rules": {"type": "enum_validation", "valid_values": ["Low", "Medium", "High", "Critical"]}
    },
    {
        "source_field": "current_monthly_cost",
        "target_field": "current_monthly_cost",
        "match_type": "direct",
        "confidence_score": 0.92,
        "status": "approved",
        "transformation_rules": {"type": "currency_conversion", "target_currency": "USD"}
    }
]

JSON_APPLICATION_MAPPINGS = [
    {
        "source_field": "application_name",
        "target_field": "name",
        "match_type": "direct",
        "confidence_score": 0.96,
        "status": "approved",
        "transformation_rules": {"type": "direct_copy"}
    },
    {
        "source_field": "application_name",
        "target_field": "application_name",
        "match_type": "direct",
        "confidence_score": 0.98,
        "status": "approved",
        "transformation_rules": {"type": "direct_copy"}
    },
    {
        "source_field": "application_type",
        "target_field": "description",
        "match_type": "semantic",
        "confidence_score": 0.75,
        "status": "suggested",
        "transformation_rules": {"type": "text_template", "template": "Application Type: {value}"}
    },
    {
        "source_field": "technology_stack",
        "target_field": "technology_stack",
        "match_type": "direct",
        "confidence_score": 0.94,
        "status": "approved",
        "transformation_rules": {"type": "direct_copy"}
    },
    {
        "source_field": "version",
        "target_field": "custom_attributes",
        "match_type": "nested",
        "confidence_score": 0.82,
        "status": "pending",
        "transformation_rules": {"type": "json_append", "key": "version"}
    },
    {
        "source_field": "environment",
        "target_field": "environment",
        "match_type": "direct",
        "confidence_score": 0.97,
        "status": "approved",
        "transformation_rules": {"type": "enum_validation", "valid_values": ["Production", "Development", "Testing"]}
    },
    {
        "source_field": "business_owner",
        "target_field": "business_owner",
        "match_type": "direct",
        "confidence_score": 0.91,
        "status": "approved",
        "transformation_rules": {"type": "email_validation"}
    },
    {
        "source_field": "technical_owner",
        "target_field": "technical_owner",
        "match_type": "direct",
        "confidence_score": 0.89,
        "status": "approved",
        "transformation_rules": {"type": "email_validation"}
    },
    {
        "source_field": "criticality",
        "target_field": "business_criticality",
        "match_type": "direct",
        "confidence_score": 0.93,
        "status": "approved",
        "transformation_rules": {"type": "enum_validation", "valid_values": ["Low", "Medium", "High", "Critical"]}
    },
    {
        "source_field": "port",
        "target_field": "custom_attributes",
        "match_type": "nested",
        "confidence_score": 0.78,
        "status": "rejected",
        "transformation_rules": {"type": "json_append", "key": "port"}
    },
    {
        "source_field": "url",
        "target_field": "custom_attributes",
        "match_type": "nested",
        "confidence_score": 0.86,
        "status": "pending",
        "transformation_rules": {"type": "json_append", "key": "service_url"}
    },
    {
        "source_field": "estimated_users",
        "target_field": "custom_attributes",
        "match_type": "nested",
        "confidence_score": 0.84,
        "status": "suggested",
        "transformation_rules": {"type": "json_append", "key": "user_count"}
    }
]

EXCEL_DEPENDENCY_MAPPINGS = [
    {
        "source_field": "asset_name",
        "target_field": "name",
        "match_type": "direct",
        "confidence_score": 0.95,
        "status": "approved",
        "transformation_rules": {"type": "direct_copy"}
    },
    {
        "source_field": "asset_type",
        "target_field": "asset_type",
        "match_type": "direct",
        "confidence_score": 0.92,
        "status": "approved",
        "transformation_rules": {"type": "enum_validation", "valid_values": ["database", "network", "load_balancer", "application", "server"]}
    },
    {
        "source_field": "environment",
        "target_field": "environment",
        "match_type": "direct",
        "confidence_score": 0.96,
        "status": "approved",
        "transformation_rules": {"type": "enum_validation", "valid_values": ["Production", "Development", "Testing"]}
    },
    {
        "source_field": "criticality",
        "target_field": "business_criticality",
        "match_type": "direct",
        "confidence_score": 0.90,
        "status": "approved",
        "transformation_rules": {"type": "enum_validation", "valid_values": ["Low", "Medium", "High", "Critical"]}
    },
    {
        "source_field": "database_type",
        "target_field": "custom_attributes",
        "match_type": "nested",
        "confidence_score": 0.88,
        "status": "approved",
        "transformation_rules": {"type": "json_append", "key": "database_type"}
    },
    {
        "source_field": "database_version",
        "target_field": "custom_attributes",
        "match_type": "nested",
        "confidence_score": 0.85,
        "status": "pending",
        "transformation_rules": {"type": "json_append", "key": "database_version"}
    },
    {
        "source_field": "device_type",
        "target_field": "description",
        "match_type": "semantic",
        "confidence_score": 0.80,
        "status": "suggested",
        "transformation_rules": {"type": "text_template", "template": "Network Device Type: {value}"}
    },
    {
        "source_field": "management_ip",
        "target_field": "ip_address",
        "match_type": "semantic",
        "confidence_score": 0.87,
        "status": "pending",
        "transformation_rules": {"type": "direct_copy", "validation": "ipv4"}
    },
    {
        "source_field": "depends_on_asset",
        "target_field": "dependencies",
        "match_type": "semantic",
        "confidence_score": 0.83,
        "status": "suggested",
        "transformation_rules": {"type": "dependency_reference", "reference_type": "asset_name"}
    },
    {
        "source_field": "dependency_type",
        "target_field": "custom_attributes",
        "match_type": "nested",
        "confidence_score": 0.81,
        "status": "suggested",
        "transformation_rules": {"type": "json_append", "key": "dependency_type"}
    },
    {
        "source_field": "cpu_cores",
        "target_field": "cpu_cores",
        "match_type": "direct",
        "confidence_score": 0.94,
        "status": "approved",
        "transformation_rules": {"type": "integer_conversion"}
    },
    {
        "source_field": "memory_gb",
        "target_field": "memory_gb",
        "match_type": "direct",
        "confidence_score": 0.93,
        "status": "approved",
        "transformation_rules": {"type": "float_conversion"}
    }
]

async def create_field_mappings():
    """Create field mappings for all three data imports."""
    print("🗂️ Creating field mappings...")
    
    async with AsyncSessionLocal() as session:
        csv_import_id = IMPORT_IDS["csv_servers"]
        json_import_id = IMPORT_IDS["json_applications"]
        excel_import_id = IMPORT_IDS["excel_dependencies"]
        
        # Create CSV server mappings
        print("  📄 Creating CSV server field mappings...")
        csv_mappings = []
        for mapping_data in CSV_SERVER_MAPPINGS:
            mapping = ImportFieldMapping(
                data_import_id=csv_import_id,
                client_account_id=DEMO_CLIENT_ID,
                source_field=mapping_data["source_field"],
                target_field=mapping_data["target_field"],
                match_type=mapping_data["match_type"],
                confidence_score=mapping_data["confidence_score"],
                status=mapping_data["status"],
                suggested_by="ai_field_mapper_v2.1",
                approved_by="analyst@democorp.com" if mapping_data["status"] == "approved" else None,
                approved_at=datetime.now(timezone.utc) if mapping_data["status"] == "approved" else None,
                transformation_rules=mapping_data["transformation_rules"]
            )
            csv_mappings.append(mapping)
        
        session.add_all(csv_mappings)
        print(f"    ✅ Created {len(csv_mappings)} CSV field mappings")
        
        # Create JSON application mappings
        print("  📄 Creating JSON application field mappings...")
        json_mappings = []
        for mapping_data in JSON_APPLICATION_MAPPINGS:
            mapping = ImportFieldMapping(
                data_import_id=json_import_id,
                client_account_id=DEMO_CLIENT_ID,
                source_field=mapping_data["source_field"],
                target_field=mapping_data["target_field"],
                match_type=mapping_data["match_type"],
                confidence_score=mapping_data["confidence_score"],
                status=mapping_data["status"],
                suggested_by="ai_field_mapper_v2.1",
                approved_by="analyst@democorp.com" if mapping_data["status"] == "approved" else None,
                approved_at=datetime.now(timezone.utc) if mapping_data["status"] == "approved" else None,
                transformation_rules=mapping_data["transformation_rules"]
            )
            json_mappings.append(mapping)
        
        session.add_all(json_mappings)
        print(f"    ✅ Created {len(json_mappings)} JSON field mappings")
        
        # Create Excel dependency mappings
        print("  📄 Creating Excel dependency field mappings...")
        excel_mappings = []
        for mapping_data in EXCEL_DEPENDENCY_MAPPINGS:
            mapping = ImportFieldMapping(
                data_import_id=excel_import_id,
                client_account_id=DEMO_CLIENT_ID,
                source_field=mapping_data["source_field"],
                target_field=mapping_data["target_field"],
                match_type=mapping_data["match_type"],
                confidence_score=mapping_data["confidence_score"],
                status=mapping_data["status"],
                suggested_by="ai_field_mapper_v2.1",
                approved_by="analyst@democorp.com" if mapping_data["status"] == "approved" else None,
                approved_at=datetime.now(timezone.utc) if mapping_data["status"] == "approved" else None,
                transformation_rules=mapping_data["transformation_rules"]
            )
            excel_mappings.append(mapping)
        
        session.add_all(excel_mappings)
        print(f"    ✅ Created {len(excel_mappings)} Excel field mappings")
        
        # Commit all mappings
        await session.commit()
        
        # Summary statistics
        total_mappings = len(csv_mappings) + len(json_mappings) + len(excel_mappings)
        
        # Count by status across all mappings
        all_mappings = CSV_SERVER_MAPPINGS + JSON_APPLICATION_MAPPINGS + EXCEL_DEPENDENCY_MAPPINGS
        status_counts = {}
        confidence_scores = []
        
        for mapping in all_mappings:
            status = mapping["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            confidence_scores.append(mapping["confidence_score"])
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        print(f"\n✅ Field mappings created successfully!")
        print(f"   📊 Total Mappings: {total_mappings}")
        print(f"   ✅ Approved: {status_counts.get('approved', 0)}")
        print(f"   ⏳ Pending: {status_counts.get('pending', 0)}")
        print(f"   💡 Suggested: {status_counts.get('suggested', 0)}")
        print(f"   ❌ Rejected: {status_counts.get('rejected', 0)}")
        print(f"   🎯 Average Confidence: {avg_confidence:.2f}")
        print(f"   📄 CSV Mappings: {len(csv_mappings)}")
        print(f"   📄 JSON Mappings: {len(json_mappings)}")
        print(f"   📄 Excel Mappings: {len(excel_mappings)}")

if __name__ == "__main__":
    asyncio.run(create_field_mappings())