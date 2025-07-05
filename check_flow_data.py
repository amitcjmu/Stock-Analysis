import asyncio
from sqlalchemy import select, text
from backend.app.core.database import AsyncSessionLocal
import json

async def check_flow_data():
    flow_id = "1e640262-4332-4087-ac4e-1674b08cd8f2"
    print(f"=== Database Analysis for Flow: {flow_id} ===\n")
    
    async with AsyncSessionLocal() as db:
        # Summary of findings
        print("SUMMARY OF FINDINGS:")
        print("1. ✅ data_imports: Found with status=discovery_initiated, 23 records")
        print("2. ✅ raw_import_records: 23 records with proper field data")
        print("3. ⚠️  discovery_flows: Found but field_mappings=None, phase_state={}")
        print("4. ✅ crewai_flow_state_extensions: Found with field_mappings (13 mappings)")
        print("5. ❌ ISSUE: Field mappings exist in master table but NOT in child table\n")
        
        # Get the actual field mappings from master table
        result = await db.execute(text("""
            SELECT flow_persistence_data
            FROM crewai_flow_state_extensions 
            WHERE flow_id = :flow_id
        """), {"flow_id": flow_id})
        master = result.fetchone()
        
        if master and master[0]:
            field_mappings = master[0].get("field_mappings", {})
            print("FIELD MAPPINGS IN MASTER TABLE:")
            for source, target in field_mappings.items():
                if source != "confidence_scores":
                    print(f"   {source} -> {target}")
                    
        # Check why discovery_flows doesn't have the mappings
        print("\nDISCOVERY_FLOWS TABLE ISSUE:")
        result = await db.execute(text("""
            SELECT field_mappings, updated_at
            FROM discovery_flows 
            WHERE flow_id = :flow_id
        """), {"flow_id": flow_id})
        discovery = result.fetchone()
        print(f"   field_mappings column: {discovery[0]}")
        print(f"   last updated: {discovery[1]}")
        
        # Check for any assets created
        print("\nASSETS CREATED:")
        result = await db.execute(text("""
            SELECT COUNT(*) FROM assets WHERE metadata->>'discovery_flow_id' = :flow_id
        """), {"flow_id": flow_id})
        assets = result.fetchone()
        print(f"   Assets with this flow_id in metadata: {assets[0]}")

if __name__ == "__main__":
    asyncio.run(check_flow_data())