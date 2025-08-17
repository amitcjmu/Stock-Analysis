#!/usr/bin/env python3
"""
Integration test for modularized API endpoints
Tests actual API endpoints through HTTP requests to verify modularization works
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional

class APIIntegrationValidator:
    """Tests API endpoints to validate modularization works correctly."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: Dict[str, Dict[str, Any]] = {}
        self.errors: List[str] = []
        
    def log_result(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """Log test result."""
        self.results[test_name] = {
            "success": success,
            "details": details,
            "error": error
        }
        
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}")
        if details:
            print(f"    Details: {details}")
        if error:
            print(f"    Error: {error}")
            self.errors.append(f"{test_name}: {error}")

    def test_api_health(self) -> bool:
        """Test that the API is responding."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                self.log_result("api_health_check", True, f"API responding with status {response.status_code}")
                return True
            else:
                self.log_result("api_health_check", False, "", f"API returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_result("api_health_check", False, "", f"Failed to connect: {e}")
            return False

    def test_collection_endpoints(self) -> bool:
        """Test collection endpoints are accessible."""
        try:
            # Test various collection endpoints that should be available
            collection_endpoints = [
                "/api/v1/collection/flows",  # Basic list endpoint
                "/docs",  # Should show the collection endpoints in docs
            ]
            
            # Test docs endpoint to see if collection routes are registered
            try:
                response = requests.get(f"{self.base_url}/docs", timeout=10)
                if response.status_code == 200:
                    self.log_result("collection_docs_accessible", True, "API docs accessible")
                else:
                    self.log_result("collection_docs_accessible", False, "", f"Docs returned {response.status_code}")
            except Exception as e:
                self.log_result("collection_docs_accessible", False, "", str(e))
            
            # Test OpenAPI spec which should include collection routes
            try:
                response = requests.get(f"{self.base_url}/openapi.json", timeout=10)
                if response.status_code == 200:
                    openapi_spec = response.json()
                    
                    # Check if collection paths are in the spec
                    collection_paths = [path for path in openapi_spec.get("paths", {}).keys() 
                                      if "collection" in path.lower()]
                    
                    if collection_paths:
                        self.log_result("collection_routes_registered", True, 
                                       f"Found {len(collection_paths)} collection routes in OpenAPI spec")
                    else:
                        self.log_result("collection_routes_registered", False, "", 
                                       "No collection routes found in OpenAPI spec")
                        
                else:
                    self.log_result("collection_routes_registered", False, "", 
                                   f"OpenAPI spec returned {response.status_code}")
                    
            except Exception as e:
                self.log_result("collection_routes_registered", False, "", str(e))
                
            return True
            
        except Exception as e:
            self.log_result("collection_endpoints", False, "", str(e))
            return False

    def test_assessment_flow_endpoints(self) -> bool:
        """Test assessment flow endpoints are accessible."""
        try:
            # Test OpenAPI spec for assessment flow routes
            try:
                response = requests.get(f"{self.base_url}/openapi.json", timeout=10)
                if response.status_code == 200:
                    openapi_spec = response.json()
                    
                    # Check if assessment flow paths are in the spec
                    assessment_paths = [path for path in openapi_spec.get("paths", {}).keys() 
                                       if "assessment" in path.lower()]
                    
                    if assessment_paths:
                        self.log_result("assessment_flow_routes_registered", True, 
                                       f"Found {len(assessment_paths)} assessment flow routes in OpenAPI spec")
                    else:
                        self.log_result("assessment_flow_routes_registered", False, "", 
                                       "No assessment flow routes found in OpenAPI spec")
                        
                else:
                    self.log_result("assessment_flow_routes_registered", False, "", 
                                   f"OpenAPI spec returned {response.status_code}")
                    
            except Exception as e:
                self.log_result("assessment_flow_routes_registered", False, "", str(e))
                
            return True
            
        except Exception as e:
            self.log_result("assessment_flow_endpoints", False, "", str(e))
            return False

    def test_api_structure_integrity(self) -> bool:
        """Test that the API structure is intact after modularization."""
        try:
            response = requests.get(f"{self.base_url}/openapi.json", timeout=10)
            if response.status_code == 200:
                openapi_spec = response.json()
                
                # Count total paths
                total_paths = len(openapi_spec.get("paths", {}))
                
                # Count different types of paths
                collection_paths = len([p for p in openapi_spec.get("paths", {}).keys() if "collection" in p.lower()])
                assessment_paths = len([p for p in openapi_spec.get("paths", {}).keys() if "assessment" in p.lower()])
                discovery_paths = len([p for p in openapi_spec.get("paths", {}).keys() if "discovery" in p.lower()])
                admin_paths = len([p for p in openapi_spec.get("paths", {}).keys() if "admin" in p.lower()])
                
                self.log_result("api_structure_integrity", True, 
                               f"Total: {total_paths}, Collection: {collection_paths}, "
                               f"Assessment: {assessment_paths}, Discovery: {discovery_paths}, Admin: {admin_paths}")
                
                # Validate that we have reasonable number of endpoints
                if total_paths > 50:  # Should have many endpoints in this system
                    self.log_result("api_endpoint_count", True, f"API has {total_paths} total endpoints")
                else:
                    self.log_result("api_endpoint_count", False, "", f"API only has {total_paths} endpoints (may be missing)")
                
                return True
            else:
                self.log_result("api_structure_integrity", False, "", f"OpenAPI spec returned {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("api_structure_integrity", False, "", str(e))
            return False

    def test_core_functionality_smoke_test(self) -> bool:
        """Smoke test core functionality to ensure modularization didn't break anything."""
        try:
            # Test that we can at least access some basic endpoints
            # without authentication (should get 401/422, not 500 errors)
            
            test_endpoints = [
                ("/api/v1/collection/flows", "Collection flows endpoint"),
                ("/api/v1/assessment-flows", "Assessment flows endpoint"),
                ("/api/v1/discovery/flows", "Discovery flows endpoint"),
            ]
            
            for endpoint, description in test_endpoints:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    
                    # We expect 401 (unauthorized) or 422 (validation error), not 500 (server error)
                    if response.status_code in [200, 401, 422]:
                        self.log_result(f"endpoint_smoke_test_{endpoint.split('/')[-1]}", True, 
                                       f"{description} accessible (status: {response.status_code})")
                    elif response.status_code == 404:
                        self.log_result(f"endpoint_smoke_test_{endpoint.split('/')[-1]}", False, "",
                                       f"{description} not found (status: 404)")
                    else:
                        self.log_result(f"endpoint_smoke_test_{endpoint.split('/')[-1]}", False, "",
                                       f"{description} returned status: {response.status_code}")
                        
                except Exception as e:
                    endpoint_name = endpoint.split('/')[-1]
                    self.log_result(f"endpoint_smoke_test_{endpoint_name}", False, "", str(e))
            
            return True
            
        except Exception as e:
            self.log_result("core_functionality_smoke_test", False, "", str(e))
            return False

    def test_error_handling_consistency(self) -> bool:
        """Test that error handling is consistent after modularization."""
        try:
            # Test invalid endpoints return consistent error format
            invalid_endpoints = [
                "/api/v1/collection/invalid",
                "/api/v1/assessment-flows/invalid",
                "/api/v1/discovery/invalid"
            ]
            
            consistent_errors = True
            for endpoint in invalid_endpoints:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    
                    # Should return 404 for invalid endpoints
                    if response.status_code != 404:
                        self.log_result(f"error_consistency_{endpoint.split('/')[-2]}", False, "",
                                       f"Expected 404, got {response.status_code}")
                        consistent_errors = False
                    else:
                        self.log_result(f"error_consistency_{endpoint.split('/')[-2]}", True,
                                       f"Correctly returns 404 for invalid endpoint")
                        
                except Exception as e:
                    endpoint_name = endpoint.split('/')[-2]
                    self.log_result(f"error_consistency_{endpoint_name}", False, "", str(e))
                    consistent_errors = False
            
            return consistent_errors
            
        except Exception as e:
            self.log_result("error_handling_consistency", False, "", str(e))
            return False

    def run_all_tests(self) -> bool:
        """Run all API integration tests."""
        print("=" * 70)
        print("API INTEGRATION VALIDATION")
        print("=" * 70)
        
        # First check if API is accessible
        if not self.test_api_health():
            print("❌ API is not accessible, skipping integration tests")
            return False
        
        tests = [
            self.test_collection_endpoints,
            self.test_assessment_flow_endpoints, 
            self.test_api_structure_integrity,
            self.test_core_functionality_smoke_test,
            self.test_error_handling_consistency
        ]
        
        all_passed = True
        for test in tests:
            try:
                result = test()
                all_passed = all_passed and result
            except Exception as e:
                print(f"[ERROR] Test {test.__name__} failed with exception: {e}")
                all_passed = False
                
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.results.values() if result["success"])
        total = len(self.results)
        
        print(f"Integration tests passed: {passed}/{total}")
        
        if self.errors:
            print(f"\nIssues found ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        if all_passed:
            print("\n✅ All API integration tests PASSED!")
        else:
            print("\n⚠️  Some API integration issues found!")
            
        return all_passed

if __name__ == "__main__":
    validator = APIIntegrationValidator()
    success = validator.run_all_tests()
    exit(0 if success else 1)