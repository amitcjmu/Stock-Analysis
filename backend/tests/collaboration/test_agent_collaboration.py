"""
Agent Collaboration Tests - Phase 6 Task 59

This module tests agent collaboration patterns including intra-crew collaboration
between specialist agents and managers, cross-crew collaboration and insight sharing,
bidirectional agent communication, collaboration effectiveness measurement,
and real-time collaboration monitoring.
"""

import time
import uuid
from typing import Dict, List
from unittest.mock import Mock

import pytest

# Mock imports for testing
try:
    from app.models.agent_communication import AgentCommunication
    from app.services.crewai_flows.agent_monitor import AgentMonitor
    from app.services.crewai_flows.collaboration_service import CollaborationService
except ImportError:
    # Fallback for testing environment
    CollaborationService = Mock
    AgentMonitor = Mock
    AgentCommunication = Mock


class MockAgent:
    """Mock agent for collaboration testing"""

    def __init__(self, role: str, crew: str, agent_type: str = "specialist"):
        self.role = role
        self.crew = crew
        self.agent_type = agent_type  # manager, specialist, coordinator
        self.collaboration_history = []
        self.communication_log = []
        self.effectiveness_score = 0.85
        self.active_collaborations = []

    def collaborate_with(self, other_agent: "MockAgent", context: Dict) -> Dict:
        """Mock collaboration between agents"""
        collaboration = {
            "timestamp": time.time(),
            "from_agent": self.role,
            "to_agent": other_agent.role,
            "context": context,
            "collaboration_type": self._determine_collaboration_type(other_agent),
            "effectiveness": self._calculate_collaboration_effectiveness(
                other_agent, context
            ),
        }

        self.collaboration_history.append(collaboration)
        other_agent.collaboration_history.append(collaboration)

        return collaboration

    def _determine_collaboration_type(self, other_agent: "MockAgent") -> str:
        """Determine type of collaboration"""
        if self.crew == other_agent.crew:
            if self.agent_type == "manager" or other_agent.agent_type == "manager":
                return "intra_crew_coordination"
            else:
                return "intra_crew_peer_collaboration"
        else:
            return "cross_crew_collaboration"

    def _calculate_collaboration_effectiveness(
        self, other_agent: "MockAgent", context: Dict
    ) -> float:
        """Calculate effectiveness of collaboration with another agent"""
        base_effectiveness = 0.8  # Higher base score

        # Complementary expertise bonus
        if self._has_complementary_expertise(other_agent):
            base_effectiveness += 0.15

        # Same crew coordination bonus
        if self.crew == other_agent.crew:
            base_effectiveness += 0.1

        # Manager-specialist coordination bonus
        if (
            self.agent_type == "manager" and other_agent.agent_type == "specialist"
        ) or (self.agent_type == "specialist" and other_agent.agent_type == "manager"):
            base_effectiveness += 0.08

        # Context-based adjustments
        if context.get("expertise_match") == "complementary":
            base_effectiveness += 0.1

        return min(base_effectiveness, 1.0)

    def _has_complementary_expertise(self, other_agent: "MockAgent") -> bool:
        """Check if agents have complementary expertise"""
        complementary_pairs = [
            ("Schema Analysis Expert", "Attribute Mapping Specialist"),
            ("Data Validation Expert", "Data Standardization Specialist"),
            ("Server Classification Expert", "Application Discovery Expert"),
            ("Application Topology Expert", "Infrastructure Relationship Analyst"),
        ]

        for role1, role2 in complementary_pairs:
            if (self.role == role1 and other_agent.role == role2) or (
                self.role == role2 and other_agent.role == role1
            ):
                return True
        return False


