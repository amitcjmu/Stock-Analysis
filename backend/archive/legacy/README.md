# Legacy Code Archive

**Archived on:** 2025-01-27
**Phase:** Backend Session-to-Flow Refactor Phase 5
**Reason:** Removing session references and transitioning to flow-based architecture

## What was archived

This directory contains legacy code that was replaced during the Backend Session-to-Flow Refactor implementation. The code has been preserved for reference and potential rollback scenarios.

### Archived Components:

#### Schemas (`schemas/`)
- `session.py` - Legacy session schema definitions for Data Import Session API
  - Contains `SessionBase`, `SessionCreate`, `SessionUpdate`, `Session` models
  - Replaced by flow-based schemas in the unified flow architecture

## Migration Notes

- All new implementations should use flow-based patterns with `flow_id` as primary identifier
- Session-based references have been replaced with flow-based references in main.py
- Legacy session schemas are preserved here for reference during transition period
- Database sessions (SQLAlchemy) are different from user sessions and remain unchanged

## Replacement Components

- Flow-based schemas in `app/schemas/`
- Flow-based context resolution in `app/core/context.py`
- Master Flow Orchestrator system for unified flow management

## Related Files

The following files were updated as part of this cleanup:
- `main.py` - Removed session_id references in debug endpoints, replaced with flow_id
- Context resolution logic updated to use flow-based patterns

## Contact

For questions about this migration, refer to the Backend Session-to-Flow Refactor Plan documentation and the Phase 5 implementation notes.
