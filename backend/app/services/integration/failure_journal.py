from __future__ import annotations

from typing import Any, Dict, Optional

import traceback
import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession


async def log_failure(
    db: AsyncSession,
    *,
    client_account_id: Optional[str],
    engagement_id: Optional[str],
    source: str,
    operation: str,
    payload: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    trace: Optional[str] = None,
) -> None:
    """Persist a failure entry to the failure_journal if the table exists.

    Best-effort: errors are swallowed to avoid masking the original failure path.
    """
    try:
        # Resolve schema once and cache on the engine bind to avoid repeated reflection
        bind = db.bind
        cache_schema_key = "_failure_journal_schema"
        schema = getattr(bind, cache_schema_key, None)
        if not schema:
            inspector = sa.inspect(bind)
            try:
                schemas = inspector.get_schema_names()
            except Exception:
                schemas = []
            schema = (
                "migration" if "migration" in schemas else inspector.default_schema_name
            )
            setattr(bind, cache_schema_key, schema)

        # Guard: table must exist (cached per schema)
        cache_exists_key = f"_failure_journal_exists_{schema}"
        table_exists = getattr(bind, cache_exists_key, None)
        if table_exists is None:
            inspector2 = sa.inspect(bind)
            table_exists = inspector2.has_table("failure_journal", schema=schema)
            setattr(bind, cache_exists_key, table_exists)
        if not table_exists:
            return

        table = sa.Table(
            "failure_journal",
            sa.MetaData(schema=schema),
            sa.Column(
                "id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True
            ),
            sa.Column(
                "client_account_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                nullable=False,
            ),
            sa.Column(
                "engagement_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                nullable=False,
            ),
            sa.Column("source", sa.String(64), nullable=False),
            sa.Column("operation", sa.String(128), nullable=False),
            sa.Column("payload", sa.dialects.postgresql.JSONB, nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("trace", sa.Text(), nullable=True),
            # Include additional columns present in migration for schema parity
            sa.Column("retry_count", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )

        insert_stmt = sa.insert(table).values(
            id=uuid.uuid4(),
            client_account_id=(
                uuid.UUID(str(client_account_id)) if client_account_id else None
            ),
            engagement_id=uuid.UUID(str(engagement_id)) if engagement_id else None,
            source=source,
            operation=operation,
            payload=(payload or {}),
            error_message=error_message,
            trace=(
                trace
                if trace is not None
                else (
                    traceback.format_exc()
                    if traceback.format_exc() != "NoneType: None\n"
                    else None
                )
            ),
            retry_count=0,
        )

        await db.execute(insert_stmt)
        await db.commit()
    except Exception:
        # Best-effort logging only; no re-raise
        try:
            await db.rollback()
        except Exception:
            pass