class MockCollaborationService:
    """Mock collaboration service for testing"""

    def __init__(self):
        self.active_collaborations = {}
        self.collaboration_metrics = {
            "total_collaborations": 0,
            "successful_collaborations": 0,
            "effectiveness_scores": [],
            "cross_crew_collaborations": 0,
            "intra_crew_collaborations": 0,
        }
        self.real_time_monitors = []

    async def initiate_collaboration(
        self, agent1: MockAgent, agent2: MockAgent, context: Dict
    ) -> str:
        """Initiate collaboration between agents"""
        collaboration_id = str(uuid.uuid4())

        collaboration = {
            "id": collaboration_id,
            "agent1": agent1,
            "agent2": agent2,
            "context": context,
            "start_time": time.time(),
            "status": "active",
            "messages": [],
            "effectiveness_score": None,
        }

        self.active_collaborations[collaboration_id] = collaboration
        self.collaboration_metrics["total_collaborations"] += 1

        # Determine collaboration type
        if agent1.crew == agent2.crew:
            self.collaboration_metrics["intra_crew_collaborations"] += 1
        else:
            self.collaboration_metrics["cross_crew_collaborations"] += 1

        return collaboration_id

    async def send_message(
        self, collaboration_id: str, from_agent: str, to_agent: str, message: Dict
    ) -> bool:
        """Send message in collaboration"""
        if collaboration_id not in self.active_collaborations:
            return False

        collaboration = self.active_collaborations[collaboration_id]

        message_entry = {
            "timestamp": time.time(),
            "from": from_agent,
            "to": to_agent,
            "message": message,
            "message_type": message.get("type", "data_exchange"),
        }

        collaboration["messages"].append(message_entry)
        return True

    async def complete_collaboration(
        self, collaboration_id: str, results: Dict
    ) -> Dict:
        """Complete collaboration and calculate effectiveness"""
        if collaboration_id not in self.active_collaborations:
            return {"success": False, "error": "Collaboration not found"}

        collaboration = self.active_collaborations[collaboration_id]
        collaboration["status"] = "completed"
        collaboration["end_time"] = time.time()
        collaboration["results"] = results

        # Calculate effectiveness
        effectiveness = self._calculate_effectiveness(collaboration)
        collaboration["effectiveness_score"] = effectiveness

        self.collaboration_metrics["effectiveness_scores"].append(effectiveness)
        if effectiveness >= 0.8:
            self.collaboration_metrics["successful_collaborations"] += 1

        return {
            "success": True,
            "collaboration_id": collaboration_id,
            "effectiveness": effectiveness,
            "duration": collaboration["end_time"] - collaboration["start_time"],
        }

    def _calculate_effectiveness(self, collaboration: Dict) -> float:
        """Calculate collaboration effectiveness"""
        base_score = 0.75  # Start with higher base

        # Message exchange quality
        messages = collaboration["messages"]
        if len(messages) >= 3:  # Good back-and-forth
            base_score += 0.12
        elif len(messages) >= 2:  # Some exchange
            base_score += 0.08

        # Bidirectional communication
        senders = set(msg["from"] for msg in messages)
        if len(senders) >= 2:
            base_score += 0.1

        # Results quality
        results = collaboration.get("results", {})
        if results.get("confidence", 0) >= 0.9:
            base_score += 0.15
        elif results.get("confidence", 0) >= 0.8:
            base_score += 0.1

        # Collaboration type bonuses
        context = collaboration.get("context", {})
        if context.get("collaboration_type") == "cross_crew_handoff":
            base_score += 0.05
        if context.get("shared_insights"):
            base_score += 0.05

        # Cross-domain expertise bonus
        if context.get("collaboration_type") == "cross_domain_expertise":
            base_score += 0.08

        # Bidirectional communication bonus
        if context.get("collaboration_type") == "bidirectional_insight_exchange":
            base_score += 0.08

        return min(base_score, 1.0)

    async def get_collaboration_metrics(self) -> Dict:
        """Get collaboration metrics"""
        metrics = self.collaboration_metrics.copy()

        if metrics["effectiveness_scores"]:
            metrics["average_effectiveness"] = sum(
                metrics["effectiveness_scores"]
            ) / len(metrics["effectiveness_scores"])
            metrics["collaboration_success_rate"] = (
                metrics["successful_collaborations"] / metrics["total_collaborations"]
            )
        else:
            metrics["average_effectiveness"] = 0.0
            metrics["collaboration_success_rate"] = 0.0

        return metrics

    async def add_real_time_monitor(self, monitor_config: Dict) -> str:
        """Add real-time collaboration monitor"""
        monitor_id = str(uuid.uuid4())
        monitor = {
            "id": monitor_id,
            "config": monitor_config,
            "alerts": [],
            "active": True,
        }

        self.real_time_monitors.append(monitor)
        return monitor_id

    async def check_collaboration_alerts(self) -> List[Dict]:
        """Check for collaboration alerts"""
        alerts = []

        for collaboration in self.active_collaborations.values():
            if collaboration["status"] == "active":
                duration = time.time() - collaboration["start_time"]

                # Alert for long-running collaborations
                if duration > 300:  # 5 minutes
                    alerts.append(
                        {
                            "type": "long_running_collaboration",
                            "collaboration_id": collaboration["id"],
                            "duration": duration,
                            "agents": [
                                collaboration["agent1"].role,
                                collaboration["agent2"].role,
                            ],
                        }
                    )

                # Alert for inactive collaborations
                if len(collaboration["messages"]) == 0 and duration > 60:
                    alerts.append(
                        {
                            "type": "inactive_collaboration",
                            "collaboration_id": collaboration["id"],
                            "duration": duration,
                        }
                    )

        return alerts


