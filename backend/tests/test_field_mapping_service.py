"""
Unit Tests for FieldMappingService

Tests the FieldMappingService that provides field mapping capabilities
following the Service Registry pattern.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.field_mapping_service import (
    FieldMappingService,
    MappingAnalysis,
    MappingRule,
)
from app.models.data_import.mapping import ImportFieldMapping as FieldMapping


class TestFieldMappingServiceInitialization:
    """Test FieldMappingService initialization and basic setup"""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def mock_context(self):
        """Create mock request context"""
        return RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            flow_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
        )

    @pytest.fixture
    def service(self, mock_session, mock_context):
        """Create FieldMappingService instance"""
        return FieldMappingService(mock_session, mock_context)

    def test_initialization(self, service, mock_session, mock_context):
        """Test service initialization"""
        assert service._session == mock_session
        assert service._context == mock_context
        assert service._learned_mappings_cache is None
        assert len(service._negative_mappings_cache) == 0
        assert len(service.BASE_MAPPINGS) > 0
        assert len(service.REQUIRED_FIELDS) > 0

    def test_base_mappings_structure(self, service):
        """Test that base mappings are properly structured"""
        assert "hostname" in service.BASE_MAPPINGS
        assert isinstance(service.BASE_MAPPINGS["hostname"], list)
        assert "host_name" in service.BASE_MAPPINGS["hostname"]

        # Check all base mappings have list values
        for key, value in service.BASE_MAPPINGS.items():
            assert isinstance(value, list)
            assert len(value) > 0

    def test_required_fields_structure(self, service):
        """Test that required fields are properly defined"""
        assert "server" in service.REQUIRED_FIELDS
        assert isinstance(service.REQUIRED_FIELDS["server"], list)
        assert "hostname" in service.REQUIRED_FIELDS["server"]

        # Check all asset types have required fields
        for asset_type in ["server", "application", "database"]:
            assert asset_type in service.REQUIRED_FIELDS
            assert len(service.REQUIRED_FIELDS[asset_type]) > 0


class TestFieldMappingAnalysis:
    """Test field mapping analysis functionality"""

    @pytest.fixture
    def service(self):
        """Create service with mocked dependencies"""
        session = AsyncMock(spec=AsyncSession)
        context = RequestContext(
            client_account_id=str(uuid.uuid4()), engagement_id=str(uuid.uuid4())
        )
        return FieldMappingService(session, context)

    @pytest.mark.asyncio
    async def test_analyze_columns_with_base_mappings(self, service):
        """Test analyzing columns that match base mappings"""
        # Mock the learned mappings cache
        service._learned_mappings_cache = {}

        columns = ["host_name", "ip_addr", "env", "unknown_field"]
        data_import_id = uuid.uuid4()
        analysis = await service.analyze_columns(
            columns, data_import_id=data_import_id, asset_type="server"
        )

        assert isinstance(analysis, MappingAnalysis)
        assert "host_name" in analysis.mapped_fields
        assert analysis.mapped_fields["host_name"] == "hostname"
        assert "ip_addr" in analysis.mapped_fields
        assert analysis.mapped_fields["ip_addr"] == "ip_address"
        assert "env" in analysis.mapped_fields
        assert analysis.mapped_fields["env"] == "environment"
        assert "unknown_field" in analysis.unmapped_fields

        # Check confidence scores
        assert analysis.confidence_scores["host_name"] == 1.0
        assert analysis.confidence_scores["ip_addr"] == 1.0
        assert analysis.confidence_scores["unknown_field"] == 0.0

    @pytest.mark.asyncio
    async def test_analyze_columns_with_learned_mappings(self, service):
        """Test analyzing columns with learned mappings"""
        # Setup learned mappings cache
        service._learned_mappings_cache = {
            "custom_field": [
                MappingRule(
                    source_field="my_custom_column",
                    target_field="custom_field",
                    confidence=0.85,
                    source="learned",
                )
            ]
        }

        columns = ["my_custom_column", "hostname"]
        data_import_id = uuid.uuid4()
        analysis = await service.analyze_columns(columns, data_import_id=data_import_id)

        assert "my_custom_column" in analysis.mapped_fields
        assert analysis.mapped_fields["my_custom_column"] == "custom_field"
        assert analysis.confidence_scores["my_custom_column"] == 0.85

    @pytest.mark.asyncio
    async def test_missing_required_fields_detection(self, service):
        """Test detection of missing required fields"""
        service._learned_mappings_cache = {}

        # Analyze columns missing required server fields
        columns = ["some_field", "another_field"]
        data_import_id = uuid.uuid4()
        analysis = await service.analyze_columns(
            columns, data_import_id=data_import_id, asset_type="server"
        )

        # Should identify missing required fields
        assert "hostname" in analysis.missing_required_fields
        assert "asset_name" in analysis.missing_required_fields
        assert "environment" in analysis.missing_required_fields

    @pytest.mark.asyncio
    async def test_overall_confidence_calculation(self, service):
        """Test overall confidence score calculation"""
        service._learned_mappings_cache = {}

        columns = ["hostname", "ip_address", "unknown1", "unknown2"]
        data_import_id = uuid.uuid4()
        analysis = await service.analyze_columns(columns, data_import_id=data_import_id)

        # 2 out of 4 columns mapped perfectly
        expected_confidence = (1.0 + 1.0 + 0.0 + 0.0) / 4
        assert analysis.overall_confidence == expected_confidence


class TestFieldMappingLearning:
    """Test field mapping learning functionality"""

    @pytest.fixture
    def service(self):
        """Create service with mocked session"""
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()

        context = RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
        )
        return FieldMappingService(session, context)

    @pytest.mark.asyncio
    async def test_learn_new_field_mapping(self, service):
        """Test learning a new field mapping"""
        # Mock database query to return no existing mapping
        service._get_existing_mapping = AsyncMock(return_value=None)
        service._learned_mappings_cache = {}

        data_import_id = uuid.uuid4()
        result = await service.learn_field_mapping(
            source_field="Custom_Field",
            target_field="asset_name",
            data_import_id=data_import_id,
            confidence=0.9,
            source="user",
            context="manual_mapping",
        )

        assert result["success"] is True
        assert result["action"] == "created"
        assert "mapping_id" in result

        # Check that mapping was added to cache
        assert "asset_name" in service._learned_mappings_cache
        assert len(service._learned_mappings_cache["asset_name"]) == 1

        cached_rule = service._learned_mappings_cache["asset_name"][0]
        assert cached_rule.source_field == "custom_field"  # normalized
        assert cached_rule.confidence == 0.9

    @pytest.mark.asyncio
    async def test_update_existing_mapping_with_higher_confidence(self, service):
        """Test updating an existing mapping with higher confidence"""
        # Mock existing mapping with lower confidence
        existing_mapping = MagicMock()
        existing_mapping.confidence_score = 0.7
        existing_mapping.id = uuid.uuid4()
        existing_mapping.metadata = {}

        service._get_existing_mapping = AsyncMock(return_value=existing_mapping)
        service._learned_mappings_cache = {}

        data_import_id = uuid.uuid4()
        result = await service.learn_field_mapping(
            source_field="field1",
            target_field="target1",
            data_import_id=data_import_id,
            confidence=0.95,
            source="ai",
        )

        assert result["success"] is True
        assert result["action"] == "updated"
        assert existing_mapping.confidence_score == 0.95
        assert existing_mapping.source == "ai"

    @pytest.mark.asyncio
    async def test_reject_lower_confidence_update(self, service):
        """Test that lower confidence updates are rejected"""
        # Mock existing mapping with higher confidence
        existing_mapping = MagicMock()
        existing_mapping.confidence_score = 0.9

        service._get_existing_mapping = AsyncMock(return_value=existing_mapping)

        data_import_id = uuid.uuid4()
        result = await service.learn_field_mapping(
            source_field="field1",
            target_field="target1",
            data_import_id=data_import_id,
            confidence=0.7,
        )

        assert result["success"] is True
        assert result["action"] == "exists"
        assert result["existing_confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_learn_negative_mapping(self, service):
        """Test learning a negative mapping (what not to map)"""
        service._negative_mappings_cache = set()

        data_import_id = uuid.uuid4()
        result = await service.learn_negative_mapping(
            source_field="Field_A",
            target_field="wrong_target",
            data_import_id=data_import_id,
            reason="User indicated this is incorrect",
        )

        assert result["success"] is True
        assert ("field_a", "wrong_target") in service._negative_mappings_cache

        # Verify database entry was created
        service._session.add.assert_called_once()
        added_mapping = service._session.add.call_args[0][0]
        assert added_mapping.confidence_score == 0.0  # 0 for rejected
        assert added_mapping.status == "rejected"

    @pytest.mark.asyncio
    async def test_reject_negative_mapping_in_learning(self, service):
        """Test that negative mappings are rejected in normal learning"""
        service._negative_mappings_cache = {("field_a", "wrong_target")}

        data_import_id = uuid.uuid4()
        result = await service.learn_field_mapping(
            source_field="field_a",
            target_field="wrong_target",
            data_import_id=data_import_id,
            confidence=0.8,
        )

        assert result["success"] is False
        assert "previously rejected" in result["message"]


class TestFieldMappingValidation:
    """Test field mapping validation functionality"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        session = AsyncMock(spec=AsyncSession)
        context = RequestContext(client_account_id=str(uuid.uuid4()))
        return FieldMappingService(session, context)

    @pytest.mark.asyncio
    async def test_validate_base_mapping(self, service):
        """Test validation of base mappings"""
        result = await service.validate_mapping(
            source_field="host_name", target_field="hostname"
        )

        assert result["valid"] is True
        assert result["confidence"] == 1.0
        assert result["source"] == "base_mapping"
        assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_validate_negative_mapping(self, service):
        """Test that negative mappings are marked invalid"""
        service._negative_mappings_cache = {("field_a", "wrong_target")}

        result = await service.validate_mapping(
            source_field="field_a", target_field="wrong_target"
        )

        assert result["valid"] is False
        assert result["confidence"] == 0.0
        assert "previously rejected" in result["issues"][0]

    @pytest.mark.asyncio
    async def test_validate_with_content(self, service):
        """Test validation with sample content"""
        # Test IP address validation
        result = await service.validate_mapping(
            source_field="server_ip",
            target_field="ip_address",
            sample_values=["192.168.1.1", "10.0.0.1", "invalid_ip"],
        )

        assert result["valid"] is False
        assert len(result["issues"]) > 0
        assert "Invalid IP address" in result["issues"][0]

    @pytest.mark.asyncio
    async def test_validate_numeric_field(self, service):
        """Test validation of numeric fields"""
        result = await service.validate_mapping(
            source_field="cores",
            target_field="cpu_cores",
            sample_values=["4", "8", "not_a_number", "16"],
        )

        assert result["valid"] is False
        assert len(result["issues"]) > 0
        assert "Expected numeric value" in result["issues"][0]


