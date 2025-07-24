"""
Test model consolidation changes
"""

from app.models import (
    Asset,
    AssetDependency,
    DataImport,
    DiscoveryFlow,
    ImportFieldMapping,
    RawImportRecord,
)


def test_data_import_model_fields():
    """Test DataImport model has correct consolidated fields"""
    # Check renamed fields exist
    assert hasattr(DataImport, "filename"), "DataImport should have 'filename' field"
    assert hasattr(DataImport, "file_size"), "DataImport should have 'file_size' field"
    assert hasattr(DataImport, "mime_type"), "DataImport should have 'mime_type' field"
    assert hasattr(
        DataImport, "source_system"
    ), "DataImport should have 'source_system' field"
    assert hasattr(
        DataImport, "error_message"
    ), "DataImport should have 'error_message' field"
    assert hasattr(
        DataImport, "error_details"
    ), "DataImport should have 'error_details' field"

    # Check removed fields don't exist
    assert not hasattr(
        DataImport, "source_filename"
    ), "DataImport should not have 'source_filename'"
    assert not hasattr(
        DataImport, "file_size_bytes"
    ), "DataImport should not have 'file_size_bytes'"
    assert not hasattr(
        DataImport, "file_type"
    ), "DataImport should not have 'file_type'"
    assert not hasattr(DataImport, "is_mock"), "DataImport should not have 'is_mock'"
    assert not hasattr(
        DataImport, "file_hash"
    ), "DataImport should not have 'file_hash'"
    assert not hasattr(
        DataImport, "import_config"
    ), "DataImport should not have 'import_config'"


def test_discovery_flow_hybrid_fields():
    """Test DiscoveryFlow has both boolean flags and JSON fields"""
    # Check boolean flags exist (backward compatibility)
    assert hasattr(DiscoveryFlow, "data_validation_completed")
    assert hasattr(DiscoveryFlow, "field_mapping_completed")
    assert hasattr(DiscoveryFlow, "data_cleansing_completed")
    assert hasattr(DiscoveryFlow, "asset_inventory_completed")
    assert hasattr(DiscoveryFlow, "dependency_analysis_completed")
    assert hasattr(DiscoveryFlow, "tech_debt_assessment_completed")

    # Check JSON fields exist (V3 features)
    assert hasattr(DiscoveryFlow, "flow_type")
    assert hasattr(DiscoveryFlow, "current_phase")
    assert hasattr(DiscoveryFlow, "phases_completed")
    assert hasattr(DiscoveryFlow, "flow_state")
    assert hasattr(DiscoveryFlow, "crew_outputs")
    assert hasattr(DiscoveryFlow, "field_mappings")
    assert hasattr(DiscoveryFlow, "discovered_assets")
    assert hasattr(DiscoveryFlow, "dependencies")
    assert hasattr(DiscoveryFlow, "tech_debt_analysis")

    # Check error fields
    assert hasattr(DiscoveryFlow, "error_message")
    assert hasattr(DiscoveryFlow, "error_phase")
    assert hasattr(DiscoveryFlow, "error_details")

    # Check removed fields
    assert not hasattr(DiscoveryFlow, "is_mock")
    assert not hasattr(DiscoveryFlow, "learning_scope")
    assert not hasattr(DiscoveryFlow, "memory_isolation_level")
    assert not hasattr(DiscoveryFlow, "assessment_package")


def test_import_field_mapping_fields():
    """Test ImportFieldMapping has correct fields"""
    assert hasattr(ImportFieldMapping, "match_type"), "Should have 'match_type' field"
    assert hasattr(
        ImportFieldMapping, "transformation_rules"
    ), "Should have 'transformation_rules' field"
    assert hasattr(ImportFieldMapping, "approved_by"), "Should have 'approved_by' field"
    assert hasattr(ImportFieldMapping, "approved_at"), "Should have 'approved_at' field"

    # Check removed fields
    assert not hasattr(
        ImportFieldMapping, "mapping_type"
    ), "Should not have old 'mapping_type'"
    assert not hasattr(
        ImportFieldMapping, "validation_rules"
    ), "Should not have 'validation_rules'"
    assert not hasattr(
        ImportFieldMapping, "user_feedback"
    ), "Should not have 'user_feedback'"
    assert not hasattr(
        ImportFieldMapping, "is_user_defined"
    ), "Should not have 'is_user_defined'"


def test_raw_import_record_fields():
    """Test RawImportRecord has correct fields"""
    assert hasattr(RawImportRecord, "record_index"), "Should have 'record_index' field"
    assert hasattr(
        RawImportRecord, "cleansed_data"
    ), "Should have 'cleansed_data' field"

    # Check removed fields
    assert not hasattr(
        RawImportRecord, "row_number"
    ), "Should not have old 'row_number'"
    assert not hasattr(
        RawImportRecord, "processed_data"
    ), "Should not have old 'processed_data'"
    assert not hasattr(RawImportRecord, "record_id"), "Should not have 'record_id'"


def test_asset_no_mock_fields():
    """Test Asset model has no is_mock fields"""
    # Verify is_mock is removed
    assert not hasattr(Asset, "is_mock"), "Asset should not have 'is_mock' field"

    # Verify key fields still exist
    assert hasattr(Asset, "master_flow_id")
    assert hasattr(Asset, "discovery_flow_id")
    assert hasattr(Asset, "hostname")
    assert hasattr(Asset, "ip_address")
    assert hasattr(Asset, "operating_system")
    assert hasattr(Asset, "cpu_cores")
    assert hasattr(Asset, "memory_gb")
    assert hasattr(Asset, "storage_gb")


def test_asset_dependency_no_mock():
    """Test AssetDependency has no is_mock field"""
    assert not hasattr(
        AssetDependency, "is_mock"
    ), "AssetDependency should not have 'is_mock'"


def test_model_relationships():
    """Test model relationships are properly defined"""
    # DataImport relationships
    assert hasattr(DataImport, "raw_records")
    assert hasattr(DataImport, "field_mappings")
    assert hasattr(DataImport, "discovery_flows")

    # ImportFieldMapping relationships
    assert hasattr(ImportFieldMapping, "data_import")


def test_no_v3_models_imported():
    """Ensure V3 models are not imported"""
    import app.models

    models_list = app.models.__all__

    # Check that V3 models are not in the exports
    v3_models = [
        "V3DataImport",
        "V3DiscoveryFlow",
        "V3FieldMapping",
        "V3RawImportRecord",
    ]
    for v3_model in v3_models:
        assert v3_model not in models_list, f"{v3_model} should not be exported"


def test_removed_models_not_imported():
    """Ensure deprecated models are not imported"""
    import app.models

    models_list = app.models.__all__

    # Check that deprecated models are not in the exports
    deprecated = [
        "DiscoveryAsset",
        "MappingLearningPattern",
        "DataQualityIssue",
        "WorkflowState",
        "WorkflowProgress",
        "ImportProcessingStep",
    ]
    for model in deprecated:
        assert model not in models_list, f"{model} should not be exported"


if __name__ == "__main__":
    # Run basic import test
    print("Testing model imports...")
    test_data_import_model_fields()
    test_discovery_flow_hybrid_fields()
    test_import_field_mapping_fields()
    test_raw_import_record_fields()
    test_asset_no_mock_fields()
    test_asset_dependency_no_mock()
    test_model_relationships()
    test_no_v3_models_imported()
    test_removed_models_not_imported()
    print("✅ All model tests passed!")
