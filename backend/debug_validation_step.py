#!/usr/bin/env python3
"""Debug the validation step to see if it's filtering out dependencies"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.discovery_agents.dependency_intelligence_agent import DependencyIntelligenceAgent
from app.api.v1.discovery.persistence import get_processed_assets
import asyncio

async def test_validation_step():
    """Test the validation step to see if it's filtering out dependencies"""
    
    agent = DependencyIntelligenceAgent()
    assets = get_processed_assets()[:5]
    
    print(f"Testing validation with {len(assets)} assets")
    
    # Step 1: Extract dependencies
    dependencies = await agent._extract_dependencies_multi_source(assets, {})
    print(f"\nStep 1 - Extracted dependencies: {len(dependencies)}")
    
    for i, dep in enumerate(dependencies[:3]):
        print(f"  Dep {i+1}: {dep.get('source_asset')} -> {dep.get('target')} (confidence: {dep.get('confidence')})")
    
    # Step 2: Validate dependencies
    print(f"\n--- Step 2: Validation ---")
    validated_dependencies = await agent._validate_and_resolve_conflicts(dependencies)
    print(f"Validated dependencies: {len(validated_dependencies)}")
    
    if len(validated_dependencies) != len(dependencies):
        print(f"❌ ISSUE FOUND: {len(dependencies) - len(validated_dependencies)} dependencies were filtered out during validation!")
        
        # Find which dependencies were filtered out
        validated_ids = set(dep.get('id') for dep in validated_dependencies)
        original_ids = set(dep.get('id') for dep in dependencies)
        filtered_out_ids = original_ids - validated_ids
        
        print(f"Filtered out dependency IDs: {filtered_out_ids}")
        
        # Show why they were filtered
        for dep in dependencies:
            if dep.get('id') in filtered_out_ids:
                is_valid = agent._validate_single_dependency(dep)
                print(f"  Dependency {dep.get('id')}: {dep.get('source_asset')} -> {dep.get('target')}")
                print(f"    Valid: {is_valid}")
                print(f"    Required fields: source_asset={bool(dep.get('source_asset'))}, target={bool(dep.get('target'))}, dependency_type={bool(dep.get('dependency_type'))}")
                print(f"    Confidence: {dep.get('confidence', 0)} (threshold: 0.3)")
    else:
        print("✅ All dependencies passed validation")
        
        for i, dep in enumerate(validated_dependencies[:3]):
            print(f"  Validated Dep {i+1}: {dep.get('source_asset')} -> {dep.get('target')}")
    
    # Step 3: Cross-app mapping (with validated dependencies)
    print(f"\n--- Step 3: Cross-App Mapping ---")
    cross_mapping = await agent._map_cross_application_dependencies(validated_dependencies, [])
    cross_app_deps = cross_mapping.get('cross_app_dependencies', [])
    print(f"Cross-app dependencies: {len(cross_app_deps)}")
    
    if len(cross_app_deps) != len(validated_dependencies):
        print(f"❌ ISSUE: Expected {len(validated_dependencies)} cross-app deps, got {len(cross_app_deps)}")
    else:
        print("✅ Cross-app mapping working correctly")

if __name__ == "__main__":
    asyncio.run(test_validation_step()) 