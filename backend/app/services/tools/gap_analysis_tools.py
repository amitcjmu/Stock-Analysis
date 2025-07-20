"""
Gap Analysis Tools for Critical Attribute Assessment and Prioritization
"""

from typing import Dict, Any, List, Optional, Tuple, ClassVar
from app.services.tools.base_tool import BaseDiscoveryTool, AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata
from app.core.database_context import get_context_db
from sqlalchemy import select, func
import logging
import json
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Import models safely
try:
    from app.models.asset import Asset
    from app.models.discovery_asset import DiscoveryAsset
    from app.models.data_import import DataImport
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    Asset = None
    DiscoveryAsset = None
    DataImport = None


class AttributeMapperTool(AsyncBaseDiscoveryTool):
    """Maps collected data fields to critical attributes framework"""
    
    name: str = "attribute_mapper"
    description: str = "Map raw data fields to the 22 critical attributes framework"
    
    # Critical attributes mapping patterns
    ATTRIBUTE_PATTERNS: ClassVar[Dict[str, List[str]]] = {
        # Infrastructure attributes
        "hostname": ["hostname", "server_name", "host", "machine_name", "computer_name"],
        "environment": ["environment", "env", "stage", "tier", "deployment_env"],
        "os_type": ["os_type", "operating_system", "os", "platform", "os_family"],
        "os_version": ["os_version", "os_ver", "version", "os_release", "kernel_version"],
        "cpu_cores": ["cpu_cores", "cores", "vcpu", "processors", "cpu_count"],
        "memory_gb": ["memory_gb", "ram", "memory", "total_memory", "mem_size"],
        "storage_gb": ["storage_gb", "disk_size", "storage", "disk_space", "total_storage"],
        "network_zone": ["network_zone", "subnet", "vlan", "network", "security_zone"],
        
        # Application attributes
        "application_name": ["application_name", "app_name", "application", "service_name"],
        "application_type": ["application_type", "app_type", "category", "app_category"],
        "technology_stack": ["technology_stack", "tech_stack", "framework", "platform", "runtime"],
        "criticality_level": ["criticality_level", "criticality", "priority", "importance"],
        "data_classification": ["data_classification", "data_class", "sensitivity", "classification"],
        "compliance_scope": ["compliance_scope", "compliance", "regulatory", "compliance_req"],
        
        # Operational attributes
        "owner": ["owner", "owner_group", "responsible_party", "team", "department"],
        "cost_center": ["cost_center", "cost_centre", "budget_code", "financial_code"],
        "backup_strategy": ["backup_strategy", "backup_policy", "backup_type", "recovery_strategy"],
        "monitoring_status": ["monitoring_status", "monitoring", "monitored", "monitoring_enabled"],
        "patch_level": ["patch_level", "patch_status", "update_level", "patch_version"],
        "last_scan_date": ["last_scan_date", "scan_date", "last_scanned", "discovery_date"],
        
        # Dependencies attributes
        "application_dependencies": ["application_dependencies", "app_dependencies", "depends_on", "dependencies"],
        "database_dependencies": ["database_dependencies", "db_dependencies", "databases", "data_sources"],
        "integration_points": ["integration_points", "integrations", "interfaces", "api_connections"],
        "data_flows": ["data_flows", "data_transfer", "data_movement", "flow_direction"]
    }
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        return ToolMetadata(
            name="attribute_mapper",
            description="Map raw data fields to the 22 critical attributes framework",
            tool_class=cls,
            categories=["gap_analysis", "attribute_mapping"],
            required_params=["data_fields"],
            optional_params=[],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(self, data_fields: List[str]) -> Dict[str, Any]:
        """Map data fields to critical attributes"""
        try:
            self.log_with_context('info', f"Mapping {len(data_fields)} fields to critical attributes")
            
            mapping_results = {
                "mapped_attributes": {},
                "unmapped_fields": [],
                "confidence_scores": {},
                "suggestions": []
            }
            
            # Normalize field names for comparison
            normalized_fields = {field.lower().replace(" ", "_"): field for field in data_fields}
            
            # Map each critical attribute
            for attribute, patterns in self.ATTRIBUTE_PATTERNS.items():
                best_match = None
                best_score = 0.0
                
                for pattern in patterns:
                    pattern_lower = pattern.lower()
                    
                    # Exact match
                    if pattern_lower in normalized_fields:
                        best_match = normalized_fields[pattern_lower]
                        best_score = 1.0
                        break
                    
                    # Partial match scoring
                    for norm_field, original_field in normalized_fields.items():
                        score = self._calculate_similarity(pattern_lower, norm_field)
                        if score > best_score and score > 0.6:  # Threshold for consideration
                            best_match = original_field
                            best_score = score
                
                if best_match:
                    mapping_results["mapped_attributes"][attribute] = best_match
                    mapping_results["confidence_scores"][attribute] = best_score
                    
                    if best_score < 0.8:
                        mapping_results["suggestions"].append({
                            "attribute": attribute,
                            "mapped_to": best_match,
                            "confidence": best_score,
                            "suggestion": "Consider manual verification due to lower confidence"
                        })
            
            # Identify unmapped fields
            mapped_fields = set(mapping_results["mapped_attributes"].values())
            mapping_results["unmapped_fields"] = [
                field for field in data_fields if field not in mapped_fields
            ]
            
            # Calculate coverage
            total_attributes = len(self.ATTRIBUTE_PATTERNS)
            mapped_count = len(mapping_results["mapped_attributes"])
            mapping_results["coverage_percentage"] = (mapped_count / total_attributes) * 100
            
            self.log_with_context(
                'info', 
                f"Mapped {mapped_count}/{total_attributes} attributes ({mapping_results['coverage_percentage']:.1f}% coverage)"
            )
            
            return mapping_results
            
        except Exception as e:
            self.log_with_context('error', f"Error in attribute mapping: {e}")
            return {"error": str(e)}
    
    def _calculate_similarity(self, pattern: str, field: str) -> float:
        """Calculate similarity score between pattern and field"""
        # Simple similarity based on common substrings
        if pattern in field or field in pattern:
            return 0.8
        
        # Check for common words
        pattern_words = set(pattern.split('_'))
        field_words = set(field.split('_'))
        common_words = pattern_words.intersection(field_words)
        
        if common_words:
            return len(common_words) / max(len(pattern_words), len(field_words))
        
        return 0.0


class CompletenessAnalyzerTool(AsyncBaseDiscoveryTool):
    """Analyzes completeness of critical attributes in collected data"""
    
    name: str = "completeness_analyzer"
    description: str = "Analyze completeness and quality of critical attributes"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        return ToolMetadata(
            name="completeness_analyzer",
            description="Analyze completeness and quality of critical attributes",
            tool_class=cls,
            categories=["gap_analysis", "data_quality"],
            required_params=["data", "attribute_mapping"],
            optional_params=[],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(self, data: List[Dict[str, Any]], attribute_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Analyze completeness of mapped attributes in data"""
        try:
            self.log_with_context('info', f"Analyzing completeness for {len(data)} records")
            
            analysis_results = {
                "total_records": len(data),
                "attribute_completeness": {},
                "category_completeness": {
                    "infrastructure": {"total": 8, "complete": 0, "percentage": 0.0},
                    "application": {"total": 6, "complete": 0, "percentage": 0.0},
                    "operational": {"total": 6, "complete": 0, "percentage": 0.0},
                    "dependencies": {"total": 4, "complete": 0, "percentage": 0.0}
                },
                "quality_issues": [],
                "recommendations": []
            }
            
            # Categorize attributes
            attribute_categories = {
                "infrastructure": ["hostname", "environment", "os_type", "os_version", 
                                 "cpu_cores", "memory_gb", "storage_gb", "network_zone"],
                "application": ["application_name", "application_type", "technology_stack",
                              "criticality_level", "data_classification", "compliance_scope"],
                "operational": ["owner", "cost_center", "backup_strategy", "monitoring_status",
                              "patch_level", "last_scan_date"],
                "dependencies": ["application_dependencies", "database_dependencies",
                               "integration_points", "data_flows"]
            }
            
            # Analyze each attribute
            for attribute, field_name in attribute_mapping.items():
                completeness_info = {
                    "field_name": field_name,
                    "records_with_data": 0,
                    "completeness_percentage": 0.0,
                    "null_count": 0,
                    "empty_count": 0,
                    "quality_score": 0.0
                }
                
                # Count completeness
                for record in data:
                    value = record.get(field_name)
                    if value is not None:
                        if value == "" or (isinstance(value, str) and value.lower() in ["null", "n/a", "unknown"]):
                            completeness_info["empty_count"] += 1
                        else:
                            completeness_info["records_with_data"] += 1
                    else:
                        completeness_info["null_count"] += 1
                
                # Calculate percentages
                if len(data) > 0:
                    completeness_info["completeness_percentage"] = (
                        completeness_info["records_with_data"] / len(data)
                    ) * 100
                    completeness_info["quality_score"] = self._calculate_quality_score(
                        completeness_info, len(data)
                    )
                
                analysis_results["attribute_completeness"][attribute] = completeness_info
                
                # Update category completeness
                for category, attributes in attribute_categories.items():
                    if attribute in attributes and completeness_info["completeness_percentage"] > 80:
                        analysis_results["category_completeness"][category]["complete"] += 1
                
                # Identify quality issues
                if completeness_info["completeness_percentage"] < 50:
                    analysis_results["quality_issues"].append({
                        "attribute": attribute,
                        "issue": "Low completeness",
                        "impact": "high" if attribute in ["hostname", "application_name", "owner"] else "medium",
                        "recommendation": f"Prioritize collecting {attribute} data"
                    })
            
            # Calculate category percentages
            for category in analysis_results["category_completeness"]:
                cat_data = analysis_results["category_completeness"][category]
                cat_data["percentage"] = (cat_data["complete"] / cat_data["total"]) * 100
            
            # Generate recommendations
            analysis_results["recommendations"] = self._generate_completeness_recommendations(
                analysis_results
            )
            
            self.log_with_context('info', "Completeness analysis completed")
            return analysis_results
            
        except Exception as e:
            self.log_with_context('error', f"Error in completeness analysis: {e}")
            return {"error": str(e)}
    
    def _calculate_quality_score(self, completeness_info: Dict[str, Any], total_records: int) -> float:
        """Calculate quality score for an attribute"""
        if total_records == 0:
            return 0.0
        
        # Base score on completeness
        score = completeness_info["completeness_percentage"] / 100
        
        # Penalize for empty/null values
        empty_ratio = completeness_info["empty_count"] / total_records
        null_ratio = completeness_info["null_count"] / total_records
        
        score = score * (1 - empty_ratio * 0.5) * (1 - null_ratio * 0.3)
        
        return round(score * 100, 2)
    
    def _generate_completeness_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on completeness analysis"""
        recommendations = []
        
        # Check category completeness
        for category, data in analysis["category_completeness"].items():
            if data["percentage"] < 50:
                recommendations.append(
                    f"Critical: {category} attributes are only {data['percentage']:.0f}% complete. "
                    f"Focus on collecting {category} data to improve migration readiness."
                )
        
        # Check for critical missing attributes
        critical_attributes = ["hostname", "application_name", "owner", "environment"]
        for attr in critical_attributes:
            if attr in analysis["attribute_completeness"]:
                if analysis["attribute_completeness"][attr]["completeness_percentage"] < 80:
                    recommendations.append(
                        f"High Priority: {attr} is critical but only "
                        f"{analysis['attribute_completeness'][attr]['completeness_percentage']:.0f}% complete"
                    )
        
        return recommendations


class QualityScorerTool(AsyncBaseDiscoveryTool):
    """Scores data quality for critical attributes"""
    
    name: str = "quality_scorer"
    description: str = "Calculate quality scores for critical attribute data"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        return ToolMetadata(
            name="quality_scorer",
            description="Calculate quality scores for critical attribute data",
            tool_class=cls,
            categories=["gap_analysis", "data_quality"],
            required_params=["data", "attribute_mapping"],
            optional_params=[],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(self, data: List[Dict[str, Any]], attribute_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Calculate quality scores for mapped attributes"""
        try:
            self.log_with_context('info', "Calculating quality scores")
            
            quality_results = {
                "overall_quality_score": 0.0,
                "attribute_scores": {},
                "quality_dimensions": {
                    "accuracy": 0.0,
                    "completeness": 0.0,
                    "consistency": 0.0,
                    "timeliness": 0.0,
                    "validity": 0.0
                },
                "quality_issues": []
            }
            
            attribute_scores = []
            
            for attribute, field_name in attribute_mapping.items():
                attr_quality = self._assess_attribute_quality(data, field_name, attribute)
                quality_results["attribute_scores"][attribute] = attr_quality
                attribute_scores.append(attr_quality["overall_score"])
                
                # Track quality issues
                if attr_quality["overall_score"] < 60:
                    quality_results["quality_issues"].append({
                        "attribute": attribute,
                        "score": attr_quality["overall_score"],
                        "main_issues": attr_quality["issues"]
                    })
            
            # Calculate overall score
            if attribute_scores:
                quality_results["overall_quality_score"] = sum(attribute_scores) / len(attribute_scores)
            
            # Update quality dimensions
            quality_results["quality_dimensions"] = self._calculate_quality_dimensions(
                quality_results["attribute_scores"]
            )
            
            self.log_with_context(
                'info', 
                f"Quality scoring completed. Overall score: {quality_results['overall_quality_score']:.1f}"
            )
            
            return quality_results
            
        except Exception as e:
            self.log_with_context('error', f"Error in quality scoring: {e}")
            return {"error": str(e)}
    
    def _assess_attribute_quality(self, data: List[Dict[str, Any]], field_name: str, attribute: str) -> Dict[str, Any]:
        """Assess quality for a single attribute"""
        quality_assessment = {
            "attribute": attribute,
            "field_name": field_name,
            "overall_score": 0.0,
            "issues": [],
            "metrics": {
                "completeness": 0.0,
                "validity": 0.0,
                "consistency": 0.0,
                "accuracy": 0.0
            }
        }
        
        if not data:
            return quality_assessment
        
        # Collect values
        values = []
        null_count = 0
        invalid_count = 0
        
        for record in data:
            value = record.get(field_name)
            if value is None:
                null_count += 1
            elif isinstance(value, str) and value.lower() in ["null", "n/a", "unknown", ""]:
                invalid_count += 1
            else:
                values.append(value)
        
        total_records = len(data)
        
        # Calculate completeness
        quality_assessment["metrics"]["completeness"] = (len(values) / total_records * 100) if total_records > 0 else 0
        
        # Calculate validity (basic checks)
        if values:
            quality_assessment["metrics"]["validity"] = self._calculate_validity(values, attribute)
        
        # Calculate consistency
        if values:
            quality_assessment["metrics"]["consistency"] = self._calculate_consistency(values)
        
        # Estimate accuracy (simplified)
        quality_assessment["metrics"]["accuracy"] = 80.0 if len(values) > total_records * 0.7 else 50.0
        
        # Calculate overall score
        metrics = quality_assessment["metrics"]
        quality_assessment["overall_score"] = (
            metrics["completeness"] * 0.4 +
            metrics["validity"] * 0.3 +
            metrics["consistency"] * 0.2 +
            metrics["accuracy"] * 0.1
        )
        
        # Identify issues
        if metrics["completeness"] < 50:
            quality_assessment["issues"].append("Low completeness")
        if metrics["validity"] < 70:
            quality_assessment["issues"].append("Validity concerns")
        if metrics["consistency"] < 80:
            quality_assessment["issues"].append("Inconsistent data")
        
        return quality_assessment
    
    def _calculate_validity(self, values: List[Any], attribute: str) -> float:
        """Calculate validity score for values"""
        valid_count = 0
        
        # Attribute-specific validation
        validation_rules = {
            "cpu_cores": lambda v: isinstance(v, (int, float)) and 0 < v <= 1024,
            "memory_gb": lambda v: isinstance(v, (int, float)) and 0 < v <= 10240,
            "storage_gb": lambda v: isinstance(v, (int, float)) and 0 < v <= 1000000,
            "hostname": lambda v: isinstance(v, str) and len(v) > 2,
            "environment": lambda v: isinstance(v, str) and v.lower() in ["dev", "test", "qa", "staging", "prod", "production"],
            "os_type": lambda v: isinstance(v, str) and any(os in v.lower() for os in ["windows", "linux", "unix", "aix", "solaris"])
        }
        
        validation_func = validation_rules.get(attribute, lambda v: v is not None and v != "")
        
        for value in values:
            try:
                if validation_func(value):
                    valid_count += 1
            except:
                pass
        
        return (valid_count / len(values) * 100) if values else 0
    
    def _calculate_consistency(self, values: List[Any]) -> float:
        """Calculate consistency score for values"""
        if not values:
            return 0.0
        
        # Check data type consistency
        types = set(type(v) for v in values)
        if len(types) > 1:
            return 50.0  # Mixed types indicate inconsistency
        
        # For strings, check format consistency
        if all(isinstance(v, str) for v in values):
            # Check case consistency
            cases = set()
            for v in values:
                if v.isupper():
                    cases.add("upper")
                elif v.islower():
                    cases.add("lower")
                else:
                    cases.add("mixed")
            
            if len(cases) == 1:
                return 100.0
            else:
                return 70.0
        
        return 90.0  # Default for consistent types
    
    def _calculate_quality_dimensions(self, attribute_scores: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Calculate overall quality dimensions from attribute scores"""
        dimensions = {
            "accuracy": [],
            "completeness": [],
            "consistency": [],
            "timeliness": [],
            "validity": []
        }
        
        for attr_data in attribute_scores.values():
            metrics = attr_data.get("metrics", {})
            dimensions["completeness"].append(metrics.get("completeness", 0))
            dimensions["validity"].append(metrics.get("validity", 0))
            dimensions["consistency"].append(metrics.get("consistency", 0))
            dimensions["accuracy"].append(metrics.get("accuracy", 0))
        
        # Calculate averages
        result = {}
        for dim, values in dimensions.items():
            if values:
                result[dim] = sum(values) / len(values)
            else:
                result[dim] = 0.0
        
        # Timeliness is estimated based on other factors
        result["timeliness"] = 85.0 if result["completeness"] > 70 else 60.0
        
        return result


class GapIdentifierTool(AsyncBaseDiscoveryTool):
    """Identifies gaps in critical attributes"""
    
    name: str = "gap_identifier"
    description: str = "Identify missing critical attributes and their impact"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        return ToolMetadata(
            name="gap_identifier",
            description="Identify missing critical attributes and their impact",
            tool_class=cls,
            categories=["gap_analysis", "gap_identification"],
            required_params=["attribute_mapping", "completeness_analysis"],
            optional_params=["business_context"],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(self, 
                  attribute_mapping: Dict[str, str], 
                  completeness_analysis: Dict[str, Any],
                  business_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Identify and categorize gaps in critical attributes"""
        try:
            self.log_with_context('info', "Identifying critical attribute gaps")
            
            gap_results = {
                "total_gaps": 0,
                "gaps_by_category": {
                    "infrastructure": [],
                    "application": [],
                    "operational": [],
                    "dependencies": []
                },
                "gaps_by_priority": {
                    "critical": [],
                    "high": [],
                    "medium": [],
                    "low": []
                },
                "business_impact_summary": {},
                "collection_difficulty": {}
            }
            
            # Define all critical attributes by category
            all_attributes = {
                "infrastructure": ["hostname", "environment", "os_type", "os_version", 
                                 "cpu_cores", "memory_gb", "storage_gb", "network_zone"],
                "application": ["application_name", "application_type", "technology_stack",
                              "criticality_level", "data_classification", "compliance_scope"],
                "operational": ["owner", "cost_center", "backup_strategy", "monitoring_status",
                              "patch_level", "last_scan_date"],
                "dependencies": ["application_dependencies", "database_dependencies",
                               "integration_points", "data_flows"]
            }
            
            # Identify gaps
            for category, attributes in all_attributes.items():
                for attribute in attributes:
                    if attribute not in attribute_mapping:
                        # This is a gap
                        gap_info = self._create_gap_info(
                            attribute, category, completeness_analysis, business_context
                        )
                        
                        gap_results["gaps_by_category"][category].append(gap_info)
                        gap_results["gaps_by_priority"][gap_info["priority"]].append(gap_info)
                        gap_results["total_gaps"] += 1
                    
                    elif attribute in completeness_analysis.get("attribute_completeness", {}):
                        # Check if mapped but has poor completeness
                        attr_completeness = completeness_analysis["attribute_completeness"][attribute]
                        if attr_completeness["completeness_percentage"] < 50:
                            gap_info = self._create_gap_info(
                                attribute, category, completeness_analysis, business_context,
                                partial=True, completeness=attr_completeness["completeness_percentage"]
                            )
                            
                            gap_results["gaps_by_category"][category].append(gap_info)
                            gap_results["gaps_by_priority"][gap_info["priority"]].append(gap_info)
                            gap_results["total_gaps"] += 1
            
            # Summarize business impact
            gap_results["business_impact_summary"] = self._summarize_business_impact(gap_results)
            
            # Assess collection difficulty
            gap_results["collection_difficulty"] = self._assess_collection_difficulty(gap_results)
            
            self.log_with_context(
                'info', 
                f"Identified {gap_results['total_gaps']} gaps "
                f"({len(gap_results['gaps_by_priority']['critical'])} critical)"
            )
            
            return gap_results
            
        except Exception as e:
            self.log_with_context('error', f"Error in gap identification: {e}")
            return {"error": str(e)}
    
    def _create_gap_info(self, attribute: str, category: str, 
                        completeness_analysis: Dict[str, Any],
                        business_context: Optional[Dict[str, Any]] = None,
                        partial: bool = False,
                        completeness: float = 0.0) -> Dict[str, Any]:
        """Create detailed gap information"""
        # Determine priority based on attribute importance
        priority_map = {
            # Critical attributes
            "hostname": "critical",
            "application_name": "critical",
            "owner": "critical",
            "environment": "critical",
            "technology_stack": "critical",
            
            # High priority
            "os_type": "high",
            "os_version": "high",
            "criticality_level": "high",
            "data_classification": "high",
            "application_dependencies": "high",
            
            # Medium priority
            "cpu_cores": "medium",
            "memory_gb": "medium",
            "storage_gb": "medium",
            "backup_strategy": "medium",
            "monitoring_status": "medium",
            
            # Low priority
            "patch_level": "low",
            "last_scan_date": "low",
            "cost_center": "low",
            "network_zone": "low"
        }
        
        # Determine collection difficulty
        difficulty_map = {
            # Easy to collect
            "hostname": "easy",
            "os_type": "easy",
            "os_version": "easy",
            "cpu_cores": "easy",
            "memory_gb": "easy",
            "storage_gb": "easy",
            
            # Medium difficulty
            "environment": "medium",
            "owner": "medium",
            "application_name": "medium",
            "backup_strategy": "medium",
            "monitoring_status": "medium",
            
            # Hard to collect
            "technology_stack": "hard",
            "application_dependencies": "hard",
            "database_dependencies": "hard",
            "integration_points": "hard",
            "data_flows": "hard",
            
            # Very hard
            "criticality_level": "hard",
            "data_classification": "hard",
            "compliance_scope": "very_hard"
        }
        
        gap_info = {
            "attribute": attribute,
            "category": category,
            "gap_type": "partial" if partial else "missing",
            "completeness": completeness if partial else 0.0,
            "priority": priority_map.get(attribute, "medium"),
            "collection_difficulty": difficulty_map.get(attribute, "medium"),
            "business_impact": self._determine_business_impact(attribute, category),
            "affects_strategies": self._determine_affected_strategies(attribute, category),
            "recommended_source": self._recommend_data_source(attribute),
            "automation_potential": difficulty_map.get(attribute) in ["easy", "medium"]
        }
        
        # Add context-specific information
        if business_context:
            if business_context.get("migration_timeline") == "urgent":
                if gap_info["priority"] == "medium":
                    gap_info["priority"] = "high"
            
            if business_context.get("compliance_required", False):
                if attribute in ["data_classification", "compliance_scope"]:
                    gap_info["priority"] = "critical"
        
        return gap_info
    
    def _determine_business_impact(self, attribute: str, category: str) -> str:
        """Determine business impact of missing attribute"""
        critical_impact = [
            "hostname", "application_name", "owner", "environment",
            "technology_stack", "application_dependencies"
        ]
        high_impact = [
            "os_type", "criticality_level", "data_classification",
            "database_dependencies", "integration_points"
        ]
        
        if attribute in critical_impact:
            return "critical"
        elif attribute in high_impact:
            return "high"
        elif category in ["infrastructure", "application"]:
            return "medium"
        else:
            return "low"
    
    def _determine_affected_strategies(self, attribute: str, category: str) -> List[str]:
        """Determine which 6R strategies are affected by this gap"""
        strategy_requirements = {
            "rehost": ["hostname", "os_type", "os_version", "cpu_cores", "memory_gb", 
                      "storage_gb", "network_zone", "environment"],
            "replatform": ["technology_stack", "os_type", "application_dependencies",
                          "database_dependencies", "integration_points"],
            "refactor": ["technology_stack", "application_type", "application_dependencies",
                        "database_dependencies", "data_flows", "criticality_level"],
            "repurchase": ["application_name", "application_type", "criticality_level",
                          "integration_points", "compliance_scope"],
            "retire": ["application_name", "criticality_level", "owner", 
                      "application_dependencies", "cost_center"],
            "retain": ["owner", "cost_center", "backup_strategy", "monitoring_status",
                      "patch_level", "criticality_level"]
        }
        
        affected = []
        for strategy, required_attrs in strategy_requirements.items():
            if attribute in required_attrs:
                affected.append(strategy)
        
        return affected if affected else ["general"]
    
    def _recommend_data_source(self, attribute: str) -> str:
        """Recommend data source for collecting attribute"""
        source_map = {
            # Automated sources
            "hostname": "discovery_tools",
            "os_type": "discovery_tools",
            "os_version": "discovery_tools",
            "cpu_cores": "discovery_tools",
            "memory_gb": "discovery_tools",
            "storage_gb": "discovery_tools",
            "network_zone": "network_scan",
            "monitoring_status": "monitoring_api",
            "last_scan_date": "discovery_logs",
            
            # Semi-automated sources
            "environment": "cmdb_import",
            "application_name": "cmdb_import",
            "backup_strategy": "backup_system",
            "patch_level": "patch_management",
            
            # Manual sources
            "owner": "stakeholder_input",
            "cost_center": "finance_team",
            "technology_stack": "technical_interview",
            "criticality_level": "business_assessment",
            "data_classification": "security_review",
            "compliance_scope": "compliance_team",
            "application_dependencies": "architecture_review",
            "database_dependencies": "dba_interview",
            "integration_points": "integration_mapping",
            "data_flows": "data_flow_analysis"
        }
        
        return source_map.get(attribute, "manual_collection")
    
    def _summarize_business_impact(self, gap_results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize overall business impact of gaps"""
        critical_count = len(gap_results["gaps_by_priority"]["critical"])
        high_count = len(gap_results["gaps_by_priority"]["high"])
        
        if critical_count >= 3:
            overall_impact = "severe"
            risk_level = "high"
            recommendation = "Address critical gaps immediately before proceeding with migration planning"
        elif critical_count >= 1 or high_count >= 3:
            overall_impact = "significant"
            risk_level = "medium-high"
            recommendation = "Prioritize critical and high-priority gaps in the next sprint"
        elif high_count >= 1:
            overall_impact = "moderate"
            risk_level = "medium"
            recommendation = "Plan gap resolution activities alongside migration assessment"
        else:
            overall_impact = "minor"
            risk_level = "low"
            recommendation = "Address gaps as part of normal migration discovery process"
        
        return {
            "overall_impact": overall_impact,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "critical_gaps": critical_count,
            "high_priority_gaps": high_count,
            "decision_readiness": "blocked" if critical_count > 0 else "proceed_with_caution"
        }
    
    def _assess_collection_difficulty(self, gap_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall collection difficulty"""
        difficulty_counts = {"easy": 0, "medium": 0, "hard": 0, "very_hard": 0}
        total_effort_hours = 0
        
        # Count difficulties and estimate effort
        for priority_gaps in gap_results["gaps_by_priority"].values():
            for gap in priority_gaps:
                difficulty = gap["collection_difficulty"]
                difficulty_counts[difficulty] += 1
                
                # Estimate hours
                effort_map = {"easy": 2, "medium": 8, "hard": 24, "very_hard": 40}
                total_effort_hours += effort_map.get(difficulty, 8)
        
        return {
            "difficulty_distribution": difficulty_counts,
            "estimated_total_effort_hours": total_effort_hours,
            "automated_collection_possible": difficulty_counts["easy"] + difficulty_counts["medium"],
            "manual_collection_required": difficulty_counts["hard"] + difficulty_counts["very_hard"],
            "recommended_approach": "hybrid" if difficulty_counts["easy"] > 0 and difficulty_counts["hard"] > 0 else "manual"
        }


class ImpactCalculatorTool(AsyncBaseDiscoveryTool):
    """Calculates business impact of data gaps"""
    
    name: str = "impact_calculator"
    description: str = "Calculate business and technical impact of missing critical attributes"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        return ToolMetadata(
            name="impact_calculator",
            description="Calculate business and technical impact of missing critical attributes",
            tool_class=cls,
            categories=["gap_analysis", "impact_analysis"],
            required_params=["gaps", "migration_context"],
            optional_params=[],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(self, gaps: List[Dict[str, Any]], migration_context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate impact of gaps on migration planning and execution"""
        try:
            self.log_with_context('info', f"Calculating impact for {len(gaps)} gaps")
            
            impact_results = {
                "migration_confidence_impact": {},
                "timeline_impact": {},
                "cost_impact": {},
                "risk_assessment": {},
                "strategy_viability": {},
                "recommendations": []
            }
            
            # Calculate confidence impact per strategy
            for strategy in ["rehost", "replatform", "refactor", "repurchase", "retire", "retain"]:
                impact_results["migration_confidence_impact"][strategy] = self._calculate_strategy_confidence(
                    gaps, strategy
                )
            
            # Calculate timeline impact
            impact_results["timeline_impact"] = self._calculate_timeline_impact(gaps, migration_context)
            
            # Calculate cost impact
            impact_results["cost_impact"] = self._calculate_cost_impact(gaps, migration_context)
            
            # Assess risks
            impact_results["risk_assessment"] = self._assess_migration_risks(gaps, migration_context)
            
            # Determine strategy viability
            impact_results["strategy_viability"] = self._assess_strategy_viability(
                impact_results["migration_confidence_impact"]
            )
            
            # Generate recommendations
            impact_results["recommendations"] = self._generate_impact_recommendations(impact_results)
            
            self.log_with_context('info', "Impact calculation completed")
            return impact_results
            
        except Exception as e:
            self.log_with_context('error', f"Error in impact calculation: {e}")
            return {"error": str(e)}
    
    def _calculate_strategy_confidence(self, gaps: List[Dict[str, Any]], strategy: str) -> Dict[str, Any]:
        """Calculate confidence impact for a specific migration strategy"""
        base_confidence = 100.0
        critical_gaps = 0
        high_gaps = 0
        
        for gap in gaps:
            if strategy in gap.get("affects_strategies", []):
                if gap["priority"] == "critical":
                    base_confidence -= 15
                    critical_gaps += 1
                elif gap["priority"] == "high":
                    base_confidence -= 10
                    high_gaps += 1
                elif gap["priority"] == "medium":
                    base_confidence -= 5
                else:
                    base_confidence -= 2
        
        return {
            "confidence_score": max(0, base_confidence),
            "critical_gaps_affecting": critical_gaps,
            "high_gaps_affecting": high_gaps,
            "recommendation_viable": base_confidence >= 60
        }
    
    def _calculate_timeline_impact(self, gaps: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate impact on migration timeline"""
        total_collection_hours = 0
        blocking_gaps = []
        
        effort_map = {
            "easy": 2,
            "medium": 8,
            "hard": 24,
            "very_hard": 40
        }
        
        for gap in gaps:
            hours = effort_map.get(gap.get("collection_difficulty", "medium"), 8)
            total_collection_hours += hours
            
            if gap["priority"] == "critical":
                blocking_gaps.append(gap["attribute"])
        
        # Calculate delay in weeks (assuming 40-hour work week, 2 people)
        estimated_delay_weeks = total_collection_hours / (40 * 2)
        
        return {
            "estimated_collection_hours": total_collection_hours,
            "estimated_delay_weeks": round(estimated_delay_weeks, 1),
            "blocking_gaps": blocking_gaps,
            "timeline_risk": "high" if blocking_gaps else "medium" if estimated_delay_weeks > 2 else "low",
            "mitigation": "Parallel collection activities recommended" if estimated_delay_weeks > 1 else "Standard process"
        }
    
    def _calculate_cost_impact(self, gaps: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate cost impact of gaps"""
        hourly_rate = context.get("hourly_rate", 150)  # Default hourly rate
        
        collection_hours = 0
        rework_risk_hours = 0
        
        for gap in gaps:
            # Collection cost
            effort_map = {"easy": 2, "medium": 8, "hard": 24, "very_hard": 40}
            collection_hours += effort_map.get(gap.get("collection_difficulty", "medium"), 8)
            
            # Risk of rework if gap not addressed
            if gap["priority"] in ["critical", "high"]:
                rework_risk_hours += 40  # Potential rework hours
        
        collection_cost = collection_hours * hourly_rate
        potential_rework_cost = rework_risk_hours * hourly_rate * 0.3  # 30% probability
        
        return {
            "data_collection_cost": collection_cost,
            "potential_rework_cost": potential_rework_cost,
            "total_cost_impact": collection_cost + potential_rework_cost,
            "roi_justification": "Investing in data collection reduces migration risks and rework",
            "cost_optimization": "Automate easy/medium difficulty collections to reduce costs"
        }
    
    def _assess_migration_risks(self, gaps: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess migration risks due to gaps"""
        risks = {
            "technical_risks": [],
            "business_risks": [],
            "compliance_risks": [],
            "operational_risks": []
        }
        
        for gap in gaps:
            if gap["attribute"] in ["technology_stack", "application_dependencies", "database_dependencies"]:
                risks["technical_risks"].append({
                    "risk": f"Unknown {gap['attribute']} may lead to incompatible migration approach",
                    "severity": "high" if gap["priority"] == "critical" else "medium"
                })
            
            if gap["attribute"] in ["criticality_level", "owner", "cost_center"]:
                risks["business_risks"].append({
                    "risk": f"Missing {gap['attribute']} affects business prioritization",
                    "severity": "medium"
                })
            
            if gap["attribute"] in ["data_classification", "compliance_scope"]:
                risks["compliance_risks"].append({
                    "risk": f"Unknown {gap['attribute']} may violate compliance requirements",
                    "severity": "high"
                })
            
            if gap["attribute"] in ["backup_strategy", "monitoring_status"]:
                risks["operational_risks"].append({
                    "risk": f"Missing {gap['attribute']} impacts operational continuity",
                    "severity": "medium"
                })
        
        # Overall risk level
        total_risks = sum(len(r) for r in risks.values())
        high_severity_risks = sum(1 for r_list in risks.values() for r in r_list if r.get("severity") == "high")
        
        overall_risk = "high" if high_severity_risks > 2 else "medium" if total_risks > 5 else "low"
        
        return {
            **risks,
            "total_risks_identified": total_risks,
            "high_severity_risks": high_severity_risks,
            "overall_risk_level": overall_risk,
            "risk_mitigation_priority": "Address compliance and technical risks first"
        }
    
    def _assess_strategy_viability(self, confidence_scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Assess viability of each migration strategy based on confidence"""
        viability = {}
        
        for strategy, scores in confidence_scores.items():
            confidence = scores["confidence_score"]
            
            if confidence >= 80:
                status = "recommended"
                action = "Proceed with confidence"
            elif confidence >= 60:
                status = "viable_with_gaps"
                action = "Address critical gaps before proceeding"
            elif confidence >= 40:
                status = "risky"
                action = "Significant gap closure required"
            else:
                status = "not_recommended"
                action = "Major data collection effort needed"
            
            viability[strategy] = {
                "status": status,
                "confidence": confidence,
                "action": action,
                "gaps_to_address": scores["critical_gaps_affecting"] + scores["high_gaps_affecting"]
            }
        
        # Identify best strategy
        best_strategy = max(confidence_scores.items(), key=lambda x: x[1]["confidence_score"])[0]
        
        return {
            "strategy_status": viability,
            "recommended_strategy": best_strategy,
            "alternative_strategies": [s for s, v in viability.items() 
                                     if v["status"] in ["recommended", "viable_with_gaps"] and s != best_strategy]
        }
    
    def _generate_impact_recommendations(self, impact_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on impact analysis"""
        recommendations = []
        
        # Timeline recommendations
        if impact_results["timeline_impact"]["timeline_risk"] == "high":
            recommendations.append(
                "URGENT: Address blocking gaps immediately to prevent migration delays. "
                "Consider dedicated gap resolution sprint."
            )
        
        # Cost recommendations
        if impact_results["cost_impact"]["total_cost_impact"] > 50000:
            recommendations.append(
                "Consider phased gap resolution to spread costs. "
                "Prioritize gaps affecting recommended migration strategy."
            )
        
        # Risk recommendations
        if impact_results["risk_assessment"]["overall_risk_level"] == "high":
            recommendations.append(
                "High risk profile detected. Implement risk mitigation plan "
                "focusing on compliance and technical gaps first."
            )
        
        # Strategy recommendations
        best_strategy = impact_results["strategy_viability"]["recommended_strategy"]
        if impact_results["migration_confidence_impact"][best_strategy]["confidence_score"] < 80:
            recommendations.append(
                f"Recommended strategy '{best_strategy}' has reduced confidence. "
                f"Focus gap resolution on attributes affecting this strategy."
            )
        
        return recommendations


class EffortEstimatorTool(AsyncBaseDiscoveryTool):
    """Estimates effort required for gap resolution"""
    
    name: str = "effort_estimator"
    description: str = "Estimate time and resources needed to collect missing attributes"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        return ToolMetadata(
            name="effort_estimator",
            description="Estimate time and resources needed to collect missing attributes",
            tool_class=cls,
            categories=["gap_analysis", "planning"],
            required_params=["gaps", "resources"],
            optional_params=[],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(self, gaps: List[Dict[str, Any]], resources: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate effort for collecting missing attributes"""
        try:
            self.log_with_context('info', f"Estimating effort for {len(gaps)} gaps")
            
            estimation_results = {
                "total_effort_hours": 0,
                "effort_by_priority": {},
                "effort_by_method": {},
                "resource_allocation": {},
                "timeline_estimate": {},
                "optimization_opportunities": []
            }
            
            # Base effort hours by difficulty
            effort_matrix = {
                "easy": {"collection": 1, "validation": 0.5, "documentation": 0.5},
                "medium": {"collection": 4, "validation": 2, "documentation": 2},
                "hard": {"collection": 16, "validation": 4, "documentation": 4},
                "very_hard": {"collection": 32, "validation": 8, "documentation": 8}
            }
            
            # Process each gap
            for gap in gaps:
                difficulty = gap.get("collection_difficulty", "medium")
                priority = gap.get("priority", "medium")
                
                # Calculate effort
                effort = effort_matrix.get(difficulty, effort_matrix["medium"])
                total_gap_effort = sum(effort.values())
                
                # Adjust for priority
                if priority == "critical":
                    total_gap_effort *= 1.2  # Add overhead for critical items
                
                # Track by priority
                if priority not in estimation_results["effort_by_priority"]:
                    estimation_results["effort_by_priority"][priority] = 0
                estimation_results["effort_by_priority"][priority] += total_gap_effort
                
                # Track by collection method
                method = gap.get("recommended_source", "manual_collection")
                if method not in estimation_results["effort_by_method"]:
                    estimation_results["effort_by_method"][method] = 0
                estimation_results["effort_by_method"][method] += total_gap_effort
                
                estimation_results["total_effort_hours"] += total_gap_effort
            
            # Calculate resource allocation
            estimation_results["resource_allocation"] = self._calculate_resource_allocation(
                gaps, resources, estimation_results["total_effort_hours"]
            )
            
            # Estimate timeline
            estimation_results["timeline_estimate"] = self._estimate_timeline(
                estimation_results["total_effort_hours"],
                resources
            )
            
            # Identify optimization opportunities
            estimation_results["optimization_opportunities"] = self._identify_optimizations(gaps)
            
            self.log_with_context(
                'info', 
                f"Total effort estimated: {estimation_results['total_effort_hours']:.1f} hours"
            )
            
            return estimation_results
            
        except Exception as e:
            self.log_with_context('error', f"Error in effort estimation: {e}")
            return {"error": str(e)}
    
    def _calculate_resource_allocation(self, gaps: List[Dict[str, Any]], 
                                     resources: Dict[str, Any], 
                                     total_hours: float) -> Dict[str, Any]:
        """Calculate optimal resource allocation"""
        available_resources = resources.get("available_team_members", 2)
        hours_per_week = resources.get("hours_per_week", 40)
        
        # Categorize work by skill requirement
        skill_requirements = {
            "technical": 0,
            "business": 0,
            "data_analyst": 0,
            "stakeholder_coordination": 0
        }
        
        for gap in gaps:
            category = gap.get("category", "unknown")
            if category == "infrastructure":
                skill_requirements["technical"] += 1
            elif category == "application":
                skill_requirements["technical"] += 0.5
                skill_requirements["business"] += 0.5
            elif category == "operational":
                skill_requirements["business"] += 0.7
                skill_requirements["stakeholder_coordination"] += 0.3
            else:  # dependencies
                skill_requirements["data_analyst"] += 0.6
                skill_requirements["technical"] += 0.4
        
        # Normalize to percentages
        total_work = sum(skill_requirements.values())
        if total_work > 0:
            for skill in skill_requirements:
                skill_requirements[skill] = (skill_requirements[skill] / total_work) * 100
        
        return {
            "recommended_team_composition": skill_requirements,
            "minimum_team_size": max(2, len([s for s in skill_requirements.values() if s > 20])),
            "optimal_team_size": min(available_resources, 4),
            "parallel_work_possible": total_hours > 80,
            "skill_gaps": [skill for skill, pct in skill_requirements.items() if pct > 30]
        }
    
    def _estimate_timeline(self, total_hours: float, resources: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate project timeline"""
        team_size = resources.get("available_team_members", 2)
        hours_per_week = resources.get("hours_per_week", 40)
        efficiency_factor = resources.get("efficiency_factor", 0.7)  # Account for meetings, overhead
        
        effective_hours_per_week = team_size * hours_per_week * efficiency_factor
        weeks_required = total_hours / effective_hours_per_week
        
        # Add buffer for dependencies and unknowns
        buffer_factor = 1.2 if total_hours > 200 else 1.1
        weeks_with_buffer = weeks_required * buffer_factor
        
        return {
            "estimated_weeks": round(weeks_required, 1),
            "weeks_with_buffer": round(weeks_with_buffer, 1),
            "estimated_completion_date": f"In {round(weeks_with_buffer, 1)} weeks",
            "confidence_level": "medium" if total_hours < 200 else "low",
            "critical_path_items": "Focus on critical priority gaps first",
            "parallelization_savings": f"{round((1 - 1/team_size) * 100)}% with {team_size} team members"
        }
    
    def _identify_optimizations(self, gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify optimization opportunities"""
        optimizations = []
        
        # Group by collection method
        method_groups = {}
        for gap in gaps:
            method = gap.get("recommended_source", "manual")
            if method not in method_groups:
                method_groups[method] = []
            method_groups[method].append(gap)
        
        # Batch collection opportunities
        for method, method_gaps in method_groups.items():
            if len(method_gaps) > 3:
                optimizations.append({
                    "type": "batch_collection",
                    "method": method,
                    "gap_count": len(method_gaps),
                    "potential_savings": f"{len(method_gaps) * 10}% time reduction",
                    "implementation": f"Collect all {method} data in single effort"
                })
        
        # Automation opportunities
        easy_gaps = [g for g in gaps if g.get("collection_difficulty") == "easy"]
        if easy_gaps:
            optimizations.append({
                "type": "automation",
                "gap_count": len(easy_gaps),
                "potential_savings": f"{len(easy_gaps) * 2} hours",
                "implementation": "Deploy discovery tools for infrastructure attributes"
            })
        
        # Template opportunities
        similar_gaps = [g for g in gaps if g.get("category") == "operational"]
        if len(similar_gaps) > 5:
            optimizations.append({
                "type": "standardization",
                "gap_count": len(similar_gaps),
                "potential_savings": "30% reduction in collection time",
                "implementation": "Create standardized collection templates"
            })
        
        return optimizations


class PriorityRankerTool(AsyncBaseDiscoveryTool):
    """Ranks gaps by business priority"""
    
    name: str = "priority_ranker"
    description: str = "Rank and prioritize gaps based on business impact and collection feasibility"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        return ToolMetadata(
            name="priority_ranker",
            description="Rank and prioritize gaps based on business impact and collection feasibility",
            tool_class=cls,
            categories=["gap_analysis", "prioritization"],
            required_params=["gaps", "ranking_criteria"],
            optional_params=[],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(self, gaps: List[Dict[str, Any]], ranking_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Rank gaps using multi-criteria decision analysis"""
        try:
            self.log_with_context('info', f"Ranking {len(gaps)} gaps")
            
            ranking_results = {
                "ranked_gaps": [],
                "ranking_methodology": "multi_criteria_weighted_scoring",
                "criteria_weights": {},
                "priority_groups": {
                    "immediate_action": [],
                    "next_sprint": [],
                    "backlog": [],
                    "nice_to_have": []
                }
            }
            
            # Define criteria weights
            weights = ranking_criteria.get("weights", {
                "business_impact": 0.35,
                "strategy_alignment": 0.25,
                "collection_feasibility": 0.20,
                "cost_benefit": 0.20
            })
            ranking_results["criteria_weights"] = weights
            
            # Score each gap
            scored_gaps = []
            for gap in gaps:
                scores = {
                    "business_impact": self._score_business_impact(gap),
                    "strategy_alignment": self._score_strategy_alignment(gap, ranking_criteria),
                    "collection_feasibility": self._score_feasibility(gap),
                    "cost_benefit": self._score_cost_benefit(gap)
                }
                
                # Calculate weighted score
                total_score = sum(scores[criteria] * weights[criteria] 
                                for criteria in scores)
                
                gap["priority_score"] = round(total_score, 2)
                gap["score_breakdown"] = scores
                scored_gaps.append(gap)
            
            # Sort by priority score
            scored_gaps.sort(key=lambda x: x["priority_score"], reverse=True)
            ranking_results["ranked_gaps"] = scored_gaps
            
            # Group into priority buckets
            for i, gap in enumerate(scored_gaps):
                if gap["priority_score"] >= 80 or gap.get("priority") == "critical":
                    ranking_results["priority_groups"]["immediate_action"].append(gap)
                elif gap["priority_score"] >= 60 or i < len(gaps) * 0.3:
                    ranking_results["priority_groups"]["next_sprint"].append(gap)
                elif gap["priority_score"] >= 40 or i < len(gaps) * 0.6:
                    ranking_results["priority_groups"]["backlog"].append(gap)
                else:
                    ranking_results["priority_groups"]["nice_to_have"].append(gap)
            
            self.log_with_context('info', "Gap ranking completed")
            return ranking_results
            
        except Exception as e:
            self.log_with_context('error', f"Error in priority ranking: {e}")
            return {"error": str(e)}
    
    def _score_business_impact(self, gap: Dict[str, Any]) -> float:
        """Score business impact (0-100)"""
        impact_level = gap.get("business_impact", "medium")
        priority = gap.get("priority", "medium")
        
        base_scores = {
            "critical": 100,
            "high": 80,
            "medium": 50,
            "low": 20
        }
        
        score = base_scores.get(impact_level, 50)
        
        # Adjust for priority
        if priority == "critical":
            score = min(100, score * 1.2)
        
        # Adjust for specific impacts
        if gap.get("blocks_decision", False):
            score = min(100, score + 20)
        if gap.get("impacts_timeline", False):
            score = min(100, score + 10)
        
        return score
    
    def _score_strategy_alignment(self, gap: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Score alignment with migration strategy (0-100)"""
        primary_strategy = criteria.get("primary_strategy", "rehost")
        affected_strategies = gap.get("affects_strategies", [])
        
        if primary_strategy in affected_strategies:
            return 100
        elif len(affected_strategies) > 3:
            return 80
        elif len(affected_strategies) > 1:
            return 60
        elif affected_strategies:
            return 40
        else:
            return 20
    
    def _score_feasibility(self, gap: Dict[str, Any]) -> float:
        """Score collection feasibility (0-100, higher is easier)"""
        difficulty = gap.get("collection_difficulty", "medium")
        
        feasibility_scores = {
            "easy": 100,
            "medium": 70,
            "hard": 40,
            "very_hard": 20
        }
        
        score = feasibility_scores.get(difficulty, 50)
        
        # Adjust for automation potential
        if gap.get("automation_potential", False):
            score = min(100, score * 1.2)
        
        return score
    
    def _score_cost_benefit(self, gap: Dict[str, Any]) -> float:
        """Score cost-benefit ratio (0-100)"""
        # Estimate based on impact vs effort
        impact = self._score_business_impact(gap)
        feasibility = self._score_feasibility(gap)
        
        # High impact + high feasibility = best cost-benefit
        # Low impact + low feasibility = worst cost-benefit
        cost_benefit = (impact * 0.6 + feasibility * 0.4)
        
        return cost_benefit


class CollectionPlannerTool(AsyncBaseDiscoveryTool):
    """Plans optimal collection strategy for gaps"""
    
    name: str = "collection_planner"
    description: str = "Create detailed collection plans for prioritized gaps"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        return ToolMetadata(
            name="collection_planner",
            description="Create detailed collection plans for prioritized gaps",
            tool_class=cls,
            categories=["gap_analysis", "planning"],
            required_params=["prioritized_gaps", "resources"],
            optional_params=["constraints"],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(self, 
                  prioritized_gaps: List[Dict[str, Any]], 
                  resources: Dict[str, Any],
                  constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create comprehensive collection plan"""
        try:
            self.log_with_context('info', "Creating collection plan")
            
            collection_plan = {
                "plan_summary": {},
                "phases": [],
                "resource_schedule": {},
                "collection_methods": {},
                "success_metrics": [],
                "risk_mitigation": []
            }
            
            # Group gaps by priority
            immediate_gaps = [g for g in prioritized_gaps if g.get("priority_score", 0) >= 80]
            next_sprint_gaps = [g for g in prioritized_gaps if 60 <= g.get("priority_score", 0) < 80]
            backlog_gaps = [g for g in prioritized_gaps if g.get("priority_score", 0) < 60]
            
            # Create phases
            if immediate_gaps:
                phase1 = self._create_collection_phase(
                    "Phase 1: Critical Gap Resolution",
                    immediate_gaps,
                    resources,
                    duration_weeks=1
                )
                collection_plan["phases"].append(phase1)
            
            if next_sprint_gaps:
                phase2 = self._create_collection_phase(
                    "Phase 2: High Priority Collection",
                    next_sprint_gaps,
                    resources,
                    duration_weeks=2
                )
                collection_plan["phases"].append(phase2)
            
            if backlog_gaps and not constraints.get("critical_only", False):
                phase3 = self._create_collection_phase(
                    "Phase 3: Comprehensive Coverage",
                    backlog_gaps,
                    resources,
                    duration_weeks=3
                )
                collection_plan["phases"].append(phase3)
            
            # Create resource schedule
            collection_plan["resource_schedule"] = self._create_resource_schedule(
                collection_plan["phases"], resources
            )
            
            # Define collection methods
            collection_plan["collection_methods"] = self._define_collection_methods(prioritized_gaps)
            
            # Set success metrics
            collection_plan["success_metrics"] = [
                "Achieve 100% coverage of critical attributes",
                "Improve overall attribute coverage to >85%",
                "Complete Phase 1 within 1 week",
                "Maintain data quality score >80%",
                "Zero blocking gaps for migration planning"
            ]
            
            # Risk mitigation
            collection_plan["risk_mitigation"] = self._identify_risks_and_mitigations(
                prioritized_gaps, resources
            )
            
            # Summary
            total_gaps = len(prioritized_gaps)
            total_effort = sum(p["estimated_effort"] for p in collection_plan["phases"])
            
            collection_plan["plan_summary"] = {
                "total_gaps_to_address": total_gaps,
                "phases_count": len(collection_plan["phases"]),
                "total_effort_hours": total_effort,
                "estimated_duration_weeks": sum(p["duration_weeks"] for p in collection_plan["phases"]),
                "critical_gaps_in_phase1": len(immediate_gaps),
                "automation_percentage": self._calculate_automation_percentage(prioritized_gaps)
            }
            
            self.log_with_context('info', "Collection plan created successfully")
            return collection_plan
            
        except Exception as e:
            self.log_with_context('error', f"Error in collection planning: {e}")
            return {"error": str(e)}
    
    def _create_collection_phase(self, name: str, gaps: List[Dict[str, Any]], 
                                resources: Dict[str, Any], duration_weeks: int) -> Dict[str, Any]:
        """Create a collection phase"""
        phase = {
            "name": name,
            "duration_weeks": duration_weeks,
            "gaps_count": len(gaps),
            "activities": [],
            "deliverables": [],
            "estimated_effort": 0
        }
        
        # Group gaps by collection method
        method_groups = {}
        for gap in gaps:
            method = gap.get("recommended_source", "manual_collection")
            if method not in method_groups:
                method_groups[method] = []
            method_groups[method].append(gap)
        
        # Create activities
        for method, method_gaps in method_groups.items():
            activity = {
                "name": f"Collect via {method}",
                "method": method,
                "attributes": [g["attribute"] for g in method_gaps],
                "effort_hours": sum(self._estimate_gap_effort(g) for g in method_gaps),
                "assigned_resources": self._assign_resources(method, resources),
                "tools_required": self._identify_required_tools(method)
            }
            phase["activities"].append(activity)
            phase["estimated_effort"] += activity["effort_hours"]
        
        # Define deliverables
        phase["deliverables"] = [
            f"Complete data for {len(gaps)} attributes",
            f"Data quality validation report",
            f"Updated CMDB with collected data",
            f"Gap closure confirmation"
        ]
        
        return phase
    
    def _create_resource_schedule(self, phases: List[Dict[str, Any]], 
                                resources: Dict[str, Any]) -> Dict[str, Any]:
        """Create resource allocation schedule"""
        schedule = {
            "team_allocation": {},
            "weekly_schedule": [],
            "resource_utilization": {}
        }
        
        team_members = resources.get("team_members", ["Analyst1", "Analyst2"])
        week_counter = 1
        
        for phase in phases:
            for week in range(phase["duration_weeks"]):
                weekly_plan = {
                    "week": week_counter,
                    "phase": phase["name"],
                    "assignments": {}
                }
                
                # Distribute activities across team
                for i, activity in enumerate(phase["activities"]):
                    assigned_to = team_members[i % len(team_members)]
                    if assigned_to not in weekly_plan["assignments"]:
                        weekly_plan["assignments"][assigned_to] = []
                    weekly_plan["assignments"][assigned_to].append(activity["name"])
                
                schedule["weekly_schedule"].append(weekly_plan)
                week_counter += 1
        
        # Calculate utilization
        for member in team_members:
            total_hours = sum(
                sum(a["effort_hours"] for a in p["activities"]) / len(team_members)
                for p in phases
            )
            schedule["resource_utilization"][member] = {
                "total_hours": total_hours,
                "average_hours_per_week": total_hours / max(1, week_counter - 1)
            }
        
        return schedule
    
    def _define_collection_methods(self, gaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Define collection methods and procedures"""
        methods = {}
        
        method_definitions = {
            "discovery_tools": {
                "description": "Automated discovery using scanning tools",
                "tools": ["Network scanner", "Asset discovery agent"],
                "procedure": "1. Deploy discovery agents\n2. Run network scan\n3. Validate results\n4. Import to CMDB"
            },
            "cmdb_import": {
                "description": "Import from existing CMDB or inventory systems",
                "tools": ["CMDB connector", "Data import wizard"],
                "procedure": "1. Connect to source CMDB\n2. Map fields\n3. Extract data\n4. Transform and load"
            },
            "stakeholder_input": {
                "description": "Collect via stakeholder interviews and surveys",
                "tools": ["Survey platform", "Interview templates"],
                "procedure": "1. Schedule stakeholder sessions\n2. Conduct interviews\n3. Validate responses\n4. Document findings"
            },
            "technical_interview": {
                "description": "Technical deep-dive sessions with SMEs",
                "tools": ["Technical questionnaire", "Architecture templates"],
                "procedure": "1. Identify SMEs\n2. Prepare technical questions\n3. Conduct sessions\n4. Document architecture"
            }
        }
        
        # Include only methods needed for the gaps
        used_methods = set(g.get("recommended_source", "manual_collection") for g in gaps)
        for method in used_methods:
            if method in method_definitions:
                methods[method] = method_definitions[method]
            else:
                methods[method] = {
                    "description": f"Custom collection method: {method}",
                    "tools": ["Manual forms", "Spreadsheet templates"],
                    "procedure": "1. Create collection template\n2. Gather data\n3. Validate\n4. Import"
                }
        
        return methods
    
    def _identify_risks_and_mitigations(self, gaps: List[Dict[str, Any]], 
                                       resources: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify collection risks and mitigations"""
        risks = []
        
        # Resource risks
        if resources.get("available_team_members", 2) < 3:
            risks.append({
                "risk": "Limited team capacity may delay collection",
                "impact": "medium",
                "mitigation": "Prioritize critical gaps and consider automation"
            })
        
        # Complexity risks
        hard_gaps = [g for g in gaps if g.get("collection_difficulty") in ["hard", "very_hard"]]
        if len(hard_gaps) > 5:
            risks.append({
                "risk": "High number of complex attributes to collect",
                "impact": "high",
                "mitigation": "Engage subject matter experts early and plan extra time"
            })
        
        # Stakeholder risks
        stakeholder_gaps = [g for g in gaps if "stakeholder" in g.get("recommended_source", "")]
        if stakeholder_gaps:
            risks.append({
                "risk": "Stakeholder availability may impact collection timeline",
                "impact": "medium",
                "mitigation": "Schedule sessions early and have backup contacts"
            })
        
        # Data quality risks
        risks.append({
            "risk": "Collected data may not meet quality standards",
            "impact": "medium",
            "mitigation": "Implement validation checkpoints and quality reviews"
        })
        
        return risks
    
    def _estimate_gap_effort(self, gap: Dict[str, Any]) -> float:
        """Estimate effort for a single gap"""
        base_effort = {
            "easy": 2,
            "medium": 8,
            "hard": 24,
            "very_hard": 40
        }
        
        difficulty = gap.get("collection_difficulty", "medium")
        return base_effort.get(difficulty, 8)
    
    def _assign_resources(self, method: str, resources: Dict[str, Any]) -> List[str]:
        """Assign appropriate resources for collection method"""
        skill_map = {
            "discovery_tools": ["technical_analyst"],
            "cmdb_import": ["data_analyst"],
            "stakeholder_input": ["business_analyst"],
            "technical_interview": ["solution_architect", "technical_analyst"],
            "manual_collection": ["data_analyst", "business_analyst"]
        }
        
        return skill_map.get(method, ["analyst"])
    
    def _identify_required_tools(self, method: str) -> List[str]:
        """Identify tools required for collection method"""
        tool_map = {
            "discovery_tools": ["ServiceNow Discovery", "Lansweeper", "Device42"],
            "cmdb_import": ["ETL tool", "Data mapping tool", "CMDB API"],
            "stakeholder_input": ["Survey tool", "Forms platform", "Interview guides"],
            "technical_interview": ["Architecture tools", "Diagramming software"],
            "manual_collection": ["Spreadsheet templates", "Data entry forms"]
        }
        
        return tool_map.get(method, ["Manual templates"])
    
    def _calculate_automation_percentage(self, gaps: List[Dict[str, Any]]) -> float:
        """Calculate percentage of gaps that can be automated"""
        automated_sources = ["discovery_tools", "cmdb_import", "monitoring_api", "cloud_api"]
        automated_gaps = [g for g in gaps if g.get("recommended_source") in automated_sources]
        
        if not gaps:
            return 0.0
        
        return (len(automated_gaps) / len(gaps)) * 100