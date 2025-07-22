#!/usr/bin/env python3
"""
Test script for Asset Classification Learning
"""

import asyncio
import os
import sys

# Add the backend directory to the path
sys.path.append('/app')

from app.services.asset_classification_learner import AssetClassification, AssetClassificationLearner


async def test_classification_learning():
    """Test asset classification learning functionality."""
    print("🧪 Testing Asset Classification Learning...")
    
    learner = AssetClassificationLearner()
    
    # Test learning from user feedback
    print("\n📚 Testing Learning from User Feedback:")
    print("=" * 60)
    
    # Simulate user confirming a classification
    asset_name = "prod-web-server-01"
    asset_metadata = {
        "environment": "production",
        "technology": "apache",
        "location": "datacenter-east"
    }
    
    classification_result = {
        "asset_type": "server",
        "application_type": "web_server",
        "technology_stack": ["apache", "linux"]
    }
    
    print("\n1. Learning from confirmed classification:")
    print(f"   Asset: {asset_name}")
    print(f"   Classification: {classification_result}")
    
    try:
        # Learn from user-confirmed classification
        result = await learner.learn_from_classification(
            asset_name=asset_name,
            asset_metadata=asset_metadata,
            classification_result=classification_result,
            user_confirmed=True,
            client_account_id="test_client_123",
            engagement_id="engagement_456",
            user_id="user_789"
        )
        
        print("   ✅ Learning Result:")
        print(f"      Pattern ID: {result.pattern_id}")
        print(f"      Confidence: {result.confidence}")
        print(f"      Success: {result.success}")
        print(f"      Message: {result.message}")
        
    except Exception as e:
        print(f"   ❌ Learning Error: {e}")
    
    # Test learning from incorrect classification
    print("\n2. Learning from incorrect classification:")
    
    incorrect_result = {
        "asset_type": "database",  # Wrong classification
        "application_type": "mysql",
        "technology_stack": ["mysql"]
    }
    
    try:
        result = await learner.learn_from_classification(
            asset_name="another-web-server",
            asset_metadata={"environment": "staging"},
            classification_result=incorrect_result,
            user_confirmed=False,  # User did not confirm
            client_account_id="test_client_123"
        )
        
        print("   ✅ Learning Result:")
        print(f"      Pattern ID: {result.pattern_id}")
        print(f"      Confidence: {result.confidence}")
        print(f"      Success: {result.success}")
        print(f"      Message: {result.message}")
        
    except Exception as e:
        print(f"   ❌ Learning Error: {e}")
    
    # Test classification after learning
    print("\n📊 Testing Classification After Learning:")
    print("=" * 60)
    
    # Test with similar asset name
    similar_asset = {
        'name': 'prod-web-server-02',  # Similar to learned pattern
        'metadata': {'environment': 'production', 'technology': 'nginx'}
    }
    
    try:
        classification = await learner.classify_asset_automatically(
            similar_asset, 
            client_account_id='test_client_123'
        )
        
        print("\n3. Classification of similar asset:")
        print(f"   Asset: {similar_asset['name']}")
        print(f"   Type: {classification.asset_type}")
        print(f"   App Type: {classification.application_type}")
        print(f"   Technology: {classification.technology_stack}")
        print(f"   Confidence: {classification.confidence:.3f}")
        print(f"   Reasoning: {classification.reasoning}")
        print(f"   Pattern IDs: {classification.pattern_ids}")
        
    except Exception as e:
        print(f"   ❌ Classification Error: {e}")
    
    print("\n✅ Asset Classification Learning Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_classification_learning()) 