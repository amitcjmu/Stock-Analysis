/**
 * Utility functions for 6R Strategy Review functionality
 * Created by CC for modularization of SixRReviewPage component
 */

export const SIX_R_STRATEGIES = [
  { value: 'rehost', label: 'Rehost (Lift & Shift)', color: 'bg-green-100 text-green-700' },
  { value: 'replatform', label: 'Replatform (Lift & Reshape)', color: 'bg-blue-100 text-blue-700' },
  { value: 'refactor', label: 'Refactor/Re-architect', color: 'bg-purple-100 text-purple-700' },
  { value: 'repurchase', label: 'Repurchase (SaaS)', color: 'bg-orange-100 text-orange-700' },
  { value: 'retire', label: 'Retire', color: 'bg-gray-100 text-gray-700' },
  { value: 'retain', label: 'Retain (Revisit)', color: 'bg-yellow-100 text-yellow-700' }
];

/**
 * Get the color class for a 6R strategy
 */
export const getStrategyColor = (strategy: string): string => {
  const strategyInfo = SIX_R_STRATEGIES.find(s => s.value === strategy);
  return strategyInfo?.color || 'bg-gray-100 text-gray-700';
};

/**
 * Get the display label for a 6R strategy
 */
export const getStrategyLabel = (strategy: string): string => {
  const strategyInfo = SIX_R_STRATEGIES.find(s => s.value === strategy);
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
