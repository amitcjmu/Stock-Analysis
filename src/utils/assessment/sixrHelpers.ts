/**
 * Utility functions for 6R Strategy Review functionality
 * Created by CC for modularization of SixRReviewPage component
 * Updated October 2025: Aligned with 6 canonical strategies
 */

// 6R canonical strategies - standardized across platform
// Note: "replace" consolidates both COTS replacement (formerly "repurchase")
// and custom rewrites (formerly "rewrite")
export const SIX_R_STRATEGIES = [
  { value: 'rehost', label: 'Rehost (Lift & Shift)', color: 'bg-green-100 text-green-700' },
  { value: 'replatform', label: 'Replatform (Reconfigure)', color: 'bg-blue-100 text-blue-700' },
  { value: 'refactor', label: 'Refactor (Modify Code)', color: 'bg-purple-100 text-purple-700' },
  { value: 'rearchitect', label: 'Rearchitect (Cloud-Native)', color: 'bg-indigo-100 text-indigo-700' },
  { value: 'replace', label: 'Replace (COTS/SaaS or Rewrite)', color: 'bg-orange-100 text-orange-700' },
  { value: 'retire', label: 'Retire (Decommission)', color: 'bg-gray-100 text-gray-700' }
];

// Backward compatibility: Map deprecated strategies to canonical ones
const STRATEGY_MIGRATION_MAP: Record<string, string> = {
  'repurchase': 'replace',
  'rewrite': 'replace',
  'retain': 'rehost', // Fallback since retention is out of scope
  're-architect': 'rearchitect',
  'refactor/re-architect': 'rearchitect'
};

/**
 * Normalize a strategy value to canonical form
 * Handles backward compatibility with deprecated strategies
 */
export const normalizeStrategyValue = (strategy: string | undefined): string => {
  if (!strategy) return '';

  const normalized = strategy.toLowerCase().trim();

  // Check if it needs migration
  if (normalized in STRATEGY_MIGRATION_MAP) {
    return STRATEGY_MIGRATION_MAP[normalized];
  }

  return normalized;
};

/**
 * Get the color class for a 6R strategy
 * Automatically normalizes deprecated strategy values
 */
export const getStrategyColor = (strategy: string): string => {
  const normalizedStrategy = normalizeStrategyValue(strategy);
  const strategyInfo = SIX_R_STRATEGIES.find(s => s.value === normalizedStrategy);
  return strategyInfo?.color || 'bg-gray-100 text-gray-700';
};

/**
 * Get the display label for a 6R strategy
 * Automatically normalizes deprecated strategy values
 */
export const getStrategyLabel = (strategy: string): string => {
  const normalizedStrategy = normalizeStrategyValue(strategy);
  const strategyInfo = SIX_R_STRATEGIES.find(s => s.value === normalizedStrategy);
  return strategyInfo?.label || strategy;
};

/**
 * Format phase names by replacing underscores with spaces and capitalizing words
 */
export const formatPhase = (phase: string): string => {
  return phase.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

/**
 * Format date strings to readable format
 */
export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};
