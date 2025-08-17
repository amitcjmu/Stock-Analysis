#!/usr/bin/env python3
"""
Isolated modularization test that bypasses external dependencies
Tests the modularization structure without triggering dependency chains
"""

import sys
import os
import ast
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional

class ModularizationStructureValidator:
    """Validates modularization structure without importing problematic dependencies."""
    
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.errors: List[str] = []
        self.backend_path = Path(__file__).parent
        
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

    def check_file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        return (self.backend_path / path).exists()

    def analyze_imports_in_file(self, file_path: str) -> List[str]:
        """Analyze imports in a Python file using AST."""
        try:
            with open(self.backend_path / file_path, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            imports.append(f"{node.module}.{alias.name}")
            
            return imports
        except Exception as e:
            return []

    def test_collection_modularization_structure(self) -> bool:
        """Test collection endpoint modularization structure."""
        try:
            # Check main collection file exists
            main_file = "app/api/v1/endpoints/collection.py"
            if not self.check_file_exists(main_file):
                self.log_result("collection_main_file", False, "", f"Main file {main_file} not found")
                return False
            
            self.log_result("collection_main_file", True, "Main collection file exists")
            
            # Check modularized components exist
            components = [
                ("crud", "app/api/v1/endpoints/collection_crud.py"),
                ("validators", "app/api/v1/endpoints/collection_validators.py"),
                ("serializers", "app/api/v1/endpoints/collection_serializers.py"),
                ("utils", "app/api/v1/endpoints/collection_utils.py")
            ]
            
            all_exist = True
            for name, path in components:
                if self.check_file_exists(path):
                    self.log_result(f"collection_{name}_module", True, f"Module {path} exists")
                else:
                    self.log_result(f"collection_{name}_module", False, "", f"Module {path} not found")
                    all_exist = False
            
            # Check that main file imports from modular components
            imports = self.analyze_imports_in_file(main_file)
            expected_imports = [
                "app.api.v1.endpoints.collection_crud",
                "collection_crud"  # relative import
            ]
            
            has_modular_imports = any(imp in " ".join(imports) for imp in expected_imports)
            if has_modular_imports:
                self.log_result("collection_facade_imports", True, "Main file imports from modular components")
            else:
                self.log_result("collection_facade_imports", False, "", "Main file doesn't import from modular components")
                all_exist = False
                
            return all_exist
            
        except Exception as e:
            self.log_result("collection_modularization_structure", False, "", str(e))
            return False

    def test_assessment_flow_modularization_structure(self) -> bool:
        """Test assessment flow modularization structure."""
        try:
            # Check main assessment flow file exists
            main_file = "app/api/v1/endpoints/assessment_flow.py"
            if not self.check_file_exists(main_file):
                self.log_result("assessment_flow_main_file", False, "", f"Main file {main_file} not found")
                return False
            
            self.log_result("assessment_flow_main_file", True, "Main assessment flow file exists")
            
            # Check modularized components exist
            components = [
                ("crud", "app/api/v1/endpoints/assessment_flow_crud.py"),
                ("validators", "app/api/v1/endpoints/assessment_flow_validators.py"),
                ("processors", "app/api/v1/endpoints/assessment_flow_processors.py"),
                ("utils", "app/api/v1/endpoints/assessment_flow_utils.py")
            ]
            
            all_exist = True
            for name, path in components:
                if self.check_file_exists(path):
                    self.log_result(f"assessment_flow_{name}_module", True, f"Module {path} exists")
                else:
                    self.log_result(f"assessment_flow_{name}_module", False, "", f"Module {path} not found")
                    all_exist = False
                    
            return all_exist
            
        except Exception as e:
            self.log_result("assessment_flow_modularization_structure", False, "", str(e))
            return False

    def test_crewai_flow_service_modularization_structure(self) -> bool:
        """Test CrewAI flow service modularization structure."""
        try:
            # Check main service file exists
            main_file = "app/services/crewai_flow_service.py"
            if not self.check_file_exists(main_file):
                self.log_result("crewai_flow_service_main_file", False, "", f"Main file {main_file} not found")
                return False
            
            self.log_result("crewai_flow_service_main_file", True, "Main CrewAI flow service file exists")
            
            # Check modularized components exist
            components = [
                ("state_manager", "app/services/crewai_flow_state_manager.py"),
                ("executor", "app/services/crewai_flow_executor.py"),
                ("lifecycle", "app/services/crewai_flow_lifecycle.py"),
                ("monitoring", "app/services/crewai_flow_monitoring.py"),
                ("utils", "app/services/crewai_flow_utils.py")
            ]
            
            all_exist = True
            for name, path in components:
                if self.check_file_exists(path):
                    self.log_result(f"crewai_flow_{name}_module", True, f"Module {path} exists")
                else:
                    self.log_result(f"crewai_flow_{name}_module", False, "", f"Module {path} not found")
                    all_exist = False
                    
            return all_exist
            
        except Exception as e:
            self.log_result("crewai_flow_service_modularization_structure", False, "", str(e))
            return False

    def test_azure_adapter_modularization_structure(self) -> bool:
        """Test Azure adapter modularization structure."""
        try:
            # Check main adapter file exists
            main_file = "app/services/adapters/azure_adapter.py"
            if not self.check_file_exists(main_file):
                self.log_result("azure_adapter_main_file", False, "", f"Main file {main_file} not found")
                return False
            
            self.log_result("azure_adapter_main_file", True, "Main Azure adapter file exists")
            
            # Check modularized components exist
            components = [
                ("auth", "app/services/adapters/azure_adapter_auth.py"),
                ("storage", "app/services/adapters/azure_adapter_storage.py"),
                ("compute", "app/services/adapters/azure_adapter_compute.py"),
                ("data", "app/services/adapters/azure_adapter_data.py"),
                ("utils", "app/services/adapters/azure_adapter_utils.py")
            ]
            
            all_exist = True
            for name, path in components:
                if self.check_file_exists(path):
                    self.log_result(f"azure_adapter_{name}_module", True, f"Module {path} exists")
                else:
                    self.log_result(f"azure_adapter_{name}_module", False, "", f"Module {path} not found")
                    all_exist = False
                    
            return all_exist
            
        except Exception as e:
            self.log_result("azure_adapter_modularization_structure", False, "", str(e))
            return False

    def test_facade_pattern_implementation(self) -> bool:
        """Test that facade pattern is properly implemented."""
        try:
            facade_tests = []
            
            # Test collection facade
            collection_file = "app/api/v1/endpoints/collection.py"
            if self.check_file_exists(collection_file):
                imports = self.analyze_imports_in_file(collection_file)
                has_crud_import = any("collection_crud" in imp for imp in imports)
                facade_tests.append(("collection_facade", has_crud_import))
                
            # Test CrewAI service facade  
            crewai_file = "app/services/crewai_flow_service.py"
            if self.check_file_exists(crewai_file):
                imports = self.analyze_imports_in_file(crewai_file)
                has_modular_imports = any(
                    any(comp in imp for comp in ["state_manager", "executor", "lifecycle", "monitoring", "utils"])
                    for imp in imports
                )
                facade_tests.append(("crewai_service_facade", has_modular_imports))
                
            # Test Azure adapter facade
            azure_file = "app/services/adapters/azure_adapter.py" 
            if self.check_file_exists(azure_file):
                imports = self.analyze_imports_in_file(azure_file)
                has_modular_imports = any(
                    any(comp in imp for comp in ["azure_adapter_auth", "azure_adapter_storage", "azure_adapter_compute"])
                    for imp in imports
                )
                facade_tests.append(("azure_adapter_facade", has_modular_imports))
            
            all_facades_good = True
            for name, result in facade_tests:
                if result:
                    self.log_result(f"{name}_pattern", True, "Facade pattern implemented")
                else:
                    self.log_result(f"{name}_pattern", False, "", "Facade pattern not properly implemented")
                    all_facades_good = False
                    
            return all_facades_good
            
        except Exception as e:
            self.log_result("facade_pattern_implementation", False, "", str(e))
            return False

    def test_modular_component_content(self) -> bool:
        """Test that modular components have meaningful content."""
        try:
            components_to_check = [
                "app/api/v1/endpoints/collection_crud.py",
                "app/api/v1/endpoints/assessment_flow_crud.py",
                "app/services/crewai_flow_state_manager.py",
                "app/services/crewai_flow_executor.py",
                "app/services/adapters/azure_adapter_auth.py"
            ]
            
            all_have_content = True
            for component in components_to_check:
                if self.check_file_exists(component):
                    try:
                        with open(self.backend_path / component, 'r') as f:
                            content = f.read().strip()
                            
                        # Check if file has meaningful content (not just imports and comments)
                        lines = [line.strip() for line in content.split('\n') if line.strip()]
                        non_trivial_lines = [
                            line for line in lines 
                            if not line.startswith(('#', '"""', "'''", 'import', 'from'))
                            and line not in ['', '"""', "'''"]
                        ]
                        
                        if len(non_trivial_lines) > 5:  # At least some substantial content
                            self.log_result(f"{component.split('/')[-1]}_content", True, f"Has {len(non_trivial_lines)} lines of code")
                        else:
                            self.log_result(f"{component.split('/')[-1]}_content", False, "", f"Only {len(non_trivial_lines)} lines of code")
                            all_have_content = False
                            
                    except Exception as e:
                        self.log_result(f"{component.split('/')[-1]}_content", False, "", f"Error reading file: {e}")
                        all_have_content = False
                else:
                    self.log_result(f"{component.split('/')[-1]}_content", False, "", "File does not exist")
                    all_have_content = False
                    
            return all_have_content
            
        except Exception as e:
            self.log_result("modular_component_content", False, "", str(e))
            return False

    def run_all_tests(self) -> bool:
        """Run all structure validation tests."""
        print("=" * 70)
        print("MODULARIZATION STRUCTURE VALIDATION")
        print("=" * 70)
        
        tests = [
            self.test_collection_modularization_structure,
            self.test_assessment_flow_modularization_structure,
            self.test_crewai_flow_service_modularization_structure,
            self.test_azure_adapter_modularization_structure,
            self.test_facade_pattern_implementation,
            self.test_modular_component_content
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
        
        print(f"Structure tests passed: {passed}/{total}")
        
        if self.errors:
            print(f"\nIssues found ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        if all_passed:
            print("\n✅ All modularization structure tests PASSED!")
        else:
            print("\n⚠️  Some modularization structure issues found!")
            
        return all_passed

if __name__ == "__main__":
    validator = ModularizationStructureValidator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)