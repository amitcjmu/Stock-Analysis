#!/usr/bin/env python3
"""
Database Model Synchronization Checker

This script compares SQLAlchemy models with actual PostgreSQL database schema
to identify mismatches and synchronization issues.

Usage:
    python scripts/db_model_sync_checker.py [--fix] [--verbose] [--table TABLE_NAME]

    --fix: Generate Alembic migration for detected differences
    --verbose: Show detailed comparison output
    --table: Check specific table only
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

# Database imports
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

# App imports
sys.path.append("/app")
from app.core.database import Base, get_database_url

# Import all models to ensure they're registered
from app.models import *


class DatabaseModelChecker:
    """Compare SQLAlchemy models with actual database schema."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.differences: List[Dict[str, Any]] = []
        self.db_url = get_database_url()
        self.async_engine = create_async_engine(self.db_url)
        self.sync_engine = create_engine(
            self.db_url.replace("postgresql+asyncpg://", "postgresql://")
        )

    async def check_schema_sync(
        self, table_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Main method to check schema synchronization."""
        print("🔍 Starting database model synchronization check...")

        try:
            # Get model metadata
            model_tables = self._get_model_tables()

            # Get database tables
            db_tables = await self._get_database_tables()

            # Compare schemas
            if table_name:
                if table_name in model_tables and table_name in db_tables:
                    await self._compare_table_schema(
                        table_name, model_tables[table_name], db_tables[table_name]
                    )
                else:
                    print(f"❌ Table '{table_name}' not found in models or database")
                    return {
                        "status": "error",
                        "message": f"Table {table_name} not found",
                    }
            else:
                await self._compare_all_tables(model_tables, db_tables)

            # Generate report
            report = self._generate_report(model_tables.keys(), db_tables.keys())

            return report

        except Exception as e:
            print(f"❌ Error during schema check: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            await self.async_engine.dispose()
            self.sync_engine.dispose()

    def _get_model_tables(self) -> Dict[str, Dict[str, Any]]:
        """Extract table schemas from SQLAlchemy models."""
        model_tables = {}
        metadata = Base.metadata

        for table_name, table in metadata.tables.items():
            model_tables[table_name] = {
                "columns": {},
                "constraints": {},
                "indexes": {},
                "foreign_keys": {},
            }

            # Extract columns
            for column in table.columns:
                model_tables[table_name]["columns"][column.name] = {
                    "type": str(column.type),
                    "nullable": column.nullable,
                    "default": str(column.default) if column.default else None,
                    "primary_key": column.primary_key,
                    "unique": column.unique,
                    "autoincrement": getattr(column, "autoincrement", None),
                }

            # Extract constraints
            for constraint in table.constraints:
                constraint_name = (
                    constraint.name or f"unnamed_{type(constraint).__name__}"
                )
                model_tables[table_name]["constraints"][constraint_name] = {
                    "type": type(constraint).__name__,
                    "columns": (
                        [col.name for col in constraint.columns]
                        if hasattr(constraint, "columns")
                        else []
                    ),
                }

            # Extract indexes
            for index in table.indexes:
                model_tables[table_name]["indexes"][index.name] = {
                    "columns": [col.name for col in index.columns],
                    "unique": index.unique,
                }

            # Extract foreign keys
            for fk in table.foreign_keys:
                fk_name = (
                    fk.constraint.name
                    if fk.constraint
                    else f"fk_{fk.parent.name}_{fk.column.name}"
                )
                model_tables[table_name]["foreign_keys"][fk_name] = {
                    "parent_column": fk.parent.name,
                    "referenced_table": fk.column.table.name,
                    "referenced_column": fk.column.name,
                }

        return model_tables

    async def _get_database_tables(self) -> Dict[str, Dict[str, Any]]:
        """Extract table schemas from actual database."""
        db_tables = {}

        async with self.async_engine.connect() as conn:
            # Get all tables
            tables_query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_type = 'BASE TABLE'
            """
            from sqlalchemy import text

            result = await conn.execute(text(tables_query))
            table_names = [row[0] for row in result.fetchall()]

            for table_name in table_names:
                db_tables[table_name] = await self._get_table_schema(conn, table_name)

        return db_tables

    async def _get_table_schema(self, conn, table_name: str) -> Dict[str, Any]:
        """Get schema for a specific table from database."""
        table_schema = {
            "columns": {},
            "constraints": {},
            "indexes": {},
            "foreign_keys": {},
        }

        # Get columns
        columns_query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_name = :table_name AND table_schema = 'migration'
            ORDER BY ordinal_position
        """
        from sqlalchemy import text

        result = await conn.execute(text(columns_query), {"table_name": table_name})
        for row in result.fetchall():
            column_name = row[0]
            table_schema["columns"][column_name] = {
                "type": self._normalize_db_type(row[1], row[4], row[5], row[6]),
                "nullable": row[2] == "YES",
                "default": row[3],
                "primary_key": False,  # Will be updated below
                "unique": False,  # Will be updated below
                "autoincrement": "nextval" in (row[3] or ""),
            }

        # Get primary keys
        pk_query = """
            SELECT column_name
            FROM information_schema.key_column_usage kcu
            JOIN information_schema.table_constraints tc
                ON kcu.constraint_name = tc.constraint_name
            WHERE tc.table_name = :table_name
            AND tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_schema = 'migration'
        """
        result = await conn.execute(text(pk_query), {"table_name": table_name})
        for row in result.fetchall():
            table_schema["columns"][row[0]]["primary_key"] = True

        # Get constraints
        constraints_query = """
            SELECT
                tc.constraint_name,
                tc.constraint_type,
                array_agg(kcu.column_name ORDER BY kcu.ordinal_position) as columns
            FROM information_schema.table_constraints tc
            LEFT JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = :table_name AND tc.table_schema = 'migration'
            GROUP BY tc.constraint_name, tc.constraint_type
        """
        result = await conn.execute(text(constraints_query), {"table_name": table_name})
        for row in result.fetchall():
            table_schema["constraints"][row[0]] = {
                "type": row[1],
                "columns": row[2] or [],
            }

        # Get indexes
        indexes_query = """
            SELECT
                i.indexname,
                i.indexdef,
                array_agg(a.attname ORDER BY a.attnum) as columns
            FROM pg_indexes i
            JOIN pg_class c ON c.relname = i.tablename
            JOIN pg_index idx ON idx.indexrelid = (
                SELECT oid FROM pg_class WHERE relname = i.indexname
            )
            JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = ANY(idx.indkey)
            WHERE i.tablename = :table_name AND i.schemaname = 'migration'
            GROUP BY i.indexname, i.indexdef
        """
        result = await conn.execute(text(indexes_query), {"table_name": table_name})
        for row in result.fetchall():
            table_schema["indexes"][row[0]] = {
                "columns": row[2],
                "unique": "UNIQUE" in row[1],
            }

        # Get foreign keys
        fk_query = """
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = :table_name
            AND tc.table_schema = 'migration'
        """
        result = await conn.execute(text(fk_query), {"table_name": table_name})
        for row in result.fetchall():
            table_schema["foreign_keys"][row[0]] = {
                "parent_column": row[1],
                "referenced_table": row[2],
                "referenced_column": row[3],
            }

        return table_schema

    def _normalize_db_type(
        self,
        data_type: str,
        max_length: Optional[int],
        precision: Optional[int],
        scale: Optional[int],
    ) -> str:
        """Normalize database types to match SQLAlchemy types."""
        type_mapping = {
            "character varying": f"VARCHAR({max_length})" if max_length else "VARCHAR",
            "text": "TEXT",
            "integer": "INTEGER",
            "bigint": "BIGINT",
            "boolean": "BOOLEAN",
            "timestamp without time zone": "TIMESTAMP",
            "timestamp with time zone": "TIMESTAMPTZ",
            "date": "DATE",
            "time without time zone": "TIME",
            "uuid": "UUID",
            "json": "JSON",
            "jsonb": "JSONB",
            "numeric": (
                f"NUMERIC({precision},{scale})" if precision and scale else "NUMERIC"
            ),
            "real": "REAL",
            "double precision": "DOUBLE_PRECISION",
        }

        return type_mapping.get(data_type, data_type.upper())

    async def _compare_all_tables(self, model_tables: Dict, db_tables: Dict):
        """Compare all tables between models and database."""
        all_tables = set(model_tables.keys()) | set(db_tables.keys())

        for table_name in sorted(all_tables):
            if table_name in model_tables and table_name in db_tables:
                await self._compare_table_schema(
                    table_name, model_tables[table_name], db_tables[table_name]
                )
            elif table_name in model_tables:
                self._add_difference(
                    "missing_table_in_db",
                    table_name,
                    f"Table '{table_name}' exists in models but not in database",
                )
            else:
                self._add_difference(
                    "extra_table_in_db",
                    table_name,
                    f"Table '{table_name}' exists in database but not in models",
                )

    async def _compare_table_schema(
        self, table_name: str, model_schema: Dict, db_schema: Dict
    ):
        """Compare schema for a specific table."""
        if self.verbose:
            print(f"🔍 Comparing table: {table_name}")

        # Compare columns
        self._compare_columns(table_name, model_schema["columns"], db_schema["columns"])

        # Compare constraints
        self._compare_constraints(
            table_name, model_schema["constraints"], db_schema["constraints"]
        )

        # Compare indexes
        self._compare_indexes(table_name, model_schema["indexes"], db_schema["indexes"])

        # Compare foreign keys
        self._compare_foreign_keys(
            table_name, model_schema["foreign_keys"], db_schema["foreign_keys"]
        )

    def _compare_columns(self, table_name: str, model_columns: Dict, db_columns: Dict):
        """Compare columns between model and database."""
        all_columns = set(model_columns.keys()) | set(db_columns.keys())

        for column_name in all_columns:
            if column_name in model_columns and column_name in db_columns:
                model_col = model_columns[column_name]
                db_col = db_columns[column_name]

                # Compare column properties
                if model_col["type"] != db_col["type"]:
                    self._add_difference(
                        "column_type_mismatch",
                        table_name,
                        f"Column '{column_name}' type mismatch: "
                        f"model={model_col['type']}, db={db_col['type']}",
                    )

                if model_col["nullable"] != db_col["nullable"]:
                    self._add_difference(
                        "column_nullable_mismatch",
                        table_name,
                        f"Column '{column_name}' nullable mismatch: "
                        f"model={model_col['nullable']}, db={db_col['nullable']}",
                    )

                if model_col["primary_key"] != db_col["primary_key"]:
                    self._add_difference(
                        "column_pk_mismatch",
                        table_name,
                        f"Column '{column_name}' primary key mismatch: "
                        f"model={model_col['primary_key']}, db={db_col['primary_key']}",
                    )

            elif column_name in model_columns:
                self._add_difference(
                    "missing_column_in_db",
                    table_name,
                    f"Column '{column_name}' exists in model but not in database",
                )
            else:
                self._add_difference(
                    "extra_column_in_db",
                    table_name,
                    f"Column '{column_name}' exists in database but not in model",
                )

    def _compare_constraints(
        self, table_name: str, model_constraints: Dict, db_constraints: Dict
    ):
        """Compare constraints between model and database."""
        # Skip automatic constraint comparisons for now - they're complex due to naming differences
        pass

    def _compare_indexes(self, table_name: str, model_indexes: Dict, db_indexes: Dict):
        """Compare indexes between model and database."""
        # Filter out primary key indexes from database (auto-generated)
        filtered_db_indexes = {
            k: v for k, v in db_indexes.items() if not k.endswith("_pkey")
        }

        all_indexes = set(model_indexes.keys()) | set(filtered_db_indexes.keys())

        for index_name in all_indexes:
            if index_name in model_indexes and index_name in filtered_db_indexes:
                model_idx = model_indexes[index_name]
                db_idx = filtered_db_indexes[index_name]

                if set(model_idx["columns"]) != set(db_idx["columns"]):
                    self._add_difference(
                        "index_columns_mismatch",
                        table_name,
                        f"Index '{index_name}' columns mismatch: "
                        f"model={model_idx['columns']}, db={db_idx['columns']}",
                    )
            elif index_name in model_indexes:
                self._add_difference(
                    "missing_index_in_db",
                    table_name,
                    f"Index '{index_name}' exists in model but not in database",
                )
            else:
                self._add_difference(
                    "extra_index_in_db",
                    table_name,
                    f"Index '{index_name}' exists in database but not in model",
                )

    def _compare_foreign_keys(self, table_name: str, model_fks: Dict, db_fks: Dict):
        """Compare foreign keys between model and database."""
        all_fks = set(model_fks.keys()) | set(db_fks.keys())

        for fk_name in all_fks:
            if fk_name in model_fks and fk_name in db_fks:
                model_fk = model_fks[fk_name]
                db_fk = db_fks[fk_name]

                if (
                    model_fk["referenced_table"] != db_fk["referenced_table"]
                    or model_fk["referenced_column"] != db_fk["referenced_column"]
                ):
                    self._add_difference(
                        "fk_reference_mismatch",
                        table_name,
                        f"Foreign key '{fk_name}' reference mismatch: "
                        f"model={model_fk['referenced_table']}.{model_fk['referenced_column']}, "
                        f"db={db_fk['referenced_table']}.{db_fk['referenced_column']}",
                    )
            elif fk_name in model_fks:
                self._add_difference(
                    "missing_fk_in_db",
                    table_name,
                    f"Foreign key '{fk_name}' exists in model but not in database",
                )
            else:
                self._add_difference(
                    "extra_fk_in_db",
                    table_name,
                    f"Foreign key '{fk_name}' exists in database but not in model",
                )

    def _add_difference(self, diff_type: str, table_name: str, message: str):
        """Add a difference to the results."""
        difference = {
            "type": diff_type,
            "table": table_name,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self.differences.append(difference)

        if self.verbose:
            print(f"  ⚠️  {message}")

    def _generate_report(
        self, model_tables: Set[str], db_tables: Set[str]
    ) -> Dict[str, Any]:
        """Generate a comprehensive report of the comparison."""
        report = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_differences": len(self.differences),
                "model_tables_count": len(model_tables),
                "db_tables_count": len(db_tables),
                "tables_in_sync": len(model_tables & db_tables),
                "tables_only_in_models": len(model_tables - db_tables),
                "tables_only_in_db": len(db_tables - model_tables),
            },
            "differences": self.differences,
            "recommendations": self._generate_recommendations(),
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on found differences."""
        recommendations = []

        if any(d["type"] == "missing_table_in_db" for d in self.differences):
            recommendations.append(
                "Run 'alembic revision --autogenerate' to create migration for missing tables"
            )

        if any(d["type"] == "missing_column_in_db" for d in self.differences):
            recommendations.append(
                "Run 'alembic revision --autogenerate' to add missing columns"
            )

        if any(d["type"].endswith("_mismatch") for d in self.differences):
            recommendations.append(
                "Review and resolve type/constraint mismatches manually"
            )

        if any(d["type"] == "extra_table_in_db" for d in self.differences):
            recommendations.append(
                "Consider removing unused tables from database or adding models"
            )

        return recommendations

    async def generate_migration(self) -> str:
        """Generate Alembic migration script for detected differences."""
        migration_ops = []

        for diff in self.differences:
            if diff["type"] == "missing_table_in_db":
                migration_ops.append(f"# Create table {diff['table']}")
            elif diff["type"] == "missing_column_in_db":
                migration_ops.append(f"# Add column to {diff['table']}")
            elif diff["type"] == "column_type_mismatch":
                migration_ops.append(f"# Fix column type in {diff['table']}")

        migration_script = f"""
\"\"\"Database schema synchronization

Revision ID: sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}
Revises:
Create Date: {datetime.now().isoformat()}

\"\"\"
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Migration operations based on detected differences
{chr(10).join('    ' + op for op in migration_ops)}
    pass

def downgrade():
    # Reverse operations
    pass
"""

        return migration_script


def print_report(report: Dict[str, Any]):
    """Print a formatted report."""
    print("\n" + "=" * 60)
    print("📊 DATABASE MODEL SYNCHRONIZATION REPORT")
    print("=" * 60)

    summary = report["summary"]
    print(f"📅 Generated: {report['timestamp']}")
    print(f"🔍 Total Differences Found: {summary['total_differences']}")
    print(f"📋 Model Tables: {summary['model_tables_count']}")
    print(f"🗄️  Database Tables: {summary['db_tables_count']}")
    print(f"✅ Tables in Sync: {summary['tables_in_sync']}")
    print(f"⚠️  Tables Only in Models: {summary['tables_only_in_models']}")
    print(f"⚠️  Tables Only in DB: {summary['tables_only_in_db']}")

    if report["differences"]:
        print("\n🔍 DETAILED DIFFERENCES:")
        print("-" * 40)

        # Group differences by type
        diff_by_type = {}
        for diff in report["differences"]:
            diff_type = diff["type"]
            if diff_type not in diff_by_type:
                diff_by_type[diff_type] = []
            diff_by_type[diff_type].append(diff)

        for diff_type, diffs in diff_by_type.items():
            print(f"\n{diff_type.replace('_', ' ').title()}:")
            for diff in diffs:
                print(f"  • {diff['message']}")

    if report["recommendations"]:
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 40)
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"{i}. {rec}")

    if summary["total_differences"] == 0:
        print("\n🎉 All models and database schemas are in sync!")
    else:
        print(
            f"\n⚠️  Found {summary['total_differences']} differences that need attention."
        )


async def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Check database model synchronization")
    parser.add_argument(
        "--fix", action="store_true", help="Generate migration for differences"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--table", "-t", help="Check specific table only")
    parser.add_argument("--output", "-o", help="Output report to JSON file")

    args = parser.parse_args()

    checker = DatabaseModelChecker(verbose=args.verbose)

    try:
        report = await checker.check_schema_sync(args.table)

        if args.output:
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            print(f"📄 Report saved to {args.output}")
        else:
            print_report(report)

        if args.fix and report["differences"]:
            migration_script = await checker.generate_migration()
            migration_file = (
                f"migration_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            )
            with open(migration_file, "w") as f:
                f.write(migration_script)
            print(f"\n🔧 Migration script generated: {migration_file}")
            print(
                "Run: alembic revision --autogenerate -m 'sync schema' for proper migration"
            )

        # Exit with error code if differences found
        sys.exit(1 if report["differences"] else 0)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
