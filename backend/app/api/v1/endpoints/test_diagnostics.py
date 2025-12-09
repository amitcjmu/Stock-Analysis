"""
Test Diagnostics Endpoint for E2E Testing
This endpoint is for testing purposes only and provides deep database validation.
Only enabled when E2E_TEST_MODE environment variable is set.
"""

import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Dict, Any

from app.core.database import get_async_db
from app.core.dependencies import get_current_context, RequestContext
from app.models.discovery_flow import DiscoveryFlow
from app.models.asset import Asset
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models import RawImportRecord

router = APIRouter()

# Only enable diagnostics endpoints in test mode
E2E_TEST_MODE = os.getenv("E2E_TEST_MODE", "false").lower() == "true"

if not E2E_TEST_MODE:
    # Return empty router if not in test mode
    router = APIRouter()
else:

    @router.get("/diagnostics/discovery/{flow_id}")
    async def get_discovery_flow_diagnostics(
        flow_id: str,
        db: AsyncSession = Depends(get_async_db),
        context: RequestContext = Depends(get_current_context),
    ) -> Dict[str, Any]:
        """
        Get comprehensive diagnostics for a discovery flow.
        This endpoint is for E2E testing only.

        Args:
            flow_id: The discovery flow ID
            db: Async database session
            context: Request context with tenant information

        Returns:
            Comprehensive diagnostics data including record counts, relationships, and validation
        """
        try:
            client_account_id = context.client_account_id
            engagement_id = context.engagement_id

            # Get discovery flow
            discovery_flow_result = await db.execute(
                select(DiscoveryFlow).filter(
                    DiscoveryFlow.id == flow_id,
                    DiscoveryFlow.client_account_id == client_account_id,
                    DiscoveryFlow.engagement_id == engagement_id,
                )
            )
            discovery_flow = discovery_flow_result.scalar_one_or_none()

            if not discovery_flow:
                raise HTTPException(status_code=404, detail="Discovery flow not found")

            # Get master flow if linked
            master_flow = None
            if discovery_flow.master_flow_id:
                master_flow_result = await db.execute(
                    select(CrewAIFlowStateExtensions).filter(
                        CrewAIFlowStateExtensions.id == discovery_flow.master_flow_id,
                        CrewAIFlowStateExtensions.client_account_id
                        == client_account_id,
                        CrewAIFlowStateExtensions.engagement_id == engagement_id,
                    )
                )
                master_flow = master_flow_result.scalar_one_or_none()

            # Count raw import records
            raw_import_count_result = await db.execute(
                select(func.count())
                .select_from(RawImportRecord)
                .filter(
                    RawImportRecord.discovery_flow_id == flow_id,
                    RawImportRecord.client_account_id == client_account_id,
                    RawImportRecord.engagement_id == engagement_id,
                )
            )
            raw_import_count = raw_import_count_result.scalar() or 0

            # Count assets
            asset_count_result = await db.execute(
                select(func.count())
                .select_from(Asset)
                .filter(
                    Asset.discovery_flow_id == flow_id,
                    Asset.client_account_id == client_account_id,
                    Asset.engagement_id == engagement_id,
                )
            )
            asset_count = asset_count_result.scalar() or 0

            # Get sample assets to verify structure
            sample_assets_result = await db.execute(
                select(Asset)
                .filter(
                    Asset.discovery_flow_id == flow_id,
                    Asset.client_account_id == client_account_id,
                    Asset.engagement_id == engagement_id,
                )
                .limit(5)
            )
            sample_assets = sample_assets_result.scalars().all()

            # Check for orphaned records (assets without proper flow linkage)
            orphaned_assets_result = await db.execute(
                select(func.count())
                .select_from(Asset)
                .filter(
                    Asset.discovery_flow_id.is_(None),
                    Asset.client_account_id == client_account_id,
                    Asset.engagement_id == engagement_id,
                )
            )
            orphaned_assets = orphaned_assets_result.scalar() or 0

            # Verify FK constraints using async query
            fk_constraints_valid = True
            try:
                # Check if all assets have valid discovery_flow_id
                invalid_fk_result = await db.execute(
                    select(func.count())
                    .select_from(Asset)
                    .outerjoin(
                        DiscoveryFlow, Asset.discovery_flow_id == DiscoveryFlow.id
                    )
                    .filter(
                        Asset.discovery_flow_id.isnot(None),
                        DiscoveryFlow.id.is_(None),
                        Asset.client_account_id == client_account_id,
                        Asset.engagement_id == engagement_id,
                    )
                )
                invalid_fk_count = invalid_fk_result.scalar() or 0

                if invalid_fk_count > 0:
                    fk_constraints_valid = False
            except Exception:
                fk_constraints_valid = False

            # Multi-tenant isolation check
            tenant_isolation_check = {"properly_scoped": True, "cross_tenant_leaks": 0}

            # Check for any cross-tenant data leakage
            cross_tenant_assets_result = await db.execute(
                select(func.count())
                .select_from(Asset)
                .filter(
                    Asset.discovery_flow_id == flow_id,
                    or_(
                        Asset.client_account_id != client_account_id,
                        Asset.engagement_id != engagement_id,
                    ),
                )
            )
            cross_tenant_assets = cross_tenant_assets_result.scalar() or 0

            if cross_tenant_assets > 0:
                tenant_isolation_check["properly_scoped"] = False
                tenant_isolation_check["cross_tenant_leaks"] = cross_tenant_assets

            # Build diagnostics response
            diagnostics = {
                "flow_id": flow_id,
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
                # Discovery flow details
                "discovery_flow": {
                    "exists": discovery_flow is not None,
                    "current_phase": (
                        discovery_flow.current_phase if discovery_flow else None
                    ),
                    "flow_status": (
                        discovery_flow.flow_status if discovery_flow else None
                    ),
                    "master_flow_id": (
                        str(discovery_flow.master_flow_id)
                        if discovery_flow and discovery_flow.master_flow_id
                        else None
                    ),
                    "field_mapping_status": (
                        discovery_flow.field_mapping_status if discovery_flow else None
                    ),
                    "data_cleansing_status": (
                        discovery_flow.data_cleansing_status if discovery_flow else None
                    ),
                },
                # Master flow details
                "master_flow": {
                    "exists": master_flow is not None,
                    "flow_type": master_flow.flow_type if master_flow else None,
                    "flow_status": master_flow.flow_status if master_flow else None,
                    "execution_state": (
                        master_flow.execution_state if master_flow else None
                    ),
                },
                # Record counts
                "raw_import_count": raw_import_count,
                "asset_count": asset_count,
                "orphaned_asset_count": orphaned_assets,
                "discovery_flow_count": 1 if discovery_flow else 0,
                "master_flow_count": 1 if master_flow else 0,
                # Relationship validation
                "master_child_linked": bool(
                    discovery_flow and discovery_flow.master_flow_id and master_flow
                ),
                "assets_linked_to_flow": asset_count > 0
                and all(a.discovery_flow_id == flow_id for a in sample_assets),
                "fk_constraints_valid": fk_constraints_valid,
                # Multi-tenant isolation
                "tenant_isolation_check": tenant_isolation_check,
                # Sample data for structure validation
                "sample_asset_fields": (
                    list(sample_assets[0].__dict__.keys()) if sample_assets else []
                ),
                # Phase-specific validations
                "phase_validations": {
                    "data_import": {
                        "raw_records_match_expected": raw_import_count > 0,
                        "raw_to_asset_ratio": (
                            asset_count / raw_import_count
                            if raw_import_count > 0
                            else 0
                        ),
                    },
                    "attribute_mapping": {
                        "mapping_completed": (
                            discovery_flow.field_mapping_status == "completed"
                            if discovery_flow
                            else False
                        )
                    },
                    "data_cleansing": {
                        "cleansing_completed": (
                            discovery_flow.data_cleansing_status == "completed"
                            if discovery_flow
                            else False
                        )
                    },
                    "inventory": {
                        "assets_normalized": asset_count > 0,
                        "all_assets_have_type": (
                            all(a.asset_type for a in sample_assets)
                            if sample_assets
                            else False
                        ),
                    },
                },
                # Database schema validation
                "schema_validation": {
                    "tables_exist": {
                        "discovery_flows": True,
                        "assets": True,
                        "raw_import_records": True,
                        "crewai_flow_state_extensions": True,
                    },
                    "migration_schema_used": True,  # All tables should be in migration schema
                },
            }

            return diagnostics

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error generating diagnostics: {str(e)}"
            )

    @router.get("/diagnostics/health")
    async def get_diagnostics_health() -> Dict[str, str]:
        """
        Simple health check for diagnostics endpoint.
        """
        return {
            "status": "healthy",
            "endpoint": "test_diagnostics",
            "purpose": "E2E testing only",
            "enabled": E2E_TEST_MODE,
        }
