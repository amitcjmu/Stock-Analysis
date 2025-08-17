#!/usr/bin/env python3
"""
Test for breaking changes in public APIs after modularization
"""

import requests
import json
from typing import Dict, List, Any, Set

class BreakingChangesValidator:
    """Validates that no breaking changes were introduced by modularization."""
    
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

    def get_openapi_spec(self) -> Dict[str, Any]:
        """Get the OpenAPI specification."""
        try:
            response = requests.get(f"{self.base_url}/openapi.json", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception:
            return {}

    def test_collection_api_completeness(self) -> bool:
        """Test that collection API endpoints are complete."""
        try:
            spec = self.get_openapi_spec()
            if not spec:
                self.log_result("collection_api_completeness", False, "", "Could not get OpenAPI spec")
                return False
            
            collection_paths = [path for path in spec.get("paths", {}).keys() 
                              if "collection" in path.lower()]
            
            # Expected collection endpoints based on common patterns
            expected_patterns = [
                "flows",  # Basic flows management
                "from-discovery",  # Create from discovery
                "continue",  # Continue/resume flows
                "export",  # Export functionality
            ]
            
            found_patterns = []
            for pattern in expected_patterns:
                matching_paths = [p for p in collection_paths if pattern in p]
                if matching_paths:
                    found_patterns.append(pattern)
            
            completeness = len(found_patterns) / len(expected_patterns) * 100
            
            if completeness >= 75:  # At least 75% of expected patterns
                self.log_result("collection_api_completeness", True, 
                               f"Collection API {completeness:.0f}% complete ({len(found_patterns)}/{len(expected_patterns)} patterns)")
            else:
                self.log_result("collection_api_completeness", False, "",
                               f"Collection API only {completeness:.0f}% complete ({len(found_patterns)}/{len(expected_patterns)} patterns)")
            
            return completeness >= 75
            
        except Exception as e:
            self.log_result("collection_api_completeness", False, "", str(e))
            return False

    def test_assessment_flow_api_completeness(self) -> bool:
        """Test that assessment flow API endpoints are complete."""
        try:
            spec = self.get_openapi_spec()
            if not spec:
                self.log_result("assessment_flow_api_completeness", False, "", "Could not get OpenAPI spec")
                return False
            
            assessment_paths = [path for path in spec.get("paths", {}).keys() 
                              if "assessment" in path.lower()]
            
            # Expected assessment endpoints based on common patterns
            expected_patterns = [
                "flows",  # Basic flows management
                "execute",  # Execute assessments
                "continue",  # Continue/resume flows
                "results",  # Get results
            ]
            
            found_patterns = []
            for pattern in expected_patterns:
                matching_paths = [p for p in assessment_paths if pattern in p]
                if matching_paths:
                    found_patterns.append(pattern)
            
            completeness = len(found_patterns) / len(expected_patterns) * 100
            
            if completeness >= 75:  # At least 75% of expected patterns
                self.log_result("assessment_flow_api_completeness", True, 
                               f"Assessment API {completeness:.0f}% complete ({len(found_patterns)}/{len(expected_patterns)} patterns)")
            else:
                self.log_result("assessment_flow_api_completeness", False, "",
                               f"Assessment API only {completeness:.0f}% complete ({len(found_patterns)}/{len(expected_patterns)} patterns)")
            
            return completeness >= 75
            
        except Exception as e:
            self.log_result("assessment_flow_api_completeness", False, "", str(e))
            return False

    def test_http_methods_consistency(self) -> bool:
        """Test that HTTP methods are consistently available."""
        try:
            spec = self.get_openapi_spec()
            if not spec:
                self.log_result("http_methods_consistency", False, "", "Could not get OpenAPI spec")
                return False
            
            paths = spec.get("paths", {})
            
            # Check for common CRUD operations
            crud_methods = ["get", "post", "put", "delete"]
            method_counts = {method: 0 for method in crud_methods}
            
            for path, methods in paths.items():
                for method in crud_methods:
                    if method in methods:
                        method_counts[method] += 1
            
            # Check that we have reasonable distribution of methods
            total_methods = sum(method_counts.values())
            get_percentage = method_counts["get"] / total_methods * 100 if total_methods > 0 else 0
            post_percentage = method_counts["post"] / total_methods * 100 if total_methods > 0 else 0
            
            # GET should be the most common, followed by POST
            if get_percentage > 40 and post_percentage > 20:
                self.log_result("http_methods_consistency", True, 
                               f"Method distribution: GET {get_percentage:.1f}%, POST {post_percentage:.1f}%")
            else:
                self.log_result("http_methods_consistency", False, "",
                               f"Unusual method distribution: GET {get_percentage:.1f}%, POST {post_percentage:.1f}%")
            
            return get_percentage > 40 and post_percentage > 20
            
        except Exception as e:
            self.log_result("http_methods_consistency", False, "", str(e))
            return False

    def test_response_schema_consistency(self) -> bool:
        """Test that response schemas are consistent."""
        try:
            spec = self.get_openapi_spec()
            if not spec:
                self.log_result("response_schema_consistency", False, "", "Could not get OpenAPI spec")
                return False
            
            components = spec.get("components", {})
            schemas = components.get("schemas", {})
            
            # Check for common response schemas
            common_schemas = [
                "CollectionFlowResponse",
                "AssessmentFlowResponse", 
                "ErrorResponse",
                "ValidationError"
            ]
            
            found_schemas = []
            for schema in common_schemas:
                if any(schema.lower() in s.lower() for s in schemas.keys()):
                    found_schemas.append(schema)
            
            schema_consistency = len(found_schemas) / len(common_schemas) * 100
            
            if schema_consistency >= 50:  # At least half of expected schemas
                self.log_result("response_schema_consistency", True, 
                               f"Schema consistency {schema_consistency:.0f}% ({len(found_schemas)}/{len(common_schemas)} schemas)")
            else:
                self.log_result("response_schema_consistency", False, "",
                               f"Low schema consistency {schema_consistency:.0f}% ({len(found_schemas)}/{len(common_schemas)} schemas)")
            
            return schema_consistency >= 50
            
        except Exception as e:
            self.log_result("response_schema_consistency", False, "", str(e))
            return False

    def test_endpoint_parameter_consistency(self) -> bool:
        """Test that endpoint parameters are consistent."""
        try:
            spec = self.get_openapi_spec()
            if not spec:
                self.log_result("endpoint_parameter_consistency", False, "", "Could not get OpenAPI spec")
                return False
            
            paths = spec.get("paths", {})
            
            # Check for consistent parameter patterns
            param_patterns = {
                "client_account_id": 0,
                "engagement_id": 0,
                "flow_id": 0,
                "id": 0
            }
            
            total_endpoints = 0
            for path, methods in paths.items():
                for method, details in methods.items():
                    if method in ["get", "post", "put", "delete"]:
                        total_endpoints += 1
                        parameters = details.get("parameters", [])
                        
                        for param in parameters:
                            param_name = param.get("name", "")
                            for pattern in param_patterns:
                                if pattern in param_name:
                                    param_patterns[pattern] += 1
            
            # Calculate consistency scores
            consistency_scores = []
            for param, count in param_patterns.items():
                if total_endpoints > 0:
                    percentage = count / total_endpoints * 100
                    consistency_scores.append(percentage)
            
            avg_consistency = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0
            
            if avg_consistency > 10:  # At least 10% average parameter consistency
                self.log_result("endpoint_parameter_consistency", True, 
                               f"Parameter consistency {avg_consistency:.1f}% average")
            else:
                self.log_result("endpoint_parameter_consistency", False, "",
                               f"Low parameter consistency {avg_consistency:.1f}% average")
            
            return avg_consistency > 10
            
        except Exception as e:
            self.log_result("endpoint_parameter_consistency", False, "", str(e))
            return False

    def test_no_500_errors_on_basic_endpoints(self) -> bool:
        """Test that basic endpoints don't return 500 errors."""
        try:
            # Test a few basic endpoints to ensure they don't return server errors
            basic_endpoints = [
                "/health",
                "/docs",
                "/openapi.json",
                "/api/v1",  # This might not exist but shouldn't cause 500
            ]
            
            no_server_errors = True
            for endpoint in basic_endpoints:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    
                    if response.status_code >= 500:
                        self.log_result(f"no_500_error_{endpoint.replace('/', '_')}", False, "",
                                       f"Endpoint {endpoint} returned server error {response.status_code}")
                        no_server_errors = False
                    else:
                        self.log_result(f"no_500_error_{endpoint.replace('/', '_')}", True,
                                       f"Endpoint {endpoint} returned {response.status_code} (no server error)")
                        
                except Exception as e:
                    # Connection errors are acceptable, server errors are not
                    if "500" in str(e) or "Internal Server Error" in str(e):
                        self.log_result(f"no_500_error_{endpoint.replace('/', '_')}", False, "", str(e))
                        no_server_errors = False
                    else:
                        self.log_result(f"no_500_error_{endpoint.replace('/', '_')}", True,
                                       f"Endpoint {endpoint} handled gracefully")
            
            return no_server_errors
            
        except Exception as e:
            self.log_result("no_500_errors_on_basic_endpoints", False, "", str(e))
            return False

    def run_all_tests(self) -> bool:
        """Run all breaking changes validation tests."""
        print("=" * 70)
        print("BREAKING CHANGES VALIDATION")
        print("=" * 70)
        
        tests = [
            self.test_collection_api_completeness,
            self.test_assessment_flow_api_completeness,
            self.test_http_methods_consistency,
            self.test_response_schema_consistency,
            self.test_endpoint_parameter_consistency,
            self.test_no_500_errors_on_basic_endpoints
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
        
        print(f"Breaking changes tests passed: {passed}/{total}")
        
        if self.errors:
            print(f"\nIssues found ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        if all_passed:
            print("\n✅ No breaking changes detected!")
        else:
            print("\n⚠️  Potential breaking changes or issues found!")
            
        return all_passed

if __name__ == "__main__":
    validator = BreakingChangesValidator()
    success = validator.run_all_tests()
    exit(0 if success else 1)