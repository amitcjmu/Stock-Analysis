#!/usr/bin/env python3
"""
Comprehensive investigation script for Discovery Flow ID: 582b87c4-0df1-4c2f-aa3b-e4b5a287d725
This script checks the current status across all relevant tables to identify any issues.
"""

import asyncio
import json
import os

# Add parent directory to Python path
import sys
from datetime import datetime

from sqlalchemy import select, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.data_import.core import DataImport, RawImportRecord
from app.models.discovery_flow import DiscoveryFlow


async def investigate_flow(flow_id: str):
    """Investigate the discovery flow and generate a comprehensive report."""
    
    print(f"\n{'='*80}")
    print(f"DISCOVERY FLOW INVESTIGATION: {flow_id}")
    print(f"Investigation Time: {datetime.utcnow().isoformat()}")
    print(f"{'='*80}\n")
    
    async with AsyncSessionLocal() as session:
        # 1. Check Discovery Flow Table
        print("1. DISCOVERY FLOW STATUS")
        print("-" * 40)
        
        discovery_flow = await session.get(DiscoveryFlow, flow_id)
        if discovery_flow:
            print(f"  Flow ID: {discovery_flow.id}")
            print(f"  Client Account ID: {discovery_flow.client_account_id}")
            print(f"  Engagement ID: {discovery_flow.engagement_id}")
            print(f"  User ID: {discovery_flow.user_id}")
            print(f"  Current Phase: {discovery_flow.current_phase}")
            print(f"  Progress Percentage: {discovery_flow.progress_percentage}%")
            print(f"  Status: {discovery_flow.status}")
            print(f"  Master Flow ID: {discovery_flow.master_flow_id}")
            print(f"  Created At: {discovery_flow.created_at}")
            print(f"  Updated At: {discovery_flow.updated_at}")
            
            # Show phase completion status
            print("\n  Phase Completion Status:")
            print(f"    - Data Import: {discovery_flow.data_import_completed}")
            print(f"    - Field Mapping: {discovery_flow.field_mapping_completed}")
            print(f"    - Data Cleansing: {discovery_flow.data_cleansing_completed}")
            print(f"    - Asset Inventory: {discovery_flow.asset_inventory_completed}")
            print(f"    - Dependency Analysis: {discovery_flow.dependency_analysis_completed}")
            print(f"    - Tech Debt Assessment: {discovery_flow.tech_debt_assessment_completed}")
            
            if discovery_flow.phase_state:
                print("\n  Phase State:")
                print(json.dumps(discovery_flow.phase_state, indent=4))
            
            if discovery_flow.agent_state:
                print("\n  Agent State:")
                print(json.dumps(discovery_flow.agent_state, indent=4))
        else:
            print("  ❌ Discovery flow not found!")
            return
        
        # 2. Check CrewAI Flow State Extensions
        print("\n\n2. CREWAI FLOW STATE EXTENSIONS")
        print("-" * 40)
        
        crewai_state = await session.execute(
            select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == flow_id
            )
        )
        crewai_state = crewai_state.scalar_one_or_none()
        
        if crewai_state:
            print(f"  Extension ID: {crewai_state.id}")
            print(f"  Flow ID: {crewai_state.flow_id}")
            print(f"  Flow Type: {crewai_state.flow_type}")
            print(f"  Master Flow ID: {crewai_state.master_flow_id}")
            print(f"  State Version: {crewai_state.state_version}")
            print(f"  Created At: {crewai_state.created_at}")
            print(f"  Updated At: {crewai_state.updated_at}")
            print(f"  Is Active: {crewai_state.is_active}")
            
            if crewai_state.execution_state:
                print("\n  Execution State:")
                print(json.dumps(crewai_state.execution_state, indent=4))
        else:
            print("  ❌ CrewAI flow state extension not found!")
        
        # 3. Check Unified Discovery Flow State - SKIPPED (table doesn't exist)
        print("\n\n3. UNIFIED DISCOVERY FLOW STATE")
        print("-" * 40)
        print("  ⚠️  Skipped - unified_discovery_flow_state table doesn't exist")
        
        # 4. Check Data Imports
        print("\n\n4. DATA IMPORTS")
        print("-" * 40)
        
        # Check data imports via master flow ID
        data_imports = await session.execute(
            select(DataImport).where(
                DataImport.master_flow_id == discovery_flow.master_flow_id
            )
        )
        data_imports = data_imports.scalars().all()
        
        if data_imports:
            print(f"  Found {len(data_imports)} data import(s):")
            for di in data_imports:
                print(f"\n  Import ID: {di.id}")
                print(f"    Client Account ID: {di.client_account_id}")
                print(f"    Status: {di.status}")
                print(f"    Import Type: {di.import_type}")
                print(f"    Processing Started: {di.processing_started_at}")
                print(f"    Processing Completed: {di.processing_completed_at}")
                print(f"    Total Records: {di.total_records}")
                print(f"    Processed Records: {di.processed_records}")
                print(f"    Created At: {di.created_at}")
                
                if di.field_mapping_config:
                    print(f"    Field Mapping Config: {json.dumps(di.field_mapping_config, indent=6)}")
        else:
            print("  ❌ No data imports found for this flow!")
        
        # 5. Check Raw Import Records
        print("\n\n5. RAW IMPORT RECORDS")
        print("-" * 40)
        
        if data_imports:
            for di in data_imports:
                raw_records_count = await session.execute(
                    select(text("COUNT(*)")).select_from(RawImportRecord).where(
                        RawImportRecord.data_import_id == di.id
                    )
                )
                count = raw_records_count.scalar()
                print(f"  Data Import {di.id}: {count} raw records")
                
                # Show a sample record
                if count > 0:
                    sample_record = await session.execute(
                        select(RawImportRecord).where(
                            RawImportRecord.data_import_id == di.id
                        ).limit(1)
                    )
                    sample = sample_record.scalar_one_or_none()
                    if sample:
                        print(f"    Sample Record ID: {sample.id}")
                        print(f"    Raw Data: {json.dumps(sample.raw_data, indent=6)}")
        else:
            print("  ⚠️  No data imports to check for raw records")
        
        # 6. Check Assets
        print("\n\n6. ASSETS")
        print("-" * 40)
        
        assets = await session.execute(
            select(Asset).where(
                Asset.discovery_flow_id == flow_id
            )
        )
        assets = assets.scalars().all()
        
        if assets:
            print(f"  Found {len(assets)} asset(s):")
            for asset in assets[:5]:  # Show first 5 assets
                print(f"\n  Asset ID: {asset.id}")
                print(f"    Name: {asset.asset_name}")
                print(f"    Type: {asset.asset_type}")
                print(f"    Status: {asset.status}")
                print(f"    Created At: {asset.created_at}")
            
            if len(assets) > 5:
                print(f"\n  ... and {len(assets) - 5} more assets")
        else:
            print("  ❌ No assets found for this flow!")
        
        # 7. Check Master Flow Reference
        print("\n\n7. MASTER FLOW REFERENCE")
        print("-" * 40)
        
        if discovery_flow.master_flow_id:
            master_flow = await session.execute(
                select(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.id == discovery_flow.master_flow_id,
                    CrewAIFlowStateExtensions.flow_type == "master"
                )
            )
            master_flow = master_flow.scalar_one_or_none()
            
            if master_flow:
                print(f"  Master Flow ID: {master_flow.id}")
                print(f"  Master Flow Type: {master_flow.flow_type}")
                print(f"  Is Active: {master_flow.is_active}")
                print(f"  Created At: {master_flow.created_at}")
            else:
                print("  ❌ Master flow reference not found in CrewAI extensions!")
        else:
            print("  ⚠️  No master flow ID set on discovery flow")
        
        # 8. Potential Issues Summary
        print("\n\n8. POTENTIAL ISSUES SUMMARY")
        print("-" * 40)
        
        issues = []
        
        # Check for common issues
        if discovery_flow.status != "completed" and discovery_flow.status != "in_progress":
            issues.append(f"Flow status is '{discovery_flow.status}' - may not appear in active flows")
        
        if discovery_flow.progress_percentage == 0:
            issues.append("Progress is 0% - flow may not have started properly")
        
        if not crewai_state:
            issues.append("Missing CrewAI flow state extension - flow orchestration may be broken")
        elif not crewai_state.is_active:
            issues.append("CrewAI flow state is inactive - flow won't appear in active flows")
        
        if not discovery_flow.master_flow_id:
            issues.append("No master flow ID - flow may not be properly linked to master orchestration")
        
        if not data_imports:
            issues.append("No data imports found - data import phase may have failed")
        
        if not assets:
            issues.append("No assets created - asset creation phase may not have completed")
        
        if discovery_flow.current_phase == "data_import" and discovery_flow.progress_percentage > 0:
            issues.append("Flow stuck in data_import phase despite having progress")
        
        if issues:
            print("  Found the following issues:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. ❌ {issue}")
        else:
            print("  ✅ No obvious issues found")
        
        # 9. Recommendations
        print("\n\n9. RECOMMENDATIONS")
        print("-" * 40)
        
        if issues:
            print("  Based on the issues found, consider:")
            
            if "CrewAI flow state is inactive" in str(issues):
                print("  • Check why the flow was marked inactive")
                print("  • Review flow execution logs for errors")
            
            if "No master flow ID" in str(issues):
                print("  • Ensure discovery flows are created through master flow orchestration")
                print("  • Check if master flow creation failed")
            
            if "No data imports found" in str(issues):
                print("  • Review data import phase execution")
                print("  • Check if CSV upload completed successfully")
            
            if "Flow stuck in data_import phase" in str(issues):
                print("  • Check field mapping executor logs")
                print("  • Verify if the flow is waiting for user input")
                print("  • Review any async task failures")
        else:
            print("  • Flow appears to be properly configured")
            print("  • Check frontend filtering logic if flow is not visible")
            print("  • Review any client-side caching issues")


async def main():
    """Main function to run the investigation."""
    # The actual discovery flow ID
    flow_id = "89c97ed2-030c-4d13-a314-342f4a2db41e"
    
    try:
        await investigate_flow(flow_id)
    except Exception as e:
        print(f"\n❌ Investigation failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())