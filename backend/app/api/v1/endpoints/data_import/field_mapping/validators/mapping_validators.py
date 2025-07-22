"""
Validators for field mapping operations.
"""

import re
from typing import Any, Dict, List, Optional

from ..models.mapping_schemas import FieldMappingCreate, MappingValidationResponse


class MappingValidator:
    """Validator for field mapping operations."""
    
    def __init__(self):
        self.valid_target_fields = {
            # Core identity fields
            'asset_id', 'name', 'asset_name', 'hostname', 'fqdn',
            
            # Asset classification
            'asset_type', 'intelligent_asset_type', 'status',
            
            # Network information
            'ip_address', 'mac_address',
            
            # System information
            'operating_system', 'os_version',
            
            # Hardware specifications
            'cpu_cores', 'memory_gb', 'storage_gb',
            
            # Location and environment
            'location', 'datacenter', 'environment',
            
            # Business information
            'business_owner', 'technical_owner', 'department',
            'application_name', 'technology_stack',
            
            # Migration assessment
            'migration_priority', 'migration_complexity', 'criticality',
            'business_criticality',
            
            # Additional fields
            'description', 'custom_attributes'
        }
        
        self.required_fields = {
            'name', 'asset_type'
        }
    
    async def validate_mapping(self, mapping: FieldMappingCreate) -> MappingValidationResponse:
        """Validate a single field mapping."""
        errors = []
        warnings = []
        
        # Validate source field
        if not mapping.source_field or not mapping.source_field.strip():
            errors.append("Source field cannot be empty")
        elif not self._is_valid_field_name(mapping.source_field):
            errors.append(f"Invalid source field name: {mapping.source_field}")
        
        # Validate target field
        if not mapping.target_field or not mapping.target_field.strip():
            errors.append("Target field cannot be empty")
        elif mapping.target_field not in self.valid_target_fields:
            # Check if it's a custom field pattern
            if not mapping.target_field.startswith('custom_'):
                errors.append(f"Invalid target field: {mapping.target_field}")
            else:
                warnings.append(f"Using custom target field: {mapping.target_field}")
        
        # Validate confidence score
        if mapping.confidence < 0.0 or mapping.confidence > 1.0:
            errors.append("Confidence score must be between 0.0 and 1.0")
        elif mapping.confidence < 0.3:
            warnings.append("Low confidence score may indicate poor mapping quality")
        
        # Validate transformation rule syntax if provided
        if mapping.transformation_rule:
            if not self._validate_transformation_rule(mapping.transformation_rule):
                errors.append("Invalid transformation rule syntax")
        
        # Validate validation rule if provided
        if mapping.validation_rule:
            if not self._validate_validation_rule(mapping.validation_rule):
                errors.append("Invalid validation rule syntax")
        
        # Check for conflicting requirements
        if mapping.is_required and mapping.confidence < 0.5:
            warnings.append("Required mapping has low confidence score")
        
        return MappingValidationResponse(
            is_valid=len(errors) == 0,
            validation_errors=errors,
            warnings=warnings,
            validated_mappings=[]
        )
    
    def _is_valid_field_name(self, field_name: str) -> bool:
        """Check if field name is valid."""
        if not field_name:
            return False
        
        # Allow alphanumeric, underscores, hyphens, dots, and spaces
        pattern = r'^[a-zA-Z0-9_\-\.\s]+$'
        return bool(re.match(pattern, field_name))
    
    def _validate_transformation_rule(self, rule: str) -> bool:
        """Enhanced transformation rule validation using AST parsing."""
        if not rule:
            return True
        
        # Length check
        if len(rule) > 500:
            return False
        
        # Strict whitelist approach using AST parsing
        try:
            import ast
            
            # Parse as AST to check for dangerous constructs
            tree = ast.parse(rule, mode='eval')
            
            # Check for dangerous node types
            for node in ast.walk(tree):
                # Block dangerous imports and executions
                if isinstance(node, (ast.Import, ast.ImportFrom, ast.Exec)):
                    return False
                
                # Block dangerous function calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        dangerous_functions = {
                            'exec', 'eval', 'compile', '__import__', 
                            'getattr', 'setattr', 'delattr', 'hasattr',
                            'globals', 'locals', 'vars', 'dir',
                            'open', 'file', 'input', 'raw_input'
                        }
                        if node.func.id in dangerous_functions:
                            return False
                    
                    # Block attribute access to dangerous methods
                    elif isinstance(node.func, ast.Attribute):
                        dangerous_attrs = {
                            '__import__', '__builtins__', '__globals__',
                            '__locals__', '__dict__', '__class__'
                        }
                        if node.func.attr in dangerous_attrs:
                            return False
                
                # Block attribute access to dangerous attributes
                if isinstance(node, ast.Attribute):
                    dangerous_attrs = {
                        '__import__', '__builtins__', '__globals__',
                        '__locals__', '__dict__', '__class__', '__bases__',
                        '__subclasses__', '__mro__'
                    }
                    if node.attr in dangerous_attrs:
                        return False
                
                # Block subscript access to dangerous items
                if isinstance(node, ast.Subscript):
                    if isinstance(node.slice, ast.Str):
                        dangerous_keys = {
                            '__builtins__', '__globals__', '__locals__'
                        }
                        if node.slice.s in dangerous_keys:
                            return False
            
            # If we get here, the rule passed AST validation
            # Now check if it contains valid transformation patterns
            valid_patterns = [
                'upper()', 'lower()', 'strip()', 'replace(',
                'split(', 'join(', 'format(', 'int(', 'float(',
                'str(', 'len(', 'sum(', 'max(', 'min(',
                'round(', 'abs(', 'bool(', 'list(', 'tuple(',
                'set(', 'sorted(', 'reversed('
            ]
            
            rule_lower = rule.lower()
            has_valid_pattern = any(pattern in rule_lower for pattern in valid_patterns)
            
            # Simple expressions without function calls are also valid
            # (e.g., "value * 2", "value + 1", etc.)
            has_only_safe_operations = all(
                not isinstance(node, ast.Call) or 
                (isinstance(node.func, ast.Name) and 
                 node.func.id in ['int', 'float', 'str', 'len', 'bool'])
                for node in ast.walk(tree)
            )
            
            return has_valid_pattern or has_only_safe_operations
            
        except SyntaxError:
            # Invalid syntax
            return False
        except Exception:
            # Any other error during parsing
            return False
    
    def _validate_validation_rule(self, rule: str) -> bool:
        """Enhanced validation rule syntax validation."""
        if not rule:
            return True
        
        # Length check
        if len(rule) > 300:
            return False
        
        # Check for dangerous patterns
        dangerous_patterns = [
            'exec', 'eval', 'import', '__', 'getattr', 'setattr',
            'delattr', 'globals', 'locals', 'open', 'file',
            'subprocess', 'os.', 'sys.', 'shutil.'
        ]
        
        rule_lower = rule.lower()
        for pattern in dangerous_patterns:
            if pattern in rule_lower:
                return False
        
        # Valid validation rule patterns
        valid_patterns = [
            'not null', 'not empty', 'not blank',
            'length >', 'length <', 'length >=', 'length <=', 'length ==',
            'matches pattern', 'matches regex', 'in range', 'type is',
            'format:', 'regex:', 'min:', 'max:', 'between:',
            'contains:', 'starts with:', 'ends with:',
            'is number', 'is integer', 'is float', 'is string',
            'is boolean', 'is email', 'is url', 'is date',
            'required', 'optional', 'default:'
        ]
        
        # Check if rule contains valid patterns
        has_valid_pattern = any(pattern in rule_lower for pattern in valid_patterns)
        
        # Simple comparison operators are also valid
        comparison_operators = ['>', '<', '>=', '<=', '==', '!=', 'in ', 'not in ']
        has_comparison = any(op in rule_lower for op in comparison_operators)
        
        return has_valid_pattern or has_comparison
    
    def validate_field_compatibility(
        self, 
        source_field: str, 
        target_field: str,
        sample_data: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """Validate compatibility between source and target fields."""
        result = {
            'compatible': True,
            'issues': [],
            'recommendations': []
        }
        
        # Check field name compatibility
        if source_field.lower() == target_field.lower():
            result['recommendations'].append("Direct field name match - high confidence")
        
        # Check data type compatibility if sample data provided
        if sample_data and len(sample_data) > 0:
            inferred_type = self._infer_data_type(sample_data)
            target_type = self._get_target_field_type(target_field)
            
            if not self._are_types_compatible(inferred_type, target_type):
                result['compatible'] = False
                result['issues'].append(
                    f"Data type mismatch: {inferred_type} -> {target_type}"
                )
                result['recommendations'].append(
                    f"Consider transformation rule to convert {inferred_type} to {target_type}"
                )
        
        return result
    
    def _infer_data_type(self, sample_data: List[Any]) -> str:
        """Infer data type from sample data."""
        if not sample_data:
            return "unknown"
        
        # Filter out None values
        valid_data = [x for x in sample_data if x is not None]
        if not valid_data:
            return "null"
        
        # Check types
        if all(isinstance(x, bool) for x in valid_data):
            return "boolean"
        elif all(isinstance(x, int) for x in valid_data):
            return "integer"
        elif all(isinstance(x, (int, float)) for x in valid_data):
            return "numeric"
        elif all(isinstance(x, str) for x in valid_data):
            # Check if all strings look like numbers
            if all(self._is_numeric_string(x) for x in valid_data):
                return "numeric_string"
            return "string"
        else:
            return "mixed"
    
    def _is_numeric_string(self, value: str) -> bool:
        """Check if string represents a number."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _get_target_field_type(self, target_field: str) -> str:
        """Get expected data type for target field."""
        type_mapping = {
            'asset_id': 'string',
            'name': 'string',
            'asset_name': 'string',
            'hostname': 'string',
            'fqdn': 'string',
            'ip_address': 'string',
            'mac_address': 'string',
            'operating_system': 'string',
            'os_version': 'string',
            'cpu_cores': 'integer',
            'memory_gb': 'numeric',
            'storage_gb': 'numeric',
            'migration_priority': 'integer',
            'migration_complexity': 'string',
            'asset_type': 'string',
            'environment': 'string',
            'location': 'string',
            'datacenter': 'string',
            'business_owner': 'string',
            'technical_owner': 'string',
            'department': 'string',
            'application_name': 'string',
            'technology_stack': 'string',
            'criticality': 'string',
            'business_criticality': 'string',
            'description': 'string',
            'status': 'string'
        }
        
        return type_mapping.get(target_field, 'string')
    
    def _are_types_compatible(self, source_type: str, target_type: str) -> bool:
        """Check if source and target types are compatible."""
        if source_type == target_type:
            return True
        
        # Define compatible type conversions
        compatible_conversions = {
            'integer': ['numeric', 'string'],
            'numeric': ['string'],
            'numeric_string': ['numeric', 'integer', 'string'],
            'string': [],  # Strings can convert to anything with transformation
            'boolean': ['string', 'integer'],
            'mixed': []  # Mixed types need careful handling
        }
        
        return target_type in compatible_conversions.get(source_type, [])