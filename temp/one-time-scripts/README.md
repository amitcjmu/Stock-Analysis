# One-Time Scripts Archive

This directory contains scripts that were created for one-time debugging or fixing specific issues during development. These scripts are kept for historical reference but are not part of the active codebase.

## Archived Scripts

### Cache Debugging Scripts
- **check_react_query_cache.js** - Browser console script to debug a specific problematic flow ID in React Query cache
- **clear_browser_cache.js** - Temporary browser console script to clear stale flow data from storage
- **clear_frontend_cache.js** - Enhanced version of cache clearing script for troubleshooting

These scripts were created during the session_id → flow_id migration (Remediation Phase 1) to debug flow context synchronization issues mentioned in the platform documentation.

## Note
These scripts should not be used in production and are kept only for reference. For current development utilities, please check the `/scripts` directory.
