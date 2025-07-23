#!/usr/bin/env python3
"""
Fix Engagement Data Association

This script moves uploaded data from the wrong engagement to the correct 
Azure Transformation 2 engagement for Marathon Petroleum.

Issue: Data was uploaded to "Debug Test Engagement" instead of "Azure Transformation 2"
"""

import asyncio
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import uuid

from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.models.data_import.core import DataImport, RawImportRecord


async def fix_engagement_data_association():
    """Move data from Debug Test Engagement to Azure Transformation 2"""
    
    async with AsyncSessionLocal() as session:
        # IDs from investigation
        marathon_client = '73dee5f1-6a01-43e3-b1b8-dbe6c66f2990'
        wrong_engagement = 'baf640df-433c-4bcd-8c8f-7b01c12e9005'  # Debug Test Engagement  
        correct_engagement = '3362a198-c917-459c-be10-b10e19b1810e'  # Azure Transformation 2
        
        print("🔧 Starting data association fix...")
        print(f"   Client: {marathon_client} (Marathon Petroleum)")
        print(f"   From: {wrong_engagement} (Debug Test Engagement)")
        print(f"   To: {correct_engagement} (Azure Transformation 2)")
        print()
        
        # Get data imports in the wrong engagement that look like user uploads
        # Focus on recent uploads with substantial data (> 1 record)
        wrong_imports_query = select(DataImport).where(
            DataImport.client_account_id == uuid.UUID(marathon_client),
            DataImport.engagement_id == uuid.UUID(wrong_engagement),
            DataImport.total_records > 1  # Skip test data with only 1 record
        ).order_by(DataImport.created_at.desc()).limit(5)  # Most recent uploads
        
        result = await session.execute(wrong_imports_query)
        wrong_imports = result.scalars().all()
        
        if not wrong_imports:
            print("❌ No substantial data imports found in wrong engagement")
            return
        
        print(f"📊 Found {len(wrong_imports)} data imports to move:")
        for imp in wrong_imports:
            print(f"   - {imp.id}: {imp.source_filename} ({imp.total_records} records, {imp.created_at})")
        
        # Ask for confirmation
        choice = input("\n🤔 Move these imports to Azure Transformation 2? (y/N): ").strip().lower()
        if choice != 'y':
            print("❌ Operation cancelled")
            return
        
        moved_count = 0
        
        for imp in wrong_imports:
            try:
                print(f"\n🔄 Moving import {imp.id}...")
                
                # Update the data import record
                await session.execute(
                    update(DataImport)
                    .where(DataImport.id == imp.id)
                    .values(engagement_id=uuid.UUID(correct_engagement))
                )
                
                # Update associated raw import records
                raw_records_result = await session.execute(
                    update(RawImportRecord)
                    .where(RawImportRecord.data_import_id == imp.id)
                    .values(engagement_id=uuid.UUID(correct_engagement))
                )
                
                print(f"   ✅ Updated import and {raw_records_result.rowcount} raw records")
                moved_count += 1
                
            except Exception as e:
                print(f"   ❌ Error moving import {imp.id}: {e}")
                
        # Commit all changes
        await session.commit()
        
        print(f"\n🎉 Successfully moved {moved_count} data imports to Azure Transformation 2!")
        print("   The latest-import endpoint should now find your uploaded data.")

if __name__ == "__main__":
    asyncio.run(fix_engagement_data_association()) 