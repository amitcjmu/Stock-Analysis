#!/usr/bin/env python3
"""
Test script to check the exact API query logic
"""

import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

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

async def test_api_query():
    """Test the exact SQL queries that the API uses."""
    
    print("=== TESTING API QUERY LOGIC ===")
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession)
    
    async with AsyncSessionLocal() as session:
        try:
            # Test with the context from the latest import
            client_id = 'bafd5b46-aaaf-4c95-8142-573699d93171'
            engagement_id = '6e9c8133-4169-4b79-b052-106dc93d0208'
            
            print(f"Testing with context:")
            print(f"  Client ID: {client_id}")
            print(f"  Engagement ID: {engagement_id}")
            
            # First query - find latest import (exactly as in the API)
            print(f"\n1. Finding latest import...")
            query = text("""
                SELECT * FROM data_imports 
                WHERE client_account_id = :client_id AND engagement_id = :engagement_id
                ORDER BY created_at DESC LIMIT 1
            """)
            result = await session.execute(query, {
                'client_id': client_id, 
                'engagement_id': engagement_id
            })
            latest_import = result.fetchone()
            
            if latest_import:
                print(f"✅ Found import: {latest_import.id}")
                print(f"   Status: {latest_import.status}")
                print(f"   File: {latest_import.source_filename}")
                
                # Second query - find mappings for this import (exactly as in the API)
                print(f"\n2. Finding mappings...")
                query = text("SELECT * FROM import_field_mappings WHERE data_import_id = :import_id")
                result = await session.execute(query, {'import_id': latest_import.id})
                mappings = result.fetchall()
                
                print(f"✅ Found {len(mappings)} mappings")
                if mappings:
                    print("First 5 mappings:")
                    for i, mapping in enumerate(mappings[:5]):
                        print(f"  {i+1}. {mapping.source_field} -> {mapping.target_field} ({mapping.status})")
                        print(f"      Confidence: {mapping.confidence_score}")
                        print(f"      Type: {mapping.mapping_type}")
                else:
                    print("❌ No mappings found for this import!")
                    
                    # Check if there are ANY mappings in the table
                    query = text("SELECT COUNT(*) FROM import_field_mappings")
                    result = await session.execute(query)
                    total_mappings = result.scalar()
                    print(f"   Total mappings in database: {total_mappings}")
                    
                    if total_mappings > 0:
                        # Show what import IDs have mappings
                        query = text("SELECT DISTINCT data_import_id FROM import_field_mappings LIMIT 5")
                        result = await session.execute(query)
                        mapping_import_ids = result.fetchall()
                        print(f"   Import IDs with mappings:")
                        for row in mapping_import_ids:
                            print(f"     - {row.data_import_id}")
            else:
                print("❌ No import found for this context")
                
                # Check what contexts exist
                query = text("SELECT DISTINCT client_account_id, engagement_id FROM data_imports LIMIT 5")
                result = await session.execute(query)
                contexts = result.fetchall()
                print(f"Available contexts:")
                for context in contexts:
                    print(f"  - Client: {context.client_account_id}, Engagement: {context.engagement_id}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_api_query()) 