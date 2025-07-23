#!/usr/bin/env python3
"""
Test script to verify ETag implementation in discovery flow query endpoints.
This script demonstrates the efficient polling behavior with ETags.
"""

import asyncio
import logging
from datetime import datetime

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1/discovery"

# Test headers with tenant context
HEADERS = {
    "X-Client-Account-ID": "11111111-def0-def0-def0-111111111111",
    "X-Engagement-ID": "22222222-def0-def0-def0-222222222222",
    "X-User-ID": "33333333-def0-def0-def0-333333333333",
    "Authorization": "Bearer test_token"  # Replace with actual token
}


async def test_flow_status_etag(flow_id: str):
    """Test the flow status endpoint with ETag support"""
    async with httpx.AsyncClient() as client:
        logger.info(f"Testing flow status endpoint for flow {flow_id}")
        
        # First request - should return full data
        response1 = await client.get(
            f"{BASE_URL}{API_PREFIX}/flows/{flow_id}/status",
            headers=HEADERS
        )
        
        if response1.status_code == 200:
            logger.info(f"✅ First request successful - Status: {response1.status_code}")
            logger.info(f"   ETag: {response1.headers.get('ETag', 'Not present')}")
            logger.info(f"   Cache-Control: {response1.headers.get('Cache-Control', 'Not present')}")
            logger.info(f"   X-Flow-Updated-At: {response1.headers.get('X-Flow-Updated-At', 'Not present')}")
            
            etag = response1.headers.get('ETag')
            
            if etag:
                # Second request with If-None-Match header - should return 304
                headers_with_etag = HEADERS.copy()
                headers_with_etag['If-None-Match'] = etag
                
                response2 = await client.get(
                    f"{BASE_URL}{API_PREFIX}/flows/{flow_id}/status",
                    headers=headers_with_etag
                )
                
                if response2.status_code == 304:
                    logger.info("✅ Second request returned 304 Not Modified - Efficient polling working!")
                    logger.info("   No body returned, saving bandwidth")
                else:
                    logger.warning(f"❌ Second request returned {response2.status_code} instead of 304")
                    logger.warning(f"   Body: {response2.text}")
            else:
                logger.warning("❌ No ETag header in response")
        else:
            logger.error(f"❌ First request failed - Status: {response1.status_code}")
            logger.error(f"   Response: {response1.text}")


async def test_active_flows_etag():
    """Test the active flows endpoint with ETag support"""
    async with httpx.AsyncClient() as client:
        logger.info("Testing active flows endpoint")
        
        # First request
        response1 = await client.get(
            f"{BASE_URL}{API_PREFIX}/flows/active",
            headers=HEADERS
        )
        
        if response1.status_code == 200:
            logger.info(f"✅ First request successful - Status: {response1.status_code}")
            logger.info(f"   ETag: {response1.headers.get('ETag', 'Not present')}")
            logger.info(f"   X-Flow-Count: {response1.headers.get('X-Flow-Count', 'Not present')}")
            
            etag = response1.headers.get('ETag')
            
            if etag:
                # Second request with If-None-Match
                headers_with_etag = HEADERS.copy()
                headers_with_etag['If-None-Match'] = etag
                
                response2 = await client.get(
                    f"{BASE_URL}{API_PREFIX}/flows/active",
                    headers=headers_with_etag
                )
                
                if response2.status_code == 304:
                    logger.info("✅ Second request returned 304 Not Modified - Efficient polling working!")
                else:
                    logger.warning(f"❌ Second request returned {response2.status_code} instead of 304")
        else:
            logger.error(f"❌ First request failed - Status: {response1.status_code}")


async def test_processing_status_etag(flow_id: str):
    """Test the processing status endpoint with ETag support"""
    async with httpx.AsyncClient() as client:
        logger.info(f"Testing processing status endpoint for flow {flow_id}")
        
        # First request
        response1 = await client.get(
            f"{BASE_URL}{API_PREFIX}/flow/{flow_id}/processing-status",
            headers=HEADERS
        )
        
        if response1.status_code == 200:
            logger.info(f"✅ First request successful - Status: {response1.status_code}")
            logger.info(f"   ETag: {response1.headers.get('ETag', 'Not present')}")
            
            etag = response1.headers.get('ETag')
            
            if etag:
                # Simulate polling with same ETag
                await asyncio.sleep(1)  # Wait a bit
                
                headers_with_etag = HEADERS.copy()
                headers_with_etag['If-None-Match'] = etag
                
                response2 = await client.get(
                    f"{BASE_URL}{API_PREFIX}/flow/{flow_id}/processing-status",
                    headers=headers_with_etag
                )
                
                if response2.status_code == 304:
                    logger.info("✅ Polling returned 304 Not Modified - Bandwidth saved!")
                else:
                    logger.warning(f"❌ Polling returned {response2.status_code} instead of 304")
        else:
            logger.error(f"❌ First request failed - Status: {response1.status_code}")


async def simulate_polling_session(flow_id: str, duration_seconds: int = 10):
    """Simulate a real polling session to show bandwidth savings"""
    async with httpx.AsyncClient() as client:
        logger.info(f"\n🔄 Starting {duration_seconds}s polling simulation for flow {flow_id}")
        
        etag = None
        request_count = 0
        not_modified_count = 0
        bytes_saved = 0
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < duration_seconds:
            request_count += 1
            
            headers = HEADERS.copy()
            if etag:
                headers['If-None-Match'] = etag
            
            response = await client.get(
                f"{BASE_URL}{API_PREFIX}/flows/{flow_id}/status",
                headers=headers
            )
            
            if response.status_code == 200:
                # Data changed or first request
                etag = response.headers.get('ETag')
                logger.info(f"   Request #{request_count}: 200 OK - Data updated")
            elif response.status_code == 304:
                # Data unchanged
                not_modified_count += 1
                # Estimate bandwidth saved (assuming typical response is ~2KB)
                bytes_saved += 2048
                logger.info(f"   Request #{request_count}: 304 Not Modified - Bandwidth saved")
            
            await asyncio.sleep(1)  # Poll every second
        
        logger.info("\n📊 Polling Summary:")
        logger.info(f"   Total requests: {request_count}")
        logger.info(f"   304 responses: {not_modified_count}")
        logger.info(f"   Efficiency rate: {(not_modified_count/request_count)*100:.1f}%")
        logger.info(f"   Estimated bandwidth saved: {bytes_saved/1024:.1f} KB")


async def main():
    """Run all ETag tests"""
    logger.info("🚀 Starting ETag Implementation Tests\n")
    
    # You'll need to replace this with an actual flow ID from your system
    test_flow_id = "12345678-1234-1234-1234-123456789012"
    
    # Test individual endpoints
    await test_flow_status_etag(test_flow_id)
    logger.info("")
    
    await test_active_flows_etag()
    logger.info("")
    
    await test_processing_status_etag(test_flow_id)
    logger.info("")
    
    # Simulate real polling behavior
    await simulate_polling_session(test_flow_id, duration_seconds=10)
    
    logger.info("\n✅ ETag implementation tests completed!")


if __name__ == "__main__":
    asyncio.run(main())