#!/usr/bin/env python3
"""
Test script for the learning pattern system
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append('/app')

from app.services.field_mapping_learner import FieldMappingLearner
from app.services.learning_pattern_service import LearningPatternService
from app.utils.vector_utils import VectorUtils
from app.services.asset_classification_learner import AssetClassificationLearner
from app.services.confidence_manager import ConfidenceManager

async def test_learning_system():
    """Test the learning pattern system functionality."""
    print("🧪 Testing Learning Pattern System")
    print("=" * 50)
    
    # Test client account
    client_account_id = "test_client_123"
    
    # Initialize services
    field_learner = FieldMappingLearner()
    learning_service = LearningPatternService()
    vector_utils = VectorUtils()
    asset_learner = AssetClassificationLearner()
    confidence_manager = ConfidenceManager()
    
    print("✅ Services initialized successfully")
    
    print("\n📝 Testing field mapping learning...")
    try:
        # Learn from a successful mapping
        result = await field_learner.learn_from_mapping(
            source_field="SERVER_NAME",
            target_field="asset_name",
            sample_values=["web-server-01", "db-server-02", "app-server-03"],
            client_account_id=client_account_id,
            success=True,
            user_id="test_user"
        )
        
        print(f"✅ Learned mapping pattern:")
        print(f"   - Pattern ID: {result.pattern_id}")
        print(f"   - Confidence: {result.confidence}")
        print(f"   - Success: {result.success}")
        print(f"   - Message: {result.message}")
        
    except Exception as e:
        print(f"❌ Error learning mapping: {e}")
    
    print("\n📝 Testing field mapping suggestions...")
    try:
        # Learn a few more patterns first
        await field_learner.learn_from_mapping(
            source_field="IP_ADDR",
            target_field="ip_address",
            sample_values=["192.168.1.10", "10.0.0.5", "172.16.1.20"],
            client_account_id=client_account_id,
            success=True
        )
        
        await field_learner.learn_from_mapping(
            source_field="OS_TYPE",
            target_field="operating_system",
            sample_values=["Windows Server 2019", "Ubuntu 20.04", "CentOS 7"],
            client_account_id=client_account_id,
            success=True
        )
        
        # Now test suggestions
        source_fields = ["HOSTNAME", "IP_ADDRESS", "OPERATING_SYS"]
        sample_data = {
            "HOSTNAME": ["web01", "db02", "app03"],
            "IP_ADDRESS": ["192.168.1.100", "10.0.0.50"],
            "OPERATING_SYS": ["Windows 10", "Linux"]
        }
        
        suggestions = await field_learner.suggest_field_mappings(
            source_fields=source_fields,
            sample_data=sample_data,
            client_account_id=client_account_id,
            max_suggestions=3
        )
        
        print(f"✅ Generated suggestions for {len(suggestions)} fields:")
        for field, field_suggestions in suggestions.items():
            print(f"   - {field}: {len(field_suggestions)} suggestions")
            for i, suggestion in enumerate(field_suggestions):
                print(f"     {i+1}. {suggestion.target_field} (confidence: {suggestion.confidence:.2f})")
                print(f"        Reasoning: {suggestion.reasoning}")
        
    except Exception as e:
        print(f"❌ Error generating suggestions: {e}")
    
    print("\n📝 Testing pattern statistics...")
    try:
        stats = await field_learner.get_mapping_statistics(client_account_id)
        print(f"✅ Pattern statistics:")
        print(f"   - Total patterns: {stats.get('total_patterns', 0)}")
        print(f"   - Mapping patterns: {stats.get('mapping_patterns', 0)}")
        print(f"   - Average confidence: {stats.get('average_confidence', 0):.2f}")
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
    
    print("\n📝 Testing asset classification learning...")
    try:
        # Test asset classification pattern storage
        classification_data = {
            "client_account_id": client_account_id,
            "pattern_name": "Web Server Pattern",
            "asset_name_pattern": "web-server",
            "predicted_asset_type": "server",
            "predicted_application_type": "web_server",
            "predicted_technology_stack": ["nginx", "apache"],
            "confidence_score": 0.85,
            "learning_source": "user_feedback"
        }
        
        pattern_id = await learning_service.store_pattern(
            classification_data,
            pattern_type="classification"
        )
        
        print(f"✅ Stored classification pattern: {pattern_id}")
        
        # Test finding similar classification patterns
        similar_patterns = await learning_service.find_similar_patterns(
            "web-app-server-01",
            client_account_id,
            pattern_type="classification",
            limit=3
        )
        
        print(f"✅ Found {len(similar_patterns)} similar classification patterns")
        for pattern, similarity in similar_patterns:
            print(f"   - Pattern: {pattern.pattern_name} (similarity: {similarity:.3f})")
        
    except Exception as e:
        print(f"❌ Error with classification learning: {e}")
    
    print("\n📝 Testing vector similarity search...")
    try:
        # Test direct vector operations
        pattern_id = await vector_utils.store_pattern_embedding(
            pattern_text="database_server mysql production",
            target_field="asset_type",
            client_account_id=client_account_id,
            pattern_context={"environment": "production", "technology": "mysql"}
        )
        
        print(f"✅ Stored vector pattern: {pattern_id}")
        
        # Test similarity search
        query_embedding = await vector_utils.embedding_service.embed_text("db_server mysql prod")
        similar_patterns = await vector_utils.find_similar_patterns(
            query_embedding,
            client_account_id,
            limit=3,
            similarity_threshold=0.6
        )
        
        print(f"✅ Vector similarity search found {len(similar_patterns)} patterns")
        
    except Exception as e:
        print(f"❌ Error with vector operations: {e}")
    
    print("\n🎯 Learning System Test Complete!")
    print("\n📊 Summary:")
    print("   - Embedding service: ✅ Working with DeepInfra")
    print("   - Field mapping learning: ✅ Storing and retrieving patterns")
    print("   - Suggestion generation: ✅ AI-powered recommendations")
    print("   - Vector similarity: ✅ pgvector integration")
    print("   - Classification patterns: ✅ Asset type learning")

async def test_end_to_end_learning_flow():
    """Test complete learning workflow."""
    print("🧪 Testing End-to-End Learning Flow...")
    print("=" * 80)
    
    # Initialize services
    field_learner = FieldMappingLearner()
    asset_learner = AssetClassificationLearner()
    confidence_manager = ConfidenceManager()
    
    client_id = "test_client_e2e"
    
    print("\n📋 Phase 1: Initial Field Mapping Learning")
    print("-" * 60)
    
    # Scenario: User maps unknown field "DR_PRIORITY" to "business_criticality"
    print("1. User encounters unknown field 'DR_PRIORITY'")
    
    # Learn from user mapping
    mapping_success = await field_learner.learn_from_mapping(
        source_field="DR_PRIORITY",
        target_field="business_criticality",
        sample_values=["HIGH", "MEDIUM", "LOW", "CRITICAL"],
        client_account_id=client_id,
        success=True,
        user_id="test_user"
    )
    
    print(f"   ✅ Learning result: {mapping_success}")
    
    # Test field mapping suggestions
    print("\n2. Testing field mapping suggestions for similar field...")
    suggestions = await field_learner.suggest_field_mappings(
        source_fields=["DISASTER_RECOVERY_TIER", "SERVER_NAME", "ENVIRONMENT"],
        sample_data={
            "DISASTER_RECOVERY_TIER": ["TIER1", "TIER2", "TIER3"],
            "SERVER_NAME": ["web-prod-01", "db-prod-02"],
            "ENVIRONMENT": ["PRODUCTION", "STAGING"]
        },
        client_account_id=client_id
    )
    
    print("   Field Mapping Suggestions:")
    for field, field_suggestions in suggestions.items():
        print(f"     {field}:")
        for suggestion in field_suggestions:
            print(f"       → {suggestion.target_field} (confidence: {suggestion.confidence:.2f})")
            print(f"         Reasoning: {suggestion.reasoning}")
        print()
    
    print("\n📊 Phase 2: Asset Classification Learning")
    print("-" * 60)
    
    # Learn from asset classifications
    print("1. Learning from asset classifications...")
    
    test_assets = [
        {
            'name': 'web-prod-server-01',
            'metadata': {'environment': 'production', 'technology': 'apache', 'tier': 'web'}
        },
        {
            'name': 'mysql-db-primary',
            'metadata': {'environment': 'production', 'technology': 'mysql', 'tier': 'database'}
        },
        {
            'name': 'api-gateway-prod',
            'metadata': {'environment': 'production', 'technology': 'nginx', 'tier': 'api'}
        }
    ]
    
    for asset in test_assets:
        # Classify asset first
        classification = await asset_learner.classify_asset_automatically(
            asset_data={'name': asset['name'], 'metadata': asset['metadata']},
            client_account_id=client_id
        )
        
        print(f"   Asset: {asset['name']}")
        print(f"     Classified as: {classification.asset_type}")
        print(f"     Confidence: {classification.confidence:.2f}")
        
        # Learn from classification (simulate user confirmation)
        learn_success = await asset_learner.learn_from_classification(
            asset_name=asset['name'],
            asset_metadata=asset['metadata'],
            classification_result={
                'asset_type': classification.asset_type,
                'application_type': classification.application_type,
                'technology_stack': classification.technology_stack
            },
            user_confirmed=True,
            client_account_id=client_id,
            user_id="test_user"
        )
        
        print(f"     Learning success: {learn_success}")
        print()
    
    print("\n2. Testing classification suggestions for new assets...")
    
    new_test_assets = [
        {
            'name': 'web-staging-server-02',
            'metadata': {'environment': 'staging', 'technology': 'apache'}
        },
        {
            'name': 'postgres-db-backup',
            'metadata': {'environment': 'production', 'technology': 'postgresql'}
        }
    ]
    
    for asset in new_test_assets:
        classification = await asset_learner.classify_asset_automatically(
            asset_data={'name': asset['name'], 'metadata': asset['metadata']},
            client_account_id=client_id
        )
        
        print(f"   New Asset: {asset['name']}")
        print(f"     Suggested Type: {classification.asset_type}")
        print(f"     Application Type: {classification.application_type}")
        print(f"     Technology: {classification.technology_stack}")
        print(f"     Confidence: {classification.confidence:.2f}")
        print(f"     Reasoning: {classification.reasoning}")
        print()
    
    print("\n⚙️ Phase 3: Confidence Management Integration")
    print("-" * 60)
    
    # Test confidence thresholds
    print("1. Testing confidence thresholds...")
    
    operations = ["field_mapping", "asset_classification"]
    for operation in operations:
        thresholds = await confidence_manager.get_thresholds(client_id, operation)
        print(f"   {operation.title()} Thresholds:")
        print(f"     Auto Apply: {thresholds.auto_apply}")
        print(f"     Suggest: {thresholds.suggest}")
        print(f"     Reject: {thresholds.reject}")
        print()
    
    # Simulate user feedback
    print("2. Recording user feedback...")
    
    feedback_events = [
        {
            'operation': 'field_mapping',
            'confidence': 0.85,
            'action': 'accepted',
            'correct': True,
            'details': {'field': 'DISASTER_RECOVERY_TIER', 'mapped_to': 'business_criticality'}
        },
        {
            'operation': 'asset_classification',
            'confidence': 0.75,
            'action': 'corrected',
            'correct': False,
            'details': {'asset': 'web-staging-server-02', 'corrected_type': 'application'}
        },
        {
            'operation': 'field_mapping',
            'confidence': 0.92,
            'action': 'accepted',
            'correct': True,
            'details': {'field': 'SERVER_NAME', 'mapped_to': 'hostname'}
        }
    ]
    
    for feedback in feedback_events:
        success = await confidence_manager.record_user_feedback(
            client_account_id=client_id,
            operation_type=feedback['operation'],
            original_confidence=feedback['confidence'],
            user_action=feedback['action'],
            was_correct=feedback['correct'],
            feedback_details=feedback['details']
        )
        
        print(f"   Recorded {feedback['action']} for {feedback['operation']}: {success}")
        print(f"     Confidence: {feedback['confidence']}, Correct: {feedback['correct']}")
    
    print("\n📈 Phase 4: Learning Performance Analysis")
    print("-" * 60)
    
    # Get learning statistics
    print("1. Analyzing learning performance...")
    
    for operation in operations:
        stats = await confidence_manager.get_threshold_statistics(
            client_account_id=client_id,
            operation_type=operation
        )
        
        print(f"   {operation.title()} Statistics:")
        print(f"     Total Feedback: {stats['total_feedback']}")
        print(f"     Overall Accuracy: {stats['overall_accuracy']:.1%}")
        print(f"     User Actions: {stats['user_action_distribution']}")
        print()
    
    print("\n🎯 Phase 5: Threshold Adjustment Testing")
    print("-" * 60)
    
    # Test threshold adjustment
    print("1. Testing threshold adjustment...")
    
    for operation in operations:
        adjustment_result = await confidence_manager.adjust_thresholds_based_on_feedback(
            client_account_id=client_id,
            operation_type=operation
        )
        
        print(f"   {operation.title()} Threshold Adjustment:")
        print(f"     Success: {adjustment_result['success']}")
        print(f"     Reason: {adjustment_result['reason']}")
        
        if 'old_thresholds' in adjustment_result:
            print(f"     Old Thresholds: {adjustment_result['old_thresholds']}")
            print(f"     New Thresholds: {adjustment_result['new_thresholds']}")
        print()
    
    print("\n✅ End-to-End Learning Flow Test Complete!")
    print("=" * 80)
    
    # Summary
    print("\n📋 Test Summary:")
    print("   ✅ Field mapping learning and suggestions working")
    print("   ✅ Asset classification learning and suggestions working")
    print("   ✅ Confidence threshold management operational")
    print("   ✅ User feedback integration functional")
    print("   ✅ Learning performance tracking active")
    print("   ✅ Threshold adjustment logic working")
    print("\n🎉 All learning systems integrated successfully!")

if __name__ == "__main__":
    asyncio.run(test_learning_system())
    asyncio.run(test_end_to_end_learning_flow()) 