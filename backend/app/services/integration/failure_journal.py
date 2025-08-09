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
        # Resolve schema from dialect default; prefer 'migration' when available
        inspector = sa.inspect(db.bind)
        schema = (
            "migration"
            if "migration" in inspector.get_schema_names()
            else inspector.default_schema_name
        )

        # Guard: table must exist
        if not inspector.has_table("failure_journal", schema=schema):
            return

        table = sa.Table(
            "failure_journal",
            sa.MetaData(schema=schema),
            sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True)),
            sa.Column("client_account_id", sa.dialects.postgresql.UUID(as_uuid=True)),
            sa.Column("engagement_id", sa.dialects.postgresql.UUID(as_uuid=True)),
            sa.Column("source", sa.String(64)),
            sa.Column("operation", sa.String(128)),
            sa.Column("payload", sa.dialects.postgresql.JSONB),
            sa.Column("error_message", sa.Text()),
            sa.Column("trace", sa.Text()),
        )

        insert_stmt = sa.insert(table).values(
            id=str(uuid.uuid4()),
            client_account_id=str(client_account_id) if client_account_id else None,
            engagement_id=str(engagement_id) if engagement_id else None,
            source=source,
            operation=operation,
            payload=(payload or {}),
            error_message=error_message,
            trace=trace or traceback.format_exc(),
        )

        await db.execute(insert_stmt)
        await db.commit()
    except Exception:
        # Best-effort logging only; no re-raise
        try:
            await db.rollback()
        except Exception:
            pass