class TestFieldMappingRetrieval:
    """Test field mapping retrieval functionality"""

    @pytest.fixture
    def service(self):
        """Create service with mock data"""
        session = AsyncMock(spec=AsyncSession)
        context = RequestContext(client_account_id=str(uuid.uuid4()))
        service = FieldMappingService(session, context)

        # Setup mock learned mappings
        service._learned_mappings_cache = {
            "custom_field": [
                MappingRule(
                    source_field="my_field",
                    target_field="custom_field",
                    confidence=0.9,
                    source="learned",
                )
            ]
        }

        return service

    @pytest.mark.asyncio
    async def test_get_all_field_mappings(self, service):
        """Test retrieving all field mappings"""
        mappings = await service.get_field_mappings()

        # Should include base mappings
        assert "hostname" in mappings
        assert "host_name" in mappings["hostname"]

        # Should include learned mappings
        assert "custom_field" in mappings
        assert "my_field" in mappings["custom_field"]

    @pytest.mark.asyncio
    async def test_get_field_mappings_by_asset_type(self, service):
        """Test filtering mappings by asset type"""
        mappings = await service.get_field_mappings(asset_type="server")

        # Should include required server fields
        assert "hostname" in mappings
        assert "operating_system" in mappings

        # May not include all base mappings
        assert len(mappings) <= len(service.BASE_MAPPINGS) + 1  # +1 for learned


