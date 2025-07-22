"""
Unit tests for Collection Flow Services
Tests core collection services including initialization, finalization, error handling,
and phase-specific operations in the ADCS system.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.flow_configs.collection_handlers import (
    _get_question_template,
    _normalize_platform_data,
    adapter_preparation,
    collection_checkpoint_handler,
    collection_data_normalization,
    collection_error_handler,
    collection_finalization,
    collection_initialization,
    collection_rollback_handler,
    gap_analysis_preparation,
    gap_prioritization,
    platform_inventory_creation,
    questionnaire_generation,
    response_processing,
    synthesis_preparation,
)


# Fixtures
@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.scalar_one_or_none = MagicMock()
    return session


@pytest.fixture
def mock_master_flow():
    """Create mock master flow object"""
    flow = MagicMock()
    flow.flow_id = str(uuid.uuid4())
    flow.collection_flow_id = None
    flow.automation_tier = None
    flow.data_collection_metadata = {}
    return flow


@pytest.fixture
def sample_context():
    """Create sample context for handlers"""
    return {
        "client_account_id": str(uuid.uuid4()),
        "engagement_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4())
    }


@pytest.fixture
def sample_initial_state():
    """Create sample initial state for collection flow"""
    return {
        "discovery_flow_id": str(uuid.uuid4()),
        "flow_name": "Test Collection Flow",
        "automation_tier": "tier_2",
        "environment": "production",
        "collection_scope": "full",
        "collection_config": {
            "timeout": 300,
            "retry_count": 3
        }
    }


@pytest.fixture
def sample_collection_flow():
    """Create sample collection flow data"""
    return {
        "id": uuid.uuid4(),
        "flow_id": uuid.uuid4(),
        "status": "initialized",
        "current_phase": "platform_detection",
        "automation_tier": "tier_2"
    }


class TestCollectionFlowLifecycleHandlers:
    """Test collection flow lifecycle handlers"""

    @pytest.mark.asyncio
    async def test_collection_initialization_success(self, mock_db_session, mock_master_flow, 
                                                   sample_context, sample_initial_state):
        """Test successful collection flow initialization"""
        # Arrange
        flow_id = str(uuid.uuid4())
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_master_flow
        mock_db_session.execute.return_value.fetchall.return_value = []

        # Act
        result = await collection_initialization(
            mock_db_session,
            flow_id,
            "collection",
            sample_initial_state,
            sample_context
        )

        # Assert
        assert result["success"] is True
        assert "collection_flow_id" in result
        assert result["automation_tier"] == "tier_2"
        assert mock_db_session.commit.called
        assert mock_db_session.execute.called

    @pytest.mark.asyncio
    async def test_collection_initialization_master_flow_not_found(self, mock_db_session, 
                                                                 sample_context, sample_initial_state):
        """Test initialization when master flow is not found"""
        # Arrange
        flow_id = str(uuid.uuid4())
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

        # Act
        result = await collection_initialization(
            mock_db_session,
            flow_id,
            "collection",
            sample_initial_state,
            sample_context
        )

        # Assert
        assert result["success"] is False
        assert "Master flow" in result["error"]
        assert mock_db_session.rollback.called

    @pytest.mark.asyncio
    async def test_collection_finalization_success(self, mock_db_session, mock_master_flow,
                                                  sample_context, sample_collection_flow):
        """Test successful collection flow finalization"""
        # Arrange
        flow_id = str(uuid.uuid4())
        final_state = {
            "crew_results": {
                "quality_report": {
                    "overall_quality": 0.85,
                    "total_resources": 150
                },
                "sixr_readiness_score": 0.90,
                "final_data": {"platform1": {}, "platform2": {}},
                "summary": {"total_platforms": 2}
            }
        }
        
        # Mock collection flow lookup
        mock_db_session.execute.return_value.fetchone.return_value = MagicMock(
            id=sample_collection_flow["id"],
            flow_id=sample_collection_flow["flow_id"],
            status=sample_collection_flow["status"],
            current_phase=sample_collection_flow["current_phase"],
            automation_tier=sample_collection_flow["automation_tier"]
        )
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_master_flow

        # Act
        result = await collection_finalization(
            mock_db_session,
            flow_id,
            final_state,
            sample_context
        )

        # Assert
        assert result["success"] is True
        assert result["final_metrics"]["quality_score"] == 0.85
        assert result["final_metrics"]["sixr_readiness"] == 0.90
        assert result["final_metrics"]["total_resources"] == 150
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_collection_error_handler_recoverable(self, mock_db_session, sample_context):
        """Test error handler with recoverable error"""
        # Arrange
        flow_id = str(uuid.uuid4())
        error = ConnectionError("Connection failed")
        error_context = {
            "phase": "automated_collection",
            "operation": "fetch_data"
        }
        
        # Mock collection flow lookup
        mock_db_session.execute.return_value.fetchone.return_value = MagicMock(
            id=uuid.uuid4(),
            flow_id=uuid.uuid4(),
            status="in_progress",
            current_phase="automated_collection",
            automation_tier="tier_3"
        )

        # Act
        result = await collection_error_handler(
            mock_db_session,
            flow_id,
            error,
            error_context,
            sample_context
        )

        # Assert
        assert result["success"] is True
        assert result["error_handled"] is True
        assert result["is_recoverable"] is True
        assert result["recovery_strategy"] == "retry"
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_collection_error_handler_non_recoverable(self, mock_db_session, sample_context):
        """Test error handler with non-recoverable error"""
        # Arrange
        flow_id = str(uuid.uuid4())
        error = ValueError("Invalid configuration")
        error_context = {
            "phase": "gap_analysis",
            "operation": "analyze_gaps"
        }
        
        # Mock collection flow lookup
        mock_db_session.execute.return_value.fetchone.return_value = MagicMock(
            id=uuid.uuid4(),
            flow_id=uuid.uuid4(),
            status="in_progress",
            current_phase="gap_analysis",
            automation_tier="tier_2"
        )

        # Act
        result = await collection_error_handler(
            mock_db_session,
            flow_id,
            error,
            error_context,
            sample_context
        )

        # Assert
        assert result["success"] is True
        assert result["error_handled"] is True
        assert result["is_recoverable"] is False
        assert result["recovery_strategy"] == "manual_intervention"

    @pytest.mark.asyncio
    async def test_collection_rollback_handler(self, mock_db_session, sample_context,
                                             sample_collection_flow):
        """Test rollback handler"""
        # Arrange
        flow_id = str(uuid.uuid4())
        rollback_to_phase = "automated_collection"
        
        # Mock collection flow lookup
        mock_db_session.execute.return_value.fetchone.return_value = MagicMock(
            id=sample_collection_flow["id"],
            flow_id=sample_collection_flow["flow_id"],
            status="failed",
            current_phase="gap_analysis",
            automation_tier="tier_2"
        )

        # Act
        result = await collection_rollback_handler(
            mock_db_session,
            flow_id,
            rollback_to_phase,
            sample_context
        )

        # Assert
        assert result["success"] is True
        assert result["rolled_back_to"] == rollback_to_phase
        assert "actions_taken" in result
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_collection_checkpoint_handler(self, mock_db_session, sample_context,
                                               sample_collection_flow):
        """Test checkpoint creation"""
        # Arrange
        flow_id = str(uuid.uuid4())
        checkpoint_data = {
            "phase": "automated_collection",
            "progress": 75,
            "platforms_collected": 3,
            "resources_count": 250
        }
        
        # Mock collection flow lookup
        mock_db_session.execute.return_value.fetchone.return_value = MagicMock(
            id=sample_collection_flow["id"],
            flow_id=sample_collection_flow["flow_id"],
            status="in_progress",
            current_phase="automated_collection",
            automation_tier="tier_3"
        )

        # Act
        result = await collection_checkpoint_handler(
            mock_db_session,
            flow_id,
            checkpoint_data,
            sample_context
        )

        # Assert
        assert result["success"] is True
        assert result["checkpoint_created"] is True
        assert result["phase"] == "automated_collection"
        assert mock_db_session.commit.called


class TestPhaseSpecificHandlers:
    """Test phase-specific handlers"""

    @pytest.mark.asyncio
    async def test_platform_inventory_creation(self, mock_db_session, sample_context):
        """Test platform inventory creation after detection"""
        # Arrange
        flow_id = str(uuid.uuid4())
        phase_results = {
            "crew_results": {
                "platforms": [
                    {"id": "aws", "name": "Amazon Web Services"},
                    {"id": "azure", "name": "Microsoft Azure"}
                ],
                "recommended_adapters": {
                    "aws": "aws_adapter_v2",
                    "azure": "azure_adapter_v1"
                },
                "platform_metadata": {
                    "aws": {"region": "us-east-1"},
                    "azure": {"subscription": "prod"}
                }
            }
        }
        
        # Mock collection flow lookup
        mock_db_session.execute.return_value.fetchone.return_value = MagicMock(
            id=uuid.uuid4(),
            flow_id=uuid.uuid4(),
            status="in_progress",
            current_phase="platform_detection",
            automation_tier="tier_2"
        )

        # Act
        result = await platform_inventory_creation(
            mock_db_session,
            flow_id,
            phase_results,
            sample_context
        )

        # Assert
        assert result["success"] is True
        assert result["platforms_detected"] == 2
        assert result["adapters_recommended"] == 2
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_adapter_preparation(self, mock_db_session, sample_context):
        """Test adapter preparation for automated collection"""
        # Arrange
        flow_id = str(uuid.uuid4())
        phase_input = {
            "adapter_configs": {
                "aws": {
                    "adapter_name": "aws_adapter_v2",
                    "config": {"region": "us-east-1"}
                },
                "azure": {
                    "adapter_name": "azure_adapter_v1",
                    "config": {"subscription": "prod"}
                }
            }
        }
        
        # Mock adapter lookups
        mock_db_session.execute.return_value.fetchone.side_effect = [
            MagicMock(id=uuid.uuid4(), adapter_name="aws_adapter_v2", status="active", capabilities={}),
            MagicMock(id=uuid.uuid4(), adapter_name="azure_adapter_v1", status="active", capabilities={})
        ]

        # Act
        result = await adapter_preparation(
            mock_db_session,
            flow_id,
            phase_input,
            sample_context
        )

        # Assert
        assert result["success"] is True
        assert result["adapter_count"] == 2
        assert "aws" in result["prepared_adapters"]
        assert "azure" in result["prepared_adapters"]

    @pytest.mark.asyncio
    async def test_collection_data_normalization(self, mock_db_session, sample_context):
        """Test data normalization after automated collection"""
        # Arrange
        flow_id = str(uuid.uuid4())
        phase_results = {
            "crew_results": {
                "collected_data": {
                    "aws": {
                        "resources": [{"type": "ec2", "id": "i-123"}],
                        "data_type": "infrastructure",
                        "adapter_name": "aws_adapter_v2"
                    },
                    "azure": {
                        "assets": [{"type": "vm", "id": "vm-456"}],
                        "data_type": "infrastructure",
                        "adapter_name": "azure_adapter_v1"
                    }
                },
                "quality_scores": {
                    "aws": 0.85,
                    "azure": 0.90
                }
            }
        }
        
        # Mock collection flow lookup
        collection_flow_id = uuid.uuid4()
        mock_db_session.execute.return_value.fetchone.return_value = MagicMock(
            id=collection_flow_id,
            flow_id=uuid.uuid4(),
            status="in_progress",
            current_phase="automated_collection",
            automation_tier="tier_3"
        )

        # Act
        result = await collection_data_normalization(
            mock_db_session,
            flow_id,
            phase_results,
            sample_context
        )

        # Assert
        assert result["success"] is True
        assert result["platforms_normalized"] == 2
        assert result["total_resources"] == 2
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_gap_analysis_preparation(self, mock_db_session, sample_context):
        """Test preparation for gap analysis"""
        # Arrange
        flow_id = str(uuid.uuid4())
        phase_input = {}
        
        collection_flow_id = uuid.uuid4()
        
        # Mock collection flow lookup
        mock_db_session.execute.return_value.fetchone.return_value = MagicMock(
            id=collection_flow_id,
            flow_id=uuid.uuid4(),
            status="in_progress",
            current_phase="gap_analysis",
            automation_tier="tier_2"
        )
        
        # Mock collected data query
        mock_db_session.execute.return_value.fetchall.return_value = [
            MagicMock(
                platform="aws",
                normalized_data={"resources": [{"type": "ec2"}]},
                quality_score=0.85,
                resource_count=10
            ),
            MagicMock(
                platform="azure",
                normalized_data={"resources": [{"type": "vm"}]},
                quality_score=0.90,
                resource_count=15
            )
        ]

        # Act
        result = await gap_analysis_preparation(
            mock_db_session,
            flow_id,
            phase_input,
            sample_context
        )

        # Assert
        assert result["success"] is True
        assert result["platform_count"] == 2
        assert result["analysis_data"]["total_resources"] == 25
        assert result["analysis_data"]["average_quality"] == 0.875

    @pytest.mark.asyncio
    async def test_gap_prioritization(self, mock_db_session, sample_context):
        """Test gap prioritization after analysis"""
        # Arrange
        flow_id = str(uuid.uuid4())
        phase_results = {
            "crew_results": {
                "data_gaps": [
                    {
                        "type": "missing_data",
                        "category": "infrastructure",
                        "field_name": "security_groups",
                        "description": "Missing security group configuration",
                        "sixr_impact": "high",
                        "priority": 9,
                        "resolution": "Manual collection required",
                        "platform": "aws",
                        "resource_type": "ec2"
                    },
                    {
                        "type": "incomplete_data",
                        "category": "network",
                        "field_name": "subnet_config",
                        "description": "Incomplete subnet configuration",
                        "sixr_impact": "medium",
                        "priority": 6,
                        "resolution": "Query network API",
                        "platform": "azure",
                        "resource_type": "vnet"
                    }
                ]
            }
        }
        
        # Mock collection flow lookup
        collection_flow_id = uuid.uuid4()
        mock_db_session.execute.return_value.fetchone.return_value = MagicMock(
            id=collection_flow_id,
            flow_id=uuid.uuid4(),
            status="in_progress",
            current_phase="gap_analysis",
            automation_tier="tier_2"
        )

        # Act
        result = await gap_prioritization(
            mock_db_session,
            flow_id,
            phase_results,
            sample_context
        )

        # Assert
        assert result["success"] is True
        assert result["total_gaps"] == 2
        assert result["high_priority_gaps"] == 1
        assert result["critical_sixr_gaps"] == 1
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_questionnaire_generation(self, mock_db_session, sample_context):
        """Test questionnaire generation for manual collection"""
        # Arrange
        flow_id = str(uuid.uuid4())
        phase_input = {}
        
        collection_flow_id = uuid.uuid4()
        
        # Mock collection flow lookup
        mock_db_session.execute.return_value.fetchone.return_value = MagicMock(
            id=collection_flow_id,
            flow_id=uuid.uuid4(),
            status="in_progress",
            current_phase="manual_collection",
            automation_tier="tier_2"
        )
        
        # Mock gaps query
        gap_id = uuid.uuid4()
        mock_db_session.execute.return_value.fetchall.return_value = [
            MagicMock(
                id=gap_id,
                gap_type="missing_data",
                field_name="security_groups",
                description="Missing security group configuration",
                priority=9,
                suggested_resolution="Provide security group details"
            )
        ]

        # Act
        result = await questionnaire_generation(
            mock_db_session,
            flow_id,
            phase_input,
            sample_context
        )

        # Assert
        assert result["success"] is True
        assert result["questions_generated"] == 1
        assert result["gaps_addressed"] == 1
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_response_processing(self, mock_db_session, sample_context):
        """Test processing of questionnaire responses"""
        # Arrange
        flow_id = str(uuid.uuid4())
        gap_id_1 = str(uuid.uuid4())
        gap_id_2 = str(uuid.uuid4())
        
        phase_results = {
            "crew_results": {
                "responses": {
                    gap_id_1: {
                        "value": {"security_groups": ["sg-123", "sg-456"]},
                        "confidence": 0.95,
                        "is_valid": True
                    },
                    gap_id_2: {
                        "value": {"subnet_config": {"cidr": "10.0.0.0/24"}},
                        "confidence": 0.80,
                        "is_valid": False
                    }
                }
            }
        }
        
        # Mock collection flow lookup
        collection_flow_id = uuid.uuid4()
        mock_db_session.execute.return_value.fetchone.return_value = MagicMock(
            id=collection_flow_id,
            flow_id=uuid.uuid4(),
            status="in_progress",
            current_phase="manual_collection",
            automation_tier="tier_2"
        )

        # Act
        result = await response_processing(
            mock_db_session,
            flow_id,
            phase_results,
            sample_context
        )

        # Assert
        assert result["success"] is True
        assert result["responses_processed"] == 2
        assert result["gaps_resolved"] == 1
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_synthesis_preparation(self, mock_db_session, sample_context):
        """Test preparation for data synthesis"""
        # Arrange
        flow_id = str(uuid.uuid4())
        phase_input = {}
        
        collection_flow_id = uuid.uuid4()
        
        # Mock collection flow lookup
        mock_db_session.execute.return_value.fetchone.return_value = MagicMock(
            id=collection_flow_id,
            flow_id=uuid.uuid4(),
            status="in_progress",
            current_phase="synthesis",
            automation_tier="tier_2"
        )
        
        # Mock collected data query
        mock_collected_result = MagicMock()
        mock_collected_result.fetchall.return_value = [
            MagicMock(
                platform="aws",
                collection_method="automated",
                normalized_data={"resources": [{"type": "ec2"}]},
                quality_score=0.85
            ),
            MagicMock(
                platform="azure",
                collection_method="automated",
                normalized_data={"resources": [{"type": "vm"}]},
                quality_score=0.90
            )
        ]
        
        # Mock resolved gaps query
        mock_gaps_result = MagicMock()
        mock_gaps_result.fetchall.return_value = [
            MagicMock(
                field_name="security_groups",
                platform="aws",
                response_value={"sg": ["sg-123"]},
                confidence_score=0.95
            )
        ]
        
        mock_db_session.execute.side_effect = [
            mock_collected_result,  # First call for collection flow lookup
            mock_collected_result,  # Second call for collected data
            mock_gaps_result        # Third call for resolved gaps
        ]

        # Act
        result = await synthesis_preparation(
            mock_db_session,
            flow_id,
            phase_input,
            sample_context
        )

        # Assert
        assert result["success"] is True
        assert result["automated_platforms"] == 2
        assert result["manual_fields"] == 1
        assert "aws" in result["synthesis_data"]["automated_data"]
        assert "azure" in result["synthesis_data"]["automated_data"]


class TestHelperFunctions:
    """Test helper functions"""

    def test_normalize_platform_data_with_resources(self):
        """Test platform data normalization with resources key"""
        # Arrange
        raw_data = {
            "resources": [{"type": "ec2", "id": "i-123"}],
            "platform": "aws",
            "region": "us-east-1",
            "custom_field": "value"
        }

        # Act
        normalized = _normalize_platform_data(raw_data)

        # Assert
        assert len(normalized["resources"]) == 1
        assert normalized["metadata"]["platform"] == "aws"
        assert normalized["metadata"]["region"] == "us-east-1"
        assert normalized["platform_specific"]["custom_field"] == "value"

    def test_normalize_platform_data_with_assets(self):
        """Test platform data normalization with assets key"""
        # Arrange
        raw_data = {
            "assets": [{"type": "vm", "id": "vm-456"}],
            "account": "prod-account",
            "environment": "production"
        }

        # Act
        normalized = _normalize_platform_data(raw_data)

        # Assert
        assert len(normalized["resources"]) == 1
        assert normalized["metadata"]["account"] == "prod-account"
        assert normalized["metadata"]["environment"] == "production"

    def test_normalize_platform_data_with_items(self):
        """Test platform data normalization with items key"""
        # Arrange
        raw_data = {
            "items": [{"name": "db-1", "type": "database"}],
            "region": "eu-west-1"
        }

        # Act
        normalized = _normalize_platform_data(raw_data)

        # Assert
        assert len(normalized["resources"]) == 1
        assert normalized["metadata"]["region"] == "eu-west-1"

    def test_get_question_template_missing_data(self):
        """Test question template for missing data"""
        # Act
        template = _get_question_template("missing_data")

        # Assert
        assert "missing" in template
        assert "{field_name}" in template
        assert "{description}" in template

    def test_get_question_template_incomplete_data(self):
        """Test question template for incomplete data"""
        # Act
        template = _get_question_template("incomplete_data")

        # Assert
        assert "incomplete" in template
        assert "{field_name}" in template

    def test_get_question_template_quality_issues(self):
        """Test question template for quality issues"""
        # Act
        template = _get_question_template("quality_issues")

        # Assert
        assert "quality issues" in template
        assert "{field_name}" in template

    def test_get_question_template_validation_errors(self):
        """Test question template for validation errors"""
        # Act
        template = _get_question_template("validation_errors")

        # Assert
        assert "validation" in template
        assert "{field_name}" in template

    def test_get_question_template_default(self):
        """Test default question template"""
        # Act
        template = _get_question_template("unknown_type")

        # Assert
        assert "provide information" in template
        assert "{field_name}" in template


class TestErrorScenarios:
    """Test error scenarios and edge cases"""

    @pytest.mark.asyncio
    async def test_initialization_database_error(self, mock_db_session, sample_context, 
                                               sample_initial_state):
        """Test initialization with database error"""
        # Arrange
        flow_id = str(uuid.uuid4())
        mock_db_session.execute.side_effect = Exception("Database connection failed")

        # Act
        result = await collection_initialization(
            mock_db_session,
            flow_id,
            "collection",
            sample_initial_state,
            sample_context
        )

        # Assert
        assert result["success"] is False
        assert "Database connection failed" in result["error"]
        assert mock_db_session.rollback.called

    @pytest.mark.asyncio
    async def test_finalization_missing_collection_flow(self, mock_db_session, sample_context):
        """Test finalization when collection flow is missing"""
        # Arrange
        flow_id = str(uuid.uuid4())
        final_state = {"crew_results": {}}
        
        # Mock collection flow not found
        mock_db_session.execute.return_value.fetchone.return_value = None

        # Act
        result = await collection_finalization(
            mock_db_session,
            flow_id,
            final_state,
            sample_context
        )

        # Assert
        assert result["success"] is False
        assert "not found" in result["error"]
        assert mock_db_session.rollback.called

    @pytest.mark.asyncio
    async def test_gap_prioritization_empty_gaps(self, mock_db_session, sample_context):
        """Test gap prioritization with no gaps identified"""
        # Arrange
        flow_id = str(uuid.uuid4())
        phase_results = {
            "crew_results": {
                "data_gaps": []
            }
        }
        
        # Mock collection flow lookup
        mock_db_session.execute.return_value.fetchone.return_value = MagicMock(
            id=uuid.uuid4(),
            flow_id=uuid.uuid4(),
            status="in_progress",
            current_phase="gap_analysis",
            automation_tier="tier_2"
        )

        # Act
        result = await gap_prioritization(
            mock_db_session,
            flow_id,
            phase_results,
            sample_context
        )

        # Assert
        assert result["success"] is True
        assert result["total_gaps"] == 0
        assert result["high_priority_gaps"] == 0
        assert result["critical_sixr_gaps"] == 0

    @pytest.mark.asyncio
    async def test_adapter_preparation_no_adapters_found(self, mock_db_session, sample_context):
        """Test adapter preparation when no adapters are found"""
        # Arrange
        flow_id = str(uuid.uuid4())
        phase_input = {
            "adapter_configs": {
                "unknown_platform": {
                    "adapter_name": "non_existent_adapter",
                    "config": {}
                }
            }
        }
        
        # Mock adapter not found
        mock_db_session.execute.return_value.fetchone.return_value = None

        # Act
        result = await adapter_preparation(
            mock_db_session,
            flow_id,
            phase_input,
            sample_context
        )

        # Assert
        assert result["success"] is True
        assert result["adapter_count"] == 0
        assert len(result["prepared_adapters"]) == 0