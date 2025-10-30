"""
Asset-related enumerations and constants.

This module contains all enum classes and constants used across
the asset model system.
"""

import enum


class AssetType(str, enum.Enum):
    """Asset type enumeration based on Azure Migrate metadata."""

    # Core Infrastructure
    SERVER = "server"
    DATABASE = "database"
    APPLICATION = "application"

    # Network Devices
    NETWORK = "network"
    LOAD_BALANCER = "load_balancer"

    # Storage Devices
    STORAGE = "storage"

    # Security Devices
    SECURITY_GROUP = "security_group"

    # Virtualization
    VIRTUAL_MACHINE = "virtual_machine"
    CONTAINER = "container"

    # Other/Unknown
    OTHER = "other"


class AssetStatus(str, enum.Enum):
    """Asset discovery and migration status."""

    DISCOVERED = "discovered"
    ASSESSED = "assessed"
    PLANNED = "planned"
    MIGRATING = "migrating"
    MIGRATED = "migrated"
    FAILED = "failed"
    EXCLUDED = "excluded"


class SixRStrategy(str, enum.Enum):
    """6R cloud migration strategy framework aligned with platform business logic.

    This platform focuses on migration and modernization - assets that stay behind
    (retain/keep as-is) are out of scope.

    The 6 strategies are:
    - REHOST: Lift and shift with minimal changes
    - REPLATFORM: Reconfigure as PaaS
    - REFACTOR: Modify code for cloud deployment
    - REARCHITECT: Microservices/cloud-native transformation
    - REPLACE: Replace with COTS/SaaS OR rewrite custom apps
    - RETIRE: Decommission/sunset assets

    Note: "REPLACE" consolidates both:
    - Repurchase (buy COTS/SaaS to replace)
    - Rewrite (rewrite custom apps from scratch)
    """

    # Migration Lift and Shift
    REHOST = (
        "rehost"  # Like to Like Migration: Lift and Shift (P2V/V2V), minimal changes
    )

    # Modernization Treatments
    REPLATFORM = "replatform"  # Reconfigure as PaaS, framework upgrades, containerize
    REFACTOR = "refactor"  # Modify/extend code base for cloud VM/container deployment
    REARCHITECT = "rearchitect"  # Modify/extend for native container/cloud native services, microservices

    # Replace or Retire
    REPLACE = "replace"  # Replace with COTS/SaaS (repurchase) OR rewrite custom apps
    RETIRE = "retire"  # Decommission/sunset assets


# Migration wave status constants
class WaveStatus(str, enum.Enum):
    """Migration wave status enumeration."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Workflow progress stage constants
class WorkflowStage(str, enum.Enum):
    """Workflow stage enumeration."""

    DISCOVERY = "discovery"
    ASSESSMENT = "assessment"
    PLANNING = "planning"
    MIGRATION = "migration"
    VALIDATION = "validation"
    COMPLETION = "completion"


# Analysis status constants
class AnalysisStatus(str, enum.Enum):
    """Analysis status enumeration."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Asset complexity levels
class ComplexityLevel(str, enum.Enum):
    """Asset migration complexity enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Asset criticality levels
class CriticalityLevel(str, enum.Enum):
    """Asset business criticality enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Discovery method constants
class DiscoveryMethod(str, enum.Enum):
    """Discovery method enumeration."""

    NETWORK_SCAN = "network_scan"
    AGENT = "agent"
    IMPORT = "import"
    MANUAL = "manual"
    API = "api"


# Assessment readiness constants
class AssessmentReadiness(str, enum.Enum):
    """Assessment readiness enumeration."""

    READY = "ready"
    NOT_READY = "not_ready"
    PENDING = "pending"
    BLOCKED = "blocked"


class ApplicationType(str, enum.Enum):
    """Application type classification."""

    COTS = "cots"  # Commercial Off-The-Shelf
    CUSTOM = "custom"  # Custom developed
    CUSTOM_COTS = "custom_cots"  # Customized COTS
    OTHER = "other"


class Lifecycle(str, enum.Enum):
    """Asset lifecycle stage."""

    RETIRE = "retire"  # Decommission
    REPLACE = "replace"  # Replace with new
    RETAIN = "retain"  # Keep as-is
    INVEST = "invest"  # Modernize/enhance


class HostingModel(str, enum.Enum):
    """Infrastructure hosting model."""

    ON_PREM = "on_prem"  # On-premises datacenter
    CLOUD = "cloud"  # Public cloud
    HYBRID = "hybrid"  # Mix of on-prem and cloud
    COLO = "colo"  # Colocation


class ServerRole(str, enum.Enum):
    """Server role classification."""

    WEB = "web"  # Web server
    DB = "db"  # Database server
    APP = "app"  # Application server
    CITRIX = "citrix"  # Citrix/VDI
    FILE = "file"  # File server
    EMAIL = "email"  # Email server
    OTHER = "other"


class RiskLevel(str, enum.Enum):
    """Migration risk assessment."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TShirtSize(str, enum.Enum):
    """Complexity sizing."""

    XS = "xs"  # Extra small
    S = "s"  # Small
    M = "m"  # Medium
    L = "l"  # Large
    XL = "xl"  # Extra large
    XXL = "xxl"  # Double extra large
