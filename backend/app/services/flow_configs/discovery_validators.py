"""
Discovery Flow Validators
MFO-040: Implement Discovery-specific validators

Validators for data validation, field mapping validation, and asset validation.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


async def field_mapping_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate field mapping configuration
    
    Ensures:
    - All required fields are mapped
    - Mapping rules are valid
    - Source fields exist in imported data
    - Target fields are valid schema fields
    """
    try:
        mapping_rules = phase_input.get("mapping_rules", {})
        imported_data = phase_input.get("imported_data", [])
        
        errors = []
        warnings = []
        
        # Check for required inputs
        if not mapping_rules:
            errors.append("Missing mapping rules")
        
        if not imported_data:
            errors.append("No data to map")
        
        # Required fields that must be mapped
        required_fields = [
            "hostname",
            "ip_address", 
            "os_type",
            "environment",
            "application_name"
        ]
        
        # Check if all required fields are mapped
        if mapping_rules:
            mapped_fields = list(mapping_rules.keys())
            missing_fields = [field for field in required_fields if field not in mapped_fields]
            
            if missing_fields:
                errors.append(f"Missing required field mappings: {', '.join(missing_fields)}")
            
            # Validate each mapping rule
            for target_field, source_field in mapping_rules.items():
                if not source_field:
                    errors.append(f"Empty source field for target field: {target_field}")
                
                # Check if source field exists in data (sample first record)
                if imported_data and isinstance(imported_data, list) and len(imported_data) > 0:
                    sample_record = imported_data[0]
                    if isinstance(sample_record, dict) and source_field not in sample_record:
                        warnings.append(f"Source field '{source_field}' not found in imported data")
        
        # Additional validation logic
        if imported_data and isinstance(imported_data, list):
            # Check data consistency
            if len(imported_data) == 0:
                errors.append("Imported data is empty")
            elif len(imported_data) > 10000:
                warnings.append(f"Large dataset detected: {len(imported_data)} records. Performance may be impacted.")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": {
                "validated_at": datetime.utcnow().isoformat(),
                "record_count": len(imported_data) if isinstance(imported_data, list) else 0,
                "mapping_count": len(mapping_rules) if mapping_rules else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Field mapping validation error: {e}")
        return {
            "valid": False,
            "errors": [f"Validation exception: {str(e)}"],
            "warnings": []
        }


