"""
EOL Lifecycle Service Pydantic Models

ADR-039: Provides data models for EOL status information.
"""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EOLStatusEnum(str, Enum):
    """EOL status classification."""

    ACTIVE = "active"  # Product actively supported
    EOL_SOON = "eol_soon"  # Within 12 months of EOL
    EOL_EXPIRED = "eol_expired"  # Past EOL date
    UNKNOWN = "unknown"  # Unable to determine


class SupportTypeEnum(str, Enum):
    """Type of vendor support available."""

    MAINSTREAM = "mainstream"  # Full support with updates
    EXTENDED = "extended"  # Security updates only
    NONE = "none"  # No support


class EOLDataSource(str, Enum):
    """Source of EOL information."""

    ENDOFLIFE_DATE = "endoflife.date"
    VENDOR_CATALOG = "vendor_catalog"
    FALLBACK_HEURISTICS = "fallback_heuristics"


class EOLStatus(BaseModel):
    """
    EOL status result for a product/version combination.

    Returned by EOLLifecycleService.get_eol_status().
    """

    product: str = Field(
        ..., description="Product name (e.g., 'windows-server', 'java')"
    )
    version: str = Field(..., description="Version string (e.g., '2012', '8')")
    product_type: str = Field(
        default="os",
        description="Product type: os, runtime, database, framework",
    )
    status: EOLStatusEnum = Field(
        default=EOLStatusEnum.UNKNOWN,
        description="EOL status classification",
    )
    eol_date: Optional[date] = Field(
        default=None,
        description="End of Life date if known",
    )
    extended_support_end: Optional[date] = Field(
        default=None,
        description="Extended support end date if applicable",
    )
    support_type: SupportTypeEnum = Field(
        default=SupportTypeEnum.NONE,
        description="Current support type",
    )
    source: EOLDataSource = Field(
        default=EOLDataSource.FALLBACK_HEURISTICS,
        description="Where this EOL information came from",
    )
    lts: Optional[bool] = Field(
        default=None,
        description="Whether this is a Long Term Support version",
    )
    latest_version: Optional[str] = Field(
        default=None,
        description="Latest available version of this product",
    )
    release_date: Optional[date] = Field(
        default=None,
        description="Original release date of this version",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence score for this EOL assessment",
    )

    class Config:
        """Pydantic model config."""

        use_enum_values = True
        json_schema_extra = {
            "example": {
                "product": "windows-server",
                "version": "2012",
                "product_type": "os",
                "status": "eol_expired",
                "eol_date": "2023-10-10",
                "support_type": "none",
                "source": "endoflife.date",
                "confidence": 0.95,
            }
        }


class EOLBatchResult(BaseModel):
    """Result of batch EOL lookup."""

    results: list[EOLStatus] = Field(default_factory=list)
    total_queried: int = Field(default=0)
    from_cache: int = Field(default=0)
    from_api: int = Field(default=0)
    from_fallback: int = Field(default=0)
    errors: list[str] = Field(default_factory=list)
