"""
Attribute Mapping Agent - Enterprise Asset Schema Mapping Specialist
Maps source data fields to the full asset table schema with critical attribute prioritization
"""

import time
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from difflib import SequenceMatcher
import pandas as pd
from datetime import datetime
import logging

from .base_discovery_agent import BaseDiscoveryAgent, AgentResult

logger = logging.getLogger(__name__)

class AttributeMappingAgent(BaseDiscoveryAgent):
    """
    Enterprise Asset Schema Mapping Specialist
    
    Maps source data fields to the 50-60+ fields in the assets table, with primary focus 
    on the 20+ critical migration attributes, ensuring comprehensive field identification 
    for downstream processing.
    """
    
    def __init__(self):
        super().__init__("Attribute Mapping Agent", "attribute_mapping_001")
        
        # Full Asset Table Schema (50-60+ fields)
        self.asset_schema = {
            # Critical Migration Attributes (Priority 1)
            'critical_attributes': {
                # Identity Attributes
                'asset_id': ['id', 'asset_id', 'identifier', 'unique_id', 'resource_id'],
                'hostname': ['hostname', 'host', 'server_name', 'machine_name', 'computer_name'],
                'asset_name': ['name', 'asset_name', 'display_name', 'friendly_name'],
                'asset_type': ['type', 'asset_type', 'resource_type', 'category'],
                
                # Business Attributes
                'business_unit': ['business_unit', 'bu', 'department', 'division', 'org_unit'],
                'owner': ['owner', 'asset_owner', 'responsible_party', 'contact'],
                'cost_center': ['cost_center', 'cost_centre', 'billing_code', 'charge_code'],
                'criticality': ['criticality', 'critical', 'importance', 'priority'],
                
                # Technical Attributes
                'operating_system': ['os', 'operating_system', 'platform', 'system'],
                'ip_address': ['ip', 'ip_address', 'primary_ip', 'network_address'],
                'environment': ['env', 'environment', 'stage', 'tier'],
                'location': ['location', 'site', 'datacenter', 'facility'],
                
                # Network Attributes
                'network_zone': ['zone', 'network_zone', 'security_zone', 'segment'],
                'subnet': ['subnet', 'network', 'vlan', 'network_segment'],
                
                # Compliance Attributes
                'compliance_scope': ['compliance', 'regulation', 'framework', 'standard'],
                'data_classification': ['classification', 'data_class', 'sensitivity', 'confidentiality'],
                
                # Operational Attributes
                'status': ['status', 'state', 'operational_status', 'health'],
                'last_scan_date': ['last_scan', 'scan_date', 'discovery_date', 'updated'],
                'install_date': ['install_date', 'created', 'deployment_date', 'commissioned']
            },
            
            # Secondary Asset Fields (Priority 2)
            'secondary_attributes': {
                # Hardware Details
                'manufacturer': ['manufacturer', 'vendor', 'make', 'brand'],
                'model': ['model', 'product', 'hardware_model', 'device_model'],
                'serial_number': ['serial', 'serial_number', 'sn', 'serial_no'],
                'cpu_count': ['cpu', 'processor', 'cores', 'vcpu'],
                'memory_gb': ['memory', 'ram', 'mem', 'memory_gb'],
                'storage_gb': ['storage', 'disk', 'hdd', 'storage_gb'],
                
                # Software Details
                'os_version': ['os_version', 'version', 'release', 'build'],
                'patch_level': ['patch', 'patch_level', 'update', 'service_pack'],
                'installed_software': ['software', 'applications', 'packages', 'programs'],
                
                # Network Details
                'mac_address': ['mac', 'mac_address', 'physical_address', 'hardware_address'],
                'dns_name': ['dns', 'fqdn', 'domain_name', 'dns_name'],
                'domain': ['domain', 'ad_domain', 'workgroup', 'realm'],
                'ports': ['ports', 'open_ports', 'services', 'listening_ports'],
                
                # Virtualization
                'virtualization_type': ['virtual', 'vm_type', 'hypervisor', 'container'],
                'host_server': ['host', 'parent', 'hypervisor_host', 'physical_host'],
                
                # Management
                'management_ip': ['mgmt_ip', 'management_ip', 'admin_ip', 'oob_ip'],
                'monitoring_status': ['monitoring', 'monitored', 'agent_status', 'snmp'],
                'backup_status': ['backup', 'backup_status', 'protected', 'backup_agent'],
                
                # Security
                'antivirus_status': ['antivirus', 'av', 'endpoint_protection', 'security_agent'],
                'firewall_status': ['firewall', 'fw', 'host_firewall', 'iptables'],
                'encryption_status': ['encryption', 'encrypted', 'bitlocker', 'luks'],
                
                # Business Context
                'service_name': ['service', 'service_name', 'application', 'workload'],
                'project_code': ['project', 'project_code', 'initiative', 'program'],
                'support_tier': ['support', 'tier', 'sla', 'support_level'],
                'maintenance_window': ['maintenance', 'window', 'downtime', 'maint_window'],
                
                # Lifecycle
                'lifecycle_stage': ['lifecycle', 'stage', 'phase', 'maturity'],
                'end_of_life': ['eol', 'end_of_life', 'retirement', 'sunset'],
                'warranty_expiry': ['warranty', 'support_end', 'contract_end', 'expiry'],
                
                # Custom Fields
                'custom_field_1': ['custom1', 'field1', 'attr1', 'tag1'],
                'custom_field_2': ['custom2', 'field2', 'attr2', 'tag2'],
                'custom_field_3': ['custom3', 'field3', 'attr3', 'tag3'],
                
                # Metadata
                'notes': ['notes', 'comments', 'description', 'remarks'],
                'tags': ['tags', 'labels', 'keywords', 'metadata']
            }
        }
        
        # Confidence thresholds
        self.confidence_thresholds = {
            'high_confidence': 85.0,
            'medium_confidence': 65.0,
            'low_confidence': 40.0,
            'ambiguous_threshold': 40.0
        }
        
        # Pattern weights for scoring
        self.pattern_weights = {
            'exact_match': 100.0,
            'case_insensitive': 95.0,
            'substring': 80.0,
            'fuzzy_high': 75.0,
            'fuzzy_medium': 60.0,
            'pattern_match': 70.0,
            'contextual': 50.0
        }
    
    def get_role(self) -> str:
        return "Enterprise Asset Schema Mapping Specialist"
    
    def get_goal(self) -> str:
        return "Intelligently map source data fields to the 50-60+ fields in the assets table, with primary focus on the 20+ critical migration attributes, ensuring comprehensive field identification for downstream processing"
    
    def get_backstory(self) -> str:
        return ("You are a data migration expert with deep knowledge of enterprise asset inventories and database schemas. "
                "You've mapped thousands of different data sources to standardized migration schemas. You excel at pattern recognition "
                "and can identify field relationships even when naming conventions vary significantly across organizations. "
                "You understand both the critical migration attributes and the full asset table schema.")
    
    async def execute(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """
        Execute comprehensive attribute mapping
        
        Args:
            data: Data with source columns to map
            context: Flow context with metadata
            
        Returns:
            AgentResult with comprehensive field mappings and confidence scores
        """
        return await self.execute_analysis(data, context)
    
    async def execute_analysis(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """
        Execute comprehensive attribute mapping analysis
        
        Args:
            data: Data with source columns to map
            context: Flow context with metadata
            
        Returns:
            AgentResult with comprehensive field mappings and confidence scores
        """
        start_time = time.time()
        context = context or {}
        
        try:
            self.logger.info("🗺️ Starting comprehensive attribute mapping...")
            
            # Extract source data
            raw_data = data.get('raw_data', [])
            source_columns = data.get('source_columns', [])
            
            # If no explicit columns provided, extract from data
            if not source_columns and raw_data:
                df = pd.DataFrame(raw_data)
                source_columns = list(df.columns)
            
            if not source_columns:
                return self._create_result(
                    execution_time=time.time() - start_time,
                    confidence_score=0.0,
                    status="failed",
                    data={},
                    errors=["No source columns provided for mapping"]
                )
            
            self.logger.info(f"📊 Mapping {len(source_columns)} source columns to asset schema")
            
            # Perform comprehensive mapping
            mapping_results = {
                'critical_mappings': await self._map_critical_attributes(source_columns),
                'secondary_mappings': await self._map_secondary_attributes(source_columns),
                'unmapped_columns': [],
                'ambiguous_mappings': [],
                'mapping_confidence': {},
                'summary': {}
            }
            
            # Analyze mapping quality
            await self._analyze_mapping_quality(mapping_results, source_columns)
            
            # Generate mapping insights
            await self._generate_mapping_insights(mapping_results, source_columns)
            
            # Check for required clarifications
            await self._check_mapping_clarifications(mapping_results, source_columns)
            
            # Calculate overall confidence
            overall_confidence = self._calculate_mapping_confidence(mapping_results)
            
            # Determine status
            status = self._determine_mapping_status(mapping_results, overall_confidence)
            
            execution_time = time.time() - start_time
            self.logger.info(f"✅ Attribute mapping completed in {execution_time:.2f}s with {overall_confidence:.1f}% confidence")
            
            return self._create_result(
                execution_time=execution_time,
                confidence_score=overall_confidence,
                status=status,
                data=mapping_results,
                metadata={
                    'source_columns_count': len(source_columns),
                    'critical_mappings_count': len(mapping_results['critical_mappings']),
                    'secondary_mappings_count': len(mapping_results['secondary_mappings']),
                    'mapping_timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ Attribute mapping failed: {str(e)}")
            
            return self._create_result(
                execution_time=execution_time,
                confidence_score=0.0,
                status="failed",
                data={},
                errors=[f"Mapping failed: {str(e)}"]
            )
    
    async def _map_critical_attributes(self, source_columns: List[str]) -> Dict[str, Any]:
        """Map critical migration attributes with high priority"""
        critical_mappings = {}
        
        for asset_field, patterns in self.asset_schema['critical_attributes'].items():
            best_match = await self._find_best_match(asset_field, patterns, source_columns)
            if best_match:
                critical_mappings[asset_field] = best_match
        
        return critical_mappings
    
    async def _map_secondary_attributes(self, source_columns: List[str]) -> Dict[str, Any]:
        """Map secondary asset attributes for comprehensive coverage"""
        secondary_mappings = {}
        
        for asset_field, patterns in self.asset_schema['secondary_attributes'].items():
            best_match = await self._find_best_match(asset_field, patterns, source_columns)
            if best_match:
                secondary_mappings[asset_field] = best_match
        
        return secondary_mappings
    
    async def _find_best_match(self, asset_field: str, patterns: List[str], source_columns: List[str]) -> Optional[Dict[str, Any]]:
        """Find the best matching source column for an asset field"""
        best_match = None
        best_score = 0.0
        
        for source_col in source_columns:
            score = await self._calculate_match_score(source_col, patterns, asset_field)
            
            if score > best_score and score >= self.confidence_thresholds['low_confidence']:
                best_score = score
                best_match = {
                    'source_column': source_col,
                    'asset_field': asset_field,
                    'confidence': score,
                    'match_type': self._get_match_type(score),
                    'pattern_matched': self._get_matched_pattern(source_col, patterns)
                }
        
        return best_match
    
    async def _calculate_match_score(self, source_col: str, patterns: List[str], asset_field: str) -> float:
        """Calculate confidence score for a potential field mapping"""
        source_lower = source_col.lower()
        max_score = 0.0
        
        for pattern in patterns:
            pattern_lower = pattern.lower()
            
            # Exact match
            if source_lower == pattern_lower:
                max_score = max(max_score, self.pattern_weights['exact_match'])
                continue
            
            # Case-insensitive exact match
            if source_col.lower() == pattern.lower():
                max_score = max(max_score, self.pattern_weights['case_insensitive'])
                continue
            
            # Substring match
            if pattern_lower in source_lower or source_lower in pattern_lower:
                max_score = max(max_score, self.pattern_weights['substring'])
                continue
            
            # Fuzzy string matching
            similarity = SequenceMatcher(None, source_lower, pattern_lower).ratio()
            if similarity > 0.8:
                max_score = max(max_score, self.pattern_weights['fuzzy_high'] * similarity)
            elif similarity > 0.6:
                max_score = max(max_score, self.pattern_weights['fuzzy_medium'] * similarity)
            
            # Pattern-based matching (regex-like)
            if self._pattern_match(source_lower, pattern_lower):
                max_score = max(max_score, self.pattern_weights['pattern_match'])
        
        # Contextual scoring based on asset field type
        contextual_bonus = self._get_contextual_bonus(source_col, asset_field)
        max_score += contextual_bonus
        
        return min(100.0, max_score)
    
    def _pattern_match(self, source: str, pattern: str) -> bool:
        """Check for pattern-based matches"""
        # Remove common separators and check
        source_clean = re.sub(r'[_\-\s]', '', source)
        pattern_clean = re.sub(r'[_\-\s]', '', pattern)
        
        return (pattern_clean in source_clean or 
                source_clean in pattern_clean or
                source_clean.startswith(pattern_clean) or
                source_clean.endswith(pattern_clean))
    
    def _get_contextual_bonus(self, source_col: str, asset_field: str) -> float:
        """Get contextual bonus based on field relationships"""
        bonus = 0.0
        source_lower = source_col.lower()
        
        # IP address patterns
        if 'ip' in asset_field and ('ip' in source_lower or 'address' in source_lower):
            bonus += 10.0
        
        # Date patterns
        if 'date' in asset_field and ('date' in source_lower or 'time' in source_lower):
            bonus += 10.0
        
        # Status patterns
        if 'status' in asset_field and ('status' in source_lower or 'state' in source_lower):
            bonus += 10.0
        
        # Size/capacity patterns
        if any(size_term in asset_field for size_term in ['gb', 'count', 'size']) and \
           any(size_term in source_lower for size_term in ['gb', 'mb', 'size', 'capacity', 'count']):
            bonus += 10.0
        
        return bonus
    
    def _get_match_type(self, score: float) -> str:
        """Determine match type based on confidence score"""
        if score >= self.confidence_thresholds['high_confidence']:
            return 'high_confidence'
        elif score >= self.confidence_thresholds['medium_confidence']:
            return 'medium_confidence'
        elif score >= self.confidence_thresholds['low_confidence']:
            return 'low_confidence'
        else:
            return 'ambiguous'
    
    def _get_matched_pattern(self, source_col: str, patterns: List[str]) -> str:
        """Get the pattern that matched best"""
        source_lower = source_col.lower()
        best_pattern = patterns[0]  # Default
        best_similarity = 0.0
        
        for pattern in patterns:
            similarity = SequenceMatcher(None, source_lower, pattern.lower()).ratio()
            if similarity > best_similarity:
                best_similarity = similarity
                best_pattern = pattern
        
        return best_pattern
    
    async def _analyze_mapping_quality(self, mapping_results: Dict[str, Any], source_columns: List[str]):
        """Analyze overall mapping quality and completeness"""
        total_critical = len(self.asset_schema['critical_attributes'])
        mapped_critical = len(mapping_results['critical_mappings'])
        
        total_secondary = len(self.asset_schema['secondary_attributes'])
        mapped_secondary = len(mapping_results['secondary_mappings'])
        
        # Find unmapped source columns
        mapped_sources = set()
        for mapping in mapping_results['critical_mappings'].values():
            mapped_sources.add(mapping['source_column'])
        for mapping in mapping_results['secondary_mappings'].values():
            mapped_sources.add(mapping['source_column'])
        
        mapping_results['unmapped_columns'] = [col for col in source_columns if col not in mapped_sources]
        
        # Find ambiguous mappings (low confidence)
        ambiguous = []
        for mapping in list(mapping_results['critical_mappings'].values()) + list(mapping_results['secondary_mappings'].values()):
            if mapping['confidence'] < self.confidence_thresholds['medium_confidence']:
                ambiguous.append(mapping)
        
        mapping_results['ambiguous_mappings'] = ambiguous
        
        # Summary statistics
        mapping_results['summary'] = {
            'critical_coverage': (mapped_critical / total_critical) * 100,
            'secondary_coverage': (mapped_secondary / total_secondary) * 100,
            'source_utilization': (len(mapped_sources) / len(source_columns)) * 100,
            'total_mappings': mapped_critical + mapped_secondary,
            'high_confidence_mappings': len([m for m in list(mapping_results['critical_mappings'].values()) + list(mapping_results['secondary_mappings'].values()) 
                                           if m['confidence'] >= self.confidence_thresholds['high_confidence']]),
            'ambiguous_count': len(ambiguous),
            'unmapped_count': len(mapping_results['unmapped_columns'])
        }
    
    async def _generate_mapping_insights(self, mapping_results: Dict[str, Any], source_columns: List[str]):
        """Generate insights for the Agent-UI-monitor panel"""
        summary = mapping_results['summary']
        
        # Coverage insight
        self.add_insight(
            title="Field Mapping Coverage",
            description=f"Mapped {summary['total_mappings']} fields: "
                       f"{len(mapping_results['critical_mappings'])} critical, "
                       f"{len(mapping_results['secondary_mappings'])} secondary. "
                       f"Critical coverage: {summary['critical_coverage']:.1f}%",
            confidence_score=summary['critical_coverage'],
            category="mapping"
        )
        
        # Quality insight
        if summary['high_confidence_mappings'] > 0:
            self.add_insight(
                title="Mapping Quality Assessment",
                description=f"{summary['high_confidence_mappings']} high-confidence mappings, "
                           f"{summary['ambiguous_count']} ambiguous mappings requiring review",
                confidence_score=85.0 if summary['ambiguous_count'] < 5 else 65.0,
                category="quality",
                actionable=summary['ambiguous_count'] > 0,
                action_items=["Review ambiguous mappings", "Confirm low-confidence assignments"]
            )
        
        # Unmapped columns insight
        if mapping_results['unmapped_columns']:
            self.add_insight(
                title="Unmapped Source Columns",
                description=f"{len(mapping_results['unmapped_columns'])} source columns remain unmapped: "
                           f"{', '.join(mapping_results['unmapped_columns'][:5])}{'...' if len(mapping_results['unmapped_columns']) > 5 else ''}",
                confidence_score=60.0,
                category="recommendation",
                actionable=True,
                action_items=["Review unmapped columns", "Consider custom field assignments"]
            )
    
    async def _check_mapping_clarifications(self, mapping_results: Dict[str, Any], source_columns: List[str]):
        """Check for required user clarifications"""
        
        # Ambiguous mappings clarification
        if mapping_results['ambiguous_mappings']:
            for mapping in mapping_results['ambiguous_mappings'][:3]:  # Limit to top 3
                asset_field = mapping['asset_field']
                source_col = mapping['source_column']
                
                # Get alternative suggestions
                alternatives = await self._get_alternative_mappings(source_col, asset_field)
                
                options = [
                    {"value": asset_field, "label": f"{asset_field} (current - {mapping['confidence']:.1f}%)"}
                ]
                options.extend([
                    {"value": alt['field'], "label": f"{alt['field']} ({alt['confidence']:.1f}%)"}
                    for alt in alternatives[:3]
                ])
                options.append({"value": "skip", "label": "Skip this mapping"})
                
                self.add_clarification_request(
                    question_text=f"Source column '{source_col}' has ambiguous mapping. Which asset field should it map to?",
                    options=options,
                    context={
                        "source_column": source_col,
                        "current_mapping": asset_field,
                        "confidence": mapping['confidence']
                    },
                    priority="medium",
                    clarification_type="mapping"
                )
        
        # Critical attributes missing clarification
        critical_mapped = set(mapping_results['critical_mappings'].keys())
        critical_required = set(self.asset_schema['critical_attributes'].keys())
        missing_critical = critical_required - critical_mapped
        
        if missing_critical:
            missing_list = list(missing_critical)[:5]  # Top 5 missing
            unmapped_cols = mapping_results['unmapped_columns'][:10]  # Available columns
            
            if unmapped_cols:
                self.add_clarification_request(
                    question_text=f"Critical attributes missing: {', '.join(missing_list)}. "
                                 f"Can any unmapped columns fill these?",
                    options=[
                        {"value": "manual_map", "label": "Manually assign mappings"},
                        {"value": "skip_missing", "label": "Skip missing critical attributes"},
                        {"value": "review_later", "label": "Review in next phase"}
                    ],
                    context={
                        "missing_critical": missing_list,
                        "unmapped_columns": unmapped_cols
                    },
                    priority="high",
                    clarification_type="mapping"
                )
    
    async def _get_alternative_mappings(self, source_col: str, current_field: str) -> List[Dict[str, Any]]:
        """Get alternative mapping suggestions for a source column"""
        alternatives = []
        
        # Check all asset fields for alternative matches
        all_fields = {**self.asset_schema['critical_attributes'], **self.asset_schema['secondary_attributes']}
        
        for asset_field, patterns in all_fields.items():
            if asset_field != current_field:
                score = await self._calculate_match_score(source_col, patterns, asset_field)
                if score >= self.confidence_thresholds['low_confidence']:
                    alternatives.append({
                        'field': asset_field,
                        'confidence': score,
                        'type': 'critical' if asset_field in self.asset_schema['critical_attributes'] else 'secondary'
                    })
        
        # Sort by confidence
        alternatives.sort(key=lambda x: x['confidence'], reverse=True)
        return alternatives
    
    def _calculate_mapping_confidence(self, mapping_results: Dict[str, Any]) -> float:
        """Calculate overall mapping confidence score"""
        all_mappings = list(mapping_results['critical_mappings'].values()) + list(mapping_results['secondary_mappings'].values())
        
        if not all_mappings:
            return 0.0
        
        # Weight critical mappings higher
        critical_weight = 0.7
        secondary_weight = 0.3
        
        critical_confidence = 0.0
        if mapping_results['critical_mappings']:
            critical_scores = [m['confidence'] for m in mapping_results['critical_mappings'].values()]
            critical_confidence = sum(critical_scores) / len(critical_scores)
        
        secondary_confidence = 0.0
        if mapping_results['secondary_mappings']:
            secondary_scores = [m['confidence'] for m in mapping_results['secondary_mappings'].values()]
            secondary_confidence = sum(secondary_scores) / len(secondary_scores)
        
        # Adjust for coverage
        critical_coverage = mapping_results['summary']['critical_coverage'] / 100
        coverage_bonus = critical_coverage * 10  # Up to 10 point bonus for good coverage
        
        overall_confidence = (critical_confidence * critical_weight + 
                            secondary_confidence * secondary_weight + 
                            coverage_bonus)
        
        return min(100.0, overall_confidence)
    
    def _determine_mapping_status(self, mapping_results: Dict[str, Any], confidence: float) -> str:
        """Determine overall mapping status"""
        critical_coverage = mapping_results['summary']['critical_coverage']
        ambiguous_count = mapping_results['summary']['ambiguous_count']
        
        if critical_coverage < 50 or confidence < 60:
            return "partial"
        elif ambiguous_count > 5 or confidence < 80:
            return "partial"
        else:
            return "success" 