#!/usr/bin/env python3
"""
Manual Asset Creation from Raw Import Records
This script bridges the gap between data cleansing and asset creation by:
1. Reading raw import records from the database
2. Applying field mappings to transform the data
3. Creating assets in the database
4. Marking raw records as processed
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def main():
    try:
        from sqlalchemy import select, update

        from app.core.database import AsyncSessionLocal
        from app.models.asset import Asset, AssetStatus
        from app.models.data_import import RawImportRecord
        from app.models.data_import.mapping import ImportFieldMapping
        
        print("🚀 Starting Manual Asset Creation from Raw Import Records...")
        
        async with AsyncSessionLocal() as session:
            # 1. Get unprocessed raw records
            raw_query = select(RawImportRecord).where(
                RawImportRecord.client_account_id == "73dee5f1-6a01-43e3-b1b8-dbe6c66f2990",
                RawImportRecord.is_processed == False
            )
            
            result = await session.execute(raw_query)
            raw_records = result.scalars().all()
            
            print(f"📊 Found {len(raw_records)} unprocessed raw records")
            
            if not raw_records:
                print("❌ No unprocessed raw records found")
                return
            
            # 2. Get approved field mappings
            mapping_query = select(ImportFieldMapping).where(
                ImportFieldMapping.status == "approved"
            )
            mapping_result = await session.execute(mapping_query)
            mappings = mapping_result.scalars().all()
            
            field_mappings = {}
            for mapping in mappings:
                field_mappings[mapping.source_field] = mapping.target_field
            
            print(f"🗺️ Using {len(field_mappings)} approved field mappings")
            
            # 3. Process each raw record into an asset
            assets_created = 0
            records_processed = 0
            
            for record in raw_records:
                try:
                    raw_data = record.raw_data
                    print(f"🔄 Processing record {record.row_number}: {raw_data.get('Asset_Name', 'Unknown')}")
                    
                    # Apply field mappings
                    mapped_data = apply_field_mappings(raw_data, field_mappings)
                    
                    # Create asset
                    asset = Asset(
                        # Multi-tenant isolation
                        client_account_id=record.client_account_id,
                        engagement_id=record.engagement_id,
                        
                        # Core identification
                        name=extract_asset_name(mapped_data, raw_data, record.row_number),
                        asset_name=mapped_data.get("asset_name") or raw_data.get("Asset_Name"),
                        hostname=mapped_data.get("hostname") or raw_data.get("Hostname"),
                        asset_type=determine_asset_type(mapped_data, raw_data),
                        
                        # Technical details
                        ip_address=mapped_data.get("ip_address") or raw_data.get("IP_Address"),
                        operating_system=mapped_data.get("operating_system") or raw_data.get("Operating_System"),
                        os_version=mapped_data.get("os_version") or raw_data.get("OS_Version"),
                        cpu_cores=safe_int(mapped_data.get("cpu_cores") or raw_data.get("CPU_Cores")),
                        memory_gb=safe_float(mapped_data.get("memory_gb") or raw_data.get("RAM_GB")),
                        storage_gb=safe_float(mapped_data.get("storage_gb") or raw_data.get("Storage_GB")),
                        
                        # Hardware details
                        manufacturer=mapped_data.get("manufacturer") or raw_data.get("Manufacturer"),
                        model=mapped_data.get("model") or raw_data.get("Model"),
                        serial_number=mapped_data.get("serial_number") or raw_data.get("Serial_Number"),
                        
                        # Environment and business info
                        environment=mapped_data.get("environment") or raw_data.get("DR_Tier", "Unknown"),
                        location=mapped_data.get("location") or raw_data.get("Location_DataCenter"),
                        business_owner=mapped_data.get("business_owner") or raw_data.get("Application_Owner"),
                        department=mapped_data.get("department") or raw_data.get("Application_Owner"),
                        criticality=determine_criticality(raw_data),
                        
                        # Migration assessment
                        status=AssetStatus.DISCOVERED,
                        migration_complexity="Medium",
                        migration_priority=determine_migration_priority(raw_data),
                        
                        # Discovery metadata
                        discovery_source="Manual Asset Creation Script",
                        discovery_method="raw_record_processing",
                        discovery_timestamp=datetime.utcnow(),
                        
                        # Data preservation
                        raw_data=raw_data,
                        field_mappings_used=field_mappings,
                        custom_attributes={
                            "import_session_id": str(record.data_import_id),
                            "raw_record_id": str(record.id),
                            "processing_method": "manual_script",
                            "migration_readiness_score": raw_data.get("Cloud_Migration_Readiness_Score", "Unknown")
                        },
                        
                        # Audit
                        imported_by=uuid.UUID("44444444-4444-4444-4444-444444444444"),  # Script user
                        imported_at=datetime.utcnow(),
                        is_mock=False
                    )
                    
                    session.add(asset)
                    await session.flush()
                    
                    # Update raw record
                    record.asset_id = asset.id
                    record.is_processed = True
                    record.processed_at = datetime.utcnow()
                    record.processing_notes = "Processed by manual asset creation script"
                    
                    assets_created += 1
                    records_processed += 1
                    
                    print(f"✅ Created asset {asset.id}: {asset.name} ({asset.asset_type})")
                    
                except Exception as e:
                    print(f"❌ Error processing record {record.id}: {e}")
                    continue
            
            # Commit all changes
            await session.commit()
            
            print("🎉 Asset creation completed:")
            print(f"   - Assets created: {assets_created}")
            print(f"   - Records processed: {records_processed}")
            
            # Verify the assets were created
            asset_query = select(Asset).where(
                Asset.client_account_id == "73dee5f1-6a01-43e3-b1b8-dbe6c66f2990"
            )
            asset_result = await session.execute(asset_query)
            all_assets = asset_result.scalars().all()
            
            print(f"🔍 Verification: Total assets in database: {len(all_assets)}")
            for asset in all_assets[-assets_created:]:  # Show newly created ones
                print(f"   - {asset.name} ({asset.asset_type}) - {asset.environment} - {asset.discovery_method}")
            
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

def apply_field_mappings(raw_data: Dict[str, Any], field_mappings: Dict[str, str]) -> Dict[str, Any]:
    """Apply field mappings to transform raw data"""
    mapped_data = {}
    
    for source_field, target_field in field_mappings.items():
        if source_field in raw_data:
            # Normalize target field name
            normalized_target = target_field.lower().replace(" ", "_").replace("-", "_")
            mapped_data[normalized_target] = raw_data[source_field]
    
    return mapped_data

def extract_asset_name(mapped_data: Dict[str, Any], raw_data: Dict[str, Any], row_number: int) -> str:
    """Extract the best asset name from available data"""
    # Try mapped data first
    if mapped_data.get("asset_name"):
        return str(mapped_data["asset_name"])
    if mapped_data.get("hostname"):
        return str(mapped_data["hostname"])
    if mapped_data.get("name"):
        return str(mapped_data["name"])
    
    # Fallback to raw data
    if raw_data.get("Asset_Name"):
        return str(raw_data["Asset_Name"])
    if raw_data.get("Hostname"):
        return str(raw_data["Hostname"])
    if raw_data.get("NAME"):
        return str(raw_data["NAME"])
    
    # Final fallback
    return f"Asset_{row_number}"

def determine_asset_type(mapped_data: Dict[str, Any], raw_data: Dict[str, Any]) -> str:
    """Determine asset type from available data"""
    # Check mapped data first
    asset_type = mapped_data.get("asset_type") or raw_data.get("Asset_Type") or raw_data.get("TYPE")
    
    if asset_type:
        asset_type_str = str(asset_type).upper()
        # Map common types
        if "SERVER" in asset_type_str or "SRV" in asset_type_str:
            return "SERVER"
        elif "DATABASE" in asset_type_str or "DB" in asset_type_str:
            return "DATABASE"
        elif "NETWORK" in asset_type_str or "NET" in asset_type_str:
            return "NETWORK"
        elif "STORAGE" in asset_type_str:
            return "STORAGE"
        elif "APPLICATION" in asset_type_str or "APP" in asset_type_str:
            return "APPLICATION"
        elif "VIRTUAL" in asset_type_str or "VM" in asset_type_str:
            return "VIRTUAL_MACHINE"
    
    # Default fallback
    return "SERVER"

def determine_criticality(raw_data: Dict[str, Any]) -> str:
    """Determine business criticality from raw data"""
    dr_tier = raw_data.get("DR_Tier", "")
    if "Tier 1" in str(dr_tier):
        return "High"
    elif "Tier 2" in str(dr_tier):
        return "Medium"
    elif "Tier 3" in str(dr_tier):
        return "Low"
    return "Medium"

def determine_migration_priority(raw_data: Dict[str, Any]) -> int:
    """Determine migration priority from raw data"""
    readiness_score = raw_data.get("Cloud_Migration_Readiness_Score", "3")
    try:
        score = int(readiness_score)
        if score >= 8:
            return 1  # High priority
        elif score >= 5:
            return 3  # Medium priority
        else:
            return 5  # Low priority
    except (ValueError, TypeError):
        return 3  # Default medium priority

def safe_int(value) -> Optional[int]:
    """Safely convert value to integer"""
    if value is None:
        return None
    try:
        return int(float(str(value)))
    except (ValueError, TypeError):
        return None

def safe_float(value) -> Optional[float]:
    """Safely convert value to float"""
    if value is None:
        return None
    try:
        return float(str(value))
    except (ValueError, TypeError):
        return None

if __name__ == "__main__":
    asyncio.run(main()) 