"""
CustomAttributeValidator Service

Validates custom_attributes JSONB against client-specific JSON schemas.
Part of Issue #1240 - JSONB Schema Validation

Usage:
    validator = CustomAttributeValidator(db_session)
    is_valid, errors = await validator.validate(
        client_account_id=uuid,
        custom_attributes={"integration_count": 5, "data_sensitivity": "internal"}
    )

Features:
- Client-specific schema lookup with caching
- JSON Schema draft-07 validation
- Strict mode (reject) vs warning mode (log only)
- Backward compatible: no schema = no validation
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.custom_attribute_schema import CustomAttributeSchema

logger = logging.getLogger(__name__)

# Try to import jsonschema, provide graceful fallback
try:
    from jsonschema import Draft7Validator
    from jsonschema.exceptions import SchemaError

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    Draft7Validator = None  # type: ignore
    SchemaError = Exception  # type: ignore
    logger.warning(
        "jsonschema package not installed. "
        "CustomAttributeValidator will skip validation. "
        "Install with: pip install jsonschema"
    )


class CustomAttributeValidator:
    """
    Validates custom_attributes JSONB against client-specific JSON schemas.

    Thread-safe, async-compatible validator that caches schemas per client.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize validator with database session.

        Args:
            db: Async SQLAlchemy session for schema lookups
        """
        self.db = db
        # Cache maps (client_id, schema_name) -> Optional[CustomAttributeSchema]
        # Fixed typing per Qodo review
        self._schema_cache: Dict[Tuple[UUID, str], Optional[CustomAttributeSchema]] = {}
        # Locks prevent race conditions during concurrent schema fetches (Qodo review)
        self._locks: Dict[Tuple[UUID, str], asyncio.Lock] = {}

    async def validate(
        self,
        client_account_id: UUID,
        custom_attributes: Dict[str, Any],
        schema_name: str = "default",
    ) -> Tuple[bool, List[str]]:
        """
        Validate custom_attributes against client's active schema.

        Args:
            client_account_id: Client to validate for
            custom_attributes: The JSONB data to validate
            schema_name: Name of schema to use (default: "default")

        Returns:
            Tuple of (is_valid, list_of_error_messages)
            - If no schema exists: (True, []) - backward compatible
            - If valid: (True, [])
            - If invalid: (False, ["error1", "error2", ...])
        """
        if not JSONSCHEMA_AVAILABLE:
            logger.debug("jsonschema not available, skipping validation")
            return True, []

        if not custom_attributes:
            return True, []

        # Get schema for client
        schema_record = await self._get_active_schema(client_account_id, schema_name)

        if not schema_record:
            # No schema defined = no validation (backward compatible)
            return True, []

        json_schema = schema_record.json_schema
        strict_mode = schema_record.strict_mode

        # Validate against JSON Schema
        errors = self._validate_against_schema(custom_attributes, json_schema)

        if errors:
            if strict_mode:
                logger.warning(
                    f"Custom attributes validation FAILED (strict mode) for "
                    f"client {client_account_id}: {errors}"
                )
                return False, errors
            else:
                logger.info(
                    f"Custom attributes validation warnings for "
                    f"client {client_account_id}: {errors}"
                )
                # Return True but include warnings for logging/reporting
                return True, errors

        return True, []

    async def _get_active_schema(
        self,
        client_account_id: UUID,
        schema_name: str,
    ) -> Optional[CustomAttributeSchema]:
        """
        Get the active schema for a client.

        Caches results to avoid repeated database queries.
        Uses asyncio.Lock to prevent race conditions (Qodo review).

        Args:
            client_account_id: Client to get schema for
            schema_name: Name of schema to retrieve

        Returns:
            CustomAttributeSchema if found and active, None otherwise
        """
        cache_key = (client_account_id, schema_name)

        # Check cache first (simple in-memory cache)
        if cache_key in self._schema_cache:
            return self._schema_cache[cache_key]

        # Ensure only one fetch per key at a time (Qodo review - race condition fix)
        lock = self._locks.setdefault(cache_key, asyncio.Lock())
        async with lock:
            # Double-check after acquiring lock (another coroutine may have populated)
            if cache_key in self._schema_cache:
                return self._schema_cache[cache_key]

            # Query database for active schema (latest version)
            # Deterministic ordering with secondary criteria (Qodo review)
            stmt = (
                select(CustomAttributeSchema)
                .where(
                    CustomAttributeSchema.client_account_id == client_account_id,
                    CustomAttributeSchema.schema_name == schema_name,
                    CustomAttributeSchema.is_active == True,  # noqa: E712
                )
                .order_by(
                    CustomAttributeSchema.schema_version.desc(),
                    CustomAttributeSchema.created_at.desc(),
                    CustomAttributeSchema.id.desc(),
                )
                .limit(1)
            )

            result = await self.db.execute(stmt)
            schema_record = result.scalar_one_or_none()

            # Validate that stored schema is valid Draft-07 (Qodo review)
            if schema_record and JSONSCHEMA_AVAILABLE:
                try:
                    Draft7Validator.check_schema(schema_record.json_schema)
                except SchemaError as e:
                    logger.error(
                        "Invalid JSON Schema stored for client %s, name '%s', "
                        "version %s: %s",
                        client_account_id,
                        schema_name,
                        schema_record.schema_version,
                        e,
                    )
                    # Return None to skip validation with malformed schema
                    schema_record = None

            # Cache the result (including None for "no schema")
            self._schema_cache[cache_key] = schema_record

            return schema_record

    def _validate_against_schema(
        self,
        data: Dict[str, Any],
        json_schema: Dict[str, Any],
    ) -> List[str]:
        """
        Validate data against JSON Schema draft-07.

        Args:
            data: The data to validate
            json_schema: JSON Schema definition

        Returns:
            List of error messages (empty if valid)
        """
        if not JSONSCHEMA_AVAILABLE:
            return []

        validator = Draft7Validator(json_schema)
        errors = []

        for error in validator.iter_errors(data):
            # Format error message with path context
            path = ".".join(str(p) for p in error.absolute_path) or "(root)"
            errors.append(f"{path}: {error.message}")

        return errors

    def clear_cache(self, client_account_id: Optional[UUID] = None) -> None:
        """
        Clear schema cache.

        Args:
            client_account_id: If provided, clear only this client's cache.
                               If None, clear entire cache.
        """
        if client_account_id:
            keys_to_remove = [
                k for k in self._schema_cache if k[0] == client_account_id
            ]
            for key in keys_to_remove:
                del self._schema_cache[key]
        else:
            self._schema_cache.clear()

    async def create_schema(
        self,
        client_account_id: UUID,
        schema_name: str,
        json_schema: Dict[str, Any],
        description: Optional[str] = None,
        strict_mode: bool = False,
        created_by: Optional[str] = None,
    ) -> CustomAttributeSchema:
        """
        Create a new schema for a client.

        Automatically increments version if schema_name already exists.

        Args:
            client_account_id: Client to create schema for
            schema_name: Name for the schema
            json_schema: JSON Schema draft-07 definition
            description: Human-readable description
            strict_mode: Whether to reject invalid data
            created_by: User creating the schema

        Returns:
            Created CustomAttributeSchema record
        """
        # Get latest version for this schema name
        stmt = (
            select(CustomAttributeSchema.schema_version)
            .where(
                CustomAttributeSchema.client_account_id == client_account_id,
                CustomAttributeSchema.schema_name == schema_name,
            )
            .order_by(CustomAttributeSchema.schema_version.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        latest_version = result.scalar_one_or_none()
        new_version = (latest_version or 0) + 1

        # Deactivate previous versions
        if latest_version:
            deactivate_stmt = (
                CustomAttributeSchema.__table__.update()
                .where(
                    CustomAttributeSchema.client_account_id == client_account_id,
                    CustomAttributeSchema.schema_name == schema_name,
                )
                .values(is_active=False)
            )
            await self.db.execute(deactivate_stmt)

        # Create new schema
        new_schema = CustomAttributeSchema(
            client_account_id=client_account_id,
            schema_name=schema_name,
            schema_version=new_version,
            json_schema=json_schema,
            description=description,
            is_active=True,
            strict_mode=strict_mode,
            created_by=created_by,
        )
        self.db.add(new_schema)
        await self.db.flush()

        # Clear cache for this client
        self.clear_cache(client_account_id)

        return new_schema
