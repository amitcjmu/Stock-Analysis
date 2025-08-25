#!/usr/bin/env python3
"""
Test database initialization flow for assessment standards.
This test validates that the initialize_assessment_standards function works correctly with the database.
"""

import sys
import os
import asyncio
import traceback
from typing import Dict, List, Any, Optional
from uuid import uuid4

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_initialize_assessment_standards():
    """Test the initialize_assessment_standards function with mock database."""
    print("Testing initialize_assessment_standards function...")
    
    try:
        from app.core.seed_data.assessment_standards import initialize_assessment_standards
        
        # Create a mock database session that doesn't require actual DB connection
        class MockEngagement:
            def __init__(self):
                self.id = uuid4()
                self.client_account_id = uuid4()
        
        class MockResult:
            def scalar_one_or_none(self):
                return MockEngagement()
            
            def first(self):
                return None  # No existing standards
        
        class MockSession:
            def __init__(self):
                self.added_records = []
                self.committed = False
                self.rolled_back = False
            
            async def execute(self, query):
                return MockResult()
                
            def add(self, record):
                self.added_records.append(record)
                
            async def commit(self):
                self.committed = True
                
            async def rollback(self):
                self.rolled_back = True
        
        # Create mock session
        mock_db = MockSession()
        test_engagement_id = str(uuid4())
        
        # Test the function call - this should work without actual database
        try:
            await initialize_assessment_standards(mock_db, test_engagement_id)
            
            # Check that records were added
            assert len(mock_db.added_records) > 0, "Should have added standards records"
            assert mock_db.committed, "Should have committed the transaction"
            assert not mock_db.rolled_back, "Should not have rolled back"
            
            print(f"✅ initialize_assessment_standards added {len(mock_db.added_records)} standards records")
            
            # Validate the structure of added records
            for i, record in enumerate(mock_db.added_records[:3]):  # Check first 3
                # Check that the record has the expected attributes
                assert hasattr(record, 'engagement_id'), f"Record {i} should have engagement_id"
                assert hasattr(record, 'client_account_id'), f"Record {i} should have client_account_id"
                assert hasattr(record, 'requirement_type'), f"Record {i} should have requirement_type"
                assert hasattr(record, 'standard_name'), f"Record {i} should have standard_name"
                assert hasattr(record, 'description'), f"Record {i} should have description"
                assert hasattr(record, 'is_mandatory'), f"Record {i} should have is_mandatory"
                
                # Check field types
                assert isinstance(record.requirement_type, str), f"Record {i} requirement_type should be string"
                assert isinstance(record.description, str), f"Record {i} description should be string"
                assert isinstance(record.is_mandatory, bool), f"Record {i} is_mandatory should be boolean"
            
            print("✅ All record structures are valid")
            return True
            
        except Exception as e:
            print(f"❌ initialize_assessment_standards failed: {e}")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        traceback.print_exc()
        return False

async def test_standards_data_consistency():
    """Test that all standards data is consistent and complete."""
    print("\nTesting standards data consistency...")
    
    try:
        from app.core.seed_data.assessment_standards import get_default_standards
        
        all_standards = get_default_standards()
        
        # Check that all categories have standards
        for category, standards in all_standards.items():
            assert len(standards) > 0, f"Category {category} should have standards"
            
            # Check each standard has required fields
            for i, standard in enumerate(standards):
                required_fields = ["requirement_type", "description", "mandatory"]
                for field in required_fields:
                    assert field in standard, f"Standard {i} in {category} missing field: {field}"
                    
                # Check that requirement_type is unique within category
                requirement_types = [s["requirement_type"] for s in standards]
                assert len(requirement_types) == len(set(requirement_types)), f"Duplicate requirement_types in {category}"
        
        # Check that requirement_types are globally unique
        all_requirement_types = []
        for standards in all_standards.values():
            all_requirement_types.extend([s["requirement_type"] for s in standards])
        
        assert len(all_requirement_types) == len(set(all_requirement_types)), "Duplicate requirement_types across categories"
        
        print(f"✅ Data consistency validated for {len(all_requirement_types)} standards across {len(all_standards)} categories")
        return True
        
    except Exception as e:
        print(f"❌ Data consistency test failed: {e}")
        traceback.print_exc()
        return False

async def test_model_compatibility():
    """Test that the standards data is compatible with the database model."""
    print("\nTesting model compatibility...")
    
    try:
        from app.models.assessment_flow import EngagementArchitectureStandard
        from app.core.seed_data.assessment_standards import get_default_standards
        from uuid import uuid4
        
        all_standards = get_default_standards()
        
        # Test creating model instances with the standards data
        test_engagement_id = uuid4()
        test_client_account_id = uuid4()
        
        created_models = []
        for category, standards in all_standards.items():
            for standard in standards:
                try:
                    # Create model instance like the initialize function does
                    standard_record = EngagementArchitectureStandard(
                        engagement_id=test_engagement_id,
                        client_account_id=test_client_account_id,
                        requirement_type=standard["requirement_type"],
                        standard_name=standard.get("standard_name", standard["requirement_type"]),
                        description=standard["description"],
                        is_mandatory=standard["mandatory"],
                        minimum_requirements=standard.get("requirement_details", {}),
                        preferred_patterns=standard.get("supported_versions", {}),
                        priority=standard.get("priority", 5),
                        business_impact=standard.get("business_impact", "medium"),
                    )
                    created_models.append(standard_record)
                    
                except Exception as e:
                    print(f"❌ Failed to create model for {standard['requirement_type']}: {e}")
                    return False
        
        print(f"✅ Successfully created {len(created_models)} model instances")
        
        # Test that all required fields are populated
        for model in created_models[:3]:  # Check first 3
            assert model.engagement_id is not None, "engagement_id should be set"
            assert model.client_account_id is not None, "client_account_id should be set"
            assert model.requirement_type, "requirement_type should be non-empty"
            assert model.standard_name, "standard_name should be non-empty"
            assert model.description, "description should be non-empty"
            assert isinstance(model.is_mandatory, bool), "is_mandatory should be boolean"
            
        print("✅ Model field validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Model compatibility test failed: {e}")
        traceback.print_exc()
        return False

async def main():
    """Run all database initialization tests."""
    print("=" * 60)
    print("DATABASE INITIALIZATION VALIDATION")
    print("=" * 60)
    
    tests = [
        test_initialize_assessment_standards,
        test_standards_data_consistency,
        test_model_compatibility
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if await test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print("DATABASE INITIALIZATION SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    print(f"Total tests: {passed + failed}")
    
    if failed == 0:
        print("🎉 ALL DATABASE TESTS PASSED - Database initialization working correctly!")
        return True
    else:
        print(f"❌ {failed} DATABASE TESTS FAILED - Issues detected")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)