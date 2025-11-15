#!/usr/bin/env python3
"""
Pre-commit hook to enforce LLM observability instrumentation.

Detects CrewAI task execution and LLM calls that bypass observability tracking.
Prevents regressions in monitoring coverage for Grafana dashboards.

Usage:
    python backend/scripts/check_llm_observability.py

Exit Codes:
    0 - All LLM calls properly instrumented
    1 - Observability violations found

Detection Rules:
    - CRITICAL: task.execute_async() without CallbackHandler in scope
    - ERROR: Direct litellm.completion() calls (use multi_model_service)
    - WARNING: crew.kickoff() without callbacks parameter

Per OBSERVABILITY_ENFORCEMENT_PLAN.md Phase 4
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


class LLMCallDetector(ast.NodeVisitor):
    """Detect LLM calls that bypass observability."""

    def __init__(self, file_content: str):
        self.violations = []
        self.has_callback_handler = False
        self.file_lines = file_content.split("\n")

    def _has_exemption_comment(self, lineno: int) -> bool:
        """Check if line has an OBSERVABILITY exemption comment."""
        if lineno <= 0 or lineno > len(self.file_lines):
            return False

        # Check current line and previous 2 lines for exemption comment
        for i in range(max(0, lineno - 3), lineno):
            if i < len(self.file_lines):
                line = self.file_lines[i]
                if "OBSERVABILITY:" in line and "tracking not needed" in line:
                    return True
        return False

    def visit_Call(self, node):
        """Check function calls for observability patterns."""

        # Check for task.execute_async() without callback
        if hasattr(node.func, "attr") and node.func.attr == "execute_async":
            # Check if CallbackHandler is in scope or exemption comment exists
            if not self.has_callback_handler and not self._has_exemption_comment(
                node.lineno
            ):
                self.violations.append(
                    (
                        node.lineno,
                        "task.execute_async() called without CallbackHandler",
                        "CRITICAL",
                    )
                )

        # Check for direct litellm.completion() calls
        if (
            hasattr(node.func, "attr")
            and node.func.attr == "completion"
            and hasattr(node.func.value, "id")
            and node.func.value.id == "litellm"
        ):
            self.violations.append(
                (
                    node.lineno,
                    "Direct litellm.completion() call - use multi_model_service instead",
                    "ERROR",
                )
            )

        # Check for crew.kickoff() without callbacks
        if hasattr(node.func, "attr") and node.func.attr in [
            "kickoff",
            "kickoff_async",
        ]:
            # Check if callbacks parameter is provided
            has_callbacks = any(kw.arg == "callbacks" for kw in node.keywords)
            if not has_callbacks and not self.has_callback_handler:
                self.violations.append(
                    (
                        node.lineno,
                        "crew.kickoff() called without callbacks parameter",
                        "WARNING",
                    )
                )

        self.generic_visit(node)

    def visit_Import(self, node):
        """Track imports of callback handlers."""
        for alias in node.names:
            if "CallbackHandler" in alias.name:
                self.has_callback_handler = True
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Track from imports of callback handlers."""
        if node.module and "callback_handler" in node.module:
            self.has_callback_handler = True
        self.generic_visit(node)


def check_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """Check a Python file for observability violations."""
    try:
        with open(file_path, "r") as f:
            content = f.read()
            tree = ast.parse(content, filename=str(file_path))

        detector = LLMCallDetector(content)
        detector.visit(tree)
        return detector.violations
    except SyntaxError:
        return []


def main():
    """Run pre-commit checks on staged Python files."""
    # Get staged Python files from git
    import subprocess

    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
    )

    files = [
        Path(f)
        for f in result.stdout.strip().split("\n")
        if f.endswith(".py") and "backend/app" in f
    ]

    all_violations = []
    for file_path in files:
        if not file_path.exists():
            continue

        violations = check_file(file_path)
        if violations:
            all_violations.append((file_path, violations))

    if all_violations:
        print("\n❌ LLM Observability Violations Found:\n")

        for file_path, violations in all_violations:
            print(f"📁 {file_path}")
            for lineno, msg, severity in violations:
                icon = (
                    "🚨"
                    if severity == "CRITICAL"
                    else "⚠️" if severity == "ERROR" else "💡"
                )
                print(f"  {icon} Line {lineno}: {msg} [{severity}]")
            print()

        print("Fix these violations before committing.")
        print("\nGuidance:")
        print("  - Use CallbackHandler for CrewAI task execution")
        print("  - Use multi_model_service.generate_response() for LLM calls")
        print("  - See docs/guidelines/OBSERVABILITY_PATTERNS.md")
        print()

        return 1

    print("✅ All LLM calls properly instrumented")
    return 0


if __name__ == "__main__":
    sys.exit(main())
