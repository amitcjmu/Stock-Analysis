#!/usr/bin/env python3
"""
End-to-End Validation Test Suite
Agent Team Delta - Comprehensive Production Validation
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Client-Account-ID": "1",
    "X-Engagement-ID": "1"
}

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "details": []
}


def log_result(test_name: str, passed: bool, details: str = ""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status} - {test_name}")
    if details:
        print(f"   Details: {details}")

    test_results["details"].append({
        "test": test_name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

    if passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1


async def test_backend_health():
    """Test 1: Backend Health Check"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/api/v1/health", headers=TEST_HEADERS) as response:
                if response.status == 200:
                    data = await response.json()
                    db_healthy = data.get("database", {}).get("status") == "healthy"
                    log_result(
                        "Backend Health Check",
                        db_healthy,
                        f"Service: {data.get('status')}, DB: {data.get('database', {}).get('status')}"
                    )
                    return db_healthy
                else:
                    log_result("Backend Health Check", False, f"Status code: {response.status}")
                    return False
        except Exception as e:
            log_result("Backend Health Check", False, str(e))
            return False


async def test_discovery_flow_creation():
    """Test 2: Discovery Flow Creation and Execution"""
    async with aiohttp.ClientSession() as session:
        # Create discovery flow
        create_data = {
            "flow_name": f"E2E Test Discovery - {datetime.now().strftime('%H%M%S')}",
            "raw_data": [
                {
                    "application_name": "E2E_TestApp1",
                    "business_criticality": "High",
                    "technical_complexity": "Medium",
                    "dependencies": ["Database", "Cache"],
                    "technology_stack": ["Java", "Spring Boot", "PostgreSQL"]
                },
                {
                    "application_name": "E2E_TestApp2",
                    "business_criticality": "Medium",
                    "technical_complexity": "Low",
                    "dependencies": ["E2E_TestApp1"],
                    "technology_stack": ["Python", "FastAPI", "Redis"]
                }
            ],
            "configuration": {
                "source": "e2e_validation_test"
            }
        }

        try:
            # Create flow
            async with session.post(
                f"{BASE_URL}/api/v1/unified-discovery/flow/initialize",
                json=create_data,
                headers=TEST_HEADERS
            ) as response:
                result = await response.json()

                if response.status == 200 and result.get("success"):
                    flow_id = result.get("flow_id")
                    log_result(
                        "Discovery Flow Creation",
                        True,
                        f"Flow ID: {flow_id}"
                    )

                    # Wait and check status
                    await asyncio.sleep(5)

                    # Check flow status
                    async with session.get(
                        f"{BASE_URL}/api/v1/unified-discovery/flow/{flow_id}/status",
                        headers=TEST_HEADERS
                    ) as status_response:
                        if status_response.status == 200:
                            status_data = await status_response.json()
                            flow_progressed = (
                                status_data.get("status") != "initialized" or
                                status_data.get("current_phase") not in [None, "initialization"]
                            )

                            log_result(
                                "Discovery Flow Execution",
                                flow_progressed,
                                f"Status: {status_data.get('status')}, Phase: {status_data.get('current_phase')}"
                            )
                            return flow_progressed
                        else:
                            log_result("Discovery Flow Execution", False, "Failed to get status")
                            return False
                else:
                    log_result(
                        "Discovery Flow Creation",
                        False,
                        result.get("error", "Unknown error")
                    )
                    return False

        except Exception as e:
            log_result("Discovery Flow Creation", False, str(e))
            return False


async def test_api_performance():
    """Test 3: API Response Time Performance"""
    endpoints = [
        ("GET", "/api/v1/health", None),
        ("POST", "/api/v1/unified-discovery/flow/initialize", {
            "flow_name": "Perf Test",
            "raw_data": [],
            "configuration": {}
        })
    ]

    performance_ok = True

    async with aiohttp.ClientSession() as session:
        for method, endpoint, data in endpoints:
            url = f"{BASE_URL}{endpoint}"
            start_time = time.time()

            try:
                if method == "POST":
                    async with session.post(url, json=data, headers=TEST_HEADERS) as response:
                        await response.read()
                else:
                    async with session.get(url, headers=TEST_HEADERS) as response:
                        await response.read()

                response_time = (time.time() - start_time) * 1000  # ms

                # Performance threshold: 1000ms
                if response_time > 1000:
                    performance_ok = False
                    log_result(
                        f"API Performance - {method} {endpoint}",
                        False,
                        f"Response time: {response_time:.2f}ms (exceeds 1000ms threshold)"
                    )
                else:
                    log_result(
                        f"API Performance - {method} {endpoint}",
                        True,
                        f"Response time: {response_time:.2f}ms"
                    )

            except Exception as e:
                performance_ok = False
                log_result(f"API Performance - {method} {endpoint}", False, str(e))

    return performance_ok


