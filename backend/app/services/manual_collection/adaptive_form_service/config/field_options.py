"""
Field Options Configuration

Defines dropdown/select options for all form fields used in adaptive questionnaires.
Organized by field type for maintainability.
"""

# Field options for common select/radio fields
FIELD_OPTIONS = {
    # Infrastructure Options
    "os_version": [
        {"value": "windows_server_2019", "label": "Windows Server 2019"},
        {"value": "windows_server_2016", "label": "Windows Server 2016"},
        {"value": "windows_server_2012", "label": "Windows Server 2012"},
        {"value": "ubuntu_20.04", "label": "Ubuntu 20.04 LTS"},
        {"value": "ubuntu_18.04", "label": "Ubuntu 18.04 LTS"},
        {"value": "rhel_8", "label": "Red Hat Enterprise Linux 8"},
        {"value": "rhel_7", "label": "Red Hat Enterprise Linux 7"},
        {"value": "centos_8", "label": "CentOS 8"},
        {"value": "centos_7", "label": "CentOS 7"},
        {"value": "other", "label": "Other (specify in description)"},
    ],
    "virtualization": [
        {"value": "vmware_vsphere", "label": "VMware vSphere"},
        {"value": "hyper_v", "label": "Microsoft Hyper-V"},
        {"value": "kvm", "label": "KVM"},
        {"value": "xen", "label": "Citrix Xen"},
        {"value": "physical", "label": "Physical Server"},
        {"value": "cloud_vm", "label": "Cloud Virtual Machine"},
        {"value": "container", "label": "Containerized"},
        {"value": "other", "label": "Other"},
    ],
    "availability_requirements": [
        {"value": "99.99", "label": "99.99% (4 minutes downtime/month)"},
        {"value": "99.9", "label": "99.9% (43 minutes downtime/month)"},
        {"value": "99.5", "label": "99.5% (3.6 hours downtime/month)"},
        {"value": "99.0", "label": "99.0% (7.2 hours downtime/month)"},
        {"value": "95.0", "label": "95.0% (36 hours downtime/month)"},
        {"value": "best_effort", "label": "Best Effort (No SLA)"},
    ],
    # Application Options
    "technology_stack": [
        {"value": "java", "label": "Java"},
        {"value": "dotnet", "label": ".NET Framework"},
        {"value": "dotnet_core", "label": ".NET Core"},
        {"value": "python", "label": "Python"},
        {"value": "nodejs", "label": "Node.js"},
        {"value": "php", "label": "PHP"},
        {"value": "ruby", "label": "Ruby"},
        {"value": "go", "label": "Go"},
        {"value": "rust", "label": "Rust"},
        {"value": "cpp", "label": "C++"},
        {"value": "oracle", "label": "Oracle Database"},
        {"value": "sql_server", "label": "SQL Server"},
        {"value": "mysql", "label": "MySQL"},
        {"value": "postgresql", "label": "PostgreSQL"},
        {"value": "mongodb", "label": "MongoDB"},
        {"value": "redis", "label": "Redis"},
        {"value": "elasticsearch", "label": "Elasticsearch"},
    ],
    "architecture_pattern": [
        {"value": "monolith", "label": "Monolithic Application"},
        {"value": "microservices", "label": "Microservices Architecture"},
        {"value": "soa", "label": "Service-Oriented Architecture (SOA)"},
        {"value": "layered", "label": "Layered/N-Tier Architecture"},
        {"value": "event_driven", "label": "Event-Driven Architecture"},
        {"value": "serverless", "label": "Serverless/Function-based"},
        {"value": "hybrid", "label": "Hybrid Architecture"},
    ],
    "security_requirements": [
        {"value": "pci_dss", "label": "PCI DSS"},
        {"value": "hipaa", "label": "HIPAA"},
        {"value": "sox", "label": "SOX"},
        {"value": "gdpr", "label": "GDPR"},
        {"value": "iso_27001", "label": "ISO 27001"},
        {"value": "fedramp", "label": "FedRAMP"},
        {"value": "pii", "label": "PII Data Protection"},
        {"value": "encryption_rest", "label": "Encryption at Rest"},
        {"value": "encryption_transit", "label": "Encryption in Transit"},
        {"value": "multi_factor_auth", "label": "Multi-Factor Authentication"},
    ],
    # Business Options
    "business_criticality": [
        {
            "value": "mission_critical",
            "label": "Mission Critical (Revenue Generating)",
        },
        {
            "value": "business_critical",
            "label": "Business Critical (Operations Dependent)",
        },
        {"value": "important", "label": "Important (Business Supporting)"},
        {"value": "standard", "label": "Standard (Operational Support)"},
        {"value": "low", "label": "Low Priority (Development/Testing)"},
    ],
    "change_tolerance": [
        {
            "value": "high",
            "label": "High (Users adapt quickly, minimal training needed)",
        },
        {
            "value": "medium",
            "label": "Medium (Some training required, moderate adaptation)",
        },
        {
            "value": "low",
            "label": "Low (Significant training needed, resistance to change)",
        },
        {
            "value": "very_low",
            "label": "Very Low (Change averse, extensive change management)",
        },
    ],
    "compliance_constraints": [
        {"value": "none", "label": "None - No specific compliance requirements"},
        {"value": "healthcare", "label": "Healthcare (HIPAA, FDA)"},
        {"value": "financial", "label": "Financial Services (PCI DSS, SOX)"},
        {"value": "government", "label": "Government (FedRAMP, FISMA)"},
        {"value": "manufacturing", "label": "Manufacturing (ITAR, EAR)"},
        {"value": "retail", "label": "Retail (PCI DSS)"},
        {"value": "education", "label": "Education (FERPA)"},
        {"value": "data_residency", "label": "Data Residency Requirements"},
        {
            "value": "cross_border",
            "label": "Cross-Border Data Transfer Restrictions",
        },
    ],
    # Technical Debt Options
    "documentation_quality": [
        {
            "value": "excellent",
            "label": "Excellent (Comprehensive, up-to-date, detailed)",
        },
        {"value": "good", "label": "Good (Mostly complete, minor gaps)"},
        {"value": "fair", "label": "Fair (Basic documentation, some outdated)"},
        {"value": "poor", "label": "Poor (Minimal documentation, mostly outdated)"},
        {"value": "none", "label": "None (No documentation available)"},
    ],
    # General/Common Options
    "cpu_cores": [
        {"value": "2", "label": "2 vCPUs"},
        {"value": "4", "label": "4 vCPUs"},
        {"value": "8", "label": "8 vCPUs"},
        {"value": "16", "label": "16 vCPUs"},
        {"value": "32", "label": "32 vCPUs"},
        {"value": "64", "label": "64 vCPUs"},
    ],
    "memory_gb": [
        {"value": "8", "label": "8 GB RAM"},
        {"value": "16", "label": "16 GB RAM"},
        {"value": "32", "label": "32 GB RAM"},
        {"value": "64", "label": "64 GB RAM"},
        {"value": "128", "label": "128 GB RAM"},
        {"value": "256", "label": "256 GB RAM"},
    ],
    "storage_gb": [
        {"value": "100", "label": "100 GB"},
        {"value": "250", "label": "250 GB"},
        {"value": "500", "label": "500 GB"},
        {"value": "1000", "label": "1 TB (1000 GB)"},
        {"value": "2000", "label": "2 TB (2000 GB)"},
        {"value": "4000", "label": "4 TB (4000 GB)"},
    ],
    "environment": [
        {"value": "production", "label": "Production"},
        {"value": "staging", "label": "Staging"},
        {"value": "uat", "label": "UAT (User Acceptance Testing)"},
        {"value": "development", "label": "Development"},
        {"value": "test", "label": "Test"},
        {"value": "dr", "label": "Disaster Recovery"},
    ],
    # MCQ options for missing critical attributes (Added for full MCQ conversion)
    "operating_system": [
        {"value": "windows_server_2019", "label": "Windows Server 2019"},
        {"value": "windows_server_2016", "label": "Windows Server 2016"},
        {"value": "rhel_8", "label": "Red Hat Enterprise Linux 8"},
        {"value": "rhel_7", "label": "Red Hat Enterprise Linux 7"},
        {"value": "ubuntu_22.04", "label": "Ubuntu 22.04 LTS"},
        {"value": "ubuntu_20.04", "label": "Ubuntu 20.04 LTS"},
        {"value": "centos_8", "label": "CentOS 8"},
        {"value": "debian", "label": "Debian"},
        {"value": "other", "label": "Other (specify in notes)"},
    ],
    "business_owner": [
        {"value": "executive_c_level", "label": "Executive / C-Level Leadership"},
        {"value": "vp_director", "label": "VP / Director Level"},
        {"value": "department_manager", "label": "Department Manager"},
        {"value": "product_owner", "label": "Product Owner / Business Owner"},
        {"value": "it_operations", "label": "IT Operations Team"},
        {"value": "multiple_stakeholders", "label": "Multiple Stakeholders"},
        {"value": "unknown", "label": "Unknown / To Be Determined"},
    ],
    "custom_attributes.complexity": [
        {"value": "simple", "label": "Simple - Basic CRUD, minimal business logic"},
        {
            "value": "moderate",
            "label": "Moderate - Standard business rules, some workflows",
        },
        {
            "value": "complex",
            "label": "Complex - Advanced workflows, multi-step processes",
        },
        {
            "value": "very_complex",
            "label": "Very Complex - Intricate business rules, regulatory logic",
        },
    ],
    "business_logic_complexity": [
        {"value": "simple", "label": "Simple - Basic CRUD, minimal business logic"},
        {
            "value": "moderate",
            "label": "Moderate - Standard business rules, some workflows",
        },
        {
            "value": "complex",
            "label": "Complex - Advanced workflows, multi-step processes",
        },
        {
            "value": "very_complex",
            "label": "Very Complex - Intricate business rules, regulatory logic",
        },
    ],
    "custom_attributes.vulnerabilities": [
        {"value": "none_known", "label": "None Known - No vulnerabilities identified"},
        {"value": "low_severity", "label": "Low Severity - Minor issues, low risk"},
        {
            "value": "medium_severity",
            "label": "Medium Severity - Moderate risk, should be addressed",
        },
        {
            "value": "high_severity",
            "label": "High Severity - Critical vulnerabilities exist",
        },
        {"value": "not_assessed", "label": "Not Assessed - Security scan needed"},
    ],
    "custom_attributes.eol_assessment": [
        {"value": "current", "label": "Current - All technologies actively supported"},
        {"value": "supported", "label": "Supported - Technologies in extended support"},
        {"value": "eol_soon", "label": "EOL Soon - Support ending within 12 months"},
        {"value": "eol_expired", "label": "EOL Expired - No vendor support available"},
        {
            "value": "mixed",
            "label": "Mixed - Combination of supported and EOL components",
        },
    ],
    "custom_attributes.compliance": [
        {"value": "healthcare", "label": "Healthcare (HIPAA, FDA)"},
        {"value": "financial", "label": "Financial Services (PCI DSS, SOX)"},
        {"value": "government", "label": "Government (FedRAMP, FISMA)"},
        {"value": "retail", "label": "Retail (PCI DSS)"},
        {"value": "gdpr", "label": "GDPR (EU Data Protection)"},
        {"value": "multiple", "label": "Multiple Compliance Requirements"},
        {"value": "none", "label": "No Specific Compliance Requirements"},
    ],
    "dependencies": [
        {
            "value": "minimal",
            "label": "Minimal - Standalone with no or few external dependencies",
        },
        {"value": "low", "label": "Low - Depends on 1-3 systems"},
        {"value": "moderate", "label": "Moderate - Depends on 4-7 systems"},
        {"value": "high", "label": "High - Depends on 8-15 systems"},
        {"value": "very_high", "label": "Very High - Highly coupled with 16+ systems"},
        {
            "value": "unknown",
            "label": "Unknown - Dependency analysis not yet performed",
        },
    ],
    # Security and EOL Technology Assessment (Issue #886)
    "security_vulnerabilities": [
        {"value": "none_known", "label": "None Known - No vulnerabilities identified"},
        {"value": "low_severity", "label": "Low Severity - Minor issues, low risk"},
        {
            "value": "medium_severity",
            "label": "Medium Severity - Moderate risk, should be addressed",
        },
        {
            "value": "high_severity",
            "label": "High Severity - Critical vulnerabilities exist",
        },
        {"value": "not_assessed", "label": "Not Assessed - Security scan needed"},
    ],
    "eol_technology": [
        {"value": "current", "label": "Current - All technologies actively supported"},
        {"value": "supported", "label": "Supported - Technologies in extended support"},
        {"value": "eol_soon", "label": "EOL Soon - Support ending within 12 months"},
        {"value": "eol_expired", "label": "EOL Expired - No vendor support available"},
        {
            "value": "mixed",
            "label": "Mixed - Combination of supported and EOL components",
        },
    ],
    # Duplicate entries with custom_attributes prefix for proper lookup
    "custom_attributes.architecture_pattern": [
        {"value": "monolith", "label": "Monolithic Application"},
        {"value": "microservices", "label": "Microservices Architecture"},
        {"value": "soa", "label": "Service-Oriented Architecture (SOA)"},
        {"value": "layered", "label": "Layered/N-Tier Architecture"},
        {"value": "event_driven", "label": "Event-Driven Architecture"},
        {"value": "serverless", "label": "Serverless/Function-based"},
        {"value": "hybrid", "label": "Hybrid Architecture"},
    ],
    "custom_attributes.availability_requirements": [
        {"value": "99.99", "label": "99.99% (4 minutes downtime/month)"},
        {"value": "99.9", "label": "99.9% (43 minutes downtime/month)"},
        {"value": "99.5", "label": "99.5% (3.6 hours downtime/month)"},
        {"value": "99.0", "label": "99.0% (7.2 hours downtime/month)"},
        {"value": "95.0", "label": "95.0% (36 hours downtime/month)"},
        {"value": "best_effort", "label": "Best Effort (No SLA)"},
    ],
    "custom_attributes.compliance_constraints": [
        {"value": "none", "label": "None - No specific compliance requirements"},
        {"value": "healthcare", "label": "Healthcare (HIPAA, FDA)"},
        {"value": "financial", "label": "Financial Services (PCI DSS, SOX)"},
        {"value": "government", "label": "Government (FedRAMP, FISMA)"},
        {"value": "manufacturing", "label": "Manufacturing (ITAR, EAR)"},
        {"value": "retail", "label": "Retail (PCI DSS)"},
        {"value": "education", "label": "Education (FERPA)"},
        {"value": "data_residency", "label": "Data Residency Requirements"},
        {
            "value": "cross_border",
            "label": "Cross-Border Data Transfer Restrictions",
        },
    ],
}