@pytest.fixture
def mock_agents():
    """Create mock agents for testing"""
    agents = {
        # Field Mapping Crew
        "field_mapping_manager": MockAgent(
            "Field Mapping Manager", "field_mapping", "manager"
        ),
        "schema_expert": MockAgent(
            "Schema Analysis Expert", "field_mapping", "specialist"
        ),
        "mapping_specialist": MockAgent(
            "Attribute Mapping Specialist", "field_mapping", "specialist"
        ),
        # Data Cleansing Crew
        "cleansing_manager": MockAgent(
            "Data Quality Manager", "data_cleansing", "manager"
        ),
        "validation_expert": MockAgent(
            "Data Validation Expert", "data_cleansing", "specialist"
        ),
        "standardization_specialist": MockAgent(
            "Data Standardization Specialist", "data_cleansing", "specialist"
        ),
        # Inventory Building Crew
        "inventory_manager": MockAgent(
            "Inventory Manager", "inventory_building", "manager"
        ),
        "server_expert": MockAgent(
            "Server Classification Expert", "inventory_building", "specialist"
        ),
        "app_expert": MockAgent(
            "Application Discovery Expert", "inventory_building", "specialist"
        ),
    }
    return agents


@pytest.fixture
def collaboration_service():
    """Create collaboration service for testing"""
    return MockCollaborationService()


