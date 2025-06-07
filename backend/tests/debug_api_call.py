#!/usr/bin/env python3
"""Debug the exact API call to see what's happening"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.discovery_agents.dependency_intelligence_agent import DependencyIntelligenceAgent
from app.api.v1.discovery.persistence import get_processed_assets
import asyncio

async def debug_api_call():
    """Debug the exact same call that the API makes"""
    
    # Initialize agent (same as API)
    from app.api.v1.endpoints.agent_discovery import dependency_intelligence_agent
    
    # Get assets (same as API)
    assets = get_processed_assets()
    applications = []
    user_context = {
        'analysis_type': 'comprehensive',
        'include_cross_app_mapping': True,
        'include_impact_analysis': True
    }
    
    print(f"API-style call with {len(assets)} assets")
    print(f"User context: {user_context}")
    
    # Call the agent exactly like the API does
    dependency_intelligence = await dependency_intelligence_agent.analyze_dependencies(
        assets, applications, user_context
    )
    
    print(f"\n--- API Response Structure ---")
    print(f"Keys: {list(dependency_intelligence.keys())}")
    
    # Check dependency analysis
    dep_analysis = dependency_intelligence.get('dependency_analysis', {})
    print(f"\nDependency Analysis:")
    print(f"  Total dependencies: {dep_analysis.get('total_dependencies', 0)}")
    
    # Check cross-application mapping
    cross_mapping = dependency_intelligence.get('cross_application_mapping', {})
    print(f"\nCross Application Mapping:")
    print(f"  Keys: {list(cross_mapping.keys())}")
    
    cross_app_deps = cross_mapping.get('cross_app_dependencies', [])
    print(f"  Cross-app dependencies: {len(cross_app_deps)}")
    
    if cross_app_deps:
        print(f"  Sample cross-app deps:")
        for i, dep in enumerate(cross_app_deps[:3]):
            print(f"    {i+1}: {dep.get('source_application')} -> {dep.get('target_application')} (Impact: {dep.get('impact_level')})")
    else:
        print(f"  ❌ NO CROSS-APP DEPENDENCIES FOUND!")
        
        # Debug the mapping structure
        print(f"\n  Debugging cross_mapping structure:")
        for key, value in cross_mapping.items():
            if isinstance(value, list):
                print(f"    {key}: list with {len(value)} items")
            elif isinstance(value, dict):
                print(f"    {key}: dict with keys {list(value.keys())}")
            else:
                print(f"    {key}: {type(value)} = {value}")
    
    # Check application clusters
    app_clusters = cross_mapping.get('application_clusters', [])
    print(f"  Application clusters: {len(app_clusters)}")
    
    # Check dependency graph
    dep_graph = cross_mapping.get('dependency_graph', {})
    nodes = dep_graph.get('nodes', [])
    edges = dep_graph.get('edges', [])
    print(f"  Dependency graph: {len(nodes)} nodes, {len(edges)} edges")

if __name__ == "__main__":
    asyncio.run(debug_api_call()) 