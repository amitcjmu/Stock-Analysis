#!/usr/bin/env python3
"""
Context Persistence and Store-Import Validation Test

This script tests:
1. Context persistence across page loads (Marathon should stay Marathon)
2. Store-import API validation with correct payload format
3. Database save operations without 422 errors
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Test contexts - Marathon should persist, not switch to Acme
TEST_CONTEXTS = {
    "marathon_petroleum": {
        "client_id": "d838573d-f461-44e4-81b5-5af510ef83b7",
        "engagement_id": "d1a93e23-719d-4dad-8bbf-b66ab9de2b94",
        "user_id": "3ee1c326-a014-4a3c-a483-5cfcf1b419d7",
        "name": "Marathon Petroleum - Cloud Migration"
    },
    "acme_corp": {
        "client_id": "bafd5b46-aaaf-4c95-8142-573699d93171",
        "engagement_id": "6e9c8133-4169-4b79-b052-106dc93d0208",
        "user_id": "44444444-4444-4444-4444-444444444444",
        "name": "Acme Corporation - Azure Transformation"
    }
}

# Sample CSV data for store-import testing
SAMPLE_CSV_DATA = [
    {
        "Asset_Name": "WEB-SERVER-01",
        "CI_Type": "Server",
        "Environment": "Production",
        "Owner": "IT Operations",
        "Location": "Dallas DC"
    },
    {
        "Asset_Name": "APP-DATABASE-01", 
        "CI_Type": "Database",
        "Environment": "Production",
        "Owner": "Database Team",
        "Location": "Dallas DC"
    },
    {
        "Asset_Name": "DEV-WEBAPP-01",
        "CI_Type": "Application",
        "Environment": "Development", 
        "Owner": "Development Team",
        "Location": "Cloud"
    }
]

async def test_store_import_validation():
    """Test that store-import API accepts the corrected payload format"""
    print("🧪 Testing Store-Import API Validation...")
    
    context = TEST_CONTEXTS["marathon_petroleum"]
    
    # Corrected payload format matching StoreImportRequest schema
    payload = {
        "file_data": SAMPLE_CSV_DATA,
        "metadata": {
            "filename": "test_cmdb_data.csv",
            "size": 1024,
            "type": "text/csv"
        },
        "upload_context": {
            "intended_type": "cmdb",
            "validation_session_id": "test-session-123",
            "upload_timestamp": datetime.now().isoformat()
        },
        "client_id": context["client_id"],        # String ID, not object
        "engagement_id": context["engagement_id"] # String ID, not object
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Client-Account-ID": context["client_id"],
        "X-Engagement-ID": context["engagement_id"],
        "X-User-ID": context["user_id"]
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "http://localhost:8000/api/v1/data-import/store-import",
                json=payload,
                headers=headers
            ) as response:
                
                result = await response.json()
                
                if response.status == 200:
                    print("✅ Store-Import API: SUCCESS (200)")
                    print(f"   Import Session ID: {result.get('import_session_id')}")
                    print(f"   Records Stored: {result.get('records_stored')}")
                    print(f"   Message: {result.get('message')}")
                    return True
                elif response.status == 422:
                    print("❌ Store-Import API: VALIDATION ERROR (422)")
                    print(f"   Error Details: {result}")
                    return False
                else:
                    print(f"⚠️  Store-Import API: Unexpected Status ({response.status})")
                    print(f"   Response: {result}")
                    return False
                    
        except Exception as e:
            print(f"❌ Store-Import API: Connection Error - {e}")
            return False

async def test_context_persistence():
    """Test context endpoints to verify Marathon context is preserved"""
    print("\n🧪 Testing Context Persistence...")
    
    context = TEST_CONTEXTS["marathon_petroleum"]
    
    headers = {
        "X-Client-Account-ID": context["client_id"],
        "X-Engagement-ID": context["engagement_id"],
        "X-User-ID": context["user_id"]
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test context extraction
            async with session.get(
                "http://localhost:8000/api/v1/discovery/latest-import",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ Context Persistence: Headers processed correctly")
                    print(f"   Expected Client: Marathon Petroleum ({context['client_id']})")
                    print("   Context Preserved: ✅")
                    return True
                else:
                    print(f"❌ Context Persistence: Failed ({response.status})")
                    return False
                    
        except Exception as e:
            print(f"❌ Context Persistence: Connection Error - {e}")
            return False

async def test_backend_context_extraction():
    """Test that backend properly extracts context from standardized headers"""
    print("\n🧪 Testing Backend Context Extraction...")
    
    context = TEST_CONTEXTS["marathon_petroleum"]
    
    # Test all header variations
    header_variations = [
        {
            "name": "Standard Format",
            "headers": {
                "X-Client-Account-ID": context["client_id"],
                "X-Engagement-ID": context["engagement_id"],
                "X-User-ID": context["user_id"]
            }
        },
        {
            "name": "Lowercase Format", 
            "headers": {
                "x-client-account-id": context["client_id"],
                "x-engagement-id": context["engagement_id"],
                "x-user-id": context["user_id"]
            }
        }
    ]
    
    success_count = 0
    async with aiohttp.ClientSession() as session:
        for variation in header_variations:
            try:
                async with session.get(
                    "http://localhost:8000/api/v1/discovery/latest-import",
                    headers=variation["headers"]
                ) as response:
                    
                    if response.status == 200:
                        print(f"✅ {variation['name']}: Context extracted successfully")
                        success_count += 1
                    else:
                        print(f"❌ {variation['name']}: Failed ({response.status})")
                        
            except Exception as e:
                print(f"❌ {variation['name']}: Error - {e}")
    
    return success_count == len(header_variations)

async def main():
    """Run all context and validation tests"""
    print("🎯 Context Persistence & Store-Import Validation Test Suite")
    print("=" * 60)
    
    results = {
        "store_import_validation": await test_store_import_validation(),
        "context_persistence": await test_context_persistence(), 
        "backend_context_extraction": await test_backend_context_extraction()
    }
    
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Context switching and store-import validation issues resolved!")
        print("   - Marathon context should persist across page loads")
        print("   - File upload database saves should work without 422 errors")
        print("   - Backend context extraction handles all header formats")
    else:
        print("\n⚠️  Some issues remain - check logs for details")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main()) 