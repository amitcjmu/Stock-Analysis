#!/usr/bin/env python3
"""
Test script for Confidence Manager Service
"""

import asyncio
import sys

# Add the backend directory to the path
sys.path.append("/app")

from app.services.confidence_manager import ConfidenceManager


async def test_confidence_manager():
    """Test confidence manager functionality."""
    print("🧪 Testing Confidence Manager...")

    manager = ConfidenceManager()
    client_id = "test_client_confidence"

    # Test getting default thresholds
    print("\n📊 Testing Default Thresholds:")
    print("=" * 60)

    try:
        # Test different operation types
        operations = [
            "field_mapping",
            "asset_classification",
            "migration_strategy",
            "risk_assessment",
        ]

        for operation in operations:
            thresholds = await manager.get_thresholds(client_id, operation)

            print(f"\n{operation}:")
            print(f"  Auto Apply: {thresholds.auto_apply}")
            print(f"  Suggest: {thresholds.suggest}")
            print(f"  Reject: {thresholds.reject}")
            print(f"  Client: {thresholds.client_account_id}")

    except Exception as e:
        print(f"❌ Error getting thresholds: {e}")

    # Test recording user feedback
    print("\n📝 Testing User Feedback Recording:")
    print("=" * 60)

    try:
        # Record some feedback events
        feedback_tests = [
            {
                "operation_type": "field_mapping",
                "original_confidence": 0.85,
                "user_action": "accepted",
                "was_correct": True,
                "feedback_details": {"field": "server_name", "mapped_to": "hostname"},
            },
            {
                "operation_type": "field_mapping",
                "original_confidence": 0.75,
                "user_action": "corrected",
                "was_correct": False,
                "feedback_details": {
                    "field": "priority",
                    "corrected_to": "business_criticality",
                },
            },
            {
                "operation_type": "asset_classification",
                "original_confidence": 0.9,
                "user_action": "accepted",
                "was_correct": True,
                "feedback_details": {"asset": "web-server-01", "type": "server"},
            },
        ]

        for i, feedback in enumerate(feedback_tests, 1):
            success = await manager.record_user_feedback(
                client_account_id=client_id,
                operation_type=feedback["operation_type"],
                original_confidence=feedback["original_confidence"],
                user_action=feedback["user_action"],
                was_correct=feedback["was_correct"],
                feedback_details=feedback["feedback_details"],
            )

            print(f"{i}. Recorded feedback for {feedback['operation_type']}: {success}")
            print(
                f"   Action: {feedback['user_action']} (confidence: {feedback['original_confidence']})"
            )

    except Exception as e:
        print(f"❌ Error recording feedback: {e}")

    # Test threshold statistics
    print("\n📈 Testing Threshold Statistics:")
    print("=" * 60)

    try:
        stats = await manager.get_threshold_statistics(client_id)

        print(f"Total Feedback Events: {stats.get('total_feedback', 0)}")
        print(f"Overall Accuracy: {stats.get('overall_accuracy', 0):.1%}")

        accuracy_by_confidence = stats.get("accuracy_by_confidence", {})
        for range_name, data in accuracy_by_confidence.items():
            print(f"  {range_name}: {data['accuracy']:.1%} ({data['count']} events)")

        action_distribution = stats.get("user_action_distribution", {})
        for action, rate in action_distribution.items():
            print(f"  {action}: {rate:.1%}")

    except Exception as e:
        print(f"❌ Error getting statistics: {e}")

    # Test threshold adjustment
    print("\n⚙️ Testing Threshold Adjustment:")
    print("=" * 60)

    try:
        # Simulate a correction event that should trigger adjustment
        correction_event = {
            "original_confidence": 0.8,
            "user_action": "corrected",
            "was_correct": False,
            "correction_details": "High confidence suggestion was wrong",
        }

        adjustment = await manager.adjust_thresholds(
            client_id, "field_mapping", correction_event
        )

        print(f"Adjustment Success: {adjustment.success}")
        print(f"Operation: {adjustment.operation_type}")
        print(f"Reason: {adjustment.adjustment_reason}")

        if adjustment.success:
            print("\nOld Thresholds:")
            print(f"  Auto Apply: {adjustment.old_thresholds.auto_apply}")
            print(f"  Suggest: {adjustment.old_thresholds.suggest}")
            print(f"  Reject: {adjustment.old_thresholds.reject}")

            print("\nNew Thresholds:")
            print(f"  Auto Apply: {adjustment.new_thresholds.auto_apply}")
            print(f"  Suggest: {adjustment.new_thresholds.suggest}")
            print(f"  Reject: {adjustment.new_thresholds.reject}")

    except Exception as e:
        print(f"❌ Error adjusting thresholds: {e}")

    print("\n✅ Confidence Manager Test Complete!")


if __name__ == "__main__":
    asyncio.run(test_confidence_manager())
