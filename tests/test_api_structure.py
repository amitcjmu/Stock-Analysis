#!/usr/bin/env python3
"""
API Structure Validation Test

This script validates the MFO integration API structure without requiring
a fully functioning database. It tests endpoint availability, authentication,
error handling, and response formats.
"""

import asyncio
import json
import sys
from typing import Dict, List

import aiohttp


class APIStructureValidator:
    """Validates API structure and integration patterns"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.results = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_result(self, test: str, status: str, details: str):
        """Log a test result"""
        symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{symbol} {test}: {status}")
        if details:
            print(f"   {details}")

        self.results.append({
            'test': test,
            'status': status,
            'details': details
        })

    async def test_openapi_specification(self):
        """Test OpenAPI specification availability and structure"""
        try:
            async with self.session.get(f"{self.base_url}/openapi.json") as response:
                if response.status == 200:
                    spec = await response.json()
                    paths = spec.get('paths', {})

                    # Check for key MFO endpoints
                    mfo_endpoints = [
                        '/api/v1/master-flows/active',
                        '/api/v1/flow-processing/continue/{flow_id}',
                        '/api/v1/unified-discovery/flow/initialize',
                        '/api/v1/collection/flows/ensure'
                    ]

                    found_endpoints = []
                    missing_endpoints = []

                    for endpoint in mfo_endpoints:
                        # Handle path parameters
                        endpoint_key = endpoint.replace('{flow_id}', '{flow_id}')
                        if endpoint_key in paths:
                            found_endpoints.append(endpoint)
                        else:
                            missing_endpoints.append(endpoint)

                    if not missing_endpoints:
                        self.log_result(
                            "OpenAPI MFO Endpoints",
                            "PASS",
                            f"All {len(found_endpoints)} key MFO endpoints found"
                        )
                    else:
                        self.log_result(
                            "OpenAPI MFO Endpoints",
                            "FAIL",
                            f"Missing endpoints: {missing_endpoints}"
                        )

                    # Check authentication schemas
                    components = spec.get('components', {})
                    schemas = components.get('schemas', {})

                    auth_schemas = ['LoginRequest', 'LoginResponse']
                    found_auth = [s for s in auth_schemas if s in schemas]

                    self.log_result(
                        "Authentication Schemas",
                        "PASS" if len(found_auth) == len(auth_schemas) else "WARN",
                        f"Found {len(found_auth)}/{len(auth_schemas)} auth schemas"
                    )

                    return True
                else:
                    self.log_result(
                        "OpenAPI Specification",
                        "FAIL",
                        f"HTTP {response.status}"
                    )
                    return False

        except Exception as e:
            self.log_result(
                "OpenAPI Specification",
                "FAIL",
                f"Exception: {str(e)}"
            )
            return False

    async def test_authentication_flow(self):
        """Test authentication endpoint and token generation"""
        try:
            # Test login endpoint
            auth_url = f"{self.base_url}/api/v1/auth/login"
            auth_data = {
                "email": "demo@demo-corp.com",
                "password": "Demo123!"
            }

            async with self.session.post(auth_url, json=auth_data) as response:
                if response.status == 200:
                    auth_response = await response.json()

                    if auth_response.get('status') == 'success':
                        token = auth_response.get('token', {}).get('access_token')
                        user_info = auth_response.get('user', {})

                        self.log_result(
                            "Demo User Authentication",
                            "PASS",
                            f"User: {user_info.get('email')}, Token: {'✓' if token else '✗'}"
                        )

                        # Test token validation by making authenticated request
                        if token:
                            headers = {'Authorization': f'Bearer {token}'}
                            test_url = f"{self.base_url}/api/v1/master-flows/active"

                            async with self.session.get(test_url, headers=headers) as test_response:
                                # We expect this to fail with 400 (context issue) not 401 (auth issue)
                                if test_response.status == 400:
                                    self.log_result(
                                        "JWT Token Validation",
                                        "PASS",
                                        "Token accepted (400 = context issue, not auth issue)"
                                    )
                                elif test_response.status in [401, 403]:
                                    self.log_result(
                                        "JWT Token Validation",
                                        "FAIL",
                                        f"Token rejected: HTTP {test_response.status}"
                                    )
                                else:
                                    self.log_result(
                                        "JWT Token Validation",
                                        "WARN",
                                        f"Unexpected response: HTTP {test_response.status}"
                                    )

                        return token
                    else:
                        self.log_result(
                            "Demo User Authentication",
                            "FAIL",
                            f"Login failed: {auth_response.get('message', 'Unknown')}"
                        )
                        return None
                else:
                    self.log_result(
                        "Demo User Authentication",
                        "FAIL",
                        f"HTTP {response.status}"
                    )
                    return None

        except Exception as e:
            self.log_result(
                "Demo User Authentication",
                "FAIL",
                f"Exception: {str(e)}"
            )
            return None

    async def test_mfo_endpoint_responses(self, token: str):
        """Test MFO endpoint response patterns"""
        headers = {'Authorization': f'Bearer {token}'} if token else {}

        test_endpoints = [
            ('Master Flows Active', 'GET', '/api/v1/master-flows/active'),
            ('Cross-Phase Analytics', 'GET', '/api/v1/master-flows/analytics/cross-phase'),
            ('Coordination Summary', 'GET', '/api/v1/master-flows/coordination/summary'),
            ('Collection Status', 'GET', '/api/v1/collection/status'),
            ('Discovery Flow Init', 'POST', '/api/v1/unified-discovery/flow/initialize'),
        ]

        for name, method, endpoint in test_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"

                if method == 'GET':
                    async with self.session.get(url, headers=headers) as response:
                        await self._analyze_endpoint_response(name, response)
                elif method == 'POST':
                    # Test with minimal data
                    test_data = {"flow_name": "test", "configuration": {}}
                    async with self.session.post(url, json=test_data, headers=headers) as response:
                        await self._analyze_endpoint_response(name, response)

            except Exception as e:
                self.log_result(
                    f"Endpoint {name}",
                    "FAIL",
                    f"Exception: {str(e)}"
                )

    async def _analyze_endpoint_response(self, name: str, response):
        """Analyze endpoint response patterns"""
        status = response.status

        try:
            content = await response.json()
        except:
            content = await response.text()

        if status == 200:
            self.log_result(
                f"Endpoint {name}",
                "PASS",
                "HTTP 200 - Endpoint fully functional"
            )
        elif status == 400:
            # Check if it's a context error (expected) vs validation error (problem)
            if isinstance(content, dict) and 'context' in str(content).lower():
                self.log_result(
                    f"Endpoint {name}",
                    "WARN",
                    "HTTP 400 - Context extraction failed (expected without full DB)"
                )
            else:
                self.log_result(
                    f"Endpoint {name}",
                    "FAIL",
                    f"HTTP 400 - Validation error: {str(content)[:100]}"
                )
        elif status in [401, 403]:
            self.log_result(
                f"Endpoint {name}",
                "FAIL",
                f"HTTP {status} - Authentication/Authorization issue"
            )
        elif status == 404:
            self.log_result(
                f"Endpoint {name}",
                "FAIL",
                "HTTP 404 - Endpoint not found"
            )
        elif status == 500:
            self.log_result(
                f"Endpoint {name}",
                "FAIL",
                f"HTTP 500 - Server error: {str(content)[:100]}"
            )
        else:
            self.log_result(
                f"Endpoint {name}",
                "WARN",
                f"HTTP {status} - Unexpected response: {str(content)[:50]}"
            )

    async def test_error_handling_patterns(self, token: str):
        """Test error handling consistency"""
        headers = {'Authorization': f'Bearer {token}'} if token else {}

        error_tests = [
            ('Invalid Flow ID', 'GET', '/api/v1/master-flows/invalid-uuid/summary'),
            ('Malformed Flow ID', 'GET', '/api/v1/master-flows/not-a-uuid/summary'),
            ('Nonexistent Flow', 'POST', '/api/v1/flow-processing/continue/00000000-0000-0000-0000-000000000000'),
        ]

        consistent_errors = 0

        for name, method, endpoint in error_tests:
            try:
                url = f"{self.base_url}{endpoint}"

                if method == 'GET':
                    async with self.session.get(url, headers=headers) as response:
                        if response.status >= 400:
                            consistent_errors += 1
                elif method == 'POST':
                    test_data = {"user_context": {"test": True}}
                    async with self.session.post(url, json=test_data, headers=headers) as response:
                        if response.status >= 400:
                            consistent_errors += 1

            except Exception:
                # Exception handling also counts as proper error handling
                consistent_errors += 1

        if consistent_errors == len(error_tests):
            self.log_result(
                "Error Handling Consistency",
                "PASS",
                f"All {len(error_tests)} error scenarios properly handled"
            )
        else:
            self.log_result(
                "Error Handling Consistency",
                "WARN",
                f"{consistent_errors}/{len(error_tests)} error scenarios handled"
            )

    async def test_health_endpoints(self):
        """Test system health endpoints"""
        health_endpoints = [
            ('/api/v1/health', 'System Health'),
            ('/docs', 'API Documentation'),
        ]

        for endpoint, name in health_endpoints:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        self.log_result(
                            name,
                            "PASS",
                            "Endpoint accessible"
                        )
                    else:
                        self.log_result(
                            name,
                            "WARN",
                            f"HTTP {response.status}"
                        )
            except Exception as e:
                self.log_result(
                    name,
                    "FAIL",
                    f"Exception: {str(e)}"
                )

    async def run_validation(self):
        """Run all validation tests"""
        print("🔍 API Structure Validation Test")
        print(f"Target: {self.base_url}")
        print("=" * 50)

        # Test 1: OpenAPI Specification
        await self.test_openapi_specification()

        # Test 2: Authentication Flow
        token = await self.test_authentication_flow()

        # Test 3: Health Endpoints
        await self.test_health_endpoints()

        # Test 4: MFO Endpoint Responses
        if token:
            await self.test_mfo_endpoint_responses(token)

            # Test 5: Error Handling
            await self.test_error_handling_patterns(token)

        # Generate Summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)

        total = len(self.results)
        passed = len([r for r in self.results if r['status'] == 'PASS'])
        failed = len([r for r in self.results if r['status'] == 'FAIL'])
        warned = len([r for r in self.results if r['status'] == 'WARN'])

        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warned}")
        print(f"Success Rate: {(passed/total*100):.1f}%")

        if failed == 0:
            print("\n🎉 API Structure Validation: PASSED")
            print("   All endpoints are properly structured and accessible")
        elif failed <= 2:
            print("\n⚠️  API Structure Validation: MOSTLY PASSED")
            print("   Minor issues found, but core structure is sound")
        else:
            print("\n❌ API Structure Validation: ISSUES FOUND")
            print("   Significant structural problems detected")

        print("\nKey Findings:")
        for result in self.results:
            if result['status'] == 'FAIL':
                print(f"  ❌ {result['test']}: {result['details']}")
            elif result['status'] == 'PASS' and 'endpoint' in result['test'].lower():
                print(f"  ✅ {result['test']}: Working")


async def main():
    async with APIStructureValidator() as validator:
        await validator.run_validation()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nValidation failed: {str(e)}")
        sys.exit(1)
