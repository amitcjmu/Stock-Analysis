"""
Asset Reasoning Patterns Repository Module

This module contains the core repository of reasoning patterns that agents use to
analyze assets and discover business value, risk factors, and modernization opportunities.
"""

import logging

# No typing imports needed for this module

from ..base import BasePatternRepository

logger = logging.getLogger(__name__)


class AssetReasoningPatterns(BasePatternRepository):
    """
    Repository of core reasoning patterns that agents use to analyze assets.
    These patterns guide how agents think about different asset characteristics.
    """

    def __init__(self):
        super().__init__("asset_reasoning_patterns")
        self._initialize_patterns()

    def _initialize_patterns(self):
        """Initialize all predefined reasoning patterns"""
        self._add_business_value_patterns()
        self._add_risk_assessment_patterns()
        self._add_modernization_patterns()

    def _add_business_value_patterns(self):
        """Add business value reasoning indicators"""
        patterns = [
            (
                "production_database_high_usage",
                {
                    "description": "Production databases with high utilization indicate critical business value",
                    "criteria": {
                        "environment": "production",
                        "asset_type": ["database", "data"],
                        "cpu_utilization_percent": {"operator": ">=", "value": 70},
                    },
                    "confidence_boost": 0.3,
                    "pattern_type": "business_value_indicator",
                    "reasoning_template": (
                        "Production database with {cpu_utilization_percent}% CPU utilization "
                        "suggests critical business usage"
                    ),
                },
            ),
            (
                "customer_facing_applications",
                {
                    "description": "Customer-facing applications typically have high business value",
                    "criteria": {
                        "naming_patterns": ["customer", "client", "portal", "api"],
                        "environment": ["production", "prod"],
                    },
                    "confidence_boost": 0.25,
                    "pattern_type": "business_value_indicator",
                    "reasoning_template": (
                        "Asset named '{name}' in {environment} environment "
                        "suggests customer-facing functionality"
                    ),
                },
            ),
            (
                "financial_system_indicators",
                {
                    "description": "Financial and transaction systems have inherently high business value",
                    "criteria": {
                        "naming_patterns": ["finance", "billing", "payment"],
                        "technology_stack": ["oracle", "sap"],
                    },
                    "confidence_boost": 0.4,
                    "pattern_type": "business_value_indicator",
                    "reasoning_template": (
                        "Financial system '{name}' using {technology_stack} "
                        "indicates critical business operations"
                    ),
                },
            ),
        ]
        for pattern_id, pattern_data in patterns:
            self.add_pattern(pattern_id, pattern_data, 0.8)

    def _add_risk_assessment_patterns(self):
        """Add risk assessment reasoning indicators"""
        risk_patterns = {
            "legacy_technology_risk": {
                "description": "Legacy technologies pose maintenance and security risks",
                "criteria": {
                    "technology_stack": {
                        "contains_any": [
                            "java 8",
                            "windows server 2012",
                            "oracle 11g",
                            "sql server 2012",
                            ".net framework 4",
                        ]
                    }
                },
                "risk_level": "medium",
                "confidence_boost": 0.2,
                "reasoning_template": "Legacy technology {technology_stack} poses maintenance and security risks",
                "pattern_type": "risk_factor",
            },
            "unsupported_platforms": {
                "description": "Unsupported platforms create significant operational risks",
                "criteria": {
                    "technology_stack": {
                        "contains_any": [
                            "centos 6",
                            "ubuntu 14",
                            "windows server 2008",
                            "java 7",
                        ]
                    }
                },
                "risk_level": "high",
                "confidence_boost": 0.35,
                "reasoning_template": (
                    "Unsupported platform {technology_stack} creates critical security "
                    "and compliance risks"
                ),
                "pattern_type": "risk_factor",
            },
            "single_point_of_failure": {
                "description": "Systems without redundancy pose availability risks",
                "criteria": {
                    "naming_patterns": ["single", "standalone", "solo"],
                    "environment": "production",
                },
                "risk_level": "medium",
                "confidence_boost": 0.2,
                "reasoning_template": "Single instance {name} in production environment poses availability risk",
                "pattern_type": "risk_factor",
            },
        }

        for pattern_id, pattern_data in risk_patterns.items():
            self.add_pattern(pattern_id, pattern_data, 0.75)

    def _add_modernization_patterns(self):
        """Add modernization potential indicators"""
        modernization_patterns = {
            "cloud_native_technologies": {
                "description": "Modern technologies are easier to modernize",
                "criteria": {
                    "technology_stack": {
                        "contains_any": [
                            "kubernetes",
                            "docker",
                            "microservices",
                            "spring boot",
                            ".net core",
                            "nodejs",
                        ]
                    }
                },
                "modernization_potential": "high",
                "confidence_boost": 0.3,
                "reasoning_template": "Modern technology {technology_stack} has high cloud modernization potential",
                "pattern_type": "modernization_opportunity",
            },
            "containerization_ready": {
                "description": "Stateless applications are ideal for containerization",
                "criteria": {
                    "asset_type": ["web application", "api", "service"],
                    "technology_stack": {
                        "contains_any": ["spring", "express", "flask", "fastapi"]
                    },
                },
                "modernization_potential": "high",
                "confidence_boost": 0.25,
                "reasoning_template": "Stateless {asset_type} using {technology_stack} is ideal for containerization",
                "pattern_type": "modernization_opportunity",
            },
            "database_modernization": {
                "description": "Standard databases can be modernized to managed cloud services",
                "criteria": {
                    "asset_type": "database",
                    "technology_stack": {
                        "contains_any": ["postgresql", "mysql", "sql server", "oracle"]
                    },
                },
                "modernization_potential": "medium",
                "confidence_boost": 0.2,
                "reasoning_template": "{technology_stack} database can be migrated to managed cloud database services",
                "pattern_type": "modernization_opportunity",
            },
        }

        for pattern_id, pattern_data in modernization_patterns.items():
            self.add_pattern(pattern_id, pattern_data, 0.7)
