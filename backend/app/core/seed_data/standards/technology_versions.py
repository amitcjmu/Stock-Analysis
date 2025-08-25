"""
Technology Version Standards for Assessment Flow
Minimum supported versions for common technology stacks.
"""

TECH_VERSION_STANDARDS = [
    {
        "requirement_type": "java_versions",
        "description": "Minimum supported Java versions for cloud migration",
        "mandatory": True,
        "supported_versions": {
            "java": "11+",
            "spring_boot": "2.5+",
            "spring_framework": "5.3+",
            "maven": "3.6+",
            "gradle": "6.0+",
        },
        "requirement_details": {
            "rationale": "Java 8 end-of-life considerations and cloud platform requirements",
            "migration_path": "Upgrade to Java 11 LTS or Java 17 LTS for long-term support",
            "compatibility_notes": "Review deprecated APIs and third-party library compatibility",
            "cloud_support": {
                "aws": "Supports Java 11+ in Lambda, ECS, EKS",
                "azure": "Supports Java 11+ in App Service, AKS",
                "gcp": "Supports Java 11+ in App Engine, GKE",
            },
            "security_benefits": [
                "Enhanced TLS support",
                "Improved cryptographic algorithms",
                "Regular security updates",
            ],
        },
    },
    {
        "requirement_type": "dotnet_versions",
        "description": "Minimum supported .NET versions for modern cloud deployment",
        "mandatory": True,
        "supported_versions": {
            "dotnet_core": "3.1+",
            "dotnet_framework": "4.8+",
            "asp_net_core": "3.1+",
            "entity_framework": "6.0+",
            "nuget": "5.0+",
        },
        "requirement_details": {
            "rationale": ".NET Core provides better cloud compatibility and performance",
            "migration_path": "Migrate from .NET Framework to .NET Core/.NET 5+",
            "compatibility_notes": "Review Windows-specific dependencies",
            "cloud_support": {
                "azure": "Native support in App Service, AKS, Service Fabric",
                "aws": "Supports .NET Core in Lambda, ECS, EKS",
                "gcp": "Supports .NET Core in App Engine, GKE",
            },
            "performance_benefits": [
                "Cross-platform deployment",
                "Improved startup times",
                "Lower memory footprint",
            ],
        },
    },
    {
        "requirement_type": "python_versions",
        "description": "Minimum supported Python versions with security updates",
        "mandatory": True,
        "supported_versions": {
            "python": "3.8+",
            "django": "3.2+",
            "flask": "2.0+",
            "fastapi": "0.65+",
            "pip": "21.0+",
        },
        "requirement_details": {
            "rationale": "Python 3.7 and below are end-of-life and lack security updates",
            "migration_path": "Upgrade to Python 3.8+ for continued security support",
            "compatibility_notes": "Review deprecated features and library compatibility",
            "cloud_support": {
                "aws": "Supports Python 3.8+ in Lambda, ECS, EC2",
                "azure": "Supports Python 3.8+ in Functions, App Service",
                "gcp": "Supports Python 3.8+ in Cloud Functions, App Engine",
            },
            "language_features": [
                "Assignment expressions (walrus operator)",
                "Positional-only parameters",
                "Improved type hints",
            ],
        },
    },
    {
        "requirement_type": "nodejs_versions",
        "description": "Minimum supported Node.js versions with LTS support",
        "mandatory": True,
        "supported_versions": {
            "nodejs": "14+",
            "npm": "6.0+",
            "express": "4.17+",
            "react": "17.0+",
            "angular": "12.0+",
        },
        "requirement_details": {
            "rationale": "Node.js 14+ provides LTS support and enhanced security",
            "migration_path": "Upgrade to Node.js 14 LTS or 16 LTS",
            "compatibility_notes": "Review npm package dependencies and security vulnerabilities",
            "cloud_support": {
                "aws": "Supports Node.js 14+ in Lambda, ECS, Elastic Beanstalk",
                "azure": "Supports Node.js 14+ in Functions, App Service",
                "gcp": "Supports Node.js 14+ in Cloud Functions, App Engine",
            },
            "performance_improvements": [
                "V8 engine updates",
                "Enhanced ES modules support",
                "Improved diagnostic reporting",
            ],
        },
    },
]
