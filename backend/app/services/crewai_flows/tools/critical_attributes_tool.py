"""
Critical Attributes Assessment Tool for 6R Decision Making

Provides tools for persistent agents to assess the completeness of critical
attributes needed for 6R migration strategy decisions.
"""

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Import CrewAI tools
try:
    from crewai.tools import BaseTool

    CREWAI_TOOLS_AVAILABLE = True
except ImportError:
    CREWAI_TOOLS_AVAILABLE = False

    class BaseTool:
        def __init__(self, *args, **kwargs):
            pass


class CriticalAttributesDefinition:
    """Defines and validates the 22 critical attributes for 6R decisions"""

    INFRASTRUCTURE_ATTRIBUTES = [
        "operating_system_version",
        "cpu_memory_storage_specs",
        "network_configuration",
        "virtualization_platform",
        "performance_baseline",
        "availability_requirements",
    ]

    APPLICATION_ATTRIBUTES = [
        "technology_stack",
        "architecture_pattern",
        "integration_dependencies",
        "data_volume_characteristics",
        "user_load_patterns",
        "business_logic_complexity",
        "configuration_complexity",
        "security_compliance_requirements",
    ]

    BUSINESS_CONTEXT_ATTRIBUTES = [
        "business_criticality_score",
        "change_tolerance",
        "compliance_constraints",
        "stakeholder_impact",
    ]

    TECHNICAL_DEBT_ATTRIBUTES = [
        "code_quality_metrics",
        "security_vulnerabilities",
        "eol_technology_assessment",
        "documentation_quality",
    ]

    @classmethod
    def get_all_attributes(cls) -> List[str]:
        """Get all 22 critical attributes"""
        return (
            cls.INFRASTRUCTURE_ATTRIBUTES
            + cls.APPLICATION_ATTRIBUTES
            + cls.BUSINESS_CONTEXT_ATTRIBUTES
            + cls.TECHNICAL_DEBT_ATTRIBUTES
        )

    @classmethod
    def get_attribute_mapping(cls) -> Dict[str, Dict[str, Any]]:
        """Map critical attributes to asset model fields and detection patterns"""
        return {
            # Infrastructure Attributes
            "operating_system_version": {
                "asset_fields": ["operating_system", "os_version"],
                "patterns": ["os", "operating_system", "platform", "os_ver"],
                "required": True,
                "category": "infrastructure",
            },
            "cpu_memory_storage_specs": {
                "asset_fields": ["cpu_cores", "memory_gb", "storage_gb"],
                "patterns": ["cpu", "memory", "ram", "storage", "disk", "cores"],
                "required": True,
                "category": "infrastructure",
            },
            "network_configuration": {
                "asset_fields": ["ip_address", "fqdn", "mac_address"],
                "patterns": ["network", "ip", "subnet", "vlan", "nic"],
                "required": False,
                "category": "infrastructure",
            },
            "virtualization_platform": {
                "asset_fields": ["custom_attributes.virtualization_platform"],
                "patterns": ["hypervisor", "vmware", "hyper-v", "kvm", "virtual"],
                "required": False,
                "category": "infrastructure",
            },
            "performance_baseline": {
                "asset_fields": [
                    "cpu_utilization_percent",
                    "memory_utilization_percent",
                    "disk_iops",
                    "network_throughput_mbps",
                ],
                "patterns": ["utilization", "performance", "baseline", "metrics"],
                "required": False,
                "category": "infrastructure",
            },
            "availability_requirements": {
                "asset_fields": ["custom_attributes.availability_requirements"],
                "patterns": ["availability", "sla", "uptime", "rto", "rpo"],
                "required": True,
                "category": "infrastructure",
            },
            # Application Attributes
            "technology_stack": {
                "asset_fields": ["technology_stack", "custom_attributes.tech_stack"],
                "patterns": [
                    "stack",
                    "framework",
                    "runtime",
                    "language",
                    "platform",
                ],
                "required": True,
                "category": "application",
            },
            "architecture_pattern": {
                "asset_fields": ["custom_attributes.architecture_pattern"],
                "patterns": [
                    "architecture",
                    "pattern",
                    "monolithic",
                    "microservices",
                    "tier",
                ],
                "required": True,
                "category": "application",
            },
            "integration_dependencies": {
                "asset_fields": ["dependencies", "related_assets"],
                "patterns": ["dependency", "integration", "api", "service", "endpoint"],
                "required": True,
                "category": "application",
            },
            "data_volume_characteristics": {
                "asset_fields": ["custom_attributes.data_volume"],
                "patterns": ["data_volume", "database_size", "storage_usage", "data"],
                "required": False,
                "category": "application",
            },
            "user_load_patterns": {
                "asset_fields": ["custom_attributes.user_load"],
                "patterns": ["users", "load", "concurrent", "traffic", "requests"],
                "required": False,
                "category": "application",
            },
            "business_logic_complexity": {
                "asset_fields": ["custom_attributes.complexity"],
                "patterns": ["complexity", "business_logic", "rules", "workflow"],
                "required": True,
                "category": "application",
            },
            "configuration_complexity": {
                "asset_fields": ["custom_attributes.config_complexity"],
                "patterns": ["configuration", "settings", "parameters", "env"],
                "required": False,
                "category": "application",
            },
            "security_compliance_requirements": {
                "asset_fields": ["custom_attributes.compliance"],
                "patterns": ["compliance", "security", "pci", "hipaa", "gdpr", "sox"],
                "required": True,
                "category": "application",
            },
            # Business Context Attributes
            "business_criticality_score": {
                "asset_fields": ["business_criticality", "criticality"],
                "patterns": ["criticality", "priority", "importance", "tier"],
                "required": True,
                "category": "business",
            },
            "change_tolerance": {
                "asset_fields": ["custom_attributes.change_tolerance"],
                "patterns": [
                    "change_window",
                    "maintenance",
                    "tolerance",
                    "flexibility",
                ],
                "required": False,
                "category": "business",
            },
            "compliance_constraints": {
                "asset_fields": ["custom_attributes.compliance_constraints"],
                "patterns": ["regulatory", "compliance", "constraint", "requirement"],
                "required": True,
                "category": "business",
            },
            "stakeholder_impact": {
                "asset_fields": ["business_owner", "technical_owner", "department"],
                "patterns": ["owner", "stakeholder", "department", "team"],
                "required": True,
                "category": "business",
            },
            # Technical Debt Attributes
            "code_quality_metrics": {
                "asset_fields": ["custom_attributes.code_quality"],
                "patterns": ["code_quality", "technical_debt", "code_coverage"],
                "required": False,
                "category": "technical_debt",
            },
            "security_vulnerabilities": {
                "asset_fields": ["custom_attributes.vulnerabilities"],
                "patterns": ["vulnerability", "cve", "security_issue", "patch"],
                "required": True,
                "category": "technical_debt",
            },
            "eol_technology_assessment": {
                "asset_fields": ["custom_attributes.eol_assessment"],
                "patterns": ["eol", "end_of_life", "deprecated", "obsolete", "legacy"],
                "required": True,
                "category": "technical_debt",
            },
            "documentation_quality": {
                "asset_fields": ["custom_attributes.documentation_quality"],
                "patterns": ["documentation", "docs", "readme", "wiki", "runbook"],
                "required": False,
                "category": "technical_debt",
            },
        }


