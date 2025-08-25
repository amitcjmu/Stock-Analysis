"""
Security and Compliance Standards for Assessment Flow
Modern authentication, encryption, and API security patterns.
"""

SECURITY_STANDARDS = [
    {
        "requirement_type": "authentication",
        "description": "Modern authentication and authorization patterns",
        "mandatory": True,
        "supported_versions": None,
        "requirement_details": {
            "required_patterns": ["OAuth2", "OIDC", "SAML"],
            "deprecated_patterns": [
                "Basic Auth",
                "Custom Sessions",
                "Plain text passwords",
            ],
            "required_features": [
                "Multi-Factor Authentication (MFA)",
                "Single Sign-On (SSO) Integration",
                "Role-Based Access Control (RBAC)",
                "Session management with timeout",
            ],
            "implementation_guidelines": {
                "token_storage": "Secure, httpOnly cookies or secure token storage",
                "token_expiration": "Access tokens: 15-60 minutes, Refresh tokens: 7-30 days",
                "password_policy": "Minimum 12 characters, complexity requirements",
            },
            "compliance_frameworks": ["SOC2", "ISO27001", "GDPR", "HIPAA"],
        },
    },
    {
        "requirement_type": "data_encryption",
        "description": "Data encryption at rest and in transit requirements",
        "mandatory": True,
        "supported_versions": None,
        "requirement_details": {
            "encryption_in_transit": {
                "minimum_tls": "TLS 1.2+",
                "preferred_tls": "TLS 1.3",
                "certificate_management": "Automated certificate rotation",
                "cipher_suites": "Modern, secure cipher suites only",
            },
            "encryption_at_rest": {
                "algorithm": "AES-256",
                "key_management": "Cloud provider KMS or dedicated HSM",
                "database_encryption": "Transparent Data Encryption (TDE)",
                "file_system_encryption": "Full disk encryption",
            },
            "key_management": {
                "rotation_policy": "Automatic key rotation every 90 days",
                "access_control": "Principle of least privilege",
                "audit_logging": "All key access logged and monitored",
            },
            "compliance_requirements": ["PCI-DSS", "SOC2", "GDPR", "HIPAA"],
        },
    },
    {
        "requirement_type": "api_security",
        "description": "API security standards and best practices",
        "mandatory": True,
        "supported_versions": None,
        "requirement_details": {
            "authentication": "OAuth2 Bearer tokens or API keys",
            "authorization": "Fine-grained permissions and scoping",
            "rate_limiting": "Per-client rate limiting and throttling",
            "input_validation": "Comprehensive input sanitization and validation",
            "security_headers": [
                "Content-Security-Policy",
                "X-Frame-Options",
                "X-Content-Type-Options",
                "Strict-Transport-Security",
            ],
            "monitoring": {
                "logging": "All API calls logged with request/response details",
                "alerting": "Anomaly detection and security event alerting",
                "metrics": "Response times, error rates, security events",
            },
            "vulnerability_management": "Regular security scanning and penetration testing",
        },
    },
]
