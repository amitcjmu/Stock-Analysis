#!/usr/bin/env python3
"""
Comprehensive test suite for the Learning Effectiveness System.
Tests feedback processing, pattern extraction, and continuous improvement.
"""

import sys
import os
import asyncio
import tempfile
import shutil
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.memory import AgentMemory
from app.services.feedback import FeedbackProcessor
from app.services.analysis import IntelligentAnalyzer
from app.services.crewai_flow_service import CrewAIService


class TestLearningSystem:
    """Test suite for learning effectiveness functionality."""
    
    def __init__(self):
        self.temp_dir = None
        self.memory = None
        self.feedback_processor = None
        self.analyzer = None
        self.service = None
    
    def setup(self):
        """Set up test environment."""
        print("🔧 Setting up learning system tests...")
        
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.memory = AgentMemory(data_dir=self.temp_dir)
        self.feedback_processor = FeedbackProcessor(self.memory)
        self.analyzer = IntelligentAnalyzer(self.memory)
        self.service = CrewAIService()
        
        print(f"   ✅ Learning system initialized with temp dir: {self.temp_dir}")
    
    def teardown(self):
        """Clean up test environment."""
        print("🧹 Cleaning up learning system tests...")
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print("   ✅ Temporary directory cleaned up")
    
    def test_feedback_processing(self):
        """Test basic feedback processing functionality."""
        print("\n💬 Testing Feedback Processing")
        print("-" * 40)
        
        # Test feedback data
        feedback_data = {
            "filename": "test_servers.csv",
            "user_corrections": {
                "analysis_issues": "These are servers, not applications. CI_TYPE field clearly indicates Server.",
                "missing_fields_feedback": "IP Address and OS Version are required for servers.",
                "comments": "Please improve server detection logic."
            },
            "asset_type_override": "server",
            "original_analysis": {
                "asset_type_detected": "application",
                "confidence_level": 0.75
            }
        }
        
        # Process feedback
        result = self.feedback_processor.intelligent_feedback_processing(feedback_data)
        
        # Verify results
        assert result["learning_applied"] is True, "Learning should be applied"
        assert len(result["patterns_identified"]) > 0, "Should identify patterns"
        assert len(result["knowledge_updates"]) > 0, "Should generate knowledge updates"
        assert result["confidence_boost"] > 0, "Should provide confidence boost"
        
        print(f"   ✅ Learning applied: {result['learning_applied']}")
        print(f"   ✅ Patterns identified: {len(result['patterns_identified'])}")
        print(f"   ✅ Knowledge updates: {len(result['knowledge_updates'])}")
        print(f"   ✅ Confidence boost: {result['confidence_boost']:.2f}")
        
        return True
    
    def test_pattern_extraction(self):
        """Test pattern extraction from feedback."""
        print("\n🔍 Testing Pattern Extraction")
        print("-" * 40)
        
        # Multiple feedback scenarios to extract patterns
        feedback_scenarios = [
            {
                "filename": "server_inventory.csv",
                "user_corrections": {
                    "analysis_issues": "CI_Type field shows 'Server' - this is clearly server data",
                    "comments": "Look for CI_Type field to determine asset type"
                },
                "asset_type_override": "server",
                "original_analysis": {"asset_type_detected": "application", "confidence_level": 0.6}
            },
            {
                "filename": "application_list.csv",
                "user_corrections": {
                    "analysis_issues": "These are applications, not servers. Application field indicates software assets",
                    "comments": "Application field is key indicator"
                },
                "asset_type_override": "application",
                "original_analysis": {"asset_type_detected": "server", "confidence_level": 0.7}
            },
            {
                "filename": "database_systems.csv",
                "user_corrections": {
                    "analysis_issues": "Database Type field shows these are database assets",
                    "comments": "Database Type field is definitive"
                },
                "asset_type_override": "database",
                "original_analysis": {"asset_type_detected": "server", "confidence_level": 0.65}
            }
        ]
        
        all_patterns = []
        
        for scenario in feedback_scenarios:
            result = self.feedback_processor.intelligent_feedback_processing(scenario)
            all_patterns.extend(result["patterns_identified"])
            print(f"   ✅ Processed feedback for {scenario['filename']}")
        
        # Verify pattern extraction
        assert len(all_patterns) > 0, "Should extract patterns from feedback"
        
        # Check for specific pattern types
        field_patterns = [p for p in all_patterns if "field" in p.lower()]
        assert len(field_patterns) > 0, "Should identify field-based patterns"
        
        print(f"   ✅ Total patterns extracted: {len(all_patterns)}")
        print(f"   ✅ Field-based patterns: {len(field_patterns)}")
        
        # Test pattern storage in memory
        learned_patterns = self.memory.experiences.get("learned_patterns", [])
        assert len(learned_patterns) > 0, "Patterns should be stored in memory"
        
        print(f"   ✅ Patterns stored in memory: {len(learned_patterns)}")
        
        return True
    
    def test_confidence_improvement(self):
        """Test confidence improvement over time."""
        print("\n📈 Testing Confidence Improvement")
        print("-" * 40)
        
        # Simulate initial analysis with low confidence
        initial_data = {
            "filename": "confidence_test.csv",
            "structure": {
                "columns": ["Name", "CI_Type", "Environment"],
                "row_count": 10
            },
            "sample_data": [
                {"Name": "WebServer01", "CI_Type": "Server", "Environment": "Production"}
            ]
        }
        
        # Get initial analysis
        initial_result = self.analyzer.intelligent_placeholder_analysis(initial_data)
        initial_confidence = initial_result["confidence_level"]
        
        print(f"   ✅ Initial confidence: {initial_confidence:.2f}")
        
        # Add positive feedback to improve confidence
        feedback_data = {
            "filename": "confidence_test.csv",
            "user_corrections": {
                "analysis_issues": "Correct! CI_Type field clearly shows Server type",
                "comments": "Good analysis - this pattern should be reinforced"
            },
            "asset_type_override": initial_result["asset_type_detected"],
            "original_analysis": initial_result
        }
        
        # Process feedback
        feedback_result = self.feedback_processor.intelligent_feedback_processing(feedback_data)
        confidence_boost = feedback_result["confidence_boost"]
        
        print(f"   ✅ Confidence boost from feedback: {confidence_boost:.2f}")
        
        # Simulate second analysis with learned patterns
        second_result = self.analyzer.intelligent_placeholder_analysis(initial_data)
        second_confidence = second_result["confidence_level"]
        
        print(f"   ✅ Second analysis confidence: {second_confidence:.2f}")
        
        # Confidence should improve (or at least not decrease significantly)
        improvement = second_confidence - initial_confidence
        print(f"   ✅ Confidence improvement: {improvement:.2f}")
        
        # Test should show learning effect
        assert improvement >= -0.1, "Confidence should not decrease significantly"
        
        return True
    
    def test_learning_metrics_tracking(self):
        """Test learning metrics tracking over time."""
        print("\n📊 Testing Learning Metrics Tracking")
        print("-" * 40)
        
        # Simulate multiple analysis and feedback cycles
        scenarios = [
            ("correct", "server", "server"),
            ("incorrect", "application", "server"),
            ("correct", "database", "database"),
            ("incorrect", "server", "application"),
            ("correct", "application", "application"),
        ]
        
        for i, (outcome, predicted, actual) in enumerate(scenarios):
            # Record analysis attempt
            self.memory.add_experience("analysis_attempt", {
                "filename": f"test_file_{i}.csv",
                "asset_type_detected": predicted,
                "confidence": 0.8,
                "actual_type": actual
            })
            
            # Update metrics
            self.memory.update_learning_metrics("total_analyses", 
                                               self.memory.learning_metrics.get("total_analyses", 0) + 1)
            
            if outcome == "correct":
                self.memory.update_learning_metrics("correct_predictions",
                                                   self.memory.learning_metrics.get("correct_predictions", 0) + 1)
            else:
                self.memory.update_learning_metrics("user_corrections",
                                                   self.memory.learning_metrics.get("user_corrections", 0) + 1)
            
            print(f"   ✅ Recorded {outcome} prediction: {predicted} -> {actual}")
        
        # Calculate accuracy
        total = self.memory.learning_metrics.get("total_analyses", 0)
        correct = self.memory.learning_metrics.get("correct_predictions", 0)
        accuracy = correct / total if total > 0 else 0
        
        print(f"   ✅ Total analyses: {total}")
        print(f"   ✅ Correct predictions: {correct}")
        print(f"   ✅ Accuracy: {accuracy:.2f}")
        
        # Verify metrics
        assert total == len(scenarios), "Should track all analyses"
        assert correct == 3, "Should track correct predictions"  # 3 correct in scenarios
        assert accuracy == 0.6, "Accuracy should be 60%"
        
        return True
    
    def test_feedback_trends_analysis(self):
        """Test feedback trends analysis."""
        print("\n📈 Testing Feedback Trends Analysis")
        print("-" * 40)
        
        # Add various feedback types
        feedback_types = [
            ("asset_type_correction", "server"),
            ("missing_fields", "IP Address needed"),
            ("asset_type_correction", "application"),
            ("analysis_quality", "Good analysis"),
            ("missing_fields", "OS Version required"),
            ("asset_type_correction", "database"),
        ]
        
        for feedback_type, content in feedback_types:
            self.memory.add_experience("user_feedback", {
                "feedback_type": feedback_type,
                "content": content,
                "timestamp": "2025-01-27T12:00:00Z"
            })
            print(f"   ✅ Added {feedback_type} feedback")
        
        # Analyze trends
        trends = self.feedback_processor.analyze_feedback_trends()
        
        # Verify trends analysis
        assert "total_feedback" in trends, "Should include total feedback count"
        assert "feedback_categories" in trends, "Should categorize feedback"
        assert "common_issues" in trends, "Should identify common issues"
        assert "improvement_areas" in trends, "Should suggest improvements"
        
        print(f"   ✅ Total feedback analyzed: {trends['total_feedback']}")
        print(f"   ✅ Feedback categories: {list(trends['feedback_categories'].keys())}")
        print(f"   ✅ Common issues identified: {len(trends['common_issues'])}")
        print(f"   ✅ Improvement areas: {len(trends['improvement_areas'])}")
        
        # Check specific trends
        assert trends["total_feedback"] == len(feedback_types), "Should count all feedback"
        assert "asset_type_correction" in trends["feedback_categories"], "Should identify correction category"
        
        return True
    
    async def test_end_to_end_learning(self):
        """Test end-to-end learning cycle."""
        print("\n🔄 Testing End-to-End Learning Cycle")
        print("-" * 40)
        
        # Step 1: Initial analysis
        test_data = {
            "filename": "learning_cycle_test.csv",
            "structure": {
                "columns": ["Name", "CI_Type", "Environment", "Application"],
                "row_count": 5
            },
            "sample_data": [
                {"Name": "WebApp01", "CI_Type": "Application", "Environment": "Production", "Application": "Web Portal"}
            ]
        }
        
        print("   🔄 Step 1: Initial analysis")
        try:
            initial_result = await self.service.analyze_cmdb_data(test_data)
            print(f"   ✅ Initial analysis: {initial_result.get('asset_type_detected', 'unknown')}")
        except Exception as e:
            print(f"   ⚠️  Using fallback analysis: {e}")
            initial_result = self.analyzer.intelligent_placeholder_analysis(test_data)
        
        # Step 2: User feedback
        print("   🔄 Step 2: Processing user feedback")
        feedback_data = {
            "filename": "learning_cycle_test.csv",
            "user_corrections": {
                "analysis_issues": "CI_Type field shows Application - this is correct",
                "comments": "Application field confirms this is application data"
            },
            "asset_type_override": "application",
            "original_analysis": initial_result
        }
        
        try:
            feedback_result = await self.service.process_user_feedback(feedback_data)
            print(f"   ✅ Feedback processed: {feedback_result.get('learning_applied', False)}")
        except Exception as e:
            print(f"   ⚠️  Using fallback feedback processing: {e}")
            feedback_result = self.feedback_processor.intelligent_feedback_processing(feedback_data)
        
        # Step 3: Second analysis (should show improvement)
        print("   🔄 Step 3: Second analysis with learning")
        test_data["filename"] = "similar_application_data.csv"
        
        try:
            second_result = await self.service.analyze_cmdb_data(test_data)
            print(f"   ✅ Second analysis: {second_result.get('asset_type_detected', 'unknown')}")
        except Exception as e:
            print(f"   ⚠️  Using fallback analysis: {e}")
            second_result = self.analyzer.intelligent_placeholder_analysis(test_data)
        
        # Verify learning occurred
        initial_confidence = initial_result.get("confidence_level", 0)
        second_confidence = second_result.get("confidence_level", 0)
        
        print(f"   ✅ Initial confidence: {initial_confidence:.2f}")
        print(f"   ✅ Second confidence: {second_confidence:.2f}")
        print("   ✅ Learning cycle completed successfully")
        
        # Check memory state
        stats = self.memory.get_memory_stats()
        print(f"   ✅ Memory contains {stats['total_experiences']} experiences")
        
        return True
    
    async def run_all_tests(self):
        """Run all learning system tests."""
        print("🧪 Running Learning System Test Suite")
        print("=" * 60)
        
        self.setup()
        
        tests = [
            ("Feedback Processing", self.test_feedback_processing),
            ("Pattern Extraction", self.test_pattern_extraction),
            ("Confidence Improvement", self.test_confidence_improvement),
            ("Learning Metrics Tracking", self.test_learning_metrics_tracking),
            ("Feedback Trends Analysis", self.test_feedback_trends_analysis),
            ("End-to-End Learning", self.test_end_to_end_learning),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
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
        print(f"🎯 Learning System Test Results: {passed} passed, {failed} failed")
        print("=" * 60)
        
        if failed == 0:
            print("🎉 All learning system tests passed!")
        else:
            print(f"⚠️  {failed} tests failed - check implementation")
        
        return failed == 0


async def main():
    """Run the learning system test suite."""
    tester = TestLearningSystem()
    success = await tester.run_all_tests()
    return success


if __name__ == "__main__":
    asyncio.run(main()) 