class TestFieldMappingHealthCheck:
    """Test health check functionality"""

    @pytest.fixture
    def service(self):
        """Create service with mocked session"""
        session = AsyncMock(spec=AsyncSession)
        context = RequestContext(
            client_account_id=str(uuid.uuid4()), engagement_id=str(uuid.uuid4())
        )
        return FieldMappingService(session, context)

    @pytest.mark.asyncio
    async def test_health_check_success(self, service):
        """Test successful health check"""
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar.return_value = 42
        service._session.execute = AsyncMock(return_value=mock_result)
        service._learned_mappings_cache = {"field1": []}

        health = await service.health_check()

        assert health["status"] == "healthy"
        assert health["service"] == "FieldMappingService"
        assert health["mapping_count"] == 42
        assert health["base_mappings"] == len(service.BASE_MAPPINGS)
        assert health["cached_learned_mappings"] == 1

    @pytest.mark.asyncio
    async def test_health_check_failure(self, service):
        """Test health check with database error"""
        service._session.execute = AsyncMock(side_effect=Exception("DB Error"))

        health = await service.health_check()

        assert health["status"] == "unhealthy"
        assert "error" in health
        assert "DB Error" in health["error"]


class TestFieldMappingCacheManagement:
    """Test cache management functionality"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        session = AsyncMock(spec=AsyncSession)
        context = RequestContext(client_account_id=str(uuid.uuid4()))
        return FieldMappingService(session, context)

    @pytest.mark.asyncio
    async def test_load_learned_mappings(self, service):
        """Test loading learned mappings from database"""
        # Mock database mappings
        mapping1 = MagicMock(spec=FieldMapping)
        mapping1.source_field = "field1"
        mapping1.target_field = "target1"
        mapping1.confidence_score = 0.9
        mapping1.source = "user"
        mapping1.metadata = {"context": "test"}
        mapping1.created_at = datetime.now(timezone.utc)

        mapping2 = MagicMock(spec=FieldMapping)
        mapping2.source_field = "field2"
        mapping2.target_field = "target1"
        mapping2.confidence_score = 0.8
        mapping2.source = "ai"
        mapping2.metadata = None
        mapping2.created_at = datetime.now(timezone.utc)

        # Mock negative mapping (rejected status)
        negative_mapping = MagicMock(spec=FieldMapping)
        negative_mapping.source_field = "bad_field"
        negative_mapping.target_field = "wrong_target"
        negative_mapping.status = "rejected"
        negative_mapping.confidence_score = 0.0

        # Setup mock results
        mock_result1 = MagicMock()
        mock_result1.scalars.return_value.all.return_value = [mapping1, mapping2]

        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.all.return_value = [negative_mapping]

        service._session.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        await service._load_learned_mappings()

        # Check learned mappings cache
        assert service._learned_mappings_cache is not None
        assert "target1" in service._learned_mappings_cache
        assert len(service._learned_mappings_cache["target1"]) == 2

        # Check negative mappings cache
        assert ("bad_field", "wrong_target") in service._negative_mappings_cache

    def test_update_cache(self, service):
        """Test updating the learned mappings cache"""
        service._learned_mappings_cache = {}

        # Add new mapping to cache
        service._update_cache(
            source_field="new_field",
            target_field="target",
            confidence=0.85,
            source="user",
        )

        assert "target" in service._learned_mappings_cache
        assert len(service._learned_mappings_cache["target"]) == 1

        rule = service._learned_mappings_cache["target"][0]
        assert rule.source_field == "new_field"
        assert rule.confidence == 0.85

        # Update existing mapping
        service._update_cache(
            source_field="new_field",
            target_field="target",
            confidence=0.95,
            source="ai",
        )

        # Should still have one rule but updated
        assert len(service._learned_mappings_cache["target"]) == 1
        updated_rule = service._learned_mappings_cache["target"][0]
        assert updated_rule.confidence == 0.95
        assert updated_rule.source == "ai"


class TestFieldNormalization:
    """Test field name normalization"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        session = AsyncMock(spec=AsyncSession)
        context = RequestContext(client_account_id=str(uuid.uuid4()))
        return FieldMappingService(session, context)

    def test_normalize_field_name(self, service):
        """Test field name normalization"""
        assert service._normalize_field_name("Field Name") == "field_name"
        assert service._normalize_field_name("FIELD-NAME") == "field_name"
        assert service._normalize_field_name("  field  ") == "field"
        assert service._normalize_field_name("field_name") == "field_name"
        assert service._normalize_field_name("Field-Name-123") == "field_name_123"


