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
    """5R cloud migration strategy framework."""

    # Migration Lift and Shift
    REHOST = "rehost"  # Like to Like Migration: Lift and Shift (P2V/V2V), Reconfigure using IAAS

    # Legacy Modernization Treatments
    REPLATFORM = "replatform"  # Reconfigure as PaaS/IAAS treatment, framework upgrades, containerize
    REFACTOR = "refactor"  # Modify/extend code base for cloud VM/container deployment
    REARCHITECT = "rearchitect"  # Modify/extend for native container/cloud native services, microservices

    # Cloud Native
    REPLACE = "replace"  # Applications identified to be retired/modernized, replace with COTS/SaaS
    REWRITE = "rewrite"  # Re-write application in cloud native code


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
