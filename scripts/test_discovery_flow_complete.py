#!/usr/bin/env python3
"""
Complete Discovery Flow Validation Test Script

This script performs comprehensive validation of the Discovery Flow functionality
to identify and document all issues that need to be fixed.
"""

import requests
import json
import os
import sys
from typing import Dict, List, Any
import asyncio

class DiscoveryFlowValidator:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.auth_headers = {}
        self.client_id = "11111111-1111-1111-1111-111111111111"
        self.engagement_id = "22222222-2222-2222-2222-222222222222"
        self.test_results = {}

    def setup_auth_headers(self):
        """Setup authentication headers for testing"""
        self.auth_headers = {
            "X-Client-Account-Id": self.client_id,
            "X-Engagement-Id": self.engagement_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def test_discovery_flows_active_endpoint(self):
        """Test the correct discovery flows active endpoint"""
        print("🔍 Testing /api/v1/unified-discovery/flows/active endpoint...")

        try:
            response = requests.get(
                f"{self.base_url}/api/v1/unified-discovery/flows/active",
                headers=self.auth_headers,
                params={"flowType": "discovery"},
                timeout=10
            )

            self.test_results["discovery_flows_active"] = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_length": len(response.text),
                "content_type": response.headers.get("content-type", "")
            }

            if response.status_code == 200:
                try:
                    data = response.json()
                    flows_count = len(data) if isinstance(data, list) else 0
                    flows_with_valid_id = 0
                    flows_with_null_id = 0

                    if isinstance(data, list):
                        for flow in data:
                            if isinstance(flow, dict):
                                flow_id = flow.get("flowId") or flow.get("flow_id")
                                if flow_id and flow_id != "undefined":
                                    flows_with_valid_id += 1
                                else:
                                    flows_with_null_id += 1

                    self.test_results["discovery_flows_active"].update({
                        "total_flows": flows_count,
                        "flows_with_valid_id": flows_with_valid_id,
                        "flows_with_null_id": flows_with_null_id,
                        "sample_flow": data[0] if flows_count > 0 else None
                    })

                    print(f"✅ Endpoint responding: {flows_count} flows returned")
                    print(f"   - Valid IDs: {flows_with_valid_id}")
                    print(f"   - Null/undefined IDs: {flows_with_null_id}")

                    if flows_with_null_id > 0:
                        print(f"🚨 CRITICAL: {flows_with_null_id} flows have null/undefined IDs!")

                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing error: {e}")
                    self.test_results["discovery_flows_active"]["json_error"] = str(e)
            else:
                print(f"❌ Endpoint failed: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"❌ Request failed: {e}")
            self.test_results["discovery_flows_active"] = {"error": str(e), "success": False}

    def test_unified_discovery_endpoint(self):
        """Test the correct unified-discovery endpoint that should work"""
        print("🔍 Testing /api/v1/unified-discovery/flows/active endpoint (should work)...")

        try:
            response = requests.get(
                f"{self.base_url}/api/v1/unified-discovery/flows/active",
                headers=self.auth_headers,
                timeout=10
            )

            self.test_results["unified_discovery_flows"] = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "expected_to_succeed": True,
                "response_text": response.text[:200] if response.text else ""
            }

            if response.status_code == 200:
                print(f"✅ Unified discovery endpoint working correctly")
            else:
                print(f"❌ Unexpected response: {response.status_code}")

        except Exception as e:
            print(f"❌ Request failed: {e}")
            self.test_results["unified_discovery_flows"] = {"error": str(e), "success": False}

    def test_flow_status_endpoint(self):
        """Test flow status endpoint with a sample flow ID"""
        print("🔍 Testing flow status endpoint...")

        # First get a flow ID from active flows
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/unified-discovery/flows/active",
                headers=self.auth_headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Find first flow with a valid ID
                    test_flow_id = None
                    for flow in data:
                        if isinstance(flow, dict):
                            flow_id = flow.get("flowId") or flow.get("flow_id")
                            if flow_id and flow_id != "undefined":
                                test_flow_id = flow_id
                                break

                    if test_flow_id:
                        # Test the status endpoint
                        status_response = requests.get(
                            f"{self.base_url}/api/v1/unified-discovery/flows/{test_flow_id}/status",
                            headers=self.auth_headers,
                            timeout=10
                        )

                        self.test_results["flow_status"] = {
                            "test_flow_id": test_flow_id,
                            "status_code": status_response.status_code,
                            "success": status_response.status_code == 200,
                            "response_length": len(status_response.text)
                        }

                        if status_response.status_code == 200:
                            print(f"✅ Flow status endpoint working for ID: {test_flow_id}")
                        else:
                            print(f"❌ Flow status failed: {status_response.status_code}")
                    else:
                        print(f"⚠️ No valid flow IDs found to test status endpoint")
                        self.test_results["flow_status"] = {"error": "No valid flow IDs", "success": False}
                else:
                    print(f"⚠️ No flows returned to test status endpoint")

        except Exception as e:
            print(f"❌ Flow status test failed: {e}")
            self.test_results["flow_status"] = {"error": str(e), "success": False}

    def test_clarifications_endpoint(self):
        """Test the clarifications submission endpoint"""
        print("🔍 Testing clarifications endpoint...")

        # This would require a valid flow ID, so we'll just test the endpoint structure
        test_flow_id = "test-flow-id"
        clarification_data = {
            "answers": {
                "test_question": "test_answer"
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/unified-discovery/flows/{test_flow_id}/clarifications/submit",
                headers=self.auth_headers,
                json=clarification_data,
                timeout=10
            )

            self.test_results["clarifications"] = {
                "status_code": response.status_code,
                "endpoint_exists": response.status_code != 404,
                "response_text": response.text[:200] if response.text else ""
            }

            if response.status_code == 404:
                print(f"❌ Clarifications endpoint missing: 404")
            elif response.status_code == 403:
                print(f"✅ Clarifications endpoint exists (403 auth expected)")
            else:
                print(f"✅ Clarifications endpoint responding: {response.status_code}")

        except Exception as e:
            print(f"❌ Clarifications test failed: {e}")
            self.test_results["clarifications"] = {"error": str(e), "success": False}

    def run_all_tests(self):
        """Run all validation tests"""
        print("🧪 Starting Discovery Flow Comprehensive Validation")
        print("=" * 60)

        self.setup_auth_headers()

        # Test all endpoints
        self.test_discovery_flows_active_endpoint()
        self.test_unified_discovery_endpoint()
        self.test_flow_status_endpoint()
        self.test_clarifications_endpoint()

        # Generate summary report
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("🏁 DISCOVERY FLOW VALIDATION REPORT")
        print("=" * 60)

        # Critical Issues
        critical_issues = []
        warnings = []
        successes = []

        # Analyze results
        if "discovery_flows_active" in self.test_results:
            result = self.test_results["discovery_flows_active"]
            if result.get("success"):
                if result.get("flows_with_null_id", 0) > 0:
                    critical_issues.append(f"❌ CRITICAL: {result['flows_with_null_id']} flows have undefined flowId")
                else:
                    successes.append("✅ Discovery flows endpoint working with valid IDs")
            else:
                critical_issues.append("❌ CRITICAL: Discovery flows endpoint not responding")

        if "unified_discovery_flows" in self.test_results:
            result = self.test_results["unified_discovery_flows"]
            if result.get("status_code") == 404:
                warnings.append("⚠️ Frontend calling non-existent /unified-discovery endpoint (expected)")

        if "flow_status" in self.test_results:
            result = self.test_results["flow_status"]
            if result.get("success"):
                successes.append("✅ Flow status endpoint working")
            else:
                critical_issues.append("❌ CRITICAL: Flow status endpoint failing")

        if "clarifications" in self.test_results:
            result = self.test_results["clarifications"]
            if result.get("endpoint_exists"):
                successes.append("✅ Clarifications endpoint exists")
            else:
                critical_issues.append("❌ CRITICAL: Clarifications endpoint missing")

        # Print summary
        print(f"\n🚨 CRITICAL ISSUES ({len(critical_issues)}):")
        for issue in critical_issues:
            print(f"   {issue}")

        print(f"\n⚠️ WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"   {warning}")

        print(f"\n✅ SUCCESSES ({len(successes)}):")
        for success in successes:
            print(f"   {success}")

        # Overall status
        if critical_issues:
            print(f"\n🚨 OVERALL STATUS: FAILED - {len(critical_issues)} critical issues must be fixed")
            return False
        else:
            print(f"\n✅ OVERALL STATUS: PASSED - Discovery Flow functionality working")
            return True

if __name__ == "__main__":
    validator = DiscoveryFlowValidator()
    success = validator.run_all_tests()

    # Save detailed results to file
    import tempfile
    results_file = os.path.join(tempfile.gettempdir(), "discovery_flow_validation_results.json")
    with open(results_file, "w") as f:
        json.dump(validator.test_results, f, indent=2)

    print(f"\n📄 Detailed results saved to: {results_file}")

    sys.exit(0 if success else 1)
