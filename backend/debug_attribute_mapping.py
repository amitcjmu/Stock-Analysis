#!/usr/bin/env python3
"""
Debug script to check database state for attribute mapping issue
"""

import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select

# Add the project root to the Python path
sys.path.append('/app')

# Get the database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ FATAL: DATABASE_URL environment variable is not set.")
    sys.exit(1)

# Ensure the URL is in the asyncpg format
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async def debug_attribute_mapping():
    """Debug the attribute mapping data retrieval issue."""
    
    print("=== DEBUGGING ATTRIBUTE MAPPING ISSUE ===")
    print(f"🔌 Using database: {DATABASE_URL}")
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession)
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Check DataImport table
            print("\n1. Checking data_imports table...")
            query = text("SELECT id, client_account_id, engagement_id, session_id, status, source_filename, total_records, created_at FROM data_imports ORDER BY created_at DESC")
            result = await session.execute(query)
            imports = result.fetchall()
            
            print(f"Found {len(imports)} data imports:")
            for imp in imports:
                print(f"  - Import ID: {imp.id}")
                print(f"    Client Account ID: {imp.client_account_id}")
                print(f"    Engagement ID: {imp.engagement_id}")
                print(f"    Session ID: {imp.session_id}")
                print(f"    Status: {imp.status}")
                print(f"    File: {imp.source_filename}")
                print(f"    Records: {imp.total_records}")
                print(f"    Created: {imp.created_at}")
                print()
            
            # 2. Check ImportFieldMapping table
            print("\n2. Checking import_field_mappings table...")
            query = text("SELECT data_import_id, source_field, target_field, status, confidence_score, mapping_type FROM import_field_mappings LIMIT 10")
            result = await session.execute(query)
            mappings = result.fetchall()
            
            print(f"Found {len(mappings)} field mappings (showing first 10):")
            for i, mapping in enumerate(mappings):
                print(f"  {i+1}. {mapping.source_field} -> {mapping.target_field}")
                print(f"      Data Import ID: {mapping.data_import_id}")
                print(f"      Status: {mapping.status}")
                print(f"      Confidence: {mapping.confidence_score}")
                print(f"      Type: {mapping.mapping_type}")
                print()
            
            # 3. Check context-specific data
            if imports:
                latest_import = imports[0]  # Most recent
                print(f"\n3. Context analysis for latest import (ID: {latest_import.id})...")
                
                query = text("""
                    SELECT source_field, target_field, status, confidence_score 
                    FROM import_field_mappings 
                    WHERE data_import_id = :import_id
                """)
                result = await session.execute(query, {"import_id": latest_import.id})
                context_mappings = result.fetchall()
                
                print(f"Mappings for this import: {len(context_mappings)}")
                for mapping in context_mappings[:5]:
                    print(f"  - {mapping.source_field} -> {mapping.target_field} ({mapping.status})")
                
                # Test the critical attributes API logic
                print(f"\n4. Testing critical attributes API logic...")
                print(f"API would search for:")
                print(f"  Client Account ID: {latest_import.client_account_id}")
                print(f"  Engagement ID: {latest_import.engagement_id}")
                
                # This simulates the exact query from the API
                query = text("""
                    SELECT * FROM data_imports 
                    WHERE client_account_id = :client_id AND engagement_id = :engagement_id
                    ORDER BY created_at DESC LIMIT 1
                """)
                result = await session.execute(query, {
                    "client_id": latest_import.client_account_id,
                    "engagement_id": latest_import.engagement_id
                })
                api_import = result.fetchone()
                
                if api_import:
                    print(f"✅ API would find import: {api_import.id}")
                    
                    # Check mappings for this import
                    query = text("SELECT COUNT(*) FROM import_field_mappings WHERE data_import_id = :import_id")
                    result = await session.execute(query, {"import_id": api_import.id})
                    mapping_count = result.scalar()
                    print(f"✅ API would find {mapping_count} mappings")
                    
                    if mapping_count == 0:
                        print("❌ No mappings found for this import - this is the problem!")
                else:
                    print("❌ API would not find any imports!")
            else:
                print("\n❌ No imports found - this is why attribute mapping shows no data!")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_attribute_mapping()) 