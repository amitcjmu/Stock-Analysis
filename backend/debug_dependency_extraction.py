#!/usr/bin/env python3
"""
Debug script to test dependency extraction from asset data
"""
import asyncio
import sys
import os

# Add backend to path  
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.discovery_agents.dependency_intelligence_agent import DependencyIntelligenceAgent
from app.api.v1.discovery.persistence import get_processed_assets

async def test_dependency_extraction():
    """Test dependency extraction with our current asset data"""
    
    # Get assets
    assets = get_processed_assets()
    print(f"Loaded {len(assets)} assets")
    
    # Show sample asset data
    print("\n--- Sample Asset Data ---")
    for i, asset in enumerate(assets[:3]):
        asset_name = asset.get("asset_name", asset.get("hostname", "Unknown"))
        related_ci = asset.get("related_ci", "None")
        print(f"Asset {i+1}: {asset_name}")
        print(f"  Type: {asset.get('asset_type', 'Unknown')}")
        print(f"  Related CI: {related_ci}")
        print(f"  Keys: {list(asset.keys())[:10]}...")
        print()
    
    # Test dependency extraction
    agent = DependencyIntelligenceAgent()
    print("--- Testing Dependency Extraction ---")
    
    try:
        # Extract dependencies from first 5 assets
        deps = await agent._extract_dependencies_multi_source(assets[:5], {})
        print(f"Dependencies found: {len(deps)}")
        
        for i, dep in enumerate(deps[:10]):
            source = dep.get("source_asset", "Unknown")
            target = dep.get("target", "Unknown")
            dep_type = dep.get("dependency_type", "Unknown")
            confidence = dep.get("confidence", 0)
            source_name = dep.get("source_asset_name", "Unknown")
            
            print(f"  Dep {i+1}: {source_name} ({source}) -> {target}")
            print(f"    Type: {dep_type}, Confidence: {confidence:.2f}")
            print(f"    Source: {dep.get('source', 'Unknown')}")
            print()
            
        # Test full dependency analysis
        print("--- Testing Full Dependency Analysis ---")
        analysis = await agent.analyze_dependencies(assets[:10], [], {})
        
        print(f"Total dependencies: {analysis.get('dependency_analysis', {}).get('total_dependencies', 0)}")
        
        cross_app_mapping = analysis.get('cross_application_mapping', {})
        cross_app_deps = cross_app_mapping.get('cross_app_dependencies', [])
        app_clusters = cross_app_mapping.get('application_clusters', [])
        graph = cross_app_mapping.get('dependency_graph', {})
        
        print(f"Cross-app dependencies: {len(cross_app_deps)}")
        print(f"Application clusters: {len(app_clusters)}")
        print(f"Graph nodes: {len(graph.get('nodes', []))}")
        print(f"Graph edges: {len(graph.get('edges', []))}")
        
        # Show sample cross-app dependencies
        if cross_app_deps:
            print("\n--- Sample Cross-App Dependencies ---")
            for i, cross_dep in enumerate(cross_app_deps[:5]):
                source_app = cross_dep.get("source_application", "Unknown")
                target_app = cross_dep.get("target_application", "Unknown")
                impact = cross_dep.get("impact_level", "Unknown")
                print(f"  {i+1}: {source_app} -> {target_app} (Impact: {impact})")
        
    except Exception as e:
        print(f"Error during dependency extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dependency_extraction()) 