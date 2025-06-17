#!/usr/bin/env python3
"""
Test script to call the actual FastAPI endpoint directly
"""

import asyncio
import os
import sys
from fastapi import Request
from unittest.mock import Mock

# Add the project root to the Python path
sys.path.append('/app')

from app.core.database import AsyncSessionLocal
from app.core.context import get_current_context, extract_context_from_request, set_context
from app.api.v1.endpoints.data_import.critical_attributes import get_critical_attributes_status

async def test_api_endpoint():
    """Test the actual FastAPI endpoint directly."""
    
    print("=== TESTING ACTUAL API ENDPOINT ===")
    
    # Create a mock request with headers
    mock_request = Mock(spec=Request)
    mock_request.headers = {
        "X-Client-Account-ID": "bafd5b46-aaaf-4c95-8142-573699d93171",
        "X-Engagement-ID": "6e9c8133-4169-4b79-b052-106dc93d0208"
    }
    
    # Extract context like FastAPI would
    context = extract_context_from_request(mock_request)
    set_context(context)
    
    print(f"Context set: {context}")
    
    # Get database session
    async with AsyncSessionLocal() as db_session:
        try:
            # Call the actual API endpoint function
            print(f"\nCalling get_critical_attributes_status()...")
            result = await get_critical_attributes_status(
                db=db_session,
                context=context
            )
            
            print(f"✅ API returned:")
            print(f"   Attributes: {len(result['attributes'])}")
            print(f"   Total attributes: {result['statistics']['total_attributes']}")
            print(f"   Mapped count: {result['statistics']['mapped_count']}")
            
            if result['attributes']:
                print(f"   First attribute: {result['attributes'][0]['name']} ({result['attributes'][0]['status']})")
            else:
                print(f"   ❌ No attributes returned!")
                
        except Exception as e:
            print(f"❌ Error calling API endpoint: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_endpoint()) 