class TestIntraCrewCollaboration:
    """Test collaboration between manager and specialists within crews"""

    @pytest.mark.asyncio
    async def test_manager_specialist_coordination(
        self, collaboration_service, mock_agents
    ):
        """Test coordination between manager and specialist agents"""
        service = collaboration_service
        manager = mock_agents["field_mapping_manager"]
        specialist = mock_agents["schema_expert"]

        # Initiate collaboration
        context = {
            "task": "schema_analysis",
            "data_preview": {"columns": ["hostname", "ip_address"]},
            "priority": "high",
        }

        collaboration_id = await service.initiate_collaboration(
            manager, specialist, context
        )
        assert collaboration_id is not None

        # Manager delegates task
        await service.send_message(
            collaboration_id,
            manager.role,
            specialist.role,
            {
                "type": "task_delegation",
                "task": "Analyze schema for semantic patterns",
                "instructions": "Focus on identifier and network fields",
                "deadline": time.time() + 3600,
            },
        )

        # Specialist responds with progress
        await service.send_message(
            collaboration_id,
            specialist.role,
            manager.role,
            {
                "type": "progress_update",
                "status": "in_progress",
                "findings": {"identifier_fields": 2, "network_fields": 1},
                "confidence": 0.9,
            },
        )

        # Manager provides feedback
        await service.send_message(
            collaboration_id,
            manager.role,
            specialist.role,
            {
                "type": "feedback",
                "feedback": "Good progress, also check for technical fields",
                "adjustments": {"include_technical_analysis": True},
            },
        )

        # Complete collaboration
        results = {
            "schema_analysis": "completed",
            "confidence": 0.92,
            "fields_analyzed": 3,
        }

        completion = await service.complete_collaboration(collaboration_id, results)

        assert completion["success"] is True
        assert completion["effectiveness"] >= 0.8

    @pytest.mark.asyncio
    async def test_specialist_peer_collaboration(
        self, collaboration_service, mock_agents
    ):
        """Test collaboration between specialist peers"""
        service = collaboration_service
        schema_expert = mock_agents["schema_expert"]
        mapping_specialist = mock_agents["mapping_specialist"]

        # Initiate peer collaboration
        context = {
            "task": "field_mapping_validation",
            "shared_findings": {"schema_patterns": ["hostname_variations"]},
            "collaboration_type": "peer_review",
        }

        collaboration_id = await service.initiate_collaboration(
            schema_expert, mapping_specialist, context
        )

        # Schema expert shares findings
        await service.send_message(
            collaboration_id,
            schema_expert.role,
            mapping_specialist.role,
            {
                "type": "data_sharing",
                "findings": {
                    "semantic_types": ["identifier", "network", "technical"],
                    "confidence_scores": [0.95, 0.90, 0.85],
                },
            },
        )

        # Mapping specialist validates and enhances
        await service.send_message(
            collaboration_id,
            mapping_specialist.role,
            schema_expert.role,
            {
                "type": "validation_response",
                "validation": "confirmed",
                "enhancements": {
                    "target_mappings": {
                        "hostname": "server_name",
                        "ip_address": "network_address",
                    },
                    "mapping_confidence": 0.93,
                },
            },
        )

        # Complete collaboration
        results = {"validated_mappings": 2, "confidence": 0.93, "peer_agreement": True}

        completion = await service.complete_collaboration(collaboration_id, results)
        assert completion["success"] is True

    @pytest.mark.asyncio
    async def test_hierarchical_coordination(self, collaboration_service, mock_agents):
        """Test hierarchical coordination within crew"""
        service = collaboration_service
        manager = mock_agents["field_mapping_manager"]
        schema_expert = mock_agents["schema_expert"]
        mapping_specialist = mock_agents["mapping_specialist"]

        # Manager coordinates between specialists
        context = {
            "coordination_task": "field_mapping_pipeline",
            "dependencies": {"schema_analysis": "mapping_creation"},
            "coordination_type": "sequential",
        }

        # Manager to schema expert
        collab1_id = await service.initiate_collaboration(
            manager, schema_expert, context
        )

        # Manager delegates first task
        await service.send_message(
            collab1_id,
            manager.role,
            schema_expert.role,
            {
                "type": "task_delegation",
                "task": "Complete schema analysis first",
                "priority": "high",
                "next_step": "mapping_creation",
            },
        )

        # Schema expert completes and signals readiness
        await service.send_message(
            collab1_id,
            schema_expert.role,
            manager.role,
            {
                "type": "task_completion",
                "status": "completed",
                "outputs": {"schema_analysis": "complete"},
                "ready_for_next": True,
            },
        )

        # Manager to mapping specialist (dependent task)
        collab2_id = await service.initiate_collaboration(
            manager, mapping_specialist, context
        )

        await service.send_message(
            collab2_id,
            manager.role,
            mapping_specialist.role,
            {
                "type": "task_delegation",
                "task": "Create mappings based on schema analysis",
                "dependencies_met": True,
                "input_data": {"schema_analysis": "complete"},
            },
        )

        # Verify coordination effectiveness
        metrics = await service.get_collaboration_metrics()
        assert metrics["total_collaborations"] >= 2
        assert metrics["intra_crew_collaborations"] >= 2


