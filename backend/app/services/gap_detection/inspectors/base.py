"""
Base inspector interface for all gap detection inspectors.

All inspectors MUST:
1. Be async (GPT-5 Rec #3) - NEVER use sync methods
2. Accept tenant scoping parameters (GPT-5 Rec #1) - client_account_id and engagement_id
3. Return Pydantic models with clamped scores (GPT-5 Rec #8)
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession


class BaseInspector(ABC):
    """
    Base interface for all gap inspectors.

    ALL inspectors MUST be async (GPT-5 Rec #3).
    ALL inspectors MUST accept tenant scoping parameters (GPT-5 Rec #1).

    Design Philosophy:
    - Single responsibility: Each inspector checks ONE data layer
    - Composition over inheritance: Inspectors are composed by GapAnalyzer
    - Async-first: All methods are async for database compatibility
    - Type-safe: All reports use Pydantic models
    """

    @abstractmethod
    async def inspect(
        self,
        asset: Any,
        application: Optional[Any],
        requirements: Any,
        client_account_id: str,
        engagement_id: str,
        db: Optional[AsyncSession] = None,
    ) -> Any:
        """
        Inspect asset for gaps in this data layer.

        IMPORTANT: This MUST be async def (GPT-5 Rec #3). Never sync.

        Args:
            asset: Asset SQLAlchemy model to inspect
            application: Optional CanonicalApplication (for application inspector)
            requirements: DataRequirements with context-aware needs
            client_account_id: Tenant client account UUID (GPT-5 Rec #1)
            engagement_id: Engagement UUID (GPT-5 Rec #1)
            db: Async database session (only for standards inspector)

        Returns:
            Inspector-specific report (ColumnGapReport, EnrichmentGapReport, etc.)

        Raises:
            ValueError: If required parameters are missing or invalid
            Exception: Database or validation errors
        """
        pass
