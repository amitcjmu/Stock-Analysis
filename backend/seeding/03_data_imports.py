"""
Seed data imports with different file types and states.
Agent 2 Task 2.4 - Data imports seeding
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.models.data_import.core import DataImport
from app.models.data_import.enums import ImportStatus, ImportType
from seeding.constants import (
    DEMO_CLIENT_ID, DEMO_ENGAGEMENT_ID, IMPORT_IDS, IMPORTS, 
    USER_IDS, USERS, BASE_TIMESTAMP, FLOW_IDS, FLOWS
)


def generate_sample_data(import_type: str, row_count: int) -> list[dict]:
    """Generate sample data based on import type."""
    if import_type == "ASSET_INVENTORY":
        return [
            {
                "server_id": f"SRV{str(i).zfill(4)}",
                "hostname": f"server{i}.democorp.com",
                "ip_address": f"10.0.{i // 256}.{i % 256}",
                "os": "Windows Server 2019" if i % 2 == 0 else "Red Hat Enterprise Linux 8",
                "cpu_cores": 8 if i % 3 == 0 else 16,
                "memory_gb": 32 if i % 3 == 0 else 64,
                "storage_gb": 500 + (i * 100),
                "environment": ["production", "staging", "development"][i % 3],
                "location": ["us-east-1", "us-west-2", "eu-central-1"][i % 3],
                "business_unit": ["Engineering", "Sales", "Marketing"][i % 3]
            }
            for i in range(1, min(row_count + 1, 10))  # Limit sample data
        ]
    
    elif import_type == "BUSINESS_APPS":
        return [
            {
                "app_id": f"APP{str(i).zfill(4)}",
                "app_name": f"Application_{i}",
                "version": f"{(i % 3) + 1}.{i % 10}.0",
                "technology_stack": ["Java", "Python", ".NET", "Node.js"][i % 4],
                "database": ["PostgreSQL", "MySQL", "Oracle", "MongoDB"][i % 4],
                "criticality": ["High", "Medium", "Low"][i % 3],
                "users": 100 * (i + 1),
                "business_owner": f"owner{i}@democorp.com",
                "technical_owner": f"tech{i}@democorp.com",
                "compliance": ["SOC2", "HIPAA", "None"][i % 3]
            }
            for i in range(1, min(row_count + 1, 10))
        ]
    
    else:  # NETWORK_DATA
        return [
            {
                "dependency_id": f"DEP{str(i).zfill(4)}",
                "source_app": f"APP{str((i % 10) + 1).zfill(4)}",
                "target_app": f"APP{str(((i + 5) % 10) + 1).zfill(4)}",
                "dependency_type": ["API", "Database", "File Transfer", "Message Queue"][i % 4],
                "protocol": ["REST", "SOAP", "TCP", "AMQP"][i % 4],
                "frequency": ["Real-time", "Hourly", "Daily", "Weekly"][i % 4],
                "data_volume_mb": 10 * (i + 1),
                "criticality": ["Critical", "Important", "Nice-to-have"][i % 3],
                "latency_requirements_ms": [10, 100, 1000, 5000][i % 4]
            }
            for i in range(1, min(row_count + 1, 10))
        ]


def generate_raw_records(sample_data: list[dict], total_rows: int) -> dict:
    """Generate raw records from sample data."""
    raw_records = {}
    
    # Use sample data as template to generate more records
    for i in range(total_rows):
        sample_index = i % len(sample_data)
        record = sample_data[sample_index].copy()
        
        # Modify IDs to make them unique
        for key in record:
            if key.endswith("_id"):
                base_id = record[key].split("_")[0] if "_" in record[key] else record[key][:3]
                record[key] = f"{base_id}{str(i).zfill(4)}"
        
        raw_records[str(i)] = record
    
    return raw_records


async def create_data_imports(db: AsyncSession) -> list[DataImport]:
    """Create data imports with different states."""
    print("Creating data imports...")
    
    # Get CrewAI state extension IDs for the flow_ids
    from sqlalchemy import select
    from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
    
    flow_id_to_crewai_id = {}
    for import_data in IMPORTS:
        result = await db.execute(
            select(CrewAIFlowStateExtensions.id).where(
                CrewAIFlowStateExtensions.flow_id == import_data["flow_id"]
            )
        )
        crewai_id = result.scalar_one_or_none()
        if crewai_id:
            flow_id_to_crewai_id[import_data["flow_id"]] = crewai_id
    
    created_imports = []
    
    for import_data in IMPORTS:
        # Calculate timestamps
        created_at = BASE_TIMESTAMP + timedelta(hours=import_data.get("hour_offset", 0))
        updated_at = created_at + timedelta(minutes=30)
        
        # Generate sample data
        sample_data = generate_sample_data(
            import_data["import_type"], 
            min(import_data["total_rows"], 10)
        )
        
        # Create DataImport
        data_import = DataImport(
            id=import_data["id"],
            master_flow_id=flow_id_to_crewai_id.get(import_data["flow_id"]),
            client_account_id=DEMO_CLIENT_ID,
            engagement_id=DEMO_ENGAGEMENT_ID,
            
            # File information
            filename=import_data["filename"],
            file_size=import_data["total_rows"] * 1024,  # Approximate size
            mime_type=get_mime_type(import_data["file_type"]),
            
            # Import details
            import_name=import_data["filename"],
            import_type=import_data["import_type"],
            status=import_data["status"],
            description=f"Demo data import from {import_data['filename']}",
            
            # Progress tracking
            total_records=import_data["total_rows"],
            processed_records=import_data["processed_rows"],
            failed_records=import_data["failed_rows"],
            progress_percentage=import_data["processed_rows"] / import_data["total_rows"],
            
            # User context
            imported_by=import_data["created_by"],
            
            # Error handling for failed imports
            error_message="Data validation failed" if import_data["failed_rows"] > 0 else None,
            error_details={
                "validation_errors": import_data["failed_rows"],
                "quality_score": 0.95 if import_data["failed_rows"] == 0 else 0.85
            } if import_data["failed_rows"] > 0 else None,
            
            # Timestamps
            started_at=created_at,
            completed_at=updated_at if import_data["status"] in ["completed", "failed"] else None
        )
        
        # Set completion time for completed imports
        if import_data["status"] == "completed":
            data_import.completed_at = updated_at
        
        db.add(data_import)
        created_imports.append(data_import)
        
        print(f"✓ Created import: {import_data['filename']} ({import_data['status']}, {import_data['processed_rows']}/{import_data['total_rows']} rows)")
    
    await db.commit()
    return created_imports


def get_mime_type(file_type: str) -> str:
    """Get MIME type based on file type."""
    mime_types = {
        "csv": "text/csv",
        "json": "application/json",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    return mime_types.get(file_type, "application/octet-stream")


async def generate_seeded_ids_json():
    """Generate SEEDED_IDS.json for Agent 3."""
    seeded_data = {
        "client_account": {
            "id": str(DEMO_CLIENT_ID),
            "name": "DemoCorp International"
        },
        "engagement": {
            "id": str(DEMO_ENGAGEMENT_ID),
            "name": "Cloud Migration Assessment 2024"
        },
        "users": [
            {
                "id": str(user["id"]),
                "email": user["email"],
                "role": user["role"]
            }
            for user in USERS
        ],
        "flows": [
            {
                "id": str(flow["id"]),
                "name": flow["name"],
                "state": flow["state"],
                "progress": flow["progress"],
                "current_phase": flow["current_phase"]
            }
            for flow in FLOWS
        ],
        "imports": [
            {
                "id": str(import_data["id"]),
                "flow_id": str(import_data["flow_id"]),
                "filename": import_data["filename"],
                "type": import_data["import_type"],
                "status": import_data["status"],
                "rows": {
                    "total": import_data["total_rows"],
                    "processed": import_data["processed_rows"],
                    "failed": import_data["failed_rows"]
                }
            }
            for import_data in IMPORTS
        ]
    }
    
    output_path = Path(__file__).parent / "SEEDED_IDS.json"
    with open(output_path, "w") as f:
        json.dump(seeded_data, f, indent=2)
    
    print(f"\n✅ Generated SEEDED_IDS.json with all seeded entity IDs")


async def main():
    """Main seeding function."""
    print("\n=== Seeding Data Imports ===\n")
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if already seeded
            existing_import = await db.get(DataImport, IMPORT_IDS["csv_servers"])
            if existing_import:
                print("⚠️  Data imports already seeded. Skipping...")
                return
            
            # Create imports
            imports = await create_data_imports(db)
            
            print(f"\n✅ Successfully seeded {len(imports)} data imports:")
            for imp in imports:
                print(f"   - {imp.filename} ({imp.status}, {imp.processed_records}/{imp.total_records} rows)")
            
            # Generate SEEDED_IDS.json
            await generate_seeded_ids_json()
            
        except Exception as e:
            print(f"\n❌ Error seeding data imports: {str(e)}")
            await db.rollback()
            raise


if __name__ == "__main__":
    # Add hour offsets to imports for temporal ordering
    for i, import_data in enumerate(IMPORTS):
        import_data["hour_offset"] = i * 2
    
    asyncio.run(main())