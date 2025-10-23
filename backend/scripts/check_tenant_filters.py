#!/usr/bin/env python3
"""
Pre-commit hook to check for missing multi-tenant filters in SQLAlchemy queries.

This script ensures all database queries include proper tenant scoping
(client_account_id and engagement_id) to prevent data leaks between tenants.

Usage:
    python backend/scripts/check_tenant_filters.py [files...]

Exit codes:
    0: No violations found
    1: Missing tenant filters detected

Override:
    Add comment '# SKIP_TENANT_CHECK' on the line to bypass validation
"""

import ast
import re
import sys
from pathlib import Path
from typing import List, Tuple, Set, Optional


# SQLAlchemy models that REQUIRE tenant scoping
TENANT_SCOPED_MODELS = {
    "CollectionFlow",
    "DiscoveryFlow",
    "AssessmentFlow",
    "Asset",
    "AssetDependency",
    "SixRAnalysis",
    "MigrationWave",
    "FieldMapping",
    "DataImport",
    "CrewAIFlowStateExtension",
    "EnhancedUserProfile",
    "TenantVendorProducts",
    "AssetProductLinks",
    "CollectionQuestionnaire",
    "CollectionQuestionnaireResponse",
    "ApplicationInfo",
}

# Required filter fields for tenant isolation
REQUIRED_FILTERS = {
    "client_account_id",
    "engagement_id",
}

# Files/directories to skip (test files, base classes, migrations)
SKIP_PATTERNS = [
    "/tests/",
    "/alembic/versions/",
    "/scripts/",
    "base_repository.py",
    "base.py",
    "demo_repository.py",  # Demo data doesn't need tenant scoping
]