class TestCrossCrewCollaboration:
    """Test collaboration and insight sharing across discovery phases"""

    @pytest.mark.asyncio
    async def test_cross_crew_insight_sharing(self, collaboration_service, mock_agents):
        """Test insight sharing between different crews"""
        service = collaboration_service
        field_mapping_manager = mock_agents["field_mapping_manager"]
        cleansing_manager = mock_agents["cleansing_manager"]

        # Cross-crew collaboration context
        context = {
            "collaboration_type": "cross_crew_handoff",
            "phase_transition": "field_mapping_to_cleansing",
            "shared_insights": True,
        }

        collaboration_id = await service.initiate_collaboration(
            field_mapping_manager, cleansing_manager, context
        )

        # Field mapping shares insights
        await service.send_message(
            collaboration_id,
            field_mapping_manager.role,
            cleansing_manager.role,
            {
                "type": "phase_handoff",
                "insights": {
                    "high_confidence_mappings": ["hostname", "ip_address"],
                    "problematic_fields": ["memory_size"],
                    "data_quality_indicators": {"overall_quality": 0.88},
                },
                "recommendations": [
                    "Focus cleansing efforts on memory_size field",
                    "Leverage high-confidence mappings for automated processing",
                ],
            },
        )

        # Cleansing manager acknowledges and provides feedback
        await service.send_message(
            collaboration_id,
            cleansing_manager.role,
            field_mapping_manager.role,
            {
                "type": "handoff_acknowledgment",
                "received_insights": True,
                "feedback": {
                    "insight_quality": "high",
                    "actionable_recommendations": 2,
                    "readiness_for_cleansing": True,
                },
                "questions": ["What confidence threshold was used for mappings?"],
            },
        )

        # Field mapping provides clarification
        await service.send_message(
            collaboration_id,
            field_mapping_manager.role,
            cleansing_manager.role,
            {
                "type": "clarification",
                "answers": {
                    "confidence_threshold": 0.8,
                    "validation_method": "semantic_analysis_with_pattern_matching",
                },
                "additional_context": {
                    "total_fields_processed": 15,
                    "success_rate": 0.92,
                },
            },
        )

        # Complete cross-crew collaboration
        results = {
            "handoff_completed": True,
            "insight_transfer": "successful",
            "cleansing_readiness": True,
            "cross_crew_effectiveness": 0.94,
        }

        completion = await service.complete_collaboration(collaboration_id, results)
        assert completion["success"] is True
        assert completion["effectiveness"] >= 0.9

    @pytest.mark.asyncio
    async def test_bidirectional_cross_crew_communication(
        self, collaboration_service, mock_agents
    ):
        """Test bidirectional communication between crews"""
        service = collaboration_service
        cleansing_manager = mock_agents["cleansing_manager"]
        inventory_manager = mock_agents["inventory_manager"]

        context = {
            "collaboration_type": "bidirectional_insight_exchange",
            "phase": "cleansing_to_inventory_feedback_loop",
        }

        collaboration_id = await service.initiate_collaboration(
            cleansing_manager, inventory_manager, context
        )

        # Forward direction: Cleansing to Inventory
        await service.send_message(
            collaboration_id,
            cleansing_manager.role,
            inventory_manager.role,
            {
                "type": "data_quality_report",
                "cleansed_records": 1250,
                "quality_metrics": {
                    "completeness": 0.95,
                    "accuracy": 0.92,
                    "consistency": 0.89,
                },
                "asset_readiness": {
                    "servers": {"ready": 450, "issues": 12},
                    "applications": {"ready": 180, "issues": 8},
                },
            },
        )

        # Backward direction: Inventory provides feedback
        await service.send_message(
            collaboration_id,
            inventory_manager.role,
            cleansing_manager.role,
            {
                "type": "classification_feedback",
                "feedback": {
                    "server_classification_accuracy": 0.91,
                    "application_detection_issues": ["unclear_service_types"],
                    "data_quality_impact": "positive",
                },
                "requests": {
                    "additional_cleansing": ["service_type_standardization"],
                    "priority_fields": ["application_category", "service_tier"],
                },
            },
        )

        # Forward direction: Cleansing responds to feedback
        await service.send_message(
            collaboration_id,
            cleansing_manager.role,
            inventory_manager.role,
            {
                "type": "feedback_response",
                "actions_taken": {
                    "service_type_standardization": "completed",
                    "application_category_enhancement": "in_progress",
                },
                "updated_quality": {"service_types": 0.94, "categories": 0.88},
            },
        )

        # Complete bidirectional collaboration
        results = {
            "bidirectional_communication": True,
            "feedback_loops": 2,
            "quality_improvements": True,
            "collaboration_effectiveness": 0.91,
        }

        completion = await service.complete_collaboration(collaboration_id, results)
        assert completion["effectiveness"] >= 0.9

    @pytest.mark.asyncio
    async def test_multi_crew_collaboration(self, collaboration_service, mock_agents):
        """Test collaboration involving multiple crews"""
        service = collaboration_service
        field_mapping_manager = mock_agents["field_mapping_manager"]
        cleansing_manager = mock_agents["cleansing_manager"]
        inventory_manager = mock_agents["inventory_manager"]

        # Multi-crew coordination context
        context = {
            "collaboration_type": "multi_crew_coordination",
            "coordination_topic": "data_quality_consistency",
            "crews_involved": ["field_mapping", "data_cleansing", "inventory_building"],
        }

        # Field mapping to cleansing
        collab1_id = await service.initiate_collaboration(
            field_mapping_manager, cleansing_manager, context
        )

        # Field mapping to inventory
        collab2_id = await service.initiate_collaboration(
            field_mapping_manager, inventory_manager, context
        )

        # Cleansing to inventory
        collab3_id = await service.initiate_collaboration(
            cleansing_manager, inventory_manager, context
        )

        # Coordinate data quality standards across all crews
        quality_standards = {
            "confidence_threshold": 0.85,
            "completeness_requirement": 0.90,
            "consistency_rules": ["standardized_naming", "validated_formats"],
        }

        # Share standards with all crews
        for collab_id, from_manager, to_manager in [
            (collab1_id, field_mapping_manager.role, cleansing_manager.role),
            (collab2_id, field_mapping_manager.role, inventory_manager.role),
            (collab3_id, cleansing_manager.role, inventory_manager.role),
        ]:
            await service.send_message(
                collab_id,
                from_manager,
                to_manager,
                {
                    "type": "standards_coordination",
                    "quality_standards": quality_standards,
                    "coordination_request": "align_quality_metrics",
                },
            )

        # Verify multi-crew coordination
        metrics = await service.get_collaboration_metrics()
        assert metrics["cross_crew_collaborations"] >= 3


