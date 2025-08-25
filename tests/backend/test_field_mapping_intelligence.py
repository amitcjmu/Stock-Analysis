#!/usr/bin/env python3
"""
Comprehensive Field Mapping Intelligence Test Suite

This test validates:
1. Intelligent mapping of unknown/random fields
2. Memory-based learning from user feedback
3. Negative learning (rejection tracking)
4. Multi-tenant isolation
5. Confidence score improvement

Run with: docker exec migration_backend pytest /app/tests/backend/test_field_mapping_intelligence.py -v
"""

import pytest
import asyncio
import uuid
import random
import string
from typing import List, Dict, Tuple
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Test will run in Docker where these imports are available
import sys
import os

# Support both local and Docker execution
if os.path.exists('/app'):
    sys.path.insert(0, '/app')
else:
    # Local execution
    backend_path = os.path.join(os.path.dirname(__file__), '../../backend')
    sys.path.insert(0, os.path.abspath(backend_path))

try:
    from app.services.field_mapping_service import FieldMappingService
    from app.models.data_import.mapping import ImportFieldMapping
    from app.core.database import AsyncSessionLocal
except ImportError:
    # Mock for demonstration if imports fail
    class FieldMappingService:
        def __init__(self):
            self._learned_mappings_cache = {}
            self._negative_mappings_cache = {}

    ImportFieldMapping = None
    AsyncSessionLocal = None


# ============================================================================
# HELPER FUNCTIONS FOR FIELD GENERATION
# ============================================================================

