"""
Test fixtures for validating the six-source asset data model.

Issue #1110 - Phase 1 of ADR-037 Implementation

These fixtures demonstrate all 6 data sources where asset information can exist:
1. Standard columns (assets.{field})
2. Custom attributes (assets.custom_attributes JSONB)
3. Enrichment data (asset_enrichments.* tables)
4. Environment field (assets.environment JSON)
5. Canonical applications (canonical_applications junction table)
6. Related assets (asset_dependencies propagation)

Usage:
    from tests.fixtures.six_source_test_assets import (
        create_asset_standard_columns_only,
        create_asset_custom_attributes_only,
        create_asset_all_six_sources
    )

    # Test scenario 1: Data only in standard columns
    asset1 = await create_asset_standard_columns_only(db)

    # Test scenario 2: Data fragmented across all 6 sources
    asset2 = await create_asset_all_six_sources(db)

    # Validate intelligent gap detection
    scanner = IntelligentGapScanner(db, client_account_id, engagement_id)
    gaps = await scanner.scan_gaps(asset2)
    assert len([g for g in gaps if g.is_true_gap]) == 0  # No true gaps
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.asset_enrichments import (
    AssetTechDebt,
    AssetPerformanceMetrics,
    AssetCostOptimization,
)
from app.models.asset_resilience import (
    AssetResilience,
    AssetComplianceFlags,
    AssetVulnerabilities,
)
from app.models.canonical_applications import CanonicalApplication
from app.models.asset import AssetDependency


# ============================================================================
# Fixture 1: Asset with data ONLY in standard columns
# ============================================================================


async def create_asset_standard_columns_only(
    db: AsyncSession,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    name: str = "StandardColumnsOnly-Asset",
) -> Asset:
    """
    Create asset with data ONLY in standard columns.

    Use Case:
        - Test baseline scenario where all data is in expected locations
        - Validate that gap detection works correctly with standard columns
        - No false gaps should be reported

    Data Present:
        - Standard columns: cpu_cores, memory_gb, operating_system, ip_address
        - Custom attributes: Empty {}
        - Enrichment tables: None
        - Environment field: None
        - Canonical apps: None
        - Related assets: None

    Expected Gap Detection Result:
        - Should identify TRUE gaps for fields not in standard columns
        - Should NOT flag fields with values as gaps
    """
    asset = Asset(
        id=uuid.uuid4(),
        name=name,
        asset_type="server",
        # Standard columns with data
        cpu_cores=8,
        memory_gb=32.0,
        storage_gb=500.0,
        operating_system="Red Hat Enterprise Linux",
        os_version="8.5",
        ip_address="10.0.1.100",
        hostname="srv-prod-01",
        fqdn="srv-prod-01.example.com",
        mac_address="00:1A:2B:3C:4D:5E",
        business_owner="Jane Smith",
        technical_owner="John Doe",
        department="Engineering",
        application_name="Web Application",
        technology_stack="Java Spring Boot",
        business_criticality="High",
        # Empty JSONB fields
        custom_attributes={},
        technical_details={},
        environment=None,
        # Multi-tenant isolation
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return asset


# ============================================================================
# Fixture 2: Asset with data ONLY in custom_attributes
# ============================================================================


async def create_asset_custom_attributes_only(
    db: AsyncSession,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    name: str = "CustomAttributesOnly-Asset",
) -> Asset:
    """
    Create asset with data ONLY in custom_attributes JSONB field.

    Use Case:
        - Test user import scenario with custom field names
        - Validate gap detection checks custom_attributes
        - Prevent false gaps for data in custom fields

    Data Present:
        - Standard columns: NULL (except name, asset_type, tenant fields)
        - Custom attributes: cpu, memory, db_type, owner, etc.
        - Enrichment tables: None
        - Environment field: None
        - Canonical apps: None
        - Related assets: None

    Expected Gap Detection Result:
        - Should NOT flag cpu_count as gap (exists as custom_attributes.cpu)
        - Should NOT flag memory_gb as gap (exists as custom_attributes.memory)
        - Should NOT flag database_type as gap (exists as custom_attributes.db_type)
    """
    asset = Asset(
        id=uuid.uuid4(),
        name=name,
        asset_type="server",
        # Standard columns: NULL
        cpu_cores=None,
        memory_gb=None,
        storage_gb=None,
        operating_system=None,
        os_version=None,
        ip_address=None,
        business_owner=None,
        technical_owner=None,
        # Data in custom_attributes
        custom_attributes={
            # Infrastructure data
            "cpu": 16,
            "memory": 64,
            "storage": 1000,
            "os": "Ubuntu 22.04 LTS",
            "os_version": "22.04.1",
            "ip": "10.0.2.50",
            # Application data
            "db_type": "PostgreSQL 14",
            "app_name": "CRM System",
            "tech_stack": "Python Django",
            # Business data
            "owner": "Sarah Johnson",
            "tech_owner": "Mike Chen",
            "dept": "Sales",
            "criticality": "Critical",
            # Nested structure
            "hardware": {
                "cpu_count": 16,
                "memory_gb": 64,
                "disk_type": "NVMe SSD",
            },
            "database": {
                "type": "PostgreSQL",
                "version": "14.5",
                "cluster": "production",
            },
            "network": {
                "ip_address": "10.0.2.50",
                "subnet": "10.0.2.0/24",
                "gateway": "10.0.2.1",
            },
        },
        # Multi-tenant isolation
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return asset


# ============================================================================
# Fixture 3: Asset with data in enrichment tables
# ============================================================================


async def create_asset_with_enrichment_data(
    db: AsyncSession,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    name: str = "EnrichmentData-Asset",
) -> Asset:
    """
    Create asset with data in enrichment tables.

    Use Case:
        - Test agent-enriched asset data
        - Validate gap detection checks enrichment tables
        - Verify performance, cost, and tech debt data sources

    Data Present:
        - Standard columns: Minimal (name, type, tenant fields)
        - Custom attributes: Empty
        - Enrichment tables:
            * AssetPerformanceMetrics (cpu/memory utilization)
            * AssetCostOptimization (cost data)
            * AssetTechDebt (modernization priority)
            * AssetResilience (RTO/RPO)
            * AssetComplianceFlags (data classification)
        - Environment field: None
        - Canonical apps: None
        - Related assets: None

    Expected Gap Detection Result:
        - Should NOT flag cpu_utilization as gap (in performance_metrics)
        - Should NOT flag monthly_cost as gap (in cost_optimization)
        - Should NOT flag tech_debt_score as gap (in tech_debt)
        - Should NOT flag rto/rpo as gaps (in resilience)
    """
    asset = Asset(
        id=uuid.uuid4(),
        name=name,
        asset_type="server",
        # Minimal standard columns
        cpu_cores=None,
        memory_gb=None,
        operating_system=None,
        custom_attributes={},
        # Multi-tenant isolation
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    db.add(asset)
    await db.flush()  # Get asset.id

    # Add performance metrics enrichment
    performance = AssetPerformanceMetrics(
        id=uuid.uuid4(),
        asset_id=asset.id,
        cpu_utilization_avg=65.5,
        cpu_utilization_peak=92.3,
        memory_utilization_avg=78.2,
        memory_utilization_peak=88.9,
        disk_iops_avg=5000,
        disk_throughput_mbps=250.5,
        network_throughput_mbps=100.2,
        network_latency_ms=1.5,
        monitoring_period_days=30,
        metrics_source="CloudWatch",
        additional_metrics={
            "cpu_cores": 8,  # Can infer CPU count from metrics
            "memory_gb": 32,  # Can infer memory from metrics
            "peak_connections": 500,
            "error_rate": 0.05,
        },
    )
    db.add(performance)

    # Add cost optimization enrichment
    cost = AssetCostOptimization(
        id=uuid.uuid4(),
        asset_id=asset.id,
        monthly_cost_usd=450.00,
        annual_cost_usd=5400.00,
        projected_monthly_cost_usd=320.00,
        projected_annual_cost_usd=3840.00,
        optimization_potential_pct=28.9,
        optimization_opportunities=[
            {"type": "rightsizing", "savings_usd": 80.00},
            {"type": "reserved_instance", "savings_usd": 50.00},
        ],
        cost_breakdown={
            "compute": 300.00,
            "storage": 100.00,
            "network": 30.00,
            "licenses": 20.00,
        },
        cost_calculation_date=datetime.utcnow().isoformat(),
        cost_source="AWS Cost Explorer",
    )
    db.add(cost)

    # Add tech debt enrichment
    tech_debt = AssetTechDebt(
        id=uuid.uuid4(),
        asset_id=asset.id,
        tech_debt_score=65.0,
        modernization_priority="high",
        code_quality_score=35.0,
        debt_items=[
            {
                "category": "outdated_dependencies",
                "description": "Using Node.js 12 (EOL)",
                "priority": "high",
            },
            {
                "category": "security_vulnerabilities",
                "description": "15 CVEs identified",
                "priority": "critical",
            },
        ],
        last_assessment_date=datetime.utcnow().isoformat(),
        assessment_method="automated",
    )
    db.add(tech_debt)

    # Add resilience enrichment
    resilience = AssetResilience(
        id=uuid.uuid4(),
        asset_id=asset.id,
        rto_minutes=60,  # 1 hour RTO
        rpo_minutes=15,  # 15 minute RPO
        sla_json={
            "uptime_target": 99.9,
            "availability": "24x7",
            "support_tier": "premium",
            "ha_enabled": True,
        },
    )
    db.add(resilience)

    # Add compliance enrichment
    compliance = AssetComplianceFlags(
        id=uuid.uuid4(),
        asset_id=asset.id,
        compliance_scopes=["GDPR", "SOC2", "ISO27001"],
        data_classification="confidential",
        residency="EU",
        evidence_refs=[
            {"scope": "GDPR", "evidence_url": "https://docs/gdpr-compliance.pdf"},
            {"scope": "SOC2", "audit_date": "2024-10-15"},
        ],
    )
    db.add(compliance)

    await db.commit()
    await db.refresh(asset)

    return asset


# ============================================================================
# Fixture 4: Asset with data in environment field
# ============================================================================


async def create_asset_with_environment_data(
    db: AsyncSession,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    name: str = "EnvironmentData-Asset",
) -> Asset:
    """
    Create asset with data in environment JSON field.

    Use Case:
        - Test discovery agent populated environment data
        - Validate gap detection checks environment field
        - Verify nested JSON path handling

    Data Present:
        - Standard columns: Minimal
        - Custom attributes: Empty
        - Enrichment tables: None
        - Environment field: Infrastructure, network, database config
        - Canonical apps: None
        - Related assets: None

    Expected Gap Detection Result:
        - Should NOT flag fields present in environment JSON
        - Should handle nested paths (environment.database.type)
        - Should handle arrays (environment.interfaces[])
    """
    asset = Asset(
        id=uuid.uuid4(),
        name=name,
        asset_type="server",
        # Minimal standard columns
        cpu_cores=None,
        memory_gb=None,
        operating_system=None,
        custom_attributes={},
        # Data in environment field
        environment={
            # Infrastructure
            "cpu_count": 12,
            "memory_gb": 48,
            "storage_gb": 800,
            "os": "AIX 7.3",
            "os_version": "7.3.0.0",
            # Network configuration
            "network": {
                "primary_ip": "192.168.1.100",
                "secondary_ip": "192.168.1.101",
                "gateway": "192.168.1.1",
                "dns_servers": ["192.168.1.10", "192.168.1.11"],
                "interfaces": [
                    {
                        "name": "eth0",
                        "ip_address": "192.168.1.100",
                        "mac_address": "AA:BB:CC:DD:EE:FF",
                        "status": "up",
                    },
                    {
                        "name": "eth1",
                        "ip_address": "192.168.1.101",
                        "mac_address": "FF:EE:DD:CC:BB:AA",
                        "status": "up",
                    },
                ],
            },
            # Database configuration
            "database": {
                "type": "Oracle",
                "version": "19c",
                "instance_name": "ORCL",
                "sid": "ORCL",
                "port": 1521,
                "connection": {
                    "host": "192.168.1.100",
                    "service_name": "ORCL.example.com",
                },
            },
            # Application server
            "app_server": {
                "type": "WebLogic",
                "version": "14.1.1",
                "domain": "production",
                "managed_servers": ["server1", "server2"],
            },
            # Resilience
            "ha_config": {
                "enabled": True,
                "cluster_name": "production-cluster",
                "nodes": 3,
                "load_balancer": "192.168.1.200",
            },
        },
        # Multi-tenant isolation
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return asset


# ============================================================================
# Fixture 5: Asset with canonical application data
# ============================================================================


async def create_asset_with_canonical_application(
    db: AsyncSession,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    name: str = "CanonicalApp-Asset",
    canonical_app_name: str = "SAP ERP Production",
) -> tuple[Asset, CanonicalApplication]:
    """
    Create asset with associated canonical application.

    Use Case:
        - Test application identity resolution
        - Validate gap detection checks canonical_applications junction
        - Verify application metadata propagation

    Data Present:
        - Standard columns: Minimal
        - Custom attributes: Empty
        - Enrichment tables: None
        - Environment field: None
        - Canonical apps: Application metadata (type, criticality, tech stack)
        - Related assets: None

    Expected Gap Detection Result:
        - Should infer application_type from canonical_applications
        - Should NOT flag application_name as gap
        - Should access technology_stack from canonical app
    """
    asset = Asset(
        id=uuid.uuid4(),
        name=name,
        asset_type="server",
        # Minimal standard columns
        cpu_cores=None,
        memory_gb=None,
        application_name=None,  # Will be inferred from canonical app
        technology_stack=None,  # Will be inferred from canonical app
        custom_attributes={},
        # Multi-tenant isolation
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    db.add(asset)
    await db.flush()

    # Create canonical application
    canonical_app = CanonicalApplication(
        id=uuid.uuid4(),
        canonical_name=canonical_app_name,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        description="Enterprise resource planning system",
        application_type="database",  # Can infer asset has database
        business_criticality="Critical",
        technology_stack={
            "database": {
                "type": "Oracle",
                "version": "19c",
                "edition": "Enterprise",
            },
            "app_server": {"type": "SAP NetWeaver", "version": "7.5"},
            "languages": ["ABAP", "Java"],
            "middleware": ["SAP Gateway", "SAP PI/PO"],
        },
        confidence_score=1.0,
        is_verified=True,
        verification_source="user_input",
    )

    db.add(canonical_app)
    await db.commit()
    await db.refresh(asset)
    await db.refresh(canonical_app)

    return asset, canonical_app


# ============================================================================
# Fixture 6: Asset with related asset dependencies
# ============================================================================


async def create_asset_with_related_dependencies(
    db: AsyncSession,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    name: str = "WebApp-Asset",
    dependency_name: str = "Database-Asset",
) -> tuple[Asset, Asset, AssetDependency]:
    """
    Create asset with dependency relationship.

    Use Case:
        - Test data propagation from related assets
        - Validate gap detection checks asset_dependencies
        - Verify dependency inference (e.g., app → database)

    Data Present:
        - Primary asset: Minimal data
        - Dependency asset: Complete database information
        - Dependency relationship: Network connection details
        - Can infer: Primary asset uses database (type, version, port)

    Expected Gap Detection Result:
        - Should infer database_type from related database asset
        - Should infer connection details from dependency relationship
        - Should propagate data with lower confidence (0.70)
    """
    # Create primary asset (web application)
    primary_asset = Asset(
        id=uuid.uuid4(),
        name=name,
        asset_type="server",
        # Minimal data
        cpu_cores=None,
        memory_gb=None,
        operating_system="Ubuntu 22.04",
        custom_attributes={
            "app_type": "web",
            "framework": "React + Node.js",
        },
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    # Create dependency asset (database server)
    dependency_asset = Asset(
        id=uuid.uuid4(),
        name=dependency_name,
        asset_type="server",
        # Complete database information
        cpu_cores=16,
        memory_gb=128.0,
        storage_gb=2000.0,
        operating_system="Red Hat Enterprise Linux",
        os_version="8.6",
        ip_address="10.0.3.100",
        custom_attributes={
            "db_type": "PostgreSQL",
            "db_version": "15.2",
            "database": {
                "type": "PostgreSQL",
                "version": "15.2",
                "port": 5432,
                "cluster": "production",
                "replication": "streaming",
            },
        },
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    db.add(primary_asset)
    db.add(dependency_asset)
    await db.flush()

    # Create dependency relationship
    dependency = AssetDependency(
        id=uuid.uuid4(),
        asset_id=primary_asset.id,  # Web app depends on
        depends_on_asset_id=dependency_asset.id,  # Database
        dependency_type="database",
        criticality="high",
        description="Primary database for web application",
        confidence_score=0.95,
        # Network discovery details (Issue #833)
        port=5432,
        protocol_name="TCP",
        conn_count=150,
        bytes_total=5242880,  # 5MB
        first_seen=datetime.utcnow(),
        last_seen=datetime.utcnow(),
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    db.add(dependency)
    await db.commit()
    await db.refresh(primary_asset)
    await db.refresh(dependency_asset)
    await db.refresh(dependency)

    return primary_asset, dependency_asset, dependency


# ============================================================================
# Fixture 7: Asset with data in ALL SIX sources (ultimate test)
# ============================================================================


async def create_asset_all_six_sources(
    db: AsyncSession,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    name: str = "AllSources-Asset",
) -> Dict[str, Any]:
    """
    Create asset with data fragmented across ALL SIX sources.

    Use Case:
        - Ultimate test for intelligent gap detection
        - Validate scanner checks all 6 sources
        - Test conflict resolution (same field in multiple sources)
        - Verify confidence scoring

    Data Distribution:
        - Source 1 (Standard): cpu_cores, operating_system
        - Source 2 (Custom Attrs): memory, storage, database.type
        - Source 3 (Enrichment): cpu_utilization, monthly_cost, tech_debt_score
        - Source 4 (Environment): network config, app_server details
        - Source 5 (Canonical Apps): application_name, technology_stack
        - Source 6 (Related Assets): database version (propagated)

    Expected Gap Detection Result:
        - ZERO true gaps (all fields covered by at least one source)
        - Should return confidence scores for each field
        - Should identify conflicts (e.g., cpu_cores in 3 places)
    """
    # Source 1: Standard columns
    asset = Asset(
        id=uuid.uuid4(),
        name=name,
        asset_type="server",
        cpu_cores=8,  # Source 1: Standard column
        memory_gb=None,  # Will be in Source 2 & 3
        storage_gb=None,  # Will be in Source 2
        operating_system="Red Hat Enterprise Linux",  # Source 1
        os_version="8.5",  # Source 1
        ip_address="10.0.4.100",  # Source 1
        hostname="srv-all-sources-01",  # Source 1
        business_owner="Emily Wilson",  # Source 1
        technical_owner="David Brown",  # Source 1
        application_name=None,  # Will be in Source 5
        technology_stack=None,  # Will be in Source 5
        custom_attributes={
            # Source 2: Custom attributes
            "memory": 32,  # Also in Source 3
            "storage": 500,
            "os": "RHEL 8.5",  # Duplicate of standard column
            "database": {
                "type": "MySQL",  # Also in Source 5
                "version": "8.0",  # Also in Source 6
                "port": 3306,
            },
            "hardware": {
                "cpu_count": 8,  # Duplicate of standard column
                "memory_gb": 32,
                "disk_type": "SSD",
            },
        },
        environment={
            # Source 4: Environment field
            "network": {
                "primary_ip": "10.0.4.100",
                "subnet": "10.0.4.0/24",
                "gateway": "10.0.4.1",
            },
            "app_server": {
                "type": "Tomcat",
                "version": "10.1",
                "java_version": "17",
            },
            "cpu_count": 8,  # Duplicate - third source!
        },
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    db.add(asset)
    await db.flush()

    # Source 3: Enrichment tables
    performance = AssetPerformanceMetrics(
        id=uuid.uuid4(),
        asset_id=asset.id,
        cpu_utilization_avg=70.5,
        memory_utilization_avg=82.3,
        additional_metrics={
            "memory_gb": 32,  # Third source for memory!
            "storage_gb": 500,  # Second source for storage
        },
    )

    cost = AssetCostOptimization(
        id=uuid.uuid4(),
        asset_id=asset.id,
        monthly_cost_usd=380.00,
        projected_monthly_cost_usd=280.00,
    )

    tech_debt = AssetTechDebt(
        id=uuid.uuid4(),
        asset_id=asset.id,
        tech_debt_score=45.0,
        modernization_priority="medium",
    )

    db.add(performance)
    db.add(cost)
    db.add(tech_debt)

    # Source 5: Canonical application
    canonical_app = CanonicalApplication(
        id=uuid.uuid4(),
        canonical_name="E-Commerce Platform",
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        application_type="web_application",
        business_criticality="High",
        technology_stack={
            "frontend": "React",
            "backend": "Java Spring Boot",
            "database": {
                "type": "MySQL",  # Duplicate - matches custom_attributes
                "version": "8.0",
            },
            "cache": "Redis",
        },
        confidence_score=1.0,
        is_verified=True,
    )

    db.add(canonical_app)
    await db.flush()

    # Source 6: Related asset (dependency)
    database_asset = Asset(
        id=uuid.uuid4(),
        name="MySQL-Database-01",
        asset_type="server",
        custom_attributes={
            "database": {
                "type": "MySQL",
                "version": "8.0.32",  # More specific version
                "cluster": "production",
            }
        },
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    db.add(database_asset)
    await db.flush()

    dependency = AssetDependency(
        id=uuid.uuid4(),
        asset_id=asset.id,
        depends_on_asset_id=database_asset.id,
        dependency_type="database",
        criticality="high",
        port=3306,
        protocol_name="TCP",
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    db.add(dependency)
    await db.commit()
    await db.refresh(asset)

    return {
        "asset": asset,
        "performance_metrics": performance,
        "cost_optimization": cost,
        "tech_debt": tech_debt,
        "canonical_app": canonical_app,
        "database_asset": database_asset,
        "dependency": dependency,
        "data_sources_by_field": {
            "cpu_cores": [
                "assets.cpu_cores (1.0)",  # Source 1
                "custom_attributes.hardware.cpu_count (0.95)",  # Source 2
                "environment.cpu_count (0.85)",  # Source 4
            ],
            "memory_gb": [
                "custom_attributes.memory (0.95)",  # Source 2
                "custom_attributes.hardware.memory_gb (0.95)",  # Source 2
                "performance_metrics.additional_metrics.memory_gb (0.90)",  # Source 3
            ],
            "database_type": [
                "custom_attributes.database.type (0.95)",  # Source 2
                "canonical_applications.technology_stack.database.type (0.80)",  # Source 5
                "related_assets.custom_attributes.database.type (0.70)",  # Source 6
            ],
        },
    }


# ============================================================================
# Test Utilities
# ============================================================================


async def validate_six_source_coverage(
    db: AsyncSession, asset: Asset
) -> Dict[str, Any]:
    """
    Validate that an asset's data is correctly accessible from all 6 sources.

    Returns:
        Dictionary with:
        - sources_found: List of sources with data
        - field_coverage: Dict[field, List[sources]]
        - conflicts: List of fields with data in multiple sources
    """
    sources_found = []
    field_coverage = {}
    conflicts = []

    # Source 1: Standard columns
    standard_fields = [
        field
        for field in [
            "cpu_cores",
            "memory_gb",
            "storage_gb",
            "operating_system",
            "ip_address",
        ]
        if getattr(asset, field, None) is not None
    ]
    if standard_fields:
        sources_found.append("standard_columns")
        for field in standard_fields:
            field_coverage.setdefault(field, []).append("standard_columns")

    # Source 2: Custom attributes
    if asset.custom_attributes:
        sources_found.append("custom_attributes")
        for key in asset.custom_attributes.keys():
            field_coverage.setdefault(key, []).append("custom_attributes")

    # Source 3: Enrichment tables (check via relationships)
    if hasattr(asset, "performance_metrics") and asset.performance_metrics:
        sources_found.append("enrichment_performance")
    if hasattr(asset, "cost_optimization") and asset.cost_optimization:
        sources_found.append("enrichment_cost")
    if hasattr(asset, "tech_debt") and asset.tech_debt:
        sources_found.append("enrichment_tech_debt")

    # Source 4: Environment field
    if asset.environment:
        sources_found.append("environment")
        for key in asset.environment.keys():
            field_coverage.setdefault(key, []).append("environment")

    # Source 5 & 6: Would need additional queries
    # (Simplified for this utility)

    # Identify conflicts
    for field, sources in field_coverage.items():
        if len(sources) > 1:
            conflicts.append({"field": field, "sources": sources})

    return {
        "sources_found": sources_found,
        "field_coverage": field_coverage,
        "conflicts": conflicts,
    }


# ============================================================================
# Bulk Fixture Creation (for integration tests)
# ============================================================================


async def create_complete_test_suite(
    db: AsyncSession,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
) -> Dict[str, Any]:
    """
    Create complete test suite with all fixture types.

    Returns dictionary with all created assets for easy access in tests.
    """
    fixtures = {}

    fixtures["standard_columns"] = await create_asset_standard_columns_only(
        db, client_account_id, engagement_id
    )

    fixtures["custom_attributes"] = await create_asset_custom_attributes_only(
        db, client_account_id, engagement_id
    )

    fixtures["enrichment_data"] = await create_asset_with_enrichment_data(
        db, client_account_id, engagement_id
    )

    fixtures["environment_data"] = await create_asset_with_environment_data(
        db, client_account_id, engagement_id
    )

    fixtures["canonical_app"] = await create_asset_with_canonical_application(
        db, client_account_id, engagement_id
    )

    fixtures["related_dependencies"] = await create_asset_with_related_dependencies(
        db, client_account_id, engagement_id
    )

    fixtures["all_six_sources"] = await create_asset_all_six_sources(
        db, client_account_id, engagement_id
    )

    return fixtures
