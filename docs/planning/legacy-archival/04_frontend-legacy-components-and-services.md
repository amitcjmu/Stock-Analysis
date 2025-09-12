# Frontend Legacy Components and Services

## Findings (from prior docs and scan)
- `src/services/FlowService.ts`: Legacy service classes with console deprecation warnings.
- `src/hooks/useFlow.ts`: Deprecated hook noting migration to masterFlowService.
- `src/utils/api/apiTypes.ts`: Legacy types retained for compatibility.
- Backup/example components: files with `.backup` or example suffixes not used in app.

## Risks
- Drift from unified MFO endpoints and snake_case conventions.
- Confusion for new contributors; duplicated logic.

## Action Items
- Search and remove unused legacy services and deprecated hooks after confirming no imports.
- Replace remaining usages with unified services (master flow, unified-discovery).
- Remove backup/example components from production bundle (retain under docs if needed).



