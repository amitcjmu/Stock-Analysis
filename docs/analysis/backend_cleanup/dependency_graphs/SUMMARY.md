# Dependency Analysis Summary

**Total files analyzed:** 2035
**Crew-related files:** 148

## Key Findings

### Orphaned Files: 0 files with no incoming imports

**✅ SAFE TO ARCHIVE:** These files are not imported anywhere.

### Migration Candidates: 28 files

**⚠️ REQUIRES MIGRATION:** These files use deprecated patterns:

- **crew_instantiation**: 26 files
- **crew_class_usage**: 2 files

### Coupling Issues

- **Mixed patterns**: 4 files contain both old and new code
- **Old → New dependencies**: 322 deprecated files import modern code
- **New → Old dependencies**: 112 modern files still depend on deprecated code

## Recommendations

1. **Archive first**: Truly orphaned files (no incoming imports)
2. **Migrate next**: Files with deprecated patterns
3. **Refactor last**: Mixed pattern files and coupling issues

## Detailed Reports

- [Orphaned Files](./orphaned_files.md)
- [Migration Candidates](./migration_candidates.md)
- [Coupling Analysis](./coupling_analysis.md)
- [Dependency Graph (Mermaid)](./dependency_graph_crews.mmd)
- [Raw Data (JSON)](./analysis_data.json)