class CriticalAttributesAssessor:
    """Implementation of critical attributes assessment logic"""

    @staticmethod
    def assess_data_coverage(
        raw_data: List[Dict[str, Any]], field_mappings: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Assess how well the raw data covers the 22 critical attributes

        Args:
            raw_data: List of raw import records
            field_mappings: Optional field mappings already defined

        Returns:
            Assessment results with coverage metrics and recommendations
        """
        try:
            logger.info(
                f"🔍 Assessing critical attributes coverage for {len(raw_data)} records"
            )

            if not raw_data:
                return CriticalAttributesAssessor._create_empty_assessment_result()

            # Get attribute definitions
            attribute_mapping = CriticalAttributesDefinition.get_attribute_mapping()
            all_fields = CriticalAttributesAssessor._extract_fields_from_data(raw_data)

            # Analyze attribute coverage
            (
                covered_attributes,
                missing_critical,
                partial_coverage,
                attribute_details,
            ) = CriticalAttributesAssessor._analyze_attribute_coverage(
                attribute_mapping, all_fields, field_mappings
            )

            # Calculate scores and metrics
            scores = CriticalAttributesAssessor._calculate_coverage_scores(
                attribute_mapping, covered_attributes, missing_critical
            )

            # Generate recommendations
            recommendations = CriticalAttributesAssessor._generate_recommendations(
                missing_critical, partial_coverage, scores["migration_readiness_score"]
            )

            # Build category coverage
            category_coverage = CriticalAttributesAssessor._build_category_coverage(
                covered_attributes, attribute_details
            )

            return {
                "total_attributes": scores["total_attributes"],
                "covered_attributes": scores["covered_count"],
                "partial_coverage": len(partial_coverage),
                "coverage_percentage": scores["coverage_percentage"],
                "migration_readiness_score": scores["migration_readiness_score"],
                "missing_critical": missing_critical,
                "attribute_details": attribute_details,
                "recommendations": recommendations,
                "category_coverage": category_coverage,
            }

        except Exception as e:
            logger.error(f"❌ Critical attributes assessment failed: {e}")
            return {
                "error": str(e),
                "total_attributes": 22,
                "covered_attributes": 0,
                "migration_readiness_score": 0,
            }

    @staticmethod
    def _create_empty_assessment_result() -> Dict[str, Any]:
        """Create empty assessment result for when no data is available"""
        return {
            "total_attributes": 22,
            "covered_attributes": 0,
            "coverage_percentage": 0,
            "migration_readiness_score": 0,
            "missing_critical": CriticalAttributesDefinition.get_all_attributes(),
            "recommendations": ["No data available for assessment"],
        }

    @staticmethod
    def _extract_fields_from_data(raw_data: List[Dict[str, Any]]) -> set:
        """Extract unique field names from raw data records"""
        all_fields = set()
        for record in raw_data[:100]:  # Sample first 100 records
            if isinstance(record, dict):
                all_fields.update(record.keys())
        return all_fields

    @staticmethod
    def _analyze_attribute_coverage(
        attribute_mapping: Dict[str, Dict[str, Any]],
        all_fields: set,
        field_mappings: Dict[str, str] = None,
    ) -> tuple:
        """Analyze coverage for each critical attribute"""
        covered_attributes = []
        missing_critical = []
        partial_coverage = []
        attribute_details = {}

        for attr_name, attr_config in attribute_mapping.items():
            found, confidence, matched_fields = (
                CriticalAttributesAssessor._check_attribute_coverage(
                    attr_config, all_fields, field_mappings
                )
            )

            attribute_details[attr_name] = {
                "covered": found,
                "required": attr_config["required"],
                "category": attr_config["category"],
                "confidence": confidence,
                "matched_fields": matched_fields,
            }

            if found:
                if confidence >= 0.8:
                    covered_attributes.append(attr_name)
                else:
                    partial_coverage.append(attr_name)
            elif attr_config["required"]:
                missing_critical.append(attr_name)

        return covered_attributes, missing_critical, partial_coverage, attribute_details

    @staticmethod
    def _check_attribute_coverage(
        attr_config: Dict[str, Any],
        all_fields: set,
        field_mappings: Dict[str, str] = None,
    ) -> tuple:
        """Check if a single attribute is covered by available data"""
        patterns = attr_config["patterns"]
        found = False
        confidence = 0.0
        matched_fields = []

        # Check for pattern matches in raw data fields
        for field in all_fields:
            field_lower = field.lower()
            for pattern in patterns:
                if pattern in field_lower or field_lower in pattern:
                    found = True
                    matched_fields.append(field)
                    confidence = max(confidence, 0.8)
                    break

        # Check if field mappings cover this attribute
        if field_mappings:
            for source_field, target_field in field_mappings.items():
                for asset_field in attr_config["asset_fields"]:
                    if target_field == asset_field or asset_field in target_field:
                        found = True
                        matched_fields.append(f"{source_field} -> {target_field}")
                        confidence = 1.0

        return found, confidence, matched_fields

    @staticmethod
    def _calculate_coverage_scores(
        attribute_mapping: Dict[str, Dict[str, Any]],
        covered_attributes: List[str],
        missing_critical: List[str],
    ) -> Dict[str, Any]:
        """Calculate coverage scores and metrics"""
        total_attributes = len(attribute_mapping)
        covered_count = len(covered_attributes)
        coverage_percentage = (covered_count / total_attributes) * 100

        # Calculate migration readiness score (weighted by requirement)
        required_attributes = [k for k, v in attribute_mapping.items() if v["required"]]
        required_covered = len(
            [a for a in covered_attributes if a in required_attributes]
        )
        migration_readiness_score = (required_covered / len(required_attributes)) * 100

        return {
            "total_attributes": total_attributes,
            "covered_count": covered_count,
            "coverage_percentage": round(coverage_percentage, 2),
            "migration_readiness_score": round(migration_readiness_score, 2),
        }

    @staticmethod
    def _generate_recommendations(
        missing_critical: List[str],
        partial_coverage: List[str],
        migration_readiness_score: float,
    ) -> List[str]:
        """Generate recommendations based on assessment results"""
        recommendations = []

        if missing_critical:
            recommendations.append(
                f"Missing {len(missing_critical)} critical required attributes"
            )
            for attr in missing_critical[:3]:  # Show top 3
                recommendations.append(f"  - Add mapping for: {attr}")

        if partial_coverage:
            recommendations.append(
                f"{len(partial_coverage)} attributes have partial coverage"
            )

        if migration_readiness_score < 50:
            recommendations.append(
                "Migration readiness is LOW - need more critical attributes"
            )
        elif migration_readiness_score < 75:
            recommendations.append(
                "Migration readiness is MODERATE - consider enriching data"
            )
        else:
            recommendations.append(
                "Migration readiness is GOOD - sufficient attributes for 6R analysis"
            )

        return recommendations

    @staticmethod
    def _build_category_coverage(
        covered_attributes: List[str], attribute_details: Dict[str, Dict[str, Any]]
    ) -> Dict[str, int]:
        """Build category coverage metrics"""
        return {
            "infrastructure": len(
                [
                    a
                    for a in covered_attributes
                    if attribute_details[a]["category"] == "infrastructure"
                ]
            ),
            "application": len(
                [
                    a
                    for a in covered_attributes
                    if attribute_details[a]["category"] == "application"
                ]
            ),
            "business": len(
                [
                    a
                    for a in covered_attributes
                    if attribute_details[a]["category"] == "business"
                ]
            ),
            "technical_debt": len(
                [
                    a
                    for a in covered_attributes
                    if attribute_details[a]["category"] == "technical_debt"
                ]
            ),
        }


class MigrationReadinessScorer:
    """Calculate migration readiness scores based on attribute coverage"""

    @staticmethod
    def calculate_sixr_readiness(
        attribute_coverage: Dict[str, Any], asset_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Calculate readiness scores for each 6R strategy based on attribute coverage

        Args:
            attribute_coverage: Results from critical attributes assessment
            asset_data: Optional asset-specific data for more accurate scoring

        Returns:
            Readiness scores for each 6R strategy with recommendations
        """
        try:
            # Base scores influenced by attribute coverage
            readiness_score = attribute_coverage.get("migration_readiness_score", 0)
            category_coverage = attribute_coverage.get("category_coverage", {})

            sixr_scores = {
                "rehost": {
                    "score": min(
                        100, readiness_score + 20
                    ),  # Easiest, needs least info
                    "confidence": (
                        0.9 if category_coverage.get("infrastructure", 0) >= 4 else 0.5
                    ),
                    "blockers": [],
                    "requirements": ["Basic infrastructure attributes"],
                },
                "replatform": {
                    "score": min(100, readiness_score + 10),
                    "confidence": (
                        0.8 if category_coverage.get("infrastructure", 0) >= 5 else 0.4
                    ),
                    "blockers": [],
                    "requirements": ["Infrastructure and basic application attributes"],
                },
                "refactor": {
                    "score": max(0, readiness_score - 10),
                    "confidence": (
                        0.7 if category_coverage.get("application", 0) >= 6 else 0.3
                    ),
                    "blockers": [],
                    "requirements": [
                        "Complete application attributes",
                        "Technical debt assessment",
                    ],
                },
                "rearchitect": {
                    "score": max(0, readiness_score - 20),
                    "confidence": (
                        0.6 if category_coverage.get("application", 0) >= 7 else 0.2
                    ),
                    "blockers": [],
                    "requirements": [
                        "All application attributes",
                        "Architecture patterns",
                        "Dependencies",
                    ],
                },
                "replace": {
                    "score": readiness_score,  # Neutral, depends on business context
                    "confidence": (
                        0.8 if category_coverage.get("business", 0) >= 3 else 0.4
                    ),
                    "blockers": [],
                    "requirements": ["Business criticality", "Stakeholder impact"],
                },
                "rewrite": {
                    "score": max(0, readiness_score - 30),  # Most complex
                    "confidence": (
                        0.5 if category_coverage.get("technical_debt", 0) >= 3 else 0.1
                    ),
                    "blockers": [],
                    "requirements": [
                        "All attributes",
                        "Complete technical debt assessment",
                    ],
                },
            }

            # Add blockers based on missing critical attributes
            missing_critical = attribute_coverage.get("missing_critical", [])
            if "technology_stack" in missing_critical:
                sixr_scores["refactor"]["blockers"].append(
                    "Missing technology stack information"
                )
                sixr_scores["rearchitect"]["blockers"].append(
                    "Cannot assess without technology stack"
                )

            if "business_criticality_score" in missing_critical:
                sixr_scores["replace"]["blockers"].append(
                    "Business criticality unknown"
                )

            if "integration_dependencies" in missing_critical:
                sixr_scores["rearchitect"]["blockers"].append("Dependencies not mapped")

            # Calculate overall recommendation
            best_strategy = max(
                sixr_scores.items(), key=lambda x: x[1]["score"] * x[1]["confidence"]
            )

            return {
                "sixr_scores": sixr_scores,
                "recommended_strategy": best_strategy[0],
                "recommendation_confidence": best_strategy[1]["confidence"],
                "overall_readiness": readiness_score,
                "data_quality_warning": readiness_score < 50,
                "enrichment_needed": readiness_score < 75,
            }

        except Exception as e:
            logger.error(f"❌ 6R readiness scoring failed: {e}")
            return {
                "error": str(e),
                "sixr_scores": {},
                "overall_readiness": 0,
            }


def create_critical_attributes_tools(context_info: Dict[str, Any]) -> List:
    """
    Create tools for agents to assess critical attributes and migration readiness

    Args:
        context_info: Dictionary containing client_account_id, engagement_id, flow_id

    Returns:
        List of critical attributes assessment tools
    """
    logger.info(
        "🔧 Creating critical attributes assessment tools for persistent agents"
    )

    if not CREWAI_TOOLS_AVAILABLE:
        logger.warning("⚠️ CrewAI tools not available - returning empty list")
        return []

    try:
        tools = []

        # Critical attributes assessor
        assessor = CriticalAttributesAssessmentTool(context_info)
        tools.append(assessor)

        # Migration readiness scorer
        scorer = MigrationReadinessScoreTool(context_info)
        tools.append(scorer)

        # Attribute mapping suggester
        suggester = AttributeMappingSuggestionTool(context_info)
        tools.append(suggester)

        logger.info(f"✅ Created {len(tools)} critical attributes tools")
        return tools
    except Exception as e:
        logger.error(f"❌ Failed to create critical attributes tools: {e}")
        return []


# CrewAI tool implementations
def _create_crewai_tool_classes():
    """Create CrewAI tool classes when CrewAI is available"""
    if not CREWAI_TOOLS_AVAILABLE:
        return _create_dummy_tool_classes()

    return {
        "CriticalAttributesAssessmentTool": _create_assessment_tool_class(),
        "MigrationReadinessScoreTool": _create_readiness_tool_class(),
        "AttributeMappingSuggestionTool": _create_suggestion_tool_class(),
    }


def _create_assessment_tool_class():
    """Create the critical attributes assessment tool class"""

    class CriticalAttributesAssessmentTool(BaseTool):
        """Tool for assessing critical attributes coverage"""

        name: str = "critical_attributes_assessor"
        description: str = """
        Assess the coverage of 22 critical attributes needed for 6R migration decisions.
        Use this tool to evaluate data completeness and migration readiness.

        Input: Dictionary with 'raw_data' (list of records) and optional 'field_mappings'
        Output: Assessment results with coverage metrics and recommendations
        """

        def __init__(self, context_info: Dict[str, Any]):
            super().__init__()
            self._context_info = context_info

        def _run(self, assessment_request: str) -> str:
            """Assess critical attributes coverage"""
            try:
                request = json.loads(assessment_request)
                raw_data = request.get("raw_data", [])
                field_mappings = request.get("field_mappings", {})

                result = CriticalAttributesAssessor.assess_data_coverage(
                    raw_data, field_mappings
                )
                return json.dumps(result)

            except Exception as e:
                logger.error(f"❌ Critical attributes assessment failed: {e}")
                return json.dumps({"error": str(e), "migration_readiness_score": 0})

    return CriticalAttributesAssessmentTool


def _create_readiness_tool_class():
    """Create the migration readiness scoring tool class"""

    class MigrationReadinessScoreTool(BaseTool):
        """Tool for calculating 6R migration readiness scores"""

        name: str = "migration_readiness_scorer"
        description: str = """
        Calculate migration readiness scores for each 6R strategy based on attribute coverage.
        Use this to recommend the best migration strategy.

        Input: Dictionary with 'attribute_coverage' from assessment and optional 'asset_data'
        Output: 6R readiness scores with strategy recommendations
        """

        def __init__(self, context_info: Dict[str, Any]):
            super().__init__()
            self._context_info = context_info

        def _run(self, scoring_request: str) -> str:
            """Calculate 6R readiness scores"""
            try:
                request = json.loads(scoring_request)
                attribute_coverage = request.get("attribute_coverage", {})
                asset_data = request.get("asset_data", {})

                result = MigrationReadinessScorer.calculate_sixr_readiness(
                    attribute_coverage, asset_data
                )
                return json.dumps(result)

            except Exception as e:
                logger.error(f"❌ Migration readiness scoring failed: {e}")
                return json.dumps({"error": str(e), "overall_readiness": 0})

    return MigrationReadinessScoreTool


def _create_suggestion_tool_class():
    """Create the attribute mapping suggestion tool class"""

    class AttributeMappingSuggestionTool(BaseTool):
        """Tool for suggesting field mappings to critical attributes"""

        name: str = "attribute_mapping_suggester"
        description: str = """
        Suggest field mappings from source data to the 22 critical attributes.
        Use this to improve attribute coverage and migration readiness.

        Input: Dictionary with 'source_fields' list
        Output: Mapping suggestions for critical attributes with confidence scores
        """

        def __init__(self, context_info: Dict[str, Any]):
            super().__init__()
            self._context_info = context_info

        def _run(self, suggestion_request: str) -> str:
            """Suggest critical attribute mappings"""
            try:
                request = json.loads(suggestion_request)
                source_fields = request.get("source_fields", [])
                suggestions = _generate_attribute_suggestions(source_fields)
                return json.dumps(suggestions)

            except Exception as e:
                logger.error(f"❌ Attribute mapping suggestion failed: {e}")
                return json.dumps({"error": str(e), "suggestions": {}})

    return AttributeMappingSuggestionTool


def _generate_attribute_suggestions(source_fields: List[str]) -> Dict[str, Any]:
    """Generate attribute mapping suggestions for given source fields"""
    attribute_mapping = CriticalAttributesDefinition.get_attribute_mapping()
    suggestions = {}

    for field in source_fields:
        field_lower = field.lower()
        best_match, best_confidence = _find_best_attribute_match(
            field_lower, attribute_mapping
        )

        if best_match:
            suggestions[field] = {
                "critical_attribute": best_match,
                "confidence": best_confidence,
                "category": attribute_mapping[best_match]["category"],
                "required": attribute_mapping[best_match]["required"],
            }

    return {
        "suggestions": suggestions,
        "total_fields": len(source_fields),
        "mapped_to_critical": len(suggestions),
        "coverage_improvement": len(suggestions) / 22 * 100,
    }


def _find_best_attribute_match(
    field_lower: str, attribute_mapping: Dict[str, Dict[str, Any]]
) -> tuple:
    """Find the best matching attribute for a given field"""
    best_match = None
    best_confidence = 0.0

    for attr_name, attr_config in attribute_mapping.items():
        for pattern in attr_config["patterns"]:
            if pattern in field_lower or field_lower in pattern:
                confidence = 0.9 if pattern == field_lower else 0.7
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = attr_name

    return best_match, best_confidence


def _create_dummy_tool_classes():
    """Create dummy tool classes when CrewAI is not available"""

    class CriticalAttributesAssessmentTool:
        def __init__(self, context_info: Dict[str, Any]):
            pass

    class MigrationReadinessScoreTool:
        def __init__(self, context_info: Dict[str, Any]):
            pass

    class AttributeMappingSuggestionTool:
        def __init__(self, context_info: Dict[str, Any]):
            pass

    return {
        "CriticalAttributesAssessmentTool": CriticalAttributesAssessmentTool,
        "MigrationReadinessScoreTool": MigrationReadinessScoreTool,
        "AttributeMappingSuggestionTool": AttributeMappingSuggestionTool,
    }


# Create tool classes based on CrewAI availability
_TOOL_CLASSES = _create_crewai_tool_classes()
CriticalAttributesAssessmentTool = _TOOL_CLASSES["CriticalAttributesAssessmentTool"]
MigrationReadinessScoreTool = _TOOL_CLASSES["MigrationReadinessScoreTool"]
AttributeMappingSuggestionTool = _TOOL_CLASSES["AttributeMappingSuggestionTool"]
