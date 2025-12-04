"""
Data Cleansing API - Resolution Helper Functions
Helper functions for resolution operations.
"""

import logging
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError, OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from app.models.data_import.core import RawImportRecord

logger = logging.getLogger(__name__)


async def ensure_resolution_table_exists(db: AsyncSession):
    """Ensure the data_quality_resolution table exists."""
    logger.info("🔨 [RESOLUTION] Checking if data_quality_resolution table exists...")
    table_exists = False
    try:
        check_table_stmt = text(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'data_quality_resolution'
            );
            """
        )
        table_check = await db.execute(check_table_stmt)
        table_exists = table_check.scalar()
        logger.info(
            f"📊 [RESOLUTION] Table 'data_quality_resolution' exists: {table_exists}"
        )
    except OperationalError as op_err:
        # Transient database connection issues (timeouts, connection lost)
        logger.warning(
            f"⚠️ [RESOLUTION] Operational error checking table existence (transient): {str(op_err)}"
        )
        try:
            await db.rollback()
        except SQLAlchemyError as rollback_err:
            logger.error(
                f"❌ [RESOLUTION] Failed to rollback after operational error: {str(rollback_err)}"
            )
        # Assume table doesn't exist if we can't check (will attempt creation)
        table_exists = False
    except ProgrammingError as prog_err:
        # Permanent SQL syntax or schema errors
        logger.error(
            f"❌ [RESOLUTION] Programming error checking table existence (permanent): {str(prog_err)}"
        )
        try:
            await db.rollback()
        except SQLAlchemyError as rollback_err:
            logger.error(
                f"❌ [RESOLUTION] Failed to rollback after programming error: {str(rollback_err)}"
            )
        raise
    except SQLAlchemyError as db_err:
        # Other SQLAlchemy errors (generic database errors)
        logger.error(
            f"❌ [RESOLUTION] Database error checking table existence: {str(db_err)}"
        )
        try:
            await db.rollback()
        except SQLAlchemyError as rollback_err:
            logger.error(
                f"❌ [RESOLUTION] Failed to rollback after database error: {str(rollback_err)}"
            )
        raise

    if not table_exists:
        await create_resolution_table(db)


async def create_resolution_table(db: AsyncSession):
    """Create the data_quality_resolution table with fallback strategies."""
    logger.info("🔨 [RESOLUTION] Table does not exist, attempting to create...")
    try:
        await db.execute(text("SAVEPOINT before_table_creation"))

        # Try with uuid_generate_v4() first
        create_stmt = text(
            """
            CREATE TABLE IF NOT EXISTS data_quality_resolution (
              id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
              flow_id TEXT NOT NULL,
              issue_id TEXT NOT NULL,
              field_name TEXT NOT NULL,
              field_value TEXT,
              record_identifier JSONB,
              updated_by TEXT NOT NULL,
              updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
        try:
            await db.execute(create_stmt)
            await db.execute(text("RELEASE SAVEPOINT before_table_creation"))
            logger.info(
                "✅ [RESOLUTION] Table created successfully (with uuid_generate_v4)"
            )
            return
        except (ProgrammingError, OperationalError, SQLAlchemyError) as e:
            # Any database error - try fallback
            error_type = type(e).__name__
            await db.execute(text("ROLLBACK TO SAVEPOINT before_table_creation"))
            logger.warning(
                f"⚠️ [RESOLUTION] Table creation with uuid_generate_v4 failed "
                f"({error_type}): {str(e)}, trying fallback..."
            )

            # Fallback: use gen_random_uuid()
            try:
                create_stmt_alt = text(
                    """
                    CREATE TABLE IF NOT EXISTS data_quality_resolution (
                      id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                      flow_id TEXT NOT NULL,
                      issue_id TEXT NOT NULL,
                      field_name TEXT NOT NULL,
                      field_value TEXT,
                      record_identifier JSONB,
                      updated_by TEXT NOT NULL,
                      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    """
                )
                await db.execute(create_stmt_alt)
                await db.execute(text("RELEASE SAVEPOINT before_table_creation"))
                logger.info(
                    "✅ [RESOLUTION] Fallback table creation with gen_random_uuid executed"
                )
                return
            except (ProgrammingError, OperationalError, SQLAlchemyError) as e2:
                # Any database error - try final fallback
                error_type2 = type(e2).__name__
                await db.execute(text("ROLLBACK TO SAVEPOINT before_table_creation"))
                logger.warning(
                    f"⚠️ [RESOLUTION] gen_random_uuid also failed ({error_type2}): {str(e2)}, trying final fallback..."
                )

                # Final fallback: no default, we'll generate UUIDs in Python
                create_stmt_final = text(
                    """
                    CREATE TABLE IF NOT EXISTS data_quality_resolution (
                      id UUID PRIMARY KEY,
                      flow_id TEXT NOT NULL,
                      issue_id TEXT NOT NULL,
                      field_name TEXT NOT NULL,
                      field_value TEXT,
                      record_identifier JSONB,
                      updated_by TEXT NOT NULL,
                      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    """
                )
                await db.execute(create_stmt_final)
                await db.execute(text("RELEASE SAVEPOINT before_table_creation"))
                logger.info(
                    "✅ [RESOLUTION] Final fallback table creation executed (no default UUID)"
                )
    except OperationalError as sp_op_err:
        # Transient connection issue during savepoint
        logger.error(
            f"❌ [RESOLUTION] Operational error during savepoint (transient): {str(sp_op_err)}"
        )
        try:
            await db.rollback()
            create_stmt_simple = text(
                """
                CREATE TABLE IF NOT EXISTS data_quality_resolution (
                  id UUID PRIMARY KEY,
                  flow_id TEXT NOT NULL,
                  issue_id TEXT NOT NULL,
                  field_name TEXT NOT NULL,
                  field_value TEXT,
                  record_identifier JSONB,
                  updated_by TEXT NOT NULL,
                  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            await db.execute(create_stmt_simple)
            logger.info("✅ [RESOLUTION] Table created after rollback (simple method)")
        except SQLAlchemyError as final_err:
            logger.error(
                f"❌ [RESOLUTION] Final table creation attempt failed: {str(final_err)}"
            )
            raise
    except ProgrammingError as sp_prog_err:
        # Permanent SQL syntax error during savepoint
        logger.error(
            f"❌ [RESOLUTION] Programming error during savepoint (permanent): {str(sp_prog_err)}"
        )
        try:
            await db.rollback()
        except SQLAlchemyError as rollback_err:
            logger.error(
                f"❌ [RESOLUTION] Failed to rollback after programming error: {str(rollback_err)}"
            )
        raise
    except SQLAlchemyError as sp_err:
        # Other SQLAlchemy errors during savepoint
        logger.error(f"❌ [RESOLUTION] Database error during savepoint: {str(sp_err)}")
        try:
            await db.rollback()
        except SQLAlchemyError as rollback_err:
            logger.error(
                f"❌ [RESOLUTION] Failed to rollback after database error: {str(rollback_err)}"
            )
        raise


async def get_resolutions(
    db: AsyncSession, flow_id: str, issue_id: str, field_name: str | None
):
    """Get resolution records from data_quality_resolution table."""
    if field_name:
        resolution_query = text(
            """
            SELECT field_name, field_value, record_identifier
            FROM data_quality_resolution
            WHERE flow_id = :flow_id AND issue_id = :issue_id AND field_name = :field_name
            """
        )
        resolution_result = await db.execute(
            resolution_query,
            {"flow_id": flow_id, "issue_id": issue_id, "field_name": field_name},
        )
    else:
        resolution_query = text(
            """
            SELECT field_name, field_value, record_identifier
            FROM data_quality_resolution
            WHERE flow_id = :flow_id AND issue_id = :issue_id
            """
        )
        resolution_result = await db.execute(
            resolution_query, {"flow_id": flow_id, "issue_id": issue_id}
        )
    return resolution_result.fetchall()


async def get_raw_records(db: AsyncSession, data_import_id):
    """Get raw import records for a data import."""
    raw_records_query = select(RawImportRecord).where(
        RawImportRecord.data_import_id == data_import_id
    )
    raw_records_result = await db.execute(raw_records_query)
    return raw_records_result.scalars().all()


def resolve_field_name_in_cleansed(
    field_name: str, cleansed_data: dict
) -> tuple[str, any]:
    """
    Resolve the actual field name in cleansed_data.
    Returns (resolved_field_name, current_value)

    Note: This function only searches in cleansed_data. If future fallback
    logic to raw_data is needed, the parameter can be added back.
    """

    def normalize(s: str) -> str:
        return "".join(ch for ch in s.lower() if ch.isalnum())

    # 1. Try exact match in cleansed_data
    if field_name in cleansed_data:
        return field_name, cleansed_data[field_name]

    # 2. Try case-insensitive match in cleansed_data
    field_norm = normalize(field_name)
    for key, value in cleansed_data.items():
        if normalize(key) == field_norm:
            logger.debug(
                f"🔍 [RESOLUTION] Found case-insensitive match in cleansed_data: '{key}' matches '{field_name}'"
            )
            return key, value

    # 3. Try common aliases
    alias_map = {
        "os": ["operating_system", "os", "os_name", "OS", "Operating_System"],
        "ip": ["ip", "ip_address", "ipaddr", "ipaddress", "IP_Address", "IPAddress"],
        "cpu": ["cpu", "cpu_cores", "processor", "vcpu", "CPU", "CPU_Cores"],
        "memory": ["memory", "memory_gb", "ram", "Memory_GB", "RAM"],
    }

    for alias, candidates in alias_map.items():
        if field_norm == normalize(alias) or any(
            normalize(c) == field_norm for c in candidates
        ):
            # Try each candidate in cleansed_data
            for cand in candidates:
                if cand in cleansed_data:
                    return cand, cleansed_data[cand]
                # Try case-insensitive
                for key, value in cleansed_data.items():
                    if normalize(key) == normalize(cand):
                        return key, value

    # 4. If not found, treat as empty (field doesn't exist in cleansed_data)
    return field_name, None


async def match_record_by_identifier(
    raw_records, res_record_identifier: dict, res_field_name: str
):
    """
    Match a raw record by identifier fields (excluding the target field).
    Returns (matched_record, resolved_cleansed_field_name) or (None, None)
    """
    target_field_lower = res_field_name.lower()

    for raw_record in raw_records:
        raw_data = raw_record.raw_data or {}
        cleansed_data = raw_record.cleansed_data or {}

        match_found = False
        match_details = []

        if res_record_identifier:
            # Strategy 1: Match on identifier fields EXCEPT the target field
            for data_source_name, data_source in [
                ("raw_data", raw_data),
                ("cleansed_data", cleansed_data),
            ]:
                if not data_source:
                    continue

                identifier_fields_match = True
                matched_fields = []

                for id_key, id_value in res_record_identifier.items():
                    if not id_value:
                        continue

                    # Skip the target field
                    id_key_lower = id_key.lower()
                    if id_key_lower == target_field_lower:
                        logger.debug(
                            f"⏭️ [RESOLUTION] Skipping identifier field '{id_key}' - "
                            f"it's the target field we're updating"
                        )
                        continue

                    id_value_normalized = str(id_value).strip().lower()
                    field_matched = False

                    # Try case-insensitive matching
                    for data_key, data_value in data_source.items():
                        data_key_lower = data_key.lower()
                        data_value_normalized = str(data_value).strip().lower()

                        if data_key_lower == id_key_lower:
                            match_details.append(
                                f"Key match in {data_source_name}: '{data_key}' == '{id_key}'"
                            )
                            if data_value_normalized == id_value_normalized:
                                field_matched = True
                                matched_fields.append(f"{id_key}='{id_value}'")
                                logger.debug(
                                    f"✅ [RESOLUTION] Field match in {data_source_name}: {id_key}='{id_value}'"
                                )
                                break
                            else:
                                match_details.append(
                                    f"  Value mismatch in {data_source_name}: '{data_value}' != '{id_value}'"
                                )
                                identifier_fields_match = False
                                break

                    if not field_matched:
                        identifier_fields_match = False
                        break

                if identifier_fields_match and matched_fields:
                    match_found = True
                    logger.info(
                        f"✅ [RESOLUTION] Matched raw_record {raw_record.id} "
                        f"on identifier fields (excluding target '{res_field_name}') "
                        f"in {data_source_name}: {', '.join(matched_fields)}"
                    )
                    break

            # Strategy 2: Value-only matching (excluding target field)
            if not match_found:
                for data_source_name, data_source in [
                    ("raw_data", raw_data),
                    ("cleansed_data", cleansed_data),
                ]:
                    if not data_source:
                        continue

                    identifier_matches = {}

                    for id_key, id_value in res_record_identifier.items():
                        if not id_value:
                            continue

                        id_key_lower = id_key.lower()
                        if id_key_lower == target_field_lower:
                            continue

                        id_value_normalized = str(id_value).strip().lower()

                        # Determine identifier type
                        is_ip = "ip" in id_key_lower or "address" in id_key_lower
                        is_hostname = (
                            "hostname" in id_key_lower or "host" in id_key_lower
                        )
                        is_name = "name" in id_key_lower
                        is_id = id_key_lower == "id"

                        for data_key, data_value in data_source.items():
                            data_value_normalized = str(data_value).strip().lower()
                            data_key_lower = data_key.lower()

                            if data_value_normalized == id_value_normalized:
                                key_matches = False
                                if is_ip and (
                                    "ip" in data_key_lower
                                    or "address" in data_key_lower
                                ):
                                    key_matches = True
                                elif is_hostname and (
                                    "hostname" in data_key_lower
                                    or "host" in data_key_lower
                                ):
                                    key_matches = True
                                elif is_name and "name" in data_key_lower:
                                    key_matches = True
                                elif is_id and data_key_lower == "id":
                                    key_matches = True
                                else:
                                    identifier_like_keys = [
                                        "ip",
                                        "hostname",
                                        "name",
                                        "id",
                                        "address",
                                        "host",
                                    ]
                                    key_matches = any(
                                        ident in data_key_lower
                                        for ident in identifier_like_keys
                                    )

                                if key_matches:
                                    identifier_matches[id_key] = (data_key, data_value)
                                    break

                    if identifier_matches:
                        match_found = True
                        matched_str = ", ".join(
                            [
                                f"{k}='{v[1]}' (as '{v[0]}')"
                                for k, v in identifier_matches.items()
                            ]
                        )
                        logger.info(
                            f"✅ [RESOLUTION] Matched raw_record {raw_record.id} "
                            f"on value-only in {data_source_name}: {matched_str}"
                        )
                        break

        if match_found:
            # Resolve field name and check if empty
            resolved_field_name, cleansed_field_value = resolve_field_name_in_cleansed(
                res_field_name, cleansed_data
            )

            is_empty_in_cleansed = cleansed_field_value is None or (
                isinstance(cleansed_field_value, str)
                and cleansed_field_value.strip() == ""
            )

            if is_empty_in_cleansed:
                return raw_record, resolved_field_name

    return None, None


async def update_cleansed_data(
    matched_record, resolved_field_name: str, field_value: str
) -> bool:
    """Update cleansed_data field in a raw import record."""
    try:
        # Get or initialize cleansed_data
        if matched_record.cleansed_data is None:
            cleansed_data = {}
            logger.debug(
                f"🔧 [RESOLUTION] Initializing cleansed_data for raw_record {matched_record.id} (was None)"
            )
        else:
            cleansed_data = dict(matched_record.cleansed_data)

        # Update the field value
        cleansed_data[resolved_field_name] = field_value

        # Update the record
        matched_record.cleansed_data = cleansed_data
        flag_modified(matched_record, "cleansed_data")

        logger.debug(
            f"📝 [RESOLUTION] Full cleansed_data after update: {cleansed_data}"
        )
        return True
    except OperationalError as op_err:
        # Transient connection issues during update
        logger.error(
            f"❌ [RESOLUTION] Operational error updating raw_record {matched_record.id} (transient): {str(op_err)}"
        )
        raise
    except ProgrammingError as prog_err:
        # Permanent SQL or schema errors during update
        logger.error(
            f"❌ [RESOLUTION] Programming error updating raw_record {matched_record.id} (permanent): {str(prog_err)}"
        )
        raise
    except SQLAlchemyError as db_err:
        # Other database errors during update
        logger.error(
            f"❌ [RESOLUTION] Database error updating raw_record {matched_record.id}: {str(db_err)}"
        )
        raise
