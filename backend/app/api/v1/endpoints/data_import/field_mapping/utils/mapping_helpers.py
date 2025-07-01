"""
Helper functions for intelligent field mapping.
"""

import re
from typing import Dict, List, Any, Optional
from difflib import SequenceMatcher


def intelligent_field_mapping(source_field: str) -> str:
    """
    Intelligently map source field to target field using pattern matching.
    
    Args:
        source_field: Source field name to map
        
    Returns:
        Best matching target field name
    """
    if not source_field:
        return "name"
    
    source_lower = source_field.lower().strip()
    
    # Common field mapping patterns with priorities
    field_patterns = {
        # Identity fields (highest priority)
        'id': ['asset_id', 'name', 'hostname'],
        'identifier': ['asset_id', 'name'],
        'uuid': ['asset_id'],
        
        # Name fields
        'name': ['name', 'asset_name', 'hostname'],
        'hostname': ['hostname', 'name'],
        'fqdn': ['fqdn', 'hostname'],
        'dns': ['hostname', 'fqdn'],
        'server': ['hostname', 'name'],
        'host': ['hostname', 'name'],
        'machine': ['hostname', 'name'],
        'computer': ['hostname', 'name'],
        
        # Asset type
        'type': ['asset_type', 'intelligent_asset_type'],
        'category': ['asset_type'],
        'kind': ['asset_type'],
        'class': ['asset_type'],
        
        # Operating system
        'os': ['operating_system'],
        'operating_system': ['operating_system'],
        'platform': ['operating_system'],
        'system': ['operating_system'],
        
        # Network
        'ip': ['ip_address'],
        'ip_address': ['ip_address'],
        'ipaddress': ['ip_address'],
        'addr': ['ip_address'],
        'address': ['ip_address'],
        'mac': ['mac_address'],
        'mac_address': ['mac_address'],
        
        # Environment
        'env': ['environment'],
        'environment': ['environment'],
        'stage': ['environment'],
        'tier': ['environment'],
        
        # Hardware specs
        'cpu': ['cpu_cores'],
        'cores': ['cpu_cores'],
        'processor': ['cpu_cores'],
        'memory': ['memory_gb'],
        'ram': ['memory_gb'],
        'mem': ['memory_gb'],
        'storage': ['storage_gb'],
        'disk': ['storage_gb'],
        'drive': ['storage_gb'],
        
        # Location
        'location': ['location'],
        'site': ['location'],
        'datacenter': ['datacenter'],
        'dc': ['datacenter'],
        'facility': ['datacenter'],
        
        # Business info
        'owner': ['business_owner', 'technical_owner'],
        'dept': ['department'],
        'department': ['department'],
        'division': ['department'],
        'org': ['department'],
        'app': ['application_name'],
        'application': ['application_name'],
        'service': ['application_name'],
        
        # Technical specs
        'version': ['os_version'],
        'tech': ['technology_stack'],
        'stack': ['technology_stack'],
        'critical': ['criticality', 'business_criticality'],
        'priority': ['migration_priority'],
        'complexity': ['migration_complexity'],
        
        # Status
        'status': ['status'],
        'state': ['status'],
        'condition': ['status']
    }
    
    # Direct exact matches first
    if source_lower in field_patterns:
        return field_patterns[source_lower][0]
    
    # Partial matches with confidence scoring
    best_match = "name"  # Default fallback
    best_score = 0.0
    
    for pattern, targets in field_patterns.items():
        # Check if pattern is contained in source field
        if pattern in source_lower:
            # Calculate match confidence
            match_ratio = len(pattern) / len(source_lower)
            similarity = SequenceMatcher(None, pattern, source_lower).ratio()
            score = (match_ratio * 0.6) + (similarity * 0.4)
            
            if score > best_score:
                best_score = score
                best_match = targets[0]
    
    # If no good partial match, try fuzzy matching
    if best_score < 0.3:
        best_match = _fuzzy_field_match(source_lower, field_patterns)
    
    return best_match