class TestContentValidation:
    """Test content validation functionality"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        session = AsyncMock(spec=AsyncSession)
        context = RequestContext(client_account_id=str(uuid.uuid4()))
        return FieldMappingService(session, context)

    def test_validate_ip_address_content(self, service):
        """Test IP address validation"""
        issues = service._validate_content(
            "ip_address", ["192.168.1.1", "10.0.0.1", "not_an_ip", "256.256.256.256"]
        )

        assert len(issues) > 0
        assert any("Invalid IP" in issue for issue in issues)

    def test_validate_email_content(self, service):
        """Test email validation"""
        issues = service._validate_content(
            "email", ["user@example.com", "invalid_email", "another@test.com"]
        )

        assert len(issues) > 0
        assert any("Invalid email" in issue for issue in issues)

    def test_validate_numeric_content(self, service):
        """Test numeric field validation"""
        issues = service._validate_content(
            "cpu_cores", ["4", "8", "not_a_number", "16.5", "text"]
        )

        assert len(issues) > 0
        assert any("Expected numeric" in issue for issue in issues)

    def test_is_valid_ip(self, service):
        """Test IP address format validation"""
        assert service._is_valid_ip("192.168.1.1") is True
        assert service._is_valid_ip("0.0.0.0") is True
        assert service._is_valid_ip("255.255.255.255") is True
        assert service._is_valid_ip("256.1.1.1") is False
        assert service._is_valid_ip("192.168.1") is False
        assert service._is_valid_ip("not_an_ip") is False
        assert service._is_valid_ip("192.168.1.1.1") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