async def test_error_handling():
    """Test 4: Error Handling and Recovery"""
    async with aiohttp.ClientSession() as session:
        # Test with invalid data
        invalid_data = {
            "flow_name": "Error Test",
            # Missing required raw_data field
            "configuration": {}
        }

        try:
            async with session.post(
                f"{BASE_URL}/api/v1/unified-discovery/flow/initialize",
                json=invalid_data,
                headers=TEST_HEADERS
            ) as response:
                result = await response.json()

                # Should handle error gracefully
                handled_gracefully = (
                    response.status == 200 and  # Returns 200 even on error
                    not result.get("success") and  # But success is false
                    result.get("error") is not None  # And error message provided
                )

                log_result(
                    "Error Handling - Invalid Data",
                    handled_gracefully,
                    f"Error message: {result.get('error', 'No error message')}"
                )
                return handled_gracefully

        except Exception as e:
            log_result("Error Handling - Invalid Data", False, f"Exception: {str(e)}")
            return False


async def test_concurrent_flows():
    """Test 5: Concurrent Flow Creation"""
    async with aiohttp.ClientSession() as session:
        # Create multiple flows concurrently
        flow_tasks = []

        for i in range(3):
            create_data = {
                "flow_name": f"Concurrent Test {i+1}",
                "raw_data": [{
                    "application_name": f"ConcurrentApp{i+1}",
                    "business_criticality": "Medium",
                    "technical_complexity": "Low"
                }],
                "configuration": {"test_id": i+1}
            }

            task = session.post(
                f"{BASE_URL}/api/v1/unified-discovery/flow/initialize",
                json=create_data,
                headers=TEST_HEADERS
            )
            flow_tasks.append(task)

        try:
            # Execute all requests concurrently
            responses = await asyncio.gather(*flow_tasks, return_exceptions=True)

            successful_flows = 0
            flow_ids = []

            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    continue

                async with response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("success"):
                            successful_flows += 1
                            flow_ids.append(result.get("flow_id"))

            all_successful = successful_flows == 3
            log_result(
                "Concurrent Flow Creation",
                all_successful,
                f"Created {successful_flows}/3 flows successfully"
            )

            return all_successful

        except Exception as e:
            log_result("Concurrent Flow Creation", False, str(e))
            return False


async def test_flow_isolation():
    """Test 6: Multi-tenant Flow Isolation"""
    async with aiohttp.ClientSession() as session:
        # Create flow for client 1
        headers_client1 = {**TEST_HEADERS, "X-Client-Account-ID": "1"}
        headers_client2 = {**TEST_HEADERS, "X-Client-Account-ID": "2"}

        flow_data = {
            "flow_name": "Isolation Test",
            "raw_data": [],
            "configuration": {}
        }

        try:
            # Create flow for client 1
            async with session.post(
                f"{BASE_URL}/api/v1/unified-discovery/flow/initialize",
                json=flow_data,
                headers=headers_client1
            ) as response:
                if response.status == 200:
                    result1 = await response.json()
                    if result1.get("success"):
                        flow_id1 = result1.get("flow_id")

                        # Try to access client 1's flow with client 2's context
                        async with session.get(
                            f"{BASE_URL}/api/v1/unified-discovery/flow/{flow_id1}/status",
                            headers=headers_client2
                        ) as status_response:
                            # Should not be able to access
                            isolated = (
                                status_response.status != 200 or
                                (await status_response.json()).get("flow_id") != flow_id1
                            )

                            log_result(
                                "Multi-tenant Isolation",
                                isolated,
                                "Client 2 cannot access Client 1 flows" if isolated else "SECURITY ISSUE: Cross-tenant access detected!"
                            )
                            return isolated

            log_result("Multi-tenant Isolation", False, "Failed to create test flow")
            return False

        except Exception as e:
            log_result("Multi-tenant Isolation", False, str(e))
            return False


async def main():
    """Run all validation tests"""
    print("\n" + "="*80)
    print("🚀 MASTER FLOW ORCHESTRATOR - END-TO-END VALIDATION SUITE")
    print("="*80)
    print("Agent Team Delta - Production Readiness Validation")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Run all tests
    await test_backend_health()
    await test_discovery_flow_creation()
    await test_api_performance()
    await test_error_handling()
    await test_concurrent_flows()
    await test_flow_isolation()

    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    total_tests = test_results["passed"] + test_results["failed"]
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {test_results['passed']} ✅")
    print(f"Failed: {test_results['failed']} ❌")
    print(f"Success Rate: {(test_results['passed']/total_tests*100):.1f}%")

    if test_results["failed"] == 0:
        print("\n🎉 ALL TESTS PASSED - SYSTEM IS PRODUCTION READY!")
    else:
        print("\n⚠️ SOME TESTS FAILED - ISSUES NEED TO BE ADDRESSED")
        print("\nFailed Tests:")
        for detail in test_results["details"]:
            if not detail["passed"]:
                print(f"  - {detail['test']}: {detail['details']}")

    print("\n" + "="*80)

    # Save results
    with open("e2e_validation_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
        print("\nDetailed results saved to: e2e_validation_results.json")


if __name__ == "__main__":
    asyncio.run(main())
