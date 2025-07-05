#!/usr/bin/env python3
"""
Simple flow analysis script - shows all database locations where flow data is stored
"""

import asyncio
import json
from sqlalchemy import text
from datetime import datetime
import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.core.database import AsyncSessionLocal

async def analyze_flow():
    flow_id = "1e640262-4332-4087-ac4e-1674b08cd8f2"
    print(f"\n=== Database Analysis for Flow: {flow_id} ===\n")
    
    async with AsyncSessionLocal() as db:
        # 1. Check ALL tables for this flow ID
        print("STEP 1: Scanning ALL database tables for flow ID...\n")
        
        # Get all table names
        result = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        all_tables = [row[0] for row in result.fetchall()]
        
        tables_found = []
        
        for table_name in all_tables:
            try:
                # Get column names for this table
                col_result = await db.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                """))
                columns = [row[0] for row in col_result.fetchall()]
                
                # Build query based on available columns
                where_clauses = []
                params = {"flow_id": flow_id}
                
                # Check direct flow_id columns
                for col in ['flow_id', 'discovery_flow_id', 'crewai_flow_id']:
                    if col in columns:
                        where_clauses.append(f"{col}::text = :flow_id")
                
                # Check JSONB columns that might contain flow_id
                jsonb_cols = [col for col in columns if any(word in col for word in ['state', 'data', 'metadata', 'configuration', 'persistence'])]
                for col in jsonb_cols:
                    where_clauses.append(f"{col}::text LIKE :flow_id_pattern")
                    params["flow_id_pattern"] = f"%{flow_id}%"
                
                if where_clauses:
                    query = f"SELECT COUNT(*) FROM {table_name} WHERE {' OR '.join(where_clauses)}"
                    result = await db.execute(text(query), params)
                    count = result.scalar()
                    
                    if count > 0:
                        # Get sample data
                        sample_query = f"SELECT * FROM {table_name} WHERE {' OR '.join(where_clauses)} LIMIT 1"
                        sample_result = await db.execute(text(sample_query), params)
                        sample = sample_result.fetchone()
                        
                        tables_found.append({
                            "table": table_name,
                            "count": count,
                            "columns": columns
                        })
                        
                        print(f"✅ Found in {table_name}: {count} records")
                        print(f"   Columns: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
                        
            except Exception as e:
                pass  # Skip tables that can't be queried
        
        print(f"\n📊 Flow data found in {len(tables_found)} tables\n")
        
        # 2. Detailed analysis of key tables
        print("\nSTEP 2: Detailed Analysis of Key Tables\n")
        
        # Check discovery_flows
        print("DISCOVERY_FLOWS TABLE:")
        result = await db.execute(text("""
            SELECT flow_id, status, current_phase, progress_percentage,
                   data_import_completed, field_mapping_completed,
                   data_cleansing_completed, asset_inventory_completed,
                   field_mappings, created_at, updated_at
            FROM discovery_flows 
            WHERE flow_id = :flow_id
        """), {"flow_id": flow_id})
        discovery = result.fetchone()
        
        if discovery:
            print(f"  Status: {discovery[1]}")
            print(f"  Current Phase: {discovery[2]}")
            print(f"  Progress: {discovery[3]}%")
            print(f"  Phases Completed:")
            print(f"    - Data Import: {discovery[4]}")
            print(f"    - Field Mapping: {discovery[5]}")
            print(f"    - Data Cleansing: {discovery[6]}")
            print(f"    - Asset Inventory: {discovery[7]}")
            print(f"  Field Mappings: {'Yes' if discovery[8] else 'No'}")
            print(f"  Created: {discovery[9]}")
            print(f"  Updated: {discovery[10]}")
        else:
            print("  ❌ Not found")
        
        # Check data_imports
        print("\n\nDATA_IMPORTS TABLE:")
        result = await db.execute(text("""
            SELECT id, status, created_at
            FROM data_imports 
            WHERE master_flow_id = :flow_id
        """), {"flow_id": flow_id})
        data_imports = result.fetchall()
        
        if data_imports:
            for imp in data_imports:
                print(f"  Import ID: {imp[0]}")
                print(f"  Status: {imp[1]}")
                print(f"  Created: {imp[2]}")
                
                # Count raw records
                raw_count = await db.execute(text("""
                    SELECT COUNT(*) FROM raw_import_records 
                    WHERE data_import_id = :import_id
                """), {"import_id": imp[0]})
                print(f"  Raw Records in DB: {raw_count.scalar()}")
        else:
            print("  ❌ No data imports found")
        
        # Check crewai_flow_state_extensions (master table)
        print("\n\nCREWAI_FLOW_STATE_EXTENSIONS (Master Table):")
        result = await db.execute(text("""
            SELECT flow_id, flow_status, flow_type, 
                   flow_persistence_data->>'field_mappings' as field_mappings,
                   created_at, updated_at
            FROM crewai_flow_state_extensions 
            WHERE flow_id = :flow_id
        """), {"flow_id": flow_id})
        master = result.fetchone()
        
        if master:
            print(f"  Flow Status: {master[1]}")
            print(f"  Flow Type: {master[2]}")
            print(f"  Has Field Mappings: {'Yes' if master[3] else 'No'}")
            print(f"  Created: {master[4]}")
            print(f"  Updated: {master[5]}")
        else:
            print("  ❌ Not found")
        
        # Check unified_discovery_flow_states
        print("\n\nUNIFIED_DISCOVERY_FLOW_STATES:")
        result = await db.execute(text("""
            SELECT COUNT(*) FROM unified_discovery_flow_states 
            WHERE flow_state::text LIKE :flow_id_pattern
        """), {"flow_id_pattern": f"%{flow_id}%"})
        count = result.scalar()
        print(f"  Records containing flow ID: {count}")
        
        # Summary
        print("\n\n=== SUMMARY ===")
        print(f"\n1. Flow exists in {len(tables_found)} tables")
        print("\n2. Data Status:")
        print(f"   - Raw data: {'✅ Available' if data_imports else '❌ Missing'}")
        print(f"   - Field mappings: {'✅ Available' if (discovery and discovery[8]) or (master and master[3]) else '❌ Missing'}")
        print(f"   - Current status: {discovery[1] if discovery else 'Unknown'}")
        
        print("\n3. Key Issues:")
        if discovery and master:
            if discovery[8] and not master[3]:
                print("   - Field mappings in child table but NOT in master")
            elif master[3] and not discovery[8]:
                print("   - Field mappings in master table but NOT in child")
            if discovery[1] == "running" and discovery[5]:
                print("   - Status is 'running' but field mapping marked complete")
        
        print("\n4. Resume Recommendations:")
        if discovery:
            if discovery[1] in ["paused", "waiting_for_approval"]:
                print("   - Flow is waiting for approval - can resume with approval")
            elif not discovery[4] and data_imports:
                print("   - Data exists but import not marked complete - can restart from raw data")
            elif discovery[4] and not discovery[5]:
                print("   - Data import complete - can resume field mapping")

if __name__ == "__main__":
    asyncio.run(analyze_flow())