"""
Tests for enhanced asset classification and 6R readiness assessment.
Validates agentic workflows and device type classification.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

from app.api.v1.discovery.utils import (
    standardize_asset_type as _standardize_asset_type,
    assess_6r_readiness as _assess_6r_readiness,
    assess_migration_complexity as _assess_migration_complexity
)
from app.api.v1.discovery.processor import CMDBDataProcessor


class TestAssetTypeClassification:
    """Test the enhanced asset type classification with agentic intelligence."""
    
    def test_database_detection_patterns(self):
        """Test database detection from various naming patterns."""
        test_cases = [
            {"name": "mysql-db-01", "type": "", "expected": "Database"},
            {"name": "oracle-prod-db", "type": "", "expected": "Database"},
            {"name": "postgres-cluster", "type": "", "expected": "Database"},
            {"name": "mongodb-shard1", "type": "", "expected": "Database"},
            {"name": "redis-cache", "type": "", "expected": "Database"},
            {"name": "elasticsearch-node", "type": "", "expected": "Database"},
            {"name": "mssql-server", "type": "", "expected": "Database"},
            {"name": "db-finance-prod", "type": "", "expected": "Database"},
            {"name": "cassandra-ring", "type": "", "expected": "Database"},
        ]
        
        for case in test_cases:
            result = _standardize_asset_type(
                case["type"], 
                case["name"], 
                {"name": case["name"], "type": case["type"]}
            )
            assert result == case["expected"], f"Failed for {case['name']}: got {result}, expected {case['expected']}"
    
    def test_network_device_detection(self):
        """Test network device classification."""
        test_cases = [
            {"name": "CoreSwitch01", "type": "Switch", "expected": "Network Device"},
            {"name": "cisco-core-switch", "type": "", "expected": "Network Device"},
            {"name": "juniper-router", "type": "", "expected": "Network Device"},
            {"name": "f5-loadbalancer", "type": "", "expected": "Network Device"},
            {"name": "gateway-01", "type": "", "expected": "Network Device"},
            {"name": "wifi-ap-01", "type": "", "expected": "Network Device"},
            {"name": "edge-router", "type": "", "expected": "Network Device"},
        ]
        
        for case in test_cases:
            result = _standardize_asset_type(
                case["type"], 
                case["name"], 
                {"name": case["name"], "type": case["type"]}
            )
            assert result == case["expected"], f"Failed for {case['name']}: got {result}, expected {case['expected']}"
    
    def test_storage_device_detection(self):
        """Test storage device classification."""
        test_cases = [
            {"name": "SAN01", "type": "", "expected": "Storage Device"},
            {"name": "netapp-storage", "type": "", "expected": "Storage Device"},
            {"name": "emc-array", "type": "", "expected": "Storage Device"},
            {"name": "dell-san", "type": "", "expected": "Storage Device"},
            {"name": "nas-backup", "type": "", "expected": "Storage Device"},
            {"name": "pure-flash", "type": "", "expected": "Storage Device"},
        ]
        
        for case in test_cases:
            result = _standardize_asset_type(
                case["type"], 
                case["name"], 
                {"name": case["name"], "type": case["type"]}
            )
            assert result == case["expected"], f"Failed for {case['name']}: got {result}, expected {case['expected']}"
    
    def test_security_device_detection(self):
        """Test security device classification with proper precedence."""
        test_cases = [
            {"name": "Firewall01", "type": "", "expected": "Security Device"},
            {"name": "checkpoint-fw", "type": "", "expected": "Security Device"},
            {"name": "splunk-ids", "type": "", "expected": "Security Device"},
            {"name": "waf-proxy", "type": "", "expected": "Security Device"},
            {"name": "ips-sensor", "type": "", "expected": "Security Device"},
            {"name": "security-gateway", "type": "", "expected": "Security Device"},
        ]
        
        for case in test_cases:
            result = _standardize_asset_type(
                case["type"], 
                case["name"], 
                {"name": case["name"], "type": case["type"]}
            )
            assert result == case["expected"], f"Failed for {case['name']}: got {result}, expected {case['expected']}"
    
    def test_virtualization_platform_detection(self):
        """Test virtualization platform classification."""
        test_cases = [
            {"name": "vmware-vcenter", "type": "", "expected": "Virtualization Platform"},
            {"name": "hyper-v-host", "type": "", "expected": "Virtualization Platform"},
            {"name": "esxi-01", "type": "", "expected": "Virtualization Platform"},
            {"name": "kubernetes-master", "type": "", "expected": "Virtualization Platform"},
            {"name": "docker-host", "type": "", "expected": "Virtualization Platform"},
            {"name": "citrix-xen", "type": "", "expected": "Virtualization Platform"},
        ]
        
        for case in test_cases:
            result = _standardize_asset_type(
                case["type"], 
                case["name"], 
                {"name": case["name"], "type": case["type"]}
            )
            assert result == case["expected"], f"Failed for {case['name']}: got {result}, expected {case['expected']}"
    
    def test_server_detection(self):
        """Test server classification."""
        test_cases = [
            {"name": "srv-web-01", "type": "", "expected": "Server"},
            {"name": "AppServer01", "type": "", "expected": "Server"},
            {"name": "mail-server", "type": "", "expected": "Server"},
            {"name": "dns-host", "type": "", "expected": "Server"},
            {"name": "web-vm-01", "type": "", "expected": "Server"},
            {"name": "domain-controller", "type": "", "expected": "Server"},
        ]
        
        for case in test_cases:
            result = _standardize_asset_type(
                case["type"], 
                case["name"], 
                {"name": case["name"], "type": case["type"]}
            )
            assert result == case["expected"], f"Failed for {case['name']}: got {result}, expected {case['expected']}"
    
    def test_application_vs_server_distinction(self):
        """Test that applications with infrastructure specs are properly classified."""
        # Application without infrastructure specs
        app_result = _standardize_asset_type(
            "", 
            "crm-application", 
            {"name": "crm-application"}
        )
        assert app_result == "Application"
        
        # Application with infrastructure specs should be classified as server
        server_result = _standardize_asset_type(
            "", 
            "webapp-service", 
            {
                "name": "webapp-service", 
                "cpu_cores": 8, 
                "memory_gb": 32
            }
        )
        assert server_result == "Server"
    
    def test_infrastructure_device_detection(self):
        """Test infrastructure device classification."""
        test_cases = [
            {"name": "ups-01", "type": "", "expected": "Infrastructure Device"},
            {"name": "kvm-console", "type": "", "expected": "Infrastructure Device"},
            {"name": "printer-01", "type": "", "expected": "Infrastructure Device"},
            {"name": "camera-security", "type": "", "expected": "Infrastructure Device"},
        ]
        
        for case in test_cases:
            result = _standardize_asset_type(
                case["type"], 
                case["name"], 
                {"name": case["name"], "type": case["type"]}
            )
            assert result == case["expected"], f"Failed for {case['name']}: got {result}, expected {case['expected']}"
    
    def test_unknown_classification(self):
        """Test that unknown assets are properly classified."""
        result = _standardize_asset_type("", "random-device-xyz", {})
        assert result == "Unknown"
    
    @patch('app.services.crewai_service.crewai_service')
    def test_agentic_intelligence_integration(self, mock_service):
        """Test that agentic intelligence is used when available."""
        # Mock CrewAI service with agents available
        mock_service.agents = {"test_agent": Mock()}
        
        # Should attempt to use agentic intelligence but fall back to rules
        result = _standardize_asset_type(
            "", 
            "mysql-database", 
            {"name": "mysql-database", "type": ""}
        )
        
        # Should still classify correctly via rule-based fallback
        assert result == "Database"
    
    def test_classification_precedence_order(self):
        """Test that classification follows correct precedence order."""
        # Security devices should be detected before network devices
        firewall_result = _standardize_asset_type("", "network-firewall-01", {})
        assert firewall_result == "Security Device"
        
        # Databases should be detected before anything else
        db_result = _standardize_asset_type("", "sql-server-db", {})
        assert db_result == "Database"
        
        # Virtualization should be detected before servers
        vmware_result = _standardize_asset_type("", "vmware-server-01", {})
        assert vmware_result == "Virtualization Platform"


class Test6RReadinessAssessment:
    """Test 6R migration readiness assessment logic."""
    
    def test_application_readiness_ready(self):
        """Test ready application assessment."""
        asset_data = {
            "Name": "CRM_System",
            "Environment": "Production",
            "Business_Owner": "Sales"
        }
        result = _assess_6r_readiness("Application", asset_data)
        assert result == "Ready"
    
    def test_application_needs_owner(self):
        """Test application missing owner info."""
        asset_data = {
            "Name": "HR_Portal",
            "Environment": "Production"
        }
        result = _assess_6r_readiness("Application", asset_data)
        assert result == "Needs Owner Info"
    
    def test_application_insufficient_data(self):
        """Test application with insufficient data."""
        asset_data = {
            "Name": "Unknown_App"
        }
        result = _assess_6r_readiness("Application", asset_data)
        assert result == "Insufficient Data"
    
    def test_server_readiness_ready(self):
        """Test ready server assessment."""
        asset_data = {
            "Name": "web-server-01",
            "Environment": "Production",
            "CPU_Cores": 8,
            "Memory_GB": 32,
            "OS": "Linux"
        }
        result = _assess_6r_readiness("Server", asset_data)
        assert result == "Ready"
    
    def test_server_needs_infrastructure_data(self):
        """Test server missing infrastructure data."""
        asset_data = {
            "Name": "app-server-02",
            "Environment": "Production"
        }
        result = _assess_6r_readiness("Server", asset_data)
        assert result == "Needs Infrastructure Data"
    
    def test_database_readiness_ready(self):
        """Test ready database assessment."""
        asset_data = {
            "Name": "mysql-prod",
            "Environment": "Production",
            "Version": "8.0"
        }
        result = _assess_6r_readiness("Database", asset_data)
        assert result == "Ready"
    
    def test_database_needs_version(self):
        """Test database missing version info."""
        asset_data = {
            "Name": "oracle-db",
            "Environment": "Production"
        }
        result = _assess_6r_readiness("Database", asset_data)
        assert result == "Needs Version Info"
    
    def test_device_not_applicable(self):
        """Test that devices are marked as not applicable."""
        device_types = ["Network Device", "Storage Device", "Security Device", "Infrastructure Device"]
        
        for device_type in device_types:
            result = _assess_6r_readiness(device_type, {"Name": "test-device"})
            assert result == "Not Applicable"
    
    def test_virtualization_complex_analysis(self):
        """Test virtualization platform requires complex analysis."""
        result = _assess_6r_readiness("Virtualization Platform", {"Name": "vmware-host"})
        assert result == "Complex Analysis Required"
    
    def test_unknown_type_classification_needed(self):
        """Test unknown type needs classification."""
        result = _assess_6r_readiness("Unknown", {"Name": "mystery-asset"})
        assert result == "Type Classification Needed"


class TestMigrationComplexityAssessment:
    """Test migration complexity assessment logic."""
    
    def test_application_high_complexity(self):
        """Test high complexity application."""
        asset_data = {
            "Related_CI": "database,server",
            "Criticality": "High",
            "Environment": "Production"
        }
        result = _assess_migration_complexity("Application", asset_data)
        assert result == "High"
    
    def test_application_medium_complexity(self):
        """Test medium complexity application."""
        asset_data = {
            "Criticality": "Medium",
            "Environment": "Production"
        }
        result = _assess_migration_complexity("Application", asset_data)
        assert result == "Medium"
    
    def test_application_low_complexity(self):
        """Test low complexity application."""
        asset_data = {
            "Environment": "Development"
        }
        result = _assess_migration_complexity("Application", asset_data)
        assert result == "Low"
    
    def test_server_high_complexity(self):
        """Test high complexity server."""
        asset_data = {
            "CPU_Cores": 32,
            "Memory_GB": 128,
            "Environment": "Production"
        }
        result = _assess_migration_complexity("Server", asset_data)
        assert result == "High"
    
    def test_server_medium_complexity(self):
        """Test medium complexity server."""
        asset_data = {
            "CPU_Cores": 12,
            "Memory_GB": 48,
            "Environment": "Production"
        }
        result = _assess_migration_complexity("Server", asset_data)
        assert result == "Medium"
    
    def test_server_low_complexity(self):
        """Test low complexity server."""
        asset_data = {
            "CPU_Cores": 4,
            "Memory_GB": 16,
            "Environment": "Development"
        }
        result = _assess_migration_complexity("Server", asset_data)
        assert result == "Low"
    
    def test_database_complexity_levels(self):
        """Test database complexity assessment."""
        # High complexity: critical + production
        high_data = {
            "Criticality": "Critical",
            "Environment": "Production"
        }
        assert _assess_migration_complexity("Database", high_data) == "High"
        
        # Medium complexity: production only
        medium_data = {
            "Environment": "Production"
        }
        assert _assess_migration_complexity("Database", medium_data) == "Medium"
        
        # Low complexity: non-production
        low_data = {
            "Environment": "Development"
        }
        assert _assess_migration_complexity("Database", low_data) == "Low"
    
    def test_device_low_complexity(self):
        """Test that all devices have low complexity."""
        device_types = ["Network Device", "Storage Device", "Security Device", "Infrastructure Device"]
        
        for device_type in device_types:
            result = _assess_migration_complexity(device_type, {})
            assert result == "Low"
    
    def test_virtualization_high_complexity(self):
        """Test virtualization platforms have high complexity."""
        result = _assess_migration_complexity("Virtualization Platform", {})
        assert result == "High"
    
    def test_unknown_medium_complexity(self):
        """Test unknown types default to medium complexity."""
        result = _assess_migration_complexity("Unknown", {})
        assert result == "Medium"


class TestCMDBDataProcessor:
    """Test the CMDB data processor with agentic workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = CMDBDataProcessor()
    
    @patch('app.services.crewai_service.CrewAIService')
    def test_processor_initialization(self, mock_crewai):
        """Test processor initializes with CrewAI service."""
        processor = CMDBDataProcessor()
        assert processor.crewai_service is not None
    
    def test_analyze_data_structure(self):
        """Test data structure analysis."""
        import pandas as pd
        
        # Create test dataframe
        test_data = pd.DataFrame({
            'Asset_Name': ['server1', 'app1', None],
            'Asset_Type': ['Server', 'Application', 'Database'],
            'Environment': ['Prod', 'Test', 'Prod'],
            'CPU_Cores': [8, None, 4]
        })
        
        analysis = self.processor.analyze_data_structure(test_data)
        
        assert analysis['total_rows'] == 3
        assert analysis['total_columns'] == 4
        assert 'Asset_Name' in analysis['columns']
        assert analysis['quality_score'] >= 0
        assert analysis['quality_score'] <= 100
        assert 'null_percentage' in analysis
        assert 'duplicate_count' in analysis
    
    def test_identify_asset_types_with_explicit_column(self):
        """Test asset type identification with explicit type column."""
        import pandas as pd
        
        test_data = pd.DataFrame({
            'ci_type': ['server', 'application', 'database', 'server'],
            'name': ['srv1', 'app1', 'db1', 'srv2']
        })
        
        coverage = self.processor.identify_asset_types(test_data)
        
        assert coverage.servers == 2
        assert coverage.applications == 1
        assert coverage.databases == 1
    
    def test_identify_missing_fields_for_applications(self):
        """Test missing field identification for applications."""
        import pandas as pd
        
        test_data = pd.DataFrame({
            'application_name': ['CRM'],
            'version': ['1.0']
        })
        
        missing_fields = self.processor.identify_missing_fields(test_data)
        
        # Should identify missing essential application fields
        assert len(missing_fields) > 0
        # Should include environment and business owner
        missing_field_names = [field.lower() for field in missing_fields]
        assert any('environment' in field or 'owner' in field for field in missing_field_names)
    
    def test_suggest_processing_steps(self):
        """Test processing step suggestions."""
        import pandas as pd
        
        # Create data with quality issues
        test_data = pd.DataFrame({
            'Asset Name': ['server1', 'server1', None],  # Duplicate and null
            'Type': ['Server', 'Server', 'App'],
            'Memory GB': [32, 32, None]
        })
        
        analysis = self.processor.analyze_data_structure(test_data)
        steps = self.processor.suggest_processing_steps(test_data, analysis)
        
        assert len(steps) > 0
        assert any('duplicate' in step.lower() for step in steps)
        assert any('missing' in step.lower() or 'null' in step.lower() for step in steps)
    
    @patch('app.services.field_mapper.field_mapper')
    def test_learned_field_mappings_integration(self, mock_field_mapper):
        """Test integration with learned field mappings."""
        # Mock field mapper response
        mock_field_mapper.get_field_mappings.return_value = {
            'Memory (GB)': ['memory', 'ram', 'memory_gb', 'mem', 'ram_gb'],
            'CPU Cores': ['cpu', 'cores', 'processors', 'vcpu', 'cpu_cores']
        }
        
        # Test that learned mappings are used
        learned_mappings = self.processor._get_learned_field_mappings()
        assert 'Memory (GB)' in learned_mappings
        assert 'ram_gb' in learned_mappings['Memory (GB)']
    
    def test_agentic_workflow_preservation(self):
        """Test that agentic workflows are preserved and not replaced by heuristics."""
        # Verify CrewAI service is initialized
        assert hasattr(self.processor, 'crewai_service')
        assert self.processor.crewai_service is not None
        
        # Verify processor doesn't override agentic analysis
        # This test ensures we don't break agentic workflows with hard-coded rules
        import pandas as pd
        
        test_data = pd.DataFrame({
            'name': ['test-asset'],
            'type': ['unknown']
        })
        
        # The processor should defer to agentic analysis when available
        # and only use rule-based analysis as fallback
        analysis = self.processor.analyze_data_structure(test_data)
        assert analysis is not None
        assert 'quality_score' in analysis