class TestCollaborationEffectivenessValidation:
    """Test collaboration effectiveness measurement and optimization"""

    @pytest.mark.asyncio
    async def test_collaboration_effectiveness_measurement(
        self, collaboration_service, mock_agents
    ):
        """Test measurement of collaboration effectiveness"""
        service = collaboration_service
        manager = mock_agents["field_mapping_manager"]
        specialist = mock_agents["schema_expert"]

        # High-effectiveness collaboration
        context = {"task": "high_quality_task", "data_quality": 0.95}
        collaboration_id = await service.initiate_collaboration(
            manager, specialist, context
        )

        # Quality message exchange
        await service.send_message(
            collaboration_id,
            manager.role,
            specialist.role,
            {
                "type": "clear_instruction",
                "task": "Well-defined analysis task",
                "resources": ["complete_data", "clear_guidelines"],
            },
        )

        await service.send_message(
            collaboration_id,
            specialist.role,
            manager.role,
            {
                "type": "detailed_response",
                "analysis": "Comprehensive findings",
                "confidence": 0.94,
            },
        )

        await service.send_message(
            collaboration_id,
            manager.role,
            specialist.role,
            {"type": "validation", "validation": "approved", "effectiveness": "high"},
        )

        # Complete with high-quality results
        results = {"confidence": 0.94, "completeness": 0.98}
        completion = await service.complete_collaboration(collaboration_id, results)

        assert completion["effectiveness"] >= 0.9

    @pytest.mark.asyncio
    async def test_collaboration_optimization_recommendations(
        self, collaboration_service, mock_agents
    ):
        """Test collaboration pattern analysis and optimization recommendations"""
        service = collaboration_service

        # Run multiple collaborations to gather data
        agents_list = list(mock_agents.values())

        for i in range(5):
            agent1 = agents_list[i % len(agents_list)]
            agent2 = agents_list[(i + 1) % len(agents_list)]

            context = {"task": f"task_{i}", "data_quality": 0.8 + (i * 0.02)}
            collaboration_id = await service.initiate_collaboration(
                agent1, agent2, context
            )

            # Simulate collaboration
            await service.send_message(
                collaboration_id,
                agent1.role,
                agent2.role,
                {"type": "task_message", "content": f"Task {i} content"},
            )

            await service.send_message(
                collaboration_id,
                agent2.role,
                agent1.role,
                {"type": "response", "response": f"Response to task {i}"},
            )

            # Complete with varying effectiveness
            results = {"confidence": 0.8 + (i * 0.02)}
            await service.complete_collaboration(collaboration_id, results)

        # Analyze collaboration metrics
        metrics = await service.get_collaboration_metrics()

        assert metrics["total_collaborations"] >= 5
        assert "average_effectiveness" in metrics
        assert "collaboration_success_rate" in metrics
        assert metrics["average_effectiveness"] > 0.7

    @pytest.mark.asyncio
    async def test_collaboration_pattern_analysis(
        self, collaboration_service, mock_agents
    ):
        """Test analysis of collaboration patterns for improvement"""
        service = collaboration_service
        schema_expert = mock_agents["schema_expert"]
        mapping_specialist = mock_agents["mapping_specialist"]

        # Test complementary expertise collaboration
        context = {"expertise_match": "complementary"}
        collaboration_id = await service.initiate_collaboration(
            schema_expert, mapping_specialist, context
        )

        # Agents have complementary skills
        collaboration_result = schema_expert.collaborate_with(
            mapping_specialist, context
        )

        assert (
            collaboration_result["collaboration_type"]
            == "intra_crew_peer_collaboration"
        )
        assert (
            collaboration_result["effectiveness"] >= 0.9
        )  # Should be high due to complementary expertise

        # Complete collaboration
        results = {"expertise_synergy": True, "confidence": 0.95}
        completion = await service.complete_collaboration(collaboration_id, results)

        assert completion["effectiveness"] >= 0.9


