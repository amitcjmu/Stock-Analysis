"""
Vendor Products API endpoints for Collection Gaps Phase 2.

This module provides endpoints for managing vendor product catalog,
including search, create, update, delete, and normalize operations.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_request_context, RequestContext
from app.models.api.collection_gaps import (
    StandardErrorResponse,
    VendorProductCreateRequest,
    VendorProductResponse,
)
from app.repositories.vendor_product_repository import (
    TenantVendorProductRepository,
    VendorProductRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vendor-products")


@router.get(
    "",
    response_model=List[VendorProductResponse],
    responses={
        400: {"model": StandardErrorResponse},
        500: {"model": StandardErrorResponse},
    },
    summary="Search vendor products catalog",
    description=(
        "Search vendor products by name patterns with unified results "
        "from global catalog and tenant overrides."
    ),
)
async def search_vendor_products(
    vendor_name: Optional[str] = Query(
        None, description="Vendor name pattern (case-insensitive)"
    ),
    product_name: Optional[str] = Query(
        None, description="Product name pattern (case-insensitive)"
    ),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> List[VendorProductResponse]:
    """
    Search vendor products catalog with unified results.

    Combines global catalog entries with tenant-specific overrides,
    giving priority to tenant customizations.
    """
    try:
        # Initialize repositories with tenant context
        tenant_repo = TenantVendorProductRepository(
            db, context.client_account_id, context.engagement_id
        )

        # Search unified products (handles both global and tenant)
        unified_products = await tenant_repo.search_unified_products(
            vendor_name=vendor_name, product_name=product_name
        )

        # Convert to response models and apply limit
        limited_products = unified_products[:limit]

        results = []
        for product in limited_products:
            results.append(
                VendorProductResponse(
                    id=product["id"],
                    vendor_name=product["vendor_name"],
                    product_name=product["product_name"],
                    versions=None,  # TODO: Load versions if needed
                )
            )

        logger.info(
            f"✅ Retrieved {len(results)} vendor products for "
            f"client {context.client_account_id}, engagement {context.engagement_id}"
        )

        return results

    except Exception as e:
        logger.error(f"❌ Failed to search vendor products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "search_failed",
                "message": f"Failed to search vendor products: {str(e)}",
                "details": {
                    "vendor_name": vendor_name,
                    "product_name": product_name,
                },
            },
        )


@router.post(
    "",
    response_model=VendorProductResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": StandardErrorResponse},
        409: {"model": StandardErrorResponse},
        500: {"model": StandardErrorResponse},
    },
    summary="Create vendor product entry",
    description="Create a new tenant-specific vendor product entry.",
)
async def create_vendor_product(
    request: VendorProductCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> VendorProductResponse:
    """
    Create a new tenant-specific vendor product.

    Creates a custom product entry for the current tenant,
    not in the global catalog.
    """
    try:
        async with db.begin():
            # Initialize tenant repository
            tenant_repo = TenantVendorProductRepository(
                db, context.client_account_id, context.engagement_id
            )

            # Create custom tenant product
            created_product = await tenant_repo.create_custom_product(
                vendor_name=request.vendor_name,
                product_name=request.product_name,
                commit=False,  # Will commit with transaction
            )

            await db.flush()  # Ensure ID is available

            result = VendorProductResponse(
                id=str(created_product.id),
                vendor_name=request.vendor_name,
                product_name=request.product_name,
                versions=None,
            )

            logger.info(
                f"✅ Created vendor product {created_product.id} for "
                f"client {context.client_account_id}, engagement {context.engagement_id}"
            )

            return result

    except Exception as e:
        logger.error(f"❌ Failed to create vendor product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "creation_failed",
                "message": f"Failed to create vendor product: {str(e)}",
                "details": {
                    "vendor_name": request.vendor_name,
                    "product_name": request.product_name,
                },
            },
        )


@router.put(
    "/{product_id}",
    response_model=VendorProductResponse,
    responses={
        400: {"model": StandardErrorResponse},
        404: {"model": StandardErrorResponse},
        500: {"model": StandardErrorResponse},
    },
    summary="Update vendor product entry",
    description="Update an existing tenant vendor product entry.",
)
async def update_vendor_product(
    product_id: str,
    request: VendorProductCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> VendorProductResponse:
    """
    Update an existing tenant vendor product.

    Only tenant-specific products can be updated through this endpoint.
    """
    try:
        # Validate UUID format
        try:
            product_uuid = UUID(product_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": "invalid_uuid",
                    "message": "Invalid product ID format",
                    "details": {"product_id": product_id},
                },
            )

        async with db.begin():
            # Initialize tenant repository
            tenant_repo = TenantVendorProductRepository(
                db, context.client_account_id, context.engagement_id
            )

            # Update the product
            updated_product = await tenant_repo.update(
                str(product_uuid),
                commit=False,
                custom_vendor_name=request.vendor_name,
                custom_product_name=request.product_name,
            )

            if not updated_product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "error": "product_not_found",
                        "message": "Vendor product not found",
                        "details": {"product_id": product_id},
                    },
                )

            result = VendorProductResponse(
                id=str(updated_product.id),
                vendor_name=request.vendor_name,
                product_name=request.product_name,
                versions=None,
            )

            logger.info(
                f"✅ Updated vendor product {product_id} for "
                f"client {context.client_account_id}, engagement {context.engagement_id}"
            )

            return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update vendor product {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "update_failed",
                "message": f"Failed to update vendor product: {str(e)}",
                "details": {"product_id": product_id},
            },
        )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": StandardErrorResponse},
        404: {"model": StandardErrorResponse},
        500: {"model": StandardErrorResponse},
    },
    summary="Delete vendor product entry",
    description="Delete a tenant vendor product entry.",
)
async def delete_vendor_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> None:
    """
    Delete a tenant vendor product.

    Only tenant-specific products can be deleted through this endpoint.
    Global catalog entries cannot be deleted.
    """
    try:
        # Validate UUID format
        try:
            product_uuid = UUID(product_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": "invalid_uuid",
                    "message": "Invalid product ID format",
                    "details": {"product_id": product_id},
                },
            )

        async with db.begin():
            # Initialize tenant repository
            tenant_repo = TenantVendorProductRepository(
                db, context.client_account_id, context.engagement_id
            )

            # Check if product exists
            existing = await tenant_repo.get_by_id(str(product_uuid))
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "error": "product_not_found",
                        "message": "Vendor product not found",
                        "details": {"product_id": product_id},
                    },
                )

            # Delete the product
            await tenant_repo.delete(str(product_uuid), commit=False)

            logger.info(
                f"✅ Deleted vendor product {product_id} for "
                f"client {context.client_account_id}, engagement {context.engagement_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete vendor product {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "deletion_failed",
                "message": f"Failed to delete vendor product: {str(e)}",
                "details": {"product_id": product_id},
            },
        )


@router.post(
    "/normalize",
    response_model=Dict[str, Any],
    responses={
        400: {"model": StandardErrorResponse},
        500: {"model": StandardErrorResponse},
    },
    summary="Normalize vendor product data",
    description="Normalize vendor/product names for consistent matching.",
)
async def normalize_vendor_product_data(
    request: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """
    Normalize vendor product data for consistent matching.

    Takes raw vendor/product names and returns normalized versions
    along with potential matches from the catalog.
    """
    try:
        vendor_name = request.get("vendor_name", "").strip()
        product_name = request.get("product_name", "").strip()

        if not vendor_name or not product_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": "missing_required_fields",
                    "message": "Both vendor_name and product_name are required",
                    "details": request,
                },
            )

        # Initialize repositories
        global_repo = VendorProductRepository(db)
        tenant_repo = TenantVendorProductRepository(
            db, context.client_account_id, context.engagement_id
        )

        # Generate normalized key
        normalized_key = f"{vendor_name.lower().replace(' ', '_')}_{product_name.lower().replace(' ', '_')}"

        # Search for potential matches
        potential_matches = await tenant_repo.search_unified_products(
            vendor_name=vendor_name, product_name=product_name
        )

        # Find exact normalized key match
        exact_match = await global_repo.get_by_normalized_key(normalized_key)

        result = {
            "original": {
                "vendor_name": vendor_name,
                "product_name": product_name,
            },
            "normalized": {
                "vendor_name": vendor_name.strip(),
                "product_name": product_name.strip(),
                "normalized_key": normalized_key,
            },
            "exact_match": (
                {
                    "id": str(exact_match.id),
                    "vendor_name": exact_match.vendor_name,
                    "product_name": exact_match.product_name,
                }
                if exact_match
                else None
            ),
            "potential_matches": potential_matches[:5],  # Limit to top 5
            "confidence_score": 1.0 if exact_match else 0.0,
        }

        logger.info(
            f"✅ Normalized vendor product data for "
            f"client {context.client_account_id}, engagement {context.engagement_id}"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to normalize vendor product data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "normalization_failed",
                "message": f"Failed to normalize vendor product data: {str(e)}",
                "details": request,
            },
        )
