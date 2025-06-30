# Documentation Archive

This directory contains archived documentation that is no longer current but preserved for historical reference.

## Archive Structure

### 📁 phase1-transition/
Documentation from the Phase 1 session_id → flow_id migration period.

- **session-based-docs/**: Original documentation referencing session_id architecture
- **analysis-superseded/**: Technical analyses that have been superseded by newer versions
- **transition-artifacts/**: Temporary documentation created during migration process

### 📁 sqlite-persistence/
Documentation from the dual SQLite/PostgreSQL persistence period (deprecated).

### 📁 pre-crewai-flows/
Documentation from before CrewAI Flow implementation.

### 📁 deprecated-apis/
API documentation for deprecated endpoints (when fully deprecated).

## Usage Guidelines

### 🔍 Finding Archived Content
- Check the **Archive Index** below for redirections to current documentation
- Use git history to see when files were archived
- Most archived content has been replaced by newer versions

### ⚠️ Important Notes
- **Do not reference archived documentation** in new development
- Archived files may contain outdated patterns and deprecated approaches
- For current documentation, see the main `/docs` folder

### 🔄 Unarchiving Process
If you need to reference or unarchive content:
1. Check if current documentation covers the same topic
2. Verify the archived content is still relevant
3. Update any deprecated references before moving back to main docs

## Archive Index - Redirections to Current Documentation

### Session-based Architecture → Flow-based Architecture
- **Old**: `session_management_architecture.md` 
- **New**: `docs/adr/001-session-to-flow-migration.md`

### Discovery Flow Analysis → Current Architecture
- **Old**: Multiple discovery flow analysis files
- **New**: `docs/development/AI_Force_Migration_Platform_Summary_for_Coding_Agents.md`

### Database Consolidation → Current Database Architecture  
- **Old**: Multiple database consolidation plans
- **New**: `docs/db/database_architecture.md`

### Platform Summaries → Current Platform Guide
- **Old**: Multiple platform summary versions
- **New**: `docs/development/CrewAI_Development_Guide.md`

## Archived File Summary

```
Total Archived Files: 45+ files (Phase 3 Cleanup)
├── Phase 1 Transition: 45+ files
│   ├── Session-based docs: 15 files (session_id architecture)
│   ├── Superseded analysis: 18 files (technical analyses)
│   └── Transition artifacts: 12 files (migration tracking)
├── Legacy Archive: 15 files (pre-existing)
└── Future Categories: TBD
```

**Recent Archival (June 30, 2024)**: 45+ files moved during Phase 3 documentation cleanup representing the completion of session_id → flow_id migration.

## Archive Maintenance

- **Review Cycle**: Annual review of archived content
- **Cleanup Policy**: Files older than 2 years may be permanently removed
- **Access**: Archived content available through git history if removed

---
*Last Updated: [Current Date]*
*Archive Created: Phase 3 of Documentation Review and Archival Plan*