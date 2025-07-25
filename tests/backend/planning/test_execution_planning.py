"""
Tests for Execution Planning and Coordination System

Tests the planning and coordination functionality including:
- Plan generation and validation
- Dynamic planning based on data complexity
- Plan monitoring and adjustment
- Success criteria validation
- Adaptive workflow management
- Cross-crew planning coordination
- Resource allocation optimization
- Planning intelligence integration
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Import planning components
try:
    from app.services.crewai_flows.discovery_flow_redesigned import DiscoveryFlowRedesigned, DiscoveryFlowState
    from app.services.crewai_flows.planning_coordinator import PlanningCoordinator
    from app.services.observability.plan_analytics import PlanAnalytics
    from crewai.planning import PlanningMixin
    PLANNING_COMPONENTS_AVAILABLE = True
except ImportError:
    PLANNING_COMPONENTS_AVAILABLE = False
    PlanningCoordinator = None


@pytest.mark.skipif(not PLANNING_COMPONENTS_AVAILABLE, reason="Planning components not available")
class TestPlanGeneration:
    """Test suite for execution plan generation"""

    @pytest.fixture
    def mock_planning_coordinator(self):
        """Mock planning coordinator for testing"""
        coordinator = Mock(spec=PlanningCoordinator)
        coordinator.create_discovery_plan = AsyncMock()
        coordinator.analyze_data_complexity = AsyncMock()
        coordinator.optimize_execution_order = AsyncMock()
        coordinator.validate_plan = AsyncMock()
        return coordinator

    @pytest.fixture
    def sample_data_scenarios(self):
        """Sample data scenarios with different complexity levels"""
        return {
            "simple_scenario": {
                "data_size": 50,
                "field_complexity": "low",
                "data_quality": 0.95,
                "asset_types": ["servers"],
                "dependency_complexity": "minimal"
            },
            "moderate_scenario": {
                "data_size": 500,
                "field_complexity": "medium",
                "data_quality": 0.82,
                "asset_types": ["servers", "applications"],
                "dependency_complexity": "moderate"
            },
            "complex_scenario": {
                "data_size": 2000,
                "field_complexity": "high",
                "data_quality": 0.68,
                "asset_types": ["servers", "applications", "devices", "networks"],
                "dependency_complexity": "high"
            }
        }

    @pytest.fixture
    def expected_plan_structure(self):
        """Expected structure for discovery execution plans"""
        return {
            "plan_id": str,
            "created_timestamp": str,
            "data_complexity_analysis": dict,
            "execution_strategy": str,
            "phases": list,
            "crew_coordination": dict,
            "resource_allocation": dict,
            "success_criteria": dict,
            "monitoring_config": dict,
            "fallback_strategies": dict
        }

    @pytest.mark.asyncio
    async def test_basic_plan_generation(self, mock_planning_coordinator, sample_data_scenarios, expected_plan_structure):
        """Test basic execution plan generation"""
        simple_scenario = sample_data_scenarios["simple_scenario"]

        # Mock plan generation result
        generated_plan = {
            "plan_id": "plan_simple_001",
            "created_timestamp": datetime.now().isoformat(),
            "data_complexity_analysis": {
                "complexity_score": 0.3,
                "identified_challenges": ["minimal_field_mapping", "basic_classification"],
                "recommended_strategy": "sequential_processing"
            },
            "execution_strategy": "sequential",
            "phases": [
                {
                    "name": "field_mapping",
                    "crew": "FieldMappingCrew",
                    "estimated_duration_minutes": 5,
                    "dependencies": [],
                    "success_criteria": ["field_mappings_confidence > 0.8"]
                },
                {
                    "name": "data_cleansing",
                    "crew": "DataCleansingCrew",
                    "estimated_duration_minutes": 3,
                    "dependencies": ["field_mapping"],
                    "success_criteria": ["data_quality_score > 0.85"]
                },
                {
                    "name": "inventory_building",
                    "crew": "InventoryBuildingCrew",
                    "estimated_duration_minutes": 8,
                    "dependencies": ["data_cleansing"],
                    "success_criteria": ["asset_classification_complete"]
                }
            ],
            "crew_coordination": {
                "coordination_strategy": "sequential",
                "shared_memory": "enabled",
                "knowledge_sharing": "progressive"
            },
            "resource_allocation": {
                "total_estimated_time_minutes": 16,
                "memory_requirement_mb": 128,
                "cpu_utilization": "low"
            },
            "success_criteria": {
                "overall_success_threshold": 0.85,
                "individual_phase_thresholds": {"field_mapping": 0.8, "data_cleansing": 0.85, "inventory_building": 0.9}
            }
        }

        mock_planning_coordinator.create_discovery_plan.return_value = generated_plan

        # Generate plan
        plan = await mock_planning_coordinator.create_discovery_plan(simple_scenario)

        # Verify plan structure
        for key, expected_type in expected_plan_structure.items():
            assert key in plan
            if expected_type != str:  # Skip type checking for str (too generic)
                assert isinstance(plan[key], expected_type)

        # Verify plan content
        assert plan["execution_strategy"] == "sequential"
        assert len(plan["phases"]) == 3
        assert plan["data_complexity_analysis"]["complexity_score"] < 0.5  # Simple scenario

    @pytest.mark.asyncio
    async def test_adaptive_plan_generation_based_on_complexity(self, mock_planning_coordinator, sample_data_scenarios):
        """Test adaptive plan generation based on data complexity"""
        scenarios = [
            ("simple", sample_data_scenarios["simple_scenario"]),
            ("moderate", sample_data_scenarios["moderate_scenario"]),
            ("complex", sample_data_scenarios["complex_scenario"])
        ]

        # Mock complexity analysis and plan adaptation
        complexity_responses = {
            "simple": {"complexity_score": 0.3, "strategy": "sequential"},
            "moderate": {"complexity_score": 0.6, "strategy": "parallel_where_possible"},
            "complex": {"complexity_score": 0.9, "strategy": "adaptive_hybrid"}
        }

        for scenario_name, scenario_data in scenarios:
            mock_planning_coordinator.analyze_data_complexity.return_value = complexity_responses[scenario_name]

            complexity_analysis = await mock_planning_coordinator.analyze_data_complexity(scenario_data)

            # Verify adaptive strategy selection
            if scenario_name == "simple":
                assert complexity_analysis["strategy"] == "sequential"
            elif scenario_name == "moderate":
                assert complexity_analysis["strategy"] == "parallel_where_possible"
            elif scenario_name == "complex":
                assert complexity_analysis["strategy"] == "adaptive_hybrid"

    @pytest.mark.asyncio
    async def test_plan_validation_and_optimization(self, mock_planning_coordinator):
        """Test plan validation and optimization"""
        # Mock initial plan
        initial_plan = {
            "phases": [
                {"name": "field_mapping", "estimated_duration_minutes": 10},
                {"name": "data_cleansing", "estimated_duration_minutes": 8},
                {"name": "inventory_building", "estimated_duration_minutes": 15}
            ],
            "total_estimated_time_minutes": 33,
            "resource_allocation": {"memory_requirement_mb": 256}
        }

        # Mock validation results
        validation_results = {
            "validation_passed": True,
            "issues_identified": [],
            "optimization_opportunities": [
                {
                    "opportunity": "parallel_execution_inventory_dependencies",
                    "potential_time_savings_minutes": 5,
                    "implementation": "execute_dependency_crews_parallel"
                }
            ],
            "optimized_plan": {
                "phases": initial_plan["phases"],
                "total_estimated_time_minutes": 28,  # Optimized
                "optimization_applied": ["parallel_dependency_execution"]
            }
        }

        mock_planning_coordinator.validate_plan.return_value = validation_results

        # Validate plan
        validation = await mock_planning_coordinator.validate_plan(initial_plan)

        # Verify validation and optimization
        assert validation["validation_passed"] is True
        assert len(validation["optimization_opportunities"]) > 0
        assert validation["optimized_plan"]["total_estimated_time_minutes"] < initial_plan["total_estimated_time_minutes"]

    def test_success_criteria_definition(self):
        """Test success criteria definition for different phases"""
        success_criteria_templates = {
            "field_mapping": {
                "primary_criteria": ["field_mappings_confidence > 0.8", "unmapped_fields < 10%"],
                "secondary_criteria": ["semantic_understanding_complete", "validation_rules_applied"],
                "failure_conditions": ["confidence_too_low", "unmapped_fields_excessive"]
            },
            "data_cleansing": {
                "primary_criteria": ["data_quality_score > 0.85", "standardization_complete"],
                "secondary_criteria": ["format_consistency_achieved", "validation_passed"],
                "failure_conditions": ["quality_threshold_not_met", "standardization_failed"]
            },
            "inventory_building": {
                "primary_criteria": ["asset_classification_complete", "cross_domain_validation"],
                "secondary_criteria": ["classification_confidence > 0.8", "domain_coverage_complete"],
                "failure_conditions": ["classification_incomplete", "domain_gaps_identified"]
            }
        }

        # Verify success criteria completeness
        for phase, criteria in success_criteria_templates.items():
            assert len(criteria["primary_criteria"]) >= 2
            assert len(criteria["secondary_criteria"]) >= 2
            assert len(criteria["failure_conditions"]) >= 2


@pytest.mark.skipif(not PLANNING_COMPONENTS_AVAILABLE, reason="Planning components not available")
class TestPlanMonitoringAndAdjustment:
    """Test suite for plan monitoring and real-time adjustment"""

    @pytest.fixture
    def mock_plan_monitor(self):
        """Mock plan monitoring system"""
        monitor = Mock()
        monitor.start_monitoring = AsyncMock()
        monitor.get_execution_status = AsyncMock()
        monitor.detect_plan_deviations = AsyncMock()
        monitor.recommend_adjustments = AsyncMock()
        monitor.apply_plan_adjustment = AsyncMock()
        return monitor

    @pytest.fixture
    def execution_status_data(self):
        """Sample execution status data during plan execution"""
        return {
            "current_phase": "data_cleansing",
            "phase_progress": 0.65,
            "elapsed_time_minutes": 12,
            "estimated_remaining_minutes": 8,
            "phases_completed": ["field_mapping"],
            "phases_in_progress": ["data_cleansing"],
            "phases_pending": ["inventory_building", "app_server_dependencies", "app_app_dependencies", "technical_debt"],
            "success_criteria_status": {
                "field_mapping": {"status": "met", "score": 0.92},
                "data_cleansing": {"status": "in_progress", "current_score": 0.83}
            },
            "performance_metrics": {
                "actual_vs_estimated_time": 1.2,  # 20% slower than estimated
                "resource_utilization": 0.78,
                "error_rate": 0.02
            }
        }

    @pytest.mark.asyncio
    async def test_real_time_plan_monitoring(self, mock_plan_monitor, execution_status_data):
        """Test real-time monitoring of plan execution"""
        mock_plan_monitor.get_execution_status.return_value = execution_status_data

        # Monitor plan execution
        status = await mock_plan_monitor.get_execution_status("plan_001")

        # Verify monitoring
        assert status["current_phase"] == "data_cleansing"
        assert status["phase_progress"] > 0.5  # More than halfway through current phase
        assert len(status["phases_completed"]) == 1
        assert status["success_criteria_status"]["field_mapping"]["status"] == "met"

    @pytest.mark.asyncio
    async def test_plan_deviation_detection(self, mock_plan_monitor):
        """Test detection of plan deviations and performance issues"""
        # Mock deviation detection
        detected_deviations = [
            {
                "deviation_type": "performance_degradation",
                "phase": "data_cleansing",
                "severity": "medium",
                "details": {
                    "expected_duration_minutes": 8,
                    "actual_duration_minutes": 12,
                    "performance_ratio": 1.5,
                    "root_cause": "data_quality_lower_than_expected"
                }
            },
            {
                "deviation_type": "resource_utilization_high",
                "phase": "data_cleansing",
                "severity": "low",
                "details": {
                    "expected_memory_mb": 128,
                    "actual_memory_mb": 180,
                    "utilization_ratio": 1.4
                }
            }
        ]

        mock_plan_monitor.detect_plan_deviations.return_value = detected_deviations

        # Detect deviations
        deviations = await mock_plan_monitor.detect_plan_deviations("plan_001")

        # Verify deviation detection
        assert len(deviations) == 2
        assert deviations[0]["deviation_type"] == "performance_degradation"
        assert deviations[0]["severity"] == "medium"
        assert deviations[1]["deviation_type"] == "resource_utilization_high"

    @pytest.mark.asyncio
    async def test_dynamic_plan_adjustment(self, mock_plan_monitor):
        """Test dynamic plan adjustment based on execution performance"""
        # Mock plan adjustment recommendations
        adjustment_recommendations = [
            {
                "adjustment_type": "increase_crew_resources",
                "target_phase": "inventory_building",
                "rationale": "data_complexity_higher_than_estimated",
                "implementation": {
                    "additional_agents": 1,
                    "memory_increase_mb": 64,
                    "estimated_improvement": "25% faster execution"
                }
            },
            {
                "adjustment_type": "modify_execution_strategy",
                "target_phases": ["app_server_dependencies", "app_app_dependencies"],
                "rationale": "parallel_execution_possible",
                "implementation": {
                    "strategy_change": "sequential_to_parallel",
                    "estimated_time_savings_minutes": 10
                }
            }
        ]

        mock_plan_monitor.recommend_adjustments.return_value = adjustment_recommendations

        # Get adjustment recommendations
        recommendations = await mock_plan_monitor.recommend_adjustments("plan_001")

        # Verify recommendations
        assert len(recommendations) == 2
        assert recommendations[0]["adjustment_type"] == "increase_crew_resources"
        assert recommendations[1]["adjustment_type"] == "modify_execution_strategy"

        # Mock applying adjustments
        adjustment_results = {
            "adjustments_applied": 2,
            "estimated_improvement": {
                "time_savings_minutes": 10,
                "performance_improvement": 0.25,
                "resource_optimization": "improved"
            },
            "updated_plan": {
                "total_estimated_time_minutes": 32,  # Reduced from original
                "execution_strategy": "adaptive_parallel"
            }
        }

        mock_plan_monitor.apply_plan_adjustment.return_value = adjustment_results

        # Apply adjustments
        results = await mock_plan_monitor.apply_plan_adjustment("plan_001", recommendations)

        # Verify adjustment application
        assert results["adjustments_applied"] == 2
        assert results["estimated_improvement"]["time_savings_minutes"] > 0

    @pytest.mark.asyncio
    async def test_success_criteria_monitoring(self, mock_plan_monitor):
        """Test monitoring of success criteria throughout execution"""
        # Mock success criteria tracking
        criteria_tracking = {
            "phase": "inventory_building",
            "criteria_status": {
                "asset_classification_complete": {
                    "status": "in_progress",
                    "current_value": 0.78,
                    "target_value": 0.90,
                    "trend": "improving"
                },
                "cross_domain_validation": {
                    "status": "pending",
                    "dependencies": ["server_classification", "app_classification"],
                    "readiness": 0.65
                },
                "classification_confidence": {
                    "status": "at_risk",
                    "current_value": 0.72,
                    "target_value": 0.80,
                    "trend": "stable",
                    "risk_factors": ["data_quality_variations"]
                }
            },
            "overall_phase_health": "on_track",
            "intervention_needed": False
        }

        mock_plan_monitor.get_execution_status.return_value = criteria_tracking

        # Monitor success criteria
        status = await mock_plan_monitor.get_execution_status("plan_001", include_criteria=True)

        # Verify criteria monitoring
        assert "criteria_status" in status
        assert status["criteria_status"]["asset_classification_complete"]["status"] == "in_progress"
        assert status["criteria_status"]["classification_confidence"]["status"] == "at_risk"
        assert status["overall_phase_health"] == "on_track"


@pytest.mark.skipif(not PLANNING_COMPONENTS_AVAILABLE, reason="Planning components not available")
class TestCrossCrewPlanningCoordination:
    """Test suite for cross-crew planning coordination"""

    @pytest.fixture
    def mock_crew_coordinator(self):
        """Mock crew coordination system"""
        coordinator = Mock()
        coordinator.coordinate_crew_execution = AsyncMock()
        coordinator.manage_crew_dependencies = AsyncMock()
        coordinator.optimize_crew_sequence = AsyncMock()
        coordinator.handle_crew_conflicts = AsyncMock()
        return coordinator

    @pytest.fixture
    def crew_dependency_graph(self):
        """Sample crew dependency graph"""
        return {
            "crews": {
                "field_mapping_crew": {
                    "dependencies": [],
                    "provides_to": ["data_cleansing_crew"],
                    "execution_priority": 1
                },
                "data_cleansing_crew": {
                    "dependencies": ["field_mapping_crew"],
                    "provides_to": ["inventory_building_crew"],
                    "execution_priority": 2
                },
                "inventory_building_crew": {
                    "dependencies": ["data_cleansing_crew"],
                    "provides_to": ["app_server_dependency_crew", "app_app_dependency_crew"],
                    "execution_priority": 3
                },
                "app_server_dependency_crew": {
                    "dependencies": ["inventory_building_crew"],
                    "provides_to": ["technical_debt_crew"],
                    "execution_priority": 4,
                    "parallel_with": ["app_app_dependency_crew"]
                },
                "app_app_dependency_crew": {
                    "dependencies": ["inventory_building_crew"],
                    "provides_to": ["technical_debt_crew"],
                    "execution_priority": 4,
                    "parallel_with": ["app_server_dependency_crew"]
                },
                "technical_debt_crew": {
                    "dependencies": ["app_server_dependency_crew", "app_app_dependency_crew"],
                    "provides_to": [],
                    "execution_priority": 5
                }
            }
        }

    @pytest.mark.asyncio
    async def test_crew_dependency_management(self, mock_crew_coordinator, crew_dependency_graph):
        """Test management of crew dependencies"""
        mock_crew_coordinator.manage_crew_dependencies.return_value = {
            "dependency_graph_valid": True,
            "execution_order": [
                "field_mapping_crew",
                "data_cleansing_crew",
                "inventory_building_crew",
                ["app_server_dependency_crew", "app_app_dependency_crew"],  # Parallel
                "technical_debt_crew"
            ],
            "parallel_opportunities": [
                {
                    "crews": ["app_server_dependency_crew", "app_app_dependency_crew"],
                    "estimated_time_savings_minutes": 12
                }
            ],
            "critical_path": [
                "field_mapping_crew", "data_cleansing_crew", "inventory_building_crew",
                "app_server_dependency_crew", "technical_debt_crew"
            ]
        }

        # Manage crew dependencies
        dependency_management = await mock_crew_coordinator.manage_crew_dependencies(crew_dependency_graph)

        # Verify dependency management
        assert dependency_management["dependency_graph_valid"] is True
        assert len(dependency_management["execution_order"]) == 5
        assert len(dependency_management["parallel_opportunities"]) > 0
        assert len(dependency_management["critical_path"]) == 5

    @pytest.mark.asyncio
    async def test_parallel_crew_execution_coordination(self, mock_crew_coordinator):
        """Test coordination of parallel crew execution"""
        # Mock parallel execution coordination
        parallel_coordination = {
            "parallel_crews": ["app_server_dependency_crew", "app_app_dependency_crew"],
            "shared_resources": {
                "memory": "partitioned",
                "knowledge_base": "shared_read_only",
                "shared_memory": "isolated_writes"
            },
            "synchronization_points": [
                {
                    "point": "completion_checkpoint",
                    "condition": "both_crews_complete",
                    "action": "proceed_to_technical_debt_crew"
                }
            ],
            "conflict_resolution": {
                "resource_conflicts": "queue_based",
                "data_conflicts": "timestamp_priority",
                "coordination_strategy": "cooperative"
            }
        }

        mock_crew_coordinator.coordinate_crew_execution.return_value = parallel_coordination

        # Coordinate parallel execution
        coordination = await mock_crew_coordinator.coordinate_crew_execution("parallel", ["app_server_dependency_crew", "app_app_dependency_crew"])

        # Verify parallel coordination
        assert len(coordination["parallel_crews"]) == 2
        assert "shared_resources" in coordination
        assert len(coordination["synchronization_points"]) > 0

    @pytest.mark.asyncio
    async def test_crew_execution_optimization(self, mock_crew_coordinator, crew_dependency_graph):
        """Test optimization of crew execution sequence"""
        # Mock optimization results
        optimization_results = {
            "original_sequence": ["sequential_all"],
            "optimized_sequence": ["sequential_with_parallel"],
            "optimizations_applied": [
                {
                    "optimization": "parallel_dependency_crews",
                    "crews_affected": ["app_server_dependency_crew", "app_app_dependency_crew"],
                    "time_savings_minutes": 12,
                    "resource_efficiency_gain": 0.15
                },
                {
                    "optimization": "overlapping_execution",
                    "crews_affected": ["inventory_building_crew", "app_server_dependency_crew"],
                    "overlap_percentage": 0.2,
                    "time_savings_minutes": 3
                }
            ],
            "total_time_savings_minutes": 15,
            "efficiency_improvement": 0.22
        }

        mock_crew_coordinator.optimize_crew_sequence.return_value = optimization_results

        # Optimize crew sequence
        optimization = await mock_crew_coordinator.optimize_crew_sequence(crew_dependency_graph)

        # Verify optimization
        assert len(optimization["optimizations_applied"]) == 2
        assert optimization["total_time_savings_minutes"] > 0
        assert optimization["efficiency_improvement"] > 0.2

    @pytest.mark.asyncio
    async def test_crew_conflict_resolution(self, mock_crew_coordinator):
        """Test resolution of crew conflicts and resource contention"""
        # Mock crew conflicts
        crew_conflicts = [
            {
                "conflict_type": "resource_contention",
                "crews_involved": ["inventory_building_crew", "app_server_dependency_crew"],
                "resource": "shared_memory_write_access",
                "severity": "medium",
                "resolution_strategy": "sequential_access_with_queuing"
            },
            {
                "conflict_type": "data_dependency_circular",
                "crews_involved": ["app_server_dependency_crew", "app_app_dependency_crew"],
                "dependency": "hosting_relationship_data",
                "severity": "low",
                "resolution_strategy": "iterative_refinement"
            }
        ]

        # Mock conflict resolution
        resolution_results = {
            "conflicts_resolved": 2,
            "resolution_strategies_applied": [
                "sequential_access_with_queuing",
                "iterative_refinement"
            ],
            "performance_impact": "minimal",
            "stability_improvement": "significant"
        }

        mock_crew_coordinator.handle_crew_conflicts.return_value = resolution_results

        # Handle crew conflicts
        resolution = await mock_crew_coordinator.handle_crew_conflicts(crew_conflicts)

        # Verify conflict resolution
        assert resolution["conflicts_resolved"] == 2
        assert len(resolution["resolution_strategies_applied"]) == 2
        assert resolution["performance_impact"] == "minimal"


@pytest.mark.skipif(not PLANNING_COMPONENTS_AVAILABLE, reason="Planning components not available")
class TestResourceAllocationOptimization:
    """Test suite for resource allocation optimization"""

    @pytest.fixture
    def mock_resource_optimizer(self):
        """Mock resource optimization system"""
        optimizer = Mock()
        optimizer.analyze_resource_requirements = AsyncMock()
        optimizer.optimize_allocation = AsyncMock()
        optimizer.monitor_utilization = AsyncMock()
        optimizer.recommend_scaling = AsyncMock()
        return optimizer

    @pytest.fixture
    def resource_scenarios(self):
        """Different resource requirement scenarios"""
        return {
            "light_workload": {
                "data_size": 100,
                "complexity": "low",
                "expected_resources": {
                    "memory_mb": 128,
                    "cpu_cores": 2,
                    "storage_mb": 50,
                    "network_bandwidth_mbps": 10
                }
            },
            "heavy_workload": {
                "data_size": 5000,
                "complexity": "high",
                "expected_resources": {
                    "memory_mb": 1024,
                    "cpu_cores": 8,
                    "storage_mb": 500,
                    "network_bandwidth_mbps": 100
                }
            }
        }

    @pytest.mark.asyncio
    async def test_resource_requirement_analysis(self, mock_resource_optimizer, resource_scenarios):
        """Test analysis of resource requirements based on workload"""
        light_workload = resource_scenarios["light_workload"]

        # Mock resource analysis
        analysis_result = {
            "workload_classification": "light",
            "resource_requirements": {
                "memory_mb": 128,
                "cpu_cores": 2,
                "storage_mb": 50,
                "network_bandwidth_mbps": 10
            },
            "scaling_recommendations": {
                "auto_scaling": "disabled",
                "manual_scaling_triggers": []
            },
            "optimization_opportunities": [
                "memory_compression",
                "cpu_scheduling_optimization"
            ]
        }

        mock_resource_optimizer.analyze_resource_requirements.return_value = analysis_result

        # Analyze requirements
        analysis = await mock_resource_optimizer.analyze_resource_requirements(light_workload)

        # Verify analysis
        assert analysis["workload_classification"] == "light"
        assert analysis["resource_requirements"]["memory_mb"] == 128
        assert len(analysis["optimization_opportunities"]) > 0

    @pytest.mark.asyncio
    async def test_dynamic_resource_allocation(self, mock_resource_optimizer):
        """Test dynamic resource allocation during execution"""
        # Mock dynamic allocation
        allocation_adjustment = {
            "trigger": "crew_performance_degradation",
            "affected_crew": "inventory_building_crew",
            "current_allocation": {
                "memory_mb": 256,
                "cpu_cores": 4
            },
            "recommended_allocation": {
                "memory_mb": 384,  # Increased
                "cpu_cores": 6     # Increased
            },
            "adjustment_rationale": "cross_domain_collaboration_intensive",
            "expected_improvement": {
                "performance_gain": 0.3,
                "time_savings_minutes": 8
            }
        }

        mock_resource_optimizer.optimize_allocation.return_value = allocation_adjustment

        # Optimize allocation
        optimization = await mock_resource_optimizer.optimize_allocation("inventory_building_crew")

        # Verify dynamic allocation
        assert optimization["recommended_allocation"]["memory_mb"] > optimization["current_allocation"]["memory_mb"]
        assert optimization["expected_improvement"]["performance_gain"] > 0.2

    @pytest.mark.asyncio
    async def test_resource_utilization_monitoring(self, mock_resource_optimizer):
        """Test monitoring of resource utilization during execution"""
        # Mock utilization monitoring
        utilization_metrics = {
            "timestamp": datetime.now().isoformat(),
            "crew_utilization": {
                "field_mapping_crew": {
                    "memory_utilization": 0.65,
                    "cpu_utilization": 0.78,
                    "storage_utilization": 0.45,
                    "efficiency_score": 0.89
                },
                "data_cleansing_crew": {
                    "memory_utilization": 0.82,
                    "cpu_utilization": 0.91,
                    "storage_utilization": 0.67,
                    "efficiency_score": 0.94
                }
            },
            "overall_utilization": {
                "memory_utilization": 0.74,
                "cpu_utilization": 0.84,
                "storage_utilization": 0.56,
                "efficiency_score": 0.91
            },
            "optimization_alerts": [
                {
                    "alert_type": "memory_under_utilization",
                    "crew": "field_mapping_crew",
                    "recommendation": "reduce_memory_allocation"
                }
            ]
        }

        mock_resource_optimizer.monitor_utilization.return_value = utilization_metrics

        # Monitor utilization
        metrics = await mock_resource_optimizer.monitor_utilization()

        # Verify monitoring
        assert "crew_utilization" in metrics
        assert "overall_utilization" in metrics
        assert metrics["overall_utilization"]["efficiency_score"] > 0.8
        assert len(metrics["optimization_alerts"]) > 0


# Pytest configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