class TenantFilterChecker(ast.NodeVisitor):
    """AST visitor to check SQLAlchemy queries for tenant filters."""

    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: List[Tuple[int, str, str]] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit assignments to detect query chains."""
        if isinstance(node.value, ast.Call):
            self._check_query(node.value)
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        """Visit return statements."""
        if node.value and isinstance(node.value, ast.Call):
            self._check_query(node.value)
        self.generic_visit(node)

    def _check_query(self, node: ast.Call) -> None:
        """Check if a call chain contains a select() with missing tenant filters."""
        # Find select() call and extract model
        model_name = self._find_select_model(node)
        if not model_name or model_name not in TENANT_SCOPED_MODELS:
            return

        # Extract all filters from the query chain
        filters = set()
        self._extract_filters_from_chain(node, filters)

        # Get query line number
        query_line = self._find_select_line(node)
        if not query_line:
            query_line = node.lineno

        # Check for skip comment
        if self._has_skip_comment(query_line):
            return

        # Check if this is a PK-only query
        if self._is_pk_only_query(filters, query_line):
            return

        # Check for missing tenant filters
        missing_filters = REQUIRED_FILTERS - filters
        if missing_filters:
            code_line = (
                self.source_lines[query_line - 1].strip()
                if query_line <= len(self.source_lines)
                else ""
            )
            missing_str = ", ".join(sorted(missing_filters))
            violation_msg = (
                f"Query on {model_name} missing tenant filters: {missing_str}"
            )
            self.violations.append((query_line, code_line, violation_msg))

    def _find_select_model(self, node: ast.AST) -> Optional[str]:
        """Recursively find the model name in a select() call."""
        if not isinstance(node, ast.Call):
            return None

        # Check if this call is select()
        if self._is_select_call(node):
            return self._extract_model_name(node)

        # Recurse into chained calls (e.g., select().where())
        if isinstance(node.func, ast.Attribute) and isinstance(
            node.func.value, ast.Call
        ):
            return self._find_select_model(node.func.value)

        return None

    def _find_select_line(self, node: ast.AST) -> Optional[int]:
        """Find the line number of the select() call."""
        if not isinstance(node, ast.Call):
            return None

        if self._is_select_call(node):
            return node.lineno

        if isinstance(node.func, ast.Attribute) and isinstance(
            node.func.value, ast.Call
        ):
            return self._find_select_line(node.func.value)

        return None

    def _extract_filters_from_chain(self, node: ast.AST, filters: Set[str]) -> None:
        """Recursively extract filter field names from the call chain."""
        if not isinstance(node, ast.Call):
            return

        # Extract filters from this call if it's a where/filter
        if self._is_filter_call(node):
            for arg in node.args:
                self._extract_filter_fields(arg, filters)

        # Recurse into chained calls
        if isinstance(node.func, ast.Attribute) and isinstance(
            node.func.value, ast.Call
        ):
            self._extract_filters_from_chain(node.func.value, filters)

    def _extract_filter_fields(self, node: ast.AST, filters: Set[str]) -> None:
        """Recursively extract filter field names from comparison nodes."""
        if isinstance(node, ast.Compare):
            # Handle Model.field == value or .field == value
            if isinstance(node.left, ast.Attribute):
                filters.add(node.left.attr)
        elif isinstance(node, ast.BoolOp):
            # Handle and_/or_ conditions
            for value in node.values:
                self._extract_filter_fields(value, filters)
        elif isinstance(node, ast.Call):
            # Handle and_(...) or or_(...) function calls
            for arg in node.args:
                self._extract_filter_fields(arg, filters)

    def _is_select_call(self, node: ast.Call) -> bool:
        """Check if node is a select() call."""
        if isinstance(node.func, ast.Name) and node.func.id == "select":
            return True
        if isinstance(node.func, ast.Attribute) and node.func.attr == "select":
            return True
        return False

    def _is_filter_call(self, node: ast.Call) -> bool:
        """Check if node is a where() or filter() call."""
        if isinstance(node.func, ast.Attribute):
            return node.func.attr in ("where", "filter", "filter_by")
        return False

    def _extract_model_name(self, node: ast.Call) -> Optional[str]:
        """Extract model name from select(Model) call."""
        if not node.args:
            return None

        arg = node.args[0]
        if isinstance(arg, ast.Name):
            return arg.id
        elif isinstance(arg, ast.Attribute):
            return arg.attr
        elif isinstance(arg, ast.Call) and hasattr(arg.func, "id"):
            # Handle select(func.count(Model))
            if arg.args and isinstance(arg.args[0], ast.Name):
                return arg.args[0].id

        return None

    def _is_pk_only_query(self, filters: Set[str], query_line: int) -> bool:
        """Check if this is a primary key only query (allowed)."""
        # Check if only filtering by .id field
        if filters == {"id"}:
            return True

        # Check source code for PK-only patterns
        PK_ONLY_PATTERNS = [
            r"\.where\(\s*\w+\.id\s*==",  # .where(Model.id == id)
            r"\.filter\(\s*\w+\.id\s*==",  # .filter(Model.id == id)
        ]

        start_line = max(0, query_line - 1)
        end_line = min(len(self.source_lines), query_line + 5)
        query_text = "\n".join(self.source_lines[start_line:end_line])

        for pattern in PK_ONLY_PATTERNS:
            if re.search(pattern, query_text):
                return True

        return False

    def _has_skip_comment(self, query_line: int) -> bool:
        """Check if query line has SKIP_TENANT_CHECK comment."""
        if query_line < 1 or query_line > len(self.source_lines):
            return False

        # Check current line and next few lines
        for offset in range(0, min(5, len(self.source_lines) - query_line + 1)):
            line_idx = query_line - 1 + offset
            if "SKIP_TENANT_CHECK" in self.source_lines[line_idx]:
                return True

        return False


def should_skip_file(file_path: str) -> bool:
    """Check if file should be skipped from tenant filter validation."""
    for pattern in SKIP_PATTERNS:
        if pattern in file_path:
            return True
    return False


def check_file(file_path: str) -> List[Tuple[int, str, str]]:
    """
    Check a single file for missing tenant filters.

    Returns:
        List of (line_number, line_content, violation_message) tuples
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
            source_lines = source.splitlines()

        tree = ast.parse(source, filename=file_path)
        checker = TenantFilterChecker(file_path, source_lines)
        checker.visit(tree)

        return checker.violations

    except SyntaxError as e:
        print(f"Warning: Syntax error in {file_path}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)
        return []


def main(files: List[str] = None) -> int:
    """
    Main entry point for tenant filter checking.

    Args:
        files: List of file paths to check. If None, checks all Python files in app/

    Returns:
        0 if no violations, 1 if violations found
    """
    if files is None:
        # Check all Python files in app directory
        app_dir = Path(__file__).parent.parent / "app"
        files = [str(f) for f in app_dir.rglob("*.py")]

    violations_found = False
    total_violations = 0

    for file_path in files:
        # Skip non-Python files
        if not file_path.endswith(".py"):
            continue

        # Skip excluded files
        if should_skip_file(file_path):
            continue

        # Check for violations
        violations = check_file(file_path)

        if violations:
            violations_found = True
            total_violations += len(violations)
            print(f"\n❌ {file_path}:")
            for line_num, line_content, message in violations:
                print(f"   Line {line_num}: {message}")
                print(f"   > {line_content}")

    if violations_found:
        print("\n" + "=" * 80)
        print("🚨 MISSING TENANT FILTERS DETECTED - SECURITY VIOLATION")
        print("=" * 80)
        print(f"\nFound {total_violations} violation(s)")
        print("\nAll queries on multi-tenant models MUST include:")
        print("  - client_account_id filter")
        print("  - engagement_id filter")
        print("\nCorrect usage:")
        print("  query = select(CollectionFlow).where(")
        print("      CollectionFlow.client_account_id == context.client_account_id,")
        print("      CollectionFlow.engagement_id == context.engagement_id")
        print("  )")
        print("\nTo bypass this check (use sparingly):")
        print("  query = select(Model).where(...)  # SKIP_TENANT_CHECK")
        print("\nSee CLAUDE.md for details on multi-tenant architecture.")
        print("=" * 80 + "\n")
        return 1
    else:
        print("✅ All queries properly scoped with tenant filters")
        return 0


if __name__ == "__main__":
    # Get files from command line args, or check all
    files = sys.argv[1:] if len(sys.argv) > 1 else None
    sys.exit(main(files))