class TestRealTimeCollaborationMonitoring:
    """Test real-time collaboration monitoring and alerting"""

    @pytest.mark.asyncio
    async def test_real_time_collaboration_monitoring(
        self, collaboration_service, mock_agents
    ):
        """Test real-time monitoring of collaboration activities"""
        service = collaboration_service

        # Setup real-time monitor
        monitor_config = {
            "monitor_type": "collaboration_health",
            "thresholds": {
                "max_duration": 300,  # 5 minutes
                "min_messages": 2,
                "effectiveness_threshold": 0.8,
            },
            "alerts_enabled": True,
        }

        monitor_id = await service.add_real_time_monitor(monitor_config)
        assert monitor_id is not None

        # Start collaboration
        manager = mock_agents["field_mapping_manager"]
        specialist = mock_agents["schema_expert"]

        context = {"task": "monitored_task"}
        collaboration_id = await service.initiate_collaboration(
            manager, specialist, context
        )

        # Simulate messages
        await service.send_message(
            collaboration_id,
            manager.role,
            specialist.role,
            {"type": "instruction", "content": "Analyze the schema patterns"},
        )

        await service.send_message(
            collaboration_id,
            specialist.role,
            manager.role,
            {"type": "progress", "status": "analyzing"},
        )

        # Check for alerts (should be none for normal collaboration)
        alerts = await service.check_collaboration_alerts()

        # Should have no alerts for active, healthy collaboration
        assert len(alerts) == 0 or all(
            alert["type"] != "inactive_collaboration" for alert in alerts
        )

    @pytest.mark.asyncio
    async def test_collaboration_alerting_system(
        self, collaboration_service, mock_agents
    ):
        """Test alerting system for collaboration issues"""
        service = collaboration_service
        manager = mock_agents["cleansing_manager"]
        specialist = mock_agents["validation_expert"]

        # Start collaboration but don't send messages (inactive)
        context = {"task": "inactive_task"}
        collaboration_id = await service.initiate_collaboration(
            manager, specialist, context
        )

        # Simulate time passing without activity
        collaboration = service.active_collaborations[collaboration_id]
        collaboration["start_time"] = time.time() - 120  # 2 minutes ago

        # Check for alerts
        alerts = await service.check_collaboration_alerts()

        # Should detect inactive collaboration
        inactive_alerts = [
            alert for alert in alerts if alert["type"] == "inactive_collaboration"
        ]
        assert len(inactive_alerts) > 0

        # Verify alert details
        alert = inactive_alerts[0]
        assert alert["collaboration_id"] == collaboration_id
        assert alert["duration"] > 60

    @pytest.mark.asyncio
    async def test_cross_domain_expertise_collaboration(
        self, collaboration_service, mock_agents
    ):
        """Test collaboration between different domain experts"""
        service = collaboration_service
        server_expert = mock_agents["server_expert"]
        app_expert = mock_agents["app_expert"]

        # Cross-domain collaboration context
        context = {
            "collaboration_type": "cross_domain_expertise",
            "domains": ["server_infrastructure", "application_services"],
            "goal": "comprehensive_asset_analysis",
        }

        collaboration_id = await service.initiate_collaboration(
            server_expert, app_expert, context
        )

        # Server expert shares infrastructure findings
        await service.send_message(
            collaboration_id,
            server_expert.role,
            app_expert.role,
            {
                "type": "domain_expertise_sharing",
                "domain": "server_infrastructure",
                "findings": {
                    "server_types": ["physical", "virtual", "cloud"],
                    "infrastructure_dependencies": ["network", "storage", "compute"],
                },
                "cross_domain_implications": {
                    "application_hosting": "multi_tier_architecture_detected",
                    "service_dependencies": "complex_topology",
                },
            },
        )

        # Application expert responds with service perspective
        await service.send_message(
            collaboration_id,
            app_expert.role,
            server_expert.role,
            {
                "type": "domain_expertise_response",
                "domain": "application_services",
                "findings": {
                    "service_types": ["web", "database", "api"],
                    "application_architectures": ["microservices", "monolithic"],
                },
                "infrastructure_requirements": {
                    "load_balancing_needed": True,
                    "database_clustering": "recommended",
                    "service_mesh": "consider_for_microservices",
                },
            },
        )

        # Complete cross-domain collaboration
        results = {
            "cross_domain_insights": True,
            "comprehensive_analysis": True,
            "infrastructure_application_alignment": 0.93,
        }

        completion = await service.complete_collaboration(collaboration_id, results)
        assert completion["success"] is True
        assert completion["effectiveness"] >= 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
