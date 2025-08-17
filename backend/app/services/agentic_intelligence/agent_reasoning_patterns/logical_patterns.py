"""
Logical reasoning patterns for Agent Intelligence Architecture

This module contains the core logical reasoning patterns that agents use to analyze
assets and discover business value, risk factors, and modernization opportunities.
These patterns represent structured business logic and technical analysis rules.
"""

import logging
from typing import Any, Dict, List

from .base import BasePatternRepository, BaseReasoningPattern

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


class BusinessValueReasoningPattern(BaseReasoningPattern):
    """
    Specialized reasoning pattern for business value analysis.
    Implements logic for evaluating asset business criticality and impact.
    """

    def __init__(self):
        super().__init__(
            "business_value_reasoning",
            "Business Value Analysis Pattern",
            "Evaluates asset business value based on usage, environment, and technology indicators",
        )

    def evaluate_business_value(
        self, asset_data: Dict[str, Any], evidence_pieces: List
    ) -> tuple[int, float, List[str]]:
        """
        Evaluate business value score with detailed reasoning.

        Args:
            asset_data: Asset data to evaluate
            evidence_pieces: Supporting evidence

        Returns:
            Tuple of (score, confidence, reasoning_parts)
        """
        base_score = 5  # Default medium value
        confidence_factors = []
        reasoning_parts = []

        # Environment analysis
        environment = asset_data.get("environment", "").lower()
        if environment in ["production", "prod"]:
            base_score += 2
            confidence_factors.append(0.9)
            reasoning_parts.append("Production environment (+2 points)")

        # Performance indicators
        cpu_util = asset_data.get("cpu_utilization_percent")
        if cpu_util is not None and cpu_util >= 70:
            base_score += 2
            confidence_factors.append(0.8)
            reasoning_parts.append(f"High CPU utilization ({cpu_util}%) (+2 points)")

        # Technology value indicators
        tech_stack = asset_data.get("technology_stack", "").lower()
        high_value_techs = ["oracle", "sap", "mainframe", "peoplesoft"]
        for tech in high_value_techs:
            if tech in tech_stack:
                base_score += 1
                confidence_factors.append(0.7)
                reasoning_parts.append(f"Enterprise technology {tech} (+1 point)")

        # Business criticality indicators
        name = asset_data.get("name", "").lower()
        critical_keywords = ["finance", "billing", "payment", "customer", "core"]
        for keyword in critical_keywords:
            if keyword in name:
                base_score += 1
                confidence_factors.append(0.6)
                reasoning_parts.append(
                    f"Business-critical naming '{keyword}' (+1 point)"
                )

        # Ensure score is in valid range
        business_value_score = max(1, min(10, base_score))

        # Calculate overall confidence
        overall_confidence = (
            sum(confidence_factors) / len(confidence_factors)
            if confidence_factors
            else 0.5
        )

        return business_value_score, overall_confidence, reasoning_parts


