#!/usr/bin/env python3
"""
Test script for Asset Classification Learner
"""

import asyncio
import sys

# Add the backend directory to the path
sys.path.append('/app')

from app.services.asset_classification_learner import AssetClassificationLearner


async def test_classification():
    """Test asset classification functionality."""
    print("🧪 Testing Asset Classification Learner...")
    
    learner = AssetClassificationLearner()
    
    # Test cases
    test_assets = [
        {
            'name': 'web-server-01',
            'metadata': {'environment': 'production', 'technology': 'apache'}
        },
        {
            'name': 'mysql-db-prod',
            'metadata': {'environment': 'production', 'technology': 'mysql'}
        },
        {
            'name': 'api-gateway-service',
            'metadata': {'environment': 'staging', 'technology': 'nodejs'}
        },
        {
            'name': 'storage-nas-backup',
            'metadata': {'environment': 'production', 'technology': 'netapp'}
        },
        {
            'name': 'unknown-system-xyz',
            'metadata': {'environment': 'test'}
        }
    ]
    
    print("\n📊 Testing Heuristic Classification:")
    print("=" * 60)
    
    for i, asset_data in enumerate(test_assets, 1):
        try:
            classification = await learner.classify_asset_automatically(
                asset_data, 
                client_account_id='test_client'
            )
            
            print(f"\n{i}. Asset: {asset_data['name']}")
            print(f"   Type: {classification.asset_type}")
            print(f"   Technology: {classification.technology_stack}")
            print(f"   Confidence: {classification.confidence:.3f}")
            print(f"   Reasoning: {classification.reasoning}")
            
        except Exception as e:
            print(f"\n{i}. Asset: {asset_data['name']} - ERROR: {e}")
    
    print("\n✅ Asset Classification Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_classification()) 