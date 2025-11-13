"""
Critical Attributes Framework Configuration

Defines the 22 critical attributes for migration assessment,
organized by category: infrastructure, application, business, technical_debt
"""

from ..enums import FieldType

# Critical Attributes Framework (22 attributes as defined in specifications)
CRITICAL_ATTRIBUTES_CONFIG = {
    # Infrastructure Attributes (6)
    "os_version": {
        "category": "infrastructure",
        "weight": 0.05,
        "label": "Operating System & Version",
        "description": "Operating system type and version information",
        "field_type": FieldType.SELECT,
        "business_impact": "Required for compatibility assessment and migration strategy",
    },
    "specifications": {
        "category": "infrastructure",
        "weight": 0.05,
        "label": "CPU/Memory/Storage Specifications",
        "description": "Hardware specifications and resource requirements",
        "field_type": FieldType.TEXTAREA,
        "business_impact": "Required for rightsizing and cost optimization",
    },
    "network_config": {
        "category": "infrastructure",
        "weight": 0.04,
        "label": "Network Configuration",
        "description": "Network topology, ports, protocols, and connectivity requirements",
        "field_type": FieldType.TEXTAREA,
        "business_impact": "Required for connectivity planning and security assessment",
    },
    "virtualization": {
        "category": "infrastructure",
        "weight": 0.04,
        "label": "Virtualization Platform",
        "description": "Current virtualization technology and configuration",
        "field_type": FieldType.SELECT,
        "business_impact": "Required for migration strategy selection",
    },
    "performance_baseline": {
        "category": "infrastructure",
        "weight": 0.04,
        "label": "Performance Baseline",
        "description": "Current performance metrics and benchmarks",
        "field_type": FieldType.TEXTAREA,
        "business_impact": "Required for performance validation post-migration",
    },
    "availability_requirements": {
        "category": "infrastructure",
        "weight": 0.03,
        "label": "Availability/Uptime Requirements",
        "description": "SLA requirements and uptime expectations",
        "field_type": FieldType.SELECT,
        "business_impact": "Required for SLA planning and architecture decisions",
    },
    # Application Attributes (8)
    "technology_stack": {
        "category": "application",
        "weight": 0.08,
        "label": "Technology Stack",
        "description": "Programming languages, frameworks, runtime versions",
        "field_type": FieldType.MULTISELECT,
        "business_impact": "Critical for modernization path selection",
    },
    "architecture_pattern": {
        "category": "application",
        "weight": 0.07,
        "label": "Architecture Pattern",
        "description": "Application architecture classification",
        "field_type": FieldType.RADIO,
        "business_impact": "Determines refactoring vs replatforming approach",
    },
    "integration_dependencies": {
        "category": "application",
        "weight": 0.06,
        "label": "Integration Dependencies",
        "description": "External APIs, databases, message queues, and service dependencies",
        "field_type": FieldType.TEXTAREA,
        "business_impact": "Critical for dependency mapping and migration ordering",
    },
    "data_characteristics": {
        "category": "application",
        "weight": 0.06,
        "label": "Data Volume and Characteristics",
        "description": "Database size, file storage, data types, and growth patterns",
        "field_type": FieldType.TEXTAREA,
        "business_impact": "Required for storage planning and data migration strategy",
    },
    "user_load_patterns": {
        "category": "application",
        "weight": 0.05,
        "label": "User Load Patterns",
        "description": "Concurrent users, peak usage times, seasonal patterns",
        "field_type": FieldType.TEXTAREA,
        "business_impact": "Required for capacity planning and scaling strategy",
    },
    "business_logic_complexity": {
        "category": "application",
        "weight": 0.05,
        "label": "Custom Business Logic Complexity",
        "description": "Proprietary algorithms, complex business rules, custom workflows",
        "field_type": FieldType.TEXTAREA,
        "business_impact": "Determines refactoring effort and cloud-native potential",
    },
    "configuration_complexity": {
        "category": "application",
        "weight": 0.04,
        "label": "Configuration Complexity",
        "description": "Environment-specific settings, feature flags, deployment configurations",
        "field_type": FieldType.TEXTAREA,
        "business_impact": "Impacts containerization and automation potential",
    },
    "security_requirements": {
        "category": "application",
        "weight": 0.04,
        "label": "Security and Compliance Requirements",
        "description": "Security protocols, regulatory constraints, data protection requirements",
        "field_type": FieldType.MULTISELECT,
        "business_impact": "Determines cloud security posture and compliance validation",
    },
    # Business Context Attributes (4)
    "business_criticality": {
        "category": "business",
        "weight": 0.08,
        "label": "Business Criticality Score",
        "description": "Revenue impact, operational importance, and business dependency",
        "field_type": FieldType.SELECT,
        "business_impact": "Determines migration priority and risk tolerance",
    },
    "change_tolerance": {
        "category": "business",
        "weight": 0.05,
        "label": "Change Tolerance",
        "description": "User adaptability, training requirements, change management needs",
        "field_type": FieldType.SELECT,
        "business_impact": "Influences modernization approach and timeline",
    },
    "compliance_constraints": {
        "category": "business",
        "weight": 0.04,
        "label": "Compliance and Regulatory Constraints",
        "description": "Industry-specific requirements, regulatory compliance needs",
        "field_type": FieldType.MULTISELECT,
        "business_impact": "Determines cloud region and compliance validation requirements",
    },
    "stakeholder_impact": {
        "category": "business",
        "weight": 0.03,
        "label": "Stakeholder Impact Analysis",
        "description": "User base size, organizational dependencies, communication needs",
        "field_type": FieldType.TEXTAREA,
        "business_impact": "Influences change management and communication strategy",
    },
    # Technical Debt Attributes (4)
    "code_quality": {
        "category": "technical_debt",
        "weight": 0.03,
        "label": "Code Quality Metrics",
        "description": "Maintainability index, technical debt ratio, code coverage",
        "field_type": FieldType.TEXTAREA,
        "business_impact": "Determines refactoring effort and modernization feasibility",
    },
    "security_vulnerabilities": {
        "category": "technical_debt",
        "weight": 0.03,
        "label": "Security Vulnerability Assessment",
        "description": "CVE count, severity classification, security scan results",
        "field_type": FieldType.SELECT,  # Issue #886: Changed to SELECT for intelligent options
        "business_impact": "Critical for security posture and remediation planning",
    },
    "eol_technology": {
        "category": "technical_debt",
        "weight": 0.02,
        "label": "End-of-Life Technology Assessment",
        "description": "Unsupported versions, deprecated features, legacy components",
        "field_type": FieldType.SELECT,  # Issue #886: Changed to SELECT for intelligent options
        "business_impact": "Determines modernization urgency and approach",
    },
    "documentation_quality": {
        "category": "technical_debt",
        "weight": 0.02,
        "label": "Documentation Quality",
        "description": "Availability, accuracy, completeness of technical documentation",
        "field_type": FieldType.SELECT,
        "business_impact": "Impacts migration complexity and knowledge transfer needs",
    },
}
