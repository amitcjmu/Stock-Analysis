#!/usr/bin/env python3
"""
Fix Asset and Field Mapping Master Flow Links

This script fixes the missing master_flow_id population in:
1. Assets table - links assets to their discovery flows
2. ImportFieldMapping table - links field mappings to their flows
"""

import asyncio

from sqlalchemy import text, update

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from app.models.data_import.mapping import ImportFieldMapping


async def fix_asset_master_flow_links():
    """Link assets to their master flows via discovery flows."""
    async with AsyncSessionLocal() as db:
        print("🔍 Fixing asset master flow links...")
        
        # Find assets without master_flow_id that should be linked
        unlinked_assets_query = text("""
            SELECT 
                a.id as asset_id,
                a.engagement_id,
                a.client_account_id,
                a.created_at,
                di.master_flow_id as data_import_master_flow_id,
                df.master_flow_id as discovery_flow_master_flow_id
            FROM assets a
            LEFT JOIN data_imports di ON di.engagement_id = a.engagement_id 
                AND di.client_account_id = a.client_account_id
                AND abs(extract(epoch from (a.created_at - di.created_at))) < 3600  -- Within 1 hour
            LEFT JOIN discovery_flows df ON df.engagement_id = a.engagement_id 
                AND df.client_account_id = a.client_account_id
                AND abs(extract(epoch from (a.created_at - df.created_at))) < 3600  -- Within 1 hour
            WHERE a.master_flow_id IS NULL
            AND (di.master_flow_id IS NOT NULL OR df.master_flow_id IS NOT NULL)
            ORDER BY a.created_at DESC;
        """)
        
        result = await db.execute(unlinked_assets_query)
        unlinked_assets = result.fetchall()
        
        print(f"📊 Found {len(unlinked_assets)} assets to link to master flows")
        
        linked_count = 0
        
        for asset_row in unlinked_assets:
            try:
                # Prefer discovery flow master_flow_id over data import master_flow_id
                master_flow_id = asset_row.discovery_flow_master_flow_id or asset_row.data_import_master_flow_id
                
                if master_flow_id:
                    # Update asset with master flow ID
                    await db.execute(
                        update(Asset)
                        .where(Asset.id == asset_row.asset_id)
                        .values(master_flow_id=master_flow_id)
                    )
                    
                    linked_count += 1
                    print(f"✅ Linked asset {asset_row.asset_id} to master flow {master_flow_id}")
                
            except Exception as e:
                print(f"❌ Error linking asset {asset_row.asset_id}: {e}")
        
        await db.commit()
        print(f"🎉 Successfully linked {linked_count} assets to master flows!")
        
        return linked_count


async def fix_field_mapping_master_flow_links():
    """Link field mappings to their master flows via data imports."""
    async with AsyncSessionLocal() as db:
        print("\n🔍 Fixing field mapping master flow links...")
        
        # Find field mappings without master_flow_id that should be linked
        unlinked_mappings_query = text("""
            SELECT 
                fm.id as mapping_id,
                fm.data_import_id,
                di.engagement_id,
                di.client_account_id,
                di.master_flow_id as data_import_master_flow_id
            FROM import_field_mappings fm
            JOIN data_imports di ON di.id = fm.data_import_id
            WHERE fm.master_flow_id IS NULL
            AND di.master_flow_id IS NOT NULL
            ORDER BY fm.created_at DESC;
        """)
        
        result = await db.execute(unlinked_mappings_query)
        unlinked_mappings = result.fetchall()
        
        print(f"📊 Found {len(unlinked_mappings)} field mappings to link to master flows")
        
        linked_count = 0
        
        for mapping_row in unlinked_mappings:
            try:
                master_flow_id = mapping_row.data_import_master_flow_id
                
                # Update field mapping with master flow ID
                await db.execute(
                    update(ImportFieldMapping)
                    .where(ImportFieldMapping.id == mapping_row.mapping_id)
                    .values(master_flow_id=master_flow_id)
                )
                
                linked_count += 1
                print(f"✅ Linked field mapping {mapping_row.mapping_id} to master flow {master_flow_id}")
                
            except Exception as e:
                print(f"❌ Error linking field mapping {mapping_row.mapping_id}: {e}")
        
        await db.commit()
        print(f"🎉 Successfully linked {linked_count} field mappings to master flows!")
        
        return linked_count


