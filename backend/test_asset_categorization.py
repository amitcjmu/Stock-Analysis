#!/usr/bin/env python3
"""
Test script to verify asset categorization logic
"""

import json

def test_asset_categorization():
    # Load processed assets
    with open('/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/data/persistence/processed_assets.json', 'r') as f:
        assets = json.load(f)
    
    print(f"Total assets loaded: {len(assets)}")
    
    # Test categorization with the new logic
    applications = sum(1 for a in assets if a.get('asset_type') and a['asset_type'].lower() == 'application')
    servers = sum(1 for a in assets if a.get('asset_type') and a['asset_type'].lower() == 'server')
    databases = sum(1 for a in assets if a.get('asset_type') and a['asset_type'].lower() == 'database')
    devices = sum(1 for a in assets if a.get('asset_type') and any(
        term in a['asset_type'].lower() for term in ['device', 'network', 'storage', 'security', 'infrastructure']
    ))
    unknown = sum(1 for a in assets if not a.get('asset_type') or a['asset_type'].lower() == 'unknown')
    
    print(f"Applications: {applications}")
    print(f"Servers: {servers}")
    print(f"Databases: {databases}")
    print(f"Devices: {devices}")
    print(f"Unknown: {unknown}")
    
    # Show asset types distribution
    asset_types = {}
    for asset in assets:
        asset_type = asset.get('asset_type', 'None')
        asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
    
    print(f"\nAsset type distribution:")
    for asset_type, count in sorted(asset_types.items()):
        print(f"  {asset_type}: {count}")
    
    # Verify total
    total_categorized = applications + servers + databases + devices + unknown
    print(f"\nTotal categorized: {total_categorized}")
    print(f"Total assets: {len(assets)}")
    print(f"Match: {total_categorized == len(assets)}")

if __name__ == '__main__':
    test_asset_categorization()