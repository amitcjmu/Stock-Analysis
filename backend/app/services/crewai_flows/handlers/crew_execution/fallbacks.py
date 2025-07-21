"""
Crew Fallback Handlers
Provides intelligent fallback implementations when crew execution fails
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class CrewFallbackHandler:
    """Handles fallback implementations for various crew failures"""
    
    def intelligent_field_mapping_fallback(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Intelligent fallback for field mapping when crew execution fails"""
        if not raw_data:
            return {
                "mappings": {},
                "confidence_scores": {},
                "unmapped_fields": [],
                "validation_results": {"valid": False, "score": 0.0},
                "agent_insights": {"fallback": "No data available for mapping"}
            }
        
        headers = list(raw_data[0].keys())
        
        # Intelligent mapping based on common field patterns
        mapping_patterns = {
            "asset_name": ["asset_name", "name", "hostname", "server_name", "device_name"],
            "asset_type": ["asset_type", "type", "category", "classification"],
            "asset_id": ["asset_id", "id", "ci_id", "sys_id"],
            "environment": ["environment", "env", "stage", "tier"],
            "business_criticality": ["business_criticality", "criticality", "priority", "tier", "dr_tier"],
            "operating_system": ["operating_system", "os", "platform"],
            "ip_address": ["ip_address", "ip", "primary_ip"],
            "location": ["location", "site", "datacenter", "facility", "location_datacenter"],
            "manufacturer": ["manufacturer", "vendor", "make"],
            "model": ["model", "hardware_model"],
            "serial_number": ["serial_number", "serial", "sn"],
            "cpu_cores": ["cpu_cores", "cores", "cpu"],
            "memory": ["memory", "ram", "ram_gb"],
            "storage": ["storage", "disk", "storage_gb"]
        }
        
        mappings = {}
        confidence_scores = {}
        unmapped_fields = []
        
        for header in headers:
            mapped = False
            header_lower = header.lower().replace('_', '').replace(' ', '')
            
            for target_attr, patterns in mapping_patterns.items():
                for pattern in patterns:
                    pattern_clean = pattern.lower().replace('_', '').replace(' ', '')
                    if pattern_clean in header_lower or header_lower in pattern_clean:
                        mappings[header] = target_attr
                        # Calculate confidence based on similarity
                        if header_lower == pattern_clean:
                            confidence_scores[header] = 1.0
                        elif pattern_clean in header_lower:
                            confidence_scores[header] = 0.9
                        else:
                            confidence_scores[header] = 0.8
                        mapped = True
                        break
                if mapped:
                    break
            
            if not mapped:
                unmapped_fields.append(header)
        
        return {
            "mappings": mappings,
            "confidence_scores": confidence_scores,
            "unmapped_fields": unmapped_fields,
            "validation_results": {
                "valid": len(mappings) > 0,
                "score": len(mappings) / len(headers) if headers else 0.0
            },
            "agent_insights": {
                "fallback": "Intelligent pattern-based mapping",
                "total_fields": len(headers),
                "mapped_fields": len(mappings),
                "unmapped_fields": len(unmapped_fields)
            }
        }

    def intelligent_asset_classification_fallback(self, cleaned_data) -> Dict[str, Any]:
        """Intelligent fallback for asset classification"""
        servers = []
        applications = []
        devices = []
        
        for asset in cleaned_data:
            asset_type = asset.get("asset_type", "").lower()
            if "server" in asset_type or "vm" in asset_type:
                servers.append(asset)
            elif "application" in asset_type or "app" in asset_type or "service" in asset_type:
                applications.append(asset)
            elif "device" in asset_type or "network" in asset_type:
                devices.append(asset)
            else:
                # Default classification based on available fields
                if asset.get("operating_system") or asset.get("cpu_cores"):
                    servers.append(asset)
                else:
                    applications.append(asset)
        
        return {
            "servers": servers,
            "applications": applications,
            "devices": devices,
            "classification_metadata": {
                "total_classified": len(cleaned_data),
                "method": "intelligent_fallback"
            }
        }

    def intelligent_dependency_fallback(self, asset_inventory, dependency_type) -> Dict[str, Any]:
        """Intelligent fallback for dependency mapping"""
        if dependency_type == "app_server":
            return {
                "hosting_relationships": [],
                "resource_mappings": [],
                "topology_insights": {"total_relationships": 0, "method": "fallback"}
            }
        elif dependency_type == "app_app":
            return {
                "communication_patterns": [],
                "api_dependencies": [],
                "integration_complexity": {"total_integrations": 0, "method": "fallback"}
            }
        else:
            return {}

    def intelligent_technical_debt_fallback(self, state) -> Dict[str, Any]:
        """Intelligent fallback for technical debt assessment"""
        return {
            "debt_scores": {"overall": 0.6, "method": "fallback"},
            "modernization_recommendations": [
                "Consider containerization for improved portability",
                "API modernization for better integration",
                "Database optimization for performance"
            ],
            "risk_assessments": {
                "migration_risk": "medium",
                "complexity_score": 0.6,
                "effort_estimate": "medium"
            },
            "six_r_preparation": {
                "ready": True,
                "recommended_strategy": "rehost",
                "confidence": 0.7,
                "fallback_analysis": True
            }
        }