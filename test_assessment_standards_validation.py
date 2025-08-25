#!/usr/bin/env python3
"""
Comprehensive validation test for modularized assessment_standards.py
This test verifies that the modularization was successful and all functionality is preserved.
"""

import sys
import os
import traceback
from typing import Dict, List, Any, Optional

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test that all imports work correctly without circular dependencies."""
    print("Testing imports...")
    try:
        # Test individual module imports
        from app.core.seed_data.standards.technology_versions import TECH_VERSION_STANDARDS
        from app.core.seed_data.standards.security_compliance import SECURITY_STANDARDS
        from app.core.seed_data.standards.architecture_patterns import ARCHITECTURE_STANDARDS
        from app.core.seed_data.standards.cloud_native import CLOUD_NATIVE_STANDARDS
        
        # Test main module imports
        from app.core.seed_data.assessment_standards import (
            get_default_standards,
            get_standards_by_type,
            validate_technology_compliance
        )
        
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_data_structure_integrity():
    """Test that all data structures are preserved and complete."""
    print("\nTesting data structure integrity...")
    try:
        from app.core.seed_data.standards.technology_versions import TECH_VERSION_STANDARDS
        from app.core.seed_data.standards.security_compliance import SECURITY_STANDARDS
        from app.core.seed_data.standards.architecture_patterns import ARCHITECTURE_STANDARDS
        from app.core.seed_data.standards.cloud_native import CLOUD_NATIVE_STANDARDS
        
        # Test that all lists exist and contain data
        assert isinstance(TECH_VERSION_STANDARDS, list), "TECH_VERSION_STANDARDS should be a list"
        assert len(TECH_VERSION_STANDARDS) > 0, "TECH_VERSION_STANDARDS should not be empty"
        
        assert isinstance(SECURITY_STANDARDS, list), "SECURITY_STANDARDS should be a list"
        assert len(SECURITY_STANDARDS) > 0, "SECURITY_STANDARDS should not be empty"
        
        assert isinstance(ARCHITECTURE_STANDARDS, list), "ARCHITECTURE_STANDARDS should be a list"
        assert len(ARCHITECTURE_STANDARDS) > 0, "ARCHITECTURE_STANDARDS should not be empty"
        
        assert isinstance(CLOUD_NATIVE_STANDARDS, list), "CLOUD_NATIVE_STANDARDS should be a list"
        assert len(CLOUD_NATIVE_STANDARDS) > 0, "CLOUD_NATIVE_STANDARDS should not be empty"
        
        # Test data structure of individual standards
        all_standards = TECH_VERSION_STANDARDS + SECURITY_STANDARDS + ARCHITECTURE_STANDARDS + CLOUD_NATIVE_STANDARDS
        
        required_fields = ["requirement_type", "description", "mandatory"]
        
        for i, standard in enumerate(all_standards):
            assert isinstance(standard, dict), f"Standard {i} should be a dictionary"
            
            for field in required_fields:
                assert field in standard, f"Standard {i} missing required field: {field}"
            
            # Test that requirement_type is a string
            assert isinstance(standard["requirement_type"], str), f"Standard {i} requirement_type should be string"
            assert len(standard["requirement_type"]) > 0, f"Standard {i} requirement_type should not be empty"
            
            # Test that description is a string
            assert isinstance(standard["description"], str), f"Standard {i} description should be string"
            assert len(standard["description"]) > 0, f"Standard {i} description should not be empty"
            
            # Test that mandatory is a boolean
            assert isinstance(standard["mandatory"], bool), f"Standard {i} mandatory should be boolean"
        
        print(f"✅ Data structure integrity validated for {len(all_standards)} standards")
        return True
        
    except Exception as e:
        print(f"❌ Data structure integrity test failed: {e}")
        traceback.print_exc()
        return False

def test_function_availability():
    """Test that all expected functions are available and working."""
    print("\nTesting function availability...")
    try:
        from app.core.seed_data.assessment_standards import (
            get_default_standards,
            get_standards_by_type,
            validate_technology_compliance
        )
        
        # Test get_default_standards
        default_standards = get_default_standards()
        assert isinstance(default_standards, dict), "get_default_standards should return a dict"
        
        expected_categories = ["technology_versions", "security_compliance", "architecture_patterns", "cloud_native"]
        for category in expected_categories:
            assert category in default_standards, f"Missing category: {category}"
            assert isinstance(default_standards[category], list), f"Category {category} should be a list"
            assert len(default_standards[category]) > 0, f"Category {category} should not be empty"
        
        # Test get_standards_by_type
        java_standard = get_standards_by_type("java_versions")
        assert java_standard is not None, "Should find java_versions standard"
        assert java_standard["requirement_type"] == "java_versions", "Should return correct standard"
        
        nonexistent_standard = get_standards_by_type("nonexistent_type")
        assert nonexistent_standard is None, "Should return None for nonexistent type"
        
        # Test validate_technology_compliance
        test_tech_stack = {
            "java": "11",
            "spring_boot": "2.5.0"
        }
        test_standards = [java_standard] if java_standard else []
        
        validation_result = validate_technology_compliance(test_tech_stack, test_standards)
        assert isinstance(validation_result, dict), "validate_technology_compliance should return a dict"
        
        expected_fields = ["compliant", "issues", "recommendations", "exceptions_needed"]
        for field in expected_fields:
            assert field in validation_result, f"Validation result missing field: {field}"
        
        print("✅ All functions are available and working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Function availability test failed: {e}")
        traceback.print_exc()
        return False

def test_specific_standard_types():
    """Test that specific standard types exist and have expected content."""
    print("\nTesting specific standard types...")
    try:
        from app.core.seed_data.assessment_standards import get_standards_by_type
        
        # Test expected standard types
        expected_types = [
            "java_versions",
            "dotnet_versions", 
            "python_versions",
            "nodejs_versions",
            "authentication",
            "data_encryption",
            "api_security",
            "containerization",
            "api_design",
            "microservices_architecture",
            "observability",
            "scalability",
            "disaster_recovery"
        ]
        
        found_types = []
        missing_types = []
        
        for standard_type in expected_types:
            standard = get_standards_by_type(standard_type)
            if standard:
                found_types.append(standard_type)
                
                # Validate structure for technology version standards
                if standard_type.endswith("_versions"):
                    assert "supported_versions" in standard, f"{standard_type} should have supported_versions"
                    if standard["supported_versions"]:
                        assert isinstance(standard["supported_versions"], dict), f"{standard_type} supported_versions should be dict"
                
                # Validate requirement_details exist
                if "requirement_details" in standard:
                    assert isinstance(standard["requirement_details"], dict), f"{standard_type} requirement_details should be dict"
                    
            else:
                missing_types.append(standard_type)
        
        print(f"✅ Found {len(found_types)} expected standard types: {found_types}")
        
        if missing_types:
            print(f"⚠️  Missing standard types: {missing_types}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Specific standard types test failed: {e}")
        traceback.print_exc()
        return False

def test_data_completeness():
    """Test that data completeness is maintained after modularization."""
    print("\nTesting data completeness...")
    try:
        from app.core.seed_data.assessment_standards import get_default_standards
        
        all_standards = get_default_standards()
        total_standards = sum(len(standards) for standards in all_standards.values())
        
        print(f"Total standards found: {total_standards}")
        
        # Verify we have a reasonable number of standards (based on what we saw in the files)
        assert total_standards >= 13, f"Expected at least 13 standards, found {total_standards}"
        
        # Check category distribution
        for category, standards in all_standards.items():
            print(f"  {category}: {len(standards)} standards")
            assert len(standards) > 0, f"Category {category} should have at least one standard"
        
        print("✅ Data completeness validated")
        return True
        
    except Exception as e:
        print(f"❌ Data completeness test failed: {e}")
        traceback.print_exc()
        return False

def test_version_compliance_logic():
    """Test the version compliance logic works correctly."""
    print("\nTesting version compliance logic...")
    try:
        from app.core.seed_data.assessment_standards import _is_version_compliant
        
        # Test exact version matching
        assert _is_version_compliant("11", "11") == True, "Exact version should match"
        assert _is_version_compliant("10", "11") == False, "Different version should not match"
        
        # Test minimum version matching (with + suffix)
        assert _is_version_compliant("11", "11+") == True, "Version 11 should meet 11+ requirement"
        assert _is_version_compliant("12", "11+") == True, "Version 12 should meet 11+ requirement"
        assert _is_version_compliant("10", "11+") == False, "Version 10 should not meet 11+ requirement"
        
        print("✅ Version compliance logic working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Version compliance logic test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all validation tests."""
    print("=" * 60)
    print("ASSESSMENT STANDARDS MODULARIZATION VALIDATION")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_data_structure_integrity,
        test_function_availability,
        test_specific_standard_types,
        test_data_completeness,
        test_version_compliance_logic
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    print(f"Total tests: {passed + failed}")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED - Modularization successful!")
        return True
    else:
        print(f"❌ {failed} TESTS FAILED - Issues detected in modularization")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)