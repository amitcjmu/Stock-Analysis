/**
 * GlobalContext compatibility exports
 * Re-exports hooks and components for easier imports
 */

// Export hooks
export {
  useAuthCompat,
  useClientCompat,
  useEngagementCompat,
  withContextMigration,
  useContextDebug
} from './compatibilityHooks';

// Export components
export {
  ContextMigrationProvider,
  ContextDebugger,
  PerformanceDebugger,
  MigrationStatusIndicator
} from './compatibilityComponents';
