"""
Data Transformation and Normalization Services

This module provides services for transforming raw collected data into
normalized formats and ensuring data consistency across different platforms.
"""

import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

logger = logging.getLogger(__name__)


class DataType(str, Enum):
    """Standard data types for normalization"""
    SERVER = "server"
    APPLICATION = "application"
    DATABASE = "database"
    NETWORK_DEVICE = "network_device"
    STORAGE = "storage"
    MIDDLEWARE = "middleware"
    CONTAINER = "container"
    SERVICE = "service"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"


class TransformationRule(str, Enum):
    """Transformation rule types"""
    FIELD_MAPPING = "field_mapping"
    VALUE_CONVERSION = "value_conversion"
    FIELD_SPLIT = "field_split"
    FIELD_MERGE = "field_merge"
    REGEX_EXTRACT = "regex_extract"
    CONDITIONAL = "conditional"
    CALCULATION = "calculation"
    LOOKUP = "lookup"


@dataclass
class TransformationResult:
    """Result of a data transformation operation"""
    success: bool
    transformed_data: Optional[Dict[str, Any]] = None
    validation_errors: List[str] = None
    transformation_metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []


class DataTransformationService:
    """
    Service for transforming raw collected data into standardized formats.
    
    This service handles:
    - Field mapping and renaming
    - Value conversions and formatting
    - Data structure transformations
    - Complex rule-based transformations
    """
    
    # Standard field mappings for common platforms
    STANDARD_FIELD_MAPPINGS = {
        "server": {
            "hostname": ["name", "host_name", "server_name", "computer_name", "fqdn"],
            "ip_address": ["ip", "ipaddress", "ip_addr", "primary_ip", "management_ip"],
            "operating_system": ["os", "os_name", "operating_system_name", "platform"],
            "os_version": ["os_version", "version", "os_release", "kernel_version"],
            "cpu_count": ["cpu", "cpus", "processor_count", "vcpus", "cores"],
            "memory_gb": ["memory", "ram", "total_memory", "memory_size"],
            "status": ["state", "power_state", "operational_status", "status"],
            "environment": ["env", "environment_type", "tier", "stage"],
            "location": ["datacenter", "dc", "site", "region", "zone"],
            "serial_number": ["serial", "service_tag", "asset_tag"],
            "model": ["hardware_model", "server_model", "platform_model"],
            "manufacturer": ["vendor", "make", "manufacturer_name"]
        },
        "application": {
            "app_name": ["name", "application_name", "app", "service_name"],
            "version": ["app_version", "release", "build"],
            "status": ["state", "health", "operational_status"],
            "environment": ["env", "stage", "tier"],
            "owner": ["app_owner", "business_owner", "contact"],
            "criticality": ["priority", "importance", "business_criticality"],
            "technology": ["tech_stack", "platform", "framework"],
            "url": ["endpoint", "base_url", "service_url"],
            "port": ["service_port", "listen_port", "app_port"]
        },
        "database": {
            "db_name": ["database_name", "name", "sid", "instance_name"],
            "db_type": ["engine", "database_type", "platform", "vendor"],
            "version": ["db_version", "engine_version", "release"],
            "host": ["hostname", "server", "db_host"],
            "port": ["db_port", "listen_port", "service_port"],
            "size_gb": ["database_size", "size", "allocated_storage"],
            "status": ["state", "availability", "health_status"]
        }
    }
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Data Transformation Service.
        
        Args:
            db: Database session
            context: Request context
        """
        self.db = db
        self.context = context
        self._transformation_rules: Dict[str, List[Callable]] = {}
        
    async def transform_data(
        self,
        raw_data: Dict[str, Any],
        data_type: DataType,
        source_platform: str,
        transformation_config: Optional[Dict[str, Any]] = None
    ) -> TransformationResult:
        """
        Transform raw data into normalized format.
        
        Args:
            raw_data: Raw data to transform
            data_type: Type of data being transformed
            source_platform: Source platform name
            transformation_config: Optional transformation configuration
            
        Returns:
            TransformationResult with transformed data
        """
        try:
            # Apply platform-specific transformations
            platform_transformed = await self._apply_platform_transformations(
                raw_data, source_platform
            )
            
            # Apply standard field mappings
            field_mapped = self._apply_field_mappings(
                platform_transformed, data_type
            )
            
            # Apply custom transformation rules
            if transformation_config:
                custom_transformed = await self._apply_custom_transformations(
                    field_mapped, transformation_config
                )
            else:
                custom_transformed = field_mapped
            
            # Validate transformed data
            validation_errors = self._validate_transformed_data(
                custom_transformed, data_type
            )
            
            return TransformationResult(
                success=len(validation_errors) == 0,
                transformed_data=custom_transformed,
                validation_errors=validation_errors,
                transformation_metadata={
                    "source_platform": source_platform,
                    "data_type": data_type.value,
                    "transformation_timestamp": datetime.utcnow().isoformat(),
                    "rules_applied": transformation_config.get("rules", []) if transformation_config else []
                }
            )
            
        except Exception as e:
            logger.error(f"Data transformation failed: {str(e)}")
            return TransformationResult(
                success=False,
                validation_errors=[f"Transformation error: {str(e)}"]
            )
    
    async def _apply_platform_transformations(
        self,
        data: Dict[str, Any],
        platform: str
    ) -> Dict[str, Any]:
        """Apply platform-specific transformations."""
        transformed = data.copy()
        
        # ServiceNow transformations
        if platform.lower() == "servicenow":
            transformed = self._transform_servicenow_data(transformed)
            
        # VMware transformations
        elif platform.lower() in ["vmware", "vcenter", "vmware_vcenter"]:
            transformed = self._transform_vmware_data(transformed)
            
        # AWS transformations
        elif platform.lower() == "aws":
            transformed = self._transform_aws_data(transformed)
            
        # Add more platform-specific transformations as needed
        
        return transformed
    
    def _transform_servicenow_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform ServiceNow specific data formats."""
        transformed = {}
        
        for key, value in data.items():
            # Handle ServiceNow reference fields
            if isinstance(value, dict) and "value" in value and "display_value" in value:
                # Use display value for human-readable fields
                transformed[key] = value.get("display_value", value.get("value"))
            # Handle ServiceNow datetime format
            elif key in ["sys_created_on", "sys_updated_on"] and isinstance(value, str):
                transformed[key] = self._parse_servicenow_datetime(value)
            else:
                transformed[key] = value
                
        return transformed
    
    def _transform_vmware_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform VMware specific data formats."""
        transformed = {}
        
        for key, value in data.items():
            # Convert VMware memory values (usually in MB) to GB
            if key in ["memorySizeMB", "memory_size_mb"] and isinstance(value, (int, float)):
                transformed["memory_gb"] = round(value / 1024, 2)
            # Handle VMware MoRef IDs
            elif key == "vm" and isinstance(value, dict) and "_moId" in value:
                transformed["vm_id"] = value["_moId"]
            else:
                transformed[key] = value
                
        return transformed
    
    def _transform_aws_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform AWS specific data formats."""
        transformed = {}
        
        for key, value in data.items():
            # Handle AWS tags
            if key == "Tags" and isinstance(value, list):
                transformed["tags"] = {tag["Key"]: tag["Value"] for tag in value}
            # Handle AWS instance state
            elif key == "State" and isinstance(value, dict):
                transformed["status"] = value.get("Name", "unknown")
            else:
                transformed[key] = value
                
        return transformed
    
    def _apply_field_mappings(
        self,
        data: Dict[str, Any],
        data_type: DataType
    ) -> Dict[str, Any]:
        """Apply standard field mappings based on data type."""
        if data_type.value not in self.STANDARD_FIELD_MAPPINGS:
            return data
            
        mappings = self.STANDARD_FIELD_MAPPINGS[data_type.value]
        transformed = {}
        used_fields = set()
        
        # Apply mappings
        for standard_field, possible_fields in mappings.items():
            for field in possible_fields:
                if field in data and field not in used_fields:
                    transformed[standard_field] = data[field]
                    used_fields.add(field)
                    break
        
        # Include unmapped fields
        for key, value in data.items():
            if key not in used_fields and key not in transformed:
                transformed[key] = value
                
        return transformed
    
    async def _apply_custom_transformations(
        self,
        data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply custom transformation rules."""
        transformed = data.copy()
        rules = config.get("rules", [])
        
        for rule in rules:
            rule_type = rule.get("type")
            
            if rule_type == TransformationRule.FIELD_MAPPING.value:
                transformed = self._apply_field_mapping_rule(transformed, rule)
                
            elif rule_type == TransformationRule.VALUE_CONVERSION.value:
                transformed = self._apply_value_conversion_rule(transformed, rule)
                
            elif rule_type == TransformationRule.FIELD_SPLIT.value:
                transformed = self._apply_field_split_rule(transformed, rule)
                
            elif rule_type == TransformationRule.FIELD_MERGE.value:
                transformed = self._apply_field_merge_rule(transformed, rule)
                
            elif rule_type == TransformationRule.REGEX_EXTRACT.value:
                transformed = self._apply_regex_extract_rule(transformed, rule)
                
            elif rule_type == TransformationRule.CONDITIONAL.value:
                transformed = self._apply_conditional_rule(transformed, rule)
                
        return transformed
    
    def _apply_field_mapping_rule(
        self,
        data: Dict[str, Any],
        rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply field mapping transformation rule."""
        source_field = rule.get("source_field")
        target_field = rule.get("target_field")
        
        if source_field in data:
            data[target_field] = data[source_field]
            if rule.get("remove_source", False):
                del data[source_field]
                
        return data
    
    def _apply_value_conversion_rule(
        self,
        data: Dict[str, Any],
        rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply value conversion transformation rule."""
        field = rule.get("field")
        conversion_type = rule.get("conversion_type")
        
        if field in data:
            value = data[field]
            
            if conversion_type == "uppercase":
                data[field] = str(value).upper()
            elif conversion_type == "lowercase":
                data[field] = str(value).lower()
            elif conversion_type == "int":
                try:
                    data[field] = int(value)
                except (ValueError, TypeError):
                    pass
            elif conversion_type == "float":
                try:
                    data[field] = float(value)
                except (ValueError, TypeError):
                    pass
            elif conversion_type == "bool":
                data[field] = str(value).lower() in ["true", "yes", "1", "on"]
            elif conversion_type == "bytes_to_gb":
                try:
                    data[field] = round(float(value) / (1024**3), 2)
                except (ValueError, TypeError):
                    pass
                    
        return data
    
    def _apply_field_split_rule(
        self,
        data: Dict[str, Any],
        rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply field split transformation rule."""
        source_field = rule.get("source_field")
        delimiter = rule.get("delimiter", " ")
        target_fields = rule.get("target_fields", [])
        
        if source_field in data and isinstance(data[source_field], str):
            parts = data[source_field].split(delimiter)
            for i, target_field in enumerate(target_fields):
                if i < len(parts):
                    data[target_field] = parts[i].strip()
                    
        return data
    
    def _apply_field_merge_rule(
        self,
        data: Dict[str, Any],
        rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply field merge transformation rule."""
        source_fields = rule.get("source_fields", [])
        target_field = rule.get("target_field")
        delimiter = rule.get("delimiter", " ")
        
        values = []
        for field in source_fields:
            if field in data and data[field]:
                values.append(str(data[field]))
                
        if values:
            data[target_field] = delimiter.join(values)
            
        return data
    
    def _apply_regex_extract_rule(
        self,
        data: Dict[str, Any],
        rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply regex extraction transformation rule."""
        source_field = rule.get("source_field")
        pattern = rule.get("pattern")
        target_field = rule.get("target_field")
        
        if source_field in data and pattern:
            try:
                match = re.search(pattern, str(data[source_field]))
                if match:
                    if match.groups():
                        data[target_field] = match.group(1)
                    else:
                        data[target_field] = match.group(0)
            except re.error:
                logger.error(f"Invalid regex pattern: {pattern}")
                
        return data
    
    def _apply_conditional_rule(
        self,
        data: Dict[str, Any],
        rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply conditional transformation rule."""
        condition = rule.get("condition", {})
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")
        
        if field in data:
            field_value = data[field]
            condition_met = False
            
            if operator == "equals":
                condition_met = field_value == value
            elif operator == "not_equals":
                condition_met = field_value != value
            elif operator == "contains":
                condition_met = str(value) in str(field_value)
            elif operator == "greater_than":
                try:
                    condition_met = float(field_value) > float(value)
                except (ValueError, TypeError):
                    pass
            elif operator == "less_than":
                try:
                    condition_met = float(field_value) < float(value)
                except (ValueError, TypeError):
                    pass
                    
            if condition_met:
                # Apply transformation if condition is met
                transform = rule.get("transform", {})
                target_field = transform.get("field")
                target_value = transform.get("value")
                if target_field:
                    data[target_field] = target_value
                    
        return data
    
    def _validate_transformed_data(
        self,
        data: Dict[str, Any],
        data_type: DataType
    ) -> List[str]:
        """Validate transformed data for completeness and correctness."""
        errors = []
        
        # Define required fields by data type
        required_fields = {
            DataType.SERVER: ["hostname", "ip_address", "operating_system"],
            DataType.APPLICATION: ["app_name", "version"],
            DataType.DATABASE: ["db_name", "db_type", "host"]
        }
        
        # Check required fields
        if data_type in required_fields:
            for field in required_fields[data_type]:
                if field not in data or not data[field]:
                    errors.append(f"Required field '{field}' is missing or empty")
        
        # Validate field formats
        if "ip_address" in data:
            if not self._is_valid_ip(data["ip_address"]):
                errors.append(f"Invalid IP address format: {data['ip_address']}")
                
        if "memory_gb" in data:
            try:
                memory = float(data["memory_gb"])
                if memory < 0:
                    errors.append("Memory value cannot be negative")
            except (ValueError, TypeError):
                errors.append(f"Invalid memory value: {data['memory_gb']}")
                
        return errors
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        try:
            parts = ip.split(".")
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except (ValueError, AttributeError):
            return False
    
    def _parse_servicenow_datetime(self, datetime_str: str) -> str:
        """Parse ServiceNow datetime format to ISO format."""
        try:
            # ServiceNow format: YYYY-MM-DD HH:MM:SS
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            return dt.isoformat()
        except ValueError:
            return datetime_str


class DataNormalizationService:
    """
    Service for normalizing data values and ensuring consistency.
    
    This service handles:
    - Value standardization (e.g., status values, boolean conversions)
    - Unit conversions (e.g., storage sizes, memory)
    - Format standardization (e.g., dates, hostnames)
    - Data deduplication and consolidation
    """
    
    # Standard status mappings
    STATUS_MAPPINGS = {
        "running": ["running", "active", "online", "up", "started", "healthy", "ok"],
        "stopped": ["stopped", "inactive", "offline", "down", "shutdown", "halted"],
        "error": ["error", "failed", "fault", "critical", "unhealthy"],
        "warning": ["warning", "degraded", "impaired", "alert"],
        "unknown": ["unknown", "undefined", "n/a", "not available"]
    }
    
    # Standard environment mappings
    ENVIRONMENT_MAPPINGS = {
        "production": ["production", "prod", "prd", "live"],
        "staging": ["staging", "stage", "stg", "uat", "preprod", "pre-prod"],
        "development": ["development", "dev", "develop"],
        "test": ["test", "testing", "tst", "qa"],
        "disaster_recovery": ["dr", "disaster recovery", "backup"]
    }
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Data Normalization Service.
        
        Args:
            db: Database session
            context: Request context
        """
        self.db = db
        self.context = context
        
    async def normalize_dataset(
        self,
        dataset: List[Dict[str, Any]],
        data_type: DataType,
        normalization_config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Normalize a complete dataset.
        
        Args:
            dataset: List of data records to normalize
            data_type: Type of data being normalized
            normalization_config: Optional normalization configuration
            
        Returns:
            List of normalized data records
        """
        normalized_data = []
        
        for record in dataset:
            normalized_record = await self.normalize_record(
                record, data_type, normalization_config
            )
            normalized_data.append(normalized_record)
            
        # Remove duplicates if configured
        if normalization_config and normalization_config.get("remove_duplicates", False):
            normalized_data = self._remove_duplicates(
                normalized_data,
                normalization_config.get("duplicate_key_fields", ["hostname"])
            )
            
        return normalized_data
    
    async def normalize_record(
        self,
        record: Dict[str, Any],
        data_type: DataType,
        normalization_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Normalize a single data record.
        
        Args:
            record: Data record to normalize
            data_type: Type of data being normalized
            normalization_config: Optional normalization configuration
            
        Returns:
            Normalized data record
        """
        normalized = record.copy()
        
        # Apply standard normalizations
        normalized = self._normalize_status_values(normalized)
        normalized = self._normalize_environment_values(normalized)
        normalized = self._normalize_boolean_values(normalized)
        normalized = self._normalize_memory_values(normalized)
        normalized = self._normalize_storage_values(normalized)
        normalized = self._normalize_hostnames(normalized)
        normalized = self._normalize_dates(normalized)
        
        # Apply data type specific normalizations
        if data_type == DataType.SERVER:
            normalized = self._normalize_server_data(normalized)
        elif data_type == DataType.APPLICATION:
            normalized = self._normalize_application_data(normalized)
        elif data_type == DataType.DATABASE:
            normalized = self._normalize_database_data(normalized)
            
        # Apply custom normalizations
        if normalization_config and "custom_rules" in normalization_config:
            normalized = self._apply_custom_normalizations(
                normalized, normalization_config["custom_rules"]
            )
            
        return normalized
    
    def _normalize_status_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize status values to standard terms."""
        status_fields = ["status", "state", "power_state", "operational_status", "health"]
        
        for field in status_fields:
            if field in data and data[field]:
                value = str(data[field]).lower().strip()
                for standard_status, variations in self.STATUS_MAPPINGS.items():
                    if value in variations:
                        data[field] = standard_status
                        break
                        
        return data
    
    def _normalize_environment_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize environment values to standard terms."""
        env_fields = ["environment", "env", "tier", "stage"]
        
        for field in env_fields:
            if field in data and data[field]:
                value = str(data[field]).lower().strip()
                for standard_env, variations in self.ENVIRONMENT_MAPPINGS.items():
                    if value in variations:
                        data[field] = standard_env
                        break
                        
        return data
    
    def _normalize_boolean_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize boolean values."""
        boolean_true = ["true", "yes", "y", "1", "on", "enabled", "active"]
        boolean_false = ["false", "no", "n", "0", "off", "disabled", "inactive"]
        
        for key, value in data.items():
            if isinstance(value, str):
                value_lower = value.lower().strip()
                if value_lower in boolean_true:
                    data[key] = True
                elif value_lower in boolean_false:
                    data[key] = False
                    
        return data
    
    def _normalize_memory_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize memory values to GB."""
        memory_fields = ["memory", "memory_gb", "ram", "total_memory"]
        
        for field in memory_fields:
            if field in data:
                value = data[field]
                if isinstance(value, str):
                    # Extract numeric value and unit
                    match = re.match(r"(\d+\.?\d*)\s*([A-Za-z]+)?", value)
                    if match:
                        num = float(match.group(1))
                        unit = match.group(2).upper() if match.group(2) else "GB"
                        
                        # Convert to GB
                        if unit == "MB":
                            data[field] = round(num / 1024, 2)
                        elif unit == "KB":
                            data[field] = round(num / (1024 * 1024), 2)
                        elif unit == "TB":
                            data[field] = round(num * 1024, 2)
                        else:
                            data[field] = round(num, 2)
                            
        return data
    
    def _normalize_storage_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize storage values to GB."""
        storage_fields = ["disk", "storage", "disk_size", "storage_gb", "size_gb"]
        
        for field in storage_fields:
            if field in data:
                value = data[field]
                if isinstance(value, str):
                    # Extract numeric value and unit
                    match = re.match(r"(\d+\.?\d*)\s*([A-Za-z]+)?", value)
                    if match:
                        num = float(match.group(1))
                        unit = match.group(2).upper() if match.group(2) else "GB"
                        
                        # Convert to GB
                        if unit == "MB":
                            data[field] = round(num / 1024, 2)
                        elif unit == "TB":
                            data[field] = round(num * 1024, 2)
                        else:
                            data[field] = round(num, 2)
                            
        return data
    
    def _normalize_hostnames(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize hostname formats."""
        hostname_fields = ["hostname", "host_name", "server_name", "fqdn"]
        
        for field in hostname_fields:
            if field in data and data[field]:
                # Convert to lowercase and strip whitespace
                data[field] = str(data[field]).lower().strip()
                
                # Remove common domain suffixes if not FQDN field
                if field != "fqdn" and "." in data[field]:
                    data[field] = data[field].split(".")[0]
                    
        return data
    
    def _normalize_dates(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize date formats to ISO 8601."""
        date_fields = ["created_at", "updated_at", "last_seen", "discovered_at"]
        
        for field in date_fields:
            if field in data and data[field]:
                normalized_date = self._parse_date(data[field])
                if normalized_date:
                    data[field] = normalized_date
                    
        return data
    
    def _parse_date(self, date_value: Any) -> Optional[str]:
        """Parse various date formats to ISO 8601."""
        if isinstance(date_value, datetime):
            return date_value.isoformat()
            
        if isinstance(date_value, str):
            # Try common date formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%m-%d-%Y",
                "%d-%m-%Y"
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_value, fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
                    
        return None
    
    def _normalize_server_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply server-specific normalizations."""
        # Normalize CPU count
        if "cpu_count" in data:
            try:
                data["cpu_count"] = int(data["cpu_count"])
            except (ValueError, TypeError):
                pass
                
        # Normalize OS names
        if "operating_system" in data and data["operating_system"]:
            os_name = str(data["operating_system"]).lower()
            if "windows" in os_name:
                data["os_family"] = "windows"
            elif "linux" in os_name or "ubuntu" in os_name or "centos" in os_name:
                data["os_family"] = "linux"
            elif "aix" in os_name:
                data["os_family"] = "aix"
            elif "solaris" in os_name:
                data["os_family"] = "solaris"
            else:
                data["os_family"] = "other"
                
        return data
    
    def _normalize_application_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply application-specific normalizations."""
        # Normalize criticality values
        if "criticality" in data and data["criticality"]:
            criticality = str(data["criticality"]).lower()
            criticality_map = {
                "critical": ["critical", "high", "1", "mission critical"],
                "high": ["important", "2", "business critical"],
                "medium": ["medium", "moderate", "3", "standard"],
                "low": ["low", "minimal", "4", "non-critical"]
            }
            
            for standard, variations in criticality_map.items():
                if criticality in variations:
                    data["criticality"] = standard
                    break
                    
        return data
    
    def _normalize_database_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply database-specific normalizations."""
        # Normalize database types
        if "db_type" in data and data["db_type"]:
            db_type = str(data["db_type"]).lower()
            type_map = {
                "oracle": ["oracle", "ora", "oracle database"],
                "mysql": ["mysql", "mariadb"],
                "postgresql": ["postgresql", "postgres", "pg"],
                "sqlserver": ["sql server", "mssql", "microsoft sql server"],
                "mongodb": ["mongodb", "mongo"],
                "redis": ["redis", "redis cache"],
                "elasticsearch": ["elasticsearch", "elastic"]
            }
            
            for standard, variations in type_map.items():
                if any(var in db_type for var in variations):
                    data["db_type"] = standard
                    break
                    
        return data
    
    def _apply_custom_normalizations(
        self,
        data: Dict[str, Any],
        rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply custom normalization rules."""
        for rule in rules:
            field = rule.get("field")
            normalization_type = rule.get("type")
            
            if field in data:
                if normalization_type == "uppercase":
                    data[field] = str(data[field]).upper()
                elif normalization_type == "lowercase":
                    data[field] = str(data[field]).lower()
                elif normalization_type == "trim":
                    data[field] = str(data[field]).strip()
                elif normalization_type == "replace":
                    old_value = rule.get("old_value")
                    new_value = rule.get("new_value")
                    if old_value and new_value:
                        data[field] = str(data[field]).replace(old_value, new_value)
                        
        return data
    
    def _remove_duplicates(
        self,
        dataset: List[Dict[str, Any]],
        key_fields: List[str]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate records based on key fields."""
        seen = set()
        unique_data = []
        
        for record in dataset:
            # Create composite key from specified fields
            key_values = []
            for field in key_fields:
                if field in record:
                    key_values.append(str(record[field]))
                    
            if key_values:
                key = "|".join(key_values)
                if key not in seen:
                    seen.add(key)
                    unique_data.append(record)
                    
        return unique_data