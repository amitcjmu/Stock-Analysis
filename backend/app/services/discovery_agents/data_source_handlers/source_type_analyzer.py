"""
Source Type Analyzer Handler
Analyzes data sources to identify their type and characteristics.
"""

import logging
import re
from typing import Dict, List, Any
from enum import Enum

from app.services.models.agent_communication import ConfidenceLevel

logger = logging.getLogger(__name__)

class SourceTypeAnalyzer:
    """Analyzes data sources to identify their type and origin."""
    
    def __init__(self):
        self.analyzer_id = "source_type_analyzer"
        
        # Learned patterns for different source types
        self.cmdb_patterns = [
            r'.*hostname.*', r'.*server.*name.*', r'.*asset.*name.*',
            r'.*ip.*address.*', r'.*environment.*', r'.*owner.*',
            r'.*department.*', r'.*location.*', r'.*os.*', r'.*operating.*system.*',
            r'.*cpu.*', r'.*memory.*', r'.*ram.*', r'.*storage.*', r'.*disk.*'
        ]
        
        self.migration_tool_patterns = [
            r'.*discovery.*', r'.*assessment.*', r'.*scan.*result.*',
            r'.*dependency.*', r'.*application.*', r'.*service.*',
            r'.*compatibility.*', r'.*readiness.*', r'.*complexity.*'
        ]
        
        self.documentation_patterns = [
            r'.*description.*', r'.*purpose.*', r'.*function.*',
            r'.*business.*owner.*', r'.*contact.*', r'.*notes.*',
            r'.*documentation.*', r'.*process.*'
        ]
        
        self.infrastructure_patterns = [
            r'.*network.*', r'.*subnet.*', r'.*vlan.*', r'.*port.*',
            r'.*interface.*', r'.*connection.*', r'.*topology.*',
            r'.*bandwidth.*', r'.*performance.*'
        ]
    
    async def identify_data_source_type(self, data: List[Dict[str, Any]], 
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
        
        pattern_matches = 0
        for column in columns:
            for pattern in self.cmdb_patterns:
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
                          ['server', 'windows', 'linux', 'prod', 'dev', 'test']):
                        content_indicators += 1
        
        column_score = pattern_matches / len(columns) if columns else 0
        content_score = min(content_indicators / len(columns), 1.0) if columns else 0
        overall_score = (column_score * 0.7) + (content_score * 0.3)
        
        return {
            "confidence_score": overall_score,
            "reasoning": f"Found {pattern_matches} CMDB-like columns out of {len(columns)} total",
            "pattern_matches": pattern_matches,
            "content_indicators": content_indicators
        }
    
    def _analyze_migration_tool_indicators(self, columns: List[str], data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze indicators that this is migration assessment tool data."""
        
        pattern_matches = 0
        for column in columns:
            for pattern in self.migration_tool_patterns:
                if re.match(pattern, column.lower()):
                    pattern_matches += 1
                    break
        
        # Look for migration-specific terminology
        migration_terms = 0
        if data:
            sample_row = data[0]
            for value in sample_row.values():
                if isinstance(value, str):
                    value_lower = value.lower()
                    if any(term in value_lower for term in 
                          ['migration', 'assessment', 'readiness', 'complexity']):
                        migration_terms += 1
        
        column_score = pattern_matches / len(columns) if columns else 0
        content_score = min(migration_terms / len(columns), 1.0) if columns else 0
        overall_score = (column_score * 0.6) + (content_score * 0.4)
        
        return {
            "confidence_score": overall_score,
            "reasoning": f"Found {pattern_matches} migration-related columns and {migration_terms} migration terms",
            "pattern_matches": pattern_matches,
            "migration_indicators": migration_terms
        }
    
    def _analyze_documentation_indicators(self, columns: List[str], data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze indicators that this is documentation or business process data."""
        
        pattern_matches = 0
        for column in columns:
            for pattern in self.documentation_patterns:
                if re.match(pattern, column.lower()):
                    pattern_matches += 1
                    break
        
        # Look for text-heavy content
        text_content = 0
        if data:
            sample_row = data[0]
            for value in sample_row.values():
                if isinstance(value, str) and len(value) > 50:
                    text_content += 1
        
        column_score = pattern_matches / len(columns) if columns else 0
        content_score = min(text_content / len(columns), 1.0) if columns else 0
        overall_score = (column_score * 0.5) + (content_score * 0.5)
        
        return {
            "confidence_score": overall_score,
            "reasoning": f"Found {pattern_matches} documentation columns and {text_content} text-heavy fields",
            "pattern_matches": pattern_matches,
            "text_indicators": text_content
        }
    
    def _analyze_infrastructure_indicators(self, columns: List[str], data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze indicators that this is infrastructure scan data."""
        
        pattern_matches = 0
        for column in columns:
            for pattern in self.infrastructure_patterns:
                if re.match(pattern, column.lower()):
                    pattern_matches += 1
                    break
        
        # Look for network/infrastructure specific content
        infra_terms = 0
        if data:
            sample_row = data[0]
            for value in sample_row.values():
                if isinstance(value, str):
                    value_lower = value.lower()
                    if any(term in value_lower for term in 
                          ['network', 'subnet', 'interface', 'port', 'protocol']):
                        infra_terms += 1
        
        column_score = pattern_matches / len(columns) if columns else 0
        content_score = min(infra_terms / len(columns), 1.0) if columns else 0
        overall_score = (column_score * 0.7) + (content_score * 0.3)
        
        return {
            "confidence_score": overall_score,
            "reasoning": f"Found {pattern_matches} infrastructure columns and {infra_terms} network terms",
            "pattern_matches": pattern_matches,
            "infra_indicators": infra_terms
        }
    
    def _analyze_custom_format_indicators(self, columns: List[str], data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze if this appears to be a custom or unknown format."""
        
        # Custom format indicators:
        # - Unusual column names
        # - Non-standard patterns
        # - Mixed data types in unusual ways
        
        unusual_patterns = 0
        for column in columns:
            # Look for very generic or unusual column names
            if any(pattern in column.lower() for pattern in 
                  ['col', 'field', 'data', 'value', 'item', 'record']):
                unusual_patterns += 1
        
        # High unusual pattern count suggests custom format
        custom_score = min(unusual_patterns / len(columns), 0.8) if columns else 0
        
        return {
            "confidence_score": custom_score,
            "reasoning": f"Found {unusual_patterns} generic or unusual column patterns",
            "unusual_patterns": unusual_patterns
        }
    
    def _score_to_confidence_level(self, score: float) -> ConfidenceLevel:
        """Convert numeric confidence score to ConfidenceLevel enum."""
        if score >= 0.8:
            return ConfidenceLevel.HIGH
        elif score >= 0.6:
            return ConfidenceLevel.MEDIUM
        elif score >= 0.4:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCERTAIN
    
    def learn_from_feedback(self, source_type: str, columns: List[str], 
                           user_correction: str) -> None:
        """Learn from user feedback to improve pattern recognition."""
        # This would update learned patterns based on user corrections
        logger.info(f"Learning opportunity: {source_type} correction to {user_correction}")
        # Implementation would update the pattern lists based on feedback 