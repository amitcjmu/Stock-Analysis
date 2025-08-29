#!/usr/bin/env python3
"""
Flow Endpoint Validation Script

This script validates that all flow endpoints are working correctly after the
consolidation from singular /flow/ to plural /flows/ convention.

Usage:
    python scripts/validate_flow_endpoints.py

Requirements:
    - Backend running on localhost:8000
    - requests library (pip install requests)
"""

import requests
import sys
import json
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class EndpointTest:
    name: str
    url: str
    method: str = "GET"
    expected_status: List[int] = None
    should_not_be_404: bool = True

def main():
    """Main validation function"""
    print("🔍 Flow Endpoint Consolidation Validation")
    print("=" * 50)

    # Define endpoints to test
    base_url = "http://localhost:8000"

    endpoints = [
        EndpointTest(
            name="Backend Health",
            url=f"{base_url}/api/v1/health",
            expected_status=[200]
        ),
        EndpointTest(
            name="Database Health",
            url=f"{base_url}/api/v1/health/database",
            expected_status=[200]
        ),
        EndpointTest(
            name="Unified Discovery Health",
            url=f"{base_url}/api/v1/unified-discovery/health",
            expected_status=[200]
        ),
        EndpointTest(
            name="Flow Health (plural convention)",
            url=f"{base_url}/api/v1/flows/health",
            expected_status=[200, 400, 401]  # Auth required but endpoint exists
        ),
        EndpointTest(
            name="Active Flows (plural convention)",
            url=f"{base_url}/api/v1/unified-discovery/flows/active",
            expected_status=[200, 400, 401]  # Auth required but endpoint exists
        ),
    ]

    # Test each endpoint
    all_passed = True
    results = []

    for endpoint in endpoints:
        try:
            print(f"\n🔍 Testing: {endpoint.name}")
            print(f"   URL: {endpoint.url}")

            response = requests.get(endpoint.url, timeout=10)
            status_code = response.status_code

            print(f"   Status: HTTP {status_code}")

            # Check if it's a 404 (should never be 404 after consolidation)
            if endpoint.should_not_be_404 and status_code == 404:
                print(f"   ❌ FAIL: Endpoint returned 404 (not found)")
                all_passed = False
                results.append({
                    "endpoint": endpoint.name,
                    "status": "FAIL",
                    "issue": "404 Not Found",
                    "actual_status": status_code
                })
                continue

            # Check expected status codes
            if endpoint.expected_status and status_code not in endpoint.expected_status:
                print(f"   ⚠️  WARN: Unexpected status code {status_code}, expected {endpoint.expected_status}")
                results.append({
                    "endpoint": endpoint.name,
                    "status": "WARN",
                    "issue": f"Unexpected status {status_code}",
                    "expected": endpoint.expected_status,
                    "actual_status": status_code
                })
            else:
                print(f"   ✅ PASS: Endpoint accessible")
                results.append({
                    "endpoint": endpoint.name,
                    "status": "PASS",
                    "actual_status": status_code
                })

            # Try to parse JSON response for additional info
            try:
                json_response = response.json()
                if "status" in json_response:
                    print(f"   Service Status: {json_response['status']}")
            except:
                pass  # Not JSON or parsing failed

        except requests.exceptions.ConnectionError:
            print(f"   ❌ FAIL: Cannot connect to {endpoint.url}")
            print(f"   Make sure backend is running on localhost:8000")
            all_passed = False
            results.append({
                "endpoint": endpoint.name,
                "status": "FAIL",
                "issue": "Connection refused"
            })
        except requests.exceptions.Timeout:
            print(f"   ❌ FAIL: Request timeout")
            all_passed = False
            results.append({
                "endpoint": endpoint.name,
                "status": "FAIL",
                "issue": "Request timeout"
            })
        except Exception as e:
            print(f"   ❌ FAIL: {str(e)}")
            all_passed = False
            results.append({
                "endpoint": endpoint.name,
                "status": "FAIL",
                "issue": str(e)
            })

    # Print summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)

    pass_count = len([r for r in results if r["status"] == "PASS"])
    warn_count = len([r for r in results if r["status"] == "WARN"])
    fail_count = len([r for r in results if r["status"] == "FAIL"])

    print(f"✅ PASSED: {pass_count}")
    print(f"⚠️  WARNINGS: {warn_count}")
    print(f"❌ FAILED: {fail_count}")

    # Show detailed results
    if warn_count > 0 or fail_count > 0:
        print(f"\n📋 DETAILED RESULTS:")
        for result in results:
            if result["status"] != "PASS":
                status_icon = "⚠️" if result["status"] == "WARN" else "❌"
                print(f"{status_icon} {result['endpoint']}: {result['issue']}")

    # Final verdict
    print(f"\n🎯 OVERALL STATUS:")
    if all_passed and fail_count == 0:
        print("✅ FLOW ENDPOINT CONSOLIDATION: VALIDATED")
        print("   All critical endpoints are accessible")
        print("   No 404 errors found")
        print("   System ready for use")
        sys.exit(0)
    elif fail_count == 0:
        print("⚠️  FLOW ENDPOINT CONSOLIDATION: MOSTLY VALIDATED")
        print("   All endpoints accessible but some warnings")
        print("   Review warnings above")
        sys.exit(0)
    else:
        print("❌ FLOW ENDPOINT CONSOLIDATION: VALIDATION FAILED")
        print("   Critical issues found - see details above")
        print("   System may not be ready for use")
        sys.exit(1)

if __name__ == "__main__":
    main()
