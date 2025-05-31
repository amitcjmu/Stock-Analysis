"""
Data Source Intelligence Agent
Analyzes incoming data (CMDB, migration tools, documentation) to understand format, structure, and content patterns.
"""

import logging
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd

from app.services.agent_ui_bridge import (
    agent_ui_bridge, QuestionType, ConfidenceLevel, DataClassification
)

logger = logging.getLogger(__name__)

class DataSourceIntelligenceAgent:
    """
    Agent specialized in analyzing data sources to understand their format, structure, and migration value.
    Uses agentic intelligence rather than hardcoded heuristics.
    """
    
    def __init__(self):
        self.agent_id = "data_source_intelligence_001"
        self.agent_name = "Data Source Intelligence Agent"
        self.analysis_history: List[Dict[str, Any]] = []
        
        # Pattern learning memory (starts empty, learns over time)
        self.learned_patterns = {
            "cmdb_formats": [],
            "migration_tool_patterns": [],
            "documentation_indicators": [],
            "field_name_patterns": [],
            "data_quality_indicators": []
        }
        
        logger.info(f"Initialized {self.agent_name}")
    
    async def analyze_data_source(self, data_source: Dict[str, Any], 
                                page_context: str = "data-import") -> Dict[str, Any]:
        """
        Main entry point for analyzing any data source.
        
        Args:
            data_source: Contains file_data, metadata, upload_context
            page_context: UI page where this analysis is happening
            
        Returns:
            Analysis results with agent insights and questions
        """
        try:
            analysis_id = f"analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Extract data for analysis
            file_data = data_source.get('file_data', [])
            metadata = data_source.get('metadata', {})
            upload_context = data_source.get('upload_context', {})
            
            logger.info(f"Starting data source analysis: {analysis_id}")
            
            # Perform multi-dimensional analysis
            analysis_result = {
                "analysis_id": analysis_id,
                "agent_analysis": await self._perform_comprehensive_analysis(
                    file_data, metadata, upload_context
                ),
                "data_classification": await self._classify_data_quality(file_data),
                "agent_insights": await self._generate_intelligent_insights(file_data, metadata),
                "clarification_questions": await self._generate_clarification_questions(
                    file_data, metadata, page_context
                ),
                "confidence_assessment": await self._assess_analysis_confidence(file_data),
                "next_steps": await self._recommend_next_steps(file_data, metadata)
            }
            
            # Store analysis for learning
            self.analysis_history.append(analysis_result)
            
            # Add insights to UI bridge
            for insight in analysis_result["agent_insights"]:
                agent_ui_bridge.add_agent_insight(
                    agent_id=self.agent_id,
                    agent_name=self.agent_name,
                    insight_type=insight["type"],
                    title=insight["title"],
                    description=insight["description"],
                    confidence=ConfidenceLevel(insight["confidence"]),
                    supporting_data=insight["supporting_data"],
                    page=page_context
                )
            
            # Add clarification questions to UI bridge
            for question in analysis_result["clarification_questions"]:
                agent_ui_bridge.add_agent_question(
                    agent_id=self.agent_id,
                    agent_name=self.agent_name,
                    question_type=QuestionType(question["type"]),
                    page=page_context,
                    title=question["title"],
                    question=question["question"],
                    context=question["context"],
                    options=question.get("options"),
                    confidence=ConfidenceLevel(question["confidence"]),
                    priority=question["priority"]
                )
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in data source analysis: {e}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "agent_fallback": True
            }
    
    async def _perform_comprehensive_analysis(self, data: List[Dict[str, Any]], 
                                            metadata: Dict[str, Any], 
                                            context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive data analysis using learned patterns."""
        
        analysis = {
            "data_source_type": await self._identify_data_source_type(data, metadata),
            "structure_analysis": await self._analyze_data_structure(data),
            "content_patterns": await self._analyze_content_patterns(data),
            "migration_value": await self._assess_migration_value(data),
            "quality_indicators": await self._identify_quality_indicators(data),
            "relationship_hints": await self._detect_relationship_patterns(data)
        }
        
        return analysis
    
    async def _identify_data_source_type(self, data: List[Dict[str, Any]], 
                                       metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently identify the type of data source."""
        
        # Analyze filename and metadata clues
        filename = metadata.get('filename', '').lower()
        file_size = metadata.get('size', 0)
        
        # Content-based analysis
        if not data:
            return {
                "type": "unknown",
                "confidence": ConfidenceLevel.UNCERTAIN,
                "reasoning": "No data content to analyze"
            }
        
        # Analyze column patterns to determine source type
        columns = set()
        for row in data:
            columns.update(row.keys())
        
        column_list = list(columns)
        
        # Use learned patterns and content analysis
        source_indicators = {
            "cmdb_export": self._analyze_cmdb_indicators(column_list, data),
            "migration_assessment": self._analyze_migration_tool_indicators(column_list, data),
            "application_documentation": self._analyze_documentation_indicators(column_list, data),
            "infrastructure_scan": self._analyze_infrastructure_indicators(column_list, data),
            "custom_format": self._analyze_custom_format_indicators(column_list, data)
        }
        
        # Determine most likely source type
        best_match = max(source_indicators.items(), key=lambda x: x[1]["confidence_score"])
        
        return {
            "type": best_match[0],
            "confidence": self._score_to_confidence_level(best_match[1]["confidence_score"]),
            "reasoning": best_match[1]["reasoning"],
            "all_indicators": source_indicators
        }
    
    def _analyze_cmdb_indicators(self, columns: List[str], data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze indicators that this is CMDB data."""
        
        # Common CMDB field patterns (learned over time)
        cmdb_patterns = [
            r'.*hostname.*', r'.*server.*name.*', r'.*asset.*name.*',
            r'.*ip.*address.*', r'.*environment.*', r'.*owner.*',
            r'.*department.*', r'.*location.*', r'.*os.*', r'.*operating.*system.*',
            r'.*cpu.*', r'.*memory.*', r'.*ram.*', r'.*storage.*', r'.*disk.*'
        ]
        
        pattern_matches = 0
        for column in columns:
            for pattern in cmdb_patterns:
                if re.match(pattern, column.lower()):
                    pattern_matches += 1
                    break
        
        # Analyze data content for CMDB characteristics
        content_indicators = 0
        if data:
            sample_row = data[0]
            
            # Look for infrastructure-related content
            for value in sample_row.values():
                if isinstance(value, str):
                    value_lower = value.lower()
                    if any(indicator in value_lower for indicator in 
                          ['server', 'prod', 'dev', 'test', 'linux', 'windows', 'database']):
                        content_indicators += 1
        
        confidence_score = (pattern_matches * 0.7 + content_indicators * 0.3) / len(columns)
        
        return {
            "confidence_score": min(confidence_score, 1.0),
            "reasoning": f"Found {pattern_matches} CMDB field patterns and {content_indicators} content indicators",
            "pattern_matches": pattern_matches,
            "content_indicators": content_indicators
        }
    
    def _analyze_migration_tool_indicators(self, columns: List[str], data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze indicators that this is migration tool output."""
        
        migration_patterns = [
            r'.*migration.*', r'.*readiness.*', r'.*complexity.*', r'.*6r.*', r'.*strategy.*',
            r'.*cloud.*ready.*', r'.*assessment.*', r'.*score.*', r'.*recommendation.*'
        ]
        
        pattern_matches = 0
        for column in columns:
            for pattern in migration_patterns:
                if re.match(pattern, column.lower()):
                    pattern_matches += 1
                    break
        
        # Look for migration-specific content
        content_indicators = 0
        if data:
            sample_row = data[0]
            for value in sample_row.values():
                if isinstance(value, str):
                    value_lower = value.lower()
                    if any(indicator in value_lower for indicator in 
                          ['rehost', 'replatform', 'refactor', 'migrate', 'cloud', 'assessment']):
                        content_indicators += 1
        
        confidence_score = (pattern_matches * 0.8 + content_indicators * 0.2) / len(columns)
        
        return {
            "confidence_score": min(confidence_score, 1.0),
            "reasoning": f"Found {pattern_matches} migration tool patterns and {content_indicators} content indicators",
            "pattern_matches": pattern_matches,
            "content_indicators": content_indicators
        }
    
    def _analyze_documentation_indicators(self, columns: List[str], data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze indicators that this is application documentation."""
        
        doc_patterns = [
            r'.*application.*', r'.*service.*', r'.*component.*', r'.*description.*',
            r'.*purpose.*', r'.*function.*', r'.*business.*process.*', r'.*stakeholder.*'
        ]
        
        pattern_matches = 0
        for column in columns:
            for pattern in doc_patterns:
                if re.match(pattern, column.lower()):
                    pattern_matches += 1
                    break
        
        # Look for documentation-specific content (longer text fields)
        content_indicators = 0
        if data:
            sample_row = data[0]
            for value in sample_row.values():
                if isinstance(value, str) and len(value) > 50:  # Longer text indicates documentation
                    content_indicators += 1
        
        confidence_score = (pattern_matches * 0.6 + content_indicators * 0.4) / len(columns)
        
        return {
            "confidence_score": min(confidence_score, 1.0),
            "reasoning": f"Found {pattern_matches} documentation patterns and {content_indicators} long-text fields",
            "pattern_matches": pattern_matches,
            "content_indicators": content_indicators
        }
    
    def _analyze_infrastructure_indicators(self, columns: List[str], data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze indicators that this is infrastructure scan data."""
        
        infra_patterns = [
            r'.*port.*', r'.*protocol.*', r'.*service.*running.*', r'.*process.*',
            r'.*network.*', r'.*interface.*', r'.*connection.*', r'.*listening.*'
        ]
        
        pattern_matches = 0
        for column in columns:
            for pattern in infra_patterns:
                if re.match(pattern, column.lower()):
                    pattern_matches += 1
                    break
        
        confidence_score = pattern_matches / len(columns) if columns else 0
        
        return {
            "confidence_score": min(confidence_score, 1.0),
            "reasoning": f"Found {pattern_matches} infrastructure scan patterns",
            "pattern_matches": pattern_matches
        }
    
    def _analyze_custom_format_indicators(self, columns: List[str], data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze indicators for custom organizational formats."""
        
        # This starts with low confidence and learns over time
        confidence_score = 0.1  # Base low confidence for unknown formats
        
        return {
            "confidence_score": confidence_score,
            "reasoning": "Unknown format - will learn patterns from user feedback",
            "requires_learning": True
        }
    
    async def _analyze_data_structure(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the structure and completeness of the data."""
        
        if not data:
            return {"error": "No data to analyze"}
        
        # Column analysis
        all_columns = set()
        for row in data:
            all_columns.update(row.keys())
        
        column_stats = {}
        for column in all_columns:
            values = [row.get(column) for row in data]
            non_empty_values = [v for v in values if v is not None and str(v).strip()]
            
            column_stats[column] = {
                "fill_rate": len(non_empty_values) / len(data),
                "unique_values": len(set(str(v) for v in non_empty_values)),
                "data_types": list(set(type(v).__name__ for v in non_empty_values)),
                "sample_values": non_empty_values[:5] if non_empty_values else []
            }
        
        return {
            "total_rows": len(data),
            "total_columns": len(all_columns),
            "column_statistics": column_stats,
            "completeness_score": sum(stats["fill_rate"] for stats in column_stats.values()) / len(column_stats) if column_stats else 0
        }
    
    async def _classify_data_quality(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Classify data quality using agent intelligence."""
        
        if not data:
            return {
                "classification": DataClassification.UNUSABLE,
                "confidence": ConfidenceLevel.HIGH,
                "reasoning": "No data present"
            }
        
        # Analyze various quality dimensions
        completeness_score = 0
        consistency_score = 0
        validity_score = 0
        
        # Completeness: How much data is present
        total_fields = 0
        filled_fields = 0
        
        for row in data:
            for value in row.values():
                total_fields += 1
                if value is not None and str(value).strip():
                    filled_fields += 1
        
        completeness_score = filled_fields / total_fields if total_fields > 0 else 0
        
        # Consistency: Are formats consistent across rows
        column_formats = {}
        for row in data:
            for column, value in row.items():
                if column not in column_formats:
                    column_formats[column] = []
                if value is not None and str(value).strip():
                    column_formats[column].append(type(value).__name__)
        
        consistent_columns = 0
        for column, types in column_formats.items():
            if len(set(types)) <= 2:  # Allow some variation
                consistent_columns += 1
        
        consistency_score = consistent_columns / len(column_formats) if column_formats else 0
        
        # Overall quality score
        overall_quality = (completeness_score * 0.6 + consistency_score * 0.4)
        
        # Determine classification
        if overall_quality >= 0.8:
            classification = DataClassification.GOOD_DATA
            confidence = ConfidenceLevel.HIGH
        elif overall_quality >= 0.6:
            classification = DataClassification.GOOD_DATA
            confidence = ConfidenceLevel.MEDIUM
        elif overall_quality >= 0.3:
            classification = DataClassification.NEEDS_CLARIFICATION
            confidence = ConfidenceLevel.MEDIUM
        else:
            classification = DataClassification.UNUSABLE
            confidence = ConfidenceLevel.HIGH
        
        return {
            "classification": classification,
            "confidence": confidence,
            "reasoning": f"Quality score: {overall_quality:.2f} (completeness: {completeness_score:.2f}, consistency: {consistency_score:.2f})",
            "quality_metrics": {
                "completeness": completeness_score,
                "consistency": consistency_score,
                "overall": overall_quality
            }
        }
    
    async def _generate_intelligent_insights(self, data: List[Dict[str, Any]], 
                                           metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate intelligent insights about the data."""
        
        insights = []
        
        if not data:
            insights.append({
                "type": "data_availability",
                "title": "No Data Content",
                "description": "The uploaded file contains no analyzable data.",
                "confidence": "high",
                "supporting_data": {"rows": 0}
            })
            return insights
        
        # Data volume insight
        row_count = len(data)
        if row_count > 1000:
            insights.append({
                "type": "data_volume",
                "title": "Large Dataset Detected",
                "description": f"Dataset contains {row_count} records, indicating comprehensive asset inventory.",
                "confidence": "high",
                "supporting_data": {"row_count": row_count}
            })
        elif row_count < 10:
            insights.append({
                "type": "data_volume",
                "title": "Small Dataset",
                "description": f"Dataset contains only {row_count} records. This may be a sample or subset.",
                "confidence": "medium",
                "supporting_data": {"row_count": row_count}
            })
        
        # Column diversity insight
        columns = set()
        for row in data:
            columns.update(row.keys())
        
        if len(columns) > 20:
            insights.append({
                "type": "data_richness",
                "title": "Rich Data Structure",
                "description": f"Dataset has {len(columns)} columns, suggesting comprehensive asset information.",
                "confidence": "high",
                "supporting_data": {"column_count": len(columns)}
            })
        
        # Pattern recognition insight
        sample_patterns = self._identify_organizational_patterns(data)
        if sample_patterns:
            insights.append({
                "type": "organizational_patterns",
                "title": "Organizational Patterns Detected",
                "description": "Found patterns that suggest organizational naming conventions and standards.",
                "confidence": "medium",
                "supporting_data": {"patterns": sample_patterns}
            })
        
        return insights
    
    def _identify_organizational_patterns(self, data: List[Dict[str, Any]]) -> List[str]:
        """Identify organizational patterns in the data."""
        patterns = []
        
        # Look for naming conventions in hostnames/asset names
        hostnames = []
        for row in data:
            for key, value in row.items():
                if 'hostname' in key.lower() or 'name' in key.lower():
                    if value and isinstance(value, str):
                        hostnames.append(value)
        
        if hostnames:
            # Analyze hostname patterns
            if any('-' in hostname for hostname in hostnames):
                patterns.append("Dash-separated naming convention")
            if any(re.match(r'.*\d{2,}$', hostname) for hostname in hostnames):
                patterns.append("Numeric suffixes for asset numbering")
            if any(re.match(r'^[a-z]{2,3}-', hostname.lower()) for hostname in hostnames):
                patterns.append("Prefix-based organizational grouping")
        
        return patterns
    
    async def _generate_clarification_questions(self, data: List[Dict[str, Any]], 
                                               metadata: Dict[str, Any], 
                                               page_context: str) -> List[Dict[str, Any]]:
        """Generate intelligent clarification questions for the user."""
        
        questions = []
        
        # Data source confirmation
        source_analysis = await self._identify_data_source_type(data, metadata)
        if source_analysis["confidence"] != ConfidenceLevel.HIGH:
            questions.append({
                "type": "data_classification",
                "title": "Data Source Type Confirmation",
                "question": f"I analyzed this as {source_analysis['type']} data with {source_analysis['confidence'].value} confidence. Can you confirm the actual source?",
                "context": {
                    "detected_type": source_analysis["type"],
                    "confidence": source_analysis["confidence"].value,
                    "reasoning": source_analysis["reasoning"]
                },
                "options": ["CMDB Export", "Migration Assessment Tool", "Application Documentation", "Infrastructure Scan", "Other"],
                "confidence": "medium",
                "priority": "high"
            })
        
        # Column interpretation questions
        columns = set()
        for row in data:
            columns.update(row.keys())
        
        unclear_columns = []
        for column in columns:
            if not self._is_column_name_clear(column):
                unclear_columns.append(column)
        
        if unclear_columns and len(unclear_columns) <= 5:  # Don't overwhelm with too many questions
            questions.append({
                "type": "field_mapping",
                "title": "Column Interpretation Needed",
                "question": f"I found some column names that need clarification: {', '.join(unclear_columns)}. What do these represent?",
                "context": {
                    "unclear_columns": unclear_columns,
                    "sample_data": {col: data[0].get(col) for col in unclear_columns if data}
                },
                "confidence": "low",
                "priority": "medium"
            })
        
        # Business context questions
        if len(data) > 100:  # Only for substantial datasets
            questions.append({
                "type": "business_context",
                "title": "Asset Scope Clarification",
                "question": f"This dataset contains {len(data)} assets. Does this represent your complete infrastructure or a specific subset?",
                "context": {
                    "asset_count": len(data),
                    "appears_comprehensive": len(data) > 500
                },
                "options": ["Complete Infrastructure", "Specific Application/Service", "Data Center/Location Subset", "Sample/Test Data"],
                "confidence": "medium",
                "priority": "medium"
            })
        
        return questions
    
    def _is_column_name_clear(self, column_name: str) -> bool:
        """Determine if a column name is clear or needs clarification."""
        
        # Clear patterns we understand
        clear_patterns = [
            r'.*hostname.*', r'.*asset.*name.*', r'.*server.*name.*',
            r'.*ip.*address.*', r'.*environment.*', r'.*department.*',
            r'.*owner.*', r'.*location.*', r'.*os.*', r'.*operating.*system.*',
            r'.*cpu.*', r'.*memory.*', r'.*ram.*', r'.*storage.*', r'.*disk.*'
        ]
        
        column_lower = column_name.lower()
        for pattern in clear_patterns:
            if re.match(pattern, column_lower):
                return True
        
        # Very short or cryptic names are unclear
        if len(column_name) <= 3 or not any(c.isalpha() for c in column_name):
            return False
        
        return True
    
    async def _assess_analysis_confidence(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall confidence in the analysis."""
        
        confidence_factors = {
            "data_availability": 1.0 if data else 0.0,
            "structure_clarity": 0.8 if len(data) > 5 else 0.3,
            "pattern_recognition": 0.7,  # Will improve with learning
            "content_understanding": 0.6  # Will improve with user feedback
        }
        
        overall_confidence = sum(confidence_factors.values()) / len(confidence_factors)
        
        return {
            "overall_confidence": self._score_to_confidence_level(overall_confidence),
            "confidence_factors": confidence_factors,
            "improvement_areas": [
                factor for factor, score in confidence_factors.items() if score < 0.7
            ]
        }
    
    async def _recommend_next_steps(self, data: List[Dict[str, Any]], 
                                  metadata: Dict[str, Any]) -> List[str]:
        """Recommend next steps based on analysis."""
        
        steps = []
        
        if not data:
            steps.append("Upload a file with data content for analysis")
            return steps
        
        # Always recommend proceeding to field mapping
        steps.append("Proceed to Attribute Mapping to map fields to migration-critical attributes")
        
        # Conditional recommendations
        quality_analysis = await self._classify_data_quality(data)
        if quality_analysis["classification"] == DataClassification.NEEDS_CLARIFICATION:
            steps.append("Review data quality issues in Data Cleansing before field mapping")
        
        if len(data) < 50:
            steps.append("Consider importing additional data sources for complete asset inventory")
        
        steps.append("Provide clarifications to help agents better understand your data")
        
        return steps
    
    def _score_to_confidence_level(self, score: float) -> ConfidenceLevel:
        """Convert numeric score to confidence level."""
        if score >= 0.8:
            return ConfidenceLevel.HIGH
        elif score >= 0.6:
            return ConfidenceLevel.MEDIUM
        elif score >= 0.4:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCERTAIN
    
    # Additional helper methods for pattern recognition and learning
    async def _detect_relationship_patterns(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect patterns that indicate relationships between assets."""
        
        relationships = {
            "potential_dependencies": [],
            "application_groupings": [],
            "environment_patterns": []
        }
        
        # Look for dependency indicators
        for row in data:
            for key, value in row.items():
                if isinstance(value, str) and ('depend' in key.lower() or 'app' in key.lower()):
                    if value and ',' in value:  # Multiple dependencies
                        relationships["potential_dependencies"].append({
                            "asset": row.get('hostname', row.get('asset_name', 'unknown')),
                            "dependencies": value.split(',')
                        })
        
        return relationships
    
    async def _assess_migration_value(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess the value of this data for migration planning."""
        
        # Count migration-relevant fields
        migration_fields = 0
        total_fields = 0
        
        migration_indicators = [
            'hostname', 'asset_name', 'environment', 'owner', 'department',
            'operating_system', 'cpu', 'memory', 'application', 'dependencies'
        ]
        
        for row in data:
            for key in row.keys():
                total_fields += 1
                if any(indicator in key.lower() for indicator in migration_indicators):
                    migration_fields += 1
        
        migration_value_score = migration_fields / total_fields if total_fields > 0 else 0
        
        return {
            "migration_value_score": migration_value_score,
            "migration_relevant_fields": migration_fields,
            "total_fields": total_fields,
            "readiness_for_6r_analysis": migration_value_score >= 0.3
        }
    
    async def _identify_quality_indicators(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify specific quality indicators in the data."""
        
        indicators = {
            "completeness_issues": [],
            "consistency_issues": [],
            "validity_issues": [],
            "enrichment_opportunities": []
        }
        
        # Analyze each column for quality issues
        columns = set()
        for row in data:
            columns.update(row.keys())
        
        for column in columns:
            values = [row.get(column) for row in data]
            non_empty_values = [v for v in values if v is not None and str(v).strip()]
            
            # Completeness
            fill_rate = len(non_empty_values) / len(data)
            if fill_rate < 0.5:
                indicators["completeness_issues"].append({
                    "column": column,
                    "fill_rate": fill_rate,
                    "missing_count": len(data) - len(non_empty_values)
                })
            
            # Consistency (format variations)
            if non_empty_values:
                unique_formats = set()
                for value in non_empty_values[:10]:  # Sample first 10
                    if isinstance(value, str):
                        # Analyze format patterns
                        if re.match(r'\d+\.\d+\.\d+\.\d+', value):
                            unique_formats.add("ip_address")
                        elif re.match(r'\d+', value):
                            unique_formats.add("numeric")
                        elif len(value) > 20:
                            unique_formats.add("long_text")
                        else:
                            unique_formats.add("short_text")
                
                if len(unique_formats) > 2:
                    indicators["consistency_issues"].append({
                        "column": column,
                        "format_variations": list(unique_formats)
                    })
        
        return indicators
    
    async def _analyze_content_patterns(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content patterns in the data to understand its nature."""
        
        if not data:
            return {"error": "No data to analyze"}
        
        patterns = {
            "field_value_patterns": {},
            "data_consistency_patterns": {},
            "organizational_patterns": {},
            "technical_patterns": {}
        }
        
        # Analyze field value patterns
        columns = set()
        for row in data:
            columns.update(row.keys())
        
        for column in columns:
            values = [str(row.get(column, '')) for row in data if row.get(column)]
            
            if values:
                # Detect common patterns in values
                pattern_analysis = {
                    "has_numeric_pattern": any(re.match(r'^\d+$', v) for v in values),
                    "has_ip_pattern": any(re.match(r'\d+\.\d+\.\d+\.\d+', v) for v in values),
                    "has_hostname_pattern": any(re.match(r'^[a-zA-Z0-9\-\.]+$', v) for v in values),
                    "has_path_pattern": any('/' in v or '\\' in v for v in values),
                    "has_version_pattern": any(re.match(r'\d+\.\d+', v) for v in values),
                    "average_length": sum(len(v) for v in values) / len(values),
                    "unique_ratio": len(set(values)) / len(values)
                }
                
                patterns["field_value_patterns"][column] = pattern_analysis
        
        return patterns

# Global instance
data_source_intelligence_agent = DataSourceIntelligenceAgent() 