/**
 * Enhanced Asset Table Component - AG Grid Migration (Issue #920)
 *
 * This component now uses AG Grid for a professional data grid experience
 * matching the gap-analysis page. The legacy HTML table implementation
 * is preserved in EnhancedAssetTable.tsx.legacy.
 *
 * Migration completed: December 2025
 * - Migrated from custom HTML table to AG Grid
 * - Preserved all features: inline editing, soft delete, trash view
 * - Added professional styling and UX enhancements from gap-analysis
 */

// Re-export the AG Grid implementation
export { AGGridAssetTable as EnhancedAssetTable } from './AGGridAssetTable';
