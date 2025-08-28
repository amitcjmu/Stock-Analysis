"""
Flow Intelligence Knowledge Base - Flow Definitions
Complete flow definitions for each flow type
"""

from .flow_intelligence_enums import FlowType

# Complete Flow Definitions
FLOW_DEFINITIONS = {
    FlowType.DISCOVERY: {
        "name": "Discovery Flow",
        "description": "Asset discovery and inventory management",
        "phases": [
            {
                "id": "data_import",
                "name": "Data Import",
                "description": "Import asset data from various sources",
                "success_criteria": [
                    "At least 1 data file uploaded successfully",
                    "Raw data records > 0 in database",
                    "Import status = 'completed'",
                    "No critical import errors",
                ],
                "user_actions": [
                    "Upload CSV/Excel files with asset data",
                    "Configure data source connections",
                    "Review and fix import errors",
                ],
                "system_actions": [
                    "Process uploaded files",
                    "Validate data formats",
                    "Store raw data in database",
                ],
                "validation_services": [
                    "data_import_service.get_latest_import",
                    "data_import_service.get_import_stats",
                    "raw_data_repository.count_records",
                ],
                "navigation_path": "/discovery/cmdb-import",
            },
            {
                "id": "attribute_mapping",
                "name": "Attribute Mapping",
                "description": "Map imported fields to critical attributes",
                "success_criteria": [
                    "At least 80% of critical attributes mapped",
                    "Required identity attributes mapped (name, id)",
                    "Mapping confidence > 0.7",
                    "Field mapping saved successfully",
                ],
                "user_actions": [
                    "Review suggested field mappings",
                    "Manually map unmapped fields",
                    "Validate mapping accuracy",
                    "Save final mapping configuration",
                ],
                "system_actions": [
                    "Generate AI-powered mapping suggestions",
                    "Calculate mapping confidence scores",
                    "Apply mapping transformations",
                ],
                "validation_services": [
                    "field_mapper_service.get_mapping_status",
                    "field_mapper_service.calculate_coverage",
                    "critical_attributes_service.validate_mappings",
                ],
                "navigation_path": "/discovery/attribute-mapping/{flow_id}",
            },
            {
                "id": "data_cleansing",
                "name": "Data Cleansing",
                "description": "Clean and standardize asset data",
                "success_criteria": [
                    "Data quality score > 80%",
                    "Critical validation errors = 0",
                    "Duplicate records resolved",
                    "Standardization rules applied",
                ],
                "user_actions": [
                    "Review data quality issues",
                    "Resolve duplicate records",
                    "Fix validation errors",
                    "Apply cleansing rules",
                ],
                "system_actions": [
                    "Run data quality analysis",
                    "Detect duplicate records",
                    "Apply standardization rules",
                    "Generate quality reports",
                ],
                "validation_services": [
                    "data_cleansing_service.get_quality_score",
                    "data_cleansing_service.get_validation_results",
                    "duplicate_detection_service.get_duplicates",
                ],
                "navigation_path": "/discovery/data-cleansing/{flow_id}",
            },
            {
                "id": "inventory",
                "name": "Asset Inventory",
                "description": "Generate comprehensive asset inventory",
                "success_criteria": [
                    "All assets categorized and classified",
                    "Asset relationships identified",
                    "Inventory completeness > 95%",
                    "Asset profiles generated",
                ],
                "user_actions": [
                    "Review asset classifications",
                    "Validate asset categories",
                    "Update asset profiles",
                    "Confirm inventory accuracy",
                ],
                "system_actions": [
                    "Classify assets using AI",
                    "Generate asset profiles",
                    "Calculate inventory metrics",
                    "Create asset hierarchy",
                ],
                "validation_services": [
                    "asset_service.get_classification_status",
                    "asset_service.get_inventory_completeness",
                    "asset_service.get_categorization_results",
                ],
                "navigation_path": "/discovery/inventory/{flow_id}",
            },
            {
                "id": "dependencies",
                "name": "Dependency Analysis",
                "description": "Analyze asset dependencies and relationships",
                "success_criteria": [
                    "Dependency mapping completed",
                    "Critical dependencies identified",
                    "Dependency confidence > 0.8",
                    "Dependency graph generated",
                ],
                "user_actions": [
                    "Review dependency mappings",
                    "Validate critical dependencies",
                    "Update dependency relationships",
                    "Approve dependency analysis",
                ],
                "system_actions": [
                    "Analyze asset dependencies",
                    "Generate dependency graphs",
                    "Calculate dependency scores",
                    "Identify critical paths",
                ],
                "validation_services": [
                    "dependency_service.get_analysis_status",
                    "dependency_service.get_dependency_count",
                    "dependency_service.get_critical_dependencies",
                ],
                "navigation_path": "/discovery/dependencies/{flow_id}",
            },
            {
                "id": "tech_debt",
                "name": "Technical Debt Analysis",
                "description": "Analyze technical debt and modernization opportunities",
                "success_criteria": [
                    "Tech debt assessment completed",
                    "Modernization opportunities identified",
                    "Risk levels calculated",
                    "Recommendations generated",
                ],
                "user_actions": [
                    "Review tech debt analysis",
                    "Validate risk assessments",
                    "Prioritize modernization opportunities",
                    "Approve recommendations",
                ],
                "system_actions": [
                    "Analyze technical debt",
                    "Calculate risk scores",
                    "Generate modernization recommendations",
                    "Create priority matrices",
                ],
                "validation_services": [
                    "tech_debt_service.get_analysis_status",
                    "tech_debt_service.get_debt_score",
                    "tech_debt_service.get_recommendations",
                ],
                "navigation_path": "/discovery/tech-debt/{flow_id}",
            },
        ],
    },
    FlowType.ASSESSMENT: {
        "name": "Assessment Flow",
        "description": "Migration readiness and impact assessment",
        "phases": [
            {
                "id": "readiness_assessment",
                "name": "Readiness Assessment",
                "description": "Assess migration readiness across all dimensions",
                "success_criteria": [
                    "All assessment categories completed",
                    "Readiness score calculated",
                    "Risk factors identified",
                    "Recommendations generated",
                ],
                "user_actions": [
                    "Complete assessment questionnaires",
                    "Review readiness scores",
                    "Address identified gaps",
                    "Validate assessment results",
                ],
                "system_actions": [
                    "Calculate readiness scores",
                    "Analyze risk factors",
                    "Generate recommendations",
                    "Create readiness reports",
                ],
                "validation_services": [
                    "assessment_service.get_readiness_status",
                    "assessment_service.get_readiness_score",
                    "assessment_service.get_risk_factors",
                ],
                "navigation_path": "/assess/readiness/{flow_id}",
            },
            {
                "id": "impact_analysis",
                "name": "Impact Analysis",
                "description": "Analyze migration impact on business and operations",
                "success_criteria": [
                    "Impact analysis completed",
                    "Business impact assessed",
                    "Operational impact evaluated",
                    "Mitigation strategies defined",
                ],
                "user_actions": [
                    "Review impact assessments",
                    "Validate business impacts",
                    "Define mitigation strategies",
                    "Approve impact analysis",
                ],
                "system_actions": [
                    "Calculate business impact",
                    "Assess operational changes",
                    "Generate impact reports",
                    "Suggest mitigation strategies",
                ],
                "validation_services": [
                    "impact_service.get_analysis_status",
                    "impact_service.get_business_impact",
                    "impact_service.get_operational_impact",
                ],
                "navigation_path": "/assess/impact/{flow_id}",
            },
        ],
    },
}
