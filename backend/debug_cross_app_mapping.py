#!/usr/bin/env python3
"""Debug the cross-application mapping logic"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.discovery_agents.dependency_intelligence_agent import DependencyIntelligenceAgent
from app.api.v1.discovery.persistence import get_processed_assets
import asyncio

async def test_cross_app_mapping():
    """Test the cross-application mapping logic specifically"""
    
    # Get sample dependencies
    agent = DependencyIntelligenceAgent()
    assets = get_processed_assets()[:5]
    
    print(f"Testing with {len(assets)} assets")
    
    # Extract dependencies first
    dependencies = await agent._extract_dependencies_multi_source(assets, {})
    print(f"\nExtracted {len(dependencies)} dependencies:")
    
    for i, dep in enumerate(dependencies[:3]):
        print(f"  Dep {i+1}: {dep.get('source_asset')} -> {dep.get('target')}")
        print(f"    Type: {dep.get('dependency_type')}")
        print(f"    Source name: {dep.get('source_asset_name')}")
    
    # Test cross-application mapping with empty applications (our current case)
    print(f"\n--- Testing Cross-App Mapping (Empty Applications) ---")
    cross_mapping = await agent._map_cross_application_dependencies(dependencies, [])
    
    cross_app_deps = cross_mapping.get('cross_app_dependencies', [])
    print(f"Cross-app dependencies created: {len(cross_app_deps)}")
    
    if cross_app_deps:
        for i, cross_dep in enumerate(cross_app_deps[:3]):
            print(f"  Cross-dep {i+1}: {cross_dep.get('source_application')} -> {cross_dep.get('target_application')}")
            print(f"    Impact: {cross_dep.get('impact_level')}")
            print(f"    Type: {cross_dep.get('dependency_type')}")
            print()
    else:
        print("❌ No cross-app dependencies created!")
        print("Let me debug why...")
        
        # Debug each dependency individually
        for i, dep in enumerate(dependencies[:3]):
            source_asset = dep.get("source_asset")
            source_name = dep.get("source_asset_name", source_asset)
            target_asset = dep.get("target")
            
            print(f"\n  Debugging dependency {i+1}:")
            print(f"    source_asset: {source_asset}")
            print(f"    source_asset_name: {source_name}")
            print(f"    target: {target_asset}")
            print(f"    dependency_type: {dep.get('dependency_type')}")
            
            # Try to create cross-app dependency manually
            try:
                impact = agent._assess_cross_app_impact(dep, [])
                print(f"    Impact assessment: {impact}")
                
                cross_dep = {
                    "source_application": source_name,
                    "target_application": target_asset,
                    "dependency": dep,
                    "impact_level": impact,
                    "dependency_type": dep.get("dependency_type", "unknown"),
                    "confidence": dep.get("confidence", 0.0)
                }
                print(f"    Manual cross-dep creation: SUCCESS")
                print(f"    Result: {cross_dep.get('source_application')} -> {cross_dep.get('target_application')}")
            except Exception as e:
                print(f"    Manual cross-dep creation: FAILED - {e}")

if __name__ == "__main__":
    asyncio.run(test_cross_app_mapping()) 