async def validate_master_flow_links():
    """Validate that all master flow links are working properly."""
    async with AsyncSessionLocal() as db:
        print("\n🔍 Validating master flow relationships...")
        
        # Check asset linkage
        asset_stats_query = text("""
            SELECT 
                COUNT(*) as total_assets,
                COUNT(CASE WHEN master_flow_id IS NOT NULL THEN 1 END) as linked_assets,
                COUNT(CASE WHEN master_flow_id IS NULL THEN 1 END) as unlinked_assets
            FROM assets;
        """)
        
        result = await db.execute(asset_stats_query)
        asset_stats = result.fetchone()
        
        # Check field mapping linkage
        mapping_stats_query = text("""
            SELECT 
                COUNT(*) as total_mappings,
                COUNT(CASE WHEN master_flow_id IS NOT NULL THEN 1 END) as linked_mappings,
                COUNT(CASE WHEN master_flow_id IS NULL THEN 1 END) as unlinked_mappings
            FROM import_field_mappings;
        """)
        
        result = await db.execute(mapping_stats_query)
        mapping_stats = result.fetchone()
        
        # Check foreign key validity
        invalid_links_query = text("""
            SELECT 
                'assets' as table_name,
                COUNT(*) as invalid_count
            FROM assets a
            LEFT JOIN crewai_flow_state_extensions cfe ON a.master_flow_id = cfe.flow_id
            WHERE a.master_flow_id IS NOT NULL AND cfe.flow_id IS NULL
            
            UNION ALL
            
            SELECT 
                'import_field_mappings' as table_name,
                COUNT(*) as invalid_count
            FROM import_field_mappings fm
            LEFT JOIN crewai_flow_state_extensions cfe ON fm.master_flow_id = cfe.flow_id
            WHERE fm.master_flow_id IS NOT NULL AND cfe.flow_id IS NULL;
        """)
        
        result = await db.execute(invalid_links_query)
        invalid_links = result.fetchall()
        
        print("📊 Master Flow Linkage Validation Results:")
        print(f"   Assets: {asset_stats.linked_assets}/{asset_stats.total_assets} linked ({(asset_stats.linked_assets/asset_stats.total_assets*100) if asset_stats.total_assets > 0 else 0:.1f}%)")
        print(f"   Field Mappings: {mapping_stats.linked_mappings}/{mapping_stats.total_mappings} linked ({(mapping_stats.linked_mappings/mapping_stats.total_mappings*100) if mapping_stats.total_mappings > 0 else 0:.1f}%)")
        
        for invalid_link in invalid_links:
            if invalid_link.invalid_count > 0:
                print(f"⚠️  {invalid_link.table_name}: {invalid_link.invalid_count} invalid foreign key references")
            else:
                print(f"✅ {invalid_link.table_name}: All foreign key references valid")


async def main():
    """Main execution function."""
    print("🚀 Starting Asset and Field Mapping Master Flow Link Fixes\n")
    
    # Fix asset links
    asset_count = await fix_asset_master_flow_links()
    
    # Fix field mapping links
    mapping_count = await fix_field_mapping_master_flow_links()
    
    # Validate results
    await validate_master_flow_links()
    
    print("\n🎉 Master Flow Link Fix Complete!")
    print(f"   Fixed {asset_count} asset links")
    print(f"   Fixed {mapping_count} field mapping links")
    print(f"   Total fixes: {asset_count + mapping_count}")


if __name__ == "__main__":
    asyncio.run(main())