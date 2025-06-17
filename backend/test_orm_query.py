#!/usr/bin/env python3
"""
Test script to check the exact ORM query logic from the API
"""

import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select

# Add the project root to the Python path
sys.path.append('/app')

from app.core.database import AsyncSessionLocal
from app.models.data_import import DataImport, ImportFieldMapping

async def test_orm_query():
    """Test the exact ORM queries that the API uses."""
    
    print("=== TESTING ORM QUERY LOGIC (Matching API) ===")
    
    async with AsyncSessionLocal() as session:
        try:
            # Test with the context from the latest import
            client_account_id = 'bafd5b46-aaaf-4c95-8142-573699d93171'
            engagement_id = '6e9c8133-4169-4b79-b052-106dc93d0208'
            
            print(f"Testing with context:")
            print(f"  Client ID: {client_account_id}")
            print(f"  Engagement ID: {engagement_id}")
            
            # First query - find latest import (EXACTLY as in the API)
            print(f"\n1. Finding latest import using ORM...")
            latest_import_query = select(DataImport).where(
                and_(
                    DataImport.client_account_id == client_account_id,
                    DataImport.engagement_id == engagement_id
                )
            ).order_by(DataImport.created_at.desc()).limit(1)
            
            latest_import_result = await session.execute(latest_import_query)
            latest_import = latest_import_result.scalar_one_or_none()
            
            if latest_import:
                print(f"✅ Found import: {latest_import.id}")
                print(f"   Status: {latest_import.status}")
                print(f"   File: {latest_import.source_filename}")
                
                # Second query - find mappings for this import (EXACTLY as in the API)
                print(f"\n2. Finding mappings using ORM...")
                mappings_query = select(ImportFieldMapping).where(
                    ImportFieldMapping.data_import_id == latest_import.id
                )
                mappings_result = await session.execute(mappings_query)
                all_mappings = mappings_result.scalars().all()
                
                print(f"✅ Found {len(all_mappings)} mappings")
                if all_mappings:
                    print("First 5 mappings:")
                    for i, mapping in enumerate(all_mappings[:5]):
                        print(f"  {i+1}. {mapping.source_field} -> {mapping.target_field} ({mapping.status})")
                        print(f"      Confidence: {mapping.confidence_score}")
                        print(f"      Type: {mapping.mapping_type}")
                        
                    print(f"\n3. Testing API response building...")
                    # Build the response exactly like the API does
                    attributes_status = []
                    for mapping in all_mappings:
                        status = "unmapped"
                        if mapping.status == "approved":
                            status = "mapped"
                        elif mapping.status == "pending":
                            status = "partially_mapped"
                        
                        attributes_status.append({
                            "name": mapping.target_field,
                            "description": f"Mapping for {mapping.source_field}",
                            "category": "uncategorized",
                            "required": False,
                            "status": status,
                            "mapped_to": mapping.source_field if status == "mapped" else None,
                            "source_field": mapping.source_field,
                            "confidence": mapping.confidence_score or 0,
                            "quality_score": (mapping.confidence_score or 0) * 100,
                            "completeness_percentage": 100 if status == "mapped" else (50 if status == "partially_mapped" else 0),
                            "mapping_type": mapping.mapping_type,
                            "ai_suggestion": None,
                            "business_impact": "unknown",
                            "migration_critical": getattr(mapping, 'is_critical_field', False)
                        })
                    
                    print(f"✅ Built {len(attributes_status)} attribute status items")
                    print(f"   First item: {attributes_status[0]['name']} ({attributes_status[0]['status']})")
                    
                else:
                    print("❌ No mappings found for this import!")
            else:
                print("❌ No import found for this context")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_orm_query()) 