class RiskAssessmentReasoningPattern(BaseReasoningPattern):
    """
    Specialized reasoning pattern for risk assessment analysis.
    Implements logic for evaluating security, compliance, and operational risks.
    """

    def __init__(self):
        super().__init__(
            "risk_assessment_reasoning",
            "Risk Assessment Analysis Pattern",
            "Evaluates asset risk factors including security, compliance, and operational concerns",
        )

    def evaluate_risk_level(
        self, asset_data: Dict[str, Any], evidence_pieces: List
    ) -> tuple[str, float, List[str]]:
        """
        Evaluate risk level with detailed reasoning.

        Args:
            asset_data: Asset data to evaluate
            evidence_pieces: Supporting evidence

        Returns:
            Tuple of (risk_level, confidence, reasoning_parts)
        """
        risk_factors = 0
        confidence_factors = []
        reasoning_parts = []

        # Legacy technology risks
        tech_stack = asset_data.get("technology_stack", "").lower()
        legacy_indicators = {
            "java 8": "Legacy Java version with security vulnerabilities",
            "windows server 2012": "End-of-life Windows Server version",
            "oracle 11g": "Unsupported Oracle database version",
            "centos 6": "End-of-life CentOS version",
            "ubuntu 14": "End-of-life Ubuntu version",
        }

        for tech, risk_reason in legacy_indicators.items():
            if tech in tech_stack:
                risk_factors += 1
                confidence_factors.append(0.8)
                reasoning_parts.append(risk_reason)

        # Single point of failure risks
        name = asset_data.get("name", "").lower()
        spof_indicators = ["single", "standalone", "solo"]
        environment = asset_data.get("environment", "").lower()

        if (
            any(indicator in name for indicator in spof_indicators)
            and environment == "production"
        ):
            risk_factors += 1
            confidence_factors.append(0.7)
            reasoning_parts.append("Single point of failure in production environment")

        # Security configuration risks
        if self._has_default_credentials(asset_data):
            risk_factors += 2
            confidence_factors.append(0.9)
            reasoning_parts.append("Default or weak credentials detected")

        # Determine risk level
        if risk_factors >= 3:
            risk_level = "high"
        elif risk_factors >= 1:
            risk_level = "medium"
        else:
            risk_level = "low"

        overall_confidence = (
            sum(confidence_factors) / len(confidence_factors)
            if confidence_factors
            else 0.5
        )

        return risk_level, overall_confidence, reasoning_parts

    def _has_default_credentials(self, asset_data: Dict[str, Any]) -> bool:
        """Check for default or weak credential indicators"""
        # Placeholder for credential analysis logic
        # In real implementation, this would check for default passwords,
        # weak authentication, etc.
        return False


class ModernizationReasoningPattern(BaseReasoningPattern):
    """
    Specialized reasoning pattern for modernization potential analysis.
    Implements logic for evaluating cloud readiness and modernization opportunities.
    """

    def __init__(self):
        super().__init__(
            "modernization_reasoning",
            "Modernization Potential Analysis Pattern",
            "Evaluates asset modernization opportunities and cloud readiness",
        )

    def evaluate_modernization_potential(
        self, asset_data: Dict[str, Any], evidence_pieces: List
    ) -> tuple[int, float, List[str]]:
        """
        Evaluate modernization potential score with detailed reasoning.

        Args:
            asset_data: Asset data to evaluate
            evidence_pieces: Supporting evidence

        Returns:
            Tuple of (modernization_score, confidence, reasoning_parts)
        """
        base_score = 50  # Default medium modernization potential
        confidence_factors = []
        reasoning_parts = []

        tech_stack = asset_data.get("technology_stack", "").lower()
        asset_type = asset_data.get("asset_type", "").lower()

        # Cloud-native technology indicators
        modern_techs = {
            "kubernetes": 25,
            "docker": 20,
            "microservices": 25,
            "spring boot": 15,
            ".net core": 15,
            "nodejs": 10,
        }

        for tech, score_boost in modern_techs.items():
            if tech in tech_stack:
                base_score += score_boost
                confidence_factors.append(0.8)
                reasoning_parts.append(
                    f"Modern technology {tech} (+{score_boost} points)"
                )

        # Architecture patterns
        if "microservices" in tech_stack or "api" in asset_type:
            base_score += 15
            confidence_factors.append(0.7)
            reasoning_parts.append("Microservices/API architecture (+15 points)")

        if "stateless" in asset_data.get("description", "").lower():
            base_score += 10
            confidence_factors.append(0.6)
            reasoning_parts.append("Stateless application design (+10 points)")

        # Database modernization potential
        if "database" in asset_type:
            modern_dbs = ["postgresql", "mysql", "mongodb"]
            if any(db in tech_stack for db in modern_dbs):
                base_score += 10
                confidence_factors.append(0.7)
                reasoning_parts.append("Modern database technology (+10 points)")

        # Legacy penalties
        legacy_techs = ["java 8", "windows server 2012", "oracle 11g"]
        for legacy_tech in legacy_techs:
            if legacy_tech in tech_stack:
                base_score -= 15
                confidence_factors.append(0.8)
                reasoning_parts.append(f"Legacy technology {legacy_tech} (-15 points)")

        modernization_score = max(0, min(100, base_score))
        overall_confidence = (
            sum(confidence_factors) / len(confidence_factors)
            if confidence_factors
            else 0.5
        )

        return modernization_score, overall_confidence, reasoning_parts
