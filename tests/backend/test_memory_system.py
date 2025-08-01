#!/usr/bin/env python3
"""
Comprehensive test suite for the Agent Memory System.
Tests memory persistence, pattern learning, and experience tracking.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.memory import AgentMemory


class TestMemorySystem:
    """Test suite for agent memory functionality."""

    def __init__(self):
        self.temp_dir = None
        self.memory = None

    def setup(self):
        """Set up test environment."""
        print("🔧 Setting up memory system tests...")

        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.memory = AgentMemory(data_dir=self.temp_dir)

        print(f"   ✅ Memory system initialized with temp dir: {self.temp_dir}")

    def teardown(self):
        """Clean up test environment."""
        print("🧹 Cleaning up memory system tests...")

        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print("   ✅ Temporary directory cleaned up")

    def test_memory_initialization(self):
        """Test memory system initialization."""
        print("\n🧠 Testing Memory Initialization")
        print("-" * 40)

        # Test basic initialization
        assert self.memory.data_dir == self.temp_dir, "Data directory should be set"
        assert isinstance(
            self.memory.experiences, dict
        ), "Experiences should be a dictionary"
        assert isinstance(
            self.memory.learning_metrics, dict
        ), "Learning metrics should be a dictionary"

        print(f"   ✅ Data directory: {self.memory.data_dir}")
        print(f"   ✅ Experiences initialized: {len(self.memory.experiences)} types")
        print(
            f"   ✅ Learning metrics initialized: {len(self.memory.learning_metrics)} metrics"
        )

        return True

    def test_experience_storage(self):
        """Test storing and retrieving experiences."""
        print("\n📚 Testing Experience Storage")
        print("-" * 40)

        # Test adding experiences
        test_experiences = [
            {
                "experience_type": "analysis_attempt",
                "data": {
                    "filename": "test_servers.csv",
                    "asset_type_detected": "server",
                    "confidence": 0.85,
                    "timestamp": "2025-01-27T12:00:00Z",
                },
            },
            {
                "experience_type": "user_feedback",
                "data": {
                    "filename": "test_servers.csv",
                    "correction": "These are actually applications",
                    "asset_type_override": "application",
                    "timestamp": "2025-01-27T12:05:00Z",
                },
            },
            {
                "experience_type": "learned_patterns",
                "data": {
                    "pattern": "CI_Type field with 'Application' indicates application assets",
                    "confidence_boost": 0.15,
                    "timestamp": "2025-01-27T12:10:00Z",
                },
            },
        ]

        for exp in test_experiences:
            self.memory.add_experience(exp["experience_type"], exp["data"])
            print(f"   ✅ Added {exp['experience_type']} experience")

        # Test retrieval
        for exp in test_experiences:
            experiences = self.memory.experiences.get(exp["experience_type"], [])
            assert (
                len(experiences) > 0
            ), f"Should have {exp['experience_type']} experiences"

            # Check the data was stored correctly
            stored_data = experiences[-1]  # Get the last added
            for key, value in exp["data"].items():
                assert stored_data.get(key) == value, f"Data should match for {key}"

        print("   ✅ All experiences stored and retrieved correctly")

        return True

    def test_relevant_experience_retrieval(self):
        """Test retrieving relevant experiences."""
        print("\n🔍 Testing Relevant Experience Retrieval")
        print("-" * 40)

        # Add test experiences with different filenames
        test_data = [
            ("server_data.csv", "server", 0.9),
            ("application_list.csv", "application", 0.8),
            ("database_inventory.csv", "database", 0.85),
            ("server_inventory.csv", "server", 0.92),
        ]

        for filename, asset_type, confidence in test_data:
            experience = {
                "filename": filename,
                "asset_type_detected": asset_type,
                "confidence": confidence,
            }
            self.memory.add_experience("analysis_attempt", experience)

        print(f"   ✅ Added {len(test_data)} test experiences")

        # Test retrieving relevant experiences
        relevant = self.memory.get_relevant_experiences("new_server_data.csv")

        assert len(relevant) > 0, "Should find relevant experiences"

        # Should prioritize server-related experiences
        server_experiences = [
            exp for exp in relevant if "server" in exp.get("filename", "").lower()
        ]
        assert len(server_experiences) > 0, "Should find server-related experiences"

        print(f"   ✅ Found {len(relevant)} relevant experiences")
        print(f"   ✅ Found {len(server_experiences)} server-related experiences")

        return True

    def test_learning_metrics(self):
        """Test learning metrics tracking."""
        print("\n📊 Testing Learning Metrics")
        print("-" * 40)

        # Test updating metrics
        metrics_to_test = [
            ("total_analyses", 5),
            ("correct_predictions", 4),
            ("user_corrections", 1),
            ("confidence_improvements", 3),
        ]

        for metric, value in metrics_to_test:
            self.memory.update_learning_metrics(metric, value)
            assert (
                self.memory.learning_metrics[metric] == value
            ), f"Metric {metric} should be {value}"
            print(f"   ✅ Updated {metric}: {value}")

        # Test calculated metrics
        accuracy = self.memory.learning_metrics.get("correct_predictions", 0) / max(
            self.memory.learning_metrics.get("total_analyses", 1), 1
        )
        expected_accuracy = 4 / 5  # 0.8

        print(f"   ✅ Calculated accuracy: {accuracy:.2f}")
        assert (
            abs(accuracy - expected_accuracy) < 0.01
        ), "Accuracy calculation should be correct"

        return True

    def test_memory_persistence(self):
        """Test memory persistence across sessions."""
        print("\n💾 Testing Memory Persistence")
        print("-" * 40)

        # Add some test data
        test_experience = {
            "filename": "persistence_test.csv",
            "asset_type_detected": "server",
            "confidence": 0.88,
            "test_marker": "persistence_test",
        }

        self.memory.add_experience("analysis_attempt", test_experience)
        self.memory.update_learning_metrics("persistence_test", 42)

        print("   ✅ Added test data to memory")

        # Save memory
        self.memory.save_memory()
        print("   ✅ Memory saved to disk")

        # Create new memory instance (simulating restart)
        new_memory = AgentMemory(data_dir=self.temp_dir)

        # Check data persistence
        analysis_experiences = new_memory.experiences.get("analysis_attempt", [])
        persistence_experiences = [
            exp
            for exp in analysis_experiences
            if exp.get("test_marker") == "persistence_test"
        ]

        assert len(persistence_experiences) > 0, "Should find persisted experience"
        assert (
            persistence_experiences[0]["confidence"] == 0.88
        ), "Data should be preserved"
        assert (
            new_memory.learning_metrics.get("persistence_test") == 42
        ), "Metrics should be preserved"

        print("   ✅ Data successfully persisted and loaded")
        print(f"   ✅ Found {len(persistence_experiences)} persisted experiences")
        print(
            f"   ✅ Metrics preserved: {new_memory.learning_metrics.get('persistence_test')}"
        )

        return True

    def test_memory_statistics(self):
        """Test memory statistics generation."""
        print("\n📈 Testing Memory Statistics")
        print("-" * 40)

        # Add varied test data
        for i in range(10):
            experience = {
                "filename": f"test_file_{i}.csv",
                "asset_type_detected": "server" if i % 2 == 0 else "application",
                "confidence": 0.7 + (i * 0.02),  # Increasing confidence
            }
            self.memory.add_experience("analysis_attempt", experience)

        # Add some feedback
        for i in range(3):
            feedback = {
                "filename": f"feedback_file_{i}.csv",
                "correction": "Improved classification",
            }
            self.memory.add_experience("user_feedback", feedback)

        print("   ✅ Added test data for statistics")

        # Get statistics
        stats = self.memory.get_memory_stats()

        # Verify statistics
        assert "total_experiences" in stats, "Should include total experiences"
        assert "experience_types" in stats, "Should include experience types"
        assert "learning_metrics" in stats, "Should include learning metrics"

        assert (
            stats["total_experiences"] >= 13
        ), "Should count all experiences"  # 10 + 3
        assert (
            "analysis_attempt" in stats["experience_types"]
        ), "Should include analysis attempts"
        assert (
            "user_feedback" in stats["experience_types"]
        ), "Should include user feedback"

        print(f"   ✅ Total experiences: {stats['total_experiences']}")
        print(f"   ✅ Experience types: {list(stats['experience_types'].keys())}")
        print(
            f"   ✅ Analysis attempts: {stats['experience_types'].get('analysis_attempt', 0)}"
        )
        print(
            f"   ✅ User feedback: {stats['experience_types'].get('user_feedback', 0)}"
        )

        return True

    def test_pattern_learning(self):
        """Test pattern learning and recognition."""
        print("\n🔍 Testing Pattern Learning")
        print("-" * 40)

        # Simulate learning patterns from experiences
        patterns = [
            {
                "pattern": "Files with 'server' in name are usually server assets",
                "confidence_boost": 0.1,
                "evidence_count": 5,
            },
            {
                "pattern": "CI_Type field with 'Application' indicates application assets",
                "confidence_boost": 0.15,
                "evidence_count": 8,
            },
            {
                "pattern": "Database files often have 'db' or 'database' in filename",
                "confidence_boost": 0.12,
                "evidence_count": 3,
            },
        ]

        for pattern in patterns:
            self.memory.add_experience("learned_patterns", pattern)
            print(f"   ✅ Learned pattern: {pattern['pattern'][:50]}...")

        # Test pattern retrieval
        learned_patterns = self.memory.experiences.get("learned_patterns", [])
        assert len(learned_patterns) == len(patterns), "Should store all patterns"

        # Test pattern application (simulated)
        total_confidence_boost = sum(p["confidence_boost"] for p in learned_patterns)
        assert total_confidence_boost > 0.3, "Should accumulate confidence boosts"

        print(f"   ✅ Total patterns learned: {len(learned_patterns)}")
        print(f"   ✅ Total confidence boost available: {total_confidence_boost:.2f}")

        return True

    def run_all_tests(self):
        """Run all memory system tests."""
        print("🧪 Running Memory System Test Suite")
        print("=" * 60)

        self.setup()

        tests = [
            ("Memory Initialization", self.test_memory_initialization),
            ("Experience Storage", self.test_experience_storage),
            ("Relevant Experience Retrieval", self.test_relevant_experience_retrieval),
            ("Learning Metrics", self.test_learning_metrics),
            ("Memory Persistence", self.test_memory_persistence),
            ("Memory Statistics", self.test_memory_statistics),
            ("Pattern Learning", self.test_pattern_learning),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                result = test_func()
                if result:
                    print(f"✅ {test_name}: PASSED")
                    passed += 1
                else:
                    print(f"❌ {test_name}: FAILED")
                    failed += 1
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
                failed += 1

        self.teardown()

        print("\n" + "=" * 60)
        print(f"🎯 Memory System Test Results: {passed} passed, {failed} failed")
        print("=" * 60)

        if failed == 0:
            print("🎉 All memory system tests passed!")
        else:
            print(f"⚠️  {failed} tests failed - check implementation")

        return failed == 0


def main():
    """Run the memory system test suite."""
    tester = TestMemorySystem()
    success = tester.run_all_tests()
    return success


if __name__ == "__main__":
    main()
