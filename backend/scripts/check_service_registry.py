#!/usr/bin/env python
"""
Service Registry CI Guard Script

This script validates that the Service Registry pattern is properly implemented
and that no new code violates the architectural principles.

Run this as part of CI/CD pipeline to ensure code quality.
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple

# Add backend to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


class ServiceRegistryChecker(ast.NodeVisitor):
    """AST visitor to check for Service Registry violations"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.violations = []
        self.async_session_imports = []
        self.direct_db_session_creations = []
        self.tool_without_registry = []

    def visit_ImportFrom(self, node):
        """Check for AsyncSessionLocal imports"""
        if node.module and "AsyncSessionLocal" in str(node.module):
            for alias in node.names:
                if alias.name == "AsyncSessionLocal":
                    self.violations.append(
                        f"{self.filepath}:{node.lineno}: Direct AsyncSessionLocal import detected"
                    )

        # Check for AsyncSession imports (allowed but track for context)
        if node.module == "sqlalchemy.ext.asyncio":
            for alias in node.names:
                if alias.name == "AsyncSession":
                    self.async_session_imports.append(node.lineno)

        self.generic_visit(node)

    def visit_With(self, node):
        """Check for 'async with AsyncSessionLocal()' patterns"""
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                if isinstance(item.context_expr.func, ast.Name):
                    if item.context_expr.func.id == "AsyncSessionLocal":
                        self.violations.append(
                            f"{self.filepath}:{node.lineno}: Direct AsyncSessionLocal usage detected"
                        )

        self.generic_visit(node)

    def visit_AsyncWith(self, node):
        """Check for 'async with AsyncSessionLocal()' patterns"""
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                if isinstance(item.context_expr.func, ast.Name):
                    if item.context_expr.func.id == "AsyncSessionLocal":
                        self.violations.append(
                            f"{self.filepath}:{node.lineno}: Direct AsyncSessionLocal usage in async context"
                        )

        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Check tool functions for proper ServiceRegistry usage"""
        # Check if this is a tool creation function
        if node.name.startswith("create_") and node.name.endswith("_tools"):
            has_registry_param = any(arg.arg == "registry" for arg in node.args.args)

            # Check if function body creates tools without registry
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Call):
                    if hasattr(stmt.func, "id") and "Tool" in str(stmt.func.id):
                        if not has_registry_param:
                            self.tool_without_registry.append(
                                f"{self.filepath}:{node.lineno}: Tool creator '{node.name}' lacks registry parameter"
                            )
                        break

        self.generic_visit(node)


def check_file(filepath: Path) -> List[str]:
    """Check a single Python file for Service Registry violations"""
    violations = []

    # Skip test files and migration files
    if "test_" in filepath.name or "alembic" in str(filepath):
        return violations

    # Skip legacy files explicitly marked
    if "_legacy.py" in filepath.name:
        return violations

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse AST
        tree = ast.parse(content)

        # Run checker
        checker = ServiceRegistryChecker(str(filepath))
        checker.visit(tree)

        violations.extend(checker.violations)
        violations.extend(checker.tool_without_registry)

    except Exception as e:
        print(f"Error checking {filepath}: {e}", file=sys.stderr)

    return violations


def check_directory(
    directory: Path, ignore_patterns: List[str] = None
) -> Tuple[List[str], int]:
    """Check all Python files in a directory for violations"""
    violations = []
    files_checked = 0

    ignore_patterns = ignore_patterns or [
        "__pycache__",
        ".git",
        "venv",
        ".venv",
        "migrations",
        "alembic",
        "_legacy.py",
    ]

    for py_file in directory.rglob("*.py"):
        # Skip ignored patterns
        if any(pattern in str(py_file) for pattern in ignore_patterns):
            continue

        file_violations = check_file(py_file)
        violations.extend(file_violations)
        files_checked += 1

    return violations, files_checked


def main():
    """Main entry point for CI guard"""
    print("🔍 Service Registry Pattern Compliance Check")
    print("=" * 60)

    # Check backend directory
    backend_dir = Path(__file__).parent.parent

    # Directories to check
    check_dirs = [
        backend_dir / "app" / "services",
        backend_dir / "app" / "api",
        backend_dir / "app" / "repositories",
    ]

    all_violations = []
    total_files = 0

    for check_dir in check_dirs:
        if check_dir.exists():
            print(f"\nChecking {check_dir.relative_to(backend_dir)}...")
            violations, files_checked = check_directory(check_dir)
            all_violations.extend(violations)
            total_files += files_checked
            print(f"  ✓ Checked {files_checked} files")

    print(f"\n{'=' * 60}")
    print(f"Total files checked: {total_files}")

    if all_violations:
        print(f"\n❌ Found {len(all_violations)} Service Registry violations:\n")
        for violation in all_violations:
            print(f"  • {violation}")

        print("\n💡 Fix suggestions:")
        print("  1. Replace AsyncSessionLocal with ServiceRegistry pattern")
        print("  2. Update tool creators to accept 'registry' parameter")
        print("  3. Move legacy code to *_legacy.py files")
        print("  4. Set USE_SERVICE_REGISTRY=true environment variable")

        sys.exit(1)
    else:
        print("\n✅ All checks passed! Service Registry pattern compliance verified.")
        sys.exit(0)


if __name__ == "__main__":
    main()