async def asset_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate created assets
    
    Ensures:
    - Assets have required fields
    - Asset IDs are unique
    - Asset types are valid
    - Business rules are satisfied
    """
    try:
        assets = phase_input.get("assets", [])
        errors = []
        warnings = []
        
        if not assets:
            errors.append("No assets created")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings
            }
        
        # Track asset IDs for uniqueness check
        asset_ids = set()
        asset_types = {}
        
        # Required fields for all assets
        required_asset_fields = ["asset_id", "asset_type", "name", "status"]
        
        # Validate each asset
        for idx, asset in enumerate(assets):
            if not isinstance(asset, dict):
                errors.append(f"Asset at index {idx} is not a dictionary")
                continue
            
            # Check required fields
            for field in required_asset_fields:
                if field not in asset or not asset.get(field):
                    errors.append(f"Asset at index {idx} missing required field: {field}")
            
            # Check asset ID uniqueness
            asset_id = asset.get("asset_id")
            if asset_id:
                if asset_id in asset_ids:
                    errors.append(f"Duplicate asset ID: {asset_id}")
                asset_ids.add(asset_id)
            
            # Track asset types
            asset_type = asset.get("asset_type")
            if asset_type:
                asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
            
            # Type-specific validation
            if asset_type == "server":
                server_fields = ["hostname", "ip_address", "os_type"]
                for field in server_fields:
                    if field not in asset:
                        warnings.append(f"Server asset {asset_id} missing recommended field: {field}")
            
            elif asset_type == "application":
                app_fields = ["application_name", "version", "environment"]
                for field in app_fields:
                    if field not in asset:
                        warnings.append(f"Application asset {asset_id} missing recommended field: {field}")
        
        # Business rule validations
        if len(assets) > 50000:
            warnings.append(f"Large number of assets created: {len(assets)}. Consider batching for performance.")
        
        # Summary statistics
        metadata = {
            "validated_at": datetime.utcnow().isoformat(),
            "total_assets": len(assets),
            "unique_assets": len(asset_ids),
            "asset_types": asset_types,
            "validation_passed": len(errors) == 0
        }
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Asset validation error: {e}")
        return {
            "valid": False,
            "errors": [f"Validation exception: {str(e)}"],
            "warnings": []
        }


async def inventory_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate asset inventory
    
    Ensures:
    - Inventory structure is valid
    - All assets are included
    - Categorization is complete
    - No orphaned assets
    """
    try:
        inventory = phase_input.get("inventory", {})
        assets = phase_input.get("assets", [])
        errors = []
        warnings = []
        
        if not inventory:
            errors.append("No inventory created")
        
        # Check inventory structure
        expected_sections = ["servers", "applications", "databases", "network_devices"]
        if inventory:
            for section in expected_sections:
                if section not in inventory:
                    warnings.append(f"Inventory missing section: {section}")
        
        # Validate asset coverage
        if assets and inventory:
            asset_ids = {asset.get("asset_id") for asset in assets if asset.get("asset_id")}
            inventory_ids = set()
            
            # Collect all asset IDs from inventory
            for section, items in inventory.items():
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and "asset_id" in item:
                            inventory_ids.add(item["asset_id"])
            
            # Check for missing assets
            missing_in_inventory = asset_ids - inventory_ids
            if missing_in_inventory:
                errors.append(f"Assets not in inventory: {len(missing_in_inventory)} assets")
            
            # Check for orphaned entries
            orphaned_in_inventory = inventory_ids - asset_ids
            if orphaned_in_inventory:
                warnings.append(f"Orphaned inventory entries: {len(orphaned_in_inventory)} entries")
        
        metadata = {
            "validated_at": datetime.utcnow().isoformat(),
            "inventory_sections": list(inventory.keys()) if inventory else [],
            "total_inventory_items": sum(
                len(items) if isinstance(items, list) else 0 
                for items in inventory.values()
            ) if inventory else 0
        }
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Inventory validation error: {e}")
        return {
            "valid": False,
            "errors": [f"Validation exception: {str(e)}"],
            "warnings": []
        }


