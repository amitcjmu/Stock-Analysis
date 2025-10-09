/**
 * Backward compatibility re-export
 *
 * This file has been modularized into components/discovery/inventory/content/
 * for better maintainability and reduced file size.
 *
 * Original file: 1,055 LOC
 * Modularized structure:
 * - content/index.tsx - Main orchestrator
 * - content/hooks/useInventoryData.ts - Asset fetching with pagination (lines 108-348)
 * - content/hooks/useAutoExecution.ts - Retry state machine (lines 523-648)
 * - content/ViewModeToggle.tsx - View mode toggle component
 * - content/ErrorBanners.tsx - Error display components
 * - content/InventoryStates.tsx - Loading/error/empty states
 * - content/InventoryActions.tsx - Action handlers
 *
 * CRITICAL PATTERNS PRESERVED:
 * - Auto-execution retry state machine with exponential backoff
 * - Ref-based loop guards (attemptCountRef)
 * - Exact useEffect dependency arrays
 * - HTTP polling logic with exact intervals
 * - All state machines and error handling
 */

export { default } from './content';
