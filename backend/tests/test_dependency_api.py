#!/usr/bin/env python3
"""Test dependency analysis API endpoint"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import json

import requests

from app.api.v1.discovery.persistence import get_processed_assets


def test_dependency_api():
    assets = get_processed_assets()[:5]
    print(f'Testing dependency API with {len(assets)} assets')
    
    # Show sample asset for debugging
    print(f'Sample asset: {assets[0].get("asset_name")} has related_ci: {assets[0].get("related_ci")}')
    
    payload = {
        'assets': assets,
        'applications': [],
        'user_context': {'analysis_type': 'comprehensive'}
    }
    
    try:
        response = requests.post('http://localhost:8000/api/v1/discovery/agents/dependency-analysis', 
                                json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            result = response.json()
            print(f'API Response status: {response.status_code}')
            
            # Check the structure
            print(f'Response keys: {list(result.keys())}')
            
            if 'dependency_intelligence' in result:
                dep_intel = result['dependency_intelligence']
                cross_mapping = dep_intel.get('cross_application_mapping', {})
                deps = cross_mapping.get('cross_app_dependencies', [])
                
                print(f'Cross-app dependencies found: {len(deps)}')
                
                # Show first few dependencies
                for i, dep in enumerate(deps[:3]):
                    print(f'  Dep {i+1}: {dep.get("source_application")} -> {dep.get("target_application")} (Impact: {dep.get("impact_level")})')
                    
                # Show overall stats
                total_deps = dep_intel.get('dependency_analysis', {}).get('total_dependencies', 0)
                print(f'Total dependencies: {total_deps}')
                
                clusters = cross_mapping.get('application_clusters', [])
                print(f'Application clusters: {len(clusters)}')
                
                graph = cross_mapping.get('dependency_graph', {})
                print(f'Graph nodes: {len(graph.get("nodes", []))}')
                print(f'Graph edges: {len(graph.get("edges", []))}')
                
            else:
                print('No dependency_intelligence in response')
                print(f'Available keys: {list(result.keys())}')
        else:
            print(f'API Error: {response.status_code}')
            print(f'Response: {response.text}')
            
    except Exception as e:
        print(f'Error calling API: {e}')

if __name__ == "__main__":
    test_dependency_api() 