def generate_random_field_names(count: int = 10) -> List[str]:
    """Generate random field names that are NOT in base mappings"""
    prefixes = ['srv', 'computer', 'machine', 'workstation', 'device', 'asset', 'node', 'system']
    suffixes = ['hostname', 'name', 'id', 'label', 'identifier', 'tag', 'code', 'ref']
    separators = ['_', '-', '.', '']

    fields = []
    for _ in range(count):
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        separator = random.choice(separators)
        fields.append(f"{prefix}{separator}{suffix}")

    # Add some truly random fields
    for _ in range(count // 2):
        random_field = ''.join(random.choices(string.ascii_lowercase, k=8))
        fields.append(f"custom_{random_field}")

    return fields


def generate_compound_field_names(count: int = 5) -> List[str]:
    """Generate compound field names that require intelligent parsing"""
    compounds = [
        "primary_owner_email",
        "secondary_owner_name",
        "cpu_core_count",
        "total_ram_gb",
        "disk_storage_tb",
        "network_bandwidth_mbps",
        "last_update_timestamp",
        "creation_date_utc",
        "department_cost_center",
        "project_billing_code"
    ]
    return random.sample(compounds, min(count, len(compounds)))


def generate_ambiguous_field_names() -> List[str]:
    """Generate ambiguous field names that require context"""
    return ["type", "name", "id", "status", "category", "class", "group", "value", "data", "info"]


# ============================================================================
# HELPER FUNCTIONS FOR SIMULATION
# ============================================================================

async def simulate_user_approval(
    service: FieldMappingService,
    source_field: str,
    target_field: str,
    data_import_id: uuid.UUID,
    confidence: float = 0.95
) -> Dict:
    """Simulate user approving a field mapping"""
    return await service.learn_field_mapping(
        source_field=source_field,
        target_field=target_field,
        data_import_id=data_import_id,
        confidence=confidence,
        source="user",
        metadata={"approved_at": datetime.utcnow().isoformat()}
    )


async def simulate_user_rejection(
    service: FieldMappingService,
    source_field: str,
    target_field: str,
    data_import_id: uuid.UUID,
    reason: str = "Incorrect mapping"
) -> Dict:
    """Simulate user rejecting a field mapping"""
    return await service.learn_negative_mapping(
        source_field=source_field,
        target_field=target_field,
        data_import_id=data_import_id,
        rejection_reason=reason
    )


async def clear_test_data(service: FieldMappingService, test_ids: List[uuid.UUID]):
    """Clear test data from database after tests"""
    async with AsyncSessionLocal() as db:
        # Delete test mappings
        for test_id in test_ids:
            await db.execute(
                "DELETE FROM import_field_mappings WHERE data_import_id = :id",
                {"id": test_id}
            )
        await db.commit()


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
async def field_mapping_service():
    """Create a field mapping service instance for testing"""
    service = FieldMappingService()
    yield service
    # Cleanup after tests
    service._learned_mappings_cache.clear()
    service._negative_mappings_cache.clear()


@pytest.fixture
def test_client_id():
    """Generate a unique client ID for test isolation"""
    return uuid.uuid4()


@pytest.fixture
def test_import_id():
    """Generate a unique import ID for tests"""
    return uuid.uuid4()


# ============================================================================
# TEST 1: INTELLIGENT MAPPING OF UNKNOWN FIELDS
# ============================================================================

@pytest.mark.asyncio
async def test_intelligent_mapping_unknown_fields(field_mapping_service, test_import_id):
    """Test that service can intelligently map unknown field names"""

    # Generate random fields
    random_fields = generate_random_field_names(5)

    # Analyze columns with random fields
    analysis = await field_mapping_service.analyze_columns(
        columns=random_fields,
        data_import_id=test_import_id
    )

    # Validate analysis structure
    assert analysis is not None
    assert hasattr(analysis, 'mapped_fields')
    assert hasattr(analysis, 'unmapped_fields')
    assert hasattr(analysis, 'suggested_mappings')
    assert hasattr(analysis, 'confidence_scores')

    # Check that service attempts to map fields intelligently
    for field in random_fields:
        # Fields with hostname/name patterns should get suggestions
        if any(pattern in field.lower() for pattern in ['hostname', 'name', 'id']):
            assert field in analysis.suggested_mappings or field in analysis.mapped_fields

        # All fields should have confidence scores (even if 0)
        assert field in analysis.confidence_scores


@pytest.mark.asyncio
async def test_compound_field_mapping(field_mapping_service, test_import_id):
    """Test mapping of compound field names"""

    compound_fields = generate_compound_field_names(5)

    # First, teach the service about some compound mappings
    await simulate_user_approval(
        field_mapping_service,
        "primary_owner_email",
        "owner_email",
        test_import_id,
        confidence=0.9
    )

    # Now analyze with compound fields
    analysis = await field_mapping_service.analyze_columns(
        columns=compound_fields,
        data_import_id=test_import_id
    )

    # Validate compound field handling
    if "primary_owner_email" in compound_fields:
        # Should be mapped based on learning
        assert analysis.confidence_scores.get("primary_owner_email", 0) > 0.8

    # CPU/RAM fields should get suggestions
    for field in compound_fields:
        if "cpu" in field.lower():
            assert field in analysis.suggested_mappings or field in analysis.mapped_fields
        elif "ram" in field.lower() or "memory" in field.lower():
            assert field in analysis.suggested_mappings or field in analysis.mapped_fields


@pytest.mark.asyncio
async def test_ambiguous_field_mapping_with_context(field_mapping_service, test_import_id):
    """Test that ambiguous fields are mapped based on context"""

    ambiguous_fields = generate_ambiguous_field_names()

    # Provide context through other fields
    context_fields = ["hostname", "ip_address", "operating_system"]
    all_fields = context_fields + ambiguous_fields

    analysis = await field_mapping_service.analyze_columns(
        columns=all_fields,
        data_import_id=test_import_id,
        asset_type="server"  # Provide asset type context
    )

    # With server context, "type" should map to asset_type or server_type
    if "type" in ambiguous_fields:
        suggestions = analysis.suggested_mappings.get("type", [])
        # Should suggest asset_type or similar
        assert len(suggestions) > 0 or "type" in analysis.mapped_fields


# ============================================================================
# TEST 2: MEMORY-BASED LEARNING
# ============================================================================

@pytest.mark.asyncio
async def test_memory_based_learning_persistence(field_mapping_service, test_import_id, test_client_id):
    """Test that learned mappings are persisted to database"""

    # Learn a new mapping
    source_field = "srv_hostname_primary"
    target_field = "hostname"

    result = await simulate_user_approval(
        field_mapping_service,
        source_field,
        target_field,
        test_import_id,
        confidence=0.95
    )

    assert result["success"] is True
    assert result["action"] in ["created", "updated"]

    # Verify it's in the database
    async with AsyncSessionLocal() as db:
        mapping = await db.execute(
            """
            SELECT * FROM import_field_mappings
            WHERE source_field = :source AND data_import_id = :import_id
            """,
            {"source": source_field, "import_id": test_import_id}
        )
        row = mapping.fetchone()

        assert row is not None
        assert row.target_field == target_field
        assert row.confidence_score >= 0.95
        assert row.status == "approved"


@pytest.mark.asyncio
async def test_learned_mapping_auto_application(field_mapping_service, test_import_id):
    """Test that learned mappings are automatically applied in future analyses"""

    # Step 1: Teach the service a mapping
    custom_field = "workstation_identifier"
    await simulate_user_approval(
        field_mapping_service,
        custom_field,
        "hostname",
        test_import_id,
        confidence=0.9
    )

    # Step 2: Load learned mappings into cache
    await field_mapping_service.load_learned_mappings(test_import_id)

    # Step 3: Analyze columns including the learned field
    test_columns = [custom_field, "ip_address", "status"]
    analysis = await field_mapping_service.analyze_columns(
        columns=test_columns,
        data_import_id=test_import_id
    )

    # Step 4: Verify the learned mapping is automatically applied
    assert custom_field in analysis.mapped_fields or \
           (custom_field in analysis.suggested_mappings and
            "hostname" in analysis.suggested_mappings[custom_field])

    # Confidence should be high due to learning
    assert analysis.confidence_scores.get(custom_field, 0) >= 0.8


@pytest.mark.asyncio
async def test_similar_field_learning(field_mapping_service, test_import_id):
    """Test that learning affects similar field name suggestions"""

    # Learn that "srv_" prefix maps to standard fields
    await simulate_user_approval(
        field_mapping_service,
        "srv_hostname",
        "hostname",
        test_import_id,
        confidence=0.95
    )

    await simulate_user_approval(
        field_mapping_service,
        "srv_ip",
        "ip_address",
        test_import_id,
        confidence=0.95
    )

    # Load learned mappings
    await field_mapping_service.load_learned_mappings(test_import_id)

    # Test with similar field
    similar_field = "srv_status"
    analysis = await field_mapping_service.analyze_columns(
        columns=[similar_field],
        data_import_id=test_import_id
    )

    # Should suggest "status" based on pattern learning
    suggestions = analysis.suggested_mappings.get(similar_field, [])
    # The service should recognize the srv_ pattern
    assert len(suggestions) > 0 or similar_field in analysis.mapped_fields


# ============================================================================
# TEST 3: NEGATIVE LEARNING
# ============================================================================

@pytest.mark.asyncio
async def test_negative_learning_persistence(field_mapping_service, test_import_id):
    """Test that rejected mappings are stored in database"""

    source_field = "custom_field_xyz"
    wrong_target = "hostname"

    result = await simulate_user_rejection(
        field_mapping_service,
        source_field,
        wrong_target,
        test_import_id,
        reason="This is not a hostname field"
    )

    assert result["success"] is True

    # Verify it's in the database with rejected status
    async with AsyncSessionLocal() as db:
        mapping = await db.execute(
            """
            SELECT * FROM import_field_mappings
            WHERE source_field = :source AND data_import_id = :import_id
            """,
            {"source": source_field, "import_id": test_import_id}
        )
        row = mapping.fetchone()

        assert row is not None
        assert row.status == "rejected"
        assert row.target_field == wrong_target


@pytest.mark.asyncio
async def test_rejected_mappings_prevent_learning(field_mapping_service, test_import_id):
    """Test that rejected mappings prevent re-learning the same incorrect mapping"""

    source_field = "user_type"
    wrong_target = "hostname"

    # Reject the mapping
    await simulate_user_rejection(
        field_mapping_service,
        source_field,
        wrong_target,
        test_import_id
    )

    # Load negative mappings
    await field_mapping_service.load_learned_mappings(test_import_id)

    # Try to learn the same mapping again
    result = await field_mapping_service.learn_field_mapping(
        source_field=source_field,
        target_field=wrong_target,
        data_import_id=test_import_id,
        confidence=0.8,
        source="ai"
    )

    # Should be rejected due to negative learning
    assert result["success"] is False
    assert "rejected" in result.get("message", "").lower()


# ============================================================================
# TEST 4: MULTI-TENANT ISOLATION
# ============================================================================

@pytest.mark.asyncio
async def test_multi_tenant_isolation(field_mapping_service):
    """Test that learned mappings are isolated by client account"""

    client1_id = uuid.uuid4()
    client2_id = uuid.uuid4()
    import1_id = uuid.uuid4()
    import2_id = uuid.uuid4()

    # Client 1 learns a mapping
    with patch.object(field_mapping_service, '_get_client_account_id', return_value=client1_id):
        await simulate_user_approval(
            field_mapping_service,
            "client1_field",
            "hostname",
            import1_id
        )

        # Load client 1's mappings
        await field_mapping_service.load_learned_mappings(import1_id)

        # Verify client 1 has the mapping
        analysis1 = await field_mapping_service.analyze_columns(
            columns=["client1_field"],
            data_import_id=import1_id
        )

    # Client 2 should not see client 1's mappings
    with patch.object(field_mapping_service, '_get_client_account_id', return_value=client2_id):
        await field_mapping_service.load_learned_mappings(import2_id)

        analysis2 = await field_mapping_service.analyze_columns(
            columns=["client1_field"],
            data_import_id=import2_id
        )

        # Client 2 should not have high confidence for client1's field
        assert analysis2.confidence_scores.get("client1_field", 0) < 0.8


# ============================================================================
# TEST 5: CONFIDENCE SCORE IMPROVEMENT
# ============================================================================

@pytest.mark.asyncio
async def test_confidence_score_improvement_through_learning(field_mapping_service, test_import_id):
    """Test that confidence scores improve with learning iterations"""

    source_field = "server_name_primary"
    target_field = "hostname"

    # Initial mapping with AI (lower confidence)
    await field_mapping_service.learn_field_mapping(
        source_field=source_field,
        target_field=target_field,
        data_import_id=test_import_id,
        confidence=0.7,
        source="ai"
    )

    # User confirms (higher confidence)
    await simulate_user_approval(
        field_mapping_service,
        source_field,
        target_field,
        test_import_id,
        confidence=0.95
    )

    # Load and analyze
    await field_mapping_service.load_learned_mappings(test_import_id)
    analysis = await field_mapping_service.analyze_columns(
        columns=[source_field],
        data_import_id=test_import_id
    )

    # Confidence should be high after user confirmation
    assert analysis.confidence_scores.get(source_field, 0) >= 0.9


# ============================================================================
# TEST 6: COMPREHENSIVE WORKFLOW
# ============================================================================

@pytest.mark.asyncio
async def test_comprehensive_intelligence_workflow(field_mapping_service):
    """Test complete workflow from unknown fields to learned intelligent mapping"""

    import_id = uuid.uuid4()

    # Phase 1: Initial analysis with unknown fields
    unknown_fields = [
        "srv_hostname_001",
        "owner_email_primary",
        "cpu_core_total",
        "memory_gb_installed",
        "custom_dept_code"
    ]

    initial_analysis = await field_mapping_service.analyze_columns(
        columns=unknown_fields,
        data_import_id=import_id
    )

    # Should have low confidence initially
    for field in unknown_fields:
        assert initial_analysis.confidence_scores.get(field, 0) < 0.8

    # Phase 2: User provides feedback
    await simulate_user_approval(field_mapping_service, "srv_hostname_001", "hostname", import_id)
    await simulate_user_approval(field_mapping_service, "owner_email_primary", "owner_email", import_id)
    await simulate_user_approval(field_mapping_service, "cpu_core_total", "cpu_cores", import_id)
    await simulate_user_rejection(field_mapping_service, "custom_dept_code", "department", import_id,
                                  "This is a billing code, not department")

    # Phase 3: Test learning on similar fields
    await field_mapping_service.load_learned_mappings(import_id)

    similar_fields = [
        "srv_hostname_002",  # Should map to hostname
        "owner_email_secondary",  # Should map to owner-related field
        "custom_dept_code",  # Should not suggest department (rejected)
        "cpu_core_available"  # Should map to cpu-related field
    ]

    learned_analysis = await field_mapping_service.analyze_columns(
        columns=similar_fields,
        data_import_id=import_id
    )

    # Validate intelligent learning
    assert learned_analysis.confidence_scores.get("srv_hostname_002", 0) > 0.7  # Learned pattern
    assert "owner" in str(learned_analysis.suggested_mappings.get("owner_email_secondary", [])).lower()

    # Rejected mapping should not be suggested
    dept_suggestions = learned_analysis.suggested_mappings.get("custom_dept_code", [])
    assert "department" not in dept_suggestions

    print("✅ Comprehensive workflow test passed!")
    print(f"  - Learned from {len(unknown_fields)} unknown fields")
    print(f"  - Applied learning to {len(similar_fields)} similar fields")
    print(f"  - Respected negative learning for rejected mappings")


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("FIELD MAPPING INTELLIGENCE TEST SUITE")
    print("=" * 60)

    # Run the comprehensive workflow test as a demo
    asyncio.run(test_comprehensive_intelligence_workflow(FieldMappingService()))

    print("\n" + "=" * 60)
    print("To run all tests with pytest:")
    print("docker exec migration_backend pytest /app/tests/backend/test_field_mapping_intelligence.py -v")
    print("=" * 60)
