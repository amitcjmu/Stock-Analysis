"""
Field Type Metadata Configuration - Issue #1261

Defines field types and constraints to prevent LLM hallucination of incorrect answer choices.
Fields listed here with field_type="text" will NOT have dropdown options generated.
This is the authoritative source for field input types.

Separated from field_options.py to keep files under 400 lines per project guidelines.
"""

# Issue #1261: Field Type Metadata Configuration
FIELD_TYPE_METADATA = {
    # Network/Identity fields - MUST be text inputs, not dropdowns
    "ip_address": {
        "field_type": "text",
        "max_length": 45,  # IPv6 can be up to 45 chars
        "validation_pattern": r"^[\d.:a-fA-F]+$",
        "placeholder": "e.g., 192.168.1.100 or 2001:db8::1",
        "help_text": "Enter the IP address (IPv4 or IPv6)",
    },
    "hostname": {
        "field_type": "text",
        "max_length": 253,
        "validation_pattern": r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$",
        "placeholder": "e.g., server01",
        "help_text": "Enter the hostname (letters, numbers, hyphens only)",
    },
    "fqdn": {
        "field_type": "text",
        "max_length": 253,
        "validation_pattern": r"^[a-zA-Z0-9]([a-zA-Z0-9\-\.]{0,251}[a-zA-Z0-9])?$",
        "placeholder": "e.g., server01.example.com",
        "help_text": "Enter the fully qualified domain name",
    },
    "mac_address": {
        "field_type": "text",
        "max_length": 17,
        "validation_pattern": r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
        "placeholder": "e.g., 00:1A:2B:3C:4D:5E",
        "help_text": "Enter MAC address in format XX:XX:XX:XX:XX:XX",
    },
    "asset_name": {
        "field_type": "text",
        "max_length": 255,
        "placeholder": "e.g., Finance Application Server",
        "help_text": "Enter a descriptive name for the asset",
    },
    "application_name": {
        "field_type": "text",
        "max_length": 255,
        "placeholder": "e.g., SAP ERP, Oracle EBS",
        "help_text": "Enter the application name",
    },
    "description": {
        "field_type": "textarea",
        "max_length": 2000,
        "placeholder": "Describe the purpose and function of this asset...",
        "help_text": "Provide a detailed description",
    },
    # Numeric fields - MUST use predefined options from FIELD_OPTIONS
    "cpu_cores": {
        "field_type": "select",
        "use_field_options": True,
        "help_text": "Select the number of CPU cores/vCPUs",
    },
    "memory_gb": {
        "field_type": "select",
        "use_field_options": True,
        "help_text": "Select the amount of RAM in GB",
    },
    "storage_gb": {
        "field_type": "select",
        "use_field_options": True,
        "help_text": "Select the storage capacity in GB",
    },
    # Business fields - can be text or select based on context
    "business_owner": {
        "field_type": "select",
        "use_field_options": True,
        "help_text": "Select the business owner role/level",
    },
    "department": {
        "field_type": "text",
        "max_length": 100,
        "placeholder": "e.g., Finance, IT, Human Resources",
        "help_text": "Enter the department name",
    },
}