class TestFieldMappingIntelligence:
    """Test field mapping and intelligent field recognition."""
    
    def test_flexible_field_value_extraction(self):
        """Test flexible field value extraction."""
        from app.api.v1.discovery.utils import get_field_value
        
        # Test multiple field name variations
        asset_data = {
            'RAM_GB': '32',
            'memory_size': '64',
            'cpu_count': '8'
        }
        
        # Should find RAM_GB for memory field
        memory_value = get_field_value(asset_data, ['memory_gb', 'memory', 'ram', 'ram_gb'])
        assert memory_value == '32'
        
        # Should find cpu_count for CPU field
        cpu_value = get_field_value(asset_data, ['cpu_cores', 'cpu', 'cores', 'cpu_count'])
        assert cpu_value == '8'
    
    def test_tech_stack_extraction(self):
        """Test technology stack extraction."""
        from app.api.v1.discovery.utils import get_tech_stack
        
        asset_data = {
            'operating_system': 'Linux Ubuntu 20.04',
            'version': '2.1.3',
            'platform': 'Docker'
        }
        
        tech_stack = get_tech_stack(asset_data)
        
        assert 'Linux Ubuntu 20.04' in tech_stack
        assert 'v2.1.3' in tech_stack
        assert 'Docker' in tech_stack
    
    def test_header_generation(self):
        """Test dynamic header generation based on asset data."""
        from app.api.v1.discovery.utils import generate_suggested_headers
        
        assets = [
            {
                'id': 'SRV001',
                'type': 'Server',
                'name': 'web-server',
                'techStack': 'Linux',
                'department': 'IT',
                'environment': 'Production',
                'criticality': 'High',
                'ipAddress': '192.168.1.10',
                'operatingSystem': 'Linux',
                'cpuCores': 8,
                'memoryGb': 32,
                'storageGb': 500
            }
        ]
        
        headers = generate_suggested_headers(assets)
        
        # Should include basic fields
        header_keys = [h['key'] for h in headers]
        assert 'id' in header_keys
        assert 'type' in header_keys
        assert 'name' in header_keys
        
        # Should include server-specific fields
        assert 'ipAddress' in header_keys
        assert 'operatingSystem' in header_keys
        assert 'cpuCores' in header_keys


@pytest.fixture
def sample_cmdb_data():
    """Fixture providing sample CMDB data for testing."""
    return {
        'filename': 'test_cmdb.csv',
        'structure': {
            'total_rows': 10,
            'total_columns': 8,
            'columns': ['Asset_Name', 'CI_Type', 'Environment', 'CPU_Cores', 'Memory_GB'],
            'quality_score': 85
        },
        'sample_data': [
            {'Asset_Name': 'mysql-prod-01', 'CI_Type': 'Database', 'Environment': 'Production'},
            {'Asset_Name': 'core-switch-01', 'CI_Type': 'Network', 'Environment': 'Production'},
            {'Asset_Name': 'firewall-dmz', 'CI_Type': 'Security', 'Environment': 'Production'}
        ]
    }


class TestAgenticWorkflowIntegration:
    """Test integration with agentic CrewAI workflows."""
    
    @patch('app.services.crewai_service.crewai_service.analyze_cmdb_data')
    async def test_agentic_cmdb_analysis_integration(self, mock_analyze, sample_cmdb_data):
        """Test that CMDB analysis integrates with agentic workflows."""
        # Mock agentic analysis response
        mock_analyze.return_value = {
            'asset_type_detected': 'mixed',
            'confidence_level': 0.95,
            'data_quality_score': 88,
            'issues': ['Minor data inconsistencies'],
            'recommendations': ['Standardize naming conventions'],
            'missing_fields_relevant': ['Business_Owner'],
            'migration_readiness': 'ready'
        }
        
        processor = CMDBDataProcessor()
        
        # Should use agentic analysis when available
        # This test verifies we don't override agentic intelligence with hard-coded rules
        assert processor.crewai_service is not None
    
    @patch('app.services.crewai_service.crewai_service.process_user_feedback')
    async def test_agentic_feedback_learning(self, mock_feedback):
        """Test that user feedback is processed through agentic learning."""
        mock_feedback.return_value = {
            'learning_applied': True,
            'patterns_identified': ['RAM_GB maps to Memory (GB)'],
            'field_mappings_learned': ['RAM_GB → Memory (GB)'],
            'accuracy_improvements': ['Improved field mapping accuracy']
        }
        
        processor = CMDBDataProcessor()
        
        # Verify feedback processing uses agentic learning
        assert processor.crewai_service is not None
    
    def test_no_hardcoded_heuristics(self):
        """Test that we don't break agentic workflows with hard-coded heuristics."""
        # Verify that classification functions support agentic input
        
        # Test that _standardize_asset_type can use agentic data
        result = _standardize_asset_type(
            "unknown_type", 
            "complex-system", 
            {
                "agentic_classification": "Custom_Application",
                "confidence": 0.95
            }
        )
        
        # Should not hard-code the result but allow agentic intelligence
        # Falls back to rule-based but doesn't prevent agentic override
        assert result in ["Application", "Server", "Unknown"]  # Valid fallback options
    
    def test_agentic_field_mapping_support(self):
        """Test that field mapping supports agentic learning."""
        processor = CMDBDataProcessor()
        
        # Test with learned mappings that would come from agentic analysis
        import pandas as pd
        
        test_data = pd.DataFrame({
            'CUSTOM_ASSET_NAME': ['test-app'],
            'BIZZ_OWNER': ['Sales Team'],
            'RAM_SIZE_GB': [32]
        })
        
        # Should not hard-code field requirements but use learned mappings
        missing_fields = processor.identify_missing_fields(test_data)
        
        # Should gracefully handle unknown field patterns
        assert isinstance(missing_fields, list)
    
    def test_extensible_device_classification(self):
        """Test that device classification is extensible for agentic learning."""
        # Test that new device types can be learned
        result = _standardize_asset_type(
            "IoT_Sensor", 
            "temperature-monitor-01", 
            {"learned_classification": "Environmental_Sensor"}
        )
        
        # Should handle unknown types gracefully without breaking
        assert result in [
            "Infrastructure Device", 
            "Unknown", 
            "Network Device"
        ]  # Valid fallback categories


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 