def calculate_mapping_confidence(source_field: str, target_field: str) -> float:
    """
    Calculate confidence score for a field mapping.
    
    Args:
        source_field: Source field name
        target_field: Target field name
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    if not source_field or not target_field:
        return 0.1
    
    source_lower = source_field.lower().strip()
    target_lower = target_field.lower().strip()
    
    # Exact match gets highest confidence
    if source_lower == target_lower:
        return 0.95
    
    # Calculate string similarity
    similarity = SequenceMatcher(None, source_lower, target_lower).ratio()
    
    # Check for common patterns
    pattern_boost = 0.0
    common_patterns = [
        ('id', 'asset_id'),
        ('name', 'asset_name'),
        ('hostname', 'hostname'),
        ('ip', 'ip_address'),
        ('type', 'asset_type'),
        ('os', 'operating_system'),
        ('env', 'environment'),
        ('cpu', 'cpu_cores'),
        ('memory', 'memory_gb'),
        ('storage', 'storage_gb')
    ]
    
    for pattern, target in common_patterns:
        if pattern in source_lower and target == target_lower:
            pattern_boost = 0.3
            break
    
    # Base confidence calculation
    base_confidence = min(0.8, similarity + pattern_boost)
    
    # Apply additional rules
    if target_field == "name" and "name" not in source_lower:
        # Penalize generic "name" mapping for non-name fields
        base_confidence *= 0.7
    
    if len(source_field) < 3:
        # Penalize very short field names
        base_confidence *= 0.8
    
    # Ensure minimum confidence for any mapping
    return max(0.1, base_confidence)


def _fuzzy_field_match(source_field: str, field_patterns: Dict[str, List[str]]) -> str:
    """Fuzzy matching for field names using edit distance."""
    best_match = "name"
    best_score = 0.0
    
    for pattern in field_patterns.keys():
        similarity = SequenceMatcher(None, source_field, pattern).ratio()
        if similarity > best_score and similarity > 0.4:  # Minimum threshold
            best_score = similarity
            best_match = field_patterns[pattern][0]
    
    return best_match


def get_field_patterns() -> Dict[str, List[str]]:
    """Get all available field mapping patterns."""
    return {
        'identity': ['asset_id', 'name', 'hostname'],
        'names': ['name', 'asset_name', 'hostname', 'fqdn'],
        'network': ['ip_address', 'mac_address', 'hostname'],
        'hardware': ['cpu_cores', 'memory_gb', 'storage_gb'],
        'system': ['operating_system', 'os_version', 'asset_type'],
        'business': ['business_owner', 'technical_owner', 'department'],
        'location': ['location', 'datacenter', 'environment'],
        'application': ['application_name', 'technology_stack'],
        'migration': ['migration_priority', 'migration_complexity', 'criticality']
    }


def normalize_field_name(field_name: str) -> str:
    """Normalize field name for better matching."""
    if not field_name:
        return ""
    
    # Convert to lowercase and remove extra spaces
    normalized = field_name.lower().strip()
    
    # Replace common separators with underscores
    normalized = re.sub(r'[-\s\.]+', '_', normalized)
    
    # Remove special characters except underscores
    normalized = re.sub(r'[^a-z0-9_]', '', normalized)
    
    # Remove leading/trailing underscores
    normalized = normalized.strip('_')
    
    return normalized


def extract_field_metadata(field_name: str, sample_values: List[Any] = None) -> Dict[str, Any]:
    """Extract metadata about a field for better mapping decisions."""
    metadata = {
        'original_name': field_name,
        'normalized_name': normalize_field_name(field_name),
        'length': len(field_name),
        'has_separators': bool(re.search(r'[-\s\.]', field_name)),
        'is_camel_case': bool(re.search(r'[a-z][A-Z]', field_name)),
        'is_snake_case': '_' in field_name,
        'is_all_caps': field_name.isupper(),
        'word_count': len(re.findall(r'\b\w+\b', field_name))
    }
    
    if sample_values:
        metadata.update({
            'sample_count': len(sample_values),
            'has_nulls': any(v is None or v == '' for v in sample_values),
            'all_numeric': all(isinstance(v, (int, float)) for v in sample_values if v is not None),
            'all_strings': all(isinstance(v, str) for v in sample_values if v is not None)
        })
    
    return metadata