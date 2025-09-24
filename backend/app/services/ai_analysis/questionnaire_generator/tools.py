"""
Questionnaire Generation Tools for AI Agents

This module provides tools that agents can use to dynamically generate
questionnaires based on identified data gaps and asset analysis.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class QuestionnaireGenerationTool:
    """Tool for generating adaptive questionnaire questions based on gaps."""

    def __init__(self):
        self.name = "questionnaire_generation"
        self.description = "Generate adaptive questions based on asset gaps and context"

    def _run(
        self,
        asset_analysis: Dict[str, Any],
        gap_type: str,
        asset_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate questions for a specific gap type and asset.

        Args:
            asset_analysis: Comprehensive analysis of the asset
            gap_type: Type of gap to address (e.g., 'missing_field', 'unmapped_attribute')
            asset_context: Context about the specific asset

        Returns:
            Generated question structure
        """
        try:
            if gap_type == "missing_field":
                return self._generate_missing_field_question(asset_analysis, asset_context)
            elif gap_type == "unmapped_attribute":
                return self._generate_unmapped_attribute_question(asset_analysis, asset_context)
            elif gap_type == "data_quality":
                return self._generate_data_quality_question(asset_analysis, asset_context)
            elif gap_type == "dependency":
                return self._generate_dependency_question(asset_analysis, asset_context)
            elif gap_type == "technical_detail":
                return self._generate_technical_detail_question(asset_analysis, asset_context)
            else:
                return self._generate_generic_question(gap_type, asset_context)

        except Exception as e:
            logger.error(f"Error generating question for gap {gap_type}: {e}")
            return self._generate_fallback_question(gap_type, asset_context)

    def _generate_missing_field_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for missing critical field."""
        field_name = asset_context.get("field_name", "unknown")
        asset_name = asset_context.get("asset_name", "the asset")
        asset_type = asset_context.get("asset_type", "application")

        # Map field names to user-friendly questions
        field_questions = {
            "business_owner": {
                "text": f"Who is the business owner responsible for {asset_name}?",
                "help_text": "Enter the name of the person or department that owns this asset from a business perspective",
                "type": "text",
                "validation": {"required": True, "min_length": 2},
            },
            "technical_owner": {
                "text": f"Who is the technical owner/team responsible for maintaining {asset_name}?",
                "help_text": "Enter the name of the technical team or individual responsible for this asset",
                "type": "text",
                "validation": {"required": True, "min_length": 2},
            },
            "six_r_strategy": {
                "text": f"What is the recommended migration strategy for {asset_name}?",
                "help_text": "Select the most appropriate 6R strategy for migrating this asset",
                "type": "select",
                "options": [
                    {"value": "rehost", "label": "Rehost (Lift & Shift)"},
                    {"value": "replatform", "label": "Replatform (Lift & Reshape)"},
                    {"value": "refactor", "label": "Refactor (Re-architect)"},
                    {"value": "repurchase", "label": "Repurchase (Replace with SaaS)"},
                    {"value": "retire", "label": "Retire (Decommission)"},
                    {"value": "retain", "label": "Retain (Keep as-is)"},
                ],
                "validation": {"required": True},
            },
            "migration_complexity": {
                "text": f"What is the migration complexity for {asset_name}?",
                "help_text": "Assess the overall complexity of migrating this asset",
                "type": "select",
                "options": [
                    {"value": "low", "label": "Low - Simple migration"},
                    {"value": "medium", "label": "Medium - Moderate complexity"},
                    {"value": "high", "label": "High - Complex migration"},
                    {"value": "very_high", "label": "Very High - Extremely complex"},
                ],
                "validation": {"required": True},
            },
            "dependencies": {
                "text": f"What other systems or applications does {asset_name} depend on?",
                "help_text": "List all dependencies, separated by commas",
                "type": "multi_select",
                "validation": {"required": False},
                "dynamic_options": True,  # Pull from existing assets
            },
            "operating_system": {
                "text": f"What operating system is {asset_name} running on?",
                "help_text": "Specify the OS and version (e.g., Windows Server 2019, Ubuntu 20.04)",
                "type": "text",
                "validation": {"required": True},
                "suggestions": ["Windows Server 2019", "Ubuntu 20.04", "RHEL 8", "CentOS 7"],
            },
        }

        base_question = field_questions.get(
            field_name,
            {
                "text": f"Please provide the {field_name.replace('_', ' ')} for {asset_name}",
                "help_text": f"This information is required for migration planning",
                "type": "text",
                "validation": {"required": True},
            },
        )

        return {
            "id": f"missing_{field_name}_{asset_context.get('asset_id', 'unknown')}",
            "category": "critical_gap",
            "priority": "critical" if field_name in ["business_owner", "six_r_strategy"] else "high",
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
            "gap_resolution": field_name,
            **base_question,
        }

    def _generate_unmapped_attribute_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for unmapped attribute validation."""
        unmapped_field = asset_context.get("unmapped_field", {})
        field_name = unmapped_field.get("field", "unknown")
        field_value = unmapped_field.get("value", "")
        suggested_mapping = unmapped_field.get("potential_mapping", "custom_attribute")

        return {
            "id": f"unmapped_{field_name}_{asset_context.get('asset_id', 'unknown')}",
            "text": f"We found unmapped data '{field_name}' with value '{field_value}'. How should this be categorized?",
            "help_text": f"This data was imported but couldn't be automatically mapped. Suggested: {suggested_mapping}",
            "type": "select",
            "category": "data_mapping",
            "priority": "medium",
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
            "options": [
                {"value": "ignore", "label": "Ignore this field"},
                {"value": suggested_mapping, "label": f"Map to {suggested_mapping}"},
                {"value": "custom", "label": "Create custom attribute"},
                {"value": "merge", "label": "Merge with existing field"},
            ],
            "conditional_follow_up": {
                "custom": {
                    "text": "What should this custom attribute be called?",
                    "type": "text",
                },
                "merge": {
                    "text": "Which existing field should this be merged with?",
                    "type": "select",
                    "dynamic_options": True,
                },
            },
        }

    def _generate_data_quality_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question to validate data quality issues."""
        asset_name = asset_context.get("asset_name", "the asset")
        quality_issue = asset_context.get("quality_issue", {})

        return {
            "id": f"quality_{asset_context.get('asset_id', 'unknown')}",
            "text": f"Please verify the following information for {asset_name}",
            "help_text": f"Data quality score is low ({quality_issue.get('completeness', 0):.1%}). Please confirm or update.",
            "type": "review_and_confirm",
            "category": "data_validation",
            "priority": "high",
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
            "fields_to_review": asset_context.get("fields_to_review", []),
            "validation": {
                "require_confirmation": True,
                "allow_edits": True,
            },
        }

    def _generate_dependency_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question about asset dependencies."""
        asset_name = asset_context.get("asset_name", "the asset")

        return {
            "id": f"dependencies_{asset_context.get('asset_id', 'unknown')}",
            "text": f"Please map the dependencies for {asset_name}",
            "help_text": "Identify all systems this asset depends on or that depend on it",
            "type": "dependency_mapper",
            "category": "technical_architecture",
            "priority": "high",
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
            "sub_questions": [
                {
                    "id": "upstream",
                    "text": "What does this asset depend on?",
                    "type": "multi_select",
                    "dynamic_options": True,
                },
                {
                    "id": "downstream",
                    "text": "What depends on this asset?",
                    "type": "multi_select",
                    "dynamic_options": True,
                },
                {
                    "id": "integration_type",
                    "text": "How are these systems integrated?",
                    "type": "select",
                    "options": [
                        {"value": "api", "label": "API/Web Service"},
                        {"value": "database", "label": "Direct Database"},
                        {"value": "file", "label": "File Transfer"},
                        {"value": "message_queue", "label": "Message Queue"},
                        {"value": "other", "label": "Other"},
                    ],
                },
            ],
        }

    def _generate_technical_detail_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for technical details."""
        asset_name = asset_context.get("asset_name", "the asset")
        asset_type = asset_context.get("asset_type", "application")

        # Generate appropriate technical questions based on asset type
        if asset_type == "database":
            return self._generate_database_technical_question(asset_context)
        elif asset_type == "application":
            return self._generate_application_technical_question(asset_context)
        elif asset_type == "server":
            return self._generate_server_technical_question(asset_context)
        else:
            return self._generate_generic_technical_question(asset_context)

    def _generate_database_technical_question(self, asset_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate database-specific technical questions."""
        asset_name = asset_context.get("asset_name", "the database")

        return {
            "id": f"db_tech_{asset_context.get('asset_id', 'unknown')}",
            "text": f"Please provide technical details for database {asset_name}",
            "type": "grouped_fields",
            "category": "technical_details",
            "priority": "medium",
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
            "field_groups": [
                {
                    "group_name": "Database Configuration",
                    "fields": [
                        {
                            "id": "db_type",
                            "text": "Database Type",
                            "type": "select",
                            "options": [
                                {"value": "mysql", "label": "MySQL"},
                                {"value": "postgresql", "label": "PostgreSQL"},
                                {"value": "oracle", "label": "Oracle"},
                                {"value": "sqlserver", "label": "SQL Server"},
                                {"value": "mongodb", "label": "MongoDB"},
                                {"value": "other", "label": "Other"},
                            ],
                        },
                        {
                            "id": "db_version",
                            "text": "Database Version",
                            "type": "text",
                        },
                        {
                            "id": "db_size_gb",
                            "text": "Database Size (GB)",
                            "type": "number",
                            "validation": {"min": 0},
                        },
                    ],
                },
                {
                    "group_name": "Performance Metrics",
                    "fields": [
                        {
                            "id": "daily_transactions",
                            "text": "Average Daily Transactions",
                            "type": "number",
                        },
                        {
                            "id": "peak_connections",
                            "text": "Peak Concurrent Connections",
                            "type": "number",
                        },
                    ],
                },
            ],
        }

    def _generate_application_technical_question(self, asset_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate application-specific technical questions."""
        asset_name = asset_context.get("asset_name", "the application")

        return {
            "id": f"app_tech_{asset_context.get('asset_id', 'unknown')}",
            "text": f"Please provide technical details for application {asset_name}",
            "type": "grouped_fields",
            "category": "technical_details",
            "priority": "medium",
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
            "field_groups": [
                {
                    "group_name": "Application Architecture",
                    "fields": [
                        {
                            "id": "architecture_type",
                            "text": "Architecture Type",
                            "type": "select",
                            "options": [
                                {"value": "monolithic", "label": "Monolithic"},
                                {"value": "microservices", "label": "Microservices"},
                                {"value": "soa", "label": "Service-Oriented"},
                                {"value": "serverless", "label": "Serverless"},
                                {"value": "other", "label": "Other"},
                            ],
                        },
                        {
                            "id": "programming_languages",
                            "text": "Programming Languages Used",
                            "type": "multi_select",
                            "options": [
                                {"value": "java", "label": "Java"},
                                {"value": "csharp", "label": "C#/.NET"},
                                {"value": "python", "label": "Python"},
                                {"value": "javascript", "label": "JavaScript"},
                                {"value": "go", "label": "Go"},
                                {"value": "other", "label": "Other"},
                            ],
                        },
                        {
                            "id": "framework",
                            "text": "Primary Framework",
                            "type": "text",
                        },
                    ],
                },
                {
                    "group_name": "Deployment",
                    "fields": [
                        {
                            "id": "deployment_type",
                            "text": "Current Deployment Type",
                            "type": "select",
                            "options": [
                                {"value": "vm", "label": "Virtual Machine"},
                                {"value": "container", "label": "Container"},
                                {"value": "bare_metal", "label": "Bare Metal"},
                                {"value": "paas", "label": "PaaS"},
                            ],
                        },
                        {
                            "id": "container_ready",
                            "text": "Is the application container-ready?",
                            "type": "select",
                            "options": [
                                {"value": "yes", "label": "Yes"},
                                {"value": "no", "label": "No"},
                                {"value": "partial", "label": "Partially"},
                                {"value": "unknown", "label": "Unknown"},
                            ],
                        },
                    ],
                },
            ],
        }

    def _generate_server_technical_question(self, asset_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate server-specific technical questions."""
        asset_name = asset_context.get("asset_name", "the server")

        return {
            "id": f"server_tech_{asset_context.get('asset_id', 'unknown')}",
            "text": f"Please provide technical details for server {asset_name}",
            "type": "grouped_fields",
            "category": "technical_details",
            "priority": "medium",
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
            "field_groups": [
                {
                    "group_name": "Hardware Specifications",
                    "fields": [
                        {
                            "id": "cpu_cores",
                            "text": "Number of CPU Cores",
                            "type": "number",
                            "validation": {"min": 1},
                        },
                        {
                            "id": "memory_gb",
                            "text": "Memory (GB)",
                            "type": "number",
                            "validation": {"min": 0},
                        },
                        {
                            "id": "storage_gb",
                            "text": "Total Storage (GB)",
                            "type": "number",
                            "validation": {"min": 0},
                        },
                    ],
                },
                {
                    "group_name": "Virtualization",
                    "fields": [
                        {
                            "id": "is_virtual",
                            "text": "Is this a virtual machine?",
                            "type": "select",
                            "options": [
                                {"value": "yes", "label": "Yes"},
                                {"value": "no", "label": "No (Physical)"},
                            ],
                        },
                        {
                            "id": "hypervisor",
                            "text": "Hypervisor Type (if virtual)",
                            "type": "select",
                            "options": [
                                {"value": "vmware", "label": "VMware"},
                                {"value": "hyper-v", "label": "Hyper-V"},
                                {"value": "kvm", "label": "KVM"},
                                {"value": "xen", "label": "Xen"},
                                {"value": "other", "label": "Other"},
                                {"value": "na", "label": "N/A"},
                            ],
                            "conditional_on": {"is_virtual": "yes"},
                        },
                    ],
                },
            ],
        }

    def _generate_generic_technical_question(self, asset_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate generic technical question for unknown asset types."""
        return {
            "id": f"generic_tech_{asset_context.get('asset_id', 'unknown')}",
            "text": f"Please provide additional technical details for {asset_context.get('asset_name', 'this asset')}",
            "type": "textarea",
            "category": "technical_details",
            "priority": "low",
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
            "help_text": "Provide any relevant technical information that would help with migration planning",
            "validation": {"min_length": 10},
        }

    def _generate_generic_question(self, gap_type: str, asset_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a generic question for unknown gap types."""
        return {
            "id": f"generic_{gap_type}_{asset_context.get('asset_id', 'unknown')}",
            "text": f"Please provide information about {gap_type.replace('_', ' ')} for {asset_context.get('asset_name', 'this asset')}",
            "type": "text",
            "category": "general",
            "priority": "low",
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
            "validation": {"required": False},
        }

    def _generate_fallback_question(self, gap_type: str, asset_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a fallback question when generation fails."""
        return {
            "id": f"fallback_{asset_context.get('asset_id', 'unknown')}",
            "text": "Please provide any additional information about this asset",
            "type": "textarea",
            "category": "general",
            "priority": "low",
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
            "help_text": f"Unable to generate specific question for {gap_type}",
        }


class GapAnalysisTool:
    """Tool for analyzing data gaps in assets."""

    def __init__(self):
        self.name = "gap_analysis"
        self.description = "Analyze assets to identify data gaps and prioritize them"

    def _run(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an asset to identify and prioritize data gaps.

        Args:
            asset_data: Asset information including mapped and unmapped data

        Returns:
            Gap analysis results with prioritized gaps
        """
        gaps = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }

        # Check for critical missing fields
        critical_fields = ["business_owner", "technical_owner", "six_r_strategy"]
        for field in critical_fields:
            if not asset_data.get(field):
                gaps["critical"].append({
                    "type": "missing_field",
                    "field": field,
                    "impact": "Cannot proceed with migration planning without this information",
                })

        # Check for high priority fields
        high_priority_fields = ["migration_complexity", "dependencies", "operating_system"]
        for field in high_priority_fields:
            if not asset_data.get(field):
                gaps["high"].append({
                    "type": "missing_field",
                    "field": field,
                    "impact": "Migration risk assessment incomplete",
                })

        # Check for unmapped attributes
        unmapped = asset_data.get("unmapped_attributes", [])
        if unmapped:
            gaps["medium"].append({
                "type": "unmapped_attributes",
                "count": len(unmapped),
                "attributes": unmapped[:5],  # First 5 for summary
                "impact": "Potential data loss or misclassification",
            })

        # Check data quality
        completeness = asset_data.get("completeness_score", 0)
        if completeness < 0.8:
            gaps["high" if completeness < 0.5 else "medium"].append({
                "type": "data_quality",
                "completeness": completeness,
                "impact": "Low confidence in migration decisions",
            })

        return {
            "asset_id": asset_data.get("asset_id"),
            "asset_name": asset_data.get("asset_name"),
            "gaps": gaps,
            "total_gaps": sum(len(v) for v in gaps.values()),
            "priority_score": self._calculate_priority_score(gaps),
        }

    def _calculate_priority_score(self, gaps: Dict[str, List]) -> float:
        """Calculate priority score based on gap severity."""
        weights = {"critical": 10, "high": 5, "medium": 2, "low": 1}
        score = sum(len(gaps[level]) * weight for level, weight in weights.items())
        return min(100, score * 2)  # Normalize to 0-100


class AssetIntelligenceTool:
    """Tool for gathering intelligence about assets."""

    def __init__(self):
        self.name = "asset_intelligence"
        self.description = "Gather comprehensive intelligence about assets including patterns and relationships"

    def _run(self, asset_id: str, asset_collection: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gather intelligence about an asset including patterns and relationships.

        Args:
            asset_id: ID of the asset to analyze
            asset_collection: Collection of all assets for relationship analysis

        Returns:
            Intelligence report about the asset
        """
        # Find the target asset
        target_asset = None
        for asset in asset_collection:
            if asset.get("asset_id") == asset_id:
                target_asset = asset
                break

        if not target_asset:
            return {"error": f"Asset {asset_id} not found"}

        # Analyze patterns
        similar_assets = self._find_similar_assets(target_asset, asset_collection)
        common_gaps = self._identify_common_gaps(similar_assets)
        migration_patterns = self._analyze_migration_patterns(similar_assets)

        return {
            "asset_id": asset_id,
            "asset_type": target_asset.get("asset_type"),
            "similar_assets": len(similar_assets),
            "common_gaps": common_gaps,
            "migration_patterns": migration_patterns,
            "recommended_questions": self._recommend_questions(common_gaps, migration_patterns),
            "confidence_level": self._calculate_confidence(target_asset, similar_assets),
        }

    def _find_similar_assets(
        self, target: Dict[str, Any], collection: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find assets similar to the target based on type and characteristics."""
        similar = []
        target_type = target.get("asset_type")
        target_stack = target.get("technology_stack", "").lower()

        for asset in collection:
            if asset.get("asset_id") == target.get("asset_id"):
                continue

            similarity_score = 0

            # Same type
            if asset.get("asset_type") == target_type:
                similarity_score += 3

            # Similar technology stack
            if target_stack and asset.get("technology_stack", "").lower() in target_stack:
                similarity_score += 2

            # Same environment
            if asset.get("environment") == target.get("environment"):
                similarity_score += 1

            # Same criticality
            if asset.get("criticality") == target.get("criticality"):
                similarity_score += 1

            if similarity_score >= 3:
                similar.append(asset)

        return similar

    def _identify_common_gaps(self, assets: List[Dict[str, Any]]) -> Dict[str, int]:
        """Identify common data gaps across similar assets."""
        gap_counts = {}

        for asset in assets:
            # Check missing fields
            for field in ["business_owner", "technical_owner", "dependencies", "six_r_strategy"]:
                if not asset.get(field):
                    gap_counts[field] = gap_counts.get(field, 0) + 1

        # Calculate percentages
        total = len(assets) if assets else 1
        return {field: count / total for field, count in gap_counts.items()}

    def _analyze_migration_patterns(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze migration patterns from similar assets."""
        strategies = {}
        complexities = {}

        for asset in assets:
            strategy = asset.get("six_r_strategy")
            if strategy:
                strategies[strategy] = strategies.get(strategy, 0) + 1

            complexity = asset.get("migration_complexity")
            if complexity:
                complexities[complexity] = complexities.get(complexity, 0) + 1

        return {
            "common_strategy": max(strategies.items(), key=lambda x: x[1])[0] if strategies else None,
            "common_complexity": max(complexities.items(), key=lambda x: x[1])[0] if complexities else None,
            "strategy_distribution": strategies,
            "complexity_distribution": complexities,
        }

    def _recommend_questions(
        self, common_gaps: Dict[str, float], patterns: Dict[str, Any]
    ) -> List[str]:
        """Recommend questions based on gaps and patterns."""
        recommendations = []

        # Recommend based on common gaps
        for field, percentage in common_gaps.items():
            if percentage > 0.5:
                recommendations.append(f"Focus on collecting {field} - missing in {percentage:.0%} of similar assets")

        # Recommend based on patterns
        if patterns.get("common_strategy"):
            recommendations.append(
                f"Consider {patterns['common_strategy']} strategy - most common for similar assets"
            )

        return recommendations

    def _calculate_confidence(self, asset: Dict[str, Any], similar: List[Dict[str, Any]]) -> str:
        """Calculate confidence level for recommendations."""
        if len(similar) >= 10:
            return "high"
        elif len(similar) >= 5:
            return "medium"
        else:
            return "low"


def create_questionnaire_generation_tools():
    """Create and return all questionnaire generation tools."""
    return [
        QuestionnaireGenerationTool(),
        GapAnalysisTool(),
        AssetIntelligenceTool(),
    ]


def create_gap_analysis_tools():
    """Create and return gap analysis specific tools."""
    return [GapAnalysisTool(), AssetIntelligenceTool()]