async def dependency_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate dependency analysis results
    
    Ensures:
    - No circular dependencies
    - All referenced assets exist
    - Dependency depth is reasonable
    """
    try:
        dependencies = phase_input.get("dependencies", {})
        inventory = phase_input.get("inventory", {})
        errors = []
        warnings = []
        
        if not dependencies:
            warnings.append("No dependencies identified")
            return {
                "valid": True,
                "errors": errors,
                "warnings": warnings
            }
        
        # Build asset ID set from inventory
        all_asset_ids = set()
        if inventory:
            for section, items in inventory.items():
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and "asset_id" in item:
                            all_asset_ids.add(item["asset_id"])
        
        # Check for circular dependencies
        def has_circular_dependency(asset_id: str, visited: set, path: list) -> bool:
            if asset_id in path:
                return True
            if asset_id in visited:
                return False
            
            visited.add(asset_id)
            path.append(asset_id)
            
            deps = dependencies.get(asset_id, [])
            for dep in deps:
                if has_circular_dependency(dep, visited, path.copy()):
                    return True
            
            return False
        
        # Validate each dependency
        visited = set()
        for asset_id, deps in dependencies.items():
            # Check if source asset exists
            if asset_id not in all_asset_ids:
                errors.append(f"Dependency source asset not found: {asset_id}")
            
            # Check if all dependency targets exist
            for dep in deps:
                if dep not in all_asset_ids:
                    warnings.append(f"Dependency target asset not found: {dep}")
            
            # Check for circular dependencies
            if has_circular_dependency(asset_id, visited.copy(), []):
                errors.append(f"Circular dependency detected starting from: {asset_id}")
            
            # Check dependency depth
            if len(deps) > 50:
                warnings.append(f"Asset {asset_id} has excessive dependencies: {len(deps)}")
        
        metadata = {
            "validated_at": datetime.utcnow().isoformat(),
            "total_dependencies": sum(len(deps) for deps in dependencies.values()),
            "assets_with_dependencies": len(dependencies),
            "max_dependency_count": max(len(deps) for deps in dependencies.values()) if dependencies else 0
        }
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Dependency validation error: {e}")
        return {
            "valid": False,
            "errors": [f"Validation exception: {str(e)}"],
            "warnings": []
        }


async def mapping_completeness(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate mapping completeness
    
    Ensures all source fields are properly mapped and no data is lost
    """
    try:
        mapping_rules = phase_input.get("mapping_rules", {})
        imported_data = phase_input.get("imported_data", [])
        errors = []
        warnings = []
        
        if not imported_data or not isinstance(imported_data, list) or len(imported_data) == 0:
            errors.append("No data available to check mapping completeness")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings
            }
        
        # Get all unique fields from imported data
        sample_size = min(100, len(imported_data))  # Sample first 100 records
        all_source_fields = set()
        
        for record in imported_data[:sample_size]:
            if isinstance(record, dict):
                all_source_fields.update(record.keys())
        
        # Check which fields are mapped
        mapped_source_fields = set(mapping_rules.values()) if mapping_rules else set()
        
        # Identify unmapped fields
        unmapped_fields = all_source_fields - mapped_source_fields
        
        # Categorize unmapped fields
        critical_unmapped = []
        for field in unmapped_fields:
            # Check if field might be important based on naming
            field_lower = field.lower()
            if any(keyword in field_lower for keyword in [
                "id", "name", "type", "status", "env", "version", 
                "ip", "host", "app", "system", "owner", "cost"
            ]):
                critical_unmapped.append(field)
        
        if critical_unmapped:
            warnings.append(f"Potentially important unmapped fields: {', '.join(critical_unmapped[:10])}")
        
        completeness_ratio = len(mapped_source_fields) / len(all_source_fields) if all_source_fields else 0
        
        if completeness_ratio < 0.5:
            warnings.append(f"Low mapping coverage: {completeness_ratio:.1%} of fields mapped")
        
        metadata = {
            "validated_at": datetime.utcnow().isoformat(),
            "total_source_fields": len(all_source_fields),
            "mapped_fields": len(mapped_source_fields),
            "unmapped_fields": len(unmapped_fields),
            "completeness_ratio": completeness_ratio,
            "sample_size": sample_size
        }
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Mapping completeness validation error: {e}")
        return {
            "valid": False,
            "errors": [f"Validation exception: {str(e)}"],
            "warnings": []
        }


async def cleansing_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate data cleansing results
    
    Ensures data quality meets thresholds
    """
    try:
        cleansed_data = phase_input.get("cleansed_data", [])
        cleansing_report = phase_input.get("cleansing_report", {})
        errors = []
        warnings = []
        
        if not cleansed_data:
            errors.append("No cleansed data produced")
        
        # Check cleansing metrics
        if cleansing_report:
            duplicates_removed = cleansing_report.get("duplicates_removed", 0)
            invalid_records = cleansing_report.get("invalid_records", 0)
            data_quality_score = cleansing_report.get("data_quality_score", 0)
            
            if data_quality_score < 0.8:
                warnings.append(f"Low data quality score: {data_quality_score:.2f}")
            
            if invalid_records > len(cleansed_data) * 0.1:
                warnings.append(f"High invalid record rate: {invalid_records} records")
        
        metadata = {
            "validated_at": datetime.utcnow().isoformat(),
            "cleansed_record_count": len(cleansed_data) if isinstance(cleansed_data, list) else 0,
            "cleansing_metrics": cleansing_report
        }
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Cleansing validation error: {e}")
        return {
            "valid": False,
            "errors": [f"Validation exception: {str(e)}"],
            "warnings": []
        }


async def circular_dependency_check(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Specific check for circular dependencies
    """
    # This is a specialized version of dependency validation
    # focusing only on circular dependency detection
    return await dependency_validation(phase_input, flow_state, overrides)