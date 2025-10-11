#!/usr/bin/env python3
"""
Dependency Analyzer for Backend Cleanup
Generates comprehensive dependency graphs and migration reports

Usage:
    python dependency_analyzer.py --output-dir docs/analysis/backend_cleanup/dependency_graphs
"""

import ast
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple

# === Configuration ===
BACKEND_ROOT = Path(__file__).parent.parent.parent / "app"
CREW_PATTERNS = [
    "app/services/crewai_flows/crews",
    "app/services/agents",
    "app/services/persistent_agents",
    "app/services/child_flow_services",
]

DEPRECATED_PATTERNS = {
    "crew_instantiation": r"Crew\s*\(",  # Direct Crew() calls
    "crew_class_usage": r"crew_class\s*=",  # crew_class in configs
    "old_agent_pattern": r"_crewai\.py$",  # Single-file agents
}

NEW_PATTERNS = {
    "persistent_agent": r"TenantScopedAgentPool",
    "child_flow_service": r"ChildFlowService|child_flow_service",
    "phase_executor": r"PhaseExecutor",
}


@dataclass
class CodeFile:
    """Represents a Python file in the codebase"""

    path: Path
    relative_path: str
    imports: List[str] = field(default_factory=list)
    imported_by: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    has_deprecated_pattern: Dict[str, bool] = field(default_factory=dict)
    has_new_pattern: Dict[str, bool] = field(default_factory=dict)
    line_count: int = 0


@dataclass
class DependencyGraph:
    """Complete dependency graph of the codebase"""

    files: Dict[str, CodeFile] = field(default_factory=dict)
    import_graph: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    reverse_import_graph: Dict[str, Set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )


class DependencyAnalyzer:
    """Analyzes Python dependencies and generates reports"""

    def __init__(self, backend_root: Path, crew_patterns: List[str]):
        self.backend_root = backend_root
        self.crew_patterns = crew_patterns
        self.graph = DependencyGraph()

    def scan_codebase(self):
        """Scan all Python files and build dependency graph"""
        print("🔍 Scanning codebase...")

        # Scan all Python files
        for py_file in self.backend_root.rglob("*.py"):
            # Skip __pycache__ and test files for now
            if "__pycache__" in str(py_file) or "test_" in py_file.name:
                continue

            relative = py_file.relative_to(self.backend_root.parent)
            file_obj = self._analyze_file(py_file, str(relative))
            self.graph.files[str(relative)] = file_obj

        # Build reverse graph (who imports this file?)
        self._build_reverse_graph()

        print(f"✅ Scanned {len(self.graph.files)} files")

    def _analyze_file(self, file_path: Path, relative_path: str) -> CodeFile:
        """Analyze a single Python file"""
        file_obj = CodeFile(path=file_path, relative_path=relative_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                file_obj.line_count = content.count("\n") + 1

            # Parse AST for imports and definitions
            try:
                tree = ast.parse(content, filename=str(file_path))
                file_obj.imports = self._extract_imports(tree)
                file_obj.functions = self._extract_functions(tree)
                file_obj.classes = self._extract_classes(tree)
            except SyntaxError:
                print(f"⚠️ Syntax error in {relative_path}")

            # Check for deprecated patterns
            for pattern_name, pattern_regex in DEPRECATED_PATTERNS.items():
                file_obj.has_deprecated_pattern[pattern_name] = bool(
                    re.search(pattern_regex, content)
                )

            # Check for new patterns
            for pattern_name, pattern_regex in NEW_PATTERNS.items():
                file_obj.has_new_pattern[pattern_name] = bool(
                    re.search(pattern_regex, content)
                )

        except Exception as e:
            print(f"❌ Error analyzing {relative_path}: {e}")

        return file_obj

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract all imports from AST"""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
                    # Also track what's imported from the module
                    for alias in node.names:
                        imports.append(f"{node.module}.{alias.name}")

        return imports

    def _extract_functions(self, tree: ast.AST) -> List[str]:
        """Extract function definitions"""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        return functions

    def _extract_classes(self, tree: ast.AST) -> List[str]:
        """Extract class definitions"""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
        return classes

    def _build_reverse_graph(self):
        """Build reverse dependency graph (who imports me?)"""
        for file_path, file_obj in self.graph.files.items():
            for imp in file_obj.imports:
                # Try to match import to a file in our codebase
                matching_files = self._find_matching_files(imp)
                for match in matching_files:
                    self.graph.import_graph[file_path].add(match)
                    self.graph.reverse_import_graph[match].add(file_path)
                    # Update imported_by in the target file
                    if match in self.graph.files:
                        self.graph.files[match].imported_by.append(file_path)

    def _find_matching_files(self, import_path: str) -> List[str]:
        """Find files that match an import path"""
        # Convert import path to file path
        # E.g., "app.services.crews.field_mapping" -> "app/services/crews/field_mapping.py"
        import_as_path = import_path.replace(".", "/")
        possible_file = f"{import_as_path}.py"
        possible_package = f"{import_as_path}/__init__.py"

        matching = []
        # Check for an exact file match
        if possible_file in self.graph.files:
            matching.append(possible_file)
        # Check for a package match
        if possible_package in self.graph.files:
            matching.append(possible_package)

        return matching

    def identify_orphaned_files(self) -> Dict[str, List[str]]:
        """Identify files with no incoming references"""
        orphaned = {"truly_orphaned": [], "only_self_referential": []}

        for file_path, file_obj in self.graph.files.items():
            # Check if it's in crew patterns we care about
            if not any(pattern in file_path for pattern in self.crew_patterns):
                continue

            imported_by = file_obj.imported_by

            if len(imported_by) == 0:
                orphaned["truly_orphaned"].append(file_path)
            else:
                # Check if only imported by files in same directory
                file_dir = str(Path(file_path).parent)
                only_same_dir = all(file_dir in imp for imp in imported_by)

                if only_same_dir:
                    orphaned["only_self_referential"].append(file_path)

        return orphaned

    def identify_migration_candidates(self) -> Dict[str, List[Tuple[str, str]]]:
        """Identify files using old patterns that should migrate"""
        candidates = {
            "crew_instantiation": [],
            "crew_class_usage": [],
            "old_agent_pattern": [],
        }

        for file_path, file_obj in self.graph.files.items():
            for pattern_name, has_pattern in file_obj.has_deprecated_pattern.items():
                if has_pattern:
                    # Find what imports this file
                    importers = file_obj.imported_by
                    candidates[pattern_name].append(
                        (file_path, f"Imported by {len(importers)} files")
                    )

        return candidates

    def analyze_coupling(self) -> Dict[str, any]:
        """Analyze coupling between old and new patterns"""
        coupling = {
            "old_importing_new": [],  # Old pattern files importing new pattern files
            "new_importing_old": [],  # New pattern files importing old pattern files
            "mixed_pattern_files": [],  # Files with both old and new patterns
        }

        for file_path, file_obj in self.graph.files.items():
            has_old = any(file_obj.has_deprecated_pattern.values())
            has_new = any(file_obj.has_new_pattern.values())

            if has_old and has_new:
                coupling["mixed_pattern_files"].append(file_path)

            if has_old:
                # Check what it imports
                for imported_file in self.graph.import_graph.get(file_path, []):
                    if imported_file in self.graph.files:
                        imported_obj = self.graph.files[imported_file]
                        if any(imported_obj.has_new_pattern.values()):
                            coupling["old_importing_new"].append(
                                (file_path, imported_file)
                            )

            if has_new:
                # Check what it imports
                for imported_file in self.graph.import_graph.get(file_path, []):
                    if imported_file in self.graph.files:
                        imported_obj = self.graph.files[imported_file]
                        if any(imported_obj.has_deprecated_pattern.values()):
                            coupling["new_importing_old"].append(
                                (file_path, imported_file)
                            )

        return coupling

    def generate_mermaid_graph(self, focus_on: List[str] = None) -> str:
        """Generate Mermaid flowchart for visualization"""
        mermaid = ["graph TD"]

        # Filter files to focus on
        files_to_show = {}
        if focus_on:
            for file_path, file_obj in self.graph.files.items():
                if any(pattern in file_path for pattern in focus_on):
                    files_to_show[file_path] = file_obj
        else:
            files_to_show = self.graph.files

        # Create nodes with styling based on patterns
        node_id_map = {}
        for idx, (file_path, file_obj) in enumerate(files_to_show.items()):
            node_id = f"N{idx}"
            node_id_map[file_path] = node_id

            # Determine node style
            has_old = any(file_obj.has_deprecated_pattern.values())
            has_new = any(file_obj.has_new_pattern.values())
            is_orphaned = len(file_obj.imported_by) == 0

            # Short name for readability
            short_name = Path(file_path).name

            if is_orphaned:
                mermaid.append(f'    {node_id}["{short_name} 🗑️"]:::orphaned')
            elif has_old and not has_new:
                mermaid.append(f'    {node_id}["{short_name} ⚠️"]:::deprecated')
            elif has_new:
                mermaid.append(f'    {node_id}["{short_name} ✅"]:::modern')
            else:
                mermaid.append(f'    {node_id}["{short_name}"]')

        # Create edges
        for file_path, imported_files in self.graph.import_graph.items():
            if file_path not in node_id_map:
                continue

            source_id = node_id_map[file_path]
            for imported_file in imported_files:
                if imported_file in node_id_map:
                    target_id = node_id_map[imported_file]
                    mermaid.append(f"    {source_id} --> {target_id}")

        # Add styling
        mermaid.extend(
            [
                "",
                "    classDef orphaned fill:#ff6b6b,stroke:#c92a2a,color:#fff",
                "    classDef deprecated fill:#ffd43b,stroke:#f59f00,color:#000",
                "    classDef modern fill:#51cf66,stroke:#2f9e44,color:#000",
            ]
        )

        return "\n".join(mermaid)

    def generate_report(self, output_dir: Path):
        """Generate comprehensive analysis reports"""
        output_dir.mkdir(parents=True, exist_ok=True)

        print("\n📊 Generating Reports...")

        # 1. Orphaned files report
        orphaned = self.identify_orphaned_files()
        with open(output_dir / "orphaned_files.md", "w") as f:
            f.write("# Orphaned Files Report\n\n")
            f.write("## Truly Orphaned (No Imports)\n\n")
            for file_path in sorted(orphaned["truly_orphaned"]):
                f.write(f"- `{file_path}`\n")

            f.write("\n## Self-Referential Only\n\n")
            for file_path in sorted(orphaned["only_self_referential"]):
                f.write(f"- `{file_path}`\n")

        print(
            f"  ✅ Orphaned files: {len(orphaned['truly_orphaned'])} truly orphaned, "
            f"{len(orphaned['only_self_referential'])} self-referential"
        )

        # 2. Migration candidates report
        migration = self.identify_migration_candidates()
        with open(output_dir / "migration_candidates.md", "w") as f:
            f.write("# Migration Candidates Report\n\n")
            for pattern_name, candidates in migration.items():
                f.write(f"## {pattern_name.replace('_', ' ').title()}\n\n")
                for file_path, note in sorted(candidates):
                    f.write(f"- `{file_path}` - {note}\n")
                f.write("\n")

        print(
            f"  ✅ Migration candidates: {sum(len(c) for c in migration.values())} files"
        )

        # 3. Coupling analysis report
        coupling = self.analyze_coupling()
        with open(output_dir / "coupling_analysis.md", "w") as f:
            f.write("# Coupling Analysis Report\n\n")

            f.write("## Mixed Pattern Files (Old + New)\n\n")
            f.write("These files contain both deprecated and modern patterns:\n\n")
            for file_path in sorted(coupling["mixed_pattern_files"]):
                f.write(f"- `{file_path}`\n")

            f.write("\n## Old Importing New\n\n")
            f.write("Deprecated files that import modern implementations:\n\n")
            for old_file, new_file in sorted(coupling["old_importing_new"]):
                f.write(f"- `{old_file}` → `{new_file}`\n")

            f.write("\n## New Importing Old\n\n")
            f.write("Modern files that still depend on deprecated code:\n\n")
            for new_file, old_file in sorted(coupling["new_importing_old"]):
                f.write(f"- `{new_file}` → `{old_file}`\n")

        print(
            f"  ✅ Coupling: {len(coupling['mixed_pattern_files'])} mixed, "
            f"{len(coupling['old_importing_new'])} old→new, "
            f"{len(coupling['new_importing_old'])} new→old"
        )

        # 4. Generate Mermaid graphs
        # Focus on crew files only for readability
        crew_graph = self.generate_mermaid_graph(focus_on=CREW_PATTERNS)
        with open(output_dir / "dependency_graph_crews.mmd", "w") as f:
            f.write(crew_graph)

        print("  ✅ Mermaid graph generated")

        # 5. JSON export for programmatic access
        export_data = {
            "orphaned": orphaned,
            "migration_candidates": {
                k: [(f, n) for f, n in v] for k, v in migration.items()
            },
            "coupling": {
                "mixed_pattern_files": coupling["mixed_pattern_files"],
                "old_importing_new": [
                    {"old": o, "new": n} for o, n in coupling["old_importing_new"]
                ],
                "new_importing_old": [
                    {"new": n, "old": o} for n, o in coupling["new_importing_old"]
                ],
            },
        }

        with open(output_dir / "analysis_data.json", "w") as f:
            json.dump(export_data, f, indent=2)

        print("  ✅ JSON export complete")

        # 6. Summary statistics
        self._generate_summary(output_dir, orphaned, migration, coupling)

    def _generate_summary(self, output_dir, orphaned, migration, coupling):
        """Generate executive summary"""
        with open(output_dir / "SUMMARY.md", "w") as f:
            f.write("# Dependency Analysis Summary\n\n")

            total_files = len(self.graph.files)
            crew_files = sum(
                1
                for p in self.graph.files.keys()
                if any(pattern in p for pattern in CREW_PATTERNS)
            )

            f.write(f"**Total files analyzed:** {total_files}\n")
            f.write(f"**Crew-related files:** {crew_files}\n\n")

            f.write("## Key Findings\n\n")

            # Orphaned files
            truly_orphaned = len(orphaned["truly_orphaned"])
            f.write(
                f"### Orphaned Files: {truly_orphaned} files with no incoming imports\n\n"
            )
            f.write(
                "**✅ SAFE TO ARCHIVE:** These files are not imported anywhere.\n\n"
            )

            # Migration candidates
            total_migration = sum(len(c) for c in migration.values())
            f.write(f"### Migration Candidates: {total_migration} files\n\n")
            f.write(
                "**⚠️ REQUIRES MIGRATION:** These files use deprecated patterns:\n\n"
            )
            for pattern_name, candidates in migration.items():
                if candidates:
                    f.write(f"- **{pattern_name}**: {len(candidates)} files\n")

            # Coupling issues
            f.write("\n### Coupling Issues\n\n")
            f.write(
                f"- **Mixed patterns**: {len(coupling['mixed_pattern_files'])} files contain both old and new code\n"
            )
            f.write(
                f"- **Old → New dependencies**: "
                f"{len(coupling['old_importing_new'])} deprecated files import modern code\n"
            )
            f.write(
                f"- **New → Old dependencies**: "
                f"{len(coupling['new_importing_old'])} modern files still depend on deprecated code\n"
            )

            f.write("\n## Recommendations\n\n")
            f.write(
                "1. **Archive first**: Truly orphaned files (no incoming imports)\n"
            )
            f.write("2. **Migrate next**: Files with deprecated patterns\n")
            f.write("3. **Refactor last**: Mixed pattern files and coupling issues\n\n")

            f.write("## Detailed Reports\n\n")
            f.write("- [Orphaned Files](./orphaned_files.md)\n")
            f.write("- [Migration Candidates](./migration_candidates.md)\n")
            f.write("- [Coupling Analysis](./coupling_analysis.md)\n")
            f.write("- [Dependency Graph (Mermaid)](./dependency_graph_crews.mmd)\n")
            f.write("- [Raw Data (JSON)](./analysis_data.json)\n")

        print(f"\n✅ Summary generated: {output_dir}/SUMMARY.md")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze backend dependencies for cleanup"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/analysis/backend_cleanup/dependency_graphs"),
        help="Output directory for reports",
    )

    args = parser.parse_args()

    print("🚀 Backend Dependency Analyzer")
    print("=" * 50)

    analyzer = DependencyAnalyzer(BACKEND_ROOT, CREW_PATTERNS)
    analyzer.scan_codebase()
    analyzer.generate_report(args.output_dir)

    print("\n✅ Analysis complete!")
    print(f"📁